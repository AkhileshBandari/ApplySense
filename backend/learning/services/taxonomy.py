from typing import Optional
from django.db.models import Q
from learning.models import SkillTaxonomy, SkillAlias

class SkillRequirementNormalizationService:
    @staticmethod
    def normalize_skill(skill_name: str) -> str:
        """
        Normalizes a raw skill string into a canonical skill name.
        Uses case-insensitive lookup and aliases.
        If no taxonomy exists, returns the title-cased original name as a fallback.
        """
        if not skill_name:
            return ""
        
        name_clean = skill_name.strip()
        name_lower = name_clean.lower()
        
        # 1. Check exact match in canonical_name
        # Using iexact for case-insensitive match
        taxonomy = SkillTaxonomy.objects.filter(canonical_name__iexact=name_clean).first()
        if taxonomy:
            return taxonomy.canonical_name
            
        # 2. Check alias
        alias = SkillAlias.objects.filter(alias_name__iexact=name_clean).select_related('taxonomy').first()
        if alias:
            return alias.taxonomy.canonical_name
            
        # 3. Fallback: normalize the string (e.g. Title Case)
        return name_clean.title()
