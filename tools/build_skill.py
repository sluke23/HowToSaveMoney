#!/usr/bin/env python3
"""Bundle the maintained guide into a portable, offline Skill; verify with --check."""
import argparse
import hashlib
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/save-money-guide'
RENT_SKILL = ROOT / 'skills/rent-decision-coach'
INCOME_SKILL = ROOT / 'skills/hidden-income-checker'
LOAN_SKILL = ROOT / 'skills/loan-cost-xray'
DISPUTE_SKILL = ROOT / 'skills/dispute-router'
CALENDAR_SKILL = ROOT / 'skills/savings-calendar'
REPO_URL = 'https://github.com/sluke23/HowToSaveMoney/blob/main/'
RENT_SECTIONS = {
    'book/01-住处.md': ['s1-2', 's1-3', 's1-4', 's1-5', 's1-6', 's1-7'],
    'book/03-出行.md': ['s3-1', 's3-2', 's3-3'],
    'book/04-水电气网与话费.md': ['s4-2', 's4-3'],
    'book/08-制度性收入.md': ['s8-1', 's8-2'],
    'book/09-北京.md': ['s9-1', 's9-5'],
    'book/10-上海.md': ['s10-1', 's10-2', 's10-6'],
    'book/11-广州.md': ['s11-1'],
    'book/12-深圳.md': ['s12-1', 's12-2'],
    'book/13-防守.md': ['s13-1', 's13-6'],
}
INCOME_SECTIONS = {
    'book/01-住处.md': ['s1-6'],
    'book/05-医疗与健康.md': ['s5-1', 's5-2', 's5-4'],
    'book/06-购物.md': ['s6-5'],
    'book/08-制度性收入.md': ['s8-1', 's8-2', 's8-3', 's8-4', 's8-5', 's8-6'],
    'book/09-北京.md': ['s9-1'],
    'book/10-上海.md': ['s10-1', 's10-2'],
    'book/11-广州.md': ['s11-1'],
    'book/12-深圳.md': ['s12-1', 's12-2', 's12-4'],
}
LOAN_SECTIONS = {
    'book/13-防守.md': ['s13-3'],
}
DISPUTE_SECTIONS = {
    'book/01-住处.md': ['s1-3', 's1-4'],
    'book/04-水电气网与话费.md': ['s4-1', 's4-2', 's4-4'],
    'book/06-购物.md': ['s6-2'],
    'book/08-制度性收入.md': ['s8-4'],
    'book/13-防守.md': ['s13-1', 's13-2', 's13-3', 's13-4', 's13-5', 's13-6'],
}
CALENDAR_SECTIONS = {
    'book/01-住处.md': ['s1-4', 's1-5'],
    'book/04-水电气网与话费.md': ['s4-1', 's4-2', 's4-4'],
    'book/06-购物.md': ['s6-4', 's6-5', 's6-6'],
    'book/08-制度性收入.md': ['s8-1', 's8-2', 's8-3', 's8-4', 's8-5', 's8-6'],
    'book/13-防守.md': ['s13-2'],
}
CALENDAR_DOCUMENTS = ('docs/附录A-一年省钱日历.md',)


