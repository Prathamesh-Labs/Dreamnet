import time
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.research_session import ResearchSession
from app.models.hypothesis import Hypothesis
from app.models.experiment import Experiment
from app.models.evaluation import Evaluation
from app.research.policies import ResearchPolicies
from app.research.state import ResearchStateManager
from app.services.llm.factory import LLMProviderFactory
from app.services.experiment.designer import ExperimentDesigner
from app.services.experiment.runner import ExperimentRunner
from app.services.experiment.evaluator import ExperimentEvaluator

class ResearchLoopEngine:
    @staticmethod
    def run_session_loop(session_id: UUID, db: Session):
        print(f"[ResearchLoopEngine] Starting research loop background task for session {session_id}")
        ResearchStateManager.register_running(session_id)
        
        try:
            while True:
                # 1. Fetch current session state from DB
                db.expire_all()
                session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
                if not session:
                    print(f"[ResearchLoopEngine] Session {session_id} not found.")
                    break
                
                # Check status
                if session.status != "RUNNING":
                    print(f"[ResearchLoopEngine] Session {session_id} status is {session.status}. Stopping loop.")
                    break

                # 2. Check budget and iterations
                if session.iteration > ResearchPolicies.MAX_ITERATIONS:
                    print(f"[ResearchLoopEngine] Max iterations ({ResearchPolicies.MAX_ITERATIONS}) reached. Completing.")
                    session.status = "COMPLETED"
                    db.commit()
                    break

                # Count experiments already run
                exp_count = db.query(Experiment).join(Hypothesis, Experiment.hypothesis_id == Hypothesis.id).filter(Hypothesis.question_id == session.question_id).count()
                if exp_count >= ResearchPolicies.MAX_EXPERIMENTS:
                    print(f"[ResearchLoopEngine] Max experiments limit reached. Completing.")
                    session.status = "COMPLETED"
                    db.commit()
                    break

                # 3. Fetch hypotheses for this question
                hypotheses = db.query(Hypothesis).filter(Hypothesis.question_id == session.question_id).order_by(Hypothesis.created_at.asc()).all()
                if not hypotheses:
                    # No hypotheses generated yet. Generate initial hypotheses.
                    print("[ResearchLoopEngine] No hypotheses found. Generating initial compete set...")
                    provider = LLMProviderFactory.get_provider()
                    hypotheses_data = provider.generate_hypotheses(session.question.text)
                    for h_data in hypotheses_data:
                        db_h = Hypothesis(
                            question_id=session.question_id,
                            statement=h_data.get("statement"),
                            rationale=h_data.get("rationale"),
                            assumptions=h_data.get("assumptions", []),
                            variables=h_data.get("variables", []),
                            predicted_outcome=h_data.get("predicted_outcome"),
                            confidence=h_data.get("confidence", 0.5),
                            testability=h_data.get("testability", "MEDIUM"),
                            status="PROPOSED"
                        )
                        db.add(db_h)
                    db.commit()
                    # Re-fetch
                    continue

                # 4. Find the first untested hypothesis
                untested_h = None
                for h in hypotheses:
                    if not h.experiment:
                        untested_h = h
                        break
                    elif h.experiment.status in ["DRAFT", "READY", "RUNNING"]:
                        untested_h = h
                        break
                
                if not untested_h:
                    # All hypotheses have been tested.
                    # Check if the last evaluation was REJECTED. If so, generate a refined/follow-up hypothesis!
                    rejected_h = db.query(Hypothesis).join(Experiment, Hypothesis.id == Experiment.hypothesis_id).join(Evaluation, Experiment.id == Evaluation.experiment_id).filter(
                        Hypothesis.question_id == session.question_id,
                        Evaluation.verdict == "REJECTED"
                    ).order_by(Evaluation.created_at.desc()).first()
                    
                    if rejected_h:
                        print(f"[ResearchLoopEngine] Latest hypothesis H{rejected_h.id} was REJECTED. Generating refined follow-up hypothesis...")
                        provider = LLMProviderFactory.get_provider()
                        
                        try:
                            followup_data = provider.generate_followup_hypothesis(
                                question=session.question.text,
                                failed_hypothesis=rejected_h.statement,
                                failed_criteria=rejected_h.experiment.measurable_success_criteria,
                                failed_metrics=rejected_h.experiment.result.metrics if rejected_h.experiment.result else {}
                            )
                            
                            db_h = Hypothesis(
                                question_id=session.question_id,
                                statement=followup_data.get("statement"),
                                rationale=followup_data.get("rationale"),
                                assumptions=followup_data.get("assumptions", []),
                                variables=followup_data.get("variables", []),
                                predicted_outcome=followup_data.get("predicted_outcome"),
                                confidence=followup_data.get("confidence", 0.5),
                                testability=followup_data.get("testability", "MEDIUM"),
                                status="PROPOSED"
                            )
                            db.add(db_h)
                            session.iteration += 1
                            db.commit()
                            print(f"[ResearchLoopEngine] Successfully added refined follow-up hypothesis: {db_h.statement}")
                        except Exception as e:
                            print(f"[ResearchLoopEngine] Error generating follow-up hypothesis: {e}")
                            session.status = "STOPPED"
                            db.commit()
                            break
                        continue
                    else:
                        # All hypotheses tested and supported or inconclusive. Complete the research session.
                        print("[ResearchLoopEngine] All hypotheses are fully tested. No active rejections. Completing.")
                        session.status = "COMPLETED"
                        db.commit()
                        break

                print(f"[ResearchLoopEngine] Selected active hypothesis statement: '{untested_h.statement}'")
                
                # 5. Ensure experiment is designed
                if not untested_h.experiment:
                    print(f"[ResearchLoopEngine] Designing experiment spec for hypothesis H{untested_h.id}...")
                    experiment = ExperimentDesigner.design_experiment(untested_h.id, db)
                else:
                    experiment = untested_h.experiment

                # 6. Human in the loop validation check
                if ResearchPolicies.REQUIRE_HUMAN_APPROVAL and not experiment.approved:
                    print(f"[ResearchLoopEngine] Experiment for hypothesis H{untested_h.id} requires human approval. Pausing session.")
                    session.status = "PAUSED"
                    db.commit()
                    break

                # 7. Run experiment
                print(f"[ResearchLoopEngine] Running experiment H{untested_h.id} in AST sandbox...")
                result = ExperimentRunner.run_experiment(experiment.id, db)
                
                # 8. Evaluate results
                print(f"[ResearchLoopEngine] Evaluating results for experiment H{untested_h.id}...")
                evaluation = ExperimentEvaluator.evaluate_experiment(experiment.id, db)
                
                # Update hypothesis status based on evaluation verdict
                untested_h.status = evaluation.verdict
                db.commit()

                # 9. Trigger Discovery Engine scan
                print(f"[ResearchLoopEngine] Scanning for unexpected discovery patterns...")
                try:
                    from app.engines.discovery.analyzer import DiscoveryAnalyzer
                    DiscoveryAnalyzer.analyze_session_for_discoveries(session.id, db)
                except Exception as ex_disc:
                    print(f"[ResearchLoopEngine] Warning: Discovery scan failed: {ex_disc}")
                
                print(f"[ResearchLoopEngine] Iteration step complete. Verdict: {evaluation.verdict}")
                time.sleep(0.5)

        except Exception as e:
            print(f"[ResearchLoopEngine] Execution loop error: {e}")
            db.rollback()
            try:
                session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
                if session:
                    session.status = "STOPPED"
                    db.commit()
            except Exception:
                pass
        finally:
            ResearchStateManager.deregister_running(session_id)
            print(f"[ResearchLoopEngine] Deregistered session {session_id} running state.")
