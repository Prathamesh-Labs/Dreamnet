from sqlalchemy.orm import Session
from uuid import UUID
from app.models.research_session import ResearchSession
from app.models.hypothesis import Hypothesis
from app.models.discovery import Discovery
from app.engines.discovery.detector import DiscoveryDetector
from app.engines.discovery.scorer import DiscoveryScorer
from app.services.llm.factory import LLMProviderFactory
from typing import Any

class DiscoveryAnalyzer:
    @staticmethod
    def analyze_session_for_discoveries(session_id: UUID, db: Session) -> list[Discovery]:
        session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
        if not session:
            raise ValueError(f"Research session {session_id} not found.")

        # Fetch hypotheses and outcomes
        hypotheses = db.query(Hypothesis).filter(Hypothesis.question_id == session.question_id).all()
        
        # 1. Detect patterns
        detected_patterns = DiscoveryDetector.detect_patterns(hypotheses)
        discoveries = []

        # 2. Score and analyze each pattern
        for pattern in detected_patterns:
            novelty, confidence, significance, reproducibility = DiscoveryScorer.score_pattern(pattern)

            # Check if this discovery is already saved
            existing = db.query(Discovery).filter(
                Discovery.research_session_id == session_id,
                Discovery.title == pattern.title
            ).first()

            if existing:
                # Update existing candidate stats/evidence
                existing.evidence = pattern.evidence
                existing.supporting_experiments = pattern.supporting_experiments
                existing.confidence = confidence
                existing.reproducibility = reproducibility
                existing.significance = significance
                db.commit()
                db.refresh(existing)
                discoveries.append(existing)
            else:
                # Generate explanation summary using LLM
                provider = LLMProviderFactory.get_provider()
                try:
                    observation_summary = provider.explain_discovery(
                        title=pattern.title,
                        pattern_type=pattern.pattern_type,
                        evidence=pattern.evidence,
                        description=pattern.description
                    )
                except Exception as e:
                    # Fallback explanation
                    observation_summary = f"Detected pattern type '{pattern.pattern_type}': {pattern.description}"

                # Default recommended action
                if pattern.pattern_type == "unexpected_magnitude":
                    action = "Validate this scaling behavior across diverse hardware profiles to isolate driver limits."
                elif pattern.pattern_type == "contradiction":
                    action = "Conduct layer-wise parameter variance checks to isolate the divergence bounds."
                else:
                    action = "Run verification validation sweeps on expanded datasets to confirm optimization stability."

                db_discovery = Discovery(
                    research_session_id=session_id,
                    title=pattern.title,
                    observation=observation_summary,
                    evidence=pattern.evidence,
                    supporting_experiments=pattern.supporting_experiments,
                    novelty_score=novelty,
                    confidence=confidence,
                    significance=significance,
                    reproducibility=reproducibility,
                    recommended_action=action,
                    status="CANDIDATE"
                )
                db.add(db_discovery)
                db.commit()
                db.refresh(db_discovery)
                discoveries.append(db_discovery)

        return discoveries
