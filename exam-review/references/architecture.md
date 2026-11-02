# 推荐技术架构（JSON + 脚本 + 模板）

内容包含 LaTeX 公式时，用三层分离。JSON 里的 `$LaTeX$` 是纯文本，没有 Python 字符串转义问题。公式字符串不要写进 f-string，也不要写进普通字符串；见 [`pitfalls.md`](pitfalls.md) 的「LaTeX / 公式类」。

v5.1 起直接调用技能里的脚本，不要按下面的形状再写一个 `assemble.py`。

```
数据层  →  content.json + practice_ch1.json ~ practice_chN.json
             练习题：[{"q": "题目 $LaTeX$", "a": "答案 $LaTeX$"}, ...]
             样例：assets/content.example.json、assets/practice_ch1.example.json
             结构：assets/schema.json

脚本层  →  scripts/assemble.py
             读取 JSON，填 assets/template.html
             只改练习题时：--patch，精确定位替换

模板层  →  assets/template.html
             知识点 + 公式 + 陷阱 + 练习题占位区
             MathJax、打印、viewport、答案隐藏已写好
```

`--patch` 只替换那个 `practice-box`，不整份重写 HTML。

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

这段计数器已经写在 `scripts/assemble.py` 里。做复习资料时调用它，不要把这段复制成新脚本。调试信息用 UTF-8 写入文件，脚本里不用 emoji，也不要靠控制台 `print()` 看中文。技能自带的脚本已经按这个做了。
