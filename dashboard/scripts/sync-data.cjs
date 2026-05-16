/**
 * Sync JSON data files from docs/assets/data/ into dashboard/public/data/.
 * Run: node scripts/sync-data.cjs
 */
const fs = require('fs');
const path = require('path');

const SRC  = path.resolve(__dirname, '../../docs/assets/data');
const DEST = path.resolve(__dirname, '../public/data');

if (!fs.existsSync(DEST)) fs.mkdirSync(DEST, { recursive: true });

const files = fs.readdirSync(SRC).filter(f => f.endsWith('.json'));
files.forEach(f => {
  fs.copyFileSync(path.join(SRC, f), path.join(DEST, f));
  console.log(`synced: ${f}`);
});
console.log(`Done — ${files.length} files synced.`);
