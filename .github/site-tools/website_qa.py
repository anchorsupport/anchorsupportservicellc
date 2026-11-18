from __future__ import annotations

from collections import Counter
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urldefrag, urljoin, urlparse
import json
import re
import tempfile

from playwright.sync_api import sync_playwright

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
PAGES = ["/", "/careers/", "/partners/", "/policy.html", "/secure-paperwork.html", "/404.html"]
VIEWPORTS = [360, 375, 390, 430, 768, 900, 1024, 1366, 1440, 1920]
EXTERNAL_EXPECTED = {
    "https://www.dphhs.mt.gov/medicaidchanges/",
    "https://dphhs.mt.gov/heartwaiver",
    "https://apply.mt.gov/access/jsp/access/Home.jsp",
    "https://www.ci.missoula.mt.us/3104/Missoula-Coordinated-Entry-System-MCES",
    "https://www.missoulahousing.org/",
    "https://montana211.org/",
    "https://humanresourcecouncil.org/",
    "https://montanafairhousing.org/",
    "https://www.hud.gov/",
    "https://mountainline.com/",
    "https://www.indeed.com/viewjob?jk=b645ab34482aea27",
    "https://docs.google.com/forms/d/e/1FAIpQLSeae9eGYlUxB4MeFz2V6wtrWI_awH7uM_E0AykRIPcDMjRBGQ/viewform",
}

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def main():
    parser = argparse.ArgumentParser(description="Run responsive and link QA against a static website directory.")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Directory to serve and test (defaults to the repository root).")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "index.html").is_file():
        parser.error(f"--root must contain index.html: {root}")
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *server_args, **kwargs: QuietHandler(*server_args, directory=str(root), **kwargs))
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}"
    results = {"pages": [], "overflow": [], "page_errors": [], "console_errors": [], "failed_local_requests": [], "broken_images": [], "internal_links": [], "external_links": [], "journeys": {}, "accessibility": []}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            page.on("pageerror", lambda error: results["page_errors"].append(str(error)))
            page.on("console", lambda msg: results["console_errors"].append(msg.text) if msg.type == "error" else None)
            page.on("requestfailed", lambda request: results["failed_local_requests"].append(request.url) if request.url.startswith(base) else None)

            for width in VIEWPORTS:
                for path in PAGES:
                    page.set_viewport_size({"width": width, "height": 900 if width >= 768 else 844})
                    response = page.goto(base + path, wait_until="networkidle")
                    if response is None or response.status != 200:
                        results["pages"].append({"path": path, "width": width, "status": response.status if response else None})
                        continue
                    page.evaluate("""async () => {
                      const images = [...document.images];
                      images.forEach(image => { image.loading = 'eager'; });
                      await Promise.all(images.map(image => image.decode().catch(() => {})));
                    }""")
                    state = page.evaluate("""() => ({inner:innerWidth, doc:document.documentElement.scrollWidth, body:document.body.scrollWidth, title:document.title, h1:[...document.querySelectorAll('h1')].map(x=>x.innerText), broken:[...document.images].filter(x=>!x.complete || !x.naturalWidth).map(x=>x.currentSrc), duplicateIds:[...document.querySelectorAll('[id]')].map(x=>x.id).filter((x,i,a)=>a.indexOf(x)!==i), unnamed:[...document.querySelectorAll('a,button')].filter(x=>!(x.innerText||x.getAttribute('aria-label')||x.getAttribute('title'))).map(x=>x.outerHTML.slice(0,120))})""")
                    results["pages"].append({"path": path, "width": width, "status": response.status, "title": state["title"]})
                    if state["doc"] > state["inner"] + 1 or state["body"] > state["inner"] + 1:
                        results["overflow"].append({"path": path, "width": width, **state})
                    if state["broken"]:
                        results["broken_images"].append({"path": path, "width": width, "images": state["broken"]})
                    if state["duplicateIds"]:
                        results["accessibility"].append({"path": path, "issue": "duplicate_ids", "ids": state["duplicateIds"]})
                    if state["unnamed"]:
                        results["accessibility"].append({"path": path, "issue": "unnamed_controls", "items": state["unnamed"]})
                    if len(state["h1"]) != 1:
                        results["accessibility"].append({"path": path, "issue": "h1_count", "count": len(state["h1"])})

                    if path == "/policy.html":
                        page.evaluate("window.scrollTo(0, Math.floor(document.documentElement.scrollHeight / 2))")
                        policy_state = page.evaluate("""() => {
                          const wrapper = document.querySelector('.policy-section');
                          const panel = document.querySelector('#mobile-information');
                          const wrapperStyle = getComputedStyle(wrapper);
                          const panelStyle = getComputedStyle(panel);
                          return {
                            wrapperOpacity: wrapperStyle.opacity,
                            wrapperVisibility: wrapperStyle.visibility,
                            panelOpacity: panelStyle.opacity,
                            panelVisibility: panelStyle.visibility,
                            panelHeight: panel.getBoundingClientRect().height,
                            panelTextLength: panel.innerText.length,
                            scrollY,
                          };
                        }""")
                        if policy_state["wrapperOpacity"] != "1" or policy_state["wrapperVisibility"] != "visible" or policy_state["panelOpacity"] != "1" or policy_state["panelVisibility"] != "visible" or policy_state["panelHeight"] <= 0 or policy_state["panelTextLength"] < 100:
                            results["accessibility"].append({"path": path, "width": width, "issue": "policy_content_not_visible_midpage", **policy_state})

                    if width in (360, 375, 390, 430, 768, 900, 1024):
                        toggle = page.locator(".nav-toggle")
                        if not toggle.is_visible():
                            results["accessibility"].append({"path": path, "width": width, "issue": "mobile_menu_toggle_hidden"})
                        else:
                            toggle.click()
                            if toggle.get_attribute("aria-expanded") != "true":
                                results["accessibility"].append({"path": path, "width": width, "issue": "aria_expanded_not_set"})
                            if not page.locator('.site-nav a[href="/careers/"]').is_visible():
                                results["accessibility"].append({"path": path, "width": width, "issue": "careers_missing_from_mobile_menu"})
                            if not page.locator('.site-nav a[href="/partners/"]').is_visible():
                                results["accessibility"].append({"path": path, "width": width, "issue": "partners_missing_from_mobile_menu"})
                            if not page.locator('.site-nav a[href="/policy.html"]').is_visible():
                                results["accessibility"].append({"path": path, "width": width, "issue": "privacy_missing_from_mobile_menu"})
                            toggle.click()
                            if toggle.get_attribute("aria-expanded") != "false":
                                results["accessibility"].append({"path": path, "width": width, "issue": "mobile_menu_did_not_close"})
                    if width >= 1366:
                        if not page.locator('.site-nav a[href="/careers/"]').is_visible():
                            results["accessibility"].append({"path": path, "width": width, "issue": "careers_missing_from_desktop_nav"})
                        if not page.locator('.site-nav a[href="/partners/"]').is_visible():
                            results["accessibility"].append({"path": path, "width": width, "issue": "partners_missing_from_desktop_nav"})
                        if page.locator(".nav-toggle").is_visible():
                            results["accessibility"].append({"path": path, "width": width, "issue": "desktop_menu_toggle_visible"})

            # Validate every local link target and every in-page fragment in the public HTML pages.
            external_found = set()
            for path in PAGES + ["/careers/index.html"]:
                response = page.goto(base + path, wait_until="networkidle")
                if not response or response.status != 200:
                    continue
                links = page.locator("a[href]").evaluate_all("els => els.map(a => ({href:a.getAttribute('href'), target:a.getAttribute('target'), rel:a.getAttribute('rel')}))")
                ids = set(page.locator("[id]").evaluate_all("els => els.map(x=>x.id)"))
                for link in links:
                    href = link["href"] or ""
                    absolute = urljoin(page.url, href)
                    parts = urlparse(absolute)
                    if parts.scheme in ("mailto", "tel"):
                        allowed_mailboxes = {"info@anchorsupportservice.com"}
                        if parts.scheme == "mailto" and parts.path.lower() not in allowed_mailboxes:
                            results["internal_links"].append({"source": path, "href": href, "issue": "unexpected_mailto"})
                        if parts.scheme == "tel" and re.sub(r"\D", "", parts.path) != "4062197035":
                            results["internal_links"].append({"source": path, "href": href, "issue": "unexpected_tel"})
                        continue
                    if parts.scheme not in ("http", "https"):
                        continue
                    if parts.netloc != urlparse(base).netloc:
                        if parts.netloc.endswith("anchorsupportservice.com"):
                            continue
                        external_found.add(urldefrag(absolute)[0])
                        if link["target"] == "_blank" and not {"noopener", "noreferrer"}.issubset(set((link["rel"] or "").split())):
                            results["accessibility"].append({"source": path, "issue": "unsafe_new_tab_link", "href": href})
                        continue
                    local = urldefrag(absolute)[0]
                    check = page.request.get(local)
                    if check.status != 200:
                        results["internal_links"].append({"source": path, "href": href, "status": check.status})
                    fragment = parts.fragment
                    target_path = parts.path or "/"
                    # Resolve same-page fragments in the currently loaded source document.
                    if fragment and target_path.rstrip("/") == urlparse(page.url).path.rstrip("/"):
                        if fragment not in ids:
                            results["internal_links"].append({"source": path, "href": href, "issue": "missing_fragment"})
                    elif fragment and target_path in ("", "/"):
                        home_html = (root / "index.html").read_text(encoding="utf-8-sig")
                        if not re.search(rf'\bid=["\']{re.escape(fragment)}["\']', home_html):
                            results["internal_links"].append({"source": path, "href": href, "issue": "missing_home_fragment"})

            # Email/phone links and external references from the homepage and Careers page.
            if not EXTERNAL_EXPECTED.issubset(external_found):
                results["internal_links"].append({"issue": "missing_expected_external_links", "missing": sorted(EXTERNAL_EXPECTED - external_found)})
            results["external_links"] = [{"url": url, "present": True} for url in sorted(external_found)]

            # Check standalone assets and the protected portal landing route without following sign-in.
            required_assets = ["/styles.css", "/script.js", "/anchor-logo.png", "/anchor-logo-display.webp", "/anchor-favicon.png", "/alex-ceo-picture.png", "/alex-ceo-picture-display.webp", "/assets/anchor-support-housing-navigator-tenancy-support-specialist-job-description.pdf"]
            for asset in required_assets:
                response = page.request.get(base + asset)
                if response.status != 200:
                    results["failed_local_requests"].append({"asset": asset, "status": response.status})
            portal = page.request.get(base + "/waivertrack/")
            results["journeys"]["waivertrack_public_route"] = {"status": portal.status, "checked_login": False}
            missing_route = page.request.get(base + "/qa-route-that-does-not-exist")
            results["journeys"]["missing_route"] = {"status": missing_route.status}
            if missing_route.status != 404:
                results["internal_links"].append({"issue": "missing_route_did_not_return_404", "status": missing_route.status})

            # Required applicant journey at mobile and desktop sizes.
            for width, label in [(390, "mobile"), (1366, "desktop")]:
                page.set_viewport_size({"width": width, "height": 900 if width >= 768 else 844})
                page.goto(base + "/", wait_until="networkidle")
                hiring_visible = page.get_by_text("Now hiring", exact=False).first.is_visible()
                page.get_by_role("link", name="View Career Opportunity").click()
                on_careers = urlparse(page.url).path == "/careers/" and page.get_by_role("heading", name="Housing Navigator / Tenancy Support Specialist").count() == 1
                text = page.locator("body").inner_text()
                content_present = all(s in text for s in ["Minimum qualifications", "Preferred qualifications", "What the work can look like", "$17.00-$18.00", "$18.00-$20.00", "twelve (12) months", "no guaranteed minimum paid hours"])
                apply_button = page.locator('a.button[aria-label^="Apply on Indeed"]').first
                apply_top = apply_button.evaluate("element => element.getBoundingClientRect().top")
                pay_top = page.locator(".careers-hero-pay").evaluate("element => element.getBoundingClientRect().top")
                compact_intro = page.locator(".careers-hero-intro-compact").is_visible() if width <= 600 else True
                apply_early = apply_top < pay_top and (width > 600 or apply_top < page.evaluate("innerHeight"))
                download_link = page.get_by_role("link", name="Download Job Description (PDF)").first
                href = download_link.get_attribute("href")
                with page.expect_download() as download_info:
                    download_link.click()
                download = download_info.value
                with tempfile.TemporaryDirectory() as d:
                    target = Path(d) / download.suggested_filename
                    download.save_as(target)
                    download_ok = target.read_bytes().startswith(b"%PDF-") and target.stat().st_size > 1000
                indeed_links = page.locator('a.button[aria-label^="Apply on Indeed"]').evaluate_all("els => els.map(x => ({href:x.href, target:x.target, rel:x.rel}))")
                indeed_ok = len(indeed_links) == 2 and all(link["href"] == "https://www.indeed.com/viewjob?jk=b645ab34482aea27" and link["target"] == "_blank" and {"noopener", "noreferrer"}.issubset(set(link["rel"].split())) for link in indeed_links) and page.locator('a[href^="mailto:alex@"]').count() == 0 and "All employment applications are processed through Indeed. Please submit your resume and application using the link above. Employment applications are not accepted through our general contact form or business email." in text and page.get_by_role("heading", name="Careers at Anchor Support Service").count() == 1 and "Community-Based and Approved Remote Work" in text and "Help individuals experiencing homelessness or housing instability obtain and maintain housing through housing assessments, individualized planning, housing searches, rental applications, landlord communication, community resource coordination, and ongoing tenancy support." in text
                menu_policy_ok = True
                if width <= 768:
                    page.locator(".nav-toggle").click()
                    page.locator('.site-nav a[href="/policy.html"]').click()
                    menu_policy_ok = urlparse(page.url).path == "/policy.html" and page.get_by_role("heading", name="Privacy Policy").count() == 1
                else:
                    page.locator('.footer-nav a[href="/policy.html"]').click()
                    menu_policy_ok = urlparse(page.url).path == "/policy.html" and page.get_by_role("heading", name="Privacy Policy").count() == 1
                page.goto(base + "/policy.html", wait_until="networkidle")
                policy_text = page.locator("main").inner_text()
                policy_ok = "Information We May Collect" in policy_text and "Children's Privacy" in policy_text and "Contact Information" in policy_text
                page.locator('.policy-toc a[href="#contact-information"]').click()
                policy_contact_ok = page.locator("#contact-information").is_visible() and page.locator('#contact-information a[href="mailto:info@anchorsupportservice.com"]').count() == 1 and page.locator('#contact-information a[href="tel:4062197035"]').count() == 1
                page.goto(base + "/#contact", wait_until="networkidle")
                contact_text = page.locator("#contact").inner_text()
                office_text = page.locator(".office-update-card").inner_text()
                questionnaire = page.locator('#contact a[href="https://docs.google.com/forms/d/e/1FAIpQLSeae9eGYlUxB4MeFz2V6wtrWI_awH7uM_E0AykRIPcDMjRBGQ/viewform"]')
                contact_ok = all(s in contact_text for s in ["(406) 219-7035", "(406) 540-7982", "info@anchorsupportservice.com", "accepting new-client inquiries", "3010 Santa Fe Ct, Suite 228", "By Appointment Only", "Walk-ins are not available", "PO Box 17021", "3150 Great Northern Loop", "General Interest Questionnaire", "not a secure Medicaid enrollment form", "Do not submit sensitive medical, Medicaid, or identifying information"]) and all(s.casefold() in office_text.casefold() for s in ["Office Location Update", "3010 Santa Fe Ct, Suite 228", "By Appointment Only", "Walk-ins are not available"]) and questionnaire.count() == 1 and questionnaire.get_attribute("target") == "_blank" and "noopener" in (questionnaire.get_attribute("rel") or "") and page.locator('#contact a[href="tel:4062197035"]').count() >= 1 and page.locator('#contact a[href="secure-paperwork.html"]').inner_text() == "View Intake Steps" and page.locator('#contact a[href^="https://www.google.com/maps/search/"]').count() == 1 and page.locator('.office-update-card a[href^="https://www.google.com/maps/search/"]').count() == 1
                page.goto(base + "/policy.html", wait_until="networkidle")
                overflow_after_zoom = []
                for zoom_width in [int(width/1.25), int(width/2)] if width <= 430 else []:
                    page.set_viewport_size({"width": zoom_width, "height": 844})
                    z = page.evaluate("({inner:innerWidth,scroll:document.documentElement.scrollWidth})")
                    if z["scroll"] > z["inner"] + 1:
                        overflow_after_zoom.append({"width": zoom_width, **z})
                results["journeys"][label] = {"hiring_visible": hiring_visible, "careers_navigation": on_careers, "position_content": content_present, "pdf_download": download_ok, "pdf_href": href, "indeed_application": indeed_ok, "mobile_intro_compact": compact_intro, "apply_button_visible_early": apply_early, "mobile_menu_to_policy": menu_policy_ok, "policy_readable": policy_ok, "policy_contact_section": policy_contact_ok, "contact_links_intake_notice_and_questionnaire": contact_ok, "zoom_overflow": overflow_after_zoom}

            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(base + "/", wait_until="networkidle")
            intake_notice_ok = "New client inquiries are open." in page.locator(".intake-notice").inner_text() and page.locator('.intake-notice').count() == 1
            page.goto(base + "/secure-paperwork.html", wait_until="networkidle")
            secure_meta = page.locator('meta[name="robots"]').get_attribute("content")
            secure_text = page.locator("main").inner_text()
            steps_text = page.locator(".paperwork-step").evaluate_all("els => els.map(el => el.textContent)")
            steps_text = " ".join(steps_text).strip()
            secure_html = (root / "secure-paperwork.html").read_text(encoding="utf-8").casefold()
            secure_online_unavailable = "online paperwork is not yet available" in secure_text.casefold()
            no_published_jotform_link = "jotform.com" not in secure_html and "/invite/" not in secure_html
            secure_intake_ok = secure_meta == "noindex, nofollow" and all(s in secure_text + " " + steps_text for s in ["Step 1", "Medicaid Eligibility Consent", "Step 2", "TSS Prior Authorization Paperwork", "only after Medicaid eligibility has been reviewed", "does not guarantee eligibility, Medicaid authorization, housing assistance"]) and secure_online_unavailable and no_published_jotform_link and page.locator(".paperwork-step").count() == 2 and page.locator("iframe").count() == 0 and page.locator("form").count() == 0 and page.locator('a[href="tel:4062197035"]').count() >= 1 and page.locator('a[href^="https://www.jotform.com/"]').count() == 0
            stale_pause_copy = re.compile(r"paused from accepting new clients|new client pause|intake (?:is )?paused|paperwork (?:is )?paused", re.I)
            public_html = [root / "index.html", root / "careers" / "index.html", root / "secure-paperwork.html"]
            no_stale_intake_pause = all(not stale_pause_copy.search(file.read_text(encoding="utf-8")) for file in public_html)
            results["journeys"]["new_client_intake"] = {"homepage_notice": intake_notice_ok, "secure_steps_and_online_forms_unavailable": secure_intake_ok, "no_jotform_or_invitation_links_published": no_published_jotform_link, "secure_route_noindex_nofollow": secure_meta == "noindex, nofollow", "no_stale_pause_copy": no_stale_intake_pause}

            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(base + "/", wait_until="networkidle")
            home_partner_link = page.locator('.partner-callout a[href="/partners/"]').count() == 1
            page.goto(base + "/partners/", wait_until="networkidle")
            partner_text = page.locator("main").inner_text()
            partner_content_ok = all(s in partner_text for s in ["Supporting Successful Tenancies. Strengthening Landlord Relationships.", "Communication Support", "Eviction Risk Reduction", "Lease Education", "Housing Stability", "Community Coordination", "WHEN A TENANCY IS AT RISK", "Communication coaching", "Help organizing housing notices and paperwork", "Budgeting and housing-retention planning", "qualified legal assistance", "Anchor does not directly pay ongoing rent or rental arrears.", "does not guarantee rental payments or co-sign leases", "does not provide legal advice or legal representation", "not a landlord, property manager, or enforcement agency", "cannot guarantee tenant compliance or specific housing outcomes", "cannot guarantee financial assistance or housing placement", "Client-specific communication requires appropriate client authorization", "No landlord is required to waive lawful rental standards", "Additional Partnership Resources Coming Soon", "opportunities for collaboration", "Do not send confidential client information through a website form or ordinary email"])
            partner_contact_ok = page.locator('#partner-contact a[href="tel:4062197035"]').count() == 1 and page.locator('#partner-contact a[href="mailto:info@anchorsupportservice.com"]').count() == 1 and page.locator('#partner-contact form').count() == 0 and page.locator('meta[name="robots"]').get_attribute("content") == "index, follow"
            results["journeys"]["partners_page"] = {"homepage_callout": home_partner_link, "content_scope_and_limitations": partner_content_ok, "verified_contact_links_no_form": partner_contact_ok}

            # Founder bio and key brand image checks.
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(base + "/", wait_until="networkidle")
            page.keyboard.press("Tab")
            results["journeys"]["skip_link_keyboard_focus"] = page.evaluate("document.activeElement.classList.contains('skip-link') && document.activeElement.matches(':focus-visible')")
            founder = page.locator(".team-photo")
            if founder.count():
                if founder.evaluate("x => x.complete && x.naturalWidth > 0") is not True:
                    results["broken_images"].append({"path": "/", "images": ["alex-ceo-picture.png"]})
                if not founder.get_attribute("alt"):
                    results["accessibility"].append({"path": "/", "issue": "founder_image_missing_alt"})
            bio = page.locator(".bio-details")
            if bio.count():
                bio.locator("summary").click()
                results["journeys"]["founder_bio_expand"] = bio.evaluate("x => x.open")

            # Check new policy alias redirects without exposing another policy copy.
            alias = page.goto(base + "/privacy-policy.html", wait_until="networkidle")
            results["journeys"]["policy_alias"] = {"status": alias.status if alias else None, "final_path": urlparse(page.url).path, "canonical": page.locator('link[rel="canonical"]').get_attribute("href") if page.locator('link[rel="canonical"]').count() else None}

            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    summary = {"page_count": len(results["pages"]), "viewports": VIEWPORTS, "overflow": results["overflow"], "page_errors": results["page_errors"], "console_errors": results["console_errors"], "failed_local_requests": results["failed_local_requests"], "broken_images": results["broken_images"], "internal_links": results["internal_links"], "external_link_count": len(results["external_links"]), "journeys": results["journeys"], "accessibility": results["accessibility"]}
    print(json.dumps(summary, indent=2))
    failed = bool(results["overflow"] or results["page_errors"] or results["console_errors"] or results["failed_local_requests"] or results["broken_images"] or results["internal_links"] or results["accessibility"])
    failed = failed or any(not all([v.get("hiring_visible"),v.get("careers_navigation"),v.get("position_content"),v.get("pdf_download"),v.get("indeed_application"),v.get("mobile_intro_compact"),v.get("apply_button_visible_early"),v.get("mobile_menu_to_policy"),v.get("policy_readable"),v.get("policy_contact_section"),v.get("contact_links_intake_notice_and_questionnaire")]) or v.get("zoom_overflow") for k,v in results["journeys"].items() if k in ("mobile","desktop"))
    intake = results["journeys"].get("new_client_intake", {})
    failed = failed or not all(intake.get(key) for key in ("homepage_notice", "secure_steps_and_online_forms_unavailable", "no_jotform_or_invitation_links_published", "secure_route_noindex_nofollow", "no_stale_pause_copy"))
    partners = results["journeys"].get("partners_page", {})
    failed = failed or not all(partners.get(key) for key in ("homepage_callout", "content_scope_and_limitations", "verified_contact_links_no_form"))

    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()
