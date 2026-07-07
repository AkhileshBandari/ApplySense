import logging
from rest_framework import views, status, permissions, generics
from rest_framework.response import Response
from .models import Job
from .serializers import JobSerializer
from .matcher import match_resume_to_job
from resumes.models import Resume
from profiles.models import Profile
from automation.scrapers import scrape_job_from_url

logger = logging.getLogger(__name__)

class JobParseView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        url = request.data.get('url')
        description_text = request.data.get('description_text')
        title = request.data.get('title')
        company = request.data.get('company')
        location = request.data.get('location', '')
        
        job = None
        
        if url:
            # Check if job was already scraped to avoid duplicate scrapers execution
            existing = Job.objects.filter(source_url=url).first()
            if existing:
                job = existing
            else:
                try:
                    scraped_data = scrape_job_from_url(url)
                    job = Job.objects.create(
                        title=scraped_data['title'],
                        company=scraped_data['company'],
                        location=scraped_data['location'],
                        portal_type=scraped_data['portal_type'],
                        source_url=url,
                        description=scraped_data['description'],
                        requirements=scraped_data['requirements']
                    )
                except Exception as e:
                    return Response({"error": f"Failed to scrape job URL: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        elif description_text and title and company:
            # Manual job insertion
            job = Job.objects.create(
                title=title,
                company=company,
                location=location,
                description=description_text
            )
        
        if not job:
            return Response({"error": "No valid job data provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Trigger matching
        try:
            profile = Profile.objects.get(user=request.user)
            resume = Resume.objects.filter(profile=profile).latest('created_at')
            match_score = match_resume_to_job(resume, job)
            return Response({"job_id": job.id, "match_score": match_score}, status=status.HTTP_200_OK)
        except Resume.DoesNotExist:
            return Response({"error": "No resume found for this user"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error during matching: {e}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
