import { useState, useMemo } from 'react';
import type { NistRow } from '../types';

interface Props { rows: NistRow[] }

type SortKey = keyof NistRow;

export function NistExplorer({ rows }: Props) {
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortKey>('pattern');
  const [sortAsc, setSortAsc] = useState(true);
  const [moduleFilter, setModuleFilter] = useState('');

  const modules = useMemo(() => [...new Set(rows.map(r => r.module))].sort(), [rows]);

  const filtered = useMemo(() => {
    const q = query.toLowerCase();
    return rows
      .filter(r =>
        (!moduleFilter || r.module === moduleFilter) &&
        (!q || Object.values(r).some(v => v.toLowerCase().includes(q)))
      )
      .sort((a, b) => {
        const va = a[sortBy].toLowerCase();
        const vb = b[sortBy].toLowerCase();
        return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
      });
  }, [rows, query, moduleFilter, sortBy, sortAsc]);

  const COLS: { key: SortKey; label: string }[] = [
    { key: 'pattern',     label: 'Pattern'      },
    { key: 'module',      label: 'Module'       },
    { key: 'nist_ai_rmf', label: 'NIST AI RMF' },
    { key: 'nist_pf',     label: 'NIST PF'      },
    { key: 'nist_csf_2',  label: 'NIST CSF 2.0' },
  ];

  function toggleSort(key: SortKey) {
    if (sortBy === key) setSortAsc(a => !a);
    else { setSortBy(key); setSortAsc(true); }
  }

  return (
    <div className="space-y-3">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="search"
          placeholder="Search controls…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm flex-1 min-w-48
                     focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
        />
        <select
          value={moduleFilter}
          onChange={e => setModuleFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm
                     focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <option value="">All modules</option>
          {modules.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <span className="text-xs text-slate-400 self-center">{filtered.length} / {rows.length} rows</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-100 text-xs text-slate-600 uppercase tracking-wide">
            <tr>
              {COLS.map(c => (
                <th
                  key={c.key}
                  onClick={() => toggleSort(c.key)}
                  className="px-4 py-3 text-left whitespace-nowrap cursor-pointer hover:bg-slate-200 select-none"
                >
                  {c.label}
                  {sortBy === c.key && <span className="ml-1 text-slate-400">{sortAsc ? '↑' : '↓'}</span>}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.length === 0 ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">No rows match the filter.</td></tr>
            ) : filtered.map((row, i) => (
              <tr key={i} className={`${i % 2 === 0 ? 'bg-white' : 'bg-slate-50'} hover:bg-blue-50 transition-colors`}>
                {COLS.map(c => (
                  <td key={c.key} className="px-4 py-2.5 text-xs text-slate-700 font-mono">{row[c.key] || '—'}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
