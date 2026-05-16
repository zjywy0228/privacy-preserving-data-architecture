import type { Module } from '../types';

const PALETTE: Record<string, { bg: string; border: string; badge: string; icon: string }> = {
  'fhe-feature-extraction':  { bg: 'bg-blue-50',   border: 'border-blue-200',   badge: 'bg-blue-100 text-blue-800',   icon: '🔐' },
  'dp-llm-training':         { bg: 'bg-violet-50', border: 'border-violet-200', badge: 'bg-violet-100 text-violet-800', icon: '🛡️' },
  'llm-leakage-assessment':  { bg: 'bg-amber-50',  border: 'border-amber-200',  badge: 'bg-amber-100 text-amber-800',  icon: '🔍' },
  'governance-templates':    { bg: 'bg-green-50',  border: 'border-green-200',  badge: 'bg-green-100 text-green-800',  icon: '📋' },
};
const DEFAULT_P = { bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-100 text-slate-700', icon: '📦' };

const STATUS_LABEL: Record<string, string> = {
  prototype: 'Prototype', template: 'Template', assessment: 'Assessment', stable: 'Stable',
};

interface Props { modules: Module[] }

export function ModuleGrid({ modules }: Props) {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      {modules.map(m => {
        const p = PALETTE[m.slug] ?? DEFAULT_P;
        return (
          <a
            key={m.slug}
            href={m.folder_url}
            target="_blank"
            rel="noopener noreferrer"
            className={`block rounded-xl border ${p.border} ${p.bg} p-5
              hover:shadow-lg hover:-translate-y-0.5 transition-all duration-150
              focus:outline-none focus:ring-2 focus:ring-blue-400`}
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xl" aria-hidden="true">{p.icon}</span>
                <h3 className="font-semibold text-slate-800 leading-tight">{m.name}</h3>
              </div>
              <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${p.badge}`}>
                {STATUS_LABEL[m.status] ?? m.status}
              </span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">{m.purpose}</p>
            <div className="mt-3 flex flex-wrap gap-4 text-xs text-slate-500">
              <span>📄 {m.lines_of_code.toLocaleString()} lines</span>
              <span>🧪 {m.test_count} tests</span>
              <span>🕒 {m.last_updated}</span>
            </div>
            <span className="mt-3 inline-block text-xs font-medium text-blue-600">View on GitHub →</span>
          </a>
        );
      })}
    </div>
  );
}
