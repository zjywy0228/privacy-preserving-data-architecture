"""Generate data-minimized Markdown or HTML leakage-assessment reports."""

from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _validated_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_rows = payload.get("results")
    if not isinstance(raw_rows, list):
        raise ValueError("Assessment payload must contain a 'results' list.")

    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            raise ValueError(f"Assessment result at index {index} is not an object.")
        case_id = raw.get("id")
        category = raw.get("category")
        passed = raw.get("passed")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"Assessment result at index {index} has no valid id.")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"Assessment result {case_id!r} has no valid category.")
        if not isinstance(passed, bool):
            raise ValueError(f"Assessment result {case_id!r} has no boolean passed value.")
        rows.append({"id": case_id, "category": category, "passed": passed})
    return rows


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, dict[str, int]] = defaultdict(lambda: {"passed": 0, "total": 0})
    for row in rows:
        counts = by_category[row["category"]]
        counts["total"] += 1
        if row["passed"]:
            counts["passed"] += 1

    total_passed = sum(1 for row in rows if row["passed"])
    return {
        "total": len(rows),
        "passed": total_passed,
        "failed": len(rows) - total_passed,
        "by_category": dict(sorted(by_category.items())),
    }


def _rate(passed: int, total: int) -> float:
    return (passed / total * 100.0) if total else 0.0


def _markdown_cell(value: Any) -> str:
    return str(value).replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def render_markdown(payload: dict[str, Any], title: str = "LLM Leakage Assessment Report") -> str:
    """Render a data-minimized Markdown report from an assessment payload."""
    rows = _validated_rows(payload)
    summary = _summary(rows)
    model = _markdown_cell(payload.get("model", "unknown"))
    timestamp = _markdown_cell(payload.get("run_timestamp", "unknown"))
    safe_title = str(title).replace("\r", " ").replace("\n", " ").strip()

    lines = [
        f"# {safe_title}",
        "",
        "> This report intentionally omits prompts, model responses, and leakage",
        "> signals. Retain the source JSON only in an access-controlled location.",
        "",
        "## Run metadata",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Model | {model} |",
        f"| Run timestamp | {timestamp} |",
        f"| Tests passed | {summary['passed']} / {summary['total']} |",
        f"| Overall pass rate | {_rate(summary['passed'], summary['total']):.1f}% |",
        "",
        "## Category summary",
        "",
        "| Category | Passed | Total | Pass rate |",
        "|---|---:|---:|---:|",
    ]

    for category, counts in summary["by_category"].items():
        lines.append(
            f"| {_markdown_cell(category)} | {counts['passed']} | {counts['total']} | "
            f"{_rate(counts['passed'], counts['total']):.1f}% |"
        )

    failed = [row for row in rows if not row["passed"]]
    lines.extend(["", "## Failed test identifiers", ""])
    if failed:
        for row in failed:
            lines.append(f"- `{_markdown_cell(row['id'])}` — {_markdown_cell(row['category'])}")
    else:
        lines.append("No configured leakage signal was detected in this run.")

    lines.extend(
        [
            "",
            "## Detailed results",
            "",
            "| Test ID | Category | Status |",
            "|---|---|---|",
        ]
    )
    for row in rows:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(
            f"| {_markdown_cell(row['id'])} | {_markdown_cell(row['category'])} | {status} |"
        )

    lines.extend(
        [
            "",
            "A passing automated run is version- and configuration-specific; it is not",
            "a certification that the evaluated system cannot leak data.",
            "",
        ]
    )
    return "\n".join(lines)


def render_html(payload: dict[str, Any], title: str = "LLM Leakage Assessment Report") -> str:
    """Render a standalone, data-minimized HTML report."""
    rows = _validated_rows(payload)
    summary = _summary(rows)
    safe_title = html.escape(str(title), quote=True)
    model = html.escape(str(payload.get("model", "unknown")), quote=True)
    timestamp = html.escape(str(payload.get("run_timestamp", "unknown")), quote=True)

    category_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(category)}</td>"
        f"<td>{counts['passed']}</td>"
        f"<td>{counts['total']}</td>"
        f"<td>{_rate(counts['passed'], counts['total']):.1f}%</td>"
        "</tr>"
        for category, counts in summary["by_category"].items()
    )
    result_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(row['id'])}</td>"
        f"<td>{html.escape(row['category'])}</td>"
        f'<td class="{"pass" if row["passed"] else "fail"}">'
        f"{'PASS' if row['passed'] else 'FAIL'}</td>"
        "</tr>"
        for row in rows
    )
    failed = [row for row in rows if not row["passed"]]
    if failed:
        failed_items = "".join(
            f"<li><code>{html.escape(row['id'])}</code> — {html.escape(row['category'])}</li>"
            for row in failed
        )
    else:
        failed_items = "<li>No configured leakage signal was detected.</li>"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{safe_title}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 960px; padding: 0 1rem; color: #172033; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border: 1px solid #cbd5e1; padding: .55rem; text-align: left; }}
    th {{ background: #f1f5f9; }}
    .pass {{ color: #166534; font-weight: 700; }}
    .fail {{ color: #b91c1c; font-weight: 700; }}
    .notice {{ border-left: 4px solid #0369a1; background: #f0f9ff; padding: .8rem 1rem; }}
  </style>
</head>
<body>
  <h1>{safe_title}</h1>
  <p class="notice">This report intentionally omits prompts, model responses, and leakage signals. Retain source JSON only in an access-controlled location.</p>
  <h2>Run metadata</h2>
  <dl>
    <dt>Model</dt><dd>{model}</dd>
    <dt>Run timestamp</dt><dd>{timestamp}</dd>
    <dt>Tests passed</dt><dd>{summary["passed"]} / {summary["total"]} ({_rate(summary["passed"], summary["total"]):.1f}%)</dd>
  </dl>
  <h2>Category summary</h2>
  <table>
    <thead><tr><th>Category</th><th>Passed</th><th>Total</th><th>Pass rate</th></tr></thead>
    <tbody>{category_rows}</tbody>
  </table>
  <h2>Failed test identifiers</h2>
  <ul>{failed_items}</ul>
  <h2>Detailed results</h2>
  <table>
    <thead><tr><th>Test ID</th><th>Category</th><th>Status</th></tr></thead>
    <tbody>{result_rows}</tbody>
  </table>
  <p>A passing automated run is version- and configuration-specific; it is not a certification that the evaluated system cannot leak data.</p>
</body>
</html>
"""


def write_report(input_path: Path, output_path: Path, title: str) -> None:
    """Load assessment JSON and write a report selected by output suffix."""
    with input_path.open(encoding="utf-8") as source:
        payload = json.load(source)
    if not isinstance(payload, dict):
        raise ValueError("Assessment JSON must contain a top-level object.")

    suffix = output_path.suffix.lower()
    if suffix == ".md":
        rendered = render_markdown(payload, title)
    elif suffix in {".htm", ".html"}:
        rendered = render_html(payload, title)
    else:
        raise ValueError("Output path must end in .md, .htm, or .html.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a data-minimized report from assessment-runner JSON."
    )
    parser.add_argument("input", type=Path, help="Assessment JSON input path")
    parser.add_argument("output", type=Path, help="Report output (.md or .html)")
    parser.add_argument("--title", default="LLM Leakage Assessment Report", help="Report title")
    args = parser.parse_args()
    write_report(args.input, args.output, args.title)


if __name__ == "__main__":
    main()
