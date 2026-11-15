# Anchor Support Service LLC Website

This repository contains the public static website for Anchor Support Service LLC. It uses plain HTML, CSS, and JavaScript and deploys to GitHub Pages from the `main` branch through `.github/workflows/static.yml`.

## Public pages

- Home: `/`
- Careers: `/careers/`
- Privacy Policy (canonical): `/policy.html`
- Legacy Privacy Policy URL: `/privacy-policy.html` redirects to `/policy.html`
- Secure paperwork status: `/secure-paperwork.html`

The public Careers page links to the applicant-facing job description in `assets/`. The current new-client intake pause remains in place.

## Local website QA

The Pages workflow publishes a curated `dist/public-site` directory, not the repository root. To build and test the exact publishable file set locally, install the pinned CI tools, generate the public PDF, assemble the allowlisted output, and run the existing responsive QA suite against it:

```powershell
python -m pip install -r .github/site-tools/requirements-ci.txt
python -m playwright install chromium
python .github/site-tools/build_public_job_description.py
python .github/site-tools/build_site.py
python .github/site-tools/website_qa.py --root dist/public-site
python -m http.server 8000 --directory dist/public-site
```

Open `http://localhost:8000/` for a local preview. The QA sweep checks internal routes and links, navigation behavior, downloads, responsive layouts, zoom widths, console errors, and key assets. The publish builder uses an explicit file allowlist and intentionally leaves WaiverTrack's current public landing route unchanged while the staff destination is being verified.

## Rebuild the public job-description PDF

Run `python .github/site-tools/build_public_job_description.py` with ReportLab installed. This creates the applicant-facing PDF in `assets/`; internal acknowledgment and staff-file mechanics are excluded.
