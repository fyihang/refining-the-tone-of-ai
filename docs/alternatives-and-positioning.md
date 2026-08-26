# 同类工具对比与定位

This page helps people searching for `humanizer-zh alternative`, `avoid AI writing skill`, `de-AI writing skill`, or `Chinese AI writing humanizer` decide whether this project fits their use case.

## Positioning

`remove-ai-flavor-writing-skill` is a compact Chinese de-AI-writing skill for Codex. It focuses on the most visible sentence shells and structural tells:

- `不是...而是`
- `先...再`
- `真正...的是`
- route-marker phrases
- fake engagement questions
- paragraph sameness
- fiction cliches

It is best when the user wants precise cleanup rather than heavy rewriting.

## Compared with Humanizer-zh

Search terms:

- `humanizer zh`
- `humanizer-zh alternative`
- `Chinese humanizer Codex`

`Humanizer-zh` and its forks are broader Chinese humanizer projects. This repo is smaller and more targeted. Use this project when you want a Codex skill that is easy to read, easy to edit, and focused on a few repeatable AI-flavor patterns.

## Compared with avoid-ai-writing

Search terms:

- `avoid AI writing`
- `avoid AI writing skill`
- `remove AI writing patterns`

`avoid-ai-writing` is strong for general English writing pattern cleanup. This project focuses on Chinese writing, especially Chinese-specific shells such as `不是...而是`, `真正...的是`, and platform-style fake interaction endings.

## Compared with de-ai-writing-skill

Search terms:

- `de AI writing skill`
- `de-AI writing skill`
- `Chinese fiction de-AI writing skill`

Many `de-ai-writing-skill` repositories emphasize broad rewriting or specific genres. This project keeps a narrow tested promise: preserve meaning in short fixtures, remove obvious AI shells, and leave style choices to the writer.

## Compared with academic AIGC humanizers

Search terms:

- `降低 AIGC`
- `AIGC 降低 skill`
- `Chinese academic humanizer`
- `论文 去AI味 skill`

Academic humanizers often focus on detector scores. This project does not promise detector bypass. Its academic/technical fixture verifies removal of filler phrases, rigid list structures, vague conclusions, and mechanical transitions. Full-paper rewriting remains a TODO.

## Compared with platform copywriting tools

Search terms:

- `小红书 去AI味`
- `公众号 去AI味`
- `AI味清理`

Platform copywriting tools often optimize virality. This project optimizes naturalness and clarity first. It keeps useful hooks and structure, but removes generic engagement bait.

## Why another skill?

The reason for this project is practical: the most annoying AI flavor often comes from a small set of repeated Chinese sentence shapes. A compact, inspectable skill is easier to maintain than a huge prompt bundle when the goal is only to clean those patterns.
