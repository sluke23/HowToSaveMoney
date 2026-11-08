# 参与完善

感谢帮助这份指南保持准确、可用。你可以在仓库的 Issues 报错，或 Fork 后提交 Pull Request。

## 哪些内容适合贡献

- 修正错别字、表格串列、计算错误与失效链接。
- 更新政策门槛、金额、办理入口和有效期。
- 补充北京、上海、广州、深圳的公共服务与实用经验。

## 政策更新怎么写

请注明城市及区县、适用人群、政策生效日期、对应章节，优先附主管部门公告或办事指南的直接链接。机构首页只能作为入口，不能单独证明某个金额或条件。

经验性价格注明采样时间、地区、条件与样本；不要把个案写成通用结论。计算示例写清公式、假设、单位与是否包含税费。不要提交推广码、返佣链接、广告或他人的个人信息。

## 修改步骤

1. 修改 `book/` 或 `docs/` 中对应的 Markdown；需要时更新 `docs/待核实清单.md`。
2. 保留既有小节编号和 `<a id="s…">` 锚点，方便读者继续使用旧链接。
3. 重要内容变更写入 `CHANGELOG.md`；新增或移动篇目时同步 `README.md` 与 `docs/内容映射.json`。原 PDF 页码仅代表初始来源，不要为新增内容虚构来源页码。
4. 执行下面的构建与检查，并将更新后的 `index.html` 和 `skills/save-money-guide/references/` 一并提交。

```bash
python3 -m pip install -r tools/requirements.txt
python3 tools/build_site.py
python3 tools/build_skill.py
python3 tools/check.py
```

原始 PDF 已不随仓库提供，原文件名、校验值与页码保留在 `docs/内容映射.json` 中作为历史来源记录。后续更新维护 Markdown；需要阅读版 PDF 时运行 `python tools/export_book.py`。`dist/` 仅存放生成产物，不纳入 Git。

## 阅读格式相关修改

改动导出工具或阅读样式后，安装 `tools/requirements-export.txt`，运行 `python3 tools/export_book.py` 和 `python3 tools/check_exports.py`。PDF 改动还应渲染抽查封面、目录及表格页。生成的 `dist/` 无需提交，GitHub Actions 会自动构建阅读文件。详见 [tools/README.md](tools/README.md)。

## 许可

贡献到既有章节的内容遵循对应章节的许可。一般内容为 CC BY-NC-SA 4.0，特定工具内容为 CC BY 4.0；范围见 [LICENSE](LICENSE)。提交贡献前请确认你有权提供这些内容。
