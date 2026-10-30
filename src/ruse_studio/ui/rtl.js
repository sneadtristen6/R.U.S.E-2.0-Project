// Persian in an app laid out left to right (the owner, 2026-10-30: Persian in the Studio and the Launcher). Each piece
// of text with Persian letters reads right to left in its own box (its element gets dir="rtl"), and text boxes follow
// what's typed in them (dir="auto"); the window keeps its layout. The same file in both apps (tests/test_languages.py).
// rtlText(true) when the language is written right to left (the languages list's `rtl`), rtlText(false) otherwise: a
// watcher keeps up with everything the page draws later.
(function () {
  const LETTERS = /[֐-ࣿיִ-﷿ﹰ-﻿]/;  // Hebrew and Arabic script: Persian's letters
  const TYPED = "input:not([type]), input[type=text], input[type=search], textarea";
  let watcher = null;

  function mark(el) {
    if (!el || el.nodeType !== 1 || el.closest("svg")) return;
    if (el.matches(TYPED)) {
      if (!el.hasAttribute("dir")) { el.dir = "auto"; el.dataset.rtl = ""; }
      return;
    }
    let rtl = false;
    if (el.matches("ol, ul")) rtl = [...el.children].some((li) => LETTERS.test(li.textContent));  // its numbers on the right
    else for (const n of el.childNodes) if (n.nodeType === 3 && LETTERS.test(n.data)) { rtl = true; break; }
    if (rtl && !el.hasAttribute("dir")) { el.dir = "rtl"; el.dataset.rtl = ""; }
    else if (!rtl && el.dataset.rtl !== undefined) { el.removeAttribute("dir"); delete el.dataset.rtl; }
    if (el.tagName === "LI" && el.parentElement) mark(el.parentElement);
  }

  function sweep(node) {
    if (node.nodeType === 3) return mark(node.parentElement);
    if (node.nodeType !== 1) return;
    mark(node);
    for (const el of node.querySelectorAll("*")) mark(el);
  }

  window.rtlText = function (on) {
    if (watcher) { watcher.disconnect(); watcher = null; }
    if (!on) {
      for (const el of document.querySelectorAll("[data-rtl]")) { el.removeAttribute("dir"); delete el.dataset.rtl; }
      return;
    }
    sweep(document.body);
    watcher = new MutationObserver((changes) => {
      for (const c of changes) {
        if (c.type === "characterData") { mark(c.target.parentElement); continue; }
        mark(c.target);
        for (const n of c.addedNodes) sweep(n);
      }
    });
    watcher.observe(document.body, { childList: true, subtree: true, characterData: true });
  };
})();