def bundle():
    manifest = json.loads((ROOT / 'docs/内容映射.json').read_text(encoding='utf-8'))
    docs = manifest['documents']
    paths = [doc['path'] for doc in docs] + ['docs/待核实清单.md', 'docs/版权与使用说明.md', 'docs/2026-11-16-读者反馈修订.md']
    result = {}
    for name in paths:
        text = (ROOT / name).read_text(encoding='utf-8')
        # Keep legacy PDF links readable in standalone text snapshots.
        text = re.sub(r'\[查看原文\]\([^\n]*?\.pdf#page=\d+\)', '原始 PDF 页码见本段；本资料包不包含 PDF', text)
        text = text.replace('../README.md#目录', '../目录.md').replace('../README.md', '../目录.md')
        text = text.replace('../LICENSE', '../LICENSE')
        result['references/' + name] = text
    license_text = (ROOT / 'LICENSE').read_text(encoding='utf-8')
    # The instructions themselves inherit the existing general-document license.
    result['references/LICENSE'] = license_text
    lines = ['# 资料目录', '', f'作者：{manifest["author"]}。原文版本：{manifest["source_version"]}。',
             '', '原文基线为 2026 年 10 月，2026 年 11 月 16 日部分修订；核查范围见随包修订记录，不能据此认定所有政策当前有效。',
             '先读 [待核实清单](docs/待核实清单.md)，再按问题读取相关小节。', '',
             '| 主题 | 资料 |', '| --- | --- |']
    topics = ['阅读方法与适用人群', '租房、看房、合同、通勤选址、政策房', '自炊、买菜、食堂、外卖',
              '公交地铁、骑行、铁路、P+R与车辆日常费用', '手机宽带、水电燃气、订阅、记账',
              '医保、门诊统筹、体检、公共健康资源', '二手、购物、大促、会员与消费补贴',
              '图书馆、展览、夜校、语言学习、旅行社交', '个税、公积金、社保、失业金、技能补贴',
              '北京地方资源与规则', '上海地方资源与规则', '广州地方资源与规则', '深圳地方资源与规则',
              '租房陷阱、预付卡、借贷、求职、防骗与维权', '买房、贷款、税费、中介费',
              '买车、牌照、购置税与汽车补贴', '孩子入学、教育资源与家长时间线',
              '应急金、储蓄、养老金、保险与风险', '年度行动时间表', '机构与办理入口', '原书政策核对记录']
    assert len(topics) == len(docs)
    lines.extend(f'| {topic} | [{doc["title"]}]({doc["path"]}) |' for topic, doc in zip(topics, docs))
    lines.extend(['', '涉及城市规则时，主题章与对应城市章交叉阅读。', '',
                  '## 来源与许可', '', '打包版本及来源哈希见 [source.json](source.json)。',
                  '修订材料与未确认事项见 [读者反馈修订记录](docs/2026-11-16-读者反馈修订.md)。',
                  '混合许可见 [LICENSE](LICENSE)，作者与版权声明见 [版权与使用说明](docs/版权与使用说明.md)。', ''])
    result['references/目录.md'] = '\n'.join(lines)
    source = {'author': manifest['author'], 'source_version': manifest['source_version'],
              'content_revision': manifest.get('content_revision'),
              'source_pdf_name': manifest['source_pdf_name'], 'source_pdf_sha256': manifest['source_sha256'],
              'source_note': manifest['source_note'],
              'note': '离线 Markdown 快照；PDF 不随包提供，政策未作当前有效性保证。',
              'sources': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths + ['LICENSE']}}
    result['references/source.json'] = json.dumps(source, ensure_ascii=False, indent=2) + '\n'
    return result


def repo_links(text, source_path, sections, full_documents=()):
    """Keep omitted cross-references usable without depending on a checkout."""
    def replace(match):
        label, href = match.groups()
        parts = urlsplit(href)
        if parts.scheme or parts.netloc:
            return match.group(0)
        target = posixpath.normpath(posixpath.join(posixpath.dirname(source_path), unquote(parts.path))) if parts.path else source_path
        bundled = target in sections and (not parts.fragment or parts.fragment in sections[target])
        bundled = bundled or target in full_documents or target in {'docs/待核实清单.md', 'docs/版权与使用说明.md', 'docs/2026-11-16-读者反馈修订.md', 'LICENSE'}
        if bundled:
            href = posixpath.relpath(target, posixpath.dirname(source_path))
            if parts.fragment:
                href += '#' + parts.fragment
            return f'[{label}]({href})'
        url = REPO_URL + quote(target, safe='/')
        if parts.fragment:
            url += '#' + quote(parts.fragment)
        return f'[{label}]({url})'
    return re.sub(r'\[([^\]\n]*)\]\(([^\n]+?)\)', replace, text)


