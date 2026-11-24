from __future__ import annotations

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urldefrag, urljoin, urlparse
import json
import re

from playwright.sync_api import sync_playwright

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
PAGES = ["/", "/careers/", "/partners/", "/housing-insights/", "/policy.html", "/secure-paperwork.html", "/waivertrack/", "/404.html"]
VIEWPORTS = [320, 360, 375, 390, 430, 768, 900, 1024, 1366, 1440, 1920]
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
    "https://docs.google.com/forms/d/e/1FAIpQLSeae9eGYlUxB4MeFz2V6wtrWI_awH7uM_E0AykRIPcDMjRBGQ/viewform",
    "https://www.ci.missoula.mt.us/3472/Housing-Assessment-Report",
    "https://www.missoulaparks.org/3112/Houseless-Data",
    "https://ravallicounty.gov/ArchiveCenter/ViewFile/Item/20329",
    "https://commerce.mt.gov/News/press-releases-and-statements/Montana-Board-of-Housing-Allocates-Funding-to-Build-136-Affordable-Homes-in-Montana",
    "https://montanafreepress.org/2026/11/13/new-transitional-housing-for-families-in-the-works/",
    "https://montanafreepress.org/2026/09/15/johnson-street-shelter-closure-response/",
    "https://montanafreepress.org/2026/07/17/survey-ids-top-barriers-for-missoula-renters/",
    "https://dphhs.mt.gov/HeartInitiative/TenancySupportServices",
    "https://dphhs.mt.gov/assets/BHDD/HeartWaiver/605_TSS-TSS_eff.1.1.25.pdf",
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
                    state = page.evaluate("""() => {
                      const overflowing = [...document.querySelectorAll('body *')].map(x => {
                        const r = x.getBoundingClientRect();
                        const s = getComputedStyle(x);
                        const before = getComputedStyle(x, '::before');
                        const after = getComputedStyle(x, '::after');
                        return {tag:x.tagName, id:x.id, className:typeof x.className === 'string' ? x.className : '', text:(x.innerText||'').trim().slice(0,100), left:Math.round(r.left), right:Math.round(r.right), width:Math.round(r.width), clientWidth:x.clientWidth, scrollWidth:x.scrollWidth, display:s.display, position:s.position, before:before.content, after:after.content};
                      }).filter(x => x.display !== 'none' && (x.right > innerWidth + 1 || x.left < -1 || x.scrollWidth > x.clientWidth + 1)).slice(0,40);
                      const brand = document.querySelector('.brand-text');
                      const brandNameVisible = !!brand && getComputedStyle(brand).display !== 'none' && getComputedStyle(brand).visibility !== 'hidden' && brand.innerText.includes('Anchor Support Service LLC');
                      const colorRgb = value => { const m = value.match(/[\\d.]+/g); return m ? m.slice(0,3).map(Number) : null; };
                      const luminance = value => { const c = colorRgb(value); if (!c) return 0; const v = c.map(n => { n /= 255; return n <= .04045 ? n / 12.92 : ((n + .055) / 1.055) ** 2.4; }); return .2126*v[0] + .7152*v[1] + .0722*v[2]; };
                      const contrast = (a,b) => { const x=luminance(a), y=luminance(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };
                      const backgroundOf = el => { for (let node=el; node; node=node.parentElement) { const c=getComputedStyle(node).backgroundColor; const m=c.match(/rgba?\\(([^)]+)\\)/); if (m) { const parts=m[1].split(',').map(Number); if (parts.length<4 || parts[3]>.99) return c; } } return 'rgb(255, 255, 255)'; };
                      const contrastIssues = [];
                      if (location.pathname === '/careers/') {
                        for (const selector of ['.careers-facts dt','.careers-facts dd','.careers-card h3','.careers-card p','.careers-panel h2','.careers-panel p','.careers-preferred h3','.careers-preferred li']) {
                          for (const el of document.querySelectorAll(selector)) { const fg=getComputedStyle(el).color, bg=backgroundOf(el), value=contrast(fg,bg); if (value < 4.5) contrastIssues.push({selector, text:el.innerText.trim().slice(0,80), foreground:fg, background:bg, ratio:+value.toFixed(2), required:4.5}); }
                        }
                        for (const selector of ['.careers-facts','.careers-card','.careers-panel','.careers-preferred']) {
                          for (const el of document.querySelectorAll(selector)) { const s=getComputedStyle(el), bg=backgroundOf(el.parentElement), value=contrast(s.borderTopColor,bg); if (s.borderTopStyle !== 'none' && value < 3) contrastIssues.push({selector, issue:'card_boundary_contrast', border:s.borderTopColor, background:bg, ratio:+value.toFixed(2), required:3}); }
                        }
                      }
                      return {inner:innerWidth, doc:document.documentElement.scrollWidth, body:document.body.scrollWidth, title:document.title, h1:[...document.querySelectorAll('h1')].map(x=>x.innerText), brandNameVisible, contrastIssues, broken:[...document.images].filter(x=>!x.complete || !x.naturalWidth).map(x=>x.currentSrc), duplicateIds:[...document.querySelectorAll('[id]')].map(x=>x.id).filter((x,i,a)=>a.indexOf(x)!==i), unnamed:[...document.querySelectorAll('a,button')].filter(x=>!(x.innerText||x.getAttribute('aria-label')||x.getAttribute('title'))).map(x=>x.outerHTML.slice(0,120)), overflowing};
                    }""")
                    results["pages"].append({"path": path, "width": width, "status": response.status, "title": state["title"]})
                    if state["doc"] > state["inner"] + 1 or state["body"] > state["inner"] + 1:
                        results["overflow"].append({"path": path, "width": width, **state})
                    if state["broken"]:
                        results["broken_images"].append({"path": path, "width": width, "images": state["broken"]})
                    if state["duplicateIds"]:
                        results["accessibility"].append({"path": path, "issue": "duplicate_ids", "ids": state["duplicateIds"]})
                    if state["unnamed"]:
                        results["accessibility"].append({"path": path, "issue": "unnamed_controls", "items": state["unnamed"]})
                    if not state["brandNameVisible"]:
                        results["accessibility"].append({"path": path, "width": width, "issue": "company_name_not_visible_in_shared_header"})
                    if state["contrastIssues"]:
                        results["accessibility"].append({"path": path, "width": width, "issue": "careers_contrast", "details": state["contrastIssues"]})
                    if len(state["h1"]) != 1:
                        results["accessibility"].append({"path": path, "issue": "h1_count", "count": len(state["h1"])})
                    if path == "/" and state["h1"] != ["Anchor Support Service LLC"]:
                        results["accessibility"].append({"path": path, "issue": "homepage_brand_h1_missing", "h1": state["h1"]})
                    if path == "/careers/" and not any("Anchor Support Service LLC" in heading for heading in state["h1"]):
                        results["accessibility"].append({"path": path, "issue": "careers_brand_h1_missing", "h1": state["h1"]})

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

                    # WaiverTrack is intentionally a standalone staff sign-in landing page with no public site menu.
                    if path != "/waivertrack/" and width in (320, 360, 375, 390, 430, 768, 900, 1024):
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
                            if not page.locator('.site-nav a[href="/housing-insights/"]').is_visible():
                                results["accessibility"].append({"path": path, "width": width, "issue": "housing_insights_missing_from_mobile_menu"})
                            toggle.click()
                            if toggle.get_attribute("aria-expanded") != "false":
                                results["accessibility"].append({"path": path, "width": width, "issue": "mobile_menu_did_not_close"})
                    if path != "/waivertrack/" and width >= 1366:
                        if not page.locator('.site-nav a[href="/careers/"]').is_visible():
                            results["accessibility"].append({"path": path, "width": width, "issue": "careers_missing_from_desktop_nav"})
                        if not page.locator('.site-nav a[href="/partners/"]').is_visible():
                            results["accessibility"].append({"path": path, "width": width, "issue": "partners_missing_from_desktop_nav"})
                        if not page.locator('.site-nav a[href="/housing-insights/"]').is_visible():
                            results["accessibility"].append({"path": path, "width": width, "issue": "housing_insights_missing_from_desktop_nav"})
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
            required_assets = ["/styles.css", "/script.js", "/anchor-logo.png", "/anchor-logo-display.webp", "/anchor-favicon.png", "/alex-ceo-picture.png", "/alex-ceo-picture-display.webp"]
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

            # Careers must be an informational page with no active applications at both breakpoints.
            for width, label in [(390, "mobile"), (1366, "desktop")]:
                page.set_viewport_size({"width": width, "height": 900 if width >= 768 else 844})
                page.goto(base + "/", wait_until="networkidle")
                home_text = page.locator("body").inner_text()
                home_careers = page.locator(".home-careers-callout")
                home_careers_ok = home_careers.get_by_role("heading", name="No Current Openings").count() == 1 and home_careers.get_by_role("link", name="Careers at Anchor").get_attribute("href") == "/careers/" and "We are not accepting new employment applications at this time." in home_careers.inner_text() and not re.search(r"now hiring", home_text, re.I)
                home_careers.get_by_role("link", name="Careers at Anchor").click()
                on_careers = urlparse(page.url).path == "/careers/" and page.get_by_role("heading", name="Careers at Anchor Support Service LLC").count() == 1
                careers_text = page.locator("body").inner_text()
                expected_thanks = "Thank you to everyone who took the time to apply and express interest in joining Anchor Support Service LLC. We sincerely appreciate your interest in our mission and the time you invested in the application process."
                expected_closed = "We are not accepting new employment applications at this time. Please check this page for future opportunities."
                careers_copy_ok = page.locator(".careers-status").inner_text().casefold() == "we are not currently hiring" and expected_thanks in careers_text and expected_closed in careers_text and not re.search(r"now hiring", careers_text, re.I)
                careers_links = page.locator("a[href]").evaluate_all("els => els.map(a => ({href:a.href, text:(a.innerText||'').trim(), aria:a.getAttribute('aria-label')||''}))")
                no_application_ctas = not any("indeed.com" in item["href"].casefold() or "job-description.pdf" in item["href"].casefold() or re.search(r"apply on indeed|submit application|apply through indeed", item["text"]+" "+item["aria"], re.I) for item in careers_links)
                career_html = (root / "careers" / "index.html").read_text(encoding="utf-8-sig")
                no_job_posting_data = not re.search(r'"@type"\s*:\s*"JobPosting"', career_html, re.I)
                careers_meta = page.locator('meta[name="description"]').get_attribute("content") or ""
                status_meta_ok = "not currently hiring" in careers_meta.casefold() and "not accepting new employment applications" in careers_meta.casefold()
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
                map_queries = page.locator('#contact a[href^="https://www.google.com/maps/search/"], .office-update-card a[href^="https://www.google.com/maps/search/"]').evaluate_all("els => els.map(a => new URL(a.href).searchParams.get('query') || '')")
                office_maps_use_suite_208 = len(map_queries) == 2 and all("Suite 208" in query and "228" not in query for query in map_queries)
                questionnaire = page.locator('#contact a[href="https://docs.google.com/forms/d/e/1FAIpQLSeae9eGYlUxB4MeFz2V6wtrWI_awH7uM_E0AykRIPcDMjRBGQ/viewform"]')
                holiday_card = page.locator("#holiday-office-closures")
                holiday_text = holiday_card.inner_text()
                expected_holidays = ["Thanksgiving Day: Thursday, November 26, 2026", "Christmas Day: Friday, December 25, 2026", "New Year\u2019s Day: Friday, January 1, 2027"]
                holiday_ok = holiday_card.get_by_role("heading", name="Upcoming Holiday Office Closures").count() == 1 and all(day in holiday_text for day in expected_holidays) and "Monday through Friday, 8:00 AM\u20135:00 PM, by appointment only." in holiday_text and "Messages received during these closures will be reviewed when regular business operations resume." in holiday_text and all(holiday_card.locator(f'time[datetime="{day}"]').count() == 1 for day in ["2026-11-26", "2026-12-25", "2027-01-01"]) and not any(forbidden in holiday_text for forbidden in ["November 27", "December 24", "December 31", "24/7", "emergency support"])
                contact_ok = all(s in contact_text for s in ["(406) 219-7035", "(406) 540-7982", "info@anchorsupportservice.com", "accepting new-client inquiries", "3010 Santa Fe Ct, Suite 208", "By Appointment Only", "Walk-ins are not available", "PO Box 17021", "3150 Great Northern Loop", "General Interest Questionnaire", "not a secure Medicaid enrollment form", "Do not submit sensitive medical, Medicaid, or identifying information", "Upcoming Holiday Office Closures"]) and all(s.casefold() in office_text.casefold() for s in ["Office Location Update", "3010 Santa Fe Ct, Suite 208", "By Appointment Only", "Walk-ins are not available"]) and questionnaire.count() == 1 and questionnaire.get_attribute("target") == "_blank" and "noopener" in (questionnaire.get_attribute("rel") or "") and page.locator('#contact a[href="tel:4062197035"]').count() >= 1 and page.locator('#contact a[href="secure-paperwork.html"]').inner_text() == "View Intake Steps" and page.locator('#contact a[href^="https://www.google.com/maps/search/"]').count() == 1 and page.locator('.office-update-card a[href^="https://www.google.com/maps/search/"]').count() == 1 and office_maps_use_suite_208 and holiday_ok
                page.goto(base + "/policy.html", wait_until="networkidle")
                overflow_after_zoom = []
                for zoom_width in [int(width/1.25), int(width/2)] if width <= 430 else []:
                    page.set_viewport_size({"width": zoom_width, "height": 844})
                    z = page.evaluate("({inner:innerWidth,scroll:document.documentElement.scrollWidth})")
                    if z["scroll"] > z["inner"] + 1:
                        overflow_after_zoom.append({"width": zoom_width, **z})
                retired_pdf = page.request.get(base + "/assets/anchor-support-housing-navigator-tenancy-support-specialist-job-description.pdf")
                results["journeys"][label] = {"homepage_no_openings_callout": home_careers_ok, "careers_navigation": on_careers, "closed_careers_copy": careers_copy_ok, "no_application_ctas": no_application_ctas, "no_job_posting_data": no_job_posting_data, "closed_status_metadata": status_meta_ok, "retired_job_description_not_published": retired_pdf.status == 404, "mobile_menu_to_policy": menu_policy_ok, "policy_readable": policy_ok, "policy_contact_section": policy_contact_ok, "contact_links_intake_notice_questionnaire_and_holiday_closures": contact_ok, "office_map_links_use_suite_208": office_maps_use_suite_208, "holiday_closures_near_business_hours": holiday_ok, "zoom_overflow": overflow_after_zoom}

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
            steps = page.locator(".paperwork-step")
            step1_open = steps.count() == 2 and steps.nth(0).evaluate("el => el.open")
            step2_summary = steps.nth(1).locator("summary") if steps.count() == 2 else None
            if step2_summary:
                step2_summary.click()
                step2_expands = steps.nth(1).evaluate("el => el.open")
                step2_summary.click()
                step2_collapses = not steps.nth(1).evaluate("el => el.open")
            else:
                step2_expands = step2_collapses = False
            secure_intake_ok = secure_meta == "noindex, nofollow" and all(s in secure_text + " " + steps_text for s in ["Step 1", "Medicaid Eligibility Consent", "Step 2", "TSS Prior Authorization Paperwork", "only after Medicaid eligibility has been reviewed", "does not guarantee eligibility, Medicaid authorization, housing assistance"]) and secure_online_unavailable and no_published_jotform_link and steps.count() == 2 and step1_open and step2_expands and step2_collapses and page.locator("iframe").count() == 0 and page.locator("form").count() == 0 and page.locator('a[href="tel:4062197035"]').count() >= 1 and page.locator('a[href^="https://www.jotform.com/"]').count() == 0
            stale_pause_copy = re.compile(r"paused from accepting new clients|new client pause|intake (?:is )?paused|paperwork (?:is )?paused", re.I)
            public_html = [root / "index.html", root / "careers" / "index.html", root / "secure-paperwork.html"]
            no_stale_intake_pause = all(not stale_pause_copy.search(file.read_text(encoding="utf-8")) for file in public_html)
            results["journeys"]["new_client_intake"] = {"homepage_notice": intake_notice_ok, "secure_steps_and_online_forms_unavailable": secure_intake_ok, "step1_open": step1_open, "step2_expandable_and_collapsible": step2_expands and step2_collapses, "no_jotform_or_invitation_links_published": no_published_jotform_link, "secure_route_noindex_nofollow": secure_meta == "noindex, nofollow", "no_stale_pause_copy": no_stale_intake_pause}

            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(base + "/", wait_until="networkidle")
            hero_questionnaire = page.locator('.hero-actions a[href="https://docs.google.com/forms/d/e/1FAIpQLSeae9eGYlUxB4MeFz2V6wtrWI_awH7uM_E0AykRIPcDMjRBGQ/viewform"]')
            hero_questionnaire_box = hero_questionnaire.bounding_box() if hero_questionnaire.count() == 1 else None
            results["journeys"]["homepage_questionnaire"] = {
                "visible_near_top": hero_questionnaire.count() == 1 and hero_questionnaire.is_visible() and hero_questionnaire_box is not None and 0 <= hero_questionnaire_box["y"] < 844,
                "opens_safely_in_new_tab": hero_questionnaire.get_attribute("target") == "_blank" and "noopener" in (hero_questionnaire.get_attribute("rel") or ""),
                "sensitive_information_warning": "Do not include sensitive medical, Medicaid, or identifying information" in page.locator(".hero-questionnaire-note").inner_text(),
                "contact_section_link_retained": page.locator('#contact a[href="https://docs.google.com/forms/d/e/1FAIpQLSeae9eGYlUxB4MeFz2V6wtrWI_awH7uM_E0AykRIPcDMjRBGQ/viewform"]').count() == 1,
            }
            insights_preview = page.locator('.housing-insights-preview a[href="/housing-insights/"]')
            results["journeys"]["homepage_housing_insights_preview"] = {
                "visible": insights_preview.count() == 1 and insights_preview.is_visible(),
                "labelled": insights_preview.count() == 1 and insights_preview.inner_text().strip() == "Explore Housing Insights",
                "heading_and_description": "Understanding Montana's Housing Challenges" in page.locator(".housing-insights-preview").inner_text() and "Explore housing statistics" in page.locator(".housing-insights-preview").inner_text(),
            }
            page.goto(base + "/housing-insights/", wait_until="networkidle")
            insight_text = page.locator("main").inner_text()
            stat_cards = page.locator(".insight-stat-card")
            article_cards = page.locator(".insight-article-card")
            progress_cards = page.locator(".insight-progress-card")
            source_links = page.locator(".insight-card a[target='_blank']")
            insight_html = (root / "housing-insights" / "index.html").read_text(encoding="utf-8").casefold()
            insight_data_path = root / "housing-insights" / "housing-insights-data.json"
            if not insight_data_path.is_file():
                insight_data_path = root.parent.parent / "housing-insights" / "housing-insights-data.json"
            insight_data = json.loads(insight_data_path.read_text(encoding="utf-8")) if insight_data_path.is_file() else None
            insight_sources_verified = insight_data is not None and all(item["sourceUrl"].casefold() in insight_html for group in ("statistics", "progress", "articles") for item in insight_data[group])
            insight_ok = (
                page.locator("h1").count() == 1
                and page.locator("h1").inner_text() == "Housing Insights & Community Impact"
                and stat_cards.count() >= 3 and article_cards.count() >= 2 and progress_cards.count() >= 1
                and source_links.count() >= stat_cards.count() + article_cards.count() + progress_cards.count()
                and insight_sources_verified
                and "49.6%" in insight_text and "180" in insight_text and "169" in insight_text
                and "not a completed or evaluated outcome" in insight_text
                and "Anchor Support Service LLC is committed to supporting individuals" in insight_text
                and "does not directly provide ongoing rental subsidies or shelter" in insight_text
                and page.locator('meta[name="description"]').count() == 1
                and page.locator('link[rel="canonical"]').get_attribute("href") == "https://anchorsupportservice.com/housing-insights/"
                and page.locator(".insights-updated time").get_attribute("datetime") == "2026-11-24"
            )
            results["journeys"]["housing_insights"] = {
                "page_structure_and_content": insight_ok,
                "statistics_articles_and_progress_cards": {"statistics": stat_cards.count(), "articles": article_cards.count(), "progress": progress_cards.count()},
                "every_data_source_linked": insight_sources_verified,
                "source_links_open_safely": source_links.count() > 0 and source_links.evaluate_all("els => els.every(a => a.rel.includes('noopener') && a.rel.includes('noreferrer'))"),
                "expected_stat_values_and_scope_notes": all(x in insight_text for x in ["49.6%", "180", "169", "one-night snapshots"]),
                "no_anchor_outcomes_claimed": "verified information about our community impact" in insight_text and "not Anchor outcomes" in insight_text,
            }
            page.goto(base + "/", wait_until="networkidle")
            home_partner_link = page.locator('.partner-callout a[href="/partners/"]').count() == 1
            page.goto(base + "/partners/", wait_until="networkidle")
            partner_text = page.locator("main").inner_text()
            partner_content_ok = all(s in partner_text for s in ["Supporting Successful Tenancies and Strengthening Landlord Relationships", "Communication Support", "Eviction Risk Reduction", "Lease Education", "Housing Stability", "Community Coordination", "WHEN A TENANCY IS AT RISK", "Communication coaching", "Help organizing housing notices and paperwork", "Budgeting and housing-retention planning", "qualified legal assistance", "Anchor does not directly pay ongoing rent or rental arrears.", "does not guarantee rental payments or co-sign leases", "does not provide legal advice or legal representation", "not a landlord, property manager, or enforcement agency", "cannot guarantee tenant compliance or specific housing outcomes", "cannot guarantee financial assistance or housing placement", "Client-specific communication requires appropriate client authorization", "No landlord is required to waive lawful rental standards", "Additional Partnership Resources Coming Soon", "opportunities for collaboration", "Do not send confidential client information through a website form or ordinary email"])
            partner_contact_ok = page.locator('#partner-contact a[href="tel:4062197035"]').count() == 1 and page.locator('#partner-contact a[href="mailto:info@anchorsupportservice.com"]').count() == 1 and page.locator('#partner-contact form').count() == 0 and page.locator('meta[name="robots"]').get_attribute("content") == "index, follow"
            results["journeys"]["partners_page"] = {"homepage_callout": home_partner_link, "content_scope_and_limitations": partner_content_ok, "verified_contact_links_no_form": partner_contact_ok}

            # Founder bio and key brand image checks.
            page.set_viewport_size({"width": 390, "height": 844})
            page.goto(base + "/", wait_until="networkidle")
            page.keyboard.press("Tab")
            results["journeys"]["skip_link_keyboard_focus"] = page.evaluate("document.activeElement.classList.contains('skip-link') && document.activeElement.matches(':focus-visible')")
            founder = page.locator(".team-photo")
            if founder.count():
                founder.scroll_into_view_if_needed()
                founder.wait_for(state="visible")
                page.wait_for_function("img => img.complete && img.naturalWidth > 0", arg=founder.element_handle(), timeout=10000)
                if founder.evaluate("x => x.complete && x.naturalWidth > 0") is not True:
                    results["broken_images"].append({"path": "/", "images": ["alex-ceo-picture.png"]})
                results["journeys"]["founder_photo_mobile"] = founder.evaluate("x => ({loaded: x.complete && x.naturalWidth > 0, width: x.naturalWidth, height: x.naturalHeight, currentSrc: x.currentSrc})")
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
    active_recruitment_pattern = re.compile(r'Now hiring|Apply on Indeed|indeed\.com/viewjob|View Career Opportunity|anchor-support-housing-navigator-tenancy-support-specialist-job-description\.pdf|"@type"\s*:\s*"JobPosting"', re.I)
    published_html = list(root.rglob("*.html"))
    no_active_recruitment = all(not active_recruitment_pattern.search(path.read_text(encoding="utf-8-sig")) for path in published_html)
    results["journeys"]["no_public_active_recruitment"] = {"verified": no_active_recruitment, "html_files_scanned": len(published_html)}
    old_suite_pattern = re.compile(r"(?:Suite|Ste\.?|#)\s*228\b|%23?228|%20Suite%20228", re.I)
    public_address_correct = all(not old_suite_pattern.search(path.read_text(encoding="utf-8-sig")) for path in published_html)
    results["journeys"]["office_suite_208"] = {"no_old_suite_in_public_html": public_address_correct, "html_files_scanned": len(published_html)}
    summary = {"page_count": len(results["pages"]), "viewports": VIEWPORTS, "overflow": results["overflow"], "page_errors": results["page_errors"], "console_errors": results["console_errors"], "failed_local_requests": results["failed_local_requests"], "broken_images": results["broken_images"], "internal_links": results["internal_links"], "external_link_count": len(results["external_links"]), "journeys": results["journeys"], "accessibility": results["accessibility"]}
    print(json.dumps(summary, indent=2))
    failed = bool(results["overflow"] or results["page_errors"] or results["console_errors"] or results["failed_local_requests"] or results["broken_images"] or results["internal_links"] or results["accessibility"])
    failed = failed or any(not all([v.get("homepage_no_openings_callout"),v.get("careers_navigation"),v.get("closed_careers_copy"),v.get("no_application_ctas"),v.get("no_job_posting_data"),v.get("closed_status_metadata"),v.get("retired_job_description_not_published"),v.get("mobile_menu_to_policy"),v.get("policy_readable"),v.get("policy_contact_section"),v.get("contact_links_intake_notice_questionnaire_and_holiday_closures"),v.get("office_map_links_use_suite_208"),v.get("holiday_closures_near_business_hours")]) or v.get("zoom_overflow") for k,v in results["journeys"].items() if k in ("mobile","desktop"))
    failed = failed or not results["journeys"].get("no_public_active_recruitment", {}).get("verified", False)
    failed = failed or not results["journeys"].get("office_suite_208", {}).get("no_old_suite_in_public_html", False)
    failed = failed or not all(results["journeys"].get("homepage_questionnaire", {}).values())
    failed = failed or not all(results["journeys"].get("homepage_housing_insights_preview", {}).values())
    housing_insights = results["journeys"].get("housing_insights", {})
    failed = failed or not all(value is True for key, value in housing_insights.items() if isinstance(value, bool))
    failed = failed or not results["journeys"].get("founder_photo_mobile", {}).get("loaded", False)
    intake = results["journeys"].get("new_client_intake", {})
    failed = failed or not all(intake.get(key) for key in ("homepage_notice", "secure_steps_and_online_forms_unavailable", "no_jotform_or_invitation_links_published", "secure_route_noindex_nofollow", "no_stale_pause_copy"))
    partners = results["journeys"].get("partners_page", {})
    failed = failed or not all(partners.get(key) for key in ("homepage_callout", "content_scope_and_limitations", "verified_contact_links_no_form"))

    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()
