import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse

class JobSourceAdapter:
    """Base interface for fetching and normalizing jobs from different sources."""
    
    def fetch(self, url: str) -> str:
        """Fetch raw HTML or JSON payload from the source."""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def normalize(self, raw_data: str, url: str) -> Dict[str, Any]:
        """Convert raw data into a normalized dictionary matching our Job schema expectations."""
        raise NotImplementedError

    def validate(self, normalized_data: Dict[str, Any]) -> bool:
        """Verify the job has the minimum required fields to be useful."""
        required_fields = ['title', 'company', 'description']
        for field in required_fields:
            if not normalized_data.get(field):
                return False
        return True


class LeverAdapter(JobSourceAdapter):
    def normalize(self, raw_data: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(raw_data, 'html.parser')
        
        title_tag = soup.find('h2')
        title = title_tag.text.strip() if title_tag else ""
        
        company_match = re.search(r'jobs\.lever\.co/([^/]+)', url)
        company = company_match.group(1).title() if company_match else ""
        
        location_div = soup.find('div', class_='sort-by-time')
        location = location_div.text.strip() if location_div else ""
        
        description = "\n".join(div.get_text(separator="\n").strip() 
                               for div in soup.find_all('div', class_='section-wrapper'))
                               
        work_mode = "Remote" if "remote" in location.lower() or "remote" in description.lower() else "Unknown"

        return {
            "title": title,
            "company": company,
            "location": location,
            "work_mode": work_mode,
            "source": "Lever",
            "application_provider": "Lever",
            "source_url": url,
            "description": description,
        }


class GreenhouseAdapter(JobSourceAdapter):
    def normalize(self, raw_data: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(raw_data, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else ""
        
        company_meta = soup.find('meta', attrs={'name': 'twitter:site'})
        company = company_meta['content'].replace('@', '') if company_meta and company_meta.get('content') else ""
        
        location_div = soup.find('div', class_='location')
        location = location_div.text.strip() if location_div else ""
        
        content_div = soup.find('div', id='content')
        description = content_div.get_text(separator="\n").strip() if content_div else ""
        
        work_mode = "Remote" if "remote" in location.lower() else "Unknown"
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "work_mode": work_mode,
            "source": "Greenhouse",
            "application_provider": "Greenhouse",
            "source_url": url,
            "description": description,
        }


class AshbyAdapter(JobSourceAdapter):
    def normalize(self, raw_data: str, url: str) -> Dict[str, Any]:
        soup = BeautifulSoup(raw_data, 'html.parser')
        
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else ""
        
        company_tag = soup.find('a', class_='company-name')
        company = company_tag.text.strip() if company_tag else ""
        
        location_tag = soup.find('span', class_='location')
        location = location_tag.text.strip() if location_tag else ""
        
        description = "\n".join(p.text.strip() for p in soup.find_all('p'))
        
        work_mode = "Remote" if "remote" in location.lower() else "Unknown"
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "work_mode": work_mode,
            "source": "Ashby",
            "application_provider": "Ashby",
            "source_url": url,
            "description": description,
        }


class ManualCaptureAdapter(JobSourceAdapter):
    def fetch(self, url: str) -> str:
        # Manual capture data is passed directly to normalize, bypassing fetch
        return ""
        
    def normalize(self, raw_data: dict, url: str = None) -> Dict[str, Any]:
        """Expects raw_data to be a dict from the extension payload."""
        title = raw_data.get("title", "")
        company = raw_data.get("company", "")
        location = raw_data.get("location", "")
        description = raw_data.get("description", "")
        
        work_mode = "Remote" if "remote" in location.lower() or "remote" in description.lower() else "Unknown"

        return {
            "title": title,
            "company": company,
            "location": location,
            "work_mode": work_mode,
            "source": raw_data.get("source_type", "Manual"),
            "application_provider": None,
            "source_url": raw_data.get("url") or url,
            "description": description,
        }
