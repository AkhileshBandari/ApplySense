from learning.models import LearningRoadmapItem, RoadmapItemStatus

class LearningProgressService:
    @staticmethod
    def mark_item_status(item: LearningRoadmapItem, status: RoadmapItemStatus):
        item.status = status
        item.save(update_fields=['status'])

class SkillGapClosureService:
    @staticmethod
    def evaluate_gap_closure(analysis, candidate_context):
        """
        In the future, this will look at completed roadmap items, 
        newly added verified skills in candidate_context, 
        and update the gap analysis states (e.g. CLOSED).
        For now, closure strictly requires the verified context to contain the skill.
        """
        pass
