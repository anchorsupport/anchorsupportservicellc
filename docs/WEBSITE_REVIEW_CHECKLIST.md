# Anchor Website Release Review Checklist

Use this checklist for every proposed production release. Save dated desktop and mobile screenshots under `review-artifacts/<release-tag>/`; the public-site allowlist intentionally excludes that directory.

## Content and desktop

- [ ] Homepage says new-client inquiries are open and does not show an intake-pause notice.
- [ ] General Interest Questionnaire is visible, loads, and warns against sensitive medical/Medicaid details.
- [ ] Telephone contact and intake steps are visible and accurate.
- [ ] Appointment-only office details, business contact information, and dated holiday closure notice are accurate; remove the temporary notice after January 1, 2027.
- [ ] Services, eligibility, resources and Partners link preserve approved scope and disclaimers.
- [ ] Housing Insights figures show their geography and reporting period, link to primary sources, and label developing projects as planned; no Anchor outcomes are implied.
- [ ] Housing Insights source links, last-updated date, TSS scope and mobile card layout are current and readable.
- [ ] Careers navigation works; the no-current-openings notice is correct and no application CTA or vacancy metadata is public.
- [ ] Privacy Policy is linked in navigation/footer and reads correctly.
- [ ] Secure paperwork explains the Step 1 → review → directed Step 2 sequence and says online signing is unavailable unless explicitly verified and activated.
- [ ] No applicant-specific invite URL, PHI, employee records, internal HR mechanics, or review-only report is in the public artifact.

## Mobile and accessibility

- [ ] Review at 360, 375, 390 and 430 px; confirm no horizontal overflow.
- [ ] Mobile menu opens, closes, reaches Careers and Privacy Policy, and has a visible focus state.
- [ ] Headings, buttons, links, images and form links remain readable and operable at 200% zoom.
- [ ] Keyboard focus order is logical; skip link works; interactive controls have accessible names.
- [ ] Contrast, landmarks, page title, and heading hierarchy have no reported automated QA issues.

## Release control

- [ ] Build the allowlisted `dist/public-site`; confirm the retired applicant job-description PDF is not included.
- [ ] Run `.github/site-tools/website_qa.py --root dist/public-site` and review the full CI result.
- [ ] Review screenshot pair, changed files, source diff, links and content against approved source truth.
- [ ] Confirm no new dependencies, backend, public administrative routes, or duplicate WaiverTrack functionality.
- [ ] Obtain owner approval before merge; do not merge while required checks fail.
- [ ] After merge, record production commit SHA and annotated release tag.
- [ ] Confirm GitHub Pages workflow deployment succeeded for that SHA.
- [ ] Check the live homepage, questionnaire, telephone pathway, Partners, Careers, intake steps and Privacy Policy; confirm review artifacts return 404.
- [ ] Save final QA summary and screenshot files with the release record.
