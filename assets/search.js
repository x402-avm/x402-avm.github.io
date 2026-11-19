/* Replaces Mintlify's hosted search (unavailable on static hosting) with a Pagefind modal. */
(function () {
  var root, panel, lastFocus, loading, ui;
  var BASE = "/pagefind/";

  function load() {
    if (loading) return loading;
    loading = new Promise(function (ok, fail) {
      var l = document.createElement("link");
      l.rel = "stylesheet"; l.href = BASE + "pagefind-ui.css"; document.head.appendChild(l);
      var s = document.createElement("script");
      s.src = BASE + "pagefind-ui.js"; s.onload = ok; s.onerror = fail; document.head.appendChild(s);
    });
    return loading;
  }

  function build() {
    root = document.createElement("div");
    root.className = "xs-root";
    root.innerHTML = '<div class="xs-panel" role="dialog" aria-modal="true" aria-label="Search the docs"><div id="xs-ui"></div><p class="xs-hint">Esc to close</p></div>';
    document.body.appendChild(root);
    panel = root.firstChild;
    root.addEventListener("mousedown", function (e) { if (e.target === root) close(); });
    root.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.preventDefault(); close(); }
      else if (e.key === "Tab") trap(e);
    });
    root.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest("a[href]");
      if (a) close();
    });
  }

  function focusables() {
    return Array.prototype.filter.call(
      panel.querySelectorAll('a[href],button,input,[tabindex]:not([tabindex="-1"])'),
      function (el) { return !el.disabled && el.offsetParent !== null; });
  }

  function trap(e) {
    var f = focusables();
    if (!f.length) { e.preventDefault(); return; }
    var first = f[0], last = f[f.length - 1], a = document.activeElement;
    if (e.shiftKey && (a === first || !panel.contains(a))) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && (a === last || !panel.contains(a))) { e.preventDefault(); first.focus(); }
  }

  function focusInput() {
    var i = panel.querySelector("input");
    if (i) i.focus();
  }

  function open() {
    if (!root) build();
    if (root.hasAttribute("data-open")) { focusInput(); return; }
    lastFocus = document.activeElement;
    root.setAttribute("data-open", "");
    document.documentElement.style.overflow = "hidden";
    load().then(function () {
      if (!ui) ui = new PagefindUI({ element: "#xs-ui", showSubResults: true, showImages: false, resetStyles: false,
        translations: { placeholder: "Search the docs" } });
      focusInput();
    }).catch(function () {
      panel.querySelector("#xs-ui").textContent = "Search is unavailable right now.";
    });
    focusInput();
  }

  function close() {
    if (!root) return;
    root.removeAttribute("data-open");
    document.documentElement.style.overflow = "";
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function swallow(e) { e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); }

  window.addEventListener("click", function (e) {
    var t = e.target.closest && e.target.closest('[data-search-item="trigger"],#search-bar-entry,#search-bar-entry-mobile');
    if (!t) return;
    swallow(e); open();
  }, true);

  window.addEventListener("keydown", function (e) {
    if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey) && !e.altKey && !e.shiftKey) {
      swallow(e); root && root.hasAttribute("data-open") ? close() : open();
    } else if (e.key === "/" && !e.metaKey && !e.ctrlKey && !e.altKey) {
      var el = document.activeElement, tag = el && el.tagName;
      if (!(tag === "INPUT" || tag === "TEXTAREA" || (el && el.isContentEditable))) { swallow(e); open(); }
    }
  }, true);
})();
