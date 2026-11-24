# Anchor Support Service LLC Website

This repository contains the public static website for Anchor Support Service LLC. It uses plain HTML, CSS, and JavaScript and deploys to GitHub Pages from the `main` branch through `.github/workflows/static.yml`.

## Public pages

- Home: `/`
- Housing insights and community progress: `/housing-insights/`
- Careers: `/careers/`
- Privacy Policy (canonical): `/policy.html`
- Legacy Privacy Policy URL: `/privacy-policy.html` redirects to `/policy.html`
- Secure paperwork status: `/secure-paperwork.html`

The Careers page currently announces that Anchor is not hiring or accepting new employment applications. The previous applicant job-description PDF and its generator remain in the repository but are excluded from the published site while applications are closed. New-client inquiries are open; secure online Jotform signing remains unavailable.

Housing Insights is generated from `housing-insights/housing-insights-data.json` and `housing-insights/page-template.html` by `.github/site-tools/build_housing_insights.py`. Update its `lastUpdated` value only after editorial review. Its source list is curated, not an automatic feed.

## Local website QA

The Pages workflow publishes a curated `dist/public-site` directory, not the repository root. To build and test the exact publishable file set locally, install the pinned CI tools, assemble the allowlisted output, and run the existing responsive QA suite against it:

```powershell
python -m pip install -r .github/site-tools/requirements-ci.txt
python -m playwright install chromium
python .github/site-tools/build_site.py
python .github/site-tools/website_qa.py --root dist/public-site
python -m http.server 8000 --directory dist/public-site
```

Open `http://localhost:8000/` for a local preview. The QA sweep checks internal routes and links, navigation behavior, intake and questionnaire paths, Careers closed-status content, holiday dates, responsive layouts, zoom widths, console errors, and key assets. The publish builder uses an explicit file allowlist and intentionally leaves WaiverTrack's current public landing route unchanged while the staff destination is being verified.

## Historical applicant job-description source

The previous public applicant job-description PDF and generator remain in `assets/` and `.github/site-tools/` for source reference. The PDF is not included in the public-site allowlist while Anchor is not accepting employment applications. Do not rebuild or publish it as an active vacancy without an approved hiring update.
