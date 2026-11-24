# Website Repository Instructions

## Source and production

- Repository: `anchorsupport/anchorsupportservicellc`.
- `main` is the production branch; GitHub Pages is configured to publish through GitHub Actions.
- This is the existing static HTML, CSS, and JavaScript site. Keep its structure, brand assets, routes, and public-site allowlist. Do not add a framework or backend.

## Build and QA

Run these from the repository root before proposing or publishing site changes:

```powershell
python .github/site-tools/build_site.py
python .github/site-tools/website_qa.py --root dist/public-site
```

The CI workflow installs `.github/site-tools/requirements-ci.txt`, installs Playwright Chromium, builds `dist/public-site`, and runs the same QA suite. Do not weaken checks to make a change pass. Review generated output and never commit `dist/` or Python `__pycache__` artifacts.

## Change and release flow

1. Start from the latest `origin/main` in a dedicated branch or worktree. Preserve unrelated local changes.
2. Make the smallest source changes needed and run the build and full QA suite.
3. Push the branch and open a PR targeting `main`. Merge only after required CI checks pass and the owner has authorized publication.
4. If the GitHub app/API integration returns `403 Resource not accessible by integration`, do not repeat that same write call. Check whether `gh` is available and authenticated. If not, Git may still be authenticated through Git Credential Manager; verify its GitHub account and use that existing credential for the requested GitHub operation without printing, logging, committing, or storing the credential. Never ask for or paste a password or token in chat.
5. Respect branch protection and repository rules. Do not disable security settings or force-push to work around a restriction. If the authenticated account cannot perform a required action, report the specific missing permission or owner action.
6. For future routine edits, the owner’s explicit request to publish authorizes the normal tested release workflow; it does not authorize bypassing failing checks, protection rules, or security review.

## Production verification

- Confirm the successful `Build and QA public site` and `Deploy verified site` jobs for the exact `main` commit.
- Open the live page routes affected by the release and verify their content, links, assets, and responsive navigation. A pushed commit or successful build alone is not proof of deployment.
- Report the commit SHA, Actions run URL, verified live routes, and any remaining blocker. Do not claim deployment when the Deploy job failed or live content is stale.

## Public-content safeguards

- Keep unverified Jotform invitation/signing links inactive. Do not test with real client information.
- Do not publish internal, applicant-specific, staff, or client data. Preserve existing intake, privacy, eligibility, and employment facts unless an authorized source explicitly changes them.
- Keep temporary review screenshots, build output, reports, and other development artifacts out of the public-site allowlist and production commits.
