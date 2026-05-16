'use strict';

const REPO      = 'zjywy0228/privacy-preserving-data-architecture';
const DATA_BASE = 'assets/data/';

const MODULE_PALETTE = {
  'fhe-feature-extraction':  { bg: 'bg-blue-50',   border: 'border-blue-200',   badge: 'bg-blue-100 text-blue-800',   icon: '🔐' },
  'dp-llm-training':         { bg: 'bg-violet-50', border: 'border-violet-200', badge: 'bg-violet-100 text-violet-800', icon: '🛡️' },
  'llm-leakage-assessment':  { bg: 'bg-amber-50',  border: 'border-amber-200',  badge: 'bg-amber-100 text-amber-800',  icon: '🔍' },
  'governance-templates':    { bg: 'bg-green-50',  border: 'border-green-200',  badge: 'bg-green-100 text-green-800',  icon: '📋' },
};
const DEFAULT_PALETTE = { bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-100 text-slate-700', icon: '📦' };

const STATUS_LABEL = { prototype: 'Prototype', template: 'Template', assessment: 'Assessment', stable: 'Stable' };

function esc(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function pct(passed, total) {
  return total === 0 ? 0 : Math.round((passed / total) * 100);
}

function leakageClasses(rate) {
  if (rate >= 80) return 'bg-green-50 border-green-200 text-green-900';
  if (rate >= 50) return 'bg-amber-50 border-amber-200 text-amber-900';
  return 'bg-red-50 border-red-200 text-red-900';
}

// ─── Module Grid ───────────────────────────────────────────────────────────────
function renderModules(modules) {
  const grid = document.getElementById('module-grid');
  if (!grid) return;
  grid.innerHTML = modules.map(m => {
    const p = MODULE_PALETTE[m.slug] || DEFAULT_PALETTE;
    const label = STATUS_LABEL[m.status] || m.status;
    return `
      <a href="${esc(m.folder_url)}" target="_blank" rel="noopener noreferrer"
         class="block rounded-xl border ${p.border} ${p.bg} p-5
                hover:shadow-lg hover:-translate-y-0.5 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-400">
        <div class="flex items-start justify-between gap-2 mb-2">
          <div class="flex items-center gap-2">
            <span class="text-xl" role="img" aria-hidden="true">${p.icon}</span>
            <h3 class="font-semibold text-slate-800 leading-tight">${esc(m.name)}</h3>
          </div>
          <span class="shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${p.badge}">${esc(label)}</span>
        </div>
        <p class="text-sm text-slate-600 leading-relaxed">${esc(m.purpose)}</p>
        <div class="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
          <span title="Lines of code">📄 ${m.lines_of_code.toLocaleString()} lines</span>
          <span title="Automated tests">🧪 ${m.test_count} tests</span>
          <span title="Last updated">🕒 ${esc(m.last_updated)}</span>
        </div>
        <span class="mt-3 inline-block text-xs font-medium text-blue-600">View on GitHub →</span>
      </a>`;
  }).join('');
}

// ─── NIST Table ────────────────────────────────────────────────────────────────
let _nistData   = [];
let _nistSortBy = null;
let _nistAsc    = true;

const NIST_COLS = [
  { key: 'pattern',     label: 'Pattern'       },
  { key: 'module',      label: 'Module'        },
  { key: 'nist_ai_rmf', label: 'NIST AI RMF'  },
  { key: 'nist_pf',     label: 'NIST PF'       },
  { key: 'nist_csf_2',  label: 'NIST CSF 2.0' },
];

function renderNist(data) {
  const table = document.getElementById('nist-table');
  if (!table) return;

  const sorted = [...data].sort((a, b) => {
    if (!_nistSortBy) return 0;
    const va = (a[_nistSortBy] || '').toLowerCase();
    const vb = (b[_nistSortBy] || '').toLowerCase();
    return _nistAsc ? va.localeCompare(vb) : vb.localeCompare(va);
  });

  const thead = `<thead class="bg-slate-100 text-xs text-slate-600 uppercase tracking-wide sticky top-0">
    <tr>${NIST_COLS.map(c => {
      const arrow = _nistSortBy === c.key ? (_nistAsc ? ' sort-asc' : ' sort-desc') : '';
      return `<th class="sortable px-4 py-3 text-left whitespace-nowrap${arrow}" data-col="${c.key}">${esc(c.label)}</th>`;
    }).join('')}</tr>
  </thead>`;

  const tbody = `<tbody class="divide-y divide-slate-100">${sorted.slice(0, 15).map((row, i) =>
    `<tr class="${i % 2 === 0 ? 'bg-white' : 'bg-slate-50'} hover:bg-blue-50 transition-colors">
      ${NIST_COLS.map(c => `<td class="px-4 py-2.5 text-xs text-slate-700 font-mono">${esc(row[c.key] || '—')}</td>`).join('')}
    </tr>`
  ).join('')}</tbody>`;

  table.innerHTML = thead + tbody;

  table.querySelectorAll('th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      if (_nistSortBy === col) { _nistAsc = !_nistAsc; }
      else { _nistSortBy = col; _nistAsc = true; }
      renderNist(_nistData);
    });
  });
}

