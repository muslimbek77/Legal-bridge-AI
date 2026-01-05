#!/usr/bin/env python3
"""
Batch analyzer for contracts in a folder.
Processes PDF/DOC/DOCX/images under `shartnomalar/` and produces rich content evaluation
beyond section/spelling checks using compliance, risk scoring and RAG clause analysis.

Outputs:
- Per-file JSON in an output directory
- Aggregated CSV summary

Usage:
    python scripts/analyze_contracts.py --input shartnomalar --out reports --rag --spelling

Environment acceleration (optional):
- OCR_PAGES_MAX: limit OCR pages (e.g., 10)
- OCR_DPI: rasterization DPI (default 400)
- OCR_CHUNK_SIZE: render OCR in chunks to reduce memory
- OPENAI_API_KEY: if set, uses OpenAI for LLM; otherwise uses local LLM in LegalRAG
"""

import os
import sys
import json
import csv
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure project root is on sys.path for ai_engine imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import AI engine modules (no Django required)
from ai_engine.ocr import OCRProcessor
from ai_engine.parser import ContractParser, SectionType
from ai_engine.compliance import LegalComplianceEngine, ComplianceIssue, IssueSeverity
from ai_engine.risk_scoring import RiskScoringEngine
from ai_engine.rag import LegalRAG
from ai_engine.spelling import SpellingChecker

SUPPORTED_EXTS = {'.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif'}


def find_files(input_dir: Path) -> List[Path]:
    files: List[Path] = []
    for root, _, filenames in os.walk(input_dir):
        for name in filenames:
            p = Path(root) / name
            if p.suffix.lower() in SUPPORTED_EXTS:
                files.append(p)
    return sorted(files)