def excerpt_bundle(sections, index_title, intro, reading_notes, source_note, full_documents=()):
    """Extract selected sections with links scoped to this standalone package."""
    manifest = json.loads((ROOT / 'docs/内容映射.json').read_text(encoding='utf-8'))
    result = {}
    index = [f'# {index_title}', '', f'作者：{manifest["author"]}。源版本：{manifest["source_version"]}。', '',
             '本目录由 tools/build_skill.py 自动从维护源摘录，保留原编号。仅摘选，不代表重新核实政策、行情或原书中的经验数值。',
             *intro, '',
             '| 资料 | 内置小节 |', '| --- | --- |']
    for name, ids in sections.items():
        text = (ROOT / name).read_text(encoding='utf-8')
        blocks = {}
        matches = list(re.finditer(r'^<a id="(s\d+-\d+)"></a>\s*$', text, re.M))
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            blocks[match.group(1)] = text[match.start():end].split('\n---\n', 1)[0].strip()
        missing = set(ids) - blocks.keys()
        if missing:
            raise ValueError(f'{name} 缺少摘录锚点：{sorted(missing)}')
        title = text.splitlines()[0]
        license_note = next((line for line in text.splitlines() if line.startswith('> 许可：')), '> 许可：CC BY-NC-SA 4.0。')
        body = '\n\n'.join(repo_links(blocks[anchor], name, sections, full_documents) for anchor in ids)
        header = f'{title}\n\n{license_note}\n\n> 作者：{manifest["author"]}。按原章节摘录；经验价格、法律简化表述和历史政策需另核。\n\n'
        result['references/guide/' + name] = header + body + '\n'
        index.append(f'| [{title.lstrip("# ")}]({name}) | {"、".join(anchor[1:].replace("-", ".") for anchor in ids)} |')
    for name in full_documents:
        text = (ROOT / name).read_text(encoding='utf-8')
        # Whole appendices retain their own license notice and are independently cited.
        title = text.splitlines()[0].lstrip('# ')
        result['references/guide/' + name] = repo_links(text, name, sections, full_documents)
        index.append(f'| [{title}]({name}) | 全文 |')
    extra_paths = ['docs/待核实清单.md', 'docs/版权与使用说明.md', 'docs/2026-11-16-读者反馈修订.md']
    for name in extra_paths:
        result['references/guide/' + name] = repo_links((ROOT / name).read_text(encoding='utf-8'), name, sections, full_documents)
    result['references/guide/LICENSE'] = (ROOT / 'LICENSE').read_text(encoding='utf-8')
    index.extend(['', *reading_notes, '',
                  '[待核实清单](docs/待核实清单.md) · [修订记录](docs/2026-11-16-读者反馈修订.md)', '',
                  '[来源与哈希](source.json) · [混合许可](LICENSE) · [版权说明](docs/版权与使用说明.md)', ''])
    result['references/guide/目录.md'] = '\n'.join(index)
    paths = list(sections) + list(full_documents) + extra_paths + ['LICENSE']
    source = {'author': manifest['author'], 'repository': REPO_URL.removesuffix('blob/main/'),
              'source_version': manifest['source_version'], 'content_revision': manifest.get('content_revision'),
              'note': source_note,
              'sections': sections,
              'sources': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}
    if full_documents:
        source['full_documents'] = list(full_documents)
    result['references/guide/source.json'] = json.dumps(source, ensure_ascii=False, indent=2) + '\n'
    return result


def rent_bundle():
    return excerpt_bundle(
        RENT_SECTIONS, '租房资料目录',
        ['原书 1.1 公式仍待核实，未打包；计算见 [费用与通勤算法](../decision-math.md)。'],
        ['北上广深分别读 9.1、10.1–10.2、11.1、12.1；短期求职过渡另读 12.2。',
         '交通报价读 3.1–3.3；水电宽带读 4.2–4.3；租金扣除读 8.1–8.2。政策当前有效性须另查官方文件。'],
        '租房相关小节摘录；未随包包含原始 PDF，不代表现行政策已核实。')


def income_bundle():
    return excerpt_bundle(
        INCOME_SECTIONS, '隐性收入与待遇资料目录',
        ['先按 [项目对照](../benefit-map.md) 筛查，再按 [核对方法](../verification.md) 查现行官方规则。'],
        ['8.1–8.2 查扣除与汇算，8.3 查账户提取，8.4–8.6 查参保、保险待遇、技能及其他补贴线索。',
         '住房读 1.6 和对应城市小节；就医读 5.1–5.2，公共服务读 5.4，原计划消费补贴读 6.5。',
         '存在项目不等于本人可申领；核对已享受、当前窗口、重复与互斥限制。'],
        '补贴与待遇相关小节摘录；历史数额与入口仅作线索，不代表现行资格或已获批。')


