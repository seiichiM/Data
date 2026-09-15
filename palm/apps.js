/* ---------------------------------------------------------------
   The applications that ship on the device.

   Every app exposes:
     title   shown in the title bar and under its launcher icon
     icon    24x24 SVG markup for the launcher
     render()  -> HTML for the 160x160 screen
     act(a, el) -> handle a tap on [data-act]
     input(ch, cmd) -> optional; receives Graffiti when no field is focused
     scroll(dir)    -> optional; the hardware rocker
     menu()         -> optional; items for the silkscreen Menu button
   --------------------------------------------------------------- */

(function () {
  'use strict';

  var PER = 9;              /* list rows that fit on one screen */
  var DAY = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function tbar(title, info) {
    return '<div class="tbar"><span>' + esc(title) + '</span><span class="grow"></span>' +
      '<span class="tinfo">' + (info || '') + '</span></div>';
  }

  function screen(bar, body, bottom, flush) {
    return '<div class="app">' + bar +
      '<div class="pane' + (flush ? ' flush' : '') + '">' + body + '</div>' +
      '<div class="bbar">' + (bottom || '') + '</div></div>';
  }

  function btn(label, act, attrs) {
    return '<button type="button" class="btn' + (attrs && attrs.cls ? ' ' + attrs.cls : '') +
      '" data-act="' + act + '"' +
      (attrs && attrs.data ? ' ' + attrs.data : '') +
      (attrs && attrs.disabled ? ' disabled' : '') +
      (attrs && attrs.pressed ? ' aria-pressed="true"' : '') +
      '>' + label + '</button>';
  }

  function arrows(canUp, canDown) {
    return '<span class="arrows inline">' +
      '<button type="button" data-act="pageup"' + (canUp ? '' : ' disabled') +
      ' aria-label="Scroll up"><svg viewBox="0 0 10 8"><path d="M5 1 9 7H1z"/></svg></button>' +
      '<button type="button" data-act="pagedown"' + (canDown ? '' : ' disabled') +
      ' aria-label="Scroll down"><svg viewBox="0 0 10 8"><path d="M5 7 1 1h8z"/></svg></button></span>';
  }

  function field(cls, value, act, extra) {
    return '<input class="fld ' + (cls || '') + '" type="text" value="' + esc(value) +
      '" data-act="' + act + '"' + (extra || '') + '>';
  }

  function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }

  function dateKey(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' +
      String(d.getDate()).padStart(2, '0');
  }

  function fromKey(k) {
    var p = k.split('-');
    return new Date(+p[0], +p[1] - 1, +p[2]);
  }

  /* =================================================================
     Date Book — one line per hour, the way the original day view read
     ================================================================= */

  var datebook = {
    title: 'Date Book',
    v: { key: null, top: 7 },
    icon: '<svg viewBox="0 0 24 24"><rect x="2.5" y="4.5" width="19" height="17" rx="2"/>' +
      '<path d="M2.5 9.5h19"/><path d="M7.5 2.5v4M16.5 2.5v4"/>' +
      '<rect class="solid" x="6" y="12.5" width="3" height="3"/>' +
      '<rect class="solid" x="11" y="12.5" width="3" height="3"/>' +
      '<rect class="solid" x="16" y="12.5" width="3" height="3"/></svg>',

    day: function () {
      if (!this.v.key) this.v.key = dateKey(new Date());
      return this.v.key;
    },

    slots: function () {
      var k = this.day();
      if (!PDA.db.events[k]) PDA.db.events[k] = {};
      return PDA.db.events[k];
    },

    render: function () {
      var k = this.day(), d = fromKey(k), s = this.slots();
      var top = this.v.top, rows = '';
      for (var i = 0; i < PER; i++) {
        var h = top + i;
        if (h > 23) break;
        var label = (h % 12 === 0 ? 12 : h % 12) + ':00' + (h >= 12 ? 'p' : 'a');
        rows += '<div class="row"><span class="tag" style="width:30px;flex:none">' + label + '</span>' +
          '<input class="fld bare grow" type="text" data-act="slot" data-h="' + h +
          '" value="' + esc(s[h] || '') + '"></div>';
      }
      var info = DAY[d.getDay()] + ' ' + d.getDate() + ' ' + MON[d.getMonth()];
      return screen(
        tbar('Date Book', info),
        '<div class="rowlist">' + rows + '</div>',
        btn('&#9664;', 'prev') + btn('Today', 'today') + btn('&#9654;', 'next') +
        '<span class="grow"></span>' + arrows(top > 0, top + PER <= 23),
        true
      );
    },

    scroll: function (dir) {
      this.v.top = Math.max(0, Math.min(23 - PER + 1, this.v.top + dir * 3));
      PDA.render();
    },

    menu: function () {
      return [{ label: 'Go to today', act: 'today' }, { label: 'Purge past days', act: 'purge' }];
    },

    act: function (a, el) {
      var d;
      if (a === 'slot') {
        var s = this.slots();
        if (el.value.trim()) s[el.dataset.h] = el.value; else delete s[el.dataset.h];
        PDA.save();
        return true;                       /* handled without re-rendering */
      }
      if (a === 'prev' || a === 'next') {
        d = fromKey(this.day());
        d.setDate(d.getDate() + (a === 'next' ? 1 : -1));
        this.v.key = dateKey(d);
      } else if (a === 'today') {
        this.v.key = dateKey(new Date());
        this.v.top = 7;
      } else if (a === 'pageup') { this.v.top = Math.max(0, this.v.top - PER); }
      else if (a === 'pagedown') { this.v.top = Math.min(23 - PER + 1, this.v.top + PER); }
      else if (a === 'purge') {
        var today = dateKey(new Date());
        Object.keys(PDA.db.events).forEach(function (key) {
          if (key < today) delete PDA.db.events[key];
        });
        PDA.save();
      }
    }
  };

  /* =================================================================
     Address
     ================================================================= */

  var address = {
    title: 'Address',
    v: { view: 'list', top: 0, id: null, look: '' },
    icon: '<svg viewBox="0 0 24 24"><rect x="2.5" y="3.5" width="19" height="17" rx="2"/>' +
      '<circle cx="9" cy="10" r="2.6"/><path d="M4.8 17.6c0-2.6 2-4 4.2-4s4.2 1.4 4.2 4"/>' +
      '<path d="M15.5 8.5h4M15.5 12h4M15.5 15.5h2.5"/></svg>',

    list: function () {
      var q = this.v.look.toLowerCase();
      return PDA.db.contacts
        .filter(function (c) {
          if (!q) return true;
          return ((c.last || '') + ' ' + (c.first || '') + ' ' + (c.company || '')).toLowerCase().indexOf(q) === 0 ||
            ((c.last || '') + ' ' + (c.first || '') + ' ' + (c.company || '')).toLowerCase().indexOf(' ' + q) > -1;
        })
        .sort(function (a, b) {
          return ((a.last || a.first || '') + (a.first || '')).localeCompare((b.last || b.first || '') + (b.first || ''));
        });
    },

    current: function () {
      var id = this.v.id;
      return PDA.db.contacts.filter(function (c) { return c.id === id; })[0];
    },

    render: function () {
      if (this.v.view === 'list') return this.renderList();
      var c = this.current();
      if (!c) { this.v.view = 'list'; return this.renderList(); }
      return this.v.view === 'edit' ? this.renderEdit(c) : this.renderView(c);
    },

    renderList: function () {
      var items = this.list(), top = this.v.top, rows = '';
      items.slice(top, top + PER - 1).forEach(function (c) {
        var name = [c.last, c.first].filter(Boolean).join(', ') || c.company || 'Unnamed';
        rows += '<div class="row" data-act="show" data-id="' + c.id + '">' +
          '<span class="grow">' + esc(name) + '</span>' +
          '<span class="tag">' + esc(c.phone || '') + '</span></div>';
      });
      if (!items.length) rows = '<div class="empty">No addresses.<br>Tap New to add one.</div>';
      return screen(
        tbar('Address', String(items.length)),
        '<div class="rowlist">' + rows + '</div>',
        btn('New', 'new') +
        '<span class="grow" style="display:flex;align-items:baseline;gap:2px">' +
        '<span class="tag" style="font-size:8px">Look&nbsp;Up:</span>' +
        field('grow', this.v.look, 'look', ' id="addr-look"') + '</span>' +
        arrows(top > 0, top + PER - 1 < items.length),
        true
      );
    },

    renderView: function (c) {
      var line = function (l, v) {
        return v ? '<div class="fldrow"><label>' + l + '</label><span class="grow">' + esc(v) + '</span></div>' : '';
      };
      var name = [c.first, c.last].filter(Boolean).join(' ') || c.company || 'Unnamed';
      return screen(
        tbar('Address View'),
        '<div style="font-weight:700;margin-bottom:3px">' + esc(name) + '</div>' +
        line('Co', c.company) + line('Work', c.phone) + line('Mail', c.email) +
        (c.note ? '<div style="margin-top:3px;font-size:9px">' + esc(c.note) + '</div>' : ''),
        btn('Done', 'back') + btn('Edit', 'edit') + '<span class="grow"></span>' + btn('Delete', 'del')
      );
    },

    renderEdit: function (c) {
      var row = function (l, key, val) {
        return '<div class="fldrow"><label>' + l + '</label>' +
          field('grow', val || '', 'set', ' data-key="' + key + '"') + '</div>';
      };
      return screen(
        tbar('Address Edit'),
        row('Last', 'last', c.last) + row('First', 'first', c.first) +
        row('Co', 'company', c.company) + row('Work', 'phone', c.phone) +
        row('Mail', 'email', c.email) +
        '<div class="fldrow"><label>Note</label>' +
        '<textarea class="fld grow" rows="3" data-act="set" data-key="note">' + esc(c.note || '') + '</textarea></div>',
        btn('Done', 'back') + '<span class="grow"></span>' + btn('Delete', 'del')
      );
    },

    scroll: function (dir) { this.act(dir > 0 ? 'pagedown' : 'pageup'); PDA.render(); },

    menu: function () {
      return this.v.view === 'list'
        ? [{ label: 'New address', act: 'new' }]
        : [{ label: 'Delete address', act: 'del' }, { label: 'Back to list', act: 'back' }];
    },

    act: function (a, el) {
      var self = this, c;
      if (a === 'set') {
        c = this.current();
        if (c) { c[el.dataset.key] = el.value; PDA.save(); }
        return true;
      }
      if (a === 'look') { this.v.look = el.value; this.v.top = 0; PDA.focusAfter = '#addr-look'; PDA.render(); return true; }
      if (a === 'show') { this.v.id = el.dataset.id; this.v.view = 'view'; }
      else if (a === 'edit') { this.v.view = 'edit'; PDA.focusAfter = '.fld'; }
      else if (a === 'back') { this.v.view = 'list'; }
      else if (a === 'new') {
        c = { id: uid(), last: '', first: '', company: '', phone: '', email: '', note: '' };
        PDA.db.contacts.push(c);
        PDA.save();
        this.v.id = c.id; this.v.view = 'edit';
        PDA.focusAfter = '.fld';
      } else if (a === 'del') {
        PDA.confirm('Delete Address', 'Delete this record?', function () {
          PDA.db.contacts = PDA.db.contacts.filter(function (x) { return x.id !== self.v.id; });
          PDA.save();
          self.v.view = 'list';
        });
      } else if (a === 'pageup') { this.v.top = Math.max(0, this.v.top - (PER - 1)); }
      else if (a === 'pagedown') {
        if (this.v.top + PER - 1 < this.list().length) this.v.top += PER - 1;
      }
    }
  };

  /* =================================================================
     To Do List
     ================================================================= */

  var todo = {
    title: 'To Do',
    v: { top: 0, hideDone: false },
    icon: '<svg viewBox="0 0 24 24"><rect x="2.5" y="3.5" width="7" height="7" rx="1.2"/>' +
      '<path d="M4.4 7.1 6.2 9l3.4-4.6"/><path d="M12.5 7h9"/>' +
      '<rect x="2.5" y="13.5" width="7" height="7" rx="1.2"/><path d="M12.5 17h9"/></svg>',

    list: function () {
      var v = this.v;
      return PDA.db.todos
        .filter(function (t) { return !(v.hideDone && t.done); })
        .sort(function (a, b) { return (a.done - b.done) || (a.pri - b.pri); });
    },

    render: function () {
      var items = this.list(), top = this.v.top, rows = '';
      items.slice(top, top + PER).forEach(function (t) {
        rows += '<div class="row">' +
          '<button type="button" class="btn plain" data-act="done" data-id="' + t.id +
          '" style="width:10px;height:10px;padding:0;border:1px solid currentColor;border-radius:2px;flex:none;line-height:1;font-size:8px">' +
          (t.done ? '&#10003;' : '') + '</button>' +
          '<button type="button" class="btn plain" data-act="pri" data-id="' + t.id +
          '" style="flex:none;font-size:8px">' + t.pri + '</button>' +
          '<input class="fld bare grow" type="text" data-act="text" data-id="' + t.id +
          '" value="' + esc(t.text) + '"' + (t.done ? ' style="text-decoration:line-through"' : '') + '>' +
          '</div>';
      });
      if (!items.length) rows = '<div class="empty">Nothing to do.<br>Tap New to add an item.</div>';
      return screen(
        tbar('To Do List', items.filter(function (t) { return !t.done; }).length + ' open'),
        '<div class="rowlist">' + rows + '</div>',
        btn('New', 'new') + btn('Purge', 'purge') +
        btn(this.v.hideDone ? 'Show&nbsp;All' : 'Hide&nbsp;Done', 'toggle') +
        '<span class="grow"></span>' + arrows(top > 0, top + PER < items.length),
        true
      );
    },

    find: function (id) {
      return PDA.db.todos.filter(function (t) { return t.id === id; })[0];
    },

    scroll: function (dir) { this.act(dir > 0 ? 'pagedown' : 'pageup'); PDA.render(); },

    menu: function () {
      return [{ label: 'New item', act: 'new' }, { label: 'Purge completed', act: 'purge' }];
    },

    act: function (a, el) {
      var t;
      if (a === 'text') {
        t = this.find(el.dataset.id);
        if (t) { t.text = el.value; PDA.save(); }
        return true;
      }
      if (a === 'done') { t = this.find(el.dataset.id); if (t) { t.done = !t.done; PDA.save(); } }
      else if (a === 'pri') { t = this.find(el.dataset.id); if (t) { t.pri = t.pri % 5 + 1; PDA.save(); } }
      else if (a === 'new') {
        t = { id: uid(), text: '', pri: 1, done: false };
        PDA.db.todos.push(t);
        PDA.save();
        PDA.focusAfter = '[data-id="' + t.id + '"].fld';
      } else if (a === 'toggle') { this.v.hideDone = !this.v.hideDone; this.v.top = 0; }
      else if (a === 'purge') {
        PDA.confirm('Purge', 'Delete all completed items?', function () {
          PDA.db.todos = PDA.db.todos.filter(function (x) { return !x.done; });
          PDA.save();
        });
      } else if (a === 'pageup') { this.v.top = Math.max(0, this.v.top - PER); }
      else if (a === 'pagedown') { if (this.v.top + PER < this.list().length) this.v.top += PER; }
    }
  };

  /* =================================================================
     Memo Pad
     ================================================================= */

  var memo = {
    title: 'Memo Pad',
    v: { view: 'list', top: 0, id: null },
    icon: '<svg viewBox="0 0 24 24"><path d="M5 2.5h14v19H5z"/>' +
      '<path d="M8 7.5h8M8 11.5h8M8 15.5h5"/></svg>',

    current: function () {
      var id = this.v.id;
      return PDA.db.memos.filter(function (m) { return m.id === id; })[0];
    },

    render: function () {
      if (this.v.view === 'edit') {
        var m = this.current();
        if (!m) { this.v.view = 'list'; return this.render(); }
        return screen(
          tbar('Memo', String(PDA.db.memos.indexOf(m) + 1) + ' of ' + PDA.db.memos.length),
          '<textarea class="fld bare" id="memo-edit" data-act="text" ' +
          'style="position:absolute;inset:2px 3px;width:auto">' + esc(m.text) + '</textarea>',
          btn('Done', 'back') + '<span class="grow"></span>' + btn('Delete', 'del'),
          true
        );
      }
      var top = this.v.top, rows = '';
      PDA.db.memos.slice(top, top + PER).forEach(function (m, i) {
        var first = (m.text || '').split('\n')[0] || 'Untitled';
        rows += '<div class="row" data-act="show" data-id="' + m.id + '">' +
          '<span class="tag" style="width:10px;flex:none">' + (top + i + 1) + '.</span>' +
          '<span class="grow">' + esc(first) + '</span></div>';
      });
      if (!PDA.db.memos.length) rows = '<div class="empty">No memos.<br>Tap New to write one.</div>';
      return screen(
        tbar('Memo Pad', String(PDA.db.memos.length)),
        '<div class="rowlist">' + rows + '</div>',
        btn('New', 'new') + '<span class="grow"></span>' +
        arrows(top > 0, top + PER < PDA.db.memos.length),
        true
      );
    },

    scroll: function (dir) { this.act(dir > 0 ? 'pagedown' : 'pageup'); PDA.render(); },

    menu: function () {
      return this.v.view === 'edit'
        ? [{ label: 'Delete memo', act: 'del' }, { label: 'Back to list', act: 'back' }]
        : [{ label: 'New memo', act: 'new' }];
    },

    act: function (a, el) {
      var self = this, m;
      if (a === 'text') {
        m = this.current();
        if (m) { m.text = el.value; PDA.save(); }
        return true;
      }
      if (a === 'show') { this.v.id = el.dataset.id; this.v.view = 'edit'; PDA.focusAfter = '#memo-edit'; }
      else if (a === 'back') { this.v.view = 'list'; }
      else if (a === 'new') {
        m = { id: uid(), text: '' };
        PDA.db.memos.unshift(m);
        PDA.save();
        this.v.id = m.id; this.v.view = 'edit';
        PDA.focusAfter = '#memo-edit';
      } else if (a === 'del') {
        PDA.confirm('Delete Memo', 'Delete this memo?', function () {
          PDA.db.memos = PDA.db.memos.filter(function (x) { return x.id !== self.v.id; });
          PDA.save();
          self.v.view = 'list';
        });
      } else if (a === 'pageup') { this.v.top = Math.max(0, this.v.top - PER); }
      else if (a === 'pagedown') { if (this.v.top + PER < PDA.db.memos.length) this.v.top += PER; }
    }
  };

  /* =================================================================
     Calculator — takes Graffiti from the number half of the pad
     ================================================================= */

  var KEYS = [
    ['CE', 'ce'], ['C', 'clear'], ['&plusmn;', 'neg'], ['&divide;', 'op/'],
    ['7', 'd7'], ['8', 'd8'], ['9', 'd9'], ['&times;', 'op*'],
    ['4', 'd4'], ['5', 'd5'], ['6', 'd6'], ['&minus;', 'op-'],
    ['1', 'd1'], ['2', 'd2'], ['3', 'd3'], ['+', 'op+'],
    ['0', 'd0'], ['.', 'dot'], ['&radic;', 'sqrt'], ['=', 'eq']
  ];

  var calc = {
    title: 'Calc',
    v: { show: '0', acc: null, op: null, fresh: true },
    icon: '<svg viewBox="0 0 24 24"><rect x="4.5" y="2.5" width="15" height="19" rx="2"/>' +
      '<rect x="7" y="5.5" width="10" height="3.5" rx="0.6"/>' +
      '<circle class="solid" cx="8.6" cy="13" r="1.1"/><circle class="solid" cx="12" cy="13" r="1.1"/>' +
      '<circle class="solid" cx="15.4" cy="13" r="1.1"/><circle class="solid" cx="8.6" cy="17.4" r="1.1"/>' +
      '<circle class="solid" cx="12" cy="17.4" r="1.1"/><circle class="solid" cx="15.4" cy="17.4" r="1.1"/></svg>',

    render: function () {
      var grid = KEYS.map(function (k) {
        return btn(k[0], k[1], { cls: /^(op|eq|sqrt|neg)/.test(k[1]) ? 'op' : '' });
      }).join('');
      return screen(
        tbar('Calculator'),
        '<div class="calcout">' + esc(this.v.show) + '</div>' +
        '<div class="calcgrid">' + grid + '</div>',
        ''
      );
    },

    push: function (ch) {
      var v = this.v;
      if (v.fresh) { v.show = (ch === '.' ? '0.' : ch); v.fresh = false; return; }
      if (ch === '.' && v.show.indexOf('.') > -1) return;
      if (v.show === '0' && ch !== '.') v.show = ch; else v.show += ch;
    },

    apply: function () {
      var v = this.v, b = parseFloat(v.show), a = v.acc, r = b;
      if (a != null && v.op) {
        if (v.op === '+') r = a + b;
        else if (v.op === '-') r = a - b;
        else if (v.op === '*') r = a * b;
        else if (v.op === '/') r = b === 0 ? NaN : a / b;
      }
      v.show = isFinite(r) ? String(Math.round(r * 1e10) / 1e10) : 'Error';
      v.acc = isFinite(r) ? r : null;
    },

    /* Graffiti in the number half feeds the keypad directly */
    input: function (ch) {
      if (ch >= '0' && ch <= '9') this.act('d' + ch);
      else if (ch === '.') this.act('dot');
      else return false;
      return true;
    },

    act: function (a) {
      var v = this.v;
      if (a.charAt(0) === 'd' && a.length === 2) this.push(a.charAt(1));
      else if (a === 'dot') this.push('.');
      else if (a === 'clear') { v.show = '0'; v.acc = null; v.op = null; v.fresh = true; }
      else if (a === 'ce') { v.show = '0'; v.fresh = true; }
      else if (a === 'neg') { v.show = v.show.charAt(0) === '-' ? v.show.slice(1) : '-' + v.show; }
      else if (a === 'sqrt') {
        var n = parseFloat(v.show);
        v.show = n < 0 ? 'Error' : String(Math.round(Math.sqrt(n) * 1e10) / 1e10);
        v.fresh = true;
      } else if (a.slice(0, 2) === 'op') {
        this.apply();
        v.op = a.charAt(2);
        v.fresh = true;
      } else if (a === 'eq') {
        this.apply();
        v.op = null;
        v.fresh = true;
      }
    }
  };

  /* =================================================================
     Graffiti reference — drawn from the recognizer's own stroke table
     ================================================================= */

  var graffiti = {
    title: 'Graffiti',
    v: { tab: 'letters' },
    icon: '<svg viewBox="0 0 24 24"><path d="M4 19c3-9 6-13 8-13s2 4 0 8-4 5-4.6 2.2S10 8.5 15 6.5"/>' +
      '<circle class="solid" cx="4" cy="19" r="1.6"/><path d="M17 16.5h4"/></svg>',

    render: function () {
      var tab = this.v.tab, body;
      if (tab === 'extras') {
        body = '<div class="chart wide">' + GRAFFITI.commands.map(function (t) {
          return '<div class="glyph">' + GRAFFITI.svg(t.points, 20) + '<span>' + t.label + '</span></div>';
        }).join('') + '</div>' +
        '<p style="font-size:8px;margin:4px 2px 0;line-height:1.35">' +
        'A single tap writes a period. Two shift strokes lock caps. ' +
        'Tap <b>abc</b> or <b>123</b> under the pad for the on-screen keyboard.</p>';
      } else {
        var set = tab === 'letters' ? GRAFFITI.letters : GRAFFITI.digits;
        body = '<div class="chart">' + set.map(function (t) {
          return '<div class="glyph">' + GRAFFITI.svg(t.points, 20) + '<span>' + t.label + '</span></div>';
        }).join('') + '</div>' +
        '<p style="font-size:8px;margin:5px 2px 0;line-height:1.4">' +
        'The dot marks where the stroke starts, the arrow where it ends. ' +
        (tab === 'letters'
          ? 'Shapes are capitals; the device writes lowercase until you stroke shift.'
          : 'Numbers are only read on the right of the pad divider.') + '</p>';
      }
      return screen(
        tbar('Graffiti', 'stroke chart'),
        body,
        '<span class="tabs">' +
        btn('Letters', 'tab', { data: 'data-tab="letters"', pressed: tab === 'letters' }) +
        btn('Numbers', 'tab', { data: 'data-tab="numbers"', pressed: tab === 'numbers' }) +
        btn('Extras', 'tab', { data: 'data-tab="extras"', pressed: tab === 'extras' }) +
        '</span>'
      );
    },

    act: function (a, el) { if (a === 'tab') this.v.tab = el.dataset.tab; }
  };

  /* =================================================================
     HotSync — writes everything to the device's own store
     ================================================================= */

  var hotsync = {
    title: 'HotSync',
    v: { running: false, pct: 0, log: [] },
    icon: '<svg viewBox="0 0 24 24"><path d="M4 9.5A8 8 0 0 1 19.4 8"/><path d="M20 14.5A8 8 0 0 1 4.6 16"/>' +
      '<path d="M19.6 3.6v4.6h-4.6"/><path d="M4.4 20.4v-4.6H9"/></svg>',

    render: function () {
      var v = this.v;
      return screen(
        tbar('HotSync'),
        '<div class="sync">' +
        '<div style="font-size:9px">' + (v.running ? 'Synchronizing&hellip;' : 'Ready to synchronize') + '</div>' +
        '<div class="bar"><i style="width:' + v.pct + '%"></i></div>' +
        '<div class="synclog">' + v.log.map(function (l) { return esc(l); }).join('<br>') + '</div>' +
        '</div>',
        btn('HotSync', 'go', { disabled: v.running })
      );
    },

    act: function (a) {
      if (a !== 'go' || this.v.running) return;
      var self = this, db = PDA.db;
      var steps = [
        'Connecting to cradle',
        'Date Book — ' + Object.keys(db.events).length + ' day(s)',
        'Address — ' + db.contacts.length + ' record(s)',
        'To Do — ' + db.todos.length + ' item(s)',
        'Memo Pad — ' + db.memos.length + ' memo(s)',
        'HotSync complete.'
      ];
      this.v.running = true; this.v.log = []; this.v.pct = 0;
      PDA.render();
      var i = 0;
      var tick = setInterval(function () {
        self.v.log.push(steps[i]);
        self.v.pct = Math.round((i + 1) / steps.length * 100);
        if (++i >= steps.length) {
          clearInterval(tick);
          self.v.running = false;
          PDA.save();
        }
        PDA.render();
      }, 380);
    }
  };

  /* =================================================================
     Prefs
     ================================================================= */

  var SKINS = [['Classic', 'classic'], ['Backlit', 'backlit'], ['Gray', 'gray']];
  var SENSE = [['Strict', 0.78], ['Normal', 0.70], ['Loose', 0.62]];

  var prefs = {
    title: 'Prefs',
    v: { view: 'main' },
    icon: '<svg viewBox="0 0 24 24"><path d="M3 7h18M3 12h18M3 17h18"/>' +
      '<circle class="solid" cx="8" cy="7" r="2.3"/><circle class="solid" cx="15" cy="12" r="2.3"/>' +
      '<circle class="solid" cx="10" cy="17" r="2.3"/></svg>',

    render: function () {
      if (this.v.view === 'about') {
        return screen(
          tbar('About'),
          '<div style="font-size:9px;line-height:1.45">' +
          '<b>Graphite PDA 5</b><br>' +
          'A browser tribute to the late-1990s Palm OS organiser, ' +
          'with a Graffiti unistroke recognizer built on the $1 ' +
          'algorithm (resample &rarr; scale &rarr; translate), ' +
          'minus its rotation step so stroke direction still counts.' +
          '<br><br>Records live in this browser only. ' +
          'Not affiliated with Palm, Inc.</div>',
          btn('Done', 'main')
        );
      }
      var p = PDA.prefs;
      var row = function (label, body) {
        return '<div class="prefrow"><span class="lbl">' + label + '</span>' + body + '</div>';
      };
      return screen(
        tbar('Preferences'),
        row('Screen', SKINS.map(function (s) {
          return btn(s[0], 'skin', { data: 'data-v="' + s[1] + '"', pressed: p.skin === s[1] });
        }).join('')) +
        row('Strokes', SENSE.map(function (s) {
          return btn(s[0], 'sense', { data: 'data-v="' + s[1] + '"', pressed: p.threshold === s[1] });
        }).join('')) +
        row('Ink trail', btn(p.ink ? 'On' : 'Off', 'ink', { pressed: p.ink })) +
        row('System keys', btn(p.syskb ? 'On' : 'Off', 'syskb', { pressed: p.syskb })) +
        '<p style="font-size:8px;margin:4px 2px 0;color:var(--ink-soft)">' +
        'System keys lets a phone’s own keyboard open when you tap a field.</p>',
        btn('About', 'about') + '<span class="grow"></span>' + btn('Reset', 'reset')
      );
    },

    act: function (a, el) {
      var p = PDA.prefs;
      if (a === 'skin') p.skin = el.dataset.v;
      else if (a === 'sense') p.threshold = parseFloat(el.dataset.v);
      else if (a === 'ink') p.ink = !p.ink;
      else if (a === 'syskb') p.syskb = !p.syskb;
      else if (a === 'about') { this.v.view = 'about'; return; }
      else if (a === 'main') { this.v.view = 'main'; return; }
      else if (a === 'reset') {
        PDA.confirm('Reset Device', 'Erase all records?', function () { PDA.reset(); });
        return;
      }
      PDA.save();
      PDA.applyPrefs();
    }
  };

  /* =================================================================
     Launcher
     ================================================================= */

  var ORDER = ['datebook', 'address', 'todo', 'memo', 'calc', 'graffiti', 'hotsync', 'prefs'];

  var launcher = {
    title: 'Applications',
    v: {},
    render: function () {
      var apps = window.PALM_APPS;
      var tiles = ORDER.map(function (k) {
        return '<button type="button" class="tile" data-act="open" data-app="' + k + '">' +
          apps[k].icon + '<span>' + esc(apps[k].title) + '</span></button>';
      }).join('');
      var now = new Date();
      var info = DAY[now.getDay()] + ' ' + now.getDate() + ' ' + MON[now.getMonth()];
      return screen(tbar('Applications', info), '<div class="grid">' + tiles + '</div>', '', true);
    },
    act: function (a, el) { if (a === 'open') PDA.open(el.dataset.app); }
  };

  window.PALM_APPS = {
    launcher: launcher,
    datebook: datebook,
    address: address,
    todo: todo,
    memo: memo,
    calc: calc,
    graffiti: graffiti,
    hotsync: hotsync,
    prefs: prefs
  };

  window.PALM_UI = { esc: esc, tbar: tbar, screen: screen, btn: btn, uid: uid, dateKey: dateKey, DAY: DAY, MON: MON, ORDER: ORDER };
})();
