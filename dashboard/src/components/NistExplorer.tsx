import { useState, useMemo, useCallback } from 'react';
import type { NistRow } from '../types';

interface Props { rows: NistRow[] }

type SortKey = keyof NistRow;

/** Wrap every occurrence of `query` inside a cell value with a yellow <mark>. */
function HighlightCell({ text, query }: { text: string; query: string }) {
  if (!query || !text) return <>{text || '—'}</>;
  const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
  return (
    <>
      {parts.map((part, i) =>
        part.toLowerCase() === query.toLowerCase()
          ? <mark key={i} className="bg-yellow-200 text-yellow-900 rounded px-0.5">{part}</mark>
          : part
      )}
    </>
  );
}

/** Convert filtered rows to a CSV blob and trigger download. */
function exportCsv(rows: NistRow[], filename = 'nist-control-mapping.csv') {
  const headers = ['pattern', 'module', 'nist_ai_rmf', 'nist_pf', 'nist_csf_2'];
  const escape = (v: string) => `"${v.replace(/"/g, '""')}"`;
  const lines = [
    headers.join(','),
    ...rows.map(r => headers.map(h => escape(r[h as SortKey])).join(',')),
  ];
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function NistExplorer({ rows }: Props) {
  const [query, setQuery]           = useState('');
  const [sortBy, setSortBy]         = useState<SortKey>('pattern');
  const [sortAsc, setSortAsc]       = useState(true);
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

  const toggleSort = useCallback((key: SortKey) => {
    if (sortBy === key) setSortAsc(a => !a);
    else { setSortBy(key); setSortAsc(true); }
  }, [sortBy]);

  const clearFilters = useCallback(() => {
    setQuery('');
    setModuleFilter('');
  }, []);

  const hasActiveFilter = query !== '' || moduleFilter !== '';

  const COLS: { key: SortKey; label: string }[] = [
    { key: 'pattern',     label: 'Pattern'      },
    { key: 'module',      label: 'Module'       },
    { key: 'nist_ai_rmf', label: 'NIST AI RMF' },
    { key: 'nist_pf',     label: 'NIST PF'      },
    { key: 'nist_csf_2',  label: 'NIST CSF 2.0' },
  ];

  return (
    <div className="space-y-3">
      {/* Filters row */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-48">
          <input
            type="search"
            placeholder="Search controls…"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm pr-8
                       focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs"
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        <select
          value={moduleFilter}
          onChange={e => setModuleFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm
                     focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          <option value="">All modules</option>
          {modules.map(m => <option key={m} value={m}>{m}</option>)}
        </select>

        {/* Result count badge */}
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium
          ${hasActiveFilter ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'}`}>
          {filtered.length} / {rows.length} rows
        </span>

        {/* Clear all filters */}
        {hasActiveFilter && (
          <button
            onClick={clearFilters}
            className="text-xs text-slate-500 underline hover:text-slate-800"
          >
            Clear filters
          </button>
        )}

        {/* Export CSV */}
        <button
          onClick={() => exportCsv(filtered)}
          className="ml-auto text-xs px-3 py-1.5 rounded-lg border border-slate-300
                     bg-white hover:bg-slate-50 text-slate-600 hover:text-slate-900
                     transition-colors flex items-center gap-1.5"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export CSV
        </button>
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
                  {sortBy === c.key && (
                    <span className="ml-1 text-blue-400">{sortAsc ? '↑' : '↓'}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                  No rows match the filter.{' '}
                  {hasActiveFilter && (
                    <button onClick={clearFilters} className="underline text-blue-500">Clear filters</button>
                  )}
                </td>
              </tr>
            ) : filtered.map((row, i) => (
              <tr key={i} className={`${i % 2 === 0 ? 'bg-white' : 'bg-slate-50'} hover:bg-blue-50 transition-colors`}>
                {COLS.map(c => (
                  <td key={c.key} className="px-4 py-2.5 text-xs text-slate-700 font-mono">
                    <HighlightCell text={row[c.key]} query={query} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400">
        Showing <strong className="text-slate-600">{filtered.length}</strong> of{' '}
        <strong className="text-slate-600">{rows.length}</strong> control mappings.
        Matched text highlighted in yellow. Use "Export CSV" to download the filtered view.
      </p>
    </div>
  );
}
