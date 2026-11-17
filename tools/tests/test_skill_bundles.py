"""Standalone excerpt links and generated-file ownership, standard library only."""
import hashlib
import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('build_skill', ROOT / 'tools/build_skill.py')
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)
CHECK_SPEC = importlib.util.spec_from_file_location('document_check', ROOT / 'tools/check.py')
DOCUMENT_CHECK = importlib.util.module_from_spec(CHECK_SPEC)
CHECK_SPEC.loader.exec_module(DOCUMENT_CHECK)


class SkillBundleTests(unittest.TestCase):
    def test_links_follow_each_packages_own_selection(self):
        # 8.3 is available in the income package, but omitted in the rental one.
        link = '[公积金](../book/08-制度性收入.md#s8-3)'
        source = 'book/01-住处.md'
        income = BUILDER.repo_links(link, source, BUILDER.INCOME_SECTIONS)
        rent = BUILDER.repo_links(link, source, BUILDER.RENT_SECTIONS)
        self.assertEqual(income, '[公积金](08-制度性收入.md#s8-3)')
        self.assertIn('https://github.com/', rent)
        self.assertTrue(rent.endswith('#s8-3)'))
        external = '[官方原文](https://example.gov.cn/policy?id=8#rule)'
        self.assertEqual(BUILDER.repo_links(external, source, BUILDER.INCOME_SECTIONS), external)
        # A complete appendix is local only in packages that include that document.
        appendix = '[日历](../docs/附录A-一年省钱日历.md)'
        local = BUILDER.repo_links(appendix, source, BUILDER.CALENDAR_SECTIONS, BUILDER.CALENDAR_DOCUMENTS)
        self.assertEqual(local, appendix)
        self.assertIn('https://github.com/', BUILDER.repo_links(appendix, source, BUILDER.INCOME_SECTIONS))

    def test_packages_resolve_local_links_after_copy(self):
        for source_skill, build in ((BUILDER.INCOME_SKILL, BUILDER.income_bundle),
                                    (BUILDER.DISPUTE_SKILL, BUILDER.dispute_bundle),
                                    (BUILDER.CALENDAR_SKILL, BUILDER.calendar_bundle)):
            files = build()
            # Copy maintained instructions too, so missing bundled references are visible.
            for path in source_skill.rglob('*.md'):
                name = path.relative_to(source_skill).as_posix()
                if not name.startswith('references/guide/'):
                    files[name] = path.read_text(encoding='utf-8')
            with tempfile.TemporaryDirectory(prefix=source_skill.name + '-') as folder:
                skill = Path(folder).resolve()
                for name, text in files.items():
                    dest = skill / name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(text, encoding='utf-8')
                for name, text in files.items():
                    if not name.endswith('.md'):
                        continue
                    for href in re.findall(r'\[[^\]\n]*\]\(([^\n]+?)\)', text):
                        parts = urlsplit(href)
                        if parts.scheme or parts.netloc:
                            continue
                        target = ((skill / name).parent / unquote(parts.path)).resolve()
                        with self.subTest(skill=source_skill.name, source=name, href=href):
                            self.assertTrue(target.is_relative_to(skill))
                            self.assertTrue(target.is_file())
                            if parts.fragment:
                                self.assertIn(unquote(parts.fragment), DOCUMENT_CHECK.anchors(target))

    def test_metadata_hashes_refer_to_maintained_sources(self):
        for build in (BUILDER.income_bundle, BUILDER.dispute_bundle, BUILDER.calendar_bundle):
            result = build()
            metadata = json.loads(result['references/guide/source.json'])
            self.assertIn('book/08-制度性收入.md', metadata['sources'])
            for path, expected in metadata['sources'].items():
                with self.subTest(package=build.__name__, path=path):
                    self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)
            for path in metadata.get('full_documents', []):
                with self.subTest(package=build.__name__, document=path):
                    self.assertIn(path, metadata['sources'])
                    self.assertIn('references/guide/' + path, result)

    def test_loan_package_preserves_source_and_omits_unverified_mortgage_policy(self):
        result = BUILDER.loan_bundle()
        metadata = json.loads(result['references/guide/source.json'])
        self.assertEqual(metadata['sections'], {'book/13-防守.md': ['s13-3']})
        self.assertIn('id="s13-3"', result['references/guide/book/13-防守.md'])
        self.assertNotIn('references/guide/book/14-买房.md', result)
        for path, expected in metadata['sources'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)

    def test_sync_check_owns_only_generated_subtree(self):
        with tempfile.TemporaryDirectory(prefix='skill-sync-') as folder:
            skill = Path(folder)
            generated = skill / 'references/guide'
            generated.mkdir(parents=True)
            (skill / 'references/manual.md').write_text('Keep maintained instructions.', encoding='utf-8')
            expected = {'references/guide/source.md': 'current source'}
            (generated / 'source.md').write_text('current source', encoding='utf-8')
            self.assertEqual(BUILDER.stale_files(skill, 'references/guide', expected), [])
            (generated / 'source.md').write_text('outdated source', encoding='utf-8')
            self.assertEqual(BUILDER.stale_files(skill, 'references/guide', expected), ['references/guide/source.md'])
            (generated / 'obsolete.md').write_text('old generated text', encoding='utf-8')
            self.assertEqual(set(BUILDER.stale_files(skill, 'references/guide', expected)),
                             {'references/guide/source.md', 'references/guide/obsolete.md'})


if __name__ == '__main__':
    unittest.main()
