# 使用租房决策官 Skill

**替你做“住哪、怎么签、怎么谈”三个最贵的租房决策。**

作者：毛毛&luke。入口：[rent-decision-coach/SKILL.md](../skills/rent-decision-coach/SKILL.md)。内置租房相关正文摘录、四城资料、条款协商稿、议价话术方法和费用计算器；可以独立安装，不需要先安装 `save-money-guide`。

| 决策 | 你提供 | 它交付 |
| --- | --- | --- |
| 住哪 | 候选房源、租金、通勤、到岗天数、预计住期 | 钱与时间对比、搬家回本期、首期资金需求、建议及成立条件 |
| 怎么签 | 已遮盖个人信息的合同或相关条款 | 原文问题、待核对事项、替换条款、签约和交接清单 |
| 怎么谈 | 当前价格、续租或新租条件、可比房源和退路 | 有依据的目标价、可接受条件、沟通草稿、被拒后的下一步 |

## 安装

先下载或克隆本仓库，下列命令在仓库根目录运行。**复制整个文件夹，不能只复制 SKILL.md**；已有同名目录时先检查或备份自己的修改。

### Claude Code

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/rent-decision-coach "$HOME/.claude/skills/"
```

打开新会话，用 `/rent-decision-coach` 调用。

### Codex

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/rent-decision-coach "${CODEX_HOME:-$HOME/.codex}/skills/"
```

打开新会话，用 `$rent-decision-coach` 调用。

### WorkBuddy

```bash
mkdir -p "$HOME/.workbuddy/skills"
cp -R skills/rent-decision-coach "$HOME/.workbuddy/skills/"
```

重新打开会话，确认当前版本的 Skill 扫描目录和列表，再提出“使用 rent-decision-coach，帮我……”的问题。与原 Skill 相同，WorkBuddy 的识别方式以实际版本为准。

## 三种问法

**住哪：住远点划算吗？**

```text
使用 $rent-decision-coach。我在上海，每月实际到岗 22 天，预计住 12 个月。
A 现住：月租 4500 元，单程门到门 30 分钟，交通费 200 元/月。
B 备选：月租 3500 元，单程门到门 60 分钟，交通费 300 元/月。
搬去 B 的中介、搬运和置办合计 2400 元，其余居住费用暂按相同。
比较现金和时间，算搬家多久回本，以及少通勤一小时要多付多少钱。
```

按上述假设，B 每月少花 900 元、多通勤 22 小时；扣除搬家费用，12 个月少花 8400 元。回本约 2.67 个月，到第 3 个完整月收回；本住期的时间价格临界点约 31.82 元/小时。这个数用于权衡个人时间，不等于保证能赚到的收入。

**怎么签：先帮我改最容易争议的条款。**

```text
使用 $rent-decision-coach。我在广州，合同未签，整租一年，月租 3200 元。
合同写“押金 6400 元，退租验收合格后退还”“家电维修均由租客负责”，
另有“提前退租扣全部押金，剩余预付租金不退”。这是部分摘录。
请指出需要补问的条件，给我可向房东提出的替换条款和付款前清单。
```

发合同前遮盖姓名、身份证号、电话、账户和具体门牌号。助手会区分已经看见的条款、未知事实和协商建议，不把示例当成法定统一标准。

**怎么谈：给我报价依据和能发送的话术。**

```text
使用 $rent-decision-coach。我在北京，当前租金 5500 元，租约 45 天后到期。
我查到三套同小区、同户型、装修相近的在租挂牌：5150、5200、5300 元，
都不含物业费。我现在的租金也不含物业费；预计还住一年。
若搬家要花 2400 元，交通和其他月费暂按不变。
请帮我定续租目标价、留下与搬家的现金边界，写一段微信沟通稿，
再给对方不降价时的备选提议。挂牌价不能当成交价。
```

Claude Code 把示例的 `$rent-decision-coach` 换为 `/rent-decision-coach`；WorkBuddy 可写“使用 rent-decision-coach”。

## 计算、资料与维护

内置计算器只需 Python 3.9+ 标准库。输入格式、费用定义和脚本用法见 [费用与通勤算法](../skills/rent-decision-coach/references/decision-math.md)。可退押金与成本分开，公积金提取和税收扣除不直接算作租金下降；未知费用与时间价值应列为假设或待核实项。

正文维护源为 `book/` 和 `docs/`；更新正文后运行以下命令，同步两个 Skill 的内置资料：

```bash
python3 tools/build_skill.py
python3 tools/build_skill.py --check
python3 tools/check.py
python3 -m unittest discover -s tools/tests
```

不要直接修改自动生成的 `skills/rent-decision-coach/references/guide/`。入口、`references/` 下的三个方法文件和 `scripts/` 则是人工维护。安装后的副本不会自动更新，拉取仓库后需重新复制。

来源摘录保留章节锚点、署名和哈希；政策及行情以当前官方资料、项目公告和实际房源为准。指南原书 1.1 算法仍待核实，新 Skill 使用单独列出的比较公式。Skill 提供分析和草稿，不会自动联系房东、付款、申领或签约。

本 Skill 新增说明、脚本、模板采用 CC BY-NC-SA 4.0；原文中特定工具章节继续采用 CC BY 4.0，范围见 [LICENSE](../LICENSE)。

[返回首页](../README.md) · [省钱指南 Skill](使用省钱指南Skill.md)
