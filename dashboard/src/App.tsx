import { useState } from 'react';
import { useDashboardData } from './hooks/useData';
import { ModuleGrid } from './components/ModuleGrid';
import { NistExplorer } from './components/NistExplorer';
import { LeakageGrid } from './components/LeakageGrid';
import { BenchmarkChart } from './components/BenchmarkChart';

const NAV = ['Modules', 'NIST Mapping', 'Leakage Assessment', 'FHE Benchmark'] as const;
type Tab = (typeof NAV)[number];

function Skeleton({ h = 'h-40' }: { h?: string }) {
  return <div className={`${h} rounded-xl bg-slate-100 animate-pulse`} />;
}

export default function App() {
  const { data, error, loading } = useDashboardData();
  const [tab, setTab] = useState<Tab>('Modules');

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 antialiased">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="mx-auto max-w-6xl px-6 py-6">
          <h1 className="text-2xl font-semibold tracking-tight">
            Privacy-Preserving Data Architecture
          </h1>
          <p className="mt-1 text-slate-500 text-sm max-w-xl">
            Interactive research dashboard — module status, NIST control mappings,
            leakage assessment results, and FHE benchmark timings.
          </p>
          <p className="mt-1 text-xs text-slate-400">
            Maintained by Junyi Zhang (
            <a className="underline hover:text-slate-600"
               href="https://github.com/zjywy0228"
               target="_blank" rel="noopener noreferrer">@zjywy0228</a>) ·{' '}
            <a className="underline hover:text-slate-600"
               href="https://github.com/zjywy0228/privacy-preserving-data-architecture"
               target="_blank" rel="noopener noreferrer">GitHub</a>
          </p>
        </div>

        {/* Tab bar */}
        <div className="mx-auto max-w-6xl px-6">
          <nav className="flex gap-1 -mb-px" role="tablist">
            {NAV.map(t => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                onClick={() => setTab(t)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap
                  ${tab === t
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
                  }`}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-6xl px-6 py-10">
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-800">
            <strong>Error loading data:</strong> {error}
            <p className="mt-1 text-xs text-red-600">
              Make sure to run <code className="bg-red-100 px-1 rounded">node scripts/sync-data.cjs</code> first,
              or copy JSON files from <code>../docs/assets/data/</code> into <code>public/data/</code>.
            </p>
          </div>
        )}

        {/* Modules tab */}
        {tab === 'Modules' && (
          <div>
            <div className="mb-5">
              <h2 className="text-xl font-semibold">Prototype Modules</h2>
              <p className="mt-1 text-sm text-slate-500">
                Four reusable modules translating published FHE, DP, and LLM-leakage research into implementable patterns.
              </p>
            </div>
            {loading ? (
              <div className="grid gap-5 md:grid-cols-2">
                <Skeleton h="h-44" /><Skeleton h="h-44" /><Skeleton h="h-44" /><Skeleton h="h-44" />
              </div>
            ) : data ? (
              <ModuleGrid modules={data.modules} />
            ) : null}
          </div>
        )}

        {/* NIST Mapping tab */}
        {tab === 'NIST Mapping' && (
          <div>
            <div className="mb-5">
              <h2 className="text-xl font-semibold">NIST Control Mapping</h2>
              <p className="mt-1 text-sm text-slate-500">
                All rows from <code>docs/compliance/nist-control-mapping.csv</code>.
                Filter by keyword or module; click any column header to sort.
              </p>
            </div>
            {loading ? <Skeleton h="h-64" /> : data ? <NistExplorer rows={data.nist} /> : null}
          </div>
        )}

        {/* Leakage Assessment tab */}
        {tab === 'Leakage Assessment' && (
          <div>
            <div className="mb-5">
              <h2 className="text-xl font-semibold">LLM Leakage Assessment Results</h2>
              <p className="mt-1 text-sm text-slate-500">
                Seven-category assessment covering prompt injection, training-data extraction,
                membership inference, system-prompt extraction, log capture, embedding inversion,
                and indirect injection.
              </p>
            </div>
            {loading ? <Skeleton h="h-64" /> : data ? <LeakageGrid data={data.leakage} /> : null}
          </div>
        )}

        {/* FHE Benchmark tab */}
        {tab === 'FHE Benchmark' && (
          <div>
            <div className="mb-5">
              <h2 className="text-xl font-semibold">FHE Benchmark</h2>
              <p className="mt-1 text-sm text-slate-500">
                Cleartext vs. CKKS ciphertext feature-extraction timings at three vector sizes.
                The overhead is the cost of keeping raw medical data encrypted throughout computation.
              </p>
            </div>
            {loading ? <Skeleton h="h-72" /> : data ? <BenchmarkChart data={data.benchmark} /> : null}
          </div>
        )}
      </main>

      <footer className="border-t bg-white mt-16">
        <div className="mx-auto max-w-6xl px-6 py-5 flex flex-wrap justify-between gap-3 text-xs text-slate-400">
          <div className="flex gap-4">
            <a className="hover:text-slate-600 underline" href="https://github.com/zjywy0228/privacy-preserving-data-architecture" target="_blank" rel="noopener noreferrer">Source</a>
            <a className="hover:text-slate-600 underline" href="https://github.com/zjywy0228/privacy-preserving-data-architecture/blob/master/LICENSE" target="_blank" rel="noopener noreferrer">MIT License</a>
            <a className="hover:text-slate-600 underline" href="https://zjywy0228.github.io/privacy-preserving-data-architecture/" target="_blank" rel="noopener noreferrer">Static site</a>
          </div>
          <span>Built with React + Vite + Recharts + Tailwind</span>
        </div>
      </footer>
    </div>
  );
}
