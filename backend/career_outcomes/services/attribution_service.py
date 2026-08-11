from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from career_outcomes.models import CareerOutcomeRecord, NormalizedOutcomeState
from career_outcomes.services.confidence_service import ConfidenceService

User = get_user_model()

class AttributionAnalysisService:
    """
    Measures associations between parameters (Resume, Match Score, Tailoring) and outcomes.
    Explicitly refuses to assert causality.
    """
    
    @classmethod
    def analyze_resume_performance(cls, user: User) -> dict:
        qs = CareerOutcomeRecord.objects.filter(user=user, resume_version_id__isnull=False)
        
        # Group by resume_version_id
        stats = qs.values('resume_version_id').annotate(
            total_apps=Count('id', filter=Q(normalized_state__in=[NormalizedOutcomeState.APPLIED, NormalizedOutcomeState.SUBMITTED])),
            total_responses=Count('id', filter=Q(normalized_state__in=[NormalizedOutcomeState.SCREENING, NormalizedOutcomeState.INTERVIEW])),
            total_interviews=Count('id', filter=Q(normalized_state=NormalizedOutcomeState.INTERVIEW))
        )
        
        results = []
        for stat in stats:
            apps = stat['total_apps']
            if apps < 10:
                results.append({
                    "resume_version_id": stat['resume_version_id'],
                    "status": "INSUFFICIENT_COMPARABLE_SAMPLE",
                    "total_apps": apps
                })
            else:
                results.append({
                    "resume_version_id": stat['resume_version_id'],
                    "status": "OBSERVED_ASSOCIATION",
                    "total_apps": apps,
                    "response_rate": round((stat['total_responses'] / apps) * 100, 2),
                    "interview_rate": round((stat['total_interviews'] / apps) * 100, 2),
                    "confidence": ConfidenceService.calculate_confidence(apps)
                })
                
        return {"resume_performance": results}

    @classmethod
    def analyze_match_score_performance(cls, user: User) -> dict:
        qs = CareerOutcomeRecord.objects.filter(user=user, job_match_score__isnull=False)
        
        buckets = {
            "90-100": {"apps": 0, "responses": 0},
            "80-89": {"apps": 0, "responses": 0},
            "70-79": {"apps": 0, "responses": 0},
            "<70": {"apps": 0, "responses": 0}
        }
        
        for record in qs:
            score = record.job_match_score
            is_app = record.normalized_state in [NormalizedOutcomeState.APPLIED, NormalizedOutcomeState.SUBMITTED]
            is_response = record.normalized_state in [NormalizedOutcomeState.SCREENING, NormalizedOutcomeState.INTERVIEW, NormalizedOutcomeState.OFFER]
            
            bucket = "<70"
            if score >= 90: bucket = "90-100"
            elif score >= 80: bucket = "80-89"
            elif score >= 70: bucket = "70-79"
                
            if is_app: buckets[bucket]['apps'] += 1
            if is_response: buckets[bucket]['responses'] += 1
            
        results = {}
        for b_name, stats in buckets.items():
            if stats['apps'] < 5:
                results[b_name] = {"status": "INSUFFICIENT_SAMPLE"}
            else:
                results[b_name] = {
                    "status": "OBSERVED_ASSOCIATION",
                    "response_rate": round((stats['responses'] / stats['apps']) * 100, 2),
                    "confidence": ConfidenceService.calculate_confidence(stats['apps'])
                }
                
        return {"match_score_performance": results}

    @classmethod
    def analyze_tailoring_performance(cls, user: User) -> dict:
        # Compare tailored (tailoring_version_id is not null) vs non-tailored
        qs = CareerOutcomeRecord.objects.filter(user=user)
        
        stats = qs.aggregate(
            total_tailored=Count('id', filter=Q(tailoring_version_id__isnull=False, normalized_state__in=[NormalizedOutcomeState.APPLIED, NormalizedOutcomeState.SUBMITTED])),
            responses_tailored=Count('id', filter=Q(tailoring_version_id__isnull=False, normalized_state__in=[NormalizedOutcomeState.SCREENING, NormalizedOutcomeState.INTERVIEW])),
            total_untailored=Count('id', filter=Q(tailoring_version_id__isnull=True, normalized_state__in=[NormalizedOutcomeState.APPLIED, NormalizedOutcomeState.SUBMITTED])),
            responses_untailored=Count('id', filter=Q(tailoring_version_id__isnull=True, normalized_state__in=[NormalizedOutcomeState.SCREENING, NormalizedOutcomeState.INTERVIEW])),
        )
        
        tailored_apps = stats['total_tailored']
        untailored_apps = stats['total_untailored']
        
        if tailored_apps < 5 or untailored_apps < 5:
            return {"status": "INSUFFICIENT_COMPARABLE_SAMPLE"}
            
        return {
            "status": "OBSERVED_ASSOCIATION",
            "tailored_response_rate": round((stats['responses_tailored'] / tailored_apps) * 100, 2),
            "untailored_response_rate": round((stats['responses_untailored'] / untailored_apps) * 100, 2),
            "confidence": ConfidenceService.calculate_confidence(tailored_apps, untailored_apps)
        }

    @classmethod
    def analyze_market_performance(cls, user: User) -> dict:
        qs = CareerOutcomeRecord.objects.filter(user=user)
        
        # Group by source_platform and provider
        source_stats = qs.values('source_platform').annotate(
            apps=Count('id', filter=Q(normalized_state__in=[NormalizedOutcomeState.APPLIED, NormalizedOutcomeState.SUBMITTED])),
            responses=Count('id', filter=Q(normalized_state__in=[NormalizedOutcomeState.SCREENING, NormalizedOutcomeState.INTERVIEW]))
        )
        
        provider_stats = qs.values('provider').annotate(
            apps=Count('id', filter=Q(normalized_state__in=[NormalizedOutcomeState.APPLIED, NormalizedOutcomeState.SUBMITTED])),
            responses=Count('id', filter=Q(normalized_state__in=[NormalizedOutcomeState.SCREENING, NormalizedOutcomeState.INTERVIEW]))
        )
        
        def process_stats(stats_qs, key_name):
            res = {}
            for s in stats_qs:
                if not s[key_name]: continue
                apps = s['apps']
                if apps < 10:
                    res[s[key_name]] = {"status": "INSUFFICIENT_SAMPLE"}
                else:
                    res[s[key_name]] = {
                        "status": "OBSERVED_ASSOCIATION",
                        "response_rate": round((s['responses'] / apps) * 100, 2),
                        "confidence": ConfidenceService.calculate_confidence(apps)
                    }
            return res
            
        return {
            "source_performance": process_stats(source_stats, 'source_platform'),
            "provider_performance": process_stats(provider_stats, 'provider')
        }

    @classmethod
    def analyze_global_market(cls, user: User) -> dict:
        qs = CareerOutcomeRecord.objects.filter(user=user)
        
        country_stats = qs.values('country').annotate(
            apps=Count('id', filter=Q(normalized_state__in=[NormalizedOutcomeState.APPLIED, NormalizedOutcomeState.SUBMITTED])),
            responses=Count('id', filter=Q(normalized_state__in=[NormalizedOutcomeState.SCREENING, NormalizedOutcomeState.INTERVIEW]))
        )
        
        res = {}
        for s in country_stats:
            if not s['country']: continue
            apps = s['apps']
            if apps < 10:
                res[s['country']] = {"status": "INSUFFICIENT_SAMPLE"}
            else:
                res[s['country']] = {
                    "status": "OBSERVED_ASSOCIATION",
                    "response_rate": round((s['responses'] / apps) * 100, 2),
                    "confidence": ConfidenceService.calculate_confidence(apps)
                }
        return {"global_market": res}
