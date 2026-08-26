# Scenario Test Report 2026-06-08

## Goal

Verify that advertised scenarios have corresponding fixtures and that untested claims are marked as TODO or unverified.

## Tested Scenarios

Command:

```bash
python3 scripts/audit_ai_flavor.py tests/fixtures/*_after.md --fail-on-review
python3 scripts/audit_ai_flavor.py tests/fixtures/*_before.md
```

| Scenario | Before fixture | After fixture | Evidence |
|---|---|---|---|
| Xiaohongshu / social post | `xhs_ai_flavor_before.md` | `xhs_ai_flavor_after.md` | After fixture passes with score 0 |
| Fiction opening | `novel_opening_before.md` | `novel_opening_after.md` | After fixture passes with score 0 |
| Academic / technical short prose | `academic_technical_before.md` | `academic_technical_after.md` | After fixture passes with score 0 |
| Public-account / long-form comment | `public_account_before.md` | `public_account_after.md` | After fixture passes with score 0 |
| Email / comment reply | `email_comment_before.md` | `email_comment_after.md` | After fixture passes with score 0 |

## Added Audit Coverage

The audit script now checks:

- binary contrast shells
- staged sequence shells
- essence claims
- assistant route markers
- lecture / summary markers
- abstract packaging words
- academic / technical filler patterns
- rigid enumeration
- fiction cliches
- repeated template colons
- ending engagement questions
- second-person overuse

## Explicit TODO / Unverified Claims

- Claude Code and OpenCode compatibility are not claimed as tested. The docs now say they are unverified TODOs.
- Full long-form batch processing is not claimed as tested.
- AI detector bypass is explicitly not promised.
- Non-Chinese rewriting is not claimed as supported.

## Conclusion

The README now separates tested scenarios from TODOs. Every scenario advertised as tested has a corresponding fixture and command-level evidence.
