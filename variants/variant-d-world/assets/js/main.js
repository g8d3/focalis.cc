// variant-d-world main
document.addEventListener('DOMContentLoaded', ()=>{
  const btn = document.getElementById('menu-btn');
  const menu = document.getElementById('mobile-menu');
  if(btn && menu){
    btn.addEventListener('click', ()=>{
      const open = !menu.classList.contains('hidden');
      menu.classList.toggle('hidden', open);
      const o = btn.querySelector('[data-icon="open"]');
      const c = btn.querySelector('[data-icon="close"]');
      if(o && c){ o.style.display = open ? '' : 'none'; c.style.display = open ? 'none' : ''; }
      btn.setAttribute('aria-expanded', String(!open));
    });
  }
  // reveal on scroll
  const obs = new IntersectionObserver((entries)=>{
    entries.forEach(e=>{ if(e.isIntersecting) e.target.classList.add('in') });
  }, {threshold:0.12});
  document.querySelectorAll('.reveal').forEach(el=>obs.observe(el));
  // year
  const y = document.getElementById('year'); if(y) y.textContent = new Date().getFullYear();
});
