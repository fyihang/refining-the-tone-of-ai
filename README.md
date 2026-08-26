# remove-ai-flavor-writing-skill

一个中文去 AI 味写作 Skill。它不是把文字改得更花，而是清理那些一眼像模型生成的表达外壳：`不是...而是`、`先...再`、`真正...的是`、`这次只看`、`X 很简单：`、讲义腔路标词、冒号模板、段落同构，以及结尾突然抛给读者的假互动问题。

默认原则很窄：保留原意、事实、语气和文体，只去掉让读者意识到“这是模型在组织答案”的结构痕迹。内部 skill 名是 `remove-ai-flavor`。

## 快速使用

把本仓库复制到 Codex skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R remove-ai-flavor-writing-skill "${CODEX_HOME:-$HOME/.codex}/skills/remove-ai-flavor"
```

也可以直接从 GitHub 安装：

```bash
git clone https://github.com/B1lli/remove-ai-flavor-writing-skill.git /tmp/remove-ai-flavor-writing-skill
cp -R /tmp/remove-ai-flavor-writing-skill "${CODEX_HOME:-$HOME/.codex}/skills/remove-ai-flavor"
```

重启 Codex 后，用下面这类说法触发：

```text
用 $remove-ai-flavor 帮我把这段小红书文案去 AI 味。
把这段小说开头里的“不是...而是”“真正...的是”去掉。
这段复盘太像 AI 写的，保留意思改得更像人。
```

## 它会清理什么

- 二分对照壳：`不是 A，而是 B`、`不在于 A，而在于 B`、`与其说 A，不如说 B`
- 机械顺序壳：`先 A，再 B`、`第一步...第二步...`、`从 A 到 B`
- 本质拔高壳：`真正重要的是`、`真正决定...的是`、`本质上`、`核心在于`
- 助手路标词：`下面我们来`、`接下来我会`、`我们可以看到`、`希望这能帮到你`
- 总结讲义腔：`总的来说`、`值得注意的是`、`由此可见`、`不难看出`
- 收束开场和简单答案壳：`这次只看...`、`这个问题很简单：`
- 假互动结尾：`你觉得呢？`、`你有没有类似经历？`、`你现在卡在哪一步？`
- 段落同构：连续几段都是“观点句 + 解释 + 段尾总结”，或者排比太密、段落长度太均匀

## 已测试场景

- 小红书/社媒文案：清理机械步骤、抽象拔高、结尾假互动。
- 公众号/长文评论：清理讲义腔、二分对照壳、段落同构。
- 邮件/评论回复：清理助手路标词、虚假客气、莫名其妙的结尾提问。
- 中文小说正文：清理套话反应、抽象评论、无必要的 `先...再` 和 `不是...而是`。
- 学术/技术短文：清理填充短语、泛化结论、整齐编号逻辑、模糊权威。
- 过度整齐的短文：打散 `这次只看`、`很简单：`、`X 很 X` 和密集排比。

## 待办/未验证

- Claude Code / OpenCode 兼容性：规则是纯 Markdown，理论上可迁移，但尚未在这两个环境里完整安装测试。
- 长篇整稿批量处理：当前只做短样本和片段级 fixture，未承诺整本书或整篇论文自动改完。
- AI 检测器绕过：本项目只清理写作痕迹，不承诺降低任何检测器分数。
- 非中文文本：关键词覆盖里有英文搜索词，但核心规则和测试都面向中文写作。

## 本地检测脚本

仓库附带一个轻量回归脚本，用来检查典型 AI 味外壳是否还残留：

```bash
python3 scripts/audit_ai_flavor.py tests/fixtures/xhs_ai_flavor_after.md
python3 scripts/audit_ai_flavor.py tests/fixtures/novel_opening_after.md --fail-on-review
```

脚本只检查可枚举的表达模式，不替代人工审稿。通过脚本只能说明“常见模板壳基本清掉了”，不等于文章一定写得好。

## 自测结论

已用五类样本自测：

- 小红书工作流帖子：原稿命中 `不是...而是`、`先...再`、`真正...的是` 和结尾互动问题；改后脚本无阻断项。
- magic_novel 小说开头：原稿命中 `真正的问题不在...`、`这不是...而是...`、`不禁/缓缓说道` 等；改后保留剧情信息，改用行动、日志、告警声和对话推进。
- 公众号/长文评论：原稿命中 `聊一聊`、二分对照、整齐编号和结尾互动；改后脚本无阻断项。
- 邮件/评论回复：原稿命中助手路标词、假客气、`真正...的是` 和结尾提问；改后脚本无阻断项。
- 学术/技术短文：原稿命中理论起笔、模糊权威、泛化结论、整齐编号逻辑；改后脚本无阻断项。
- 过度整齐短文：原稿命中 `这次只看`、`很简单：`、`X 很 X` 和排比；改后保留意思但打散节奏。

用本仓库规则再对照几个已有通用去 AI 味 Skill 的重点项检查后，改后样本没有明显可继续清理的“硬壳”。剩余空间主要是作者风格选择，不再是通用 AI 味问题。

## 设计取舍

- 不做“同义词替换器”。只换词很容易把文字改成另一种 AI 味。
- 不强行口语化。学术、技术、小说和小红书的自然感不一样。
- 不默认加互动结尾。需要评论引导时再写，而且要具体。
- 不把外部参考 Skill 的文本搬进来。这个仓库只吸收方法论，规则和示例重新写。

## 相关资料

- [搜索关键词与用例索引](docs/search-keywords.md)：覆盖 `小红书去AI味`、`公众号去AI味`、`小说去AI味 skill`、`论文去AI味 skill`、`Codex 去AI味 skill` 等搜索词。
- [同类工具对比](docs/alternatives-and-positioning.md)：说明它和 `Humanizer-zh`、`avoid-ai-writing`、`de-ai-writing-skill`、`Chinese AI writing humanizer` 类项目的差异。

## 致谢

这个 Skill 参考并感谢以下项目的公开思路：

- [OUBIGFA/De-AI-Prompt-Enhancer-Writer-Booster-SKILL](https://github.com/OUBIGFA/De-AI-Prompt-Enhancer-Writer-Booster-SKILL)：保真改写、二分对照壳、路标词和协作口吻清理。
- [redbaronyyyyy-eng/humanizer-zh-academic](https://github.com/redbaronyyyyy-eng/humanizer-zh-academic)：学术写作中的硬约束、泛化结尾、段落套路和统计规律意识。
- [zengrong233/awesome-ai-research-writing-skill](https://github.com/zengrong233/awesome-ai-research-writing-skill)：按任务最小加载、把 prompt 库整理成可执行 Skill 的结构思路。
- [leenbj/novel-creator-skill](https://github.com/leenbj/novel-creator-skill)：小说场景中的两遍式去 AI 味、正文隔离和用行动替代抽象套话。
- [op7418/Humanizer-zh](https://github.com/op7418/Humanizer-zh)：中文 humanizer 方向的上游启发。

如果你的项目未在这里列出，但你觉得这个 Skill 受到了你的启发，欢迎提 issue，我会补上。

## 支持

如果你用上了这个 Skill，欢迎给本仓库点个 star：

https://github.com/B1lli/remove-ai-flavor-writing-skill

详细方法：

1. 打开上面的 GitHub 仓库链接。
2. 登录 GitHub。
3. 在页面右上角找到 `Star` 按钮。
4. 点击后按钮变成 `Starred`，就说明成功了。

GitHub CLI 用户可以直接运行：

```bash
gh repo star B1lli/remove-ai-flavor-writing-skill
```

## License

MIT License. See [LICENSE](LICENSE).
