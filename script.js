const navToggle = document.querySelector('.nav-toggle');
const siteNav = document.querySelector('.site-nav');
const navLinks = document.querySelectorAll('.site-nav a');
const reducedMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

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

const samePageNavLinks = Array.from(document.querySelectorAll('.site-nav a[href^="#"]'));
const navTargets = samePageNavLinks
  .map((link) => document.querySelector(link.getAttribute('href')))
  .filter(Boolean);

if (samePageNavLinks.length && navTargets.length && 'IntersectionObserver' in window) {
  const setActiveNav = (id) => {
    samePageNavLinks.forEach((link) => {
      link.classList.toggle('is-active', link.getAttribute('href') === `#${id}`);
    });
  };

  const navObserver = new IntersectionObserver(
    (entries) => {
      const visibleEntry = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

      if (visibleEntry?.target?.id) {
        setActiveNav(visibleEntry.target.id);
      }
    },
    {
      rootMargin: '-35% 0px -55% 0px',
      threshold: [0.1, 0.35, 0.6],
    }
  );

  navTargets.forEach((target) => navObserver.observe(target));
}

const revealTargets = document.querySelectorAll(
  '.hero, main > .section, .secure-paperwork-hero, .secure-paperwork-layout, .secure-paperwork-section, .secure-lower-cta, .site-footer'
);

if (!reducedMotionQuery.matches && revealTargets.length && 'IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    {
      rootMargin: '0px 0px -12% 0px',
      threshold: 0.08,
    }
  );

  revealTargets.forEach((target) => {
    if (target.getBoundingClientRect().top < window.innerHeight * 0.95) {
      target.classList.add('is-visible');
    }

    target.classList.add('reveal-on-scroll');
    revealObserver.observe(target);
  });
}

const securePaperworkLinks = document.querySelectorAll('a[href="#secure-paperwork"]');
const securePaperworkSection = document.getElementById('secure-paperwork');
const securePaperworkTitle = document.getElementById('secure-paperwork-title');

if (securePaperworkSection && securePaperworkLinks.length) {
  securePaperworkLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      event.preventDefault();
      history.pushState(null, '', '#secure-paperwork');
      securePaperworkSection.scrollIntoView({
        behavior: reducedMotionQuery.matches ? 'auto' : 'smooth',
        block: 'start',
      });

      const focusDelay = reducedMotionQuery.matches ? 0 : 350;
      window.setTimeout(() => {
        securePaperworkTitle?.focus({ preventScroll: true });
      }, focusDelay);
    });
  });
}
