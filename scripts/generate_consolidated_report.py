#!/usr/bin/env python3
import argparse
import json
import os
import glob
import csv
from collections import Counter, defaultdict
from statistics import mean


def load_json_files(folder):
    paths = sorted(glob.glob(os.path.join(folder, '*.json')))
    docs = []
    for p in paths:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Attach file name for reference
                data['__file_name'] = os.path.basename(p)
                docs.append(data)
        except Exception as e:
            print(f"[WARN] Failed to load {p}: {e}")
    return docs


def safe_mean(values):
    values = [v for v in values if isinstance(v, (int, float))]
    return round(mean(values), 2) if values else None


def extract_scores(doc):
    # Try multiple possible locations for scores
    scores = {}
    # Flat top-level fields
    for k in ['overall_score', 'compliance_score', 'completeness_score', 'clarity_score', 'balance_score',
              'ambiguity_score', 'specificity_score']:
        if k in doc and isinstance(doc[k], (int, float)):
            scores[k] = doc[k]

    # Nested result/risk/scores structures
    for parent in ['risk', 'result', 'analysis', 'scores']:
        nested = doc.get(parent, {})
        if isinstance(nested, dict):
            for k in ['overall_score', 'compliance_score', 'completeness_score', 'clarity_score', 'balance_score',
                      'ambiguity_score', 'specificity_score']:
                if k in nested and isinstance(nested[k], (int, float)):
                    scores[k] = nested[k]
            # Also check for keys without '_score' suffix in 'scores' dict
            if parent == 'scores':
                for short_k in ['overall', 'compliance', 'completeness', 'clarity', 'balance', 'ambiguity', 'specificity']:
                    long_k = f'{short_k}_score'
                    if short_k in nested and isinstance(nested[short_k], (int, float)) and long_k not in scores:
                        scores[long_k] = nested[short_k]
    return scores


def extract_meta(doc):
    contract_type = doc.get('contract_type') or doc.get('type') or doc.get('document_type')
    language = doc.get('language') or doc.get('lang')
    risk_level = doc.get('risk_level') or doc.get('risk', {}).get('level') or doc.get('scores', {}).get('level')
    parties = doc.get('parties') or doc.get('metadata', {}).get('parties')
    return {
        'contract_type': contract_type or 'unknown',
        'language': language or 'unknown',
        'risk_level': (risk_level or 'unknown').lower(),
        'parties': parties if isinstance(parties, dict) else None,
    }


def count_items(doc, key_candidates):
    for k in key_candidates:
        v = doc.get(k)
        if isinstance(v, list):
            return len(v)
        if isinstance(v, dict):
            return len(v)
    return 0


def extract_risky_clauses(doc):
    clauses = []
    # Common locations
    candidates = []
    for k in ['risky_clauses', 'issues', 'risks', 'risk_items']:
        v = doc.get(k)
        if isinstance(v, list):
            candidates.extend(v)
        elif isinstance(v, dict):
            for item in v.values():
                if isinstance(item, list):
                    candidates.extend(item)
                elif isinstance(item, dict):
                    candidates.append(item)

    # Normalize to text
    for item in candidates:
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            text = item.get('text') or item.get('clause') or item.get('title') or item.get('description')
            text = (text or '').strip()
        else:
            text = ''
        if text:
            clauses.append(text)
    return clauses


def aggregate(docs):
    agg = {
        'count': len(docs),
        'risk_level_counts': Counter(),
        'by_type': defaultdict(list),
        'scores': defaultdict(list),
        'ambiguity_scores': [],
        'specificity_scores': [],
        'risky_clause_freq': Counter(),
    }

    for d in docs:
        scores = extract_scores(d)
        meta = extract_meta(d)

        agg['risk_level_counts'][meta['risk_level']] += 1
        if meta['contract_type']:
            agg['by_type'][meta['contract_type']].append(scores)

        for k, v in scores.items():
            agg['scores'][k].append(v)
        if 'ambiguity_score' in scores:
            agg['ambiguity_scores'].append(scores['ambiguity_score'])
        if 'specificity_score' in scores:
            agg['specificity_scores'].append(scores['specificity_score'])

        clauses = extract_risky_clauses(d)
        for c in clauses:
            # Normalize clause text for frequency
            c_norm = ' '.join(c.split())[:200]
            agg['risky_clause_freq'][c_norm] += 1

    return agg


