import type { LeakageResults } from '../types';

function pct(passed: number, total: number) {
  return total === 0 ? 0 : Math.round((passed / total) * 100);
}

function colorClass(rate: number) {
  if (rate >= 80) return 'bg-green-50 border-green-200 text-green-900';
  if (rate >= 50) return 'bg-amber-50 border-amber-200 text-amber-900';
  return 'bg-red-50 border-red-200 text-red-900';
}

interface Props { data: LeakageResults }

export function LeakageGrid({ data }: Props) {
  const runDate = new Date(data.run_timestamp).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });

  const total = data.categories.reduce((s, c) => s + c.total, 0);
  const passed = data.categories.reduce((s, c) => s + c.passed, 0);
  const overall = pct(passed, total);

  return (
    <div className="space-y-4">
      {/* Overall banner */}
      <div className="rounded-xl border border-slate-200 bg-white px-5 py-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <span className="text-sm text-slate-500">Overall pass rate</span>
          <p className="text-xs text-slate-400 mt-0.5">
            Model: <code className="bg-slate-100 px-1 rounded">{data.model_under_test}</code> · Run: {runDate}
          </p>
        </div>
        <div className="text-right">
          <span className="text-3xl font-bold text-slate-800">{overall}%</span>
          <p className="text-xs text-slate-400">{passed} / {total} test cases passed</p>
        </div>
      </div>

      {/* Category grid */}
      <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {data.categories.map(cat => {
          const rate = pct(cat.passed, cat.total);
          const cls = colorClass(rate);
          return (
            <div key={cat.name} className={`rounded-xl border px-5 py-4 ${cls}`}>
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-sm">{cat.name}</span>
                <span className="text-xl font-bold">{rate}%</span>
              </div>
              <p className="text-xs opacity-70">{cat.passed} / {cat.total} passed</p>
              {/* Progress bar */}
              <div className="mt-2 h-1.5 rounded-full bg-current opacity-15 overflow-hidden">
                <div className="h-full rounded-full bg-current opacity-65" style={{ width: `${rate}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      <p className="text-xs text-slate-400">
        Color: <span className="inline-block px-2 py-0.5 rounded bg-green-100 text-green-800 mr-1">≥ 80% passed</span>
        <span className="inline-block px-2 py-0.5 rounded bg-amber-100 text-amber-800 mr-1">50–79%</span>
        <span className="inline-block px-2 py-0.5 rounded bg-red-100 text-red-800">&lt; 50%</span>
      </p>
    </div>
  );
}
