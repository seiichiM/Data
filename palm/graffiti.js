/* ---------------------------------------------------------------
   Graffiti — unistroke handwriting recognition.

   Each character is one stroke. Strokes are compared with the
   $1 Unistroke Recognizer's resample/scale/translate pipeline,
   minus the rotate-to-indicative-angle step: Graffiti is
   orientation sensitive (n vs u, m vs w), so rotation invariance
   would destroy exactly the information we need. The 1-D fix from
   $1's later revision is kept, so straight strokes (i, l, space)
   scale uniformly instead of being blown up into noise.

   The stroke shapes below are also the source for the on-device
   reference chart, so what the chart draws is by construction what
   the recognizer expects.
   --------------------------------------------------------------- */

window.GRAFFITI = (function () {
  'use strict';

  var DIVIDE = 0.62;      /* fraction of the pad width given to letters */
  var N = 40;             /* resample resolution */
  var SQUARE = 100;
  var HALF_DIAG = Math.sqrt(SQUARE * SQUARE * 2) / 2;

  function parse(s) {
    return s.trim().split(/\s+/).map(function (pair) {
      var xy = pair.split(',');
      return { x: parseFloat(xy[0]), y: parseFloat(xy[1]) };
    });
  }

  /* --- stroke table -------------------------------------------------
     Coordinates live in a 0..10 box, y pointing down, drawn in order. */

  var LETTER_SHAPES = {
    a: '0,10 5,0 10,10',
    b: '2,0 2,10 2,0 7,2 6,4 2,5 7,7 6,9 2,10',
    c: '9,1 6,0 2,2 1,5 2,8 6,10 9,9',
    d: '2,0 7,2 8,5 7,8 2,10 2,0',
    e: '8,2 5,0 2,1 2,4 6,5 2,6 2,9 5,10 8,8',
    f: '9,0 2,0 2,10 2,5 7,5',
    g: '9,1 6,0 2,2 1,5 2,8 6,10 9,8 9,5 5,5',
    h: '1,0 1,10 1,5 6,5 6,10',
    i: '5,0 5,10',
    j: '6,0 6,8 4,10 1,8',
    k: '1,0 1,10 1,5 6,0 1,5 6,10',
    l: '1,0 1,10 9,10',
    m: '1,10 1,0 5,8 9,0 9,10',
    n: '1,10 1,0 9,10 9,0',
    o: '5,0 2,2 1,5 2,8 5,10 8,8 9,5 8,2 5,0',
    p: '2,10 2,0 7,2 6,4 2,5',
    q: '8,8 5,10 2,8 1,5 2,2 5,0 8,2 9,5 8,8 9,10',
    r: '2,10 2,0 7,2 6,4 2,5 7,10',
    s: '9,1 5,0 2,2 3,4 6,5 8,7 6,10 2,9',
    t: '1,0 9,0 5,0 5,10',
    u: '1,0 1,7 3,10 7,10 9,7 9,0',
    v: '1,0 5,10 9,0',
    w: '1,0 3,10 5,3 7,10 9,0',
    x: '1,0 9,10 5,5 9,0 1,10',
    y: '1,0 4,5 7,0 7,7 4,10 1,9',
    z: '1,0 9,0 1,10 9,10'
  };

  var DIGIT_SHAPES = {
    '0': '5,0 2,2 1,5 2,8 5,10 8,8 9,5 8,2 5,0',
    '1': '5,0 5,10',
    '2': '1,2 4,0 7,2 1,10 9,10',
    '3': '1,1 5,0 7,3 4,5 7,7 5,10 1,9',
    '4': '6,0 1,7 9,7',
    '5': '9,0 3,0 2,4 6,4 8,6 6,10 2,9',
    '6': '8,0 4,1 2,4 2,8 5,10 8,8 7,5 3,5 2,7',
    '7': '1,0 9,0 3,10',
    '8': '8,1 4,0 2,2 5,5 8,7 7,10 3,10 2,7 5,5',
    '9': '7,5 4,6 2,4 3,1 6,0 8,3 8,6 6,10 3,10'
  };

  /* strokes that mean the same thing in both halves of the pad */
  var COMMAND_SHAPES = [
    { cmd: 'space',     label: 'Space',      shape: '1,5 9,5' },
    { cmd: 'backspace', label: 'Backspace',  shape: '9,5 1,5' },
    { cmd: 'enter',     label: 'Return',     shape: '9,0 1,10' },
    { cmd: 'tab',       label: 'Next field', shape: '1,10 9,0' },
    { cmd: 'shift',     label: 'Shift',      shape: '5,10 5,0' }
  ];

  /* --- $1 pipeline --------------------------------------------------- */

  function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }

  function pathLength(p) {
    var d = 0;
    for (var i = 1; i < p.length; i++) d += dist(p[i - 1], p[i]);
    return d;
  }

  function resample(points, n) {
    var interval = pathLength(points) / (n - 1);
    if (!(interval > 0)) return null;
    var src = points.slice();
    var out = [src[0]];
    var acc = 0;
    for (var i = 1; i < src.length; i++) {
      var d = dist(src[i - 1], src[i]);
      if (d === 0) continue;
      if (acc + d >= interval) {
        var t = (interval - acc) / d;
        var q = {
          x: src[i - 1].x + t * (src[i].x - src[i - 1].x),
          y: src[i - 1].y + t * (src[i].y - src[i - 1].y)
        };
        out.push(q);
        src.splice(i, 0, q);
        acc = 0;
      } else {
        acc += d;
      }
    }
    while (out.length < n) out.push(src[src.length - 1]);
    return out.slice(0, n);
  }

  function bbox(p) {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (var i = 0; i < p.length; i++) {
      if (p[i].x < minX) minX = p[i].x;
      if (p[i].y < minY) minY = p[i].y;
      if (p[i].x > maxX) maxX = p[i].x;
      if (p[i].y > maxY) maxY = p[i].y;
    }
    return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
  }

  function normalize(points) {
    if (!points || points.length < 2) return null;
    var p = resample(points, N);
    if (!p) return null;

    var b = bbox(p);
    var w = Math.max(b.w, 1e-6);
    var h = Math.max(b.h, 1e-6);
    var thin = Math.min(w, h) / Math.max(w, h) < 0.28;
    var sx = thin ? SQUARE / Math.max(w, h) : SQUARE / w;
    var sy = thin ? SQUARE / Math.max(w, h) : SQUARE / h;

    var i, cx = 0, cy = 0;
    for (i = 0; i < p.length; i++) {
      p[i] = { x: (p[i].x - b.x) * sx, y: (p[i].y - b.y) * sy };
      cx += p[i].x; cy += p[i].y;
    }
    cx /= p.length; cy /= p.length;
    for (i = 0; i < p.length; i++) { p[i].x -= cx; p[i].y -= cy; }
    return p;
  }

  function score(a, b) {
    var s = 0;
    for (var i = 0; i < a.length; i++) s += Math.hypot(a[i].x - b[i].x, a[i].y - b[i].y);
    return 1 - (s / a.length) / HALF_DIAG;
  }

  /* --- template sets -------------------------------------------------- */

  function tpl(def) {
    def.points = parse(def.shape);
    def.norm = normalize(def.points);
    return def;
  }

  var letterTemplates = [];
  var digitTemplates = [];
  var commandTemplates = [];

  Object.keys(LETTER_SHAPES).forEach(function (ch) {
    letterTemplates.push(tpl({ out: ch, label: ch.toUpperCase(), shape: LETTER_SHAPES[ch] }));
  });
  Object.keys(DIGIT_SHAPES).forEach(function (ch) {
    digitTemplates.push(tpl({ out: ch, label: ch, shape: DIGIT_SHAPES[ch] }));
  });
  COMMAND_SHAPES.forEach(function (c) {
    commandTemplates.push(tpl({ cmd: c.cmd, label: c.label, shape: c.shape }));
  });

  var SETS = {
    letters: letterTemplates.concat(commandTemplates),
    numbers: digitTemplates.concat(commandTemplates)
  };

  /* --- public API ----------------------------------------------------- */

  function recognize(points, set, threshold) {
    var candidate = normalize(points);
    if (!candidate) return null;
    var pool = SETS[set] || SETS.letters;
    var best = null, bestScore = -Infinity;
    for (var i = 0; i < pool.length; i++) {
      var s = score(candidate, pool[i].norm);
      if (s > bestScore) { bestScore = s; best = pool[i]; }
    }
    if (!best || bestScore < (threshold == null ? 0.7 : threshold)) return null;
    return { out: best.out, cmd: best.cmd, label: best.label, score: bestScore };
  }

  /* SVG for the on-device reference chart, built from the same points */
  function svg(points, size) {
    var s = size || 20;
    var pad = 3;
    var k = (s - pad * 2) / 10;
    var d = points.map(function (p, i) {
      return (i ? 'L' : 'M') + (pad + p.x * k).toFixed(2) + ' ' + (pad + p.y * k).toFixed(2);
    }).join(' ');

    var a = points[points.length - 2];
    var b = points[points.length - 1];
    var ang = Math.atan2(b.y - a.y, b.x - a.x);
    var tipX = pad + b.x * k, tipY = pad + b.y * k;
    var arm = 2.6;
    function leg(off) {
      return (tipX - arm * Math.cos(ang + off)).toFixed(2) + ',' +
             (tipY - arm * Math.sin(ang + off)).toFixed(2);
    }

    return '<svg viewBox="0 0 ' + s + ' ' + s + '" aria-hidden="true">' +
      '<path d="' + d + '"/>' +
      '<path d="M' + tipX.toFixed(2) + ' ' + tipY.toFixed(2) + ' L' + leg(0.45) + ' M' +
        tipX.toFixed(2) + ' ' + tipY.toFixed(2) + ' L' + leg(-0.45) + '"/>' +
      '<circle cx="' + (pad + points[0].x * k).toFixed(2) + '" cy="' +
        (pad + points[0].y * k).toFixed(2) + '" r="1.2"/>' +
      '</svg>';
  }

  return {
    DIVIDE: DIVIDE,
    recognize: recognize,
    svg: svg,
    letters: letterTemplates,
    digits: digitTemplates,
    commands: commandTemplates,
    pathLength: pathLength
  };
})();
