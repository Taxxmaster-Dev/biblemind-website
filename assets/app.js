(function () {
  'use strict';

  var nav = document.querySelector('.nav');
  var burger = document.getElementById('burger');
  var links = document.getElementById('navlinks');
  var langmenu = document.querySelector('.langmenu');
  var langbtn = document.getElementById('langbtn');

  function closeMenu() {
    if (!nav || !burger) return;
    nav.classList.remove('open');
    burger.setAttribute('aria-expanded', 'false');
  }

  function closeLang() {
    if (!langmenu || !langbtn) return;
    langmenu.classList.remove('open');
    langbtn.setAttribute('aria-expanded', 'false');
  }

  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (!open) closeLang();
    });
  }

  if (langbtn && langmenu) {
    langbtn.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var open = langmenu.classList.toggle('open');
      langbtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // Close the mobile menu after jumping to a section on the same page.
  if (links) {
    links.addEventListener('click', function (ev) {
      var a = ev.target.closest('a');
      if (a && a.getAttribute('href') && a.getAttribute('href').indexOf('#') > -1) {
        closeMenu();
        closeLang();
      }
    });
  }

  document.addEventListener('click', function (ev) {
    if (langmenu && !langmenu.contains(ev.target)) closeLang();
    if (nav && !nav.contains(ev.target)) closeMenu();
  });

  // An explicit pick in the language selector or the language grid wins over the
  // browser setting: the inline detector on the root page skips once this is set.
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest && ev.target.closest('a[hreflang]');
    if (!a) return;
    try { localStorage.setItem('bm_lang', a.getAttribute('hreflang')); } catch (err) {}
  });

  // Anchor jumps: a calm glide that eases in and settles slowly on arrival.
  // CSS keeps `scroll-behavior:smooth` as the no-JS fallback, but it has to be
  // switched off while we animate: it would turn every frame of ours into its
  // own smooth scroll, and the two would lag against each other.
  var root = document.documentElement;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var gliding = false;

  function stopGlide() {
    gliding = false;
    root.style.scrollBehavior = '';
  }

  function targetTop(el) {
    var offset = nav ? nav.getBoundingClientRect().height + 20 : 0;
    var max = Math.max(0, root.scrollHeight - window.innerHeight);
    var y = window.pageYOffset + el.getBoundingClientRect().top - offset;
    return Math.max(0, Math.min(y, max));
  }

  function land(el, hash) {
    stopGlide();
    if (window.history && history.pushState) history.pushState(null, '', hash);
    if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
    el.focus({ preventScroll: true });
  }

  function glideTo(el, hash) {
    var from = window.pageYOffset;
    var dist = targetTop(el) - from;
    root.style.scrollBehavior = 'auto';

    if (reduce.matches || Math.abs(dist) < 2) {
      window.scrollTo(0, from + dist);
      land(el, hash);
      return;
    }

    // Longer jumps get more time, but never drag on.
    var time = Math.min(1500, Math.max(620, Math.abs(dist) * 0.55));
    var start = 0;
    gliding = true;

    requestAnimationFrame(function step(now) {
      if (!gliding) return;
      if (!start) start = now;
      var t = Math.min(1, (now - start) / time);
      // easeInOutQuart: a soft push off, then a long, slow landing.
      var k = t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(2 - 2 * t, 4) / 2;
      window.scrollTo(0, from + dist * k);
      if (t < 1) return requestAnimationFrame(step);
      land(el, hash);
    });
  }

  // Any real scroll input hands control straight back to the visitor.
  ['wheel', 'touchstart', 'keydown'].forEach(function (type) {
    window.addEventListener(type, function () { if (gliding) stopGlide(); }, { passive: true });
  });

  document.addEventListener('click', function (ev) {
    if (ev.defaultPrevented || ev.button || ev.metaKey || ev.ctrlKey ||
        ev.shiftKey || ev.altKey) return;
    var a = ev.target && ev.target.closest && ev.target.closest('a[href]');
    if (!a || a.target === '_blank' || !a.hash || a.hash === '#') return;
    // Same document only: `./#features` from a legal page must stay a real load.
    if (a.host !== location.host || a.pathname !== location.pathname) return;
    var el = document.getElementById(a.hash.slice(1));
    if (!el) return;
    ev.preventDefault();
    glideTo(el, a.hash);
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') {
      closeLang();
      closeMenu();
      if (langbtn) langbtn.focus();
    }
  });

})();
