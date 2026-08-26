# Search Audit 2026-06-06

## Context

This repository was created and pushed on 2026-06-06. GitHub repository search updated quickly; broader web search had not fully indexed the new repo during the first audit.

## GitHub Search Results Before Metadata Update

Command form:

```bash
gh search repos '<query>' --limit 20 --json fullName,url,description,stargazersCount,updatedAt
```

| Query | Result for `B1lli/remove-ai-flavor-writing-skill` |
|---|---|
| `remove ai flavor writing skill` | Rank 1 |
| `remove-ai-flavor-writing-skill` | Rank 1 |
| `remove AI flavor` | Rank 2 |
| `de-AI writing skill` | Not in top 20 |
| `去 AI 味 skill` | Not in top 20 |
| `去AI味 skill` | Not in top 20 |
| `Chinese AI writing humanizer` | Not in top 20 |
| `Codex remove AI writing skill` | Not in top 20 |
| `remove ai writing skill` | Not in top 20 |

## Web Search Results Before Metadata Update

Queries tested through web search:

- `remove-ai-flavor-writing-skill GitHub`
- `"remove-ai-flavor-writing-skill"`
- `"remove AI flavor" "writing skill" GitHub`
- `"去 AI 味" "remove-ai-flavor" GitHub`

Result: the new repo did not appear in the returned first-page results. Older and more established writing-humanizer skills ranked first, especially `blader/humanizer`, `conorbronsdon/avoid-ai-writing`, and several skill registry mirrors.

## Metadata Update

To improve precision and recall, repository metadata was updated with:

- Description containing `去AI味`, `AI味清理`, `Chinese remove AI flavor writing skill`, and `Humanize Chinese AI writing`.
- Topics: `remove-ai-flavor`, `ai-writing`, `de-ai-writing`, `writing-skill`, `chinese-writing`, `humanizer`, `codex-skill`, `ai-flavor`, `chinese-humanizer`, `ai-writing-humanizer`.
- README first-screen keywords covering Chinese and English search variants.

## Competitor Keyword Sweep

Additional GitHub repository searches showed which terms currently surface comparable de-AI-writing skills:

| Query | Top matching repos / keyword signal | Current result for this repo before competitor-term update |
|---|---|---|
| `去AI味 skill` | `Antony232/zh_de_ai_ify` uses description `去AI味skill`; `jiaw-Zh/anti-ai-qiang` says it merges two de-AI skills | Not in top 10 |
| `去 AI 味 skill` | Same as above | Not in top 10 |
| `Chinese AI writing humanizer` | `KyrieHuang/humanizer_zh`; `smilelida/chinese-ai-writing-humanizer` | Not in top 10 |
| `de AI writing skill` | `sgsss998/de-ai-writing-skill`; `Akimiya-z/auto-de-ai-writing-skill`; `deedeekong07-alt/fiction-humanizer-zh` | Not in top 10 |
| `humanizer zh` | `op7418/Humanizer-zh`; `redbaronyyyyy-eng/humanizer-zh-academic`; `ai-zixun/humanizer-zh` | Not in top 10 |
| `avoid AI writing skill` | `conorbronsdon/avoid-ai-writing` dominates related web results; GitHub repo search surfaced one localized fork | Not in top 10 |
| `remove AI writing patterns skill` | `stop-slop` appeared by exact description | Not in top 10 |
| `AI writing humanizer skill` | `Niks_Humanizer`, `tech-humanizer-skill`, `thekozugroup/humanizer` | Not in top 10 |
| `去AI味 写作` | `gongwen-deai-skill` | Not in top 10 |
| `AI味清理` | `B1lli/remove-ai-flavor-writing-skill` | Rank 1 |

Web search also showed strong external visibility for established terms:

- `avoid-ai-writing` ranks through the GitHub repo and its phrase `remove AI writing patterns`.
- `humanizer` and `humanizer-zh` rank through skill directories and GitHub mirrors.
- Chinese skill directories use phrases like `Chinese Humanizer`, `去除 AI 写作特征`, `AI writing traces`, and `Chinese AI-generated text`.

## Competitor-term Metadata Update

The repository was updated again to include exact and competitor-adjacent phrases:

- GitHub description now includes exact `去AI味 skill` and `Chinese AI writing humanizer`.
- Extra topics were added: `avoid-ai-writing`, `anti-ai-writing`, `ai-writing-patterns`, `anti-ai-slop`, `ai-humanizer`, `claude-code-skill`, `remove-ai-writing`, `chinese-ai-writing`.
- README first-screen keywords now include `remove AI writing patterns`, `avoid AI writing`, `anti AI writing`, `AI writing humanizer`, `humanizer-zh`, `降低AIGC`, and `Claude Code skill`.

## GitHub Search Results After Competitor-term Update

Immediate re-check:

| Query | Result for `B1lli/remove-ai-flavor-writing-skill` | Notes |
|---|---:|---|
| `去AI味 skill` | Rank 3 | Improved from not in top 10. Repos with exact Chinese descriptions still rank above it. |
| `Chinese AI writing humanizer` | Rank 2 | Improved from not in top 10. `KyrieHuang/humanizer_zh` remains rank 1 due exact Traditional Chinese humanizer wording. |
| `AI味清理` | Rank 1 | Strongest Chinese phrase for this repo. |
| `humanizer zh` | Not in top 20 | Dominated by `Humanizer-zh` forks and variants. |
| `de AI writing skill` | Not in top 20 | Dominated by exact `de-ai-writing-skill` repository names. |
| `avoid AI writing skill` | Not in top 20 | Dominated by exact `avoid-ai-writing` naming and localized forks. |
| `remove AI writing patterns skill` | Not in top 20 | Dominated by exact description matches such as `stop-slop`. |
| `AI writing humanizer skill` | Not in top 20 | Broad English term dominated by generic humanizer repositories. |

Interpretation:

- Exact phrase placement in the GitHub description helped immediately for `去AI味 skill` and `Chinese AI writing humanizer`.
- Name-level competition remains hard to beat for terms like `humanizer zh`, `de AI writing skill`, and `avoid AI writing skill` because competing repositories include those words directly in the repository name.
- Further gains likely require external backlinks, stars, releases, and index refresh rather than more keyword stuffing.

## Interpretation

The repo is already strong for exact name and exact `remove ai flavor writing skill` queries. It is weak for broad or highly competitive queries immediately after publication. That is expected for a newly indexed repository with very little external authority.

The best next steps are:

1. Keep the repository name as `remove-ai-flavor-writing-skill`.
2. Keep the internal skill name as `remove-ai-flavor`.
3. Add stars, backlinks, and real usage examples over time.
4. Re-run this audit after GitHub and web search indexes refresh.
