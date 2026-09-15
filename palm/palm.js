/* ---------------------------------------------------------------
   The shell: storage, screen routing, the Graffiti pad, the
   on-screen keyboard, Find, menus and the hardware keys.
   --------------------------------------------------------------- */

(function () {
  'use strict';

  var APPS = window.PALM_APPS;
  var UI = window.PALM_UI;
  var esc = UI.esc;
  var STORE = 'graphite-pda-v1';

  var vscreen = document.getElementById('vscreen');
  var glass = document.getElementById('glass');
  var pad = document.getElementById('pad');
  var ink = document.getElementById('ink');
  var padshift = document.getElementById('padshift');
  var screenoff = document.getElementById('screenoff');
  var led = document.getElementById('led');
  var stageEl = document.getElementById('stage');
  var fitEl = document.getElementById('fit');
  var deviceEl = document.getElementById('device');

  var cur = 'launcher';
  var modal = null;
  var menu = null;
  var shift = 0;                 /* 0 none · 1 next char · 2 caps lock */
  var kbTab = 'abc';
  var kbShift = false;
  var findQ = '';
  var powered = true;
  var lastField = null;

  /* ================= storage ================= */

  function seed() {
    var today = UI.dateKey(new Date());
    var events = {};
    events[today] = { 9: 'Stand-up', 11: 'Call with Nakamura-san', 15: 'Design review' };
    return {
      events: events,
      contacts: [
        { id: 'c1', last: 'Aoki', first: 'Rin', company: 'Kite Supply Co.', phone: '03-5555-0142', email: 'rin@kitesupply.example', note: 'Sample record.' },
        { id: 'c2', last: 'Delgado', first: 'Mateo', company: 'Harbour Press', phone: '555-0188', email: 'mateo@harbour.example', note: '' },
        { id: 'c3', last: 'Okonkwo', first: 'Ada', company: '', phone: '555-0117', email: '', note: 'Prefers e-mail.' }
      ],
      todos: [
        { id: 't1', text: 'Practice the Graffiti alphabet', pri: 1, done: false },
        { id: 't2', text: 'Replace the AAA batteries', pri: 3, done: false },
        { id: 't3', text: 'Back up before the trip', pri: 2, done: true }
      ],
      memos: [
        { id: 'm1', text: 'Graffiti\n\nOne stroke per character.\nLetters left of the divider,\nnumbers right of it.\n\nStroke up = shift.\nTap = period.\n\nOpen the Graffiti app for\nthe full chart.' },
        { id: 'm2', text: 'Sample memo\n\nEverything on this device is\nstored in this browser only.\nPrefs > Reset erases it.' }
      ]
    };
  }

  function loadStore() {
    try {
      var raw = localStorage.getItem(STORE);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && parsed.db) return parsed;
      }
    } catch (e) { /* private mode, blocked storage — fall through to seed */ }
    return null;
  }

  var stored = loadStore();
  var PDA = window.PDA = {
    db: stored ? stored.db : seed(),
    prefs: Object.assign({ skin: 'classic', threshold: 0.70, ink: true, syskb: false },
      stored ? stored.prefs : null),
    focusAfter: null
  };
  ['events', 'contacts', 'todos', 'memos'].forEach(function (k) {
    if (!PDA.db[k]) PDA.db[k] = k === 'events' ? {} : [];
  });

  PDA.save = function () {
    try {
      localStorage.setItem(STORE, JSON.stringify({ db: PDA.db, prefs: PDA.prefs }));
    } catch (e) { /* nothing we can do; the session still works in memory */ }
  };

  PDA.reset = function () {
    try { localStorage.removeItem(STORE); } catch (e) {}
    PDA.db = seed();
    cur = 'launcher';
    PDA.save();
  };

  PDA.applyPrefs = function () {
    glass.setAttribute('data-skin', PDA.prefs.skin);
  };

  /* ================= routing & render ================= */

  PDA.open = function (name) {
    if (!APPS[name]) return;
    cur = name;
    modal = null; menu = null;
    PDA.render();
  };

  PDA.confirm = function (title, message, onYes) {
    modal = { type: 'confirm', title: title, message: message, onYes: onYes };
    PDA.render();
  };

  function confirmHtml() {
    return '<div class="scrim"></div><div class="dlg"><h2>' + esc(modal.title) + '</h2>' +
      '<div class="dbody"><p style="margin:0 0 5px;font-size:9px">' + esc(modal.message) + '</p>' +
      '<div style="display:flex;gap:3px">' +
      '<button type="button" class="btn" data-act="cf:ok">OK</button>' +
      '<button type="button" class="btn" data-act="cf:cancel">Cancel</button></div></div></div>';
  }

  /* --- on-screen keyboard --- */

  var KB = {
    abc: [
      'q w e r t y u i o p',
      'a s d f g h j k l',
      'z x c v b n m'
    ],
    '123': [
      '1 2 3 4 5 6 7 8 9 0',
      '- / : ; ( ) $ & @ "',
      '. , ? ! ’ % + ='
    ],
    intl: [
      'à á â ä è é ê ë ì í',
      'î ï ò ó ô ö ù ú û ü',
      'ñ ç ß ¥ £ € # * < >'
    ]
  };

  function keyboardHtml() {
    var rows = KB[kbTab].map(function (row) {
      return '<div class="kbrow">' + row.split(' ').map(function (k) {
        var label = (kbTab === 'abc' && kbShift) ? k.toUpperCase() : k;
        return '<button type="button" class="key" data-act="kb:key" data-k="' + esc(label) + '">' +
          esc(label) + '</button>';
      }).join('') + '</div>';
    }).join('');

    rows += '<div class="kbrow">' +
      '<button type="button" class="key" data-act="kb:shift"' + (kbShift ? ' aria-pressed="true"' : '') + '>&#8679;</button>' +
      '<button type="button" class="key wide" data-act="kb:key" data-k=" ">space</button>' +
      '<button type="button" class="key" data-act="kb:back">&#9003;</button>' +
      '<button type="button" class="key" data-act="kb:ret">&#8629;</button>' +
      '</div>';

    var tab = function (id, label) {
      return '<button type="button" class="btn" data-act="kb:tab" data-t="' + id + '"' +
        (kbTab === id ? ' aria-pressed="true"' : '') + '>' + label + '</button>';
    };

    return '<div class="scrim"></div><div class="dlg" data-nofocus><h2>Keyboard</h2>' +
      '<div class="dbody"><div class="kb">' + rows + '</div>' +
      '<div class="tabs" style="margin-top:3px">' + tab('abc', 'abc') + tab('123', '123') +
      tab('intl', 'int’l') + '<span class="grow" style="flex:1"></span>' +
      '<button type="button" class="btn" data-act="kb:done">Done</button></div></div></div>';
  }

  /* --- find --- */

  function findResults() {
    var q = findQ.trim().toLowerCase();
    if (!q) return [];
    var out = [];
    PDA.db.memos.forEach(function (m) {
      if ((m.text || '').toLowerCase().indexOf(q) > -1)
        out.push({ app: 'memo', id: m.id, kind: 'Memo', text: (m.text || '').split('\n')[0] });
    });
    PDA.db.contacts.forEach(function (c) {
      var hay = [c.last, c.first, c.company, c.phone, c.email, c.note].join(' ').toLowerCase();
      if (hay.indexOf(q) > -1)
        out.push({ app: 'address', id: c.id, kind: 'Addr', text: [c.last, c.first].filter(Boolean).join(', ') || c.company });
    });
    PDA.db.todos.forEach(function (t) {
      if ((t.text || '').toLowerCase().indexOf(q) > -1)
        out.push({ app: 'todo', id: t.id, kind: 'To Do', text: t.text });
    });
    Object.keys(PDA.db.events).forEach(function (day) {
      var slots = PDA.db.events[day];
      Object.keys(slots).forEach(function (h) {
        if (String(slots[h]).toLowerCase().indexOf(q) > -1)
          out.push({ app: 'datebook', id: day, hour: +h, kind: day.slice(5), text: slots[h] });
      });
    });
    return out.slice(0, 6);
  }

  function findHtml() {
    var res = findResults();
    var rows = res.map(function (r, i) {
      return '<div class="row" data-act="find:go" data-i="' + i + '">' +
        '<span class="tag" style="width:22px;flex:none">' + esc(r.kind) + '</span>' +
        '<span class="grow">' + esc(r.text) + '</span></div>';
    }).join('');
    if (!rows) rows = '<div class="empty" style="padding:8px">' +
      (findQ ? 'Nothing found.' : 'Type or write a word to search all records.') + '</div>';

    return '<div class="scrim"></div><div class="dlg"><h2>Find</h2><div class="dbody">' +
      '<div class="fldrow"><label>Find</label>' +
      '<input class="fld grow" id="find-q" type="text" data-act="find:q" value="' + esc(findQ) + '"></div>' +
      '<div style="height:66px;overflow:hidden">' + rows + '</div>' +
      '<div style="display:flex;justify-content:flex-end">' +
      '<button type="button" class="btn" data-act="find:done">Done</button></div></div></div>';
  }

  /* --- menu --- */

  function menuItems() {
    var app = APPS[cur];
    var items = (app.menu ? app.menu() : []).slice();
    if (items.length) items.push({ sep: true });
    items.push({ label: 'Applications', go: 'launcher' });
    items.push({ label: 'Graffiti help', go: 'graffiti' });
    items.push({ label: 'Preferences', go: 'prefs' });
    return items;
  }

  function menuHtml() {
    return '<div class="scrim" data-act="menu:close"></div><div class="menu">' +
      menu.map(function (it, i) {
        return it.sep ? '<hr>' :
          '<button type="button" data-act="menu:pick" data-i="' + i + '">' + esc(it.label) + '</button>';
      }).join('') + '</div>';
  }

  PDA.render = function () {
    var html = APPS[cur].render();
    if (modal && modal.type === 'confirm') html += confirmHtml();
    else if (modal && modal.type === 'keyboard') html += keyboardHtml();
    else if (modal && modal.type === 'find') html += findHtml();
    if (menu) html += menuHtml();
    vscreen.innerHTML = html;

    Array.prototype.forEach.call(vscreen.querySelectorAll('.fld'), function (el) {
      el.setAttribute('autocomplete', 'off');
      el.setAttribute('autocapitalize', 'off');
      el.setAttribute('autocorrect', 'off');
      el.setAttribute('spellcheck', 'false');
      if (!PDA.prefs.syskb) el.setAttribute('inputmode', 'none');
      else el.removeAttribute('inputmode');
    });

    var target = PDA.focusAfter && vscreen.querySelector(PDA.focusAfter);
    PDA.focusAfter = null;
    if (modal && modal.type === 'find') target = vscreen.querySelector('#find-q');
    if (target) focusField(target);
    updateShiftBadge();
  };

  function focusField(el) {
    el.focus({ preventScroll: true });
    try { el.setSelectionRange(el.value.length, el.value.length); } catch (e) {}
    lastField = el;
  }

  /* ================= action dispatch ================= */

  function shellAction(a, el) {
    var ns = a.split(':')[0], what = a.split(':')[1];

    if (ns === 'cf') {
      var yes = modal && modal.onYes;
      modal = null;
      if (what === 'ok' && yes) yes();
      PDA.render();
      return true;
    }
    if (ns === 'kb') {
      if (what === 'key') insertText(el.dataset.k);
      else if (what === 'back') backspace();
      else if (what === 'ret') command('enter');
      else if (what === 'shift') kbShift = !kbShift;
      else if (what === 'tab') kbTab = el.dataset.t;
      else if (what === 'done') modal = null;
      if (what === 'key' && kbShift && kbTab === 'abc') kbShift = false;
      PDA.render();
      return true;
    }
    if (ns === 'find') {
      if (what === 'q') { findQ = el.value; PDA.render(); return true; }
      if (what === 'done') { modal = null; PDA.render(); return true; }
      if (what === 'go') {
        var r = findResults()[+el.dataset.i];
        modal = null;
        if (r) {
          if (r.app === 'memo') { APPS.memo.v.id = r.id; APPS.memo.v.view = 'edit'; }
          if (r.app === 'address') { APPS.address.v.id = r.id; APPS.address.v.view = 'view'; }
          if (r.app === 'datebook') { APPS.datebook.v.key = r.id; APPS.datebook.v.top = Math.max(0, r.hour - 1); }
          cur = r.app;
        }
        PDA.render();
        return true;
      }
    }
    if (ns === 'menu') {
      var items = menu || [];
      var picked = what === 'pick' ? items[+el.dataset.i] : null;
      menu = null;
      if (picked) {
        if (picked.go) { PDA.open(picked.go); return true; }
        if (picked.act && APPS[cur].act) APPS[cur].act(picked.act, el);
      }
      PDA.render();
      return true;
    }
    return false;
  }

  vscreen.addEventListener('click', function (e) {
    if (!powered) return;
    var el = e.target.closest('[data-act]');
    if (!el || el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') return;
    var a = el.dataset.act;
    if (a.indexOf(':') > -1) { shellAction(a, el); return; }
    if (menu) { menu = null; }
    var handled = APPS[cur].act ? APPS[cur].act(a, el) : null;
    if (handled !== true) PDA.render();
  });

  vscreen.addEventListener('input', function (e) {
    var el = e.target.closest('[data-act]');
    if (!el) return;
    var a = el.dataset.act;
    if (a.indexOf(':') > -1) { shellAction(a, el); return; }
    var handled = APPS[cur].act ? APPS[cur].act(a, el) : null;
    if (handled !== true) PDA.render();
  });

  vscreen.addEventListener('focusin', function (e) {
    if (e.target.classList && e.target.classList.contains('fld')) lastField = e.target;
  });

  /* keep taps on the keyboard and the Graffiti pad from stealing focus */
  document.addEventListener('mousedown', function (e) {
    if (e.target.closest && e.target.closest('[data-nofocus], #pad')) e.preventDefault();
  });

  /* ================= text entry ================= */

  function activeField() {
    var el = document.activeElement;
    if (el && vscreen.contains(el) && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) return el;
    if (lastField && vscreen.contains(lastField)) return lastField;
    return null;
  }

  function fields() {
    return Array.prototype.slice.call(vscreen.querySelectorAll('.fld'));
  }

  function insertText(t) {
    var el = activeField();
    if (!el) {
      if (APPS[cur].input && APPS[cur].input(t)) { PDA.render(); return true; }
      el = fields()[0];
      if (!el) return false;
      focusField(el);
    }
    el.focus({ preventScroll: true });
    var s = el.selectionStart, e2 = el.selectionEnd;
    if (s == null) el.value += t;
    else el.setRangeText(t, s, e2, 'end');
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  }

  function backspace() {
    var el = activeField();
    if (!el) return false;
    el.focus({ preventScroll: true });
    var s = el.selectionStart, e2 = el.selectionEnd;
    if (s === e2) { if (s === 0) return true; s -= 1; }
    el.setRangeText('', s, e2, 'end');
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return true;
  }

  function focusNext(delta) {
    var list = fields();
    if (!list.length) return;
    var el = activeField();
    var i = list.indexOf(el);
    focusField(list[(i + (delta || 1) + list.length) % list.length]);
  }

  function command(cmd) {
    if (cmd === 'space') return insertText(' ');
    if (cmd === 'backspace') return backspace();
    if (cmd === 'tab') { focusNext(1); return true; }
    if (cmd === 'shift') { shift = (shift + 1) % 3; updateShiftBadge(); return true; }
    if (cmd === 'enter') {
      var el = activeField();
      if (el && el.tagName === 'TEXTAREA') return insertText('\n');
      focusNext(1);
      return true;
    }
    return false;
  }

  function updateShiftBadge() {
    if (!padshift) return;
    padshift.textContent = shift === 1 ? '⇧' : shift === 2 ? '⇪' : '';
    padshift.hidden = shift === 0;
  }

  function flashPad(mark) {
    if (!padshift) return;
    padshift.hidden = false;
    padshift.textContent = mark;
    setTimeout(updateShiftBadge, 420);
  }

  /* ================= the Graffiti pad ================= */

  var ctx = ink.getContext('2d');
  var stroke = null;

  function sizeInk() {
    var w = pad.clientWidth, h = pad.clientHeight;
    var dpr = Math.min(3, window.devicePixelRatio || 1);
    ink.width = Math.max(1, Math.round(w * dpr));
    ink.height = Math.max(1, Math.round(h * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineWidth = 2.4;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = '#e9eef5';
  }

  function padPoint(e) {
    var r = pad.getBoundingClientRect();
    return {
      x: (e.clientX - r.left) / r.width * pad.clientWidth,
      y: (e.clientY - r.top) / r.height * pad.clientHeight
    };
  }

  pad.addEventListener('pointerdown', function (e) {
    if (!powered) return;
    if (e.target.closest('.pad-tag')) return;
    e.preventDefault();
    try { pad.setPointerCapture(e.pointerId); } catch (err) {}
    var p = padPoint(e);
    stroke = {
      pts: [p],
      area: p.x < pad.clientWidth * GRAFFITI.DIVIDE ? 'letters' : 'numbers'
    };
    ctx.clearRect(0, 0, pad.clientWidth, pad.clientHeight);
    ink.style.opacity = '1';
    if (PDA.prefs.ink) { ctx.beginPath(); ctx.moveTo(p.x, p.y); }
  });

  pad.addEventListener('pointermove', function (e) {
    if (!stroke) return;
    e.preventDefault();
    var p = padPoint(e);
    stroke.pts.push(p);
    if (PDA.prefs.ink) { ctx.lineTo(p.x, p.y); ctx.stroke(); }
  });

  function endStroke() {
    if (!stroke) return;
    var s = stroke;
    stroke = null;
    ink.style.opacity = '0';
    setTimeout(function () { ctx.clearRect(0, 0, pad.clientWidth, pad.clientHeight); }, 200);

    var len = GRAFFITI.pathLength(s.pts);
    if (len < 9) { emit({ out: '.' }); return; }          /* a tap writes a period */

    var r = GRAFFITI.recognize(s.pts, s.area, PDA.prefs.threshold);
    if (!r) { flashPad('?'); return; }
    emit(r);
  }

  /* the pad captures the pointer, so the release can land anywhere */
  window.addEventListener('pointerup', endStroke);
  window.addEventListener('pointercancel', endStroke);

  function emit(r) {
    if (r.cmd) { command(r.cmd); return; }
    var ch = r.out;
    if (shift > 0 && /[a-z]/.test(ch)) {
      ch = ch.toUpperCase();
      if (shift === 1) { shift = 0; updateShiftBadge(); }
    }
    if (!insertText(ch)) flashPad('?');
  }

  /* ================= silkscreen, keys, power ================= */

  document.querySelectorAll('[data-silk]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (!powered) return;
      var which = b.dataset.silk;
      if (which === 'home') PDA.open('launcher');
      else if (which === 'calc') PDA.open('calc');
      else if (which === 'menu') { menu = menu ? null : menuItems(); modal = null; PDA.render(); }
      else if (which === 'find') { modal = { type: 'find' }; menu = null; findQ = ''; PDA.render(); }
    });
  });

  document.querySelectorAll('[data-kb]').forEach(function (b) {
    b.addEventListener('click', function () {
      if (!powered) return;
      kbTab = b.dataset.kb === '123' ? '123' : 'abc';
      modal = { type: 'keyboard' };
      menu = null;
      PDA.render();
    });
  });

  var HW = { date: 'datebook', address: 'address', todo: 'todo', memo: 'memo' };
  document.querySelectorAll('[data-hw]').forEach(function (b) {
    b.addEventListener('click', function () {
      var which = b.dataset.hw;
      if (!powered) { setPower(true); return; }
      if (HW[which]) { PDA.open(HW[which]); return; }
      var app = APPS[cur];
      if (app.scroll) app.scroll(which === 'down' ? 1 : -1);
    });
  });

  function setPower(on) {
    powered = on;
    screenoff.hidden = on;
    led.classList.toggle('on', !on ? false : PDA.prefs.skin === 'backlit');
  }

  /* tap the power key to sleep or wake; hold it for the backlight */
  var powerEl = document.getElementById('power');
  var holdTimer = null, held = false;

  function toggleBacklight() {
    PDA.prefs.skin = PDA.prefs.skin === 'backlit' ? 'classic' : 'backlit';
    PDA.save();
    PDA.applyPrefs();
    setPower(true);
  }

  powerEl.addEventListener('pointerdown', function () {
    held = false;
    holdTimer = setTimeout(function () { held = true; toggleBacklight(); }, 450);
  });
  powerEl.addEventListener('pointerup', function () {
    clearTimeout(holdTimer);
    if (!held) setPower(!powered);
  });
  powerEl.addEventListener('pointercancel', function () { clearTimeout(holdTimer); });

  /* ================= physical keyboard ================= */

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && (modal || menu)) { modal = null; menu = null; PDA.render(); e.preventDefault(); return; }
    var el = document.activeElement;
    if (el && vscreen.contains(el) && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA')) return;
    if (cur === 'calc' && APPS.calc.input) {
      if (/^[0-9.]$/.test(e.key)) { APPS.calc.input(e.key); PDA.render(); e.preventDefault(); }
      else if ('+-*/'.indexOf(e.key) > -1) { APPS.calc.act('op' + e.key); PDA.render(); e.preventDefault(); }
      else if (e.key === 'Enter' || e.key === '=') { APPS.calc.act('eq'); PDA.render(); e.preventDefault(); }
      else if (e.key === 'Escape') { APPS.calc.act('clear'); PDA.render(); }
    }
  });

  /* ================= fit the device to the viewport ================= */

  function fit() {
    fitEl.style.transform = 'none';
    fitEl.style.width = '';
    fitEl.style.height = '';
    var w = deviceEl.offsetWidth, h = deviceEl.offsetHeight;
    if (!w || !h) return;
    var availW = stageEl.clientWidth - 32;
    var availH = window.innerHeight - 150;
    var k = Math.min(1, availW / w, availH / h);
    if (k >= 0.999) return;
    fitEl.style.transform = 'scale(' + k + ')';
    fitEl.style.width = (w * k) + 'px';
    fitEl.style.height = (h * k) + 'px';
  }

  window.addEventListener('resize', function () { fit(); sizeInk(); });

  /* ================= boot ================= */

  pad.style.setProperty('--divide', (GRAFFITI.DIVIDE * 100).toFixed(2) + '%');
  PDA.applyPrefs();
  setPower(true);
  sizeInk();
  PDA.render();
  fit();

  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(function () { fit(); sizeInk(); });
  }
})();
