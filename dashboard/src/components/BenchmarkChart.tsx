import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts';
import type { BenchmarkData } from '../types';

interface Props { data: BenchmarkData }

export function BenchmarkChart({ data }: Props) {
  const chartData = data.rows.map(r => ({
    name: `${r.vector_size.toLocaleString()}d`,
    Cleartext: r.cleartext_ms,
    'CKKS Ciphertext': r.ciphertext_ms,
    overhead: Math.round(r.ciphertext_ms / r.cleartext_ms),
  }));

  const runDate = new Date(data.run_timestamp).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        {data.rows.map(r => {
          const ov = Math.round(r.ciphertext_ms / r.cleartext_ms);
          return (
            <div key={r.vector_size} className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-center">
              <p className="text-xs text-slate-400 font-mono">{r.vector_size.toLocaleString()}d vector</p>
              <p className="text-2xl font-bold text-orange-500 mt-1">{ov}×</p>
              <p className="text-xs text-slate-500">ciphertext overhead</p>
              <p className="text-xs text-slate-400 mt-1">
                {r.cleartext_ms} ms → {r.ciphertext_ms} ms
              </p>
            </div>
          );
        })}
      </div>

      {/* Recharts bar chart */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="text-sm font-medium text-slate-600 mb-4">
          Cleartext vs. CKKS ciphertext timing (ms) · {data.scheme}
        </h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} unit=" ms" />
            <Tooltip
              formatter={(value: number, name: string) => [`${value} ms`, name]}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Cleartext" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="CKKS Ciphertext" fill="#f97316" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
        <p className="text-xs text-slate-400 mt-2">
          Single-thread averages · run {runDate}. See <code>fhe-feature-extraction/benchmarks/</code> for methodology.
        </p>
      </div>
    </div>
  );
}
