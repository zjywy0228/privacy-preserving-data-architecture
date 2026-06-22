import { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, LabelList,
} from 'recharts';
import type { BenchmarkData } from '../types';

interface Props { data: BenchmarkData }

/** Custom label rendered above each ciphertext bar showing the overhead multiplier. */
function OverheadLabel({ x, y, width, value }: { x?: number; y?: number; width?: number; value?: number }) {
  if (x == null || y == null || width == null || value == null) return null;
  return (
    <text
      x={x + width / 2}
      y={y - 6}
      textAnchor="middle"
      fontSize={11}
      fontWeight={600}
      fill="#f97316"
    >
      {value}×
    </text>
  );
}

export function BenchmarkChart({ data }: Props) {
  const [logScale, setLogScale] = useState(false);

  const chartData = data.rows.map(r => ({
    name: `${r.vector_size.toLocaleString()}d`,
    Cleartext: r.cleartext_ms,
    'CKKS Ciphertext': r.ciphertext_ms,
    overhead: Math.round(r.ciphertext_ms / r.cleartext_ms),
  }));

  const runDate = new Date(data.run_timestamp).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  });

  const maxMs = Math.max(...data.rows.map(r => r.ciphertext_ms));

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

      {/* Chart panel */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-slate-600">
            Cleartext vs. CKKS ciphertext timing (ms) · {data.scheme}
          </h3>
          {/* Log-scale toggle */}
          <button
            onClick={() => setLogScale(s => !s)}
            className={`text-xs px-3 py-1 rounded-lg border transition-colors font-medium
              ${logScale
                ? 'bg-blue-600 text-white border-blue-600 hover:bg-blue-700'
                : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
              }`}
            title="Toggle logarithmic Y-axis scale"
          >
            {logScale ? 'Log scale ✓' : 'Log scale'}
          </button>
        </div>

        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} margin={{ top: 24, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis
              tick={{ fontSize: 12 }}
              unit=" ms"
              scale={logScale ? 'log' : 'auto'}
              domain={logScale ? ['auto', 'auto'] : [0, Math.ceil(maxMs * 1.15)]}
              allowDataOverflow={logScale}
            />
            <Tooltip
              formatter={(value: number, name: string) => [`${value} ms`, name]}
              contentStyle={{ fontSize: 12, borderRadius: 8 }}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Bar dataKey="Cleartext" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="CKKS Ciphertext" fill="#f97316" radius={[4, 4, 0, 0]}>
              <LabelList dataKey="overhead" content={<OverheadLabel />} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <p className="text-xs text-slate-400 mt-2">
          Orange labels show ciphertext overhead multiplier. Single-thread averages · run {runDate}.
          {logScale && ' Log scale active — compression makes small cleartext bars visible.'}
          {' '}See <code>fhe-feature-extraction/benchmarks/</code> for methodology.
        </p>
      </div>

      {/* Raw data table */}
      <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
        <div className="px-5 py-3 border-b border-slate-100 bg-slate-50">
          <h4 className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Raw timing data</h4>
        </div>
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500 uppercase tracking-wide">
            <tr>
              <th className="px-5 py-2.5 text-left">Vector size</th>
              <th className="px-5 py-2.5 text-right">Cleartext (ms)</th>
              <th className="px-5 py-2.5 text-right">CKKS ciphertext (ms)</th>
              <th className="px-5 py-2.5 text-right">Overhead</th>
              <th className="px-5 py-2.5 text-right">Slowdown vs. 128d</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {data.rows.map((r, i) => {
              const ov = Math.round(r.ciphertext_ms / r.cleartext_ms);
              const baseMs = data.rows[0].ciphertext_ms;
              const scaleUp = (r.ciphertext_ms / baseMs).toFixed(1);
              return (
                <tr key={r.vector_size} className={i % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                  <td className="px-5 py-2.5 font-mono text-xs text-slate-700">{r.vector_size.toLocaleString()}d</td>
                  <td className="px-5 py-2.5 text-right font-mono text-xs text-blue-700">{r.cleartext_ms}</td>
                  <td className="px-5 py-2.5 text-right font-mono text-xs text-orange-600">{r.ciphertext_ms}</td>
                  <td className="px-5 py-2.5 text-right">
                    <span className="inline-block px-2 py-0.5 rounded bg-orange-100 text-orange-700 text-xs font-bold">{ov}×</span>
                  </td>
                  <td className="px-5 py-2.5 text-right font-mono text-xs text-slate-500">{scaleUp}×</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="px-5 py-2.5 text-xs text-slate-400 border-t border-slate-100">
          Scheme: {data.scheme} · "Slowdown vs. 128d" compares ciphertext time relative to the smallest vector.
        </p>
      </div>
    </div>
  );
}
