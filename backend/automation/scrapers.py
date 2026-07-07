import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def scrape_job_from_url(url: str) -> dict:
    """
    Detects the job portal from the URL and delegates to the appropriate scraper.
    Returns a dictionary with keys:
        title, company, location, portal_type, description, requirements
    """
    try:
        domain = urlparse(url).netloc.lower()

        if 'lever.co' in domain:
            return _scrape_lever(url)
        elif 'greenhouse.io' in domain:
            return _scrape_greenhouse(url)
        elif 'ashbyhq.com' in domain:
            return _scrape_ashby(url)
        else:
            return _scrape_generic(url)
    except Exception as e:
        logger.error(f"Failed to scrape URL {url}: {str(e)}")
        raise ValueError(f"Portal scraping failed: {str(e)}")


# ----------------------------------------------------------------------
# Lever scraper
# ----------------------------------------------------------------------
def _scrape_lever(url: str) -> dict:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    title_tag = soup.find('h2')
    title = title_tag.text.strip() if title_tag else "Job Title"

    company_match = re.search(r'jobs\.lever\.co/([^/]+)', url)
    company = company_match.group(1).title() if company_match else "Company"

    location_div = soup.find('div', class_='sort-by-time')
    location = location_div.text.strip() if location_div else "Remote"

    # Description block – concatenate all section wrappers
    description = "\n".join(div.get_text(separator="\n").strip()
                           for div in soup.find_all('div', class_='section-wrapper'))

    return {
        "title": title,
        "company": company,
        "location": location,
        "portal_type": "Lever",
        "description": description,
        "requirements": {},  # Lever does not expose a clean JSON payload
    }


# ----------------------------------------------------------------------
# Greenhouse scraper
# ----------------------------------------------------------------------
def _scrape_greenhouse(url: str) -> dict:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    title_tag = soup.find('h1')
    title = title_tag.text.strip() if title_tag else "Job Title"

    # Company name often appears in the meta tag or a div
    company = soup.find('meta', attrs={'name': 'twitter:site'})
    if company and company.get('content'):
        company = company['content']
    else:
        company = "Company"

    location = soup.find('div', class_='location')
    location = location.text.strip() if location else "Remote"

    description_section = soup.find('div', class_='content')
    description = description_section.get_text(separator="\n").strip() if description_section else ""

    # Simple requirement extraction: look for <li> under a heading containing “Requirements”
    requirements = {}
    req_heading = soup.find(lambda t: t.name in ["h2", "h3"] and "require" in t.text.lower())
    if req_heading:
        ul = req_heading.find_next_sibling('ul')
        if ul:
            requirements = {"items": [li.text.strip() for li in ul.find_all('li')]}

    return {
        "title": title,
        "company": company,
        "location": location,
        "portal_type": "Greenhouse",
        "description": description,
        "requirements": requirements,
    }


# ----------------------------------------------------------------------
# Ashby scraper (very basic – many portals require custom logic)
# ----------------------------------------------------------------------
def _scrape_ashby(url: str) -> dict:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    title = soup.find('h1').text.strip() if soup.find('h1') else "Job Title"
    company = soup.find('a', class_='company-name')
    company = company.text.strip() if company else "Company"
    location = soup.find('span', class_='location')
    location = location.text.strip() if location else "Remote"

    description = "\n".join(p.text.strip() for p in soup.find_all('p'))

    return {
        "title": title,
        "company": company,
        "location": location,
        "portal_type": "Ashby",
        "description": description,
        "requirements": {},  # Placeholder – real implementation would parse lists
    }


# ----------------------------------------------------------------------
# Generic scraper – fallback for unknown portals
# ----------------------------------------------------------------------
def _scrape_generic(url: str) -> dict:
    """
    Naïve generic scraper – extracts the <title> and body text.
    """
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    title_tag = soup.find('title')
    title = title_tag.text.strip() if title_tag else "Job Title"

    # Very simple description extraction – all visible text
    description = "\n".join(
        elem.get_text(separator="\n", strip=True)
        for elem in soup.find_all(['p', 'li', 'h2', 'h3'])
    )

    return {
        "title": title,
        "company": "Company",
        "location": "Remote",
        "portal_type": "Generic",
        "description": description,
        "requirements": {},
    }
