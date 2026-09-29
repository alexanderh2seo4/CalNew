"""Readable experiment registry and endpoint comparison reports."""
from pathlib import Path
from .io import read_json


def render_report(run):
    run=Path(run); r=read_json(run/'report.json')
    lines=[f"# CALNEW — {r['endpoint']}",'',f"**Status:** {r['status']}. Prospective validation: {r['prospective_validation']}.",'',
           f"Source: `{r['source']}`. {r['rows']} rows; {r['development_rows']} development, {r['calibration_rows']} calibration and {r['reserved_test_rows']} reserved test rows.",'',
           f"Selected by the declared one-standard-error rule: **{r['selected']}**. This is a development selection.",'',
           '| Candidate | Outer-fold mean score¹ | Standard error | Pooled development metric |', '|---|---:|---:|---:|']
    for name,values in r['summary'].items():
        lines.append(f"| {name} | {values['mean_score']:.4f} | {values['standard_error']:.4f} | {values['evaluation']['primary']:.4f} |")
    lines.extend(['','¹ Higher is better: macro average precision for descriptors; negative log-threshold MAE for regression. Pooled metrics weight rows rather than folds.','',
                  '## Interpretation','',*['- '+x for x in r['limitations']],'','## Unavailable candidates',''])
    lines.extend([f"- **{name}:** {v['reason']}" for name,v in r['failures'].items()] or ['None in this run.'])
    lines.extend(['','The machine-readable report includes per-label metrics, paired group-bootstrap comparisons, source caveats and configuration lineage.',
                  'Independent interval coverage must be measured on a subsequent evaluation set; calibration-set fit is not an independent coverage result.',''])
    output=run/'REPORT.md';output.write_text('\n'.join(lines));return output
