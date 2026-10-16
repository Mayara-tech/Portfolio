/* Portfólio Mayara Alves · v2.0
   Sem dependências. A página funciona inteira sem este arquivo;
   ele só acrescenta menu móvel, seção ativa, revelação ao rolar e copiar e-mail. */
(function () {
  "use strict";

  var header = document.querySelector(".header");
  var nav = document.getElementById("nav");
  var btn = document.querySelector(".menu-btn");

  /* menu móvel */
  function closeMenu() {
    if (!nav || !btn) return;
    nav.classList.remove("is-open");
    btn.setAttribute("aria-expanded", "false");
  }
  if (nav && btn) {
    btn.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) {
        var first = nav.querySelector("a");
        if (first) first.focus({ preventScroll: true });
      }
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) closeMenu();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        closeMenu();
        btn.focus();
      }
    });
    window.matchMedia("(min-width: 901px)").addEventListener("change", function (mq) {
      if (mq.matches) closeMenu();
    });
  }

  /* borda do cabeçalho depois de rolar */
  function onScroll() {
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 8);
  }
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  /* troca de idioma preserva a seção atual */
  var lang = document.querySelector(".lang");
  if (lang) {
    lang.addEventListener("click", function () {
      var base = lang.getAttribute("href").split("#")[0];
      lang.setAttribute("href", base + (location.hash || ""));
    });
  }

  if (!("IntersectionObserver" in window)) return;

  /* link da seção visível marcado no menu */
  var links = nav ? Array.prototype.slice.call(nav.querySelectorAll('.nav__list a[href^="#"]')) : [];
  var byId = {};
  links.forEach(function (a) { byId[a.getAttribute("href").slice(1)] = a; });
  var spy = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (!en.isIntersecting) return;
      links.forEach(function (a) { a.removeAttribute("aria-current"); });
      var a = byId[en.target.id];
      if (a) a.setAttribute("aria-current", "true");
    });
  }, { rootMargin: "-45% 0px -50% 0px" });
  Object.keys(byId).forEach(function (id) {
    var s = document.getElementById(id);
    if (s) spy.observe(s);
  });

  /* revelação suave ao rolar */
  var reveal = new IntersectionObserver(function (entries) {
    entries.forEach(function (en) {
      if (en.isIntersecting) {
        en.target.classList.add("is-in");
        reveal.unobserve(en.target);
      }
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });
  document.querySelectorAll(".reveal").forEach(function (el) { reveal.observe(el); });
})();

/* copiar e-mail */
(function () {
  var b = document.querySelector("[data-copy]");
  if (!b || !navigator.clipboard) {
    if (b) b.hidden = true;
    return;
  }
  var original = b.textContent;
  b.addEventListener("click", function () {
    navigator.clipboard.writeText(b.getAttribute("data-copy")).then(function () {
      b.textContent = b.getAttribute("data-done");
      setTimeout(function () { b.textContent = original; }, 1800);
    }, function () {
      b.hidden = true;
    });
  });
})();
