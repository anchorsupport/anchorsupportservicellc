# Anchor Support Service Website Master

The `main` branch of `anchorsupport/anchorsupportservicellc` is the source of truth for the public website. Production uses GitHub Pages with the GitHub Actions build source. The allowlisted public artifact is assembled in `dist/public-site` by `.github/site-tools/build_site.py`; do not publish the repository root directly.

## Approved structure and source files

| Public area | Source of truth |
| --- | --- |
| Homepage, service/eligibility content, intake availability, contact, questionnaire, office location, navigation and footer | `index.html` |
| Shared branding, layout, responsive behavior, mobile navigation and focus styles | `styles.css`, `script.js` |
| Logo, favicon, founder photo and public service photos | `anchor-logo.png`, `anchor-logo-display.webp`, `anchor-favicon.png`, `alex-ceo-picture.png`, `alex-ceo-picture-display.webp`, `scotty-housing-navigator.jpg`, `scotty-housing-navigator pic.jpg` |
| Careers status announcement | `careers/index.html`; the homepage no-openings callout is in `index.html`; the previous applicant PDF is retained in the repository but excluded from the public-site allowlist while applications are closed. |
| Landlord and community partner information | `partners/index.html` |
| Privacy policy and its compatibility route | `policy.html`, `privacy-policy.html` |
| Telephone inquiry and two-step paperwork instructions | `secure-paperwork.html` |
| WaiverTrack public landing route | `waivertrack/index.html`; do not change the protected application/authentication from this public-site master |
| Public routes and search indexing | `sitemap.xml`, `robots.txt`, `404.html`, `CNAME` |
| Public file allowlist and publishing protections | `.github/site-tools/build_site.py`, `.github/workflows/static.yml`, `_config.yml` |
| Build and responsive/link/privacy checks | `.github/site-tools/website_qa.py`, `.github/site-tools/requirements-ci.txt` |

## Approved navigation and branding

The shared primary navigation is Home, Services, Eligibility, Who We Support, Resources, Contact, Partners, Careers, and Privacy Policy. Keep existing section IDs and routes so bookmarks continue to work. The footer repeats important section, Careers, Partners, Privacy Policy, and contact links. The visual identity uses Anchor navy (`#00335f`), teal (`#0c747d`), bright teal (`#2fc7bf`), coral (`#f25f4c`), gold (`#e9a93a`), and cream backgrounds. Preserve the existing Anchor logo and image appearance; display WebP derivatives are for the website while original assets remain available for print/PDF source use.

## Public business information

The contact section in `index.html` is the source for business contact details: (406) 219-7035, fax (406) 540-7982, `info@anchorsupportservice.com`, Monday through Friday, 8:00 AM?5:00 PM by appointment only, and the Missoula office at 3010 Santa Fe Ct, Suite 208. The temporary holiday notice is in `#holiday-office-closures`; review and remove it after January 1, 2027. The mailing address is PO Box 17021, 3150 Great Northern Loop, Missoula, Montana 59808-7021. Verify factual changes with the owner before publishing them.

## Careers, partners and intake

- Anchor is not currently hiring and is not accepting new employment applications. `careers/index.html` contains the approved announcement. Do not publish an active vacancy, application link, or old job-description PDF while this status remains in effect.
- The Partners page explains landlord/property-manager coordination, housing stability, confidentiality, scope limitations, and future partnership resources.
- New-client inquiries are open. The General Interest Questionnaire is for general inquiries only and must not solicit sensitive health or Medicaid information. Telephone intake remains available through the listed business phone.
- The original workflow is Step 1 Medicaid Eligibility Consent, then Medicaid review, then Step 2 TSS referral/PA paperwork when Anchor directs the applicant to proceed. The current public `secure-paperwork.html` page states that online paperwork is not yet available. Do not activate historical or applicant-specific Jotform invite links until reusable blank signing sessions, applicant isolation, routing, notifications, and HIPAA/BAA coverage have been verified by the administrator and approved by the owner.

## Build, test and publish

GitHub Actions workflow `.github/workflows/static.yml` assembles the allowlisted site, runs the complete responsive/public-site QA suite, and deploys only the verified artifact to GitHub Pages. The former applicant job-description PDF is not included in public output while there are no openings. Pages is configured with `build_type: workflow`. `_config.yml` excludes review and development artifacts if branch/Jekyll mode is ever re-enabled. Do not add broad `git add .` deploy flows or use repository-root Pages publishing.

Run locally from the repository root:

```powershell
python -m pip install -r .github/site-tools/requirements-ci.txt
python .github/site-tools/build_site.py
python .github/site-tools/website_qa.py --root dist/public-site
```

The QA suite checks 11 viewport widths from 320 through 1920 px; route/asset/link integrity; intake and questionnaire pathways; the no-openings Careers status and absence of active application links; holiday dates and office-hours placement; Partners; mobile menu and Privacy Policy access; console and page errors; accessibility basics; and inactive Jotform safeguards.

## Release archive and rollback

Approved release source archives are available from GitHub's version-specific tag archive endpoint:

`https://github.com/anchorsupport/anchorsupportservicellc/archive/refs/tags/<release-tag>.zip`

The approved intake inquiry deployment is tagged `release-2026-11-18-intake-inquiries-open`. The prior production baseline is tagged `production-baseline-2026-11-18`. Tag archives retain source references and the files for that exact commit.

To roll back, create a new branch from `main`, revert the release commit (or cherry-pick the desired approved tag content into a new commit), run the same build and QA workflow, and open a reviewed pull request to `main`. Merge only after owner approval and CI success. GitHub Pages then deploys the tested artifact. Verify the live homepage, contact/form link, Careers, Partners, intake and policy routes. Never reset or force-push `main`, and do not rerun an old workflow artifact as a substitute for changing the source branch.

## Persistent visual preview setup

No Cloudflare Pages project or preview URL has been created yet. Once an authorized Cloudflare account administrator connects the repository:

1. In Cloudflare Dashboard, open **Workers & Pages → Create application → Pages → Connect to Git** and authorize the `anchorsupport/anchorsupportservicellc` repository.
2. Name the project `anchorsupportservicellc-review`; set production branch to `main`, Framework preset to **None**, and root directory to `/`.
3. Set build command to `python -m pip install -r .github/site-tools/requirements-ci.txt && python .github/site-tools/build_public_job_description.py && python .github/site-tools/build_site.py`; set build output directory to `dist/public-site`.
4. Set `PYTHON_VERSION=3.12` in Pages environment variables. Enable branch preview deployments for `phase2/partners` and proposed review branches.
5. Do not configure `anchorsupportservice.com` or `www.anchorsupportservice.com` as a Pages custom domain. If preview confidentiality is needed, protect preview deployments with Cloudflare Access; verify every preview URL is protected before sharing. Test only synthetic information and keep unverified signing links out of previews.
6. The Pages project will show the actual `*.pages.dev` URL after first successful deployment. Record that URL and its branch-specific previews in the release report; do not guess a URL before creation.

The current successful production deployment remains on GitHub Pages at `https://anchorsupportservice.com/`; no Cloudflare preview URL is asserted.
