# 一站式复习资料生成法

从课件、PDF、往年试卷和笔记，做出一门课的一站式复习资料。做法来自多次实战，当前版本 **v5.1**。本仓库把这份方法收成可复用的 Agent Skill（Claude Code、Cursor、Codex 都读 `SKILL.md`）。提取、转图片、拼 HTML、清理临时文件都有现成脚本，agent 直接调用，不必每次重写。

Agent 会先出计划，等你批准再做：读完全部资料，列考点频次表，按章节生成 HTML（知识点、公式、陷阱、真题、练习），对照检查清单交付，再小步修改。

## 仓库里有什么

```
exam-review/
  SKILL.md                          给 agent 的操作说明
  scripts/
    extract_and_check.py            pdfplumber 提取并检查字数
    pdf_to_images.py                PyMuPDF 转 PNG（150 dpi）
    assemble.py                     JSON 填 HTML 模板
    cleanup.py                      删除 extracted/ 和 pdf_images/
    common.py                       控制台只打 ASCII，文件用 UTF-8
    requirements.txt                pymupdf、pdfplumber
  assets/
    template.html                   MathJax、打印、答案隐藏
    schema.json                     内容 JSON 的结构
    content.example.json            章节样例
    practice_ch1.example.json       练习题样例
  references/
    pitfalls.md                     实战经验
    vision-workflow.md              图片型 PDF 的视觉分析
    checklist.md                    交付前检查清单
    architecture.md                 JSON + 脚本 + 模板
  templates/
    prompt-template.md              填空用的提示词
    agent-task-template.md          派子任务用的指令模板
```

`SKILL.md` 里的 `name` 是 `exam-review`，必须和文件夹同名。

## 安装

把 `exam-review` 整个文件夹拷进所用工具的 skills 目录（拷文件夹，不是只拷 `SKILL.md`）。

| 工具 | 只在本仓库生效 | 本机所有项目 |
| --- | --- | --- |
| Cursor | `.cursor/skills/` 或 `.agents/skills/` | `~/.cursor/skills/` 或 `~/.agents/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.agents/skills/` |

Cursor 也会读 `.claude/skills/` 和 `.codex/skills/`。Codex 从当前目录向上找到仓库根的 `.agents/skills/`。换过目录后新开一轮会话，技能才会被重新加载。

## 用法

1. 装好技能后，直接说要做哪门课的复习资料，并附上课件、PDF、往年卷、大纲或笔记。
2. Agent 应先给出计划（资料清单、哪些 PDF 走视觉分析、HTML 要几个文件、有没有公式）。你点头之后它再生成。PDF 和 HTML 走 `exam-review/scripts/` 里的脚本，不另写代码。依赖：

```bash
pip install -r exam-review/scripts/requirements.txt
```

3. 也可以把 [`exam-review/templates/prompt-template.md`](exam-review/templates/prompt-template.md) 里的模板填好，和资料一起发出去。

有老师划重点的录音或笔记、往年卷、课件里标了重点的页，一并附上。技能会把这些强调计入考点频次表的预估分值。这份加权是转成技能时加的一小节，正文里标了「相对 v5.0 原文新增」。

## 版本历史

本仓库从 v5.0 起。2026-11-02 把当时的方法说明转成了 Skill；同一天的 v5.1 加上了固定脚本。

- **v5.1**（2026-11-02）：固定步骤收成可直接运行的脚本，避免每次重写代码和 LaTeX 转义。`scripts/pdf_to_images.py`（PyMuPDF，150 dpi，按 PDF 分文件夹）、`scripts/extract_and_check.py`（pdfplumber 提取，不足 500 字标为图片型并写报告）、`scripts/assemble.py`（读 content JSON 和 `practice_chN.json`，填模板；`--patch` 只换练习题区块）、`scripts/cleanup.py`（删除 `extracted/` 和 `pdf_images/`）。`assets/template.html` 写好 MathJax 3（`svg.scale` 1.05、`mjx-container` 105%、行高 2.2）、viewport、`@media print`，答案默认隐藏，单题切换，每章有显示全部 / 隐藏全部。附 `assets/schema.json` 和样例 JSON。控制台只打 ASCII，正文写 UTF-8 文件。
- **v5.0**（2026-06-22；2026-11-02 转为 Skill）
  - 转为 Skill：正文进 `exam-review/SKILL.md`，实战经验、视觉分析、检查清单、JSON 架构分到 `references/`，提示词和子任务模板分到 `templates/`。只在某一产品里存在的呈现命令、以及点名某一环境的读写工具，改成「写入文件 / 读取图片」的说法。
  - 转成 Skill 时增补一小节（文中已标明）：老师划重点的录音或笔记、往年卷、课件中的强调部分，用来给考点频次表加权。
  - 方法本身在 v5.0 的更新：新增 3 条坑（Agent 输出未落盘、多 Agent 结果收集混乱、沙箱路径限制）；新增「推荐做法」（PDF 处理决策树、Agent 任务设计模板、检查清单使用方式）；核心原则增至 10 条（第 10 条：Agent 输出必须落盘）；流程拆解改为引述实战经验，减少重复；Windows 控制台编码坑补充「Python 脚本禁用 emoji」；视觉分析要求指令里写明落盘；检查清单增加「各章节 HTML 已成功保存」。
- **v4.0**（2026-06-21）：新增视觉分析工作流专节。
- **v3.1**（2026-06-18）：补充 JS 按钮 bug 和 `\b` 退格符坑。
- **v3.0**（2025-06-18）：大物三上实战后的升级，LaTeX 转义坑 6 条。
- **v2.0**（2026-06-18）：重构生成法，补入一批踩坑记录。
- **v1.0**（日期不详）：初始版本。

## 贡献

新的坑追加到 `exam-review/references/pitfalls.md` 的对应类别里，保留「现象 / 解决」这种写法。同时在上面的版本历史加一条，并把版本号往上抬一档（例如 v5.1 → v5.2）。若这条坑会改变 agent 的步骤，同步改 `SKILL.md` 里点到它的那一句，以及 `SKILL.md` 开头若写了版本也一并改掉。只记这次真实遇到的现象和解决办法。

## 许可

[MIT](LICENSE)。
