from typing import List
from learning.models import (
    SkillGapAnalysis, LearningRoadmap, LearningRoadmapItem, 
    PriorityBand, RoadmapItemStatus, GapType
)

class SkillDependencyService:
    # A simple mock dependency graph for deterministic ordering
    DEPENDENCY_GRAPH = {
        "React": ["JavaScript", "HTML", "CSS"],
        "Django": ["Python"],
        "Kubernetes": ["Docker"],
        "AWS": ["Networking", "Linux"],
        "PostgreSQL": ["SQL"]
    }

    @classmethod
    def get_dependencies(cls, skill: str) -> List[str]:
        return cls.DEPENDENCY_GRAPH.get(skill, [])

class LearningRoadmapService:
    @staticmethod
    def generate_roadmap(analysis: SkillGapAnalysis, hours_per_week: int = 10) -> LearningRoadmap:
        # Check if one already exists
        existing = LearningRoadmap.objects.filter(analysis=analysis, is_stale=False).first()
        if existing:
            return existing
            
        roadmap = LearningRoadmap.objects.create(
            user=analysis.user,
            analysis=analysis,
            title=f"Learning Roadmap for {analysis.target_type}",
            hours_per_week=hours_per_week
        )
        
        # We only want gaps that are actually missing or need improvement
        gaps_to_close = analysis.gap_items.exclude(gap_type=GapType.NO_GAP)
        
        # Sort gaps deterministically by priority
        priority_weights = {
            PriorityBand.CRITICAL: 4,
            PriorityBand.HIGH: 3,
            PriorityBand.MEDIUM: 2,
            PriorityBand.LOW: 1
        }
        
        sorted_gaps = sorted(
            gaps_to_close, 
            key=lambda g: priority_weights.get(g.priority_band, 0), 
            reverse=True
        )
        
        sequence = 1
        for gap in sorted_gaps:
            deps = SkillDependencyService.get_dependencies(gap.canonical_skill)
            
            # Estimate effort deterministically based on gap type
            effort = 10.0
            if gap.gap_type == GapType.MISSING_SKILL:
                effort = 40.0
            elif gap.gap_type == GapType.EXPERIENCE_GAP:
                effort = 20.0
            elif gap.gap_type == GapType.EVIDENCE_GAP:
                effort = 15.0 # Just build a project
                
            LearningRoadmapItem.objects.create(
                roadmap=roadmap,
                canonical_skill=gap.canonical_skill,
                title=f"Master {gap.canonical_skill}",
                objective=f"Close {gap.gap_type} for {gap.canonical_skill}",
                priority=gap.priority_band,
                sequence=sequence,
                estimated_effort_hours=effort,
                dependency_skills=deps
            )
            sequence += 1
            
        return roadmap
        
    @staticmethod
    def mark_stale(roadmap: LearningRoadmap, reason: str):
        roadmap.is_stale = True
        roadmap.stale_reason = reason
        roadmap.save(update_fields=['is_stale', 'stale_reason'])
