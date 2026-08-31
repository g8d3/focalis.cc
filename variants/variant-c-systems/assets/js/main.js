// Focalis Systems — main.js — theme + interactions
(function(){
  // --- THEME ---
  var STORAGE_KEY = 'focalis-theme';
  var html = document.documentElement;

  function applyTheme(theme){
    html.setAttribute('data-theme', theme);
    try{ localStorage.setItem(STORAGE_KEY, theme); }catch(e){}
    var btn = document.getElementById('theme-toggle');
    if(btn){
      var isDark = theme === 'dark';
      btn.setAttribute('aria-label', isDark ? 'Switch to light theme' : 'Switch to dark theme');
      btn.setAttribute('aria-pressed', isDark ? 'true' : 'false');
      btn.title = isDark ? 'Switch to light theme' : 'Switch to dark theme';
      var sun = btn.querySelector('[data-theme-icon="sun"]');
      var moon = btn.querySelector('[data-theme-icon="moon"]');
      if(sun) sun.style.display = isDark ? 'none' : 'block';
      if(moon) moon.style.display = isDark ? 'block' : 'none';
    }
  }

  function initTheme(){
    var saved = null;
    try{ saved = localStorage.getItem(STORAGE_KEY); }catch(e){}
    var theme = saved;
    if(!theme){
      var prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = prefersDark ? 'dark' : 'light';
    }
    if(theme !== 'light' && theme !== 'dark') theme = 'light';
    applyTheme(theme);
  }

  // apply immediately to avoid flash
  initTheme();

  document.addEventListener('DOMContentLoaded', function(){
    // Re-apply on load to sync button icons (init already ran, but button exists now)
    var current = html.getAttribute('data-theme') || 'light';
    applyTheme(current);

    var toggle = document.getElementById('theme-toggle');
    if(toggle){
      toggle.addEventListener('click', function(){
        var cur = html.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        applyTheme(cur === 'dark' ? 'light' : 'dark');
      });
    }

    // Listen for system changes only if no saved preference
    try{
      var mql = window.matchMedia('(prefers-color-scheme: dark)');
      var handler = function(e){
        try{
          if(!localStorage.getItem(STORAGE_KEY)){
            applyTheme(e.matches ? 'dark' : 'light');
          }
        }catch(e2){}
      };
      if(mql.addEventListener) mql.addEventListener('change', handler);
      else if(mql.addListener) mql.addListener(handler);
    }catch(e){}

    // Mobile menu toggle
    var btn = document.getElementById('menu-btn');
    var menu = document.getElementById('mobile-menu');
    if(btn && menu){
      btn.addEventListener('click', function(){
        var open = menu.classList.contains('open');
        menu.classList.toggle('open', !open);
        btn.setAttribute('aria-expanded', !open);
        var iconOpen = btn.querySelector('[data-icon="open"]');
        var iconClose = btn.querySelector('[data-icon="close"]');
        if(iconOpen) iconOpen.style.display = open ? 'block' : 'none';
        if(iconClose) iconClose.style.display = open ? 'none' : 'block';
      });
    }

    // Reveal on scroll
    var reveals = document.querySelectorAll('.reveal');
    if('IntersectionObserver' in window){
      var io = new IntersectionObserver(function(entries){
        entries.forEach(function(e){
          if(e.isIntersecting){
            e.target.classList.add('in');
            io.unobserve(e.target);
          }
        });
      }, {threshold:0.12});
      reveals.forEach(function(el){ io.observe(el); });
    } else {
      reveals.forEach(function(el){ el.classList.add('in'); });
    }

    // Pricing toggle (monthly / annual)
    var toggle2 = document.getElementById('billing-toggle');
    if(toggle2){
      toggle2.addEventListener('change', function(){
        var annual = toggle2.checked;
        document.querySelectorAll('[data-price-monthly]').forEach(function(el){
          var m = el.getAttribute('data-price-monthly');
          var a = el.getAttribute('data-price-annual');
          el.textContent = annual ? a : m;
        });
        document.querySelectorAll('[data-billing-label]').forEach(function(el){
          el.textContent = annual ? 'billed annually' : 'billed monthly';
        });
        var badge = document.getElementById('annual-badge');
        if(badge) badge.style.display = annual ? 'inline-flex' : 'none';
      });
    }

    // FAQ accordion
    document.querySelectorAll('[data-faq-trigger]').forEach(function(trigger){
      trigger.addEventListener('click', function(){
        var item = trigger.closest('[data-faq-item]');
        var body = item.querySelector('[data-faq-body]');
        var icon = trigger.querySelector('[data-faq-icon]');
        var isOpen = item.getAttribute('data-open') === 'true';
        if(!isOpen && item.parentElement.hasAttribute('data-single')){
          item.parentElement.querySelectorAll('[data-faq-item][data-open="true"]').forEach(function(other){
            other.setAttribute('data-open','false');
            var b = other.querySelector('[data-faq-body]');
            var ic = other.querySelector('[data-faq-icon]');
            if(b) b.style.display='none';
            if(ic) ic.style.transform='rotate(0deg)';
          });
        }
        item.setAttribute('data-open', !isOpen);
        if(body) body.style.display = isOpen ? 'none' : 'block';
        if(icon) icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
      });
    });

    // Contact form — demo handler
    var form = document.getElementById('contact-form');
    if(form){
      form.addEventListener('submit', function(e){
        e.preventDefault();
        var btn2 = form.querySelector('button[type="submit"]');
        var note = document.getElementById('form-note');
        if(btn2){ btn2.disabled=true; btn2.textContent='Sending…'; }
        setTimeout(function(){
          if(btn2){ btn2.disabled=false; btn2.textContent='Send message'; }
          if(note){
            note.style.display='block';
            note.textContent='Thank you — your message has been received. We respond within one business day (often within 4 hours during CET business hours). You can also reach us directly at contact@focalis.cc or hello@focalis.cc';
            note.className='mt-4 p-3 rounded-md text-sm bg-[#E6F7F5] border border-[#BFE9E4] text-[#0F766E]';
            if(html.getAttribute('data-theme')==='dark'){
              note.style.background='#0F2A2A';
              note.style.borderColor='#1E4A4A';
              note.style.color='#2DD4BF';
            }
          }
          form.reset();
        }, 700);
      });
    }

    // Dodo checkout placeholder
    document.querySelectorAll('[data-dodo-checkout]').forEach(function(btn){
      btn.addEventListener('click', function(e){
        e.preventDefault();
        var product = btn.getAttribute('data-product') || 'this product';
        var toast = document.createElement('div');
        toast.setAttribute('role','status');
        toast.style.cssText='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#0F2342;color:white;padding:14px 20px;border-radius:8px;font-size:14px;box-shadow:0 8px 32px rgba(15,35,66,0.2);z-index:9999;display:flex;align-items:center;gap:10px;max-width:90vw';
        if(html.getAttribute('data-theme')==='dark'){
          toast.style.background='#E8E4DE';
          toast.style.color='#080C1A';
        }
        toast.innerHTML='<span style="width:8px;height:8px;background:#14B8A6;border-radius:50%;display:inline-block;flex-shrink:0"></span> Checkout for <strong>'+product+'</strong> is handled securely by Dodo Payments. Integration pending — you will be redirected to checkout when live.';
        document.body.appendChild(toast);
        setTimeout(function(){ toast.style.opacity='0'; toast.style.transition='opacity 0.4s'; setTimeout(function(){ toast.remove(); }, 400); }, 3500);
      });
    });

    // Hero 3D fallback handling — ensure canvas fallback to CSS if Three.js fails
    var heroCanvas = document.getElementById('hero-3d');
    if(heroCanvas){
      // If Three.js fails to init within 2s, show CSSfallback gradient opacity
      setTimeout(function(){
        if(!heroCanvas.hasAttribute('data-rendered')){
          heroCanvas.style.display='none';
          var mesh = document.querySelector('.hero-mesh');
          if(mesh) mesh.style.opacity='1';
        }
      }, 2500);
      // Video fallback: if video fails to load, show gradient
      var vid = document.querySelector('.video-wrap video');
      var fallback = document.querySelector('.video-fallback');
      if(vid && fallback){
        var showFallback = function(){ fallback.classList.add('video-fallback--show'); };
        vid.addEventListener('error', showFallback);
        // If video hasn't loaded after 4s, keep poster/fallback
        setTimeout(function(){
          if(vid.readyState < 2) { /* keep poster; fallback stays hidden unless error */ }
        }, 4000);
      }
    }
  });

  // Expose for hero Three.js init
  window.__focalisApplyTheme = applyTheme;
})();