// ─── Leakage Grid ──────────────────────────────────────────────────────────────
function renderLeakage(data) {
  const grid = document.getElementById('leakage-grid');
  const meta = document.getElementById('leakage-meta');
  if (!grid) return;

  if (meta && data.run_timestamp) {
    const d = new Date(data.run_timestamp);
    const ds = d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    meta.innerHTML = `Last run: ${ds}. Model under test: <code class="bg-slate-100 px-1 rounded text-xs">${esc(data.model_under_test)}</code>. See <code class="bg-slate-100 px-1 rounded text-xs">llm-leakage-assessment/</code> for methodology.`;
  }

  grid.innerHTML = (data.categories || []).map(cat => {
    const rate = pct(cat.passed, cat.total);
    const cls  = leakageClasses(rate);
    return `
      <div class="rounded-xl border px-5 py-4 ${cls}">
        <div class="flex items-center justify-between mb-1">
          <span class="font-medium text-sm">${esc(cat.name)}</span>
          <span class="text-xl font-bold">${rate}%</span>
        </div>
        <p class="text-xs opacity-70">${cat.passed} / ${cat.total} test cases passed</p>
        <div class="leakage-bar-track mt-2 rounded-full" role="progressbar" aria-valuenow="${rate}" aria-valuemin="0" aria-valuemax="100">
          <div class="leakage-bar-fill rounded-full" style="width:${rate}%"></div>
        </div>
      </div>`;
  }).join('');
}

