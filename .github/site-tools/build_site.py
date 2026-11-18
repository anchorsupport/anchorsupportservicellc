"""Assemble the reviewed public-site allowlist into dist/public-site for Pages."""

from __future__ import annotations

from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "dist" / "public-site"

# Keep this list intentionally explicit: repository-root review files, local
# artifacts, dependencies, and internal application source are never published.
PUBLIC_FILES = (
    "CNAME",
    "404.html",
    "index.html",
    "policy.html",
    "privacy-policy.html",
    "secure-paperwork.html",
    "careers/index.html",
    "partners/index.html",
    "waivertrack/index.html",
    "styles.css",
    "script.js",
    "robots.txt",
    "sitemap.xml",
    "anchor-logo.png",
    "anchor-logo-display.webp",
    "anchor-favicon.png",
    "alex-ceo-picture.png",
    "alex-ceo-picture-display.webp",
    "scotty-housing-navigator.jpg",
    "scotty-housing-navigator pic.jpg",
    "assets/anchor-support-housing-navigator-tenancy-support-specialist-job-description.pdf",
)


def main() -> None:
    missing = [rel for rel in PUBLIC_FILES if not (ROOT / rel).is_file()]
    if missing:
        raise SystemExit("Missing required public files: " + ", ".join(missing))

    dist = ROOT / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    if OUTPUT.is_symlink() or OUTPUT.absolute().parent.resolve() != dist.resolve() or OUTPUT.name != "public-site":
        raise SystemExit("Refusing to publish outside dist/public-site")
    if OUTPUT.exists() and (not OUTPUT.is_dir() or not (OUTPUT / ".nojekyll").is_file()):
        raise SystemExit("Refusing to write into dist/public-site without its generated-output marker")

    expected = set(PUBLIC_FILES) | {".nojekyll"}
    if OUTPUT.exists():
        paths = list(OUTPUT.rglob("*"))
        symlinks = sorted(path.relative_to(OUTPUT).as_posix() for path in paths if path.is_symlink())
        if symlinks:
            raise SystemExit("Symlinks are not permitted in the generated output: " + ", ".join(symlinks))
        existing = {path.relative_to(OUTPUT).as_posix() for path in paths if path.is_file()}
        unexpected = sorted(existing - expected)
        if unexpected:
            raise SystemExit("Unexpected files in generated output: " + ", ".join(unexpected))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for rel in PUBLIC_FILES:
        source = ROOT / rel
        target = OUTPUT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    # This standard Pages marker also identifies a prior generated directory.
    (OUTPUT / ".nojekyll").touch()
    actual = {path.relative_to(OUTPUT).as_posix() for path in OUTPUT.rglob("*") if path.is_file()}
    if actual != expected:
        raise SystemExit("Published output does not match the explicit file allowlist")

    print(f"Assembled {len(PUBLIC_FILES)} allowlisted public files in {OUTPUT}")
    for rel in PUBLIC_FILES:
        print(f"  {rel}")


if __name__ == "__main__":
    main()
