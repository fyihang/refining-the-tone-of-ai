# Search Rank Baseline 2026-06-08

Command:

```bash
python3 scripts/search_rank_audit.py --limit 20
```

## Strong Rankings To Preserve

| Query | Rank |
|---|---:|
| `remove-ai-flavor-writing-skill` | 1 |
| `remove ai flavor writing skill` | 1 |
| `remove AI flavor` | 1 |
| `AI味清理` | 1 |
| `Chinese AI writing humanizer` | 1 |
| `去AI味 skill` | 3 |
| `去 AI 味 skill` | 3 |

## Weak Queries To Improve

The target repo was not in the top 20 for these terms at the first baseline:

- `去AI味 写作`
- `中文去AI味`
- `中文去 AI 味`
- `降低AI感`
- `降低 AIGC`
- `AIGC 降低 skill`
- `AI写作痕迹去除`
- `AI 写作痕迹 去除`
- `AI generated text Chinese humanizer`
- `Chinese writing humanizer skill`
- `Chinese text humanizer skill`
- `Chinese AI text humanizer`
- `remove AI writing patterns skill`
- `AI writing humanizer skill`
- `avoid AI writing skill`
- `anti AI writing skill`
- `anti AI slop writing skill`
- `de AI writing skill`
- `de-AI writing skill`
- `humanizer zh`
- `humanizer-zh alternative`
- `Codex humanizer zh`
- `Codex remove AI writing skill`
- `Codex writing humanizer`
- `Codex 去AI味 skill`
- `Claude Code Chinese humanizer`
- `Claude Code 去AI味 skill`
- `OpenCode Chinese humanizer`
- `小红书 去AI味`
- `公众号 去AI味`
- `小说 去AI味 skill`
- `学术 写作 去AI味 skill`
- `论文 去AI味 skill`

## Interpretation

The repo has good GitHub search placement for exact and near-exact terms. It needs more content, backlinks, stars, and repository authority for use-case queries and competitor-adjacent terms.

## After Long-tail Landing Pages

After adding `docs/search-keywords.md`, `docs/alternatives-and-positioning.md`, stronger metadata, and the regression script:

| Query | Rank |
|---|---:|
| `中文去AI味` | 4 |
| `中文去 AI 味` | 3 |
| `humanizer zh` | 13 |
| `humanizer-zh alternative` | 1 |

The guarded strong terms still pass:

| Query | Required | Current |
|---|---:|---:|
| `remove-ai-flavor-writing-skill` | 1 | 1 |
| `remove ai flavor writing skill` | 1 | 1 |
| `remove AI flavor` | 1 | 1 |
| `AI味清理` | 1 | 1 |
| `Chinese AI writing humanizer` | 1 | 1 |
| `去AI味 skill` | 3 | 3 |
| `去 AI 味 skill` | 3 | 3 |
