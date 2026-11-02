---
name: exam-review
description: >-
  Generate one-stop exam review materials from course slides, PDFs, and past
  papers (课件、讲义、PDF、往年卷、大纲、笔记). Use when the user asks for 一站式复习资料,
  an exam review pack, a topic-frequency table (考点频次表), or chapter HTML
  covering 知识点、公式、陷阱、真题 and practice questions.
license: MIT
---

# 一站式复习资料生成法

本文件是给执行任务的 agent 的操作说明。方法主体是 v5.0；v5.1 把提取、转图、拼装和清理收成固定脚本。按下面的顺序做。细节以链接的文件为准，不要凭记忆省略或另造规则。

进入某一步时再读该步点名的文件：

- 判断 PDF 怎么提取、处理图片型课件：[`references/vision-workflow.md`](references/vision-workflow.md)
- 内容含 LaTeX：[`references/architecture.md`](references/architecture.md)
- 提取、写 HTML、管文件、派子任务：先看对应类别 [`references/pitfalls.md`](references/pitfalls.md)
- 交付前逐项勾选：[`references/checklist.md`](references/checklist.md)
- 交给用户填空的整段提示词：[`templates/prompt-template.md`](templates/prompt-template.md)
- 派子 agent：[`templates/agent-task-template.md`](templates/agent-task-template.md)
- 固定步骤调用现成脚本，不要另写：[`scripts/`](scripts/)（模板和 JSON 样例在 [`assets/`](assets/)）

## 核心原则

1. **先计划，后执行** — 计划获批准再动手
2. **文件越少越好** — 宁可内容长，不要文件多
3. **每步都检查** — 提取完立即查质量，别等最后
4. **样式先行** — 先确定 CSS 规范，再生成内容
5. **及时清理** — 临时文件用完就删
6. **数据与模板分离** — LaTeX 内容用 JSON 存，别硬编码进 Python
7. **局部修补优于全量重写** — 只改坏的部分
8. **图片型 PDF 预判** — PPT 转的 PDF 直接视觉分析
9. **提取质量即时验证** — 第一轮提取完立即查，差就换方法
10. **Agent 输出必须落盘** — 明确要求把结果写入指定文件，不要只写在回复里

## 用现成脚本（v5.1）

提取文字、PDF 转图片、拼 HTML、删除临时目录，都调用本技能目录 `scripts/` 里的脚本。不要为当前课程另写一套，也不要把脚本复制出来改。缺包时只安装依赖，不要换库重写：

```
pip install -r <本技能目录>/scripts/requirements.txt
```

包名是 `pymupdf`，导入才是 `fitz`。

```
python <本技能目录>/scripts/extract_and_check.py <pdf或目录> --out <工作区>/extracted
python <本技能目录>/scripts/pdf_to_images.py <pdf或目录> --out <工作区>/pdf_images
python <本技能目录>/scripts/assemble.py --content <工作区>/content.json --out <工作区>/ch1.html --only ch1
python <本技能目录>/scripts/assemble.py --patch <工作区>/ch1.html --chapter ch1 --practice <工作区>/practice_ch1.json
python <本技能目录>/scripts/cleanup.py --root <工作区>
```

- 未知来源的 PDF：先 `extract_and_check.py`。报告里 `likely_image_pdf` 为真（不足 500 字）就改走 `pdf_to_images.py`，不要再写 pdfplumber。
- PPT 转的 PDF、扫描件：跳过提取，直接 `pdf_to_images.py`（默认 150 dpi，输出 `pdf_images/<文件名>/page_001.png`）。
- 章节正文和公式写入 JSON。结构见 [`assets/schema.json`](assets/schema.json)，样例是 [`assets/content.example.json`](assets/content.example.json) 和 [`assets/practice_ch1.example.json`](assets/practice_ch1.example.json)。`assemble.py` 填 [`assets/template.html`](assets/template.html)。不要在 Python 里写 LaTeX。
- 计划里说好几个 HTML，就按章 `--only` 各跑一次，每次一个 `--out`。
- 只改练习题：改对应的 `practice_chN.json`，再 `--patch`。脚本用深度计数器换掉那个 `practice-box`，文件其余部分不动。
- HTML 生成完运行 `cleanup.py`。它删除工作区里的 `extracted/` 和 `pdf_images/`。临时脚本用 `--extra` 点名。不要删本技能目录。Markdown 笔记留着。

## 工作流

### 0. 先出计划，等批准

计划里写清：课程名、考试类型、当前水平、目标分数、资料清单、哪些 PDF 是图片型、最终 HTML 文件数量、有没有 LaTeX（有则走 JSON + 脚本 + 模板）。用户批准后再执行。需求没说清就先问清楚再动手。

### 1. 准备并一次读完资料

- 资料放在一个文件夹里。文件名只用字母、数字、下划线、短横线。中文引号等特殊字符会导致路径解析失败，先重命名。
- PPT 转成的 PDF 标成图片型，计划里直接排视觉分析。
- 旧版 `.doc` 先转成 `.docx`（WPS / LibreOffice）再读。PDF 用上面的脚本（pdfplumber 在 `extract_and_check.py` 里），doc/docx 用 pandoc。pandoc 不接受 PDF 输入。不要把视觉分析文档里的示例代码再写一遍。
- 一次性读完全部资料（真题、大纲、笔记、课件）。分批给会看不到全局；只给真题不给大纲会不知道范围。

### 2. 分析资料，做考点频次表

逐份读取，统计考点频次，按题型分类。输出表，列为：考点、出现次数、预估分值、难度。

用 `extract_and_check.py` 做字符数检查，立刻看 `quality_report.json`。选 pdfplumber 还是视觉分析，按 [`references/vision-workflow.md`](references/vision-workflow.md) 的决策树，不要在质量差的提取结果上继续耗。乱码放弃，按知识点重新出题，不要在乱码上改写。优先用资料里的真实内容；只有资料严重不足时才补充领域知识，不要用通用教科书知识代替老师课件。

#### 补充：把老师强调的内容计入频次（相对 v5.0 原文新增）

做上表时，另记老师强调过的考点，并据此上调该考点的预估分值。可用来加权的材料只有：

- 老师划重点的录音或课堂笔记
- 往年卷（本来就要计入出现次数；老师又点过同一考点时，再上调预估分值）
- 课件里被强调的部分（反复出现、单独成页，或标了重点 / 必考 / 考试范围）

没有这些材料就不要编造「老师强调」。不新增打分公式，仍用原来的四列；强调了什么写在该考点旁边，并体现在预估分值上。

### 3. 样式先行，再按章节生成

样式以 [`assets/template.html`](assets/template.html) 为准：提示框、代码框、表格的类名已经和正文一致，MathJax、`@media print`、viewport、答案隐藏也已写好。含 LaTeX 时，先读 [`references/architecture.md`](references/architecture.md) 和 [`references/pitfalls.md`](references/pitfalls.md) 的「LaTeX / 公式类」，把数据放进 JSON，用 `assemble.py` 拼装。不要另写拼装脚本，也不要把公式写进 Python 字符串。

写 HTML、练习题之前先读实战经验里的「HTML 生成类」和「内容质量类」。

每个章节包含：

- 核心知识点（大白话讲解）
- 必背公式 / 模板（表格 + 代码框）
- 陷阱警告
- 真题还原（题目 + 答案 + 解析）
- 巩固练习（每章 4–6 题；难度 ⭐～⭐⭐⭐⭐，从易到难；答案可隐藏）

输出约定（MathJax、打印、viewport、答案按钮已在模板里，生成后仍要核对）：

- HTML 文件数量在计划里事先说定
- 有 LaTeX 时加载 MathJax 3，配 `svg: { scale: 1.05 }`，CSS 加 `mjx-container { font-size: 105% }`，正文 `line-height: 2.2`；生成后立刻检查 `<head>` 里有配置和加载脚本
- 包含 `@media print` 和 viewport meta
- 答案默认 `display:none`，用脚本切换；按钮用 `onclick="this.parentElement.nextElementSibling..."`；每章有「显示全部 / 隐藏全部」
- 各章分别写入独立文件，再组装。写完后确认文件在磁盘上
- 多个 agent 时，每人只写入一个文件，主流程读这些文件组装。任务写法用 [`templates/agent-task-template.md`](templates/agent-task-template.md)
- 用视觉分析或提取得到的真实内容生成 HTML

### 4. 交付前过检查清单

按 [`references/checklist.md`](references/checklist.md) 逐项核对。把清单给用户，请其重点看需要人工核对的项。交付时写明请重点检查：公式清晰度、答案交互、打印效果。

每完成一个阶段汇报一次进度。承诺说保守一点，做完再超出。更新任务状态之前，先核对文件是否真的写好、该步是否真的做完。

HTML 生成完，运行 `cleanup.py` 删除工作区里的 `extracted/`、`pdf_images/`，并用 `--extra` 点名临时脚本。视觉分析写下的 Markdown 笔记留着，方便以后改。

### 5. 迭代

一次只改 1–2 处，改完确认再继续。改练习题时改 JSON，再用 `assemble.py --patch`（深度计数器只换 `practice-box`）。改别的句子时先读完整文件，用精确的原文片段替换坏掉的部分，不要整份重写，也不要为此新写 Python。改完把清单里对应项重新勾一遍。

## 派子任务

用 [`templates/agent-task-template.md`](templates/agent-task-template.md)。指令里写明输入文件和输出文件（工作区内的相对路径），并要求写入成功后再回复已保存。路径不要指向桌面、文档、Downloads；沙箱常拒绝写入这些用户目录。先写工作区，再按当前环境交付文件的方式交给用户。一个任务过大就拆开（大约超过 30 分钟的工作量就拆）。
