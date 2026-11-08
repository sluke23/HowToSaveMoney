# 使用省钱指南 Skill

这个 Skill 让支持 Skill 的 AI 助手先查《一线城市省钱指南》，再结合城市、开支和时间成本给出建议，每条注明章节出处。作者：毛毛&luke。

入口为 [skills/save-money-guide/SKILL.md](../skills/save-money-guide/SKILL.md)。目录内包含完整 Markdown 资料、附录与待核实清单，可以离线查询，不依赖本仓库的原始路径或在线下载。

## 安装

先下载或克隆本仓库。下面的命令均在仓库根目录运行；**复制整个文件夹，不能只复制 SKILL.md**。如目标目录已有同名 Skill，先检查或备份已有内容。

### Codex

将目录复制到个人 Skill 目录。设置过 `CODEX_HOME` 时使用该目录，否则使用 `~/.codex`：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/save-money-guide "${CODEX_HOME:-$HOME/.codex}/skills/"
```

打开新的 Codex 会话，用 `$save-money-guide` 显式调用。如果安装后未立即发现，重新打开应用或会话再试。不同版本的发现方式可查 [Codex 官方 Skill 文档](https://developers.openai.com/codex/skills/)。

### Claude Code

将同一个目录复制到个人 Skill 目录：

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/save-money-guide "$HOME/.claude/skills/"
```

打开新会话后用 `/save-money-guide` 调用，或直接提出与省钱指南相关的问题。

### WorkBuddy

将整个资料包复制到 WorkBuddy 的个人 Skill 目录 `~/.workbuddy/skills/`：

```bash
mkdir -p "$HOME/.workbuddy/skills"
cp -R skills/save-money-guide "$HOME/.workbuddy/skills/"
```

重新打开 WorkBuddy 会话，在可用 Skill 列表中确认 `save-money-guide` 已被识别，再提出“使用 save-money-guide，帮我……”的问题。若未识别，请在当前版本的 Skill 设置中确认扫描目录是否为 `~/.workbuddy/skills`；不同版本的目录和加载方式可能不同。

本项目只提供 Skill 文件和使用说明，不会自动修改你的个人配置或安装目录。

## 可以这样问

```text
使用 $save-money-guide。我在上海，房租 4500 元，话费宽带每月 180 元，
午餐经常点外卖。先帮我找三件最值得做的省钱动作，并注明章节出处。
```

```text
使用 $save-money-guide。两套房月租分别为 4500 和 3500 元，单程通勤分别为
30 和 60 分钟，每月上班 22 天，交通费分别为 200 和 300 元。帮我比较钱和时间，
缺少的数据请列为假设，不要直接套原书时薪表。
```

```text
使用 $save-money-guide。我在深圳，想了解公积金租房提取。
请区分原书说法和当前核实过的规则，没有核实就告诉我去哪里查。
```

Claude Code 中将示例里的 `$save-money-guide` 换为 `/save-money-guide`。WorkBuddy 可改为“使用 save-money-guide”。

## 回答会怎么组织

助手先查相关小节与待核实清单，再给出动作、成本、适用条件和章节出处；涉及当前政策时，在具备联网能力的环境中进一步查官方原文。离线资料的基线为 2026 年 10 月，不能自动证明现在仍可申领。

公积金提取、税款节省、真正减少支出和不确定补贴分开计算。书里的算术疑点不会直接作为结论，也不会把不同案例里的节省金额相加。

Skill 不会自动修改套餐、申请补贴、购买产品或联系第三方，也不需要提供身份证、验证码等敏感信息。

## 更新与维护

维护源仍是仓库的 `book/`、附录和版权文档。不要直接修改 Skill 内自动打包的 `references/`；修改维护源后运行：

```bash
python3 tools/build_skill.py
python3 tools/build_skill.py --check
python3 tools/check.py
```

`tools/check.py` 需要先安装 `tools/requirements.txt`。更新仓库后，重新复制整个 Skill 目录到安装位置，已安装的快照不会自动更新。

Skill 入口经过结构校验，内置资料经过链接、章节和源文件一致性检查；不同模型的实际回答可能有差异。仓库自动检查不保证政策有效性或模型回答质量。

## 许可

Skill 说明属于一般文档内容，采用 CC BY-NC-SA 4.0；内置正文与工具内容继续按 [LICENSE](../LICENSE) 的混合许可执行。打包成 Skill 不改变原有许可，也不将整包变为 CC BY 4.0。

[返回首页](../README.md)
