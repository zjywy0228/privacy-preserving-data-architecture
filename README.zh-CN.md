# 隐私保护数据架构（Privacy-Preserving Data Architecture）

[![CI](https://github.com/zjywy0228/privacy-preserving-data-architecture/actions/workflows/ci.yml/badge.svg)](https://github.com/zjywy0228/privacy-preserving-data-architecture/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

> **English README:** [README.md](README.md)

面向需要在控制原始数据暴露、人工智能泄露风险和合规义务的同时分析敏感生物医学与科学数据的机构，提供可复用的架构模式、原型模块和评估框架。

由 Junyi Zhang（[@zjywy0228](https://github.com/zjywy0228)）维护。欢迎提交 Issue 和反馈。

**[→ 在线项目仪表板](https://zjywy0228.github.io/privacy-preserving-data-architecture/)** — 模块状态、NIST 控制映射、泄露评估结果、全同态加密基准测试及实时提交记录。

---

## 背景与动机

现代生物医学和科学研究日益依赖跨机构数据协作。然而，两类核心约束使这种协作面临困难：

1. **法规与伦理对原始数据传输的限制。** 患者记录、儿科临床数据、健康登记数据、基因组数据及同等科学数据集受 HIPAA（美国健康保险可移植性和责任法案）、GDPR 第 9 条、瑞典《患者数据法》（Patientdatalag）及相关框架约束，限制了原始记录跨系统和跨辖区的共享、复制或传输方式。

2. **人工智能时代的数据泄露风险。** 基于或接入敏感数据训练的人工智能（AI）与大语言模型（LLM）系统，可能通过记忆化、成员推断攻击（Membership Inference）、提示注入（Prompt Injection）、日志捕获及下游工具泄露等方式暴露数据——这些风险超出了传统访问控制架构的设计范围。

本仓库将关于**全同态加密（FHE）**、**差分隐私（DP）**和**大语言模型数据泄露评估**的研究转化为实用的架构模式和原型模块，供研究团队、医院 IT 部门和合规审查人员评估和采用。

---

## 研究基础

本工作基于以下已发表研究：

| 论文 | 期刊/会议 | DOI / 链接 |
|---|---|---|
| *基于全同态加密的医学图像隐私保护特征提取* | MDPI Applied Sciences（2024） | [doi:10.3390/app14062531](https://doi.org/10.3390/app14062531) |
| *基于差分隐私机制防止大语言模型训练数据泄露* | Springer Neural Processing Letters（2025） | [doi:10.1007/s11063-024-11604-9](https://doi.org/10.1007/s11063-024-11604-9) |
| *大语言模型数据泄露风险的评估方法与防护策略* | IEEE（2025） | 详见论文 |
| *医院感染疾病与老年癫痫风险* | Nature Aging（2025） | [doi:10.1038/s43587-024-00783-8](https://doi.org/10.1038/s43587-024-00783-8) |
| *腺样体扁桃体切除术后儿童轻度睡眠呼吸障碍的生长与睡眠结局* | Scientific Reports（2025） | 详见论文 |

Nature Aging 和 Scientific Reports 生物医学论文是本仓库的应用背景：两项研究均需要跨辖区对敏感患者记录进行受控、规范的访问，充分说明了为何可复用架构模式对于无法为每项新研究从头重新设计数据处理流程的团队至关重要。

---

## 仓库结构

```
privacy-preserving-data-architecture/
├── architectures/                # 参考架构（与机构无关，以论文为基础）
│   └── biomedical-reference-architecture.md
├── fhe-feature-extraction/       # 加密医学图像特征的 FHE 流水线
│   ├── fhe_pipeline.py
│   └── examples/
├── dp-llm-training/              # 大语言模型/机器学习训练的差分隐私包装器
│   ├── dp_trainer.py
│   ├── budget_accountant.py
│   └── examples/
├── llm-leakage-assessment/       # 大语言模型数据泄露威胁分类与评估清单
│   ├── assessment_runner.py
│   ├── ASSESSMENT-CHECKLIST.md
│   └── attacks/
├── governance-templates/         # IRB 修订模板、合成数据生成器
├── examples/                     # 端到端临床数据流 Jupyter Notebook
├── gallery/                      # 架构图 PNG 渲染
├── docs/
│   ├── adr/                      # 架构决策记录（ADR）
│   ├── compliance/               # NIST、HIPAA 控制映射
│   ├── glossary.md               # 隐私保护机器学习术语表
│   ├── schemas/                  # JSON Schema（差分隐私审计日志等）
│   └── papers/                   # BibTeX 引用
├── tools/                        # 仓库维护工具
│   └── validate_control_mapping.py
└── dashboard/                    # 在线仪表板（React/TypeScript）
```

---

## 快速开始

### 全同态加密特征提取

```bash
pip install tenseal numpy Pillow scikit-learn
python fhe-feature-extraction/examples/basic_usage.py
```

### 差分隐私训练

```bash
pip install opacus torch transformers
python dp-llm-training/examples/demo_training.py
```

### 大语言模型泄露评估

查阅 `llm-leakage-assessment/ASSESSMENT-CHECKLIST.md` 获取结构化工作流程。Python 运行器（`assessment_runner.py`）可自动执行提示注入和日志捕获测试用例。

### 端到端演示（Jupyter Notebook）

```bash
pip install -r examples/requirements-notebook.txt
jupyter notebook examples/end-to-end-clinical-data-flow.ipynb
```

该 Notebook 使用 512 条全合成临床记录，演示 FHE 特征提取 → 差分隐私训练 → 大语言模型泄露评估的完整流程。**不涉及任何真实患者健康信息（PHI）。**

---

## 联邦政策对齐

本工作兼容以下框架：

- [NIST 隐私框架（NIST Privacy Framework）](https://www.nist.gov/privacy-framework)
- [NIST 人工智能风险管理框架（AI RMF）](https://www.nist.gov/system/files/documents/2023/01/26/AI%20RMF%201.0.pdf)
- [NIST 对抗性机器学习报告（2025）](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-2e2025.pdf)
- [CISA 人工智能数据安全最佳实践](https://www.cisa.gov/resources-tools/resources/guidelines-secure-ai-system-development)
- [HHS OCR HIPAA 安全规则](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [国家隐私保护数据共享与分析促进战略（PPDSA）](https://www.whitehouse.gov/wp-content/uploads/2023/03/National-Strategy-to-Advance-Privacy-Preserving-Data-Sharing-and-Analytics.pdf)

---

## 引用

如果您在研究中使用了本仓库的内容，请引用上方相关论文。

## 许可证

MIT 许可证。详见 [LICENSE](LICENSE)。

## 贡献

参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何贡献代码、文档和架构模式。

---

## 人工智能辅助披露

本仓库的部分代码和文档由 Claude（Anthropic）辅助生成。所有生成的内容均经过作者审阅、测试和验证，并在相关提交消息中明确标注 AI 辅助内容（`Co-authored-by: Claude`）。详见 [docs/ai-assistance-policy.md](docs/ai-assistance-policy.md)。
