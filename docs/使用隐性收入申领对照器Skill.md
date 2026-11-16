# 使用隐性收入申领对照器 Skill

**你的情况里，有哪些城市发给你的钱忘了领？**

`hidden-income-checker` 根据城市、就业参保、住房和家庭情况，筛出可能漏填、漏报或漏办的待遇，核对是否已享受，再整理条件、材料、办理人、期限和官方入口。作者：毛毛&luke。

入口：[skills/hidden-income-checker/SKILL.md](../skills/hidden-income-checker/SKILL.md)。内置相关正文摘录与四城资料，可以独立安装，不需要先安装另外两个 Skill。

| 你想查 | 它重点核对 |
| --- | --- |
| 在职租房有什么可办的 | 个税扣除、公积金租房提取、人才与住房支持，是否已按月享受 |
| 毕业、取证、换工作后有无遗漏 | 当地项目是否存在、毕业/入职/证书与参保条件、个人或单位申请 |
| 离职后哪些待遇值得查 | 失业保险金、医保衔接及与本地条件相关的项目 |
| 家里有孩子或老人 | 生育与育儿相关待遇、家庭扣除、已发工资和单位办理情况 |
| 医疗支出有没有漏报 | 已结算与未结算费用、补办程序、大病医疗扣除的适用口径 |

现金补贴、社会保险待遇、减税或退税、账户提取、低租金住房与公共服务会分别标明。全国制度与城市项目也会区分，不把所有权益都写成城市额外发钱。

## 安装

先下载或克隆仓库，下面的命令在仓库根目录运行。**复制整个文件夹，不能只复制 SKILL.md**；目标已有同名 Skill 时，先检查或备份自己的修改。

### Claude Code

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/hidden-income-checker "$HOME/.claude/skills/"
```

打开新会话，用 `/hidden-income-checker` 调用。

### Codex

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/hidden-income-checker "${CODEX_HOME:-$HOME/.codex}/skills/"
```

打开新会话，用 `$hidden-income-checker` 调用。

### WorkBuddy

```bash
mkdir -p "$HOME/.workbuddy/skills"
cp -R skills/hidden-income-checker "$HOME/.workbuddy/skills/"
```

重新打开会话，确认当前版本扫描目录和 Skill 列表，再提出“使用 hidden-income-checker，帮我……”的问题。具体发现与加载方式以实际版本为准。

## 可以这样问

**在职租房：核对是否已经享受。**

```text
使用 $hidden-income-checker。我在深圳南山区，27 岁，2024 年本科毕业，
目前在职，社保在深圳连续缴了约 18 个月；未婚，本人在深圳无房，月租 3200 元。
我已经开通公积金租房提取，不确定个税是否填了住房租金扣除。
帮我查还有哪些事项值得核对，已享受的单列，别把账户提取算成新增收入。
有联网能力就查当前官方规则，未查到的标明待核实。
```

**合同到期未续签：先核对待遇条件和窗口。**

```text
使用 $hidden-income-checker。我在上海，2026 年 10 月合同到期，单位未续签，
失业保险累计缴费约 28 个月，目前未重新就业，还没查是否已完成失业登记。
帮我列出最值得先核对的待遇、还缺哪些条件、医保怎么衔接、下一步向谁办理。
不要默认能领满一年，也不要替我提交申请。
```

**家庭扣除与育儿：避免重复计算。**

```text
使用 $hidden-income-checker。我在广州，有一个 2 岁孩子，母亲 65 岁，
我是非独生子女。夫妻都在广州工作；我已按月申报婴幼儿照护扣除，
不确定分摊比例，赡养老人扣除和育儿相关待遇也没查过。
请先补问影响判断的少量条件，再按现金待遇、减税和公共服务分别列出待办。
不要把扣除额度当退税金额，也不要把已经按月享受的列成新收益。
```

Claude Code 把示例的 `$hidden-income-checker` 换为 `/hidden-income-checker`；WorkBuddy 可写“使用 hidden-income-checker”。这些输入只演示如何提问，不表示示例人物已具备任何项目资格。

## 会得到什么

助手先选相关项目，再逐项核对公开规则、个人条件和办理状态。结果通常包括：

- 值得先办的少量事项，以及为什么和你有关。
- 还缺哪些条件、是否已由单位办理或自动结算、有没有互斥和重复申报。
- 官方材料中的金额或公式、申请人、材料、截止/补报规则、办事指南和查询日期。
- 尚未核实的项目与具体咨询问题；暂不匹配、已享受或已过窗口的原因。

资料可离线阅读；判断当前金额、申领期和办理路径需要联网读取官方资料，不能访问时会保留待核实状态。单凭学历、月薪、无房或缴费时长，不会承诺能领多少钱。金额与权益类型的处理方法见 [官方核对与金额口径](../skills/hidden-income-checker/references/verification.md)。

只需提供条件或遮盖个人信息的摘要。实名资料应由你在官方系统自行提交，不需要把身份证号、银行卡号、验证码或完整病历发给助手。Skill 默认提供对照清单与草稿，实际提交、联系机构或创建外部提醒需要另外授权。

## 维护与许可

相关正文和政策线索维护在 `book/`、`docs/`。修改后运行以下命令，同步仓库各 Skill 的内置资料：

```bash
python3 tools/build_skill.py
python3 tools/build_skill.py --check
python3 tools/check.py
python3 -m unittest discover -s tools/tests
```

不要直接修改自动生成的 `skills/hidden-income-checker/references/guide/`。Skill 入口、`references/benefit-map.md` 与 `references/verification.md` 为人工维护。安装副本不会自动更新，更新仓库后需重新复制整个目录。

署名为“毛毛&luke”，新增说明和方法文件采用 CC BY-NC-SA 4.0，原有资料继续遵循 [LICENSE](../LICENSE) 的许可范围。打包不会改变正文许可或证明政策当前有效。

[返回首页](../README.md) · [省钱指南 Skill](使用省钱指南Skill.md) · [租房决策官 Skill](使用租房决策官Skill.md)
