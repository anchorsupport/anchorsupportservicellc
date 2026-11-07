from __future__ import annotations

from collections import Counter
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import urldefrag, urljoin, urlparse
import json
import re
import tempfile

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGES = ["/", "/careers/", "/policy.html", "/secure-paperwork.html", "/404.html"]
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
    "https://docs.google.com/forms/d/e/1FAIpQLSeae9eGYlUxB4MeFz2V6wtrWI_awH7uM_E0AykRIPcDMjRBGQ/viewform",
}

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), lambda *args, **kwargs: QuietHandler(*args, directory=str(ROOT), **kwargs))
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
                            if not page.locator('.site-nav a[href="/policy.html"]').is_visible():
                                results["accessibility"].append({"path": path, "width": width, "issue": "privacy_missing_from_mobile_menu"})
                            toggle.click()
                            if toggle.get_attribute("aria-expanded") != "false":
                                results["accessibility"].append({"path": path, "width": width, "issue": "mobile_menu_did_not_close"})
                    if width >= 1366:
                        if not page.locator('.site-nav a[href="/careers/"]').is_visible():
                            results["accessibility"].append({"path": path, "width": width, "issue": "careers_missing_from_desktop_nav"})
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
                        allowed_mailboxes = {"info@anchorsupportservice.com", "alex@anchorsupportservice.com"} if path.startswith("/careers") else {"info@anchorsupportservice.com"}
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
                        home_html = (ROOT / "index.html").read_text(encoding="utf-8-sig")
                        if not re.search(rf'\bid=["\']{re.escape(fragment)}["\']', home_html):
                            results["internal_links"].append({"source": path, "href": href, "issue": "missing_home_fragment"})

            # Email/phone links and external references from the homepage and Careers page.
            if not EXTERNAL_EXPECTED.issubset(external_found):
                results["internal_links"].append({"issue": "missing_expected_external_links", "missing": sorted(EXTERNAL_EXPECTED - external_found)})
            results["external_links"] = [{"url": url, "present": True} for url in sorted(external_found)]

            # Check standalone assets and the protected portal landing route without following sign-in.
            required_assets = ["/styles.css", "/script.js", "/anchor-logo.png", "/alex-ceo-picture.png", "/assets/anchor-support-housing-navigator-tenancy-support-specialist-job-description.pdf"]
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
                download_link = page.get_by_role("link", name="Download Job Description (PDF)").first
                href = download_link.get_attribute("href")
                with page.expect_download() as download_info:
                    download_link.click()
                download = download_info.value
                with tempfile.TemporaryDirectory() as d:
                    target = Path(d) / download.suggested_filename
                    download.save_as(target)
                    download_ok = target.read_bytes().startswith(b"%PDF-") and target.stat().st_size > 1000
                email_hrefs = page.locator('a[href^="mailto:"]').evaluate_all("els => els.map(x=>x.href)")
                application_copy_ok = "alex@anchorsupportservice.com" in text and page.locator('a.button[href^="mailto:info@anchorsupportservice.com"]').count() == 0
                mailto_ok = application_copy_ok and page.get_by_role("link", name="Email Your Résumé").count() == 2 and all(u == "mailto:alex@anchorsupportservice.com?subject=Housing%20Navigator%20-%20Resume" for u in page.locator('a.button-primary[href^="mailto:"]').evaluate_all("els => els.map(x=>x.getAttribute('href'))")) and "Interested in joining Anchor Support Service? Email your résumé and a brief introduction to alex@anchorsupportservice.com. To request the complete job description, please email the same address." in text
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
                contact_ok = "(406) 219-7035" in contact_text and "(406) 540-7982" in contact_text and "info@anchorsupportservice.com" in contact_text and "paused from accepting new clients" in contact_text
                page.goto(base + "/policy.html", wait_until="networkidle")
                overflow_after_zoom = []
                for zoom_width in [int(width/1.25), int(width/2)] if width <= 430 else []:
                    page.set_viewport_size({"width": zoom_width, "height": 844})
                    z = page.evaluate("({inner:innerWidth,scroll:document.documentElement.scrollWidth})")
                    if z["scroll"] > z["inner"] + 1:
                        overflow_after_zoom.append({"width": zoom_width, **z})
                results["journeys"][label] = {"hiring_visible": hiring_visible, "careers_navigation": on_careers, "position_content": content_present, "pdf_download": download_ok, "pdf_href": href, "application_mailto": mailto_ok, "mobile_menu_to_policy": menu_policy_ok, "policy_readable": policy_ok, "policy_contact_section": policy_contact_ok, "contact_links_and_client_pause": contact_ok, "zoom_overflow": overflow_after_zoom}

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
    failed = failed or any(not all([v.get("hiring_visible"),v.get("careers_navigation"),v.get("position_content"),v.get("pdf_download"),v.get("application_mailto"),v.get("mobile_menu_to_policy"),v.get("policy_readable"),v.get("policy_contact_section"),v.get("contact_links_and_client_pause")]) or v.get("zoom_overflow") for k,v in results["journeys"].items() if k in ("mobile","desktop"))
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()