def analyze_file(
    file_path: Path,
    use_rag: bool = True,
    analyze_spelling: bool = False,
    llm_model: str = 'llama3.1'
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Analyze a single file end-to-end without Django models.
    Returns (result_dict, metrics_dict).
    """
    t0 = time.time()
    ocr = OCRProcessor()
    parser = ContractParser()
    compliance = LegalComplianceEngine()
    risk = RiskScoringEngine()
    spell = SpellingChecker()

    # Optional RAG
    rag = None
    if use_rag:
        try:
            import os as _os
            use_openai = bool(_os.environ.get('OPENAI_API_KEY'))
            rag = LegalRAG(llm_model=llm_model, use_openai=use_openai, openai_model='gpt-3.5-turbo')
            rag.initialize()
        except Exception as e:
            rag = None

    metrics = {
        't_ocr': 0.0,
        't_parse': 0.0,
        't_spelling': 0.0,
        't_compliance': 0.0,
        't_risk': 0.0,
        't_rag': 0.0,
    }

    # 1) OCR / text extraction
    t = time.time()
    text, ocr_confidence, is_scanned = ocr.extract_text_from_file(str(file_path))
    metrics['t_ocr'] = time.time() - t

    # 2) Parse
    t = time.time()
    sections, metadata = parser.parse(text)
    metrics['t_parse'] = time.time() - t

    # 3) Detect contract type (reuse pipeline logic)
    def _detect_contract_type(text: str) -> str:
        tl = text.lower()
        type_patterns = {
            'service': ['xizmat ko\'rsatish', 'оказание услуг', 'xizmatlar', 'услуги', 'сервис'],
            'supply': ['mol yetkazib berish', 'поставка', 'yetkazib berish', 'mahsulot yetkazish', 'товар'],
            'work': ['pudrat', 'подряд', 'qurilish', 'qurish', "ta'mirlash", 'строительство', 'ремонт', 'пудрат', 'қурилиш', 'курилиш', 'қуриш', 'иншоот', 'иншоат'],
            'labor': ['mehnat shartnomasi', 'трудовой договор', 'ish haqi', 'заработная плата', 'xodim'],
            'lease': ['ijara', 'аренда', 'ijaraga berish', 'ijaraga olish'],
            'procurement': ['davlat xaridi', 'государственная закупка', 'tender', 'тендер', 'konkurs'],
            'loan': ['qarz', 'займ', 'кредит', 'kredit', 'ssuda'],
        }
        scores = {k: 0 for k in type_patterns}
        for ctype, pats in type_patterns.items():
            for p in pats:
                if p in tl:
                    scores[ctype] += 1
        bt = max(scores.items(), key=lambda x: x[1])
        return bt[0] if bt[1] > 0 else 'other'

    contract_type = _detect_contract_type(text)

    # 4) Compliance
    t = time.time()
    issues = compliance.check_compliance(sections, metadata, contract_type)
    metrics['t_compliance'] = time.time() - t

    # 5) Spelling (optional)
    spelling_errors = []
    if analyze_spelling:
        t = time.time()
        spelling_errors = spell.check_text(text, metadata.language)
        metrics['t_spelling'] = time.time() - t
        from ai_engine.compliance import IssueType
        for sp in spelling_errors:
            issues.append(
                ComplianceIssue(
                    issue_type=IssueType.SPELLING,
                    severity=IssueSeverity.LOW,
                    title=f"Imloviy xato: {sp.word}",
                    description=sp.description,
                    section_reference=f"{sp.line_number}-qator",
                    text_excerpt=sp.context,
                    suggestion=f"To'g'ri yozilishi: {sp.suggestion}",
                    suggested_text=sp.suggestion,
                )
            )

    # 6) Risk scoring with optional LLM structured analyses
    t = time.time()
    clause_analyses = None
    if rag:
        try:
            key_sections = [SectionType.LIABILITY, SectionType.PRICE, SectionType.TERM, SectionType.FORCE_MAJEURE]
            clause_analyses = {}
            for section in sections:
                if section.section_type in key_sections:
                    structured = rag.analyze_clause_structured(section.content[:800], contract_type)
                    data = structured.get('analysis_structured', {})
                    compliance = data.get('compliance', 'noaniq')
                    severity = 'critical' if compliance == 'mos emas' else 'medium'
                    from ai_engine.risk_scoring import ClauseAnalysis
                    clause_analyses[section.section_type.value] = ClauseAnalysis(
                        clause_text=section.content[:500],
                        compliance=compliance,
                        risks=list(data.get('risks', []))[:6],
                        recommendations=list(data.get('recommendations', []))[:6],
                        severity=severity,
                        suggested_text=data.get('rewrite', ''),
                    )
        except Exception:
            clause_analyses = None
    risk_score = risk.calculate_score(sections, metadata, issues, contract_type, clause_analyses)
    metrics['t_risk'] = time.time() - t

    # 7) Enhanced RAG analysis (explanatory)
    rag_details = {}
    if rag:
        t = time.time()
        try:
            relevant_laws = rag.search_laws(text[:2000], contract_type, n_results=8)
            rag_details['relevant_laws'] = relevant_laws
            key_sections = [SectionType.SUBJECT, SectionType.LIABILITY, SectionType.PRICE]
            section_analyses = {}
            for section in sections:
                if section.section_type in key_sections:
                    analysis = rag.analyze_clause(section.content[:800], contract_type)
                    section_analyses[section.section_type.value] = analysis.get('analysis', '')
            rag_details['section_analyses'] = section_analyses
        except Exception as e:
            rag_details['error'] = str(e)
        metrics['t_rag'] = time.time() - t

    # Aggregate issue counts
    by_severity = {
        'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0
    }
    for i in issues:
        by_severity[i.severity.value] = by_severity.get(i.severity.value, 0) + 1

    result = {
        'file': str(file_path),
        'filename': file_path.name,
        'contract_type': contract_type,
        'language': metadata.language,
        'is_scanned': is_scanned,
        'ocr_confidence': ocr_confidence,
        'sections_count': len(sections),
        'issues': [
            {
                'type': i.issue_type.value,
                'severity': i.severity.value,
                'title': i.title,
                'description': i.description,
                'section': i.section_reference,
                'text_excerpt': i.text_excerpt,
                'suggestion': i.suggestion,
            }
            for i in issues
        ],
        'issue_counts': by_severity,
        'scores': {
            'overall': risk_score.overall_score,
            'level': risk_score.risk_level.value,
            'compliance': risk_score.compliance_score,
            'completeness': risk_score.completeness_score,
            'clarity': risk_score.clarity_score,
            'balance': risk_score.balance_score,
        },
        'recommendations': risk_score.recommendations,
        'rag': rag_details,
        'processing_time': round(time.time() - t0, 3),
    }

    return result, metrics


def write_outputs(results: List[Dict[str, Any]], metrics_list: List[Dict[str, Any]], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    # Per-file JSON
    for res in results:
        fname = Path(res['filename']).stem + '.json'
        with open(out_dir / fname, 'w', encoding='utf-8') as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
    # Aggregated CSV
    csv_path = out_dir / 'summary.csv'
    fieldnames = [
        'filename', 'contract_type', 'language', 'is_scanned', 'ocr_confidence',
        'sections_count', 'overall', 'risk_level', 'compliance', 'completeness', 'clarity', 'balance',
        'issues_critical', 'issues_high', 'issues_medium', 'issues_low', 'issues_info', 'processing_time',
        't_ocr', 't_parse', 't_spelling', 't_compliance', 't_risk', 't_rag'
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for res, m in zip(results, metrics_list):
            scores = res.get('scores', {})
            counts = res.get('issue_counts', {})
            row = {
                'filename': res.get('filename', ''),
                'contract_type': res.get('contract_type', ''),
                'language': res.get('language', ''),
                'is_scanned': res.get('is_scanned', False),
                'ocr_confidence': res.get('ocr_confidence', 0.0),
                'sections_count': res.get('sections_count', 0),
                'overall': scores.get('overall', 0),
                'risk_level': scores.get('level', ''),
                'compliance': scores.get('compliance', 0),
                'completeness': scores.get('completeness', 0),
                'clarity': scores.get('clarity', 0),
                'balance': scores.get('balance', 0),
                'issues_critical': counts.get('critical', 0),
                'issues_high': counts.get('high', 0),
                'issues_medium': counts.get('medium', 0),
                'issues_low': counts.get('low', 0),
                'issues_info': counts.get('info', 0),
                'processing_time': res.get('processing_time', 0.0),
                't_ocr': round(m.get('t_ocr', 0.0), 3),
                't_parse': round(m.get('t_parse', 0.0), 3),
                't_spelling': round(m.get('t_spelling', 0.0), 3),
                't_compliance': round(m.get('t_compliance', 0.0), 3),
                't_risk': round(m.get('t_risk', 0.0), 3),
                't_rag': round(m.get('t_rag', 0.0), 3),
            }
            w.writerow(row)


def main():
    ap = argparse.ArgumentParser(description='Batch analyze contracts in a folder')
    ap.add_argument('--input', '-i', default='shartnomalar', help='Input folder path')
    ap.add_argument('--out', '-o', default='media/reports/batch', help='Output folder for results')
    ap.add_argument('--rag', action='store_true', help='Enable RAG/LLM clause analysis for stronger content evaluation')
    ap.add_argument('--spelling', action='store_true', help='Enable spelling checks')
    # OCR tuning flags (passed via env for ai_engine.ocr)
    ap.add_argument('--max-pages', type=int, default=0, help='Limit number of pages per PDF for OCR')
    ap.add_argument('--dpi', type=int, default=0, help='OCR rasterization DPI')
    # Processing limit
    ap.add_argument('--limit', type=int, default=0, help='Analyze only first N files')
    args = ap.parse_args()

    input_dir = Path(args.input).resolve()
    out_dir = Path(args.out).resolve()

    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        sys.exit(1)

    files = find_files(input_dir)
    if args.limit and args.limit > 0:
        files = files[:args.limit]
    if not files:
        print(f"❌ No supported files found in: {input_dir}")
        sys.exit(1)

    # Set OCR env knobs if provided
    if args.max_pages and args.max_pages > 0:
        os.environ['OCR_PAGES_MAX'] = str(args.max_pages)
    if args.dpi and args.dpi > 0:
        os.environ['OCR_DPI'] = str(args.dpi)

    print(f"Found {len(files)} files. Starting analysis...\n")

    results: List[Dict[str, Any]] = []
    metrics_list: List[Dict[str, Any]] = []

    for idx, fp in enumerate(files, 1):
        print(f"[{idx}/{len(files)}] Analyzing: {fp.name}")
        try:
            res, met = analyze_file(fp, use_rag=args.rag, analyze_spelling=args.spelling)
            results.append(res)
            metrics_list.append(met)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Write minimal error JSON for traceability
            results.append({'filename': fp.name, 'file': str(fp), 'error': str(e)})
            metrics_list.append({'t_ocr': 0, 't_parse': 0, 't_spelling': 0, 't_compliance': 0, 't_risk': 0, 't_rag': 0})

    write_outputs(results, metrics_list, out_dir)

    print(f"\n✓ Done. Results:\n  - JSON files in: {out_dir}\n  - Summary: {out_dir / 'summary.csv'}")


if __name__ == '__main__':
    main()
