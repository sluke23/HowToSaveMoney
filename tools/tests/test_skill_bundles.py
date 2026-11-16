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

    def test_income_package_resolves_local_links_after_copy(self):
        files = BUILDER.income_bundle()
        # Include maintained method files as they would be installed with the package.
        for name in ('benefit-map.md', 'verification.md'):
            files['references/' + name] = (BUILDER.INCOME_SKILL / 'references' / name).read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory(prefix='income-skill-') as folder:
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
                    with self.subTest(source=name, href=href):
                        self.assertTrue(target.is_relative_to(skill))
                        self.assertTrue(target.is_file())
                        if parts.fragment:
                            self.assertIn(f'id="{unquote(parts.fragment)}"', target.read_text(encoding='utf-8'))

    def test_metadata_hashes_refer_to_maintained_sources(self):
        result = BUILDER.income_bundle()
        metadata = json.loads(result['references/guide/source.json'])
        self.assertIn('book/08-制度性收入.md', metadata['sources'])
        for path, expected in metadata['sources'].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected)

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
