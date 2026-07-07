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


class JobRecommendationView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        jobs = Job.objects.all().order_by("-discovered_at")[:10]

        recommendations = []

        for job in jobs:
            recommendations.append({
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "match_score": getattr(job, "match_score", 75),
            })

        return Response(
            recommendations,
            status=status.HTTP_200_OK,
        )


class JobDetailView(generics.RetrieveAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = (permissions.IsAuthenticated,)


class JobParseView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        url = request.data.get("url")
        description_text = request.data.get("description_text")
        title = request.data.get("title")
        company = request.data.get("company")
        location = request.data.get("location", "")

        job = None

        if url:
            existing = Job.objects.filter(source_url=url).first()

            if existing:
                job = existing
            else:
                try:
                    scraped_data = scrape_job_from_url(url)

                    job = Job.objects.create(
                        title=scraped_data.get("title", ""),
                        company=scraped_data.get("company", ""),
                        location=scraped_data.get("location", ""),
                        portal_type=scraped_data.get("portal_type", "Custom"),
                        source_url=url,
                        description=scraped_data.get("description", ""),
                        requirements=scraped_data.get("requirements", {}),
                    )

                except Exception as e:
                    return Response(
                        {
                            "error": f"Failed to scrape job URL: {str(e)}"
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        elif description_text and title and company:
            job = Job.objects.create(
                title=title,
                company=company,
                location=location,
                description=description_text,
            )

        if not job:
            return Response(
                {
                    "error": "No valid job data provided"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = Profile.objects.get(user=request.user)

            resume = Resume.objects.filter(
                user=request.user
            ).latest("uploaded_at")

            match_result = match_resume_to_job(
                resume.parsed_text,
                job.description,
                profile,
            )

            return Response(
                {
                    "job_id": job.id,
                    "match_result": match_result,
                },
                status=status.HTTP_200_OK,
            )

        except Resume.DoesNotExist:
            return Response(
                {
                    "error": "No resume found for this user"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Profile.DoesNotExist:
            return Response(
                {
                    "error": "Profile not found"
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except Exception as e:
            logger.exception("Job matching failed")

            return Response(
                {
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )