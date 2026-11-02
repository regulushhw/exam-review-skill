# 图片型 PDF 的视觉分析

## 适用场景

- PPT 转成的 PDF（课程课件最常见）
- 扫描件 PDF
- pdfplumber 提取质量差（< 500 字符或大量乱码）

## PDF 处理决策树

```
PDF 来源？
├── PPT 导出 → 直接视觉分析（不必试 pdfplumber）
├── 扫描件   → 直接视觉分析 / OCR
└── 未知来源 → pdfplumber 试提取
                    ├── ≥ 2000 字符/章 → 质量可用，直接提取全文
                    └── < 500 字符    → 切换视觉分析
```

提取脚本自带字符数检查，低于 500 字符的 PDF 自动标出，立刻换方法，不要用领域知识把缺口补上。

## 完整流程

### Step 1：安装 PyMuPDF

```bash
pip install pymupdf
```

包名是 `pymupdf`，导入时用 `import fitz`。优先用 PyMuPDF，比 pdf2image 更轻量。

### Step 2：PDF 转图片

150 dpi 够用，清晰度和速度比较均衡。

```python
import fitz
doc = fitz.open("文件.pdf")
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    pix.save(f"pdf_images/文件/page_{i+1:03d}.png")
```

图片先放在工作区的 `pdf_images/`。HTML 生成完立即删除这个目录。

### Step 3：视觉分析提取内容

- 方式 A（推荐）：逐批读取 PNG（每批 4–5 张），用当前环境读取图片的能力
- 方式 B：调用当前环境已有的视觉分析能力

每批 4–5 张，避免一次超出读取限制。

### Step 4：大 PDF 多 Agent 并行

每个 Agent 负责一个章节。指令里必须写明把结果写入文件，模板见 [`../templates/agent-task-template.md`](../templates/agent-task-template.md)。路径用工作区内的相对路径。示例：

```
分析完毕后，将结果写入文件：
notes/chX_notes.md
保存成功后回复「章节 X 笔记已保存」。
```

每人只写自己那一个文件。主流程再读这些文件，不要从各条回复里收集正文。

### Step 5：整理成结构化笔记

每章输出 Markdown，包含：各节标题、核心概念、重要数据、分类体系。笔记留在仓库里，方便以后改。

### Step 6：用真实内容生成 HTML

优先用视觉分析提取的内容，不要拿通用教科书知识代替。

## 效率技巧

- **预判**：PPT 转 PDF 直接走视觉分析，不必先试 pdfplumber
- **并行**：多章节同时分析
- **分批**：每批 4–5 张图片
- **PyMuPDF**：比 pdf2image 更轻量
- **150 dpi**：清晰度与速度的平衡
- **存档**：笔记存 Markdown，方便后续修改
- **落盘**：每条 Agent 指令都写明输出文件路径；每个 Agent 独立保存一个文件
