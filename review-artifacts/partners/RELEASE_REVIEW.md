# Anchor Intake and Partners Release Review

**Branch:** `phase2/partners`  
**Target:** `main`  
**State:** Draft PR requested; do not merge or deploy before Jotform and owner approval.

## Integrated history

This branch preserves the current main baseline and prior work in its ancestry:

- `dee39e3` — current main baseline, including Careers/Indeed recruitment updates.
- `bf3afc0` — Phase 1 static-site modernization, allowlisted Pages publishing, and QA workflow.
- `4be833e` — Phase 2 intake reopening copy and telephone fallback, with unverified signing forms withheld.
- `db1ec4e` — Partners page, site navigation, sitemap, allowlist, and QA coverage.

No old intake-pause notice was restored. Careers and Indeed links and the deployment allowlist remain intact.

## Partners page

The `/partners/` route covers landlord and property-manager coordination, tenant communication and housing stability, eviction-risk coaching and referrals, legal/financial limits, confidentiality and authorization, existing contact information, and “Additional Partnership Resources Coming Soon.” It adds no form, client database, or backend. The contact path is the existing phone and general email, expressly for general partnership inquiries; confidential client details are not requested by ordinary email.

The page makes support conditional on eligibility, the client’s service plan, authorization, and program requirements. It does not promise eviction prevention, tenant compliance, rental payments, funding, placement, or service eligibility. It states that Anchor does not provide legal advice or representation and landlords need not waive lawful standards.

## Jotform readiness: blocked pending administrator verification

The two historical forms are:

1. **Anchor Medicaid Eligibility Consent**
2. **TSS PA / Referral Paperwork**

Historical invitation-specific or prefilled-document URLs were not reused. No authenticated Jotform administration access was available, no form submissions were inspected, and no form was submitted.

An authorized Jotform administrator must verify and document all of the following before enabling online paperwork:

1. Obtain each form’s current reusable public signing URL from the live account. Confirm each link starts a new, independent session; exclude one-time invitation tokens, prefilled client documents, and links carrying identifiers or PHI in query strings.
2. Verify a current, executed HIPAA Business Associate Agreement applies to Anchor’s Jotform account, plan, forms, storage, and enabled features. Confirm which submissions and attachments it covers; do not infer coverage from a product label or a generic vendor statement.
3. Review submission privacy and separation: who can view, edit, export, download, or share each form’s responses; whether responses or attachments appear in public/shared locations; and whether access is limited to the correct authorized staff.
4. Review account access: current named staff, role permissions, authentication/MFA settings, former-staff access removal, and available access/audit history.
5. Review notifications and routing: send only minimum-necessary notifications, avoid PHI in ordinary email subjects/bodies and attachments, confirm recipients are authorized, and keep the consent and TSS PA workflows separate and correctly ordered.
6. Confirm retention, deletion, export/backups, and incident/escalation procedures for the submissions under Anchor’s applicable policies and agreements.
7. Test only with synthetic data after the account checks. Verify the links, separate sessions, notifications, routing, access, and deletion without entering or submitting actual client PHI.

Until then, the public secure-paperwork route offers a clearly labeled **Call Anchor About Intake** telephone option. It shows no online application button, does not claim that online paperwork is active, and remains `noindex, nofollow`. The branch is ready for telephone-based inquiries as a website flow; the live website has not been updated.

## Verification results

Ran the public-site builder and existing Playwright QA suite against `dist/public-site` after adding `/partners/` to the explicit allowlist.

- 60 page/viewport combinations across 360, 375, 390, 430, 768, 900, 1024, 1366, 1440, and 1920 px.
- No overflow, page errors, console errors, failed local requests, broken images, unresolved internal links, or automated accessibility smoke-test findings.
- Partners content/limitations/privacy/contact/no-form checks passed; route is in the sitemap, public allowlist, homepage callout, mobile navigation, desktop navigation, footer, Careers, Policy, secure-paperwork, and 404 navigation.
- Existing client-intake phone fallback, Careers/Indeed/PDF, Privacy Policy, contact links, and public WaiverTrack landing-route checks passed. WaiverTrack authentication was not opened or changed.
- No real client data was used; no Jotform was submitted.

### Screenshots

![Partners page on mobile](partners-mobile-full.png)

![Partners page on desktop](partners-desktop-full.png)

These review-only artifacts are outside the public-site allowlist and are not deployed.

## Release gate

**Telephone inquiry flow:** implemented and QA-passing in this branch; not live until the owner approves the PR and deployment.  
**Full online Jotform intake:** not ready. Reusable links and account/privacy controls remain unverified.  
**Production:** not ready and not deployed. Complete the Jotform administrator checklist, review the draft PR and CI results, obtain owner approval, and only then merge/deploy. After verified links are configured, rerun the full synthetic-data QA before enabling the forms.
