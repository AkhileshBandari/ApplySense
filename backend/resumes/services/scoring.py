import re
from typing import Dict, List, Any

class ResumeScoringService:
    @staticmethod
    def calculate_general_score(parsed_data: Dict[str, Any], raw_text: str) -> Dict[str, Any]:
        """
        Calculate deterministic general resume score.
        Score dimensions:
        - Content Completeness (20)
        - Experience Presentation (20)
        - Impact & Metrics (20)
        - Formatting/Readability (20)
        - Skills Presentation (20)
        """
        dimensions = []
        total_score = 0
        issues = []

        # 1. Content Completeness (Max 20)
        comp_score = 20
        missing = []
        if not parsed_data.get('contact', {}).get('email'):
            comp_score -= 5
            missing.append("Email missing")
            issues.append({"severity": "FAIL", "issue": "Missing contact email", "category": "Completeness"})
        if not parsed_data.get('experience'):
            if not parsed_data.get('projects') and not parsed_data.get('education'):
                comp_score -= 15
                issues.append({"severity": "FAIL", "issue": "Missing experience and projects", "category": "Completeness"})
            else:
                # Fresher: don't penalize heavily if projects exist
                comp_score -= 5
        
        dimensions.append({
            "name": "Content Completeness",
            "score": max(0, comp_score),
            "max_score": 20,
            "evidence": "Checked contact info, experience, projects, education",
            "issues": missing
        })
        total_score += max(0, comp_score)

        # 2. Impact & Metrics (Max 20)
        impact_score = 0
        metrics_found = 0
        # Simple heuristic: find numbers or % in text, particularly in bullet points
        metrics_pattern = r'\b\d+%\b|\b\d+\+\b|\$\d+[kKmMbB]?\b'
        matches = re.findall(metrics_pattern, raw_text)
        metrics_found = len(matches)
        
        if metrics_found >= 5:
            impact_score = 20
        elif metrics_found > 0:
            impact_score = 10 + (metrics_found * 2)
        else:
            impact_score = 5
            issues.append({"severity": "WARNING", "issue": "No quantifiable metrics found", "category": "Impact"})
            
        dimensions.append({
            "name": "Impact & Metrics",
            "score": impact_score,
            "max_score": 20,
            "evidence": f"Found {metrics_found} quantifiable metrics (%, $, numbers)",
            "issues": [] if impact_score == 20 else ["Consider adding quantifiable impact"]
        })
        total_score += impact_score

        # 3. Skills Presentation (Max 20)
        skills = parsed_data.get('skills', [])
        skill_score = 20
        if not skills:
            skill_score = 0
            issues.append({"severity": "FAIL", "issue": "No skills section found", "category": "Skills"})
        elif len(skills) < 3:
            skill_score = 10
            issues.append({"severity": "WARNING", "issue": "Very few skills listed", "category": "Skills"})
        elif len(skills) > 30:
            skill_score = 15
            issues.append({"severity": "WARNING", "issue": "Too many skills listed (potential keyword stuffing)", "category": "Skills"})
            
        dimensions.append({
            "name": "Skills Presentation",
            "score": skill_score,
            "max_score": 20,
            "evidence": f"Found {len(skills)} skills",
            "issues": []
        })
        total_score += skill_score

        # 4. formatting/readability (Max 20)
        format_score = 20
        word_count = len(raw_text.split())
        if word_count < 100:
            format_score = 5
            issues.append({"severity": "FAIL", "issue": "Resume is extremely short", "category": "Formatting"})
        elif word_count > 1000:
            format_score -= 10
            issues.append({"severity": "WARNING", "issue": "Resume is excessively long (>1000 words)", "category": "Formatting"})
            
        dimensions.append({
            "name": "Formatting & Readability",
            "score": max(0, format_score),
            "max_score": 20,
            "evidence": f"Word count: {word_count}",
            "issues": []
        })
        total_score += max(0, format_score)
        
        # 5. Experience Presentation (Max 20)
        exp_score = 20
        experiences = parsed_data.get('experience', [])
        if experiences:
            # Check for descriptions
            missing_desc = [e.get('company') for e in experiences if not e.get('description')]
            if missing_desc:
                exp_score -= 10
                issues.append({"severity": "WARNING", "issue": f"Missing descriptions for {len(missing_desc)} roles", "category": "Experience"})
        else:
            projects = parsed_data.get('projects', [])
            if not projects:
                exp_score = 0
            else:
                missing_desc = [p.get('name') for p in projects if not p.get('description')]
                if missing_desc:
                    exp_score -= 10

        dimensions.append({
            "name": "Experience & Project Presentation",
            "score": max(0, exp_score),
            "max_score": 20,
            "evidence": f"Checked {len(experiences)} experiences and {len(parsed_data.get('projects', []))} projects",
            "issues": []
        })
        total_score += max(0, exp_score)

        return {
            "overall_score": total_score,
            "dimensions": dimensions,
            "issues": issues,
            "calculation_version": "v1.0"
        }