def loan_bundle():
    return excerpt_bundle(
        LOAN_SECTIONS, '借贷成本资料目录',
        ['先读 [现金流还原](../cashflow-modeling.md)，按 [IRR 算法](../irr-method.md) 统一计算。'],
        ['13.3 是借贷成本比较的正文来源；新增算法、输入格式与情景比较在上层方法文件。',
         '14.2 的贷款贴息与提前还款阶段结论仍待核实，未纳入摘录，不作为贷款成本计算依据。'],
        '借贷成本相关小节摘录；政策及法律判断须另查现行原文，数学计算不证明合同合法性。')


def dispute_bundle():
    return excerpt_bundle(
        DISPUTE_SECTIONS, '维权分诊资料目录',
        ['先读 [渠道与判断边界](../routes.md)，按 [证据与行动模板](../evidence-and-actions.md) 整理材料；',
         '程序与期限按 [官方核对方法](../official-verification.md) 查适用原文。'],
        ['1.3–1.4、13.1 查租赁主体、合同及交接；13.2 查预付，6.2 查二手，4.1–4.2/4.4 查账单与订阅。',
         '8.4、13.4 查用工与参保线索；13.3、13.5 查借贷及诈骗风险；13.6 提供基础维权工具箱。',
         '原文的固定递进顺序、热线范围、证据排序和清理提示需按上层方法文件限定，不能直接作为程序或证据规则。',
         '新增劳动争议与正式程序指引为补充分诊方法，不声称原书已完整覆盖相关法律。'],
        '维权相关小节摘录；保留原文不等于认可其法律简化表述，受理、证据及期限另核适用官方规则。')


def calendar_bundle():
    return excerpt_bundle(
        CALENDAR_SECTIONS, '月度省钱行动资料目录',
        ['先按 [节律与事项对照](../rhythm-map.md) 选任务，再按 [时点核对与复盘](../deadlines-and-review.md) 排个人日程。'],
        ['附录 A 的月份是检查线索，不证明当前政策窗口或商户最低价；医保年度、参保期和其他规则按地区与身份另核。',
         '1.4–1.5 查合同与续租准备；4.1–4.2/4.4 查套餐、优惠和订阅到期；6.4–6.6 查原计划消费与会员。',
         '8.1–8.6 查扣除、汇算、账户及待遇线索，13.2 查预付条款；不把历史金额、经验时限和简化合同表述当成现行个人规则。'],
        '年度日历全文及月度行动相关摘录；日历月份不是统一截止日，个人时点与现行窗口须分别核对。',
        full_documents=CALENDAR_DOCUMENTS)


def bundles():
    return [(SKILL, 'references', bundle()),
            (RENT_SKILL, 'references/guide', rent_bundle()),
            (INCOME_SKILL, 'references/guide', income_bundle()),
            (LOAN_SKILL, 'references/guide', loan_bundle()),
            (DISPUTE_SKILL, 'references/guide', dispute_bundle()),
            (CALENDAR_SKILL, 'references/guide', calendar_bundle())]


def stale_files(skill, generated_root, files):
    stale = [name for name, text in files.items() if not (skill / name).is_file() or (skill / name).read_text(encoding='utf-8') != text]
    extra = sorted(p.relative_to(skill).as_posix() for p in (skill / generated_root).rglob('*')
                   if p.is_file() and p.relative_to(skill).as_posix() not in files)
    return stale + extra


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    for skill, generated_root, files in bundles():
        if args.check:
            stale = stale_files(skill, generated_root, files)
            if stale:
                raise SystemExit(f'{skill.name} 资料未同步，请运行 python3 tools/build_skill.py：\n' + '\n'.join(stale))
            print(f'{skill.name} 内置资料与维护源一致。')
        else:
            # Only the generated subtree is owned by this builder.
            for path in (skill / generated_root).rglob('*'):
                if path.is_file() and path.relative_to(skill).as_posix() not in files:
                    path.unlink()
            for name, text in files.items():
                path = skill / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding='utf-8')
            print(f'{skill.name}：已同步 {len(files)} 份资料，安装时复制整个 skills/{skill.name} 目录即可。')


if __name__ == '__main__':
    main()
