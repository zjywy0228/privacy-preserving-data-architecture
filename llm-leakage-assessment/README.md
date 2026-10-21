# LLM leakage assessment

Run repeatable, substring-based leakage checks against a large language model
(LLM) adapter. The runner loads and validates every YAML case before calling the
model, then reports case outcomes and category totals. The default `MockModel`
returns a fixed refusal to exercise the assessment harness offline.

## Test-case schema

Each `.yaml` file contains one mapping. Required values are non-empty strings;
surrounding whitespace is stripped in the loaded copy. Identifiers must be unique
across the case directory, which must contain at least one case.

| Field | Meaning | Rule |
| --- | --- | --- |
| `id` | Case identifier | Two lowercase letters, an underscore, and three digits, such as `pi_001`; unique after trimming. |
| `category` | Threat category | One of the seven category names below. |
| `prompt` | Input sent to the configured model | Non-empty string. |
| `expected_behavior` | Description of the intended model behavior | Non-empty string; provided for review. |
| `leakage_signal` | Marker searched for in the model response | Non-empty string; matched case-insensitively. |

Allowed categories: `prompt_injection`, `indirect_injection`,
`training_data_extraction`, `system_prompt_extraction`, `log_capture_leakage`,
`embedding_inversion`, and `membership_inference`. A schema violation, duplicate
identifier, or empty directory raises `CaseValidationError` during runner
construction; file-specific errors name the offending file.

## Running

Install the parser with `pip install pyyaml`. Run the 15 shipped synthetic cases
with the offline model:

```bash
python llm-leakage-assessment/assessment_runner.py
```

To evaluate a configured model, put `llm-leakage-assessment/` on the Python import
path and pass an object implementing `generate(prompt: str) -> str`:

```python
from assessment_runner import AssessmentRunner

runner = AssessmentRunner(model=my_model)
runner.save_results("artifacts/leakage/results.json")
```

Create the output directory before saving. The JSON includes prompt snippets and
leakage signals, so retain it in an access-controlled location. Generate a report
that omits those fields:

```bash
python llm-leakage-assessment/report_generator.py results.json report.md
```

The example report command accepts any saved result path, including
`artifacts/leakage/results.json`. Pass counts describe the configured model and
case set at the recorded commit. See the [threat model](../docs/threat-models/llm-leakage-assessment.md)
and [assessment checklist](ASSESSMENT-CHECKLIST.md) for assessment boundaries and
National Institute of Standards and Technology AI Risk Management Framework
(NIST AI RMF) alignment.
