const navToggle = document.querySelector('.nav-toggle');
const siteNav = document.querySelector('.site-nav');
const navLinks = document.querySelectorAll('.site-nav a');

if (navToggle && siteNav) {
  const setMenuOpen = (isOpen) => {
    siteNav.classList.toggle('open', isOpen);
    navToggle.setAttribute('aria-expanded', String(isOpen));
  };

  navToggle.addEventListener('click', () => {
    setMenuOpen(!siteNav.classList.contains('open'));
  });

  navLinks.forEach((link) => {
    link.addEventListener('click', () => {
      setMenuOpen(false);
    });
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      setMenuOpen(false);
      navToggle.focus();
    }
  });
}

const securePaperworkLinks = document.querySelectorAll('a[href="#secure-paperwork"]');
const securePaperworkSection = document.getElementById('secure-paperwork');
const securePaperworkTitle = document.getElementById('secure-paperwork-title');

if (securePaperworkSection && securePaperworkLinks.length) {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  securePaperworkLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      history.pushState(null, '', '#secure-paperwork');
      securePaperworkSection.scrollIntoView({
        behavior: prefersReducedMotion.matches ? 'auto' : 'smooth',
        block: 'start',
      });

      const focusDelay = prefersReducedMotion.matches ? 0 : 350;
      window.setTimeout(() => {
        securePaperworkTitle?.focus({ preventScroll: true });
      }, focusDelay);
    });
  });
}
