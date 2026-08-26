# Rhythm Pattern Test 2026-06-10

## Why

New user review identified subtler AI-flavored writing patterns:

- `这次只看`
- `X 很简单：`
- Repeated `X 很 X` judgment sentences
- Dense parallel clauses
- Text distributed too evenly across paragraphs and sentences

The goal is to treat these as rhythm and shape problems, not just keyword cleanup.

## Changes Tested

- Added skill guidance for narrowing frames, easy-answer colon shells, repeated `X 很 X` sentences, dense parallelism, and over-even paragraph weight.
- Added audit rules:
  - `narrowing_frame`
  - `easy_answer_colon`
  - `dense_hen_judgments`
  - `parallel_hen_clauses`
  - `over_even_paragraph_distribution`
- Added fixtures:
  - `tests/fixtures/over_neat_rhythm_before.md`
  - `tests/fixtures/over_neat_rhythm_after.md`

## Verification

```bash
python3 -m py_compile scripts/audit_ai_flavor.py scripts/search_rank_audit.py
python3 scripts/audit_ai_flavor.py tests/fixtures/*_after.md --fail-on-review
python3 scripts/audit_ai_flavor.py tests/fixtures/over_neat_rhythm_before.md
python3 scripts/audit_ai_flavor.py tests/fixtures/*_before.md
```

## Results

- Syntax check passed.
- All six `*_after.md` fixtures passed with no findings.
- `over_neat_rhythm_before.md` was flagged as `review`, score `12`, findings `6`.
- The new before fixture hit:
  - `很字判断句过密`
  - `过度收束开场`
  - `很简单冒号模板`
  - `很字排比过密`
  - `整齐编号逻辑`
  - `讲义腔/总结腔`

## Conclusion

The skill now covers the newly observed rhythm-level AI flavor without breaking existing cleaned fixtures. The audit script still remains a regression aid; editorial judgment is required for final text quality.
