#!/usr/bin/env python3
"""Bundle the maintained guide into a portable, offline Skill; verify with --check."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/save-money-guide'


def bundle():
    manifest = json.loads((ROOT / 'docs/内容映射.json').read_text(encoding='utf-8'))
    docs = manifest['documents']
    paths = [doc['path'] for doc in docs] + ['docs/待核实清单.md', 'docs/版权与使用说明.md']
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
             '', '正文金额沿用原书口径，不能据此认定当前政策有效。',
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
                  '混合许可见 [LICENSE](LICENSE)，作者与版权声明见 [版权与使用说明](docs/版权与使用说明.md)。', ''])
    result['references/目录.md'] = '\n'.join(lines)
    source = {'author': manifest['author'], 'source_version': manifest['source_version'],
              'source_pdf_name': manifest['source_pdf_name'], 'source_pdf_sha256': manifest['source_sha256'],
              'source_note': manifest['source_note'],
              'note': '离线 Markdown 快照；PDF 不随包提供，政策未作当前有效性保证。',
              'sources': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths + ['LICENSE']}}
    result['references/source.json'] = json.dumps(source, ensure_ascii=False, indent=2) + '\n'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files = bundle()
    if args.check:
        stale = [name for name, text in files.items() if not (SKILL / name).is_file() or (SKILL / name).read_text(encoding='utf-8') != text]
        extra = sorted(p.relative_to(SKILL).as_posix() for p in (SKILL / 'references').rglob('*') if p.is_file() and p.relative_to(SKILL).as_posix() not in files)
        if stale or extra:
            raise SystemExit('Skill 资料未同步，请运行 python3 tools/build_skill.py：\n' + '\n'.join(stale + extra))
        print('Skill 内置资料与维护源一致。')
    else:
        # Clean only generated reference files that no longer have a maintained source.
        for path in (SKILL / 'references').rglob('*'):
            if path.is_file() and path.relative_to(SKILL).as_posix() not in files:
                path.unlink()
        for name, text in files.items():
            path = SKILL / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        print(f'已同步 {len(files)} 份 Skill 资料，安装时复制整个 skills/save-money-guide 目录即可。')


if __name__ == '__main__':
    main()
