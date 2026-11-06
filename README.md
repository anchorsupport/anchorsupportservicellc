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

Run `python .github/site-tools/website_qa.py` with Python Playwright and its Chromium browser installed. The sweep checks internal routes and links, navigation behavior, downloads, responsive layouts, zoom widths, console errors, and key assets.

## Rebuild the public job-description PDF

Run `python .github/site-tools/build_public_job_description.py` with ReportLab installed. This creates the applicant-facing PDF in `assets/`; internal acknowledgment and staff-file mechanics are excluded.
