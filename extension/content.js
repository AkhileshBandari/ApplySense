// ApplySense AI - Content Script (Scraper & Autofill Orchestrator)

(function () {
  console.log("ApplySense AI extension loaded.");

  // 1. Detect Portal Type and Scrape DOM
  function scrapeJobDetails() {
    const url = window.location.href;
    let title = "";
    let company = "";
    let description = "";
    let portalType = "Custom";

    if (url.includes("lever.co")) {
      portalType = "Lever";
      title = document.querySelector("h2")?.innerText || "";
      company = url.split("lever.co/")[1]?.split("/")[0] || "";
      description = document.querySelector(".section-wrapper")?.innerText || "";
    } else if (url.includes("greenhouse.io")) {
      portalType = "Greenhouse";
      title = document.querySelector(".app-title")?.innerText || "";
      company = document.querySelector(".company-name")?.innerText?.replace("at", "")?.strip() || "";
      description = document.querySelector("#content")?.innerText || "";
    } else if (url.includes("ashbyhq.com")) {
      portalType = "Ashby";
      title = document.querySelector("h1")?.innerText || "";
      description = document.querySelector("main")?.innerText || "";
    } else if (url.includes("linkedin.com/jobs")) {
      portalType = "LinkedIn";
      title = document.querySelector(".job-details-jobs-unified-top-card__job-title")?.innerText || "";
      company = document.querySelector(".job-details-jobs-unified-top-card__company-name")?.innerText || "";
      description = document.querySelector(".jobs-description__content")?.innerText || "";
    }

    return { title, company, description, portalType, url };
  }

  // 2. Mock profile for instant overlay evaluation (in case API is offline)
  const mockCandidateProfile = {
    name: "B. Akhilesh",
    email: "akhilesh.b@applysense.ai",
    phone: "+91 98765 43210",
    linkedin: "https://linkedin.com/in/akhilesh-b",
    github: "https://github.com/akhilesh-b",
    portfo
<truncated 6639 bytes>
