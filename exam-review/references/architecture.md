# 推荐技术架构（JSON + 脚本 + 模板）

内容包含 LaTeX 公式时，用三层分离。JSON 里的 `$LaTeX$` 是纯文本，没有 Python 字符串转义问题。公式字符串不要写进 f-string，也不要写进普通字符串；见 [`pitfalls.md`](pitfalls.md) 的「LaTeX / 公式类」。

```
数据层  →  practice_ch1.json ~ practice_chN.json
             存：[{"q": "题目 $LaTeX$", "a": "答案 $LaTeX$"}, ...]

脚本层  →  assemble.py
             读取 JSON → 拼装 HTML → 精确定位替换

模板层  →  复习资料_template.html
             知识点 + 公式 + 陷阱 + 练习题占位区
```

脚本只替换模板里的练习题区块，不整份重写 HTML。

## 练习题区块定位

用 div 嵌套深度计数器定位匹配的闭合标签：

```python
# 用 div 嵌套深度计数器定位匹配的闭合标签
depth = 0
pos = html.find('<div class="practice-box">')
while pos < len(html):
    if html[pos:pos+4] == '<div':
        depth += 1
    elif html[pos:pos+6] == '</div>':
        depth -= 1
        if depth == 0:
            end = pos + 6
            break
    pos += 1
```

长脚本直接写成 `.py` 文件。调试信息用 UTF-8 写入文件，脚本里不用 emoji，也不要靠控制台 `print()` 看中文。
