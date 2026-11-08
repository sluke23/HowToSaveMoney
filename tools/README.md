# 阅读工具与构建

所有导出以 `book/`、附录、待核实清单和版权文档为源，署名为 **毛毛&luke**，保留原有混合许可。格式组织参考 [HowToLiveBetter/tools](https://github.com/eternity4719/HowToLiveBetter/tree/main/tools)，具体实现针对本项目的分章和表格内容编写。

## 支持的阅读格式

| 格式 | 文件 | 适合场景 | 功能 |
| --- | --- | --- | --- |
| EPUB 3 | `dist/HowToSaveMoney.epub` | Apple Books、支持 EPUB 的手机 App 与电子阅读器 | 可重排版、章节与小节导航、NCX 目录、书内跳转、作者与语言元数据 |
| PDF | `dist/HowToSaveMoney.pdf` | 固定版面阅读、打印 | A4、嵌入中文字体、页码目录、章节书签、表格跨页重复表头、可点击链接 |
| 单文件 HTML | `dist/HowToSaveMoney.html` | 浏览器、完全离线分享 | 双击打开、全文搜索、内嵌正文与样式、书内跳转，无本地文件或 CDN 依赖 |
| UTF-8 TXT | `dist/HowToSaveMoney.txt` | 纯文本阅读器、辅助阅读及文本检索 | 保留正文、表格内容与原始外部网址；表格按制表符分列 |

导出文件是由当前 Markdown 重新生成的阅读版。原始 PDF 已不随仓库提供，也不参与构建与检查；导出版可因后续正文修订而与原文不同。EPUB 的实际字体、表格宽度和分页由阅读器决定；PDF 为固定版面。这里不承诺 Kindle 等专有格式的转换兼容性。

## 一次生成全部格式

需要 Python 3.9 或以上。推荐单独建立虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r tools/requirements-export.txt
python tools/export_book.py
python tools/check_exports.py
```

Windows PowerShell 可将环境激活命令换为 `.venv\Scripts\Activate.ps1`，其余命令用 `python` 执行。

产物写入仓库根目录的 `dist/`。`build-info.json` 记录作者、原文版本、UTC 构建时间、维护源哈希以及本次各产物的大小与 SHA-256。该构建时间不表示政策在该日重新核实过。

### PDF 中文字体

PDF 必须使用有简体中文字形的 TrueType 字体，会将使用到的字形嵌入文件。工具自动查找 macOS 的 Arial Unicode 或 Linux 的文泉驿正黑；不复制、分发本机字体原文件。版权说明中的原排版字体描述指原始 PDF；导出版实际字体记录在 `build-info.json`。

Ubuntu/Debian：

```bash
sudo apt-get install fonts-wqy-zenhei
```

其他环境可用相对路径指定允许嵌入的中文 `.ttf` 或 TrueType `.ttc`（使用第一个字体面）：

```bash
python tools/export_book.py --font fonts/chinese-font.ttf
```

也可设置 `SAVE_MONEY_PDF_FONT`。只有英文的字体、OpenType CFF 字体、缺少目标字形的字体不适用。指定字体存在但无法加载时构建会报错，请换成兼容的 TrueType 字体。字体授权由相应权利人规定。

### 只生成指定格式

```bash
python tools/export_book.py --format epub
python tools/export_book.py --format html txt
python tools/export_book.py --format pdf --output-dir dist/pdf-preview
python tools/check_exports.py --output-dir dist/pdf-preview
```

EPUB、HTML 和 TXT 只需要 `tools/requirements.txt` 中的 Markdown；PDF 需要 `tools/requirements-export.txt` 中的额外依赖与中文字体。检查 PDF 时也需要额外依赖。

构建清单描述**本次命令请求的格式**；同目录先前生成的其他格式不会自动更新。对外打包时请使用一次完整构建的产物，或为不同构建指定不同输出目录。`dist/` 中的所有导出产物均由 Git 忽略，无需提交。Actions 直接从 Markdown 构建，不需要原始 PDF。

## 检查什么

```bash
python tools/check.py
python tools/check_exports.py
```

- `check.py`：仓库文档链接、锚点、表格列数、历史来源元数据格式、阅读页与 Skill 资料同步（不读取原始 PDF）。
- `check_exports.py`：维护源与构建清单一致、产物哈希、EPUB ZIP 容器及 XML、导航和书内链接、HTML 离线依赖、各格式文字完整性、TXT 外部网址，以及 PDF 作者、书签、页面边距、字体嵌入和跳转目标。

这些检查不替代各阅读器实测，也不是完整的 EPUBCheck 认证。如安装了 EPUBCheck，可额外运行：

```bash
epubcheck dist/HowToSaveMoney.epub
```

PDF 排版变更后还应渲染检查封面、目录、密集表格、长链接与跨页位置。内容检查不核验政策有效性。

## GitHub 自动构建

[构建工作流](../.github/workflows/exports.yml)会在推送、Pull Request 和手动触发时构建四种格式并检查，将阅读文件作为 `reading-formats` 构建产物保存。可在仓库 **Actions → 构建阅读格式 → 对应运行 → Artifacts** 下载；该功能需要工作流被 GitHub 允许运行。

工作流只上传 Actions 产物，不创建 Release。确认正式发布时，可再将同批文件附加到 GitHub Release，避免首页链接指向尚未存在的下载地址。

## 现有工具

```bash
# 网站阅读页（含项目链接与城市、章节筛选）
python tools/build_site.py
python tools/build_site.py --check

# 可安装的离线 Skill 资料
python tools/build_skill.py
python tools/build_skill.py --check
```

`index.html` 是项目网站；`dist/HowToSaveMoney.html` 是无仓库文件依赖的完整单文件阅读版，适合独立分发。

## 实现位置

- `export_book.py`：统一构建入口及构建清单。
- `reading/book.py`：读取维护源、清理仓库导航、统一锚点及书内链接。
- `reading/epub.py`：EPUB 3 容器、章节、导航及 NCX。
- `reading/pdf.py`：PDF 排版、中文字体、页码目录与书签。
- `reading/offline.py`：独立 HTML 和 TXT。
- `reading/style.css`：EPUB 与独立 HTML 的阅读样式。
- `check_exports.py`：产物完整性与格式检查。

[返回项目首页](../README.md)
