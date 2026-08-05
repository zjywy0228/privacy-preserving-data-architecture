# Anchor-Paper Metadata Verification

Last verified: 2026-08-04

The repository uses the publisher records below as the source of truth for its
five foundation papers. Each DOI resolves to the matching title and journal
record.

## Fully homomorphic encryption

- **Title:** Privacy-Preserving Feature Extraction for Medical Images Based on
  Fully Homomorphic Encryption
- **Authors:** Junyi Zhang; Xingpeng Xiao; Wenkun Ren; Yaomin Zhang
- **Journal:** *Journal of Advanced Computing Systems*, 4(2), 15–28 (2024)
- **DOI:** [10.69987/JACS.2024.40202](https://doi.org/10.69987/JACS.2024.40202)
- **Publisher record:**
  [SciPublication](https://scipublication.com/index.php/JACS/article/view/141)

## Differential privacy for LLM training

- **Title:** A Differential Privacy-Based Mechanism for Preventing Data Leakage
  in Large Language Model Training
- **Authors:** Xingpeng Xiao; Yaomin Zhang; Heyao Chen; Wenkun Ren; Junyi Zhang;
  Jian Xu
- **Journal:** *Academic Journal of Sociology and Management*, 3(2), 33–42
  (2025)
- **DOI:**
  [10.70393/616a736d.323732](https://doi.org/10.70393/616a736d.323732)
- **Publisher record:**
  [Southern United Academy of Sciences](https://www.suaspress.org/ojs/index.php/AJSM/article/view/v3n2a04)

## LLM leakage assessment

- **Title:** Assessment Methods and Protection Strategies for Data Leakage
  Risks in Large Language Models
- **Authors:** Xingpeng Xiao; Yaomin Zhang; Jian Xu; Wenkun Ren; Junyi Zhang
- **Journal:** *Journal of Industrial Engineering and Applied Science*, 3(2),
  6–15 (2025)
- **DOI:**
  [10.70393/6a69656173.323736](https://doi.org/10.70393/6a69656173.323736)
- **Publisher record:**
  [Southern United Academy of Sciences](https://www.suaspress.org/ojs/index.php/JIEAS/article/view/v3n2a02)

## Biomedical application context: population health

- **Title:** Hospital-treated infectious diseases and the risk of epilepsy in
  older age
- **Authors:** Qiyuan Zhuang; Yihan Hu; Dang Wei; Chenxi Qin; Kejia Hu; Junyi
  Zhang; Lida Chen; Zhelun Yang; Weimin Ye; Karin Wirdefeldt; Xiang Zou; Ying
  Mao; Sara Hägg; Fang Fang
- **Journal:** *Nature Aging*, 5, 2188–2196 (2025)
- **DOI:**
  [10.1038/s43587-025-01005-x](https://doi.org/10.1038/s43587-025-01005-x)
- **Contribution boundary:** The published statement credits J.Z. with
  writing–review and editing; it does not credit J.Z. with methodology or
  formal analysis.

## Biomedical application context: pediatric sleep

- **Title:** Growth and sleep outcomes after adenotonsillectomy in pediatric
  mild sleep-disordered breathing
- **Authors:** Wendan Gong; Kuanen Huang; Ioannis Psychogios; Shangjun Li; Lida
  Chen; Junyi Zhang; Fang Fang; Zhe Zhang; Yihan Hu
- **Journal citation:** *Scientific Reports*, 16, Article 688 (2026)
- **Online publication date:** 5 December 2025
- **DOI:**
  [10.1038/s41598-025-30271-3](https://doi.org/10.1038/s41598-025-30271-3)
- **Contribution boundary:** The published statement assigns full data access
  and statistical analyses to W.G. and I.P. The repository does not infer a
  different individual role.

The two biomedical papers are used as application-domain context. Repository
architecture descriptions do not infer individual author responsibilities
beyond the published contribution statements.

## Maintenance rule

When a citation changes, update `CITATION.md`, `CITATIONS-OF-THIS-REPO.md`,
`docs/papers/references.bib`, the two README files, and any module-specific
references in the same pull request. Run `pytest
tests/test_citation_metadata.py` before merging.
