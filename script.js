/* Tooltech Technologies - site-wide behaviour (menu, slider, image fallback).
   No inline scripts are used anywhere on the site, so the Content-Security-Policy can
   block injected code. Everything runs from this file. */
(function () {
  "use strict";

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- mobile menu ---------- */
  var navbar = $("#navbar");
  var navLinks = $("#navLinks");
  var hamburger = $("#hamburger");

  function setMenu(open) {
    if (!navLinks || !hamburger) return;
    navLinks.classList.toggle("show", open);
    hamburger.classList.toggle("active", open);
    hamburger.setAttribute("aria-expanded", open ? "true" : "false");
    hamburger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }

  if (hamburger) {
    hamburger.addEventListener("click", function () {
      setMenu(!navLinks.classList.contains("show"));
    });
    hamburger.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        setMenu(!navLinks.classList.contains("show"));
      }
    });
  }
  $$(".nav-links a").forEach(function (a) {
    a.addEventListener("click", function () { setMenu(false); });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setMenu(false);
  });

  window.addEventListener("scroll", function () {
    if (navbar) navbar.classList.toggle("sticky", window.scrollY > 50);
  });

  /* ---------- hero slider ---------- */
  var slides = $$(".slide");
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (slides.length > 1 && !reduce) {
    var current = 0;
    setInterval(function () {
      slides[current].classList.remove("active");
      current = (current + 1) % slides.length;
      slides[current].classList.add("active");
    }, 5000);
  }

  /* ---------- keep page content clear of the fixed header ---------- */
  function setHeaderOffset() {
    var header = $("header");
    if (header) document.body.style.paddingTop = header.offsetHeight + "px";
  }
  window.addEventListener("load", setHeaderOffset);
  window.addEventListener("resize", setHeaderOffset);
  if (window.ResizeObserver && $("header")) new ResizeObserver(setHeaderOffset).observe($("header"));
  setHeaderOffset();

  /* ---------- picture fallback (replaces the old inline onerror="" attributes) ---------- */
  function useFallback(img) {
    if (!img || img.getAttribute("data-fell-back")) return;
    img.setAttribute("data-fell-back", "1");
    img.src = img.getAttribute("data-fallback") || "img/placeholder.svg";
  }
  document.addEventListener("error", function (e) {
    if (e.target && e.target.tagName === "IMG") useFallback(e.target);
  }, true);
  $$("img").forEach(function (img) {
    // pictures that already failed before this script ran
    if (img.complete && img.naturalWidth === 0 && img.getAttribute("src")) useFallback(img);
  });
})();