def write_csv(docs, out_csv):
    fieldnames = [
        'file', 'risk_level', 'contract_type', 'language',
        'overall_score', 'compliance_score', 'completeness_score', 'clarity_score', 'balance_score',
        'ambiguity_score', 'specificity_score', 'issues_count', 'recommendations_count'
    ]
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in docs:
            scores = extract_scores(d)
            meta = extract_meta(d)
            row = {
                'file': d.get('__file_name', ''),
                'risk_level': meta['risk_level'],
                'contract_type': meta['contract_type'],
                'language': meta['language'],
                'overall_score': scores.get('overall_score'),
                'compliance_score': scores.get('compliance_score'),
                'completeness_score': scores.get('completeness_score'),
                'clarity_score': scores.get('clarity_score'),
                'balance_score': scores.get('balance_score'),
                'ambiguity_score': scores.get('ambiguity_score'),
                'specificity_score': scores.get('specificity_score'),
                'issues_count': count_items(d, ['issues', 'risks', 'risky_clauses', 'risk_items']),
                'recommendations_count': count_items(d, ['recommendations', 'advice', 'suggestions']),
            }
            writer.writerow(row)
    print(f"[OK] Wrote CSV: {out_csv}")


def write_html(agg, docs, out_html):
    avg_overall = safe_mean(agg['scores'].get('overall_score', []))
    avg_ambiguity = safe_mean(agg['ambiguity_scores'])
    avg_specificity = safe_mean(agg['specificity_scores'])

    top_risky = agg['risky_clause_freq'].most_common(15)

    def esc(s):
        return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    html = []
    html.append('<!DOCTYPE html>')
    html.append('<html lang="en"><head><meta charset="utf-8">')
    html.append('<title>Consolidated Contract Analysis Report</title>')
    html.append('<style>body{font-family:system-ui,Arial,sans-serif;margin:24px;} h1,h2{margin:0 0 12px;} table{border-collapse:collapse;width:100%;} th,td{border:1px solid #ddd;padding:8px;font-size:14px;} th{background:#f6f6f6;text-align:left;} .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;} .card{border:1px solid #eee;padding:12px;border-radius:8px;background:#fafafa;} .muted{color:#666;}</style>')
    html.append('</head><body>')
    html.append('<h1>Consolidated Contract Analysis Report</h1>')

    # Summary cards
    html.append('<div class="grid">')
    html.append(f'<div class="card"><h2>Total Documents</h2><div>{agg["count"]}</div></div>')
    html.append(f'<div class="card"><h2>Avg Overall Score</h2><div>{avg_overall if avg_overall is not None else "N/A"}</div></div>')
    html.append(f'<div class="card"><h2>Ambiguity / Specificity</h2><div>{avg_ambiguity if avg_ambiguity is not None else "N/A"} / {avg_specificity if avg_specificity is not None else "N/A"}</div></div>')
    html.append('</div>')

    # Risk levels
    html.append('<h2>Risk Level Distribution</h2>')
    html.append('<table><thead><tr><th>Risk Level</th><th>Count</th></tr></thead><tbody>')
    for level, count in agg['risk_level_counts'].items():
        html.append(f'<tr><td>{esc(level)}</td><td>{count}</td></tr>')
    html.append('</tbody></table>')

    # By type averages
    html.append('<h2>Averages by Contract Type</h2>')
    html.append('<table><thead><tr><th>Type</th><th>Avg Overall</th><th>Avg Ambiguity</th><th>Avg Specificity</th></tr></thead><tbody>')
    for ctype, score_list in agg['by_type'].items():
        overall_vals = [s.get('overall_score') for s in score_list if s.get('overall_score') is not None]
        amb_vals = [s.get('ambiguity_score') for s in score_list if s.get('ambiguity_score') is not None]
        spec_vals = [s.get('specificity_score') for s in score_list if s.get('specificity_score') is not None]
        html.append('<tr>'
                    f'<td>{esc(ctype)}</td>'
                    f'<td>{safe_mean(overall_vals) if overall_vals else "N/A"}</td>'
                    f'<td>{safe_mean(amb_vals) if amb_vals else "N/A"}</td>'
                    f'<td>{safe_mean(spec_vals) if spec_vals else "N/A"}</td>'
                    '</tr>')
    html.append('</tbody></table>')

    # Top risky clauses
    html.append('<h2>Top Risky Clauses</h2>')
    if top_risky:
        html.append('<table><thead><tr><th>Clause (truncated)</th><th>Frequency</th></tr></thead><tbody>')
        for text, freq in top_risky:
            html.append(f'<tr><td class="muted">{esc(text)}</td><td>{freq}</td></tr>')
        html.append('</tbody></table>')
    else:
        html.append('<p class="muted">No risky clauses detected across documents.</p>')

    # Detailed table
    html.append('<h2>Per-Document Summary</h2>')
    html.append('<table><thead><tr>'
                '<th>File</th><th>Risk</th><th>Type</th><th>Lang</th>'
                '<th>Overall</th><th>Compliance</th><th>Completeness</th><th>Clarity</th><th>Balance</th>'
                '<th>Ambiguity</th><th>Specificity</th><th>Issues</th><th>Recommendations</th>'
                '</tr></thead><tbody>')
    for d in docs:
        scores = extract_scores(d)
        meta = extract_meta(d)
        html.append('<tr>'
                    f'<td>{esc(d.get("__file_name", ""))}</td>'
                    f'<td>{esc(meta.get("risk_level"))}</td>'
                    f'<td>{esc(meta.get("contract_type"))}</td>'
                    f'<td>{esc(meta.get("language"))}</td>'
                    f'<td>{scores.get("overall_score", "")}</td>'
                    f'<td>{scores.get("compliance_score", "")}</td>'
                    f'<td>{scores.get("completeness_score", "")}</td>'
                    f'<td>{scores.get("clarity_score", "")}</td>'
                    f'<td>{scores.get("balance_score", "")}</td>'
                    f'<td>{scores.get("ambiguity_score", "")}</td>'
                    f'<td>{scores.get("specificity_score", "")}</td>'
                    f'<td>{count_items(d, ["issues", "risks", "risky_clauses", "risk_items"] )}</td>'
                    f'<td>{count_items(d, ["recommendations", "advice", "suggestions"] )}</td>'
                    '</tr>')
    html.append('</tbody></table>')

    html.append('</body></html>')

    with open(out_html, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html))
    print(f"[OK] Wrote HTML: {out_html}")


def main():
    parser = argparse.ArgumentParser(description='Generate consolidated HTML/CSV report from batch JSON outputs')
    parser.add_argument('--input', required=True, help='Folder with per-file JSON outputs (e.g. media/reports/shartnomalar_batch)')
    parser.add_argument('--out-html', help='Output HTML path (default: <input>/consolidated.html)')
    parser.add_argument('--out-csv', help='Output CSV path (default: <input>/consolidated.csv)')
    args = parser.parse_args()

    in_dir = args.input
    out_html = args.out_html or os.path.join(in_dir, 'consolidated.html')
    out_csv = args.out_csv or os.path.join(in_dir, 'consolidated.csv')

    docs = load_json_files(in_dir)
    if not docs:
        print(f"[ERROR] No JSON files found in {in_dir}")
        return 2

    agg = aggregate(docs)
    write_csv(docs, out_csv)
    write_html(agg, docs, out_html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
