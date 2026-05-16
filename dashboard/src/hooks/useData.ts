import { useState, useEffect } from 'react';
import type { DashboardData } from '../types';

const BASE = 'data/';

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(BASE + path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

export function useDashboardData() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchJson<DashboardData['modules']>('modules.json'),
      fetchJson<DashboardData['nist']>('nist-mapping.json'),
      fetchJson<DashboardData['leakage']>('leakage-results.json'),
      fetchJson<DashboardData['benchmark']>('benchmark.json'),
    ])
      .then(([modules, nist, leakage, benchmark]) => {
        if (!cancelled) {
          setData({ modules, nist, leakage, benchmark });
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error loading data');
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, []);

  return { data, error, loading };
}
