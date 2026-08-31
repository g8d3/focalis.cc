// Focalis Studio — interactions
document.addEventListener('DOMContentLoaded', () => {
  // mobile menu
  const btn = document.getElementById('menu-btn');
  const menu = document.getElementById('mobile-menu');
  if (btn && menu) {
    btn.addEventListener('click', () => {
      const open = menu.classList.contains('hidden');
      menu.classList.toggle('hidden', !open);
      btn.setAttribute('aria-expanded', String(open));
    });
  }

  // reveal on scroll
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  // contact form demo
  const form = document.getElementById('contact-form');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      const orig = btn.textContent;
      btn.textContent = 'Message sent — we reply within 24h';
      btn.disabled = true;
      btn.style.background = '#16a34a';
      setTimeout(() => {
        btn.textContent = orig;
        btn.disabled = false;
        btn.style.background = '';
        form.reset();
      }, 3500);
    });
  }

  // pricing billing toggle (if present)
  const toggle = document.getElementById('billing-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      const yearly = toggle.dataset.period === 'yearly';
      toggle.dataset.period = yearly ? 'monthly' : 'yearly';
      document.querySelectorAll('[data-monthly]').forEach(el => {
        el.textContent = yearly ? el.dataset.monthly : el.dataset.yearly;
      });
      toggle.querySelector('[data-handle]').style.transform = yearly ? 'translateX(0)' : 'translateX(20px)';
      toggle.querySelector('[data-label-monthly]').style.opacity = yearly ? '1' : '0.5';
      toggle.querySelector('[data-label-yearly]').style.opacity = yearly ? '0.5' : '1';
    });
  }
});
