export interface Module {
  name: string;
  slug: string;
  purpose: string;
  lines_of_code: number;
  test_count: number;
  last_updated: string;
  folder_url: string;
  status: 'prototype' | 'template' | 'assessment' | 'stable';
}

export interface NistRow {
  pattern: string;
  module: string;
  nist_ai_rmf: string;
  nist_pf: string;
  nist_csf_2: string;
}

export interface LeakageCategory {
  name: string;
  passed: number;
  total: number;
}

export interface LeakageResults {
  run_timestamp: string;
  model_under_test: string;
  categories: LeakageCategory[];
}

export interface BenchmarkRow {
  vector_size: number;
  cleartext_ms: number;
  ciphertext_ms: number;
}

export interface BenchmarkData {
  run_timestamp: string;
  scheme: string;
  rows: BenchmarkRow[];
}

export interface DashboardData {
  modules: Module[];
  nist: NistRow[];
  leakage: LeakageResults;
  benchmark: BenchmarkData;
}
