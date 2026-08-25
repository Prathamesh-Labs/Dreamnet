from sqlalchemy.orm import Session
from uuid import UUID
from app.models.research_session import ResearchSession
from app.models.hypothesis import Hypothesis
from app.models.experiment import Experiment
from app.models.experiment_result import ExperimentResult
from app.models.evaluation import Evaluation
from app.models.discovery import Discovery

class ResearchReportGenerator:
    @staticmethod
    def generate_markdown_report(session_id: UUID, db: Session) -> str:
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session:
            raise ValueError(f"Research session {session_id} not found.")

        # Gather data
        question_text = session.question.text
        hypotheses = db.query(Hypothesis).filter(Hypothesis.question_id == session.question_id).all()
        discoveries = db.query(Discovery).filter(Discovery.research_session_id == session_id).all()

        report = []
        report.append(f"# DREAMNET Autonomous Scientific Research Report")
        report.append(f"**Research Question:** {question_text}")
        report.append(f"**Session ID:** {session.id}")
        report.append(f"**Iteration Loop:** {session.iteration} / {session.budget}")
        report.append(f"**Status:** {session.status}")
        report.append(f"**Generated At:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if session.created_at else ''}\n")
        report.append("---")

        # 1. Hypotheses Section
        report.append(f"## 🧬 Hypotheses Pipeline ({len(hypotheses)})")
        for idx, h in enumerate(hypotheses):
            report.append(f"### H{idx+1}: {h.statement}")
            report.append(f"- **Rationale:** {h.rationale}")
            report.append(f"- **Predicted Outcome:** {h.predicted_outcome}")
            report.append(f"- **Confidence:** {h.confidence * 100:.0f}%")
            report.append(f"- **Testability:** {h.testability}")
            report.append(f"- **Final Verdict:** {h.status}\n")

        report.append("---")

        # 2. Experiments and Evaluations
        report.append("## 🧪 Experimental Methods & Evaluations")
        for idx, h in enumerate(hypotheses):
            if not h.experiment:
                report.append(f"### Hypothesis H{idx+1} (No Experiment Run)")
                continue

            exp = h.experiment
            report.append(f"### Experiment Trial: H{idx+1}")
            report.append(f"**Objective:** {exp.objective}")
            report.append(f"**Baseline Setup:** {exp.baseline}")
            report.append(f"**Treatment:** {exp.treatment}")
            report.append(f"**Dataset:** {exp.dataset}")
            report.append(f"**Measurable Success Criteria:** {exp.measurable_success_criteria}\n")

            if exp.result:
                res = exp.result
                report.append(f"#### 📊 Sandbox Results")
                report.append(f"- **Execution Time:** {res.execution_time_ms:.1f}ms")
                report.append(f"- **Extracted Metrics:**")
                for k, v in (res.metrics or {}).items():
                    report.append(f"  - `{k}`: {v}")
                
                # Truncated raw logs
                raw_logs = res.raw_output or ""
                truncated_logs = "\n".join(raw_logs.splitlines()[:15])
                if len(raw_logs.splitlines()) > 15:
                    truncated_logs += "\n... [truncated logs] ..."
                report.append(f"\n*Raw Terminal Log Fragment:*")
                report.append(f"```text\n{truncated_logs}\n```\n")

            if exp.evaluation:
                eval_out = exp.evaluation
                report.append(f"#### 🧠 Verdict Evaluation")
                report.append(f"- **Verdict Decision:** `{eval_out.verdict}` (Confidence: {eval_out.confidence * 100:.0f}%)")
                report.append(f"- **Assertions Checklist Status:**")
                for check in (eval_out.evidence or []):
                    status_icon = "✓ Passed" if check.get("passed") else "✗ Failed"
                    report.append(f"  - `{check.get('rule')}` -> observed: `{check.get('observed')}` -> **{status_icon}**")
                
                report.append(f"\n*LLM Observation Explanation:*")
                report.append(f"> {eval_out.observations}\n")

        report.append("---")

        # 3. Discoveries Section
        report.append(f"## 🔎 Discovery Candidates ({len(discoveries)})")
        if not discoveries:
            report.append("No unexpected anomalies, direction flips, or contradictions were flagged during this research run.")
        else:
            for idx, d in enumerate(discoveries):
                report.append(f"### Candidate #{idx+1}: {d.title}")
                report.append(f"- **Status:** `{d.status}`")
                report.append(f"- **Observation Summary:** {d.observation}")
                report.append(f"- **Confidence:** {d.confidence:.2f} | Novelty: {d.novelty_score:.2f} | Significance: {d.significance:.2f} | Reproducibility: {d.reproducibility:.2f}")
                report.append(f"- **Action Lead:** {d.recommended_action}\n")

        return "\n".join(report)
