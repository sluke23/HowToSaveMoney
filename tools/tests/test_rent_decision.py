"""Rental arithmetic and standalone installation checks; standard library only."""
import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills/rent-decision-coach'
SPEC = importlib.util.spec_from_file_location('compare_rent', SKILL / 'scripts/compare_rent.py')
CALCULATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CALCULATOR)


def example():
    return {'months': 12, 'workdays_per_month': 22, 'plans': [
        {'name': '现住 A', 'rent': 4500, 'commute_minutes_one_way': 30, 'transport_monthly': 200},
        {'name': '备选 B', 'rent': 3500, 'commute_minutes_one_way': 60, 'transport_monthly': 300,
         'upfront_cost': 2400},
    ]}


class RentalDecisionTests(unittest.TestCase):
    def test_cash_time_and_payback_are_separate(self):
        result = CALCULATOR.calculate(example())
        a, b = result['plans']
        comparison = result['comparisons'][0]
        self.assertEqual((a['period_cash_cost'], b['period_cash_cost']), (56400, 48000))
        self.assertEqual((a['monthly_commute_hours'], b['monthly_commute_hours']), (22, 44))
        self.assertEqual(comparison['period_cash_saving'], 8400)
        self.assertAlmostEqual(comparison['period_time_price_threshold'], 31.8182)
        self.assertAlmostEqual(comparison['cash_payback_months'], 2.6667)
        self.assertEqual(comparison['cash_payback_full_months'], 3)
        self.assertIsNone(b['period_cash_and_time_cost'])

    def test_short_stay_can_reverse_the_choice(self):
        data = example()
        data['months'] = 2
        comparison = CALCULATOR.calculate(data)['comparisons'][0]
        self.assertEqual(comparison['period_cash_saving'], -600)
        self.assertIsNone(comparison['period_time_price_threshold'])

    def test_deposit_and_prepaid_rent_change_liquidity_not_consumed_cost(self):
        data = example()
        before = CALCULATOR.calculate(data)['plans'][1]
        data['plans'][1].update(deposit=7000, prepaid_months=3)
        after = CALCULATOR.calculate(data)['plans'][1]
        self.assertEqual(before['period_cash_cost'], after['period_cash_cost'])
        self.assertEqual(after['initial_housing_cash'], 19900)

    def test_user_time_value_can_reverse_cash_preference(self):
        data = example()
        data['time_value_per_hour'] = 50
        comparison = CALCULATOR.calculate(data)['comparisons'][0]
        self.assertEqual(comparison['period_saving_after_time_value'], -4800)

    def test_zero_commute_and_no_recurring_savings(self):
        data = example()
        data['workdays_per_month'] = 0
        data['plans'][1]['rent'] = 4500
        comparison = CALCULATOR.calculate(data)['comparisons'][0]
        self.assertEqual(comparison['extra_commute_hours_per_month'], 0)
        self.assertIsNone(comparison['recurring_time_price_threshold'])
        self.assertIsNone(comparison['cash_payback_months'])

    def test_nonpositive_extra_cost_is_already_recovered(self):
        data = example()
        data['plans'][1]['upfront_cost'] = 0
        self.assertEqual(CALCULATOR.calculate(data)['comparisons'][0]['cash_payback_months'], 0)

    def test_invalid_inputs_do_not_produce_plausible_results(self):
        mutations = [
            lambda d: d.update(months=0), lambda d: d.update(months=1.5),
            lambda d: d.update(workdays_per_month=32),
            lambda d: d.update(time_value_per_hour=True),
            lambda d: d['plans'][0].update(rent=-1),
            lambda d: d['plans'][0].update(rent=float('nan')),
            lambda d: d['plans'][0].update(deposit=float('inf')),
            lambda d: d['plans'][0].update(prepaid_months=0),
            lambda d: d['plans'][0].pop('transport_monthly'),
            lambda d: d['plans'][0].update(transport_montly=50),
            lambda d: d['plans'][1].update(name='现住 A'),
        ]
        for mutation in mutations:
            data = copy.deepcopy(example())
            mutation(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                CALCULATOR.calculate(data)

    def test_copied_skill_runs_outside_repository(self):
        with tempfile.TemporaryDirectory(prefix='rent-decision-') as folder:
            work = Path(folder)
            installed = work / '独立安装/rent-decision-coach'
            shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns('__pycache__'))
            source = work / '房源选项.json'
            source.write_text(json.dumps(example(), ensure_ascii=False), encoding='utf-8')
            process = subprocess.run([sys.executable, str(installed / 'scripts/compare_rent.py'),
                                      '--input', str(source)], cwd=work, text=True, capture_output=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(json.loads(process.stdout)['comparisons'][0]['period_cash_saving'], 8400)
            source.write_text('{"months": 0}', encoding='utf-8')
            invalid = subprocess.run([sys.executable, str(installed / 'scripts/compare_rent.py'),
                                      '--input', str(source)], cwd=work, text=True, capture_output=True)
            self.assertEqual(invalid.returncode, 2)
            self.assertEqual(invalid.stdout, '')
            self.assertNotIn('Traceback', invalid.stderr)


if __name__ == '__main__':
    unittest.main()
