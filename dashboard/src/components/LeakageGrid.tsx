import { useState } from 'react';
import type { LeakageResults, LeakageCategory } from '../types';

function pct(passed: number, total: number) {
  return total === 0 ? 0 : Math.round((passed / total) * 100);
}

function colorScheme(rate: number) {
  if (rate >= 80) return { card: 'bg-green-50 border-green-200', text: 'text-green-900', bar: 'bg-green-500', badge: 'bg-green-100 text-green-700' };
  if (rate >= 50) return { card: 'bg-amber-50 border-amber-200', text: 'text-amber-900', bar: 'bg-amber-500', badge: 'bg-amber-100 text-amber-700' };
  return { card: 'bg-red-50 border-red-200', text: 'text-red-900', bar: 'bg-red-500', badge: 'bg-red-100 text-red-700' };
}

interface CategoryCardProps {
  cat: LeakageCategory;
  expanded: boolean;
  onToggle: () => void;
}

function CategoryCard({ cat, expanded, onToggle }: CategoryCardProps) {
  const rate = pct(cat.passed, cat.total);
  const s = colorScheme(rate);
  const hasTests = cat.tests && cat.tests.length > 0;

  return (
    <div className={`rounded-xl border ${s.card} overflow-hidden transition-shadow ${expanded ? 'shadow-md' : ''}`}>
      {/* Header — always visible */}
      <button
        onClick={hasTests ? onToggle : undefined}
        className={`w-full text-left px-5 py-4 ${hasTests ? 'cursor-pointer hover:brightness-95' : 'cursor-default'}`}
        aria-expanded={expanded}
      >
        <div className={`flex items-center justify-between mb-1 ${s.text}`}>
          <span className="font-medium text-sm">{cat.name}</span>
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold">{rate}%</span>
            {hasTests && (
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${s.badge}`}>
                {expanded ? '▲' : '▼'}
              </span>
            )}
          </div>
        </div>

        <p className={`text-xs opacity-70 ${s.text}`}>{cat.passed} / {cat.total} passed</p>

        {/* Progress bar */}
        <div className="mt-2 h-1.5 rounded-full bg-slate-200 overflow-hidden">
          <div
            className={`h-full rounded-full ${s.bar} transition-all duration-500`}
            style={{ width: `${rate}%` }}
          />
        </div>
      </button>

      {/* Expandable test-case list */}
      {expanded && hasTests && (
        <div className="border-t border-current border-opacity-10 bg-white bg-opacity-60 px-5 py-3 space-y-2">
          {cat.tests!.map(t => (
            <div key={t.id} className="flex items-start gap-2.5 text-xs">
              <span
                className={`mt-0.5 shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-white text-[10px] font-bold
                  ${t.passed ? 'bg-green-500' : 'bg-red-500'}`}
                aria-label={t.passed ? 'passed' : 'failed'}
              >
                {t.passed ? '✓' : '✗'}
              </span>
              <div>
                <span className="font-mono text-slate-500 mr-1.5">{t.id}</span>
                <span className={t.passed ? 'text-slate-700' : 'text-red-700 font-medium'}>{t.description}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface Props { data: LeakageResults }

export function LeakageGrid({ data }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const runDate = new Date(data.run_timestamp).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });

  const total   = data.categories.reduce((s, c) => s + c.total, 0);
  const passed  = data.categories.reduce((s, c) => s + c.passed, 0);
  const overall = pct(passed, total);

  const failed = data.categories
    .flatMap(c => (c.tests ?? []).filter(t => !t.passed).map(t => ({ cat: c.name, ...t })));

  return (
    <div className="space-y-4">
      {/* Overall banner */}
      <div className="rounded-xl border border-slate-200 bg-white px-5 py-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <span className="text-sm text-slate-500">Overall pass rate</span>
          <p className="text-xs text-slate-400 mt-0.5">
            Model: <code className="bg-slate-100 px-1 rounded">{data.model_under_test}</code> · Run: {runDate}
          </p>
          <p className="text-xs text-slate-400 mt-0.5">
            Click any category card to see individual test cases.
          </p>
        </div>
        <div className="text-right">
          <span className="text-3xl font-bold text-slate-800">{overall}%</span>
          <p className="text-xs text-slate-400">{passed} / {total} test cases passed</p>
        </div>
      </div>

      {/* Category grid */}
      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {data.categories.map(cat => (
          <CategoryCard
            key={cat.name}
            cat={cat}
            expanded={expanded === cat.name}
            onToggle={() => setExpanded(prev => prev === cat.name ? null : cat.name)}
          />
        ))}
      </div>

      {/* Failed test summary */}
      {failed.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4">
          <h4 className="text-sm font-medium text-red-800 mb-2">
            {failed.length} test case{failed.length > 1 ? 's' : ''} failed — expand the category card for details
          </h4>
          <ul className="space-y-1">
            {failed.map(f => (
              <li key={f.id} className="text-xs text-red-700 flex gap-2">
                <span className="font-mono shrink-0">[{f.cat}] {f.id}</span>
                <span>{f.description}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-slate-400">
        Color: <span className="inline-block px-2 py-0.5 rounded bg-green-100 text-green-800 mr-1">≥ 80% passed</span>
        <span className="inline-block px-2 py-0.5 rounded bg-amber-100 text-amber-800 mr-1">50–79%</span>
        <span className="inline-block px-2 py-0.5 rounded bg-red-100 text-red-800">&lt; 50%</span>
      </p>
    </div>
  );
}
