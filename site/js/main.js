/* Hack the Pool 2026 · Choreografie
   Hero, Scroll-Szenen (GSAP + ScrollTrigger), Live-Daten und Charts, Filmstreifen, Karte, Konsole. */
(function () {
  "use strict";
  window.HTP_READY = true;

  var root = document.documentElement;
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var params = new URLSearchParams(location.search);
  var OG = params.has("og");
  var motion = root.dataset.motion !== "calm";
  var G = window.gsap, ST = window.ScrollTrigger;
  var fmt = new Intl.NumberFormat("de-DE");
  var led = function (n) { return fmt.format(n).replace(/\./g, "\u202f"); };
  // Der Doppelpunkt der Punktschrift liest sich wie ein Kreuz, daher Plex Mono dafür
  var ledTime = function (s) { return String(s).replace(/:/g, '<span class="colon">:</span>'); };
  var pct = function (v) { return (v * 100).toFixed(1).replace(".", ",") + " %"; };

  if (G) {
    G.registerPlugin.apply(G, ["ScrollTrigger", "SplitText", "ScrambleTextPlugin", "DrawSVGPlugin", "Draggable", "InertiaPlugin"].map(function (n) { return window[n]; }).filter(Boolean));
    G.defaults({ ease: "power3.out" });
  }
  var anim = !!(G && ST && motion && !OG);
  if (!anim) root.classList.remove("anim");

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  /* ------------------------------------------------------------------
     Zeit: Anmeldeschluss und Event (Wiener Zeit). ?now=2026-10-27T15:00:00%2B01:00 simuliert.
     ------------------------------------------------------------------ */
  var offset = 0;
  if (params.get("now")) { var sim = new Date(params.get("now")); if (!isNaN(sim)) offset = sim - Date.now(); }
  function now() { return new Date(Date.now() + offset); }
  var DEADLINE = new Date("2026-10-06T23:59:59+02:00");
  var EVENT_START = new Date("2026-10-27T09:00:00+01:00");
  var EVENT_END = new Date("2026-10-28T16:30:00+01:00");
  var DAY2 = new Date("2026-10-28T00:00:00+01:00");
  var INFO_URL = "https://info.kulturpool.at/hack-the-pool-2026/";
  var pad = function (n) { return String(n).padStart(2, "0"); };
  function span(ms) { var s = Math.max(0, Math.floor(ms / 1000)); return { d: Math.floor(s / 86400), h: Math.floor((s % 86400) / 3600), m: Math.floor((s % 3600) / 60), s: s % 60 }; }
  var dayFmt = new Intl.DateTimeFormat("de-AT", { timeZone: "Europe/Vienna", year: "numeric", month: "2-digit", day: "2-digit" });

  var regText = $("[data-reg-text]"), regCd = $("[data-reg-countdown]"), regCta = $("[data-reg-cta]");
  var heroCta = $("[data-reg-cta-hero]"), hudCta = $("[data-hud-cta]"), eventState = $("[data-event-state]");
  var regMode = null;

  function registration(n) {
    if (n <= DEADLINE) {
      var t = span(DEADLINE - n), lastDay = dayFmt.format(n) === dayFmt.format(DEADLINE);
      if (regMode !== "open") {
        regMode = "open";
        if (regText) regText.innerHTML = lastDay ? "Heute ist der letzte Tag. Anmeldung bis <strong>23:59</strong>" : "Anmeldung bis <strong>6. Oktober 2026, 23:59</strong>";
        var short = $("[data-reg-short]"); if (short && lastDay) short.textContent = "nur noch heute";
      }
      if (regCd) regCd.innerHTML = ledTime((t.d > 0 ? t.d + "T " : "") + pad(t.h) + ":" + pad(t.m) + ":" + pad(t.s));
      return;
    }
    var live = n >= EVENT_START && n < EVENT_END, over = n >= EVENT_END, e = span(EVENT_START - n);
    if (regMode !== "closed") {
      regMode = "closed";
      if (regText) regText.innerHTML = over ? "Das war Hack the Pool 2026. <strong>Danke an alle Teams.</strong>" : "Anmeldung geschlossen. <strong>Wir sehen uns am 27. Oktober.</strong>";
      if (regCta) { regCta.textContent = over ? "Ergebnisse auf GitHub" : "Infos zum Event"; regCta.href = over ? "https://github.com/kulturpool/Hack-The-Pool-2026" : INFO_URL; }
      if (heroCta) { heroCta.textContent = "Programm"; heroCta.href = "#programm"; }
      if (hudCta) { hudCta.textContent = "Programm"; hudCta.href = "#programm"; }
    }
    if (regCd) regCd.innerHTML = live ? "Live" : over ? "" : ledTime(e.d + "T " + pad(e.h) + ":" + pad(e.m) + ":" + pad(e.s));
  }

  function markSlots(n) {
    $$(".day").forEach(function (day) {
      $$(".slots li", day).forEach(function (li) {
        var s = new Date(day.dataset.day + "T" + li.dataset.t + ":00+01:00");
        var e = li.dataset.end ? new Date(day.dataset.day + "T" + li.dataset.end + ":00+01:00") : new Date(s.getTime() + 30 * 60000);
        li.classList.toggle("is-now", n >= s && n < e);
        li.classList.toggle("is-past", n >= e);
      });
    });
    if (!eventState) return;
    if (n < EVENT_START) { var t = span(EVENT_START - n); eventState.textContent = t.d > 1 ? "Noch " + t.d + " Tage bis zum Start" : t.d === 1 ? "Morgen geht’s los" : "Heute geht’s los"; }
    else if (n < EVENT_END) eventState.textContent = "Live · Tag " + (n < DAY2 ? 1 : 2);
    else eventState.textContent = "Vorbei";
  }

  function tick() {
    var n = now();
    registration(n);
    if (!tick.done || n.getSeconds() % 20 === 0) { markSlots(n); tick.done = true; }
  }
  $$(".slots time").forEach(function (t) { t.setAttribute("datetime", t.textContent); t.innerHTML = ledTime(t.textContent); });
  tick();
  setInterval(tick, 1000);

  // Tagesbalken: Blöcke maßstäblich von 9 bis 22 Uhr
  $$(".day").forEach(function (day) {
    var bar = $(".day__bar", day); if (!bar) return;
    var from = 9, total = 13;
    $$(".slots li", day).forEach(function (li) {
      if (!li.dataset.end) return;
      var a = li.dataset.t.split(":"), b = li.dataset.end.split(":");
      var s = +a[0] + a[1] / 60, e = +b[0] + b[1] / 60, i = el("i");
      i.style.left = ((s - from) / total * 100) + "%";
      i.style.width = ((e - s) / total * 100) + "%";
      i.style.setProperty("--c", li.classList.contains("is-hack") ? "var(--cyan)" : li.classList.contains("is-key") ? "var(--magenta)" : li.classList.contains("is-food") ? "var(--line-2)" : "var(--violet)");
      bar.appendChild(i);
    });
    var ticks = el("div", "day__ticks"); ticks.setAttribute("aria-hidden", "true");
    ["09", "12", "15", "18", "22"].forEach(function (h) { ticks.appendChild(el("span", "", h)); });
    bar.insertAdjacentElement("afterend", ticks);
  });

  /* ------------------------------------------------------------------
     Menü (mobil)
     ------------------------------------------------------------------ */
  var menuBtn = $(".hud__menu"), menu = $("#menu");
  function setMenu(open) {
    if (!menu || !menuBtn) return;
    menuBtn.setAttribute("aria-expanded", String(open));
    menu.hidden = !open;
    if (open) {
      if (anim) G.from($$("a", menu), { y: 40, opacity: 0, stagger: 0.04, duration: 0.5 });
      var first = $("a", menu); if (first) first.focus();
    }
  }
  if (menuBtn) menuBtn.addEventListener("click", function () { setMenu(menu.hidden); });
  if (menu) menu.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && menu && !menu.hidden) { setMenu(false); menuBtn.focus(); } });

  /* ------------------------------------------------------------------
     Titel auf Satzbreite dehnen (Breitenachse von Anybody)
     ------------------------------------------------------------------ */
  function fitWidth(h, max) {
    var target = h.firstElementChild || h, isMark = h.classList.contains("foot__mark");
    h.classList.remove("is-wrapped");
    var avail = h.clientWidth, lo = 50, hi = max || 150, best = 50;
    if (!avail) return;
    var measure = function () { return isMark ? h.scrollWidth : target.getBoundingClientRect().width; };
    for (var i = 0; i < 8; i++) {
      var mid = (lo + hi) / 2;
      h.style.setProperty("--wdth", mid);
      if (measure() <= avail + 0.5) { best = mid; lo = mid; } else hi = mid;
    }
    h.style.setProperty("--wdth", best);
    h.dataset.fitted = best;
    if (best <= 50.5 && measure() > avail + 1) h.classList.add("is-wrapped");
  }
  function fitAll() {
    $$("[data-stretch], .foot__mark").forEach(function (h) { fitWidth(h, 150); });
    $$(".quest__name[data-fit]").forEach(function (h) { fitWidth(h, +h.dataset.fit || 130); });
  }

  /* ------------------------------------------------------------------
     Wortmarke und Hero
     ------------------------------------------------------------------ */
  var wordmark = null;
  function initWordmark() {
    var c = $(".wordmark");
    if (!c || !window.DotMatrix) return;
    try {
      wordmark = new DotMatrix(c, { box: $(".hero__title"), turbo: motion && !OG, assembled: !anim });
      root.classList.add("wm-ready");
      $(".hero__title").addEventListener("click", function () { wordmark.burst(); });
    } catch (e) { if (window.console) console.warn("[wordmark]", e); }
  }

  function heroIntro() {
    if (!anim) { $$("[data-hero], .hero__title").forEach(function (x) { x.style.opacity = 1; }); if (wordmark) wordmark.setActive(true); return; }
    var tl = G.timeline();
    tl.set(".hero__title", { opacity: 1 }, 0);
    if (wordmark) tl.add(wordmark.assemble(2.6), 0); else tl.from(".hero__fallback", { opacity: 0, y: 40, duration: 1 }, 0);
    var credits = $("[data-hero='credits'] [data-scramble]");
    tl.set("[data-hero='credits']", { opacity: 1 }, 0.2)
      .to(credits, { duration: 1.4, scrambleText: { text: credits.textContent, chars: "upperCase", speed: 0.6 } }, 0.2)
      .set("[data-hero='tagline']", { opacity: 1 }, 1.3);
    if (window.SplitText) {
      var split = SplitText.create("[data-hero='tagline']", { type: "words,chars", charsClass: "char" });
      tl.from(split.chars, { yPercent: 120, rotation: 10, opacity: 0, duration: 0.7, stagger: 0.022, ease: "back.out(2)" }, 1.3);
    }
    tl.set("[data-hero='row']", { opacity: 1 }, 1.7)
      .from("[data-hero='row'] > *", { y: 32, opacity: 0, duration: 0.9, stagger: 0.1 }, 1.7)
      .to(".hero__date .led", { duration: 1.2, scrambleText: { text: $(".hero__date .led").textContent, chars: "0123456789", speed: 0.8 } }, 1.7)
      .from(".ticker", { yPercent: 100, duration: 0.8 }, 2.1);
  }

  /* ------------------------------------------------------------------
     Videos: Retro-Fenster in allen Bereichen, Pool im Finale. Laden erst bei Sichtkontakt.
     ------------------------------------------------------------------ */
  var videos = $$(".win video, .finale__video");
  function ensureSrc(v) { if (!v.getAttribute("src") && v.dataset.src) { v.src = v.dataset.src; v.load(); } }
  function start(v) { ensureSrc(v); var p = v.play(); if (p && p.catch) p.catch(function () {}); }
  function hms(t) { t = Math.floor(t); return pad(Math.floor(t / 3600)) + ":" + pad(Math.floor((t % 3600) / 60)) + ":" + pad(t % 60); }
  function syncBtn(v) { if (!v._btn) return; v._btn.textContent = v.paused ? "Abspielen" : "Pause"; v._btn.setAttribute("aria-pressed", String(!v.paused)); }
  $$(".win").forEach(function (win) {
    var v = $("video", win); if (!v) return;
    var btn = $("[data-play]", win), tc = $("[data-tc]", win), base = 0;
    v._btn = btn;
    if (tc) { var p = tc.textContent.split(":"); base = (+p[0]) * 3600 + (+p[1]) * 60 + (+p[2]); }
    var cues = []; try { cues = JSON.parse(v.dataset.cues || "[]"); } catch (e) {}
    var sub = $(".win__sub", win);
    v.addEventListener("timeupdate", function () {
      var t = v.currentTime, txt = "";
      if (tc) tc.textContent = hms(base + t);
      for (var i = 0; i < cues.length; i++) if (t >= cues[i][0] && t < cues[i][1]) { txt = cues[i][2]; break; }
      if (sub && sub.textContent !== txt) sub.textContent = txt;
    });
    v.addEventListener("play", function () { syncBtn(v); });
    v.addEventListener("pause", function () { syncBtn(v); });
    var toggle = function () { if (v.paused) { v._userPaused = false; start(v); } else { v._userPaused = true; v.pause(); } };
    if (btn) btn.addEventListener("click", toggle);
    $(".win__body", win).addEventListener("click", toggle);
    syncBtn(v);
  });
  if ("IntersectionObserver" in window) {
    var vio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        var v = en.target;
        if (en.isIntersecting) { if (motion && !OG && !v._userPaused) start(v); else ensureSrc(v); }
        else if (!v.paused) v.pause();
      });
    }, { rootMargin: "80px 0px", threshold: 0.15 });
    videos.forEach(function (v) { vio.observe(v); });
  } else videos.forEach(function (v) { if (motion) start(v); });

  // Fenster: ziehen, Zoom-Rechtecke beim Öffnen (wie im Finder von 1995)
  var zTop = 10;
  function zoomOpen(win) {
    var r = win.getBoundingClientRect();
    for (var i = 0; i < 4; i++) {
      var z = el("div", "zoomrect");
      document.body.appendChild(z);
      G.fromTo(z, { left: r.left + r.width / 2 - 12, top: r.top + r.height / 2 - 9, width: 24, height: 18, opacity: 1 },
        { left: r.left, top: r.top, width: r.width, height: r.height, opacity: 0.25, duration: 0.42, delay: i * 0.07, ease: "power2.out", onComplete: z.remove.bind(z) });
    }
    G.fromTo(win, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.25, delay: 0.42 });
  }
  function windows() {
    $$("[data-window]").forEach(function (win) {
      if (G) G.set(win, { rotation: win.classList.contains("win--tilt-l") ? -1.8 : win.classList.contains("win--tilt-r") ? 1.6 : 0 });
      var bar = $(".win__bar", win);
      if (window.Draggable && bar) Draggable.create(win, {
        type: "x,y", trigger: bar, inertia: !!window.InertiaPlugin, edgeResistance: 0.75,
        bounds: win.closest(".sec, .finale") || document.body,
        onPress: function () { win.style.zIndex = ++zTop; },
        onDragStart: function () { win.classList.add("is-dragging"); },
        onRelease: function () { win.classList.remove("is-dragging"); }
      });
      if (anim) { G.set(win, { autoAlpha: 0 }); ST.create({ trigger: win, start: "top 88%", once: true, onEnter: function () { zoomOpen(win); } }); }
    });
  }

  /* ------------------------------------------------------------------
     Inhaltsfenster: alle Bereiche und Unterpunkte, mit Fortschritt
     ------------------------------------------------------------------ */
  var questTween = null;
  var TOC = [
    { id: "top", label: "Start" },
    { id: "event", label: "Event", sub: [["fuer-wen", "Für wen"], ["bereit", "Was bereitsteht"]] },
    { id: "pool", label: "Der Pool", sub: [["zeitstrahl", "Jahrhunderte"], ["bildfarben", "Bildfarben"], ["partner", "Partnerinstitutionen"]] },
    { id: "quests", label: "Quests", sub: [["q-lod", "Linked Open Data"], ["q-similarity", "Similarity"], ["q-quality", "Data Quality"], ["q-interfaces", "Interfaces"], ["q-verification", "Verification"]] },
    { id: "programm", label: "Programm", sub: [["tag-1", "Di 27. Oktober"], ["tag-2", "Mi 28. Oktober"]] },
    { id: "daten", label: "Daten & APIs", sub: [["live-suche", "Live-Suche"], ["ressourcen", "Endpunkte"], ["sparql", "SPARQL"]] },
    { id: "beispiele", label: "Beispiele", sub: [["disketten", "Beispiele 2026"], ["vorjahr", "Vorjahr 2025"]] },
    { id: "ort", label: "Ort" },
    { id: "anmeldung", label: "Anmeldung" }
  ];
  function initToc() {
    var toc = $("#toc"), list = $("#toc-list"); if (!toc || !list) return;
    var secs = [], subs = [];
    TOC.forEach(function (t) {
      var target = document.getElementById(t.id); if (!target) return;
      var li = el("li", "toc__sec"), a = el("a");
      a.href = "#" + t.id; a.appendChild(el("span", "", t.label));
      var mini = el("span", "toc__bar-mini"), fill = el("i"); mini.appendChild(fill); mini.setAttribute("aria-hidden", "true"); a.appendChild(mini);
      li.appendChild(a); list.appendChild(li);
      secs.push({ el: target, li: li, fill: fill, label: t.label });
      if (t.sub) {
        var ol = el("ol");
        t.sub.forEach(function (s) {
          var se = document.getElementById(s[0]); if (!se) return;
          var sl = el("li"), sa = el("a", "", s[1]); sa.href = "#" + s[0];
          sl.appendChild(sa); ol.appendChild(sl);
          subs.push({ el: se, a: sa, sec: t.id });
        });
        li.appendChild(ol);
      }
    });
    list.addEventListener("click", function (e) {
      var a = e.target.closest("a"); if (!a) return;
      var id = a.hash.slice(1), qi = ["q-lod", "q-similarity", "q-quality", "q-interfaces", "q-verification"].indexOf(id);
      if (qi > -1 && questTween && questTween.scrollTrigger) {
        e.preventDefault();
        var st = questTween.scrollTrigger;
        window.scrollTo({ top: st.start + (st.end - st.start) * (qi / 4) + 2, behavior: motion ? "smooth" : "auto" });
      }
    });
    var toggle = $(".toc__toggle", toc);
    function setOpen(open) { toc.classList.toggle("is-collapsed", !open); toggle.setAttribute("aria-expanded", String(open)); }
    toggle.addEventListener("click", function () { setOpen(toc.classList.contains("is-collapsed")); });
    var foot = $("[data-toc-open]", toc); if (foot) foot.addEventListener("click", function () { setOpen(toc.classList.contains("is-collapsed")); });
    list.addEventListener("click", function (e) { if (e.target.closest("a")) setTimeout(function () { setOpen(false); }, 400); });
    if (window.Draggable && G) Draggable.create(toc, { type: "x,y", trigger: $(".toc__bar", toc), bounds: window, edgeResistance: 0.8, inertia: !!window.InertiaPlugin });
    var pos = $("[data-toc-pos]", toc), meter = $("[data-toc-progress]", toc), waiting = false;
    function update() {
      waiting = false;
      var line = window.innerHeight * 0.4, cur = secs[0];
      toc.classList.toggle("is-on", window.scrollY > window.innerHeight * 0.55);
      secs.forEach(function (s) {
        var r = s.el.getBoundingClientRect();
        if (r.top <= line) cur = s;
        var p = Math.max(0, Math.min(1, (line - r.top) / Math.max(1, r.height)));
        s.fill.style.transform = "scaleX(" + p.toFixed(3) + ")";
      });
      secs.forEach(function (s) { s.li.classList.toggle("is-current", s === cur); });
      var curSub = null;
      subs.forEach(function (s) {
        var r = s.el.getBoundingClientRect();
        if (s.sec === cur.el.id && r.top <= line && r.left < window.innerWidth * 0.5) curSub = s;
      });
      subs.forEach(function (s) { s.a.classList.toggle("is-current", s === curSub); });
      if (pos) pos.textContent = curSub ? curSub.a.textContent : cur.label;
      var max = document.documentElement.scrollHeight - window.innerHeight;
      if (meter) meter.style.transform = "scaleX(" + (max > 0 ? window.scrollY / max : 0).toFixed(3) + ")";
    }
    window.addEventListener("scroll", function () { if (!waiting) { waiting = true; requestAnimationFrame(update); } }, { passive: true });
    window.addEventListener("resize", update);
    update();
  }

  /* ------------------------------------------------------------------
     Pins: Halbton-Punkte für die Similarity-Quest
     ------------------------------------------------------------------ */
  (function halftone() {
    var g = $("[data-halftone]"); if (!g) return;
    var out = "", step = 7.4;
    for (var y = -88, row = 0; y <= 88; y += step, row++) {
      for (var x = -88; x <= 88; x += step) {
        var px = x + (row % 2) * step / 2, py = y;
        if (px * px + py * py > 80 * 80) continue;
        var d1 = Math.hypot(px + 21, py + 16), d2 = Math.hypot(px - 21, py + 16);
        var i1 = Math.max(0, 1 - d1 / 46), i2 = Math.max(0, 1 - d2 / 46);
        var v = Math.min(1, i1 + i2 + (i1 > 0 && i2 > 0 ? 0.3 : 0));
        if (py > 26) v *= 0.12;
        if (v < 0.07) continue;
        var t = (py + 88) / 176;
        out += '<circle cx="' + px.toFixed(1) + '" cy="' + py.toFixed(1) + '" r="' + (0.6 + v * 3.2).toFixed(2) + '" fill="rgb(255,' + Math.round(150 - t * 110) + ',' + Math.round(40 - t * 20) + ')"/>';
      }
    }
    g.innerHTML = out;
  })();

  /* ------------------------------------------------------------------
     Charts: Zeitstrahl, Bildfarben, Partnerinstitutionen
     ------------------------------------------------------------------ */
  var CENTURIES = [
    { from: null, to: 1000, label: "vor dem Jahr 1000", short: "<1000" },
    { from: 1000, to: 1100, label: "11. Jahrhundert", short: "11." },
    { from: 1100, to: 1200, label: "12. Jahrhundert", short: "12." },
    { from: 1200, to: 1300, label: "13. Jahrhundert", short: "13." },
    { from: 1300, to: 1400, label: "14. Jahrhundert", short: "14." },
    { from: 1400, to: 1500, label: "15. Jahrhundert", short: "15." },
    { from: 1500, to: 1600, label: "16. Jahrhundert", short: "16." },
    { from: 1600, to: 1700, label: "17. Jahrhundert", short: "17." },
    { from: 1700, to: 1800, label: "18. Jahrhundert", short: "18." },
    { from: 1800, to: 1900, label: "19. Jahrhundert", short: "19." },
    { from: 1900, to: 2000, label: "20. Jahrhundert", short: "20." },
    { from: 2000, to: 2100, label: "21. Jahrhundert", short: "21." }
  ];
  // Stand 6.10.2026, wird live ersetzt
  var SNAP_TIME = [17311, 231, 647, 6083, 18276, 27148, 78392, 95430, 218002, 697349, 523410, 179436];
  var SNAP_COLORS = { brown: 1043201, white: 841151, gray: 603106, black: 60557, blue: 18092, green: 11534, red: 10125, orange: 4477, pink: 3324, teal: 2510, yellow: 1662, purple: 911 };
  var COLOR_INFO = {
    brown: ["Braun", "#8a5b37"], white: ["Weiß", "#ebe5d8"], gray: ["Grau", "#8e8b94"], black: ["Schwarz", "#2a282e"],
    blue: ["Blau", "#3570e6"], green: ["Grün", "#2fa851"], red: ["Rot", "#e2382f"], orange: ["Orange", "#f08a24"],
    pink: ["Rosa", "#f08bbd"], teal: ["Petrol", "#1ea4a1"], yellow: ["Gelb", "#f2cf1f"], purple: ["Violett", "#8b50d8"]
  };
  var NEUTRAL = { brown: 1, white: 1, gray: 1, black: 1 };
  var shown = {};

  function tipFor(chart) {
    var t = $(".tip", chart);
    if (!t) { t = el("div", "tip"); t.setAttribute("aria-hidden", "true"); chart.appendChild(t); }
    return t;
  }
  function bindTip(chart, mark, value, label) {
    var tip = tipFor(chart);
    var show = function () {
      tip.textContent = "";
      tip.appendChild(el("b", "", value));
      tip.appendChild(document.createTextNode(label));
      var c = chart.getBoundingClientRect(), r = mark.getBoundingClientRect();
      var x = r.left + r.width / 2 - c.left;
      x = Math.max(tip.offsetWidth / 2 + 4, Math.min(c.width - tip.offsetWidth / 2 - 4, x));
      tip.style.left = x + "px";
      tip.style.top = (r.top - c.top) + "px";
      tip.classList.add("is-on");
    };
    var hide = function () { tip.classList.remove("is-on"); };
    mark.addEventListener("pointerenter", show);
    mark.addEventListener("focus", show);
    mark.addEventListener("pointerleave", hide);
    mark.addEventListener("blur", hide);
  }

  function renderTime(values) {
    var box = $("[data-cols]"), chart = $("[data-chart='time']");
    if (!box || !chart) return;
    var max = Math.max.apply(null, values), step = 200000, top = Math.ceil(max / step) * step;
    box.innerHTML = "";
    box.style.setProperty("--n", values.length);
    box.setAttribute("role", "list");
    box.setAttribute("aria-label", "Objekte nach Jahrhundert");
    for (var t = 0; t <= top; t += step) {
      var g = el("div", "cols__grid" + (t === 0 ? " cols__grid--base" : ""));
      g.style.bottom = (t / top * 100) + "%";
      g.setAttribute("aria-hidden", "true");
      g.appendChild(el("span", "cols__tick", fmt.format(t)));
      box.appendChild(g);
    }
    var maxIdx = values.indexOf(max);
    values.forEach(function (n, i) {
      var c = CENTURIES[i], col = el("div", "col");
      col.tabIndex = 0;
      col.setAttribute("role", "listitem");
      col.setAttribute("aria-label", c.label + ": " + fmt.format(n) + " Objekte");
      col.style.setProperty("--v", n / top);
      var bar = el("span", "col__bar"); bar.setAttribute("aria-hidden", "true");
      col.appendChild(bar);
      var x = el("span", "col__x", c.short); x.setAttribute("aria-hidden", "true"); col.appendChild(x);
      if (i === maxIdx || i === values.length - 1) { var v = el("span", "col__v" + (i === maxIdx ? "" : " col__v--end"), led(n)); v.setAttribute("aria-hidden", "true"); col.appendChild(v); }
      box.appendChild(col);
      bindTip(chart, bar, fmt.format(n), c.label);
    });
    var tb = $("[data-time-table] tbody");
    if (tb) { tb.innerHTML = ""; values.forEach(function (n, i) { var tr = el("tr"); tr.appendChild(el("td", "", CENTURIES[i].label)); tr.appendChild(el("td", "", fmt.format(n))); tb.appendChild(tr); }); }
    var dated = $("[data-dated]"); if (dated) dated.textContent = fmt.format(values.reduce(function (a, b) { return a + b; }, 0));
    if (anim && !shown.time) G.set($$(".col__bar, .col__v", box), { scaleY: 0, transformOrigin: "50% 100%" });
  }

  function renderColors(counts) {
    var chart = $("[data-chart='colors']"); if (!chart) return;
    var list = Object.keys(counts).filter(function (k) { return COLOR_INFO[k]; }).map(function (k) { return { k: k, n: counts[k] }; }).sort(function (a, b) { return b.n - a.n; });
    var total = list.reduce(function (a, c) { return a + c.n; }, 0); if (!total) return;
    var colorful = list.filter(function (c) { return !NEUTRAL[c.k]; }), cTotal = colorful.reduce(function (a, c) { return a + c.n; }, 0);
    function fill(strip, items, sum) {
      strip.innerHTML = "";
      items.forEach(function (c) {
        var s = el("span"), info = COLOR_INFO[c.k];
        s.style.setProperty("--w", c.n / sum);
        s.style.setProperty("--c", info[1]);
        s.dataset.k = c.k;
        s.tabIndex = 0;
        s.setAttribute("role", "listitem");
        s.setAttribute("aria-label", info[0] + ": " + fmt.format(c.n) + " Objekte, " + pct(c.n / total));
        strip.appendChild(s);
        bindTip(chart, s, fmt.format(c.n), info[0] + " · " + pct(c.n / total));
      });
    }
    var all = $("[data-strip='all']", chart), zoom = $("[data-strip='colorful']", chart);
    all.setAttribute("role", "list"); all.setAttribute("aria-label", "Bildfarben im Verhältnis");
    zoom.setAttribute("role", "list"); zoom.setAttribute("aria-label", "Bunte Bildfarben, vergrößert");
    fill(all, list, total);
    fill(zoom, colorful, cTotal);
    var share = cTotal / total;
    var a = $("[data-colorful]", chart); if (a) a.textContent = pct(share);
    var b = $("[data-colorful-short]", chart); if (b) b.textContent = Math.round(share * 100) + " %";
    var sw = $("[data-swatches]", chart);
    if (sw) {
      sw.innerHTML = "";
      list.forEach(function (c) {
        var li = el("li"), i = el("i"); i.style.setProperty("--c", COLOR_INFO[c.k][1]); i.setAttribute("aria-hidden", "true");
        li.appendChild(i); li.appendChild(el("span", "", COLOR_INFO[c.k][0])); li.appendChild(el("span", "", fmt.format(c.n)));
        sw.appendChild(li);
      });
    }
    funnel();
    if (anim && !shown.colors) G.set($$("span", all).concat($$("span", zoom)), { scaleX: 0 });
  }

  // Trichter von den bunten Segmenten zur vergrößerten Leiste
  function funnel() {
    var chart = $("[data-chart='colors']"); if (!chart) return;
    var all = $("[data-strip='all']", chart), zoom = $("[data-strip='colorful']", chart);
    var svg = $(".strip__funnel", chart);
    if (!svg) {
      svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "strip__funnel"); svg.setAttribute("aria-hidden", "true"); svg.setAttribute("preserveAspectRatio", "none");
      svg.appendChild(document.createElementNS("http://www.w3.org/2000/svg", "path"));
      all.insertAdjacentElement("afterend", svg);
    }
    var segs = $$("span", all), first = null;
    segs.forEach(function (s) { if (!first && !NEUTRAL[s.dataset.k]) first = s; });
    var W = all.clientWidth || 1, x0 = first ? first.offsetLeft : W - 4;
    svg.setAttribute("viewBox", "0 0 " + W + " 44");
    $("path", svg).setAttribute("d", "M" + x0 + " 0H" + W + "L" + W + " 44H0Z");
  }

  function renderProviders(counts) {
    var list = $("[data-providers]"); if (!list || !counts.length) return;
    var max = counts[0].count;
    list.innerHTML = "";
    counts.slice(0, 4).forEach(function (f) {
      var li = el("li"); li.style.setProperty("--v", (f.count / max).toFixed(4));
      li.appendChild(el("span", "providers__name", f.value));
      var bar = el("span", "providers__bar"); bar.appendChild(el("i")); li.appendChild(bar);
      li.appendChild(el("span", "providers__n", led(f.count)));
      list.appendChild(li);
    });
    if (anim && !shown.providers) G.set($$(".providers__bar i", list), { scaleX: 0 });
  }

  // Ticker: nur Facettenzahlen aus der Such-API
  function renderTicker(f, val) {
    var run = $("[data-ticker]"); if (!run) return;
    var items = [], T = { IMAGE: "Bilder", TEXT: "Texte", "3D": "3D-Objekte", VIDEO: "Videos", SOUND: "Audio" };
    var O = { portrait: "Hochformat", landscape: "Querformat", square: "Quadratisch" };
    (f.edmType || []).forEach(function (x) { items.push([T[x.value] || x.value, x.count]); });
    var iiif = val("hasIiifManifest", "true"); if (iiif) items.push(["Mit IIIF-Manifest", iiif]);
    (f.imageOrientation || []).forEach(function (x) { items.push([O[x.value] || x.value, x.count]); });
    (f.edmRightsName || []).slice(0, 8).forEach(function (x) { items.push([x.value, x.count]); });
    (f.dcType || []).slice(0, 8).forEach(function (x) { items.push([x.value, x.count]); });
    (f.imageColor || []).forEach(function (x) { if (COLOR_INFO[x.value]) items.push([COLOR_INFO[x.value][0], x.count]); });
    if (!items.length) return;
    var html = items.map(function (i) { return "<span><b>" + esc(i[0]) + "</b> <em>" + led(i[1]) + "</em></span>"; }).join("");
    run.innerHTML = html + html;
  }

  function setKpi(key, n) { var e = $("[data-kpi='" + key + "']"); if (e && n != null) e.textContent = led(n); }

  function liveData() {
    if (!window.Pool) return;
    Pool.stats().then(function (j) {
      if (!j || !j.found) return;
      var c = $("[data-count]"); if (c) { c.dataset.count = j.found; if (!shown.count || !anim) c.textContent = led(j.found); }
      var f = {};
      (j.facet_counts || []).forEach(function (fc) { f[fc.field_name] = fc.counts || []; });
      var val = function (field, v) { var hit = (f[field] || []).filter(function (x) { return x.value === v; })[0]; return hit ? hit.count : null; };
      if (f.dataProvider) { setKpi("providers", f.dataProvider.length); renderProviders(f.dataProvider); }
      setKpi("open", val("edmRightsReusePolicy", "OPEN"));
      setKpi("iiif", val("hasIiifManifest", "true"));
      setKpi("3d", val("edmType", "3D"));
      if (f.imageColor) { var cc = {}; f.imageColor.forEach(function (x) { cc[x.value] = x.count; }); renderColors(cc); }
      renderTicker(f, val);
      var src = $("[data-pool-src]"); if (src) src.textContent = "live, gerade eben";
    }).catch(function () {});

    var started = false;
    var go = function () {
      if (started) return; started = true;
      Pool.centuries(CENTURIES).then(function (rows) {
        var vals = rows.map(function (r) { return r.n; });
        if (vals.some(function (v) { return v > 0; })) renderTime(vals);
      }).catch(function () {});
    };
    var target = $("#pool");
    if (target && "IntersectionObserver" in window) new IntersectionObserver(function (en, ob) { if (en[0].isIntersecting) { ob.disconnect(); go(); } }, { rootMargin: "600px 0px" }).observe(target);
    else go();

    var words = ["Wien", "Porträt", "Gletscher", "Plakat", "Brief", "Karte", "Uhr", "Theater", "Mineral", "Kaiser", "Donau", "Fotografie", "Engel", "Stadt"];
    Pool.search(words[(Math.random() * words.length) | 0], { perPage: 40, page: 1 + ((Math.random() * 4) | 0) }).then(function (j) {
      var docs = (j.hits || []).map(Pool.doc).filter(function (d) { return d.title && d.title !== "Ohne Titel"; });
      if (!docs.length) return;
      if (window.City) City.setTitles(docs.map(function (d) { return d.title; }));
    }).catch(function () {});

    var api = $("[data-ping='api']"), sp = $("[data-ping='sparql']");
    function status(e, p) {
      if (!e) return;
      p.then(function (ms) { e.classList.add("is-up"); $("span", e).textContent = "online · " + ms + " ms"; })
       .catch(function () { e.classList.add("is-down"); $("span", e).textContent = "nicht erreichbar"; });
    }
    var pinged = false, res = $(".res");
    var ping = function () { if (pinged) return; pinged = true; status(api, Pool.ping()); status(sp, Pool.sparqlPing()); };
    if (res && "IntersectionObserver" in window) new IntersectionObserver(function (en, ob) { if (en[0].isIntersecting) { ob.disconnect(); ping(); } }, { rootMargin: "200px" }).observe(res);
    else ping();
  }

  /* ------------------------------------------------------------------
     Konsole: Suche und Ähnlichkeit live
     ------------------------------------------------------------------ */
  function consoleUI() {
    var form = $("[data-search]"); if (!form || !window.Pool) return;
    var input = $("#q", form), grid = $("[data-results]"), foundEl = $("[data-found]"), msEl = $("[data-ms]"), modeEl = $("[data-mode]"), reset = $("[data-reset]");
    var lastQ = "", req = 0;
    function ghosts(n) { grid.innerHTML = ""; for (var i = 0; i < n; i++) { var li = el("li"); li.appendChild(el("div", "obj--ghost")); grid.appendChild(li); } }
    function msg(html) { grid.innerHTML = '<li class="console__msg">' + html + "</li>"; }
    function setFound(n) {
      if (!foundEl) return;
      if (!anim) { foundEl.textContent = led(n); return; }
      var o = { v: 0 }; G.to(o, { v: n, duration: 0.9, ease: "power2.out", onUpdate: function () { foundEl.textContent = led(Math.round(o.v)); } });
    }
    function card(d) {
      var li = el("li");
      var label = d.title + (d.provider ? ", " + d.provider : "");
      var b = el("button", "obj"); b.type = "button"; b.setAttribute("aria-label", "Ähnliche Objekte zu: " + label);
      var im = el("span", "obj__img");
      if (d.img) { var img = el("img"); img.src = d.img; img.alt = ""; img.loading = "lazy"; img.decoding = "async"; img.addEventListener("error", function () { img.remove(); }); im.appendChild(img); }
      b.appendChild(im);
      b.appendChild(el("span", "obj__t", d.title));
      b.appendChild(el("span", "obj__p", d.provider + (d.date ? " · " + d.date : "")));
      b.addEventListener("click", function () { similar(d); });
      li.appendChild(b);
      if (d.dist !== null) { var dd = el("span", "obj__d", d.dist.toFixed(3).replace(".", ",")); dd.title = "Vektordistanz"; li.appendChild(dd); }
      var a = el("a", "obj__open"); a.href = d.url; a.target = "_blank"; a.rel = "noopener"; a.appendChild(el("span", "sr-only", "Im Kulturpool öffnen (neuer Tab)")); li.appendChild(a);
      return li;
    }
    function render(docs) {
      grid.innerHTML = "";
      if (!docs.length) { msg("Nichts gefunden. Anderer Begriff?"); return; }
      docs.forEach(function (d) { grid.appendChild(card(d)); });
      if (anim) G.from(grid.children, { y: 26, opacity: 0, scale: 0.94, duration: 0.6, stagger: 0.04 });
    }
    function search(q) {
      var my = ++req; lastQ = q;
      if (modeEl) { modeEl.textContent = "Suche"; modeEl.classList.remove("is-similar"); }
      if (reset) reset.hidden = true;
      ghosts(8);
      Pool.search(q, { perPage: 12, images: true }).then(function (j) {
        if (my !== req) return;
        setFound(j.found || 0); if (msEl) msEl.textContent = j.__ms;
        render((j.hits || []).map(Pool.doc));
      }).catch(function () { if (my === req) msg("Der Pool antwortet gerade nicht. Später nochmal versuchen, oder direkt in die <a href=\"https://api.kulturpool.at/reference/\">API-Referenz</a> schauen."); });
    }
    function similar(d) {
      var my = ++req;
      if (modeEl) { modeEl.textContent = "Ähnlich zu: " + (d.title.length > 38 ? d.title.slice(0, 36) + "…" : d.title); modeEl.classList.add("is-similar"); }
      if (reset) reset.hidden = false;
      ghosts(8);
      var top = $(".panel--search"); if (top && top.getBoundingClientRect().top < 0) top.scrollIntoView({ behavior: motion ? "smooth" : "auto" });
      Pool.similar(d.id, 13).then(function (j) {
        if (my !== req) return;
        setFound(j.found || 0); if (msEl) msEl.textContent = j.__ms;
        render((j.hits || []).map(Pool.doc).filter(function (x) { return x.id !== d.id; }).slice(0, 12));
      }).catch(function () { if (my === req) msg("Ähnlichkeitssuche gerade nicht erreichbar."); });
    }
    form.addEventListener("submit", function (e) { e.preventDefault(); search(input.value.trim() || input.placeholder); });
    if (reset) reset.addEventListener("click", function () { search(lastQ || input.placeholder); });

    var started = false;
    function demo() {
      if (started) return; started = true;
      var words = ["Gletscher", "Plakat", "Kaiserin", "Donau", "Taschenuhr", "Porträt", "Stadtplan"];
      var w = words[(Math.random() * words.length) | 0];
      if (!anim) { input.value = w; search(w); return; }
      var tl = G.timeline();
      for (var i = 1; i <= w.length; i++) tl.call((function (s) { return function () { input.value = s; }; })(w.slice(0, i)), null, i * 0.07);
      tl.call(function () { search(w); }, null, w.length * 0.07 + 0.25);
    }
    var panel = $(".panel--search");
    if (panel && "IntersectionObserver" in window) new IntersectionObserver(function (en, ob) { if (en[0].isIntersecting) { ob.disconnect(); demo(); } }, { threshold: 0.25 }).observe(panel);
    else demo();
  }

  /* ------------------------------------------------------------------
     Kopieren, SPARQL-Hervorhebung
     ------------------------------------------------------------------ */
  function copyText(text, btn) {
    var done = function () { var old = btn.textContent; btn.classList.add("is-done"); btn.textContent = "kopiert"; setTimeout(function () { btn.classList.remove("is-done"); btn.textContent = old; }, 1600); };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, function () {});
    else { var ta = el("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select(); try { document.execCommand("copy"); done(); } catch (e) {} ta.remove(); }
  }
  $$("[data-copy]").forEach(function (b) { b.addEventListener("click", function () { copyText(b.dataset.copy, b); }); });
  var codeEl = $("[data-sparql] code"), rawQuery = codeEl ? codeEl.textContent : "";
  $$("[data-copy-code]").forEach(function (b) { b.addEventListener("click", function () { copyText(rawQuery, b); }); });
  if (codeEl) {
    var KW = /^(PREFIX|SELECT|WHERE|GROUP|BY|ORDER|DESC|ASC|LIMIT|OFFSET|COUNT|AS|FILTER|SERVICE|OPTIONAL|GRAPH|DISTINCT|UNION|a)$/;
    codeEl.innerHTML = rawQuery.split("\n").map(function (line) {
      if (/^\s*#/.test(line)) return '<span class="c">' + esc(line) + "</span>";
      var out = "", re = /(<[^>\s]*>)|(\?[A-Za-z_]\w*)|([A-Za-z][\w-]*:[A-Za-z_][\w-]*|[A-Za-z][\w-]*:(?=\s))|(\b[A-Za-z]+\b)|(\d+)|([^<?\w]+|[<?])/g, m;
      while ((m = re.exec(line))) {
        if (m[1]) out += '<span class="i">' + esc(m[1]) + "</span>";
        else if (m[2]) out += '<span class="v">' + esc(m[2]) + "</span>";
        else if (m[3]) out += '<span class="p">' + esc(m[3]) + "</span>";
        else if (m[4]) out += KW.test(m[4]) ? '<span class="k">' + esc(m[4]) + "</span>" : esc(m[4]);
        else if (m[5]) out += '<span class="n">' + esc(m[5]) + "</span>";
        else out += esc(m[6]);
      }
      return out;
    }).join("\n");
  }

  /* ------------------------------------------------------------------
     Karte: Innere Stadt als Platine
     ------------------------------------------------------------------ */
  function buildMap() {
    var M = window.HTP_MAP, fig = $("[data-map]");
    if (!M || !fig) return;
    var V = M.venue, s = [];
    s.push('<svg viewBox="0 0 ' + M.w + " " + M.h + '" role="img" aria-label="Karte der Inneren Stadt: Die ÖAW in der Bäckerstraße 13 liegt zwischen Stephansplatz, Stubentor und Schwedenplatz.">');
    s.push('<defs><pattern id="mapdots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#2a2450"/></pattern>');
    s.push('<radialGradient id="mapfade" cx="' + (V[0] / M.w) + '" cy="' + (V[1] / M.h) + '" r=".62"><stop offset=".55" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>');
    s.push('<mask id="mapmask"><rect width="100%" height="100%" fill="url(#mapfade)"/></mask></defs>');
    s.push('<g mask="url(#mapmask)"><rect width="100%" height="100%" fill="url(#mapdots)"/>');
    var glow = [], roads = [], pads = [];
    M.roads.forEach(function (r, i) {
      var cls = "map__road map__road--" + r[1];
      roads.push('<path class="' + cls + '" d="' + r[2] + '"/>');
      if (r[1] === "M") glow.push('<path class="' + cls + '" d="' + r[2] + '"/>');
      if (i % 9 === 0) { var m = /^M(-?\d+) (-?\d+)/.exec(r[2]); if (m) pads.push('<circle cx="' + m[1] + '" cy="' + m[2] + '" r="3"/>'); }
    });
    s.push('<g class="map__glow">' + glow.join("") + '</g><g class="map__roads">' + roads.join("") + '</g><g class="map__pads">' + pads.join("") + "</g>");
    if (M.dome) {
      s.push('<path class="map__dome" d="' + M.dome + '"/>');
      var nums = M.dome.match(/-?\d+/g).map(Number), cx = 0, cy = 0, n = nums.length / 2;
      for (var k = 0; k < nums.length; k += 2) { cx += nums[k]; cy += nums[k + 1]; }
      s.push('<text class="map__label map__label--dim" x="' + (cx / n).toFixed(0) + '" y="' + (cy / n + 62).toFixed(0) + '" text-anchor="middle">Stephansdom</text>');
    }
    s.push("</g>");
    var INFO = {
      "Stephansplatz": { dx: -16, dy: -26, a: "end", lines: [["U1", "#e3000f"], ["U3", "#ee7d00"]] },
      "Stubentor": { dx: 18, dy: 34, a: "start", lines: [["U3", "#ee7d00"], ["2", "#fff"]] },
      "Schwedenplatz": { dx: 20, dy: -18, a: "start", lines: [["U1", "#e3000f"], ["U4", "#009540"]] }
    };
    Object.keys(M.stations).forEach(function (name) {
      var p = M.stations[name], info = INFO[name]; if (!info) return;
      var lx = p[0] + info.dx, ly = p[1] + info.dy;
      var badges = info.lines.map(function (l, j) {
        var bx = info.a === "end" ? lx - (info.lines.length - j) * 30 : lx + j * 30, tram = l[0] === "2";
        return '<g class="map__badge"><rect x="' + bx + '" y="' + (ly + 8) + '" width="26" height="17" rx="' + (tram ? 8.5 : 2) + '" fill="' + l[1] + '"/><text x="' + (bx + 13) + '" y="' + (ly + 20.5) + '" text-anchor="middle"' + (tram ? ' style="fill:#e3000f"' : "") + ">" + l[0] + "</text></g>";
      }).join("");
      s.push('<g class="map__st"><circle cx="' + p[0] + '" cy="' + p[1] + '" r="11"/><circle class="map__stdot" cx="' + p[0] + '" cy="' + p[1] + '" r="4"/><text class="map__label" x="' + lx + '" y="' + ly + '" text-anchor="' + info.a + '">' + name + "</text>" + badges + "</g>");
    });
    var vw = 92, vh = 52, vx = V[0] - vw / 2, vy = V[1] - vh / 2, pins = "";
    for (var px = vx + 10; px < vx + vw - 6; px += 12) pins += '<path class="map__pinline" d="M' + px + " " + vy + "v-9M" + px + " " + (vy + vh) + 'v9"/>';
    for (var py = vy + 10; py < vy + vh - 6; py += 12) pins += '<path class="map__pinline" d="M' + vx + " " + py + "h-9M" + (vx + vw) + " " + py + 'h9"/>';
    s.push('<g class="map__venue"><circle class="map__ping" cx="' + V[0] + '" cy="' + V[1] + '" r="30"/><circle class="map__ping" cx="' + V[0] + '" cy="' + V[1] + '" r="30"/>' + pins +
      '<rect x="' + vx + '" y="' + vy + '" width="' + vw + '" height="' + vh + '" rx="3"/><text x="' + V[0] + '" y="' + (V[1] + 7) + '" text-anchor="middle">ÖAW</text>' +
      '<text class="map__label" x="' + (vx + vw + 18) + '" y="' + (V[1] - 2) + '">Bäckerstraße 13</text></g></svg>');
    fig.insertAdjacentHTML("afterbegin", s.join(""));
    if (!anim) return;
    var svg = $("svg", fig), paths = $$(".map__roads path", svg), venue = $(".map__venue", svg), stations = $$(".map__st", svg);
    var late = $$(".map__glow, .map__pads, .map__dome, .map__label--dim", svg);
    G.set(paths, { drawSVG: "0%" });
    G.set(late.concat(stations), { opacity: 0 });
    G.set(venue, { scale: 0, transformOrigin: "50% 50%" });
    ST.create({ trigger: fig, start: "top 78%", once: true, onEnter: function () {
      G.timeline()
        .to(venue, { scale: 1, duration: 0.7, ease: "back.out(2)" }, 0)
        .to(paths, { drawSVG: "100%", duration: 0.9, ease: "power2.out", stagger: { each: 2.4 / paths.length } }, 0.25)
        .to(late, { opacity: 1, duration: 1.2 }, 1.6)
        .to(stations, { opacity: 1, duration: 0.5, stagger: 0.18 }, 1.2);
      $$(".map__ping", svg).forEach(function (c, i) {
        G.fromTo(c, { attr: { r: 30 }, opacity: 0.9 }, { attr: { r: 150 }, opacity: 0, duration: 2.6, repeat: -1, delay: 1 + i * 1.3, ease: "power2.out" });
      });
    } });
  }

  /* ------------------------------------------------------------------
     Disketten
     ------------------------------------------------------------------ */
  function disks() {
    if (!anim) return;
    $$(".disk").forEach(function (d) {
      G.set(d, { transformPerspective: 900 });
      var rx = G.quickTo(d, "rotationX", { duration: 0.6, ease: "power3" }), ry = G.quickTo(d, "rotationY", { duration: 0.6, ease: "power3" });
      d.addEventListener("pointermove", function (e) {
        if (e.pointerType === "touch") return;
        var b = d.getBoundingClientRect();
        ry(((e.clientX - b.left) / b.width - 0.5) * 24);
        rx(-((e.clientY - b.top) / b.height - 0.5) * 24);
      });
      d.addEventListener("pointerleave", function () { rx(0); ry(0); });
    });
  }

  /* ------------------------------------------------------------------
     Scroll-Szenen
     ------------------------------------------------------------------ */
  var cityCanvas = $("#city"), CITY_DIM = 0.16;
  function cityOpacity(v) { if (cityCanvas) cityCanvas.style.opacity = v.toFixed(3); }

  function scenes() {
    var mm = G.matchMedia();

    // Hero: Wortmarke zerstreut sich, Stadt dimmt, Kamera beschleunigt beim Scrollen
    ST.create({
      trigger: ".hero", start: "top top", end: "bottom top", scrub: true,
      onUpdate: function (self) {
        if (wordmark) wordmark.state.scatter = Math.pow(self.progress, 1.4) * 1.1;
        cityOpacity(1 - self.progress * (1 - CITY_DIM));
      },
      onToggle: function (self) { if (wordmark) wordmark.setActive(self.isActive || window.scrollY < 10); }
    });
    G.to(".hero__inner", { yPercent: -14, ease: "none", scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: true } });
    G.fromTo(".hero__row, .hero__tagline, .hero__credits", { opacity: 1 }, { opacity: 0, ease: "none", immediateRender: false, scrollTrigger: { trigger: ".hero", start: "20% top", end: "70% top", scrub: true } });
    ST.create({ start: 0, end: "max", onUpdate: function (self) { if (window.City) City.boost(self.getVelocity()); } });

    // Finale: Stadt aus, Pool an
    ST.create({
      trigger: ".finale", start: "top 70%", end: "bottom top",
      onToggle: function (self) {
        G.to(cityCanvas, { opacity: self.isActive ? 0 : CITY_DIM, duration: 0.8, overwrite: true });
        if (window.City) City.setActive(!self.isActive);
      }
    });

    // Titel: Breitenachse dehnt sich auf Satzbreite, Text wird entschlüsselt
    $$("[data-stretch]").forEach(function (h) {
      G.fromTo(h, { "--wdth": 50 }, {
        "--wdth": function () { return +h.dataset.fitted || 135; }, ease: "none", immediateRender: false,
        scrollTrigger: { trigger: h, start: "top 96%", end: "top 40%", scrub: 0.6, invalidateOnRefresh: true }
      });
      var s = $("[data-scramble]", h);
      if (s) ST.create({ trigger: h, start: "top 88%", once: true, onEnter: function () {
        G.to(s, { duration: 1.1, scrambleText: { text: s.textContent, chars: "ABCDEFGHIJKLMNOPQRSTUVWXYZ#%&0123456789", revealDelay: 0.15, speed: 0.5 } });
      } });
    });

    // Statement: Zeilen tauchen aus der Maske auf
    $$("[data-split]").forEach(function (e) {
      SplitText.create(e, {
        type: "lines", mask: "lines", autoSplit: true, linesClass: "line",
        onSplit: function (self) {
          e.style.visibility = "visible";
          return G.from(self.lines, { yPercent: 115, duration: 1.15, ease: "power4.out", stagger: 0.1, scrollTrigger: { trigger: e, start: "top 82%", once: true } });
        }
      });
    });

    // Einblendungen
    var rev = $$(".prose p, .kicker, .lede, .kit__list li, .res__row, .archive__list li, .programm__notes p, .ort__addr > *, .crowd__note, .query__side > *, .contrib, .chart__head, .tile, .poolcount__label, .swatches, .strip__label");
    G.set(rev, { autoAlpha: 0, y: 30 });
    ST.batch(rev, { start: "top 90%", once: true, onEnter: function (b) { G.to(b, { autoAlpha: 1, y: 0, duration: 0.9, stagger: 0.07, overwrite: true }); } });
    var crowd = $$(".crowd__list span");
    G.set(crowd, { autoAlpha: 0, y: 24 });
    ST.batch(crowd, { start: "top 92%", once: true, onEnter: function (b) { G.to(b, { autoAlpha: 1, y: 0, duration: 0.8, stagger: 0.09 }); } });
    $$(".panel").forEach(function (p) { G.from(p, { y: 60, opacity: 0, duration: 1.1, scrollTrigger: { trigger: p, start: "top 85%", once: true } }); });

    // Zahlen
    var cnt = $("[data-count]");
    if (cnt) ST.create({ trigger: cnt, start: "top 85%", once: true, onEnter: function () {
      shown.count = true;
      var o = { p: 0 };
      G.to(o, { p: 1, duration: 2.4, ease: "power3.out", onUpdate: function () { cnt.textContent = led(Math.round(o.p * (+cnt.dataset.count || 0))); } });
    } });
    $$(".tile dd").forEach(function (dd, i) {
      ST.create({ trigger: dd, start: "top 90%", once: true, onEnter: function () {
        G.to(dd, { duration: 1.2, delay: i * 0.08, scrambleText: { text: dd.textContent, chars: "0123456789", speed: 0.7 } });
      } });
    });
    $$(".spec").forEach(function (sp, i) {
      var dt = $("dt", sp);
      ST.create({ trigger: sp, start: "top 88%", once: true, onEnter: function () {
        G.from(sp, { y: 40, opacity: 0, duration: 0.9, delay: i * 0.08 });
        G.to(dt, { duration: 1.2, delay: i * 0.08, scrambleText: { text: dt.textContent, chars: "0123456789", speed: 0.7 } });
      } });
    });

    // Charts wachsen aus ihrer Grundlinie
    ST.create({ trigger: "[data-chart='time']", start: "top 75%", once: true, onEnter: function () {
      shown.time = true;
      G.to("[data-cols] .col__bar, [data-cols] .col__v", { scaleY: 1, duration: 1.1, stagger: 0.05, ease: "power4.out" });
    } });
    ST.create({ trigger: "[data-chart='colors']", start: "top 75%", once: true, onEnter: function () {
      shown.colors = true;
      G.to("[data-strip] > span", { scaleX: 1, duration: 0.9, stagger: 0.03, ease: "power4.out" });
    } });
    ST.create({ trigger: "[data-providers]", start: "top 85%", once: true, onEnter: function () {
      shown.providers = true;
      G.to("[data-providers] .providers__bar i", { scaleX: 1, duration: 1.3, stagger: 0.1, ease: "power4.out" });
    } });

    // Band: Endlosschleife, Tempo folgt dem Scrollen
    var track = $("[data-band]"), loop = null;
    if (track) {
      var original = track.innerHTML;
      var copies = Math.max(1, Math.ceil((window.innerWidth * 1.3) / Math.max(1, track.scrollWidth)));
      var html = ""; for (var i = 0; i < copies; i++) html += original;
      track.innerHTML = html + html;
      loop = G.fromTo(track, { xPercent: -50 }, { xPercent: 0, duration: 34, ease: "none", repeat: -1 });
      var proxy = { ts: 1 };
      ST.create({
        trigger: ".bandwrap", start: "top bottom", end: "bottom top",
        onToggle: function (self) { if (self.isActive) loop.play(); else loop.pause(); },
        onUpdate: function (self) {
          var v = self.getVelocity();
          G.killTweensOf(proxy);
          proxy.ts = 1 + Math.min(Math.abs(v) / 240, 7);
          loop.timeScale(proxy.ts);
          G.to(proxy, { ts: 1, duration: 1.4, ease: "power2.out", onUpdate: function () { loop.timeScale(proxy.ts); } });
        }
      });
    }

    // Quests: horizontaler Flug durch fünf Pins
    mm.add("(min-width: 961px)", function () {
      root.classList.add("hscroll");
      $$(".quest__name[data-fit]").forEach(function (h) { fitWidth(h, +h.dataset.fit || 130); });
      var trk = $(".quests__track"), pinEl = $(".quests__pin"), panels = $$(".quest", trk), dots = $$(".quests__dots li");
      var dist = function () { return trk.scrollWidth - window.innerWidth; };
      var tween = G.to(trk, {
        x: function () { return -dist(); }, ease: "none",
        scrollTrigger: {
          trigger: pinEl, start: "top top", end: function () { return "+=" + dist(); }, pin: true, scrub: 0.7,
          invalidateOnRefresh: true, anticipatePin: 1, refreshPriority: 10,
          onUpdate: function (self) { var idx = Math.round(self.progress * (panels.length - 1)); dots.forEach(function (d, i) { d.classList.toggle("is-on", i === idx); }); }
        }
      });
      questTween = tween;
      panels.forEach(function (p, i) {
        var pin = $(".pin", p), body = $(".quest__body", p);
        if (i > 0) {
          G.fromTo(pin, { rotation: -140, scale: 0.55, opacity: 0 }, { rotation: 0, scale: 1, opacity: 1, ease: "none", scrollTrigger: { trigger: p, containerAnimation: tween, start: "left 100%", end: "left 30%", scrub: true } });
          G.from(body.children, { x: 160, opacity: 0, stagger: 0.05, ease: "none", scrollTrigger: { trigger: p, containerAnimation: tween, start: "left 80%", end: "left 20%", scrub: true } });
        }
        G.to(pin, { rotation: 35, scale: 0.85, ease: "none", scrollTrigger: { trigger: p, containerAnimation: tween, start: "right 60%", end: "right 0%", scrub: true } });
        p.onfocusin = function () {
          var st = tween.scrollTrigger; if (!st || !root.classList.contains("hscroll")) return;
          var y = st.start + (st.end - st.start) * (i / Math.max(1, panels.length - 1));
          if (Math.abs(window.scrollY - y) > 4) window.scrollTo(0, y);
        };
      });
      return function () { questTween = null; root.classList.remove("hscroll"); $$(".quest__name[data-fit]").forEach(function (h) { fitWidth(h, +h.dataset.fit || 130); }); };
    });
    mm.add("(max-width: 960px)", function () {
      $$(".quest").forEach(function (p) {
        G.from($(".pin", p), { rotation: -120, scale: 0.6, opacity: 0, duration: 1.2, ease: "back.out(1.4)", scrollTrigger: { trigger: p, start: "top 80%", once: true } });
        G.from($(".quest__body", p).children, { y: 30, opacity: 0, stagger: 0.07, duration: 0.8, scrollTrigger: { trigger: p, start: "top 65%", once: true } });
      });
    });

    // Programm
    ST.create({ trigger: ".days", start: "top 78%", once: true, onEnter: function () {
      G.from(".day__bar i", { scaleX: 0, duration: 1, stagger: 0.06, ease: "power4.out" });
      G.from(".slots li", { x: -40, opacity: 0, duration: 0.7, stagger: 0.045 });
      $$(".day__name .led").forEach(function (x) { G.to(x, { duration: 1, scrambleText: { text: x.textContent, chars: "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", speed: 0.7 } }); });
    } });

    // Disketten fallen ins Bild
    G.from(".disk", { y: -180, rotation: function (i) { return [-16, 10, -7, 13][i % 4]; }, opacity: 0, duration: 1.3, ease: "bounce.out", stagger: 0.12, scrollTrigger: { trigger: ".disks", start: "top 82%", once: true } });

    // Finale-Titel
    if (window.SplitText) {
      var ft = SplitText.create("[data-finale-title]", { type: "words,chars", charsClass: "char" });
      G.from(ft.chars, { yPercent: 130, rotationX: -90, opacity: 0, transformOrigin: "50% 100%", duration: 1, stagger: 0.04, ease: "back.out(2.2)", scrollTrigger: { trigger: ".finale__title", start: "top 85%", once: true } });
    }

    // Navigation: aktuelle Sektion
    var navLinks = $$(".hud__nav a");
    $$("[data-sec]").forEach(function (sec) {
      ST.create({ trigger: sec, start: "top 50%", end: "bottom 50%", onToggle: function (self) {
        if (!self.isActive) return;
        navLinks.forEach(function (a) { if (a.hash === "#" + sec.id) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current"); });
      } });
    });

    ST.addEventListener("refreshInit", fitAll);
    window.addEventListener("resize", function () { clearTimeout(scenes.t); scenes.t = setTimeout(funnel, 200); });
  }

  function staticScenes() {
    $$("[data-split]").forEach(function (e) { e.style.visibility = "visible"; });
    var hero = $(".hero");
    var onScroll = function () {
      var h = hero ? hero.offsetHeight : window.innerHeight;
      cityOpacity(Math.max(CITY_DIM, 1 - (window.scrollY / h) * (1 - CITY_DIM)));
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    window.addEventListener("resize", function () { clearTimeout(staticScenes.t); staticScenes.t = setTimeout(function () { fitAll(); funnel(); }, 150); });
    var fin = $(".finale");
    if (fin && "IntersectionObserver" in window) new IntersectionObserver(function (en) {
      if (window.City) City.setActive(!en[0].isIntersecting);
    }, { threshold: 0.3 }).observe(fin);
  }

  /* ------------------------------------------------------------------
     Start
     ------------------------------------------------------------------ */
  function fontsReady() {
    var p = document.fonts && document.fonts.load ? Promise.all([
      document.fonts.load("900 100px Anybody"), document.fonts.load("italic 900 100px Anybody"), document.fonts.load("900 40px Doto")
    ]) : Promise.resolve();
    return Promise.race([p, new Promise(function (r) { setTimeout(r, 2200); })]).catch(function () {});
  }

  renderTime(SNAP_TIME);
  renderColors(SNAP_COLORS);
  liveData();
  consoleUI();
  buildMap();

  fontsReady().then(function () {
    initWordmark();
    fitAll();
    if (anim) scenes(); else staticScenes();
    windows();
    initToc();
    disks();
    heroIntro();
    if (ST) { ST.refresh(); setTimeout(function () { ST.refresh(); funnel(); }, 700); }
    if (window.City && !motion) City.setTurbo(false);
    if (window.Caustics && !motion) Caustics.setTurbo(false);
  });
})();