// ─── FHE Benchmark ─────────────────────────────────────────────────────────────
function renderBenchmark(data) {
  const container = document.getElementById('benchmark-table');
  if (!container) return;

  const rows   = data.rows || [];
  const maxMs  = Math.max(...rows.map(r => r.ciphertext_ms), 1);

  const trows = rows.map(row => {
    const cPct = Math.max(Math.round((row.cleartext_ms  / maxMs) * 100), 1);
    const xPct = Math.max(Math.round((row.ciphertext_ms / maxMs) * 100), 1);
    const overhead = `${Math.round(row.ciphertext_ms / row.cleartext_ms)}×`;
    return `
      <tr class="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
        <td class="px-5 py-3 text-sm font-mono text-slate-700 whitespace-nowrap">${row.vector_size.toLocaleString()}</td>
        <td class="px-5 py-3">
          <div class="flex items-center gap-2">
            <span class="bar-track"><span class="bar-fill bar-cleartext" style="width:${cPct}%"></span></span>
            <span class="text-xs text-slate-600 whitespace-nowrap">${row.cleartext_ms} ms</span>
          </div>
        </td>
        <td class="px-5 py-3">
          <div class="flex items-center gap-2">
            <span class="bar-track"><span class="bar-fill bar-ciphertext" style="width:${xPct}%"></span></span>
            <span class="text-xs text-slate-600 whitespace-nowrap">${row.ciphertext_ms} ms</span>
          </div>
        </td>
        <td class="px-5 py-3 text-xs font-semibold text-slate-500">${overhead}</td>
      </tr>`;
  }).join('');

  const ts = data.run_timestamp
    ? ` · Run: ${new Date(data.run_timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
    : '';

  container.innerHTML = `
    <div class="overflow-x-auto rounded-xl border border-slate-200 shadow-sm bg-white">
      <table class="min-w-full text-sm">
        <thead class="bg-slate-100 text-xs text-slate-600 uppercase tracking-wide">
          <tr>
            <th class="px-5 py-3 text-left whitespace-nowrap">Vector size</th>
            <th class="px-5 py-3 text-left">
              <span class="bar-track inline-block w-3 h-3 rounded-sm bar-cleartext mr-1 align-middle" style="width:12px;height:12px"></span>Cleartext
            </th>
            <th class="px-5 py-3 text-left">
              <span class="bar-track inline-block w-3 h-3 rounded-sm bar-ciphertext mr-1 align-middle" style="width:12px;height:12px"></span>Ciphertext (CKKS)
            </th>
            <th class="px-5 py-3 text-left">Overhead</th>
          </tr>
        </thead>
        <tbody>${trows}</tbody>
      </table>
      <p class="px-5 py-2 text-xs text-slate-400 border-t border-slate-100">
        Single-thread averages on consumer hardware${ts}${data.scheme ? ' · ' + esc(data.scheme) : ''}.
        See <code>fhe-feature-extraction/benchmarks/</code> for run script and methodology.
      </p>
    </div>`;
}

// ─── Recent Commits ────────────────────────────────────────────────────────────
async function renderCommits() {
  const feed = document.getElementById('commit-feed');
  if (!feed) return;

  try {
    const res = await fetch(
      `https://api.github.com/repos/${REPO}/commits?per_page=10`,
      { headers: { 'Accept': 'application/vnd.github.v3+json' } }
    );
    if (!res.ok) throw new Error(`GitHub API responded with ${res.status}`);
    const commits = await res.json();
    if (!Array.isArray(commits) || commits.length === 0) throw new Error('No commits returned');

    feed.innerHTML = commits.map(c => {
      const subject = esc(c.commit.message.split('\n')[0]);
      const sha     = c.sha.slice(0, 7);
      const date    = new Date(c.commit.author.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      const author  = esc(c.commit.author.name);
      return `
        <li class="flex items-start gap-3 py-2.5 border-b border-slate-100 last:border-0">
          <a href="${esc(c.html_url)}" target="_blank" rel="noopener noreferrer"
             class="font-mono text-xs text-slate-400 mt-0.5 shrink-0 hover:text-blue-600 transition-colors">${sha}</a>
          <div class="min-w-0 flex-1">
            <p class="text-slate-800 text-sm truncate" title="${subject}">${subject}</p>
            <p class="text-xs text-slate-400 mt-0.5">${author} · ${date}</p>
          </div>
        </li>`;
    }).join('');
  } catch {
    feed.innerHTML = `<li class="py-2">
      <a href="https://github.com/${REPO}/commits/master"
         class="text-sm text-blue-600 underline hover:text-blue-800" target="_blank" rel="noopener noreferrer">
        View full commit history on GitHub →
      </a>
    </li>`;
  }
}

// ─── Bootstrap ────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const [modules, nist, leakage, benchmark] = await Promise.allSettled([
    fetch(DATA_BASE + 'modules.json').then(r => { if (!r.ok) throw r; return r.json(); }),
    fetch(DATA_BASE + 'nist-mapping.json').then(r => { if (!r.ok) throw r; return r.json(); }),
    fetch(DATA_BASE + 'leakage-results.json').then(r => { if (!r.ok) throw r; return r.json(); }),
    fetch(DATA_BASE + 'benchmark.json').then(r => { if (!r.ok) throw r; return r.json(); }),
  ]);

  if (modules.status   === 'fulfilled') renderModules(modules.value);
  if (nist.status      === 'fulfilled') { _nistData = nist.value; renderNist(_nistData); }
  if (leakage.status   === 'fulfilled') renderLeakage(leakage.value);
  if (benchmark.status === 'fulfilled') renderBenchmark(benchmark.value);

  renderCommits();
});
