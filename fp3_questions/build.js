// Rebuilds fp3_tracker.html's DATA array from the per-chapter JSON files in this directory.
// Usage: node fp3_questions/build.js <path-to-fp3_tracker.html>
const fs = require('fs');
const path = require('path');

const htmlPath = process.argv[2];
if (!htmlPath) throw new Error('Usage: node build.js <path-to-fp3_tracker.html>');

const dir = __dirname;
const order = ['lp', 'risk', 'invest', 'tax', 're', 'souzoku'];
const chapters = order.map(id => JSON.parse(fs.readFileSync(path.join(dir, `${id}.json`), 'utf8')));

const dataJs = 'const DATA = ' + JSON.stringify(chapters, null, 2) + ';\n';

const html = fs.readFileSync(htmlPath, 'utf8');
const newHtml = html.replace(/const DATA = \[[\s\S]*?\n\];\n/, dataJs);
if (newHtml === html) throw new Error('DATA array not replaced — pattern mismatch');
fs.writeFileSync(htmlPath, newHtml, 'utf8');

let total = 0;
for (const ch of chapters) {
  console.log(`${ch.id}: ${ch.quiz.length} questions, ${ch.cards.length} cards`);
  total += ch.quiz.length;
}
console.log(`TOTAL: ${total} questions`);
