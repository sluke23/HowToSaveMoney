"""Independently known cash-flow roots and portable CLI behavior."""
from datetime import date, timedelta
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills/loan-cost-xray'
SPEC = importlib.util.spec_from_file_location('loan_irr', SKILL / 'scripts/loan_irr.py')
IRR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IRR)


def periodic(flows, periods=12):
    return {'mode': 'periodic', 'periods_per_year': periods, 'cashflows': flows}


class LoanIRRTests(unittest.TestCase):
    def test_interest_only_has_exact_monthly_rate(self):
        result = IRR.calculate(periodic([10000] + [-60] * 11 + [-10060]))
        self.assertAlmostEqual(result['periodic_irr_percent'], 0.6, places=9)
        self.assertAlmostEqual(result['nominal_annual_percent'], 7.2, places=9)
        self.assertAlmostEqual(result['effective_annual_irr_percent'], ((1.006 ** 12) - 1) * 100, places=9)
        self.assertAlmostEqual(result['net_financing_cost'], 720)

    def test_fixed_original_principal_fee_costs_more_than_advertised_rate(self):
        result = IRR.calculate(periodic([10000] + [-893.33] * 11 + [-893.37]))
        self.assertAlmostEqual(result['net_financing_cost'], 720)
        self.assertAlmostEqual(result['nominal_annual_percent'], 13.0341, places=3)
        self.assertAlmostEqual(result['effective_annual_irr_percent'], 13.842, places=2)
        monthly = result['periodic_irr_percent'] / 100
        self.assertAlmostEqual(10000, sum(payment / (1 + monthly) ** i
                                         for i, payment in enumerate([893.33] * 11 + [893.37], 1)), places=6)

    def test_exact_two_period_polynomial_root(self):
        # x = 1+r; 100*x^2 - 60*x - 60 = 0.
        expected = (60 + math.sqrt(60 ** 2 + 4 * 100 * 60)) / 200 - 1
        result = IRR.calculate(periodic([100, -60, -60], 1))
        self.assertAlmostEqual(result['effective_annual_irr_percent'], expected * 100, places=10)
        self.assertLess(result['relative_npv_residual'], 1e-10)

    def test_balloon_actual_days_and_leap_year(self):
        start, end = date(2024, 1, 1), date(2025, 1, 1)
        result = IRR.calculate({'mode': 'dated', 'cashflows': [
            {'date': end.isoformat(), 'amount': -1100},
            {'date': start.isoformat(), 'amount': 1000},
        ]})
        self.assertEqual((end - start).days, 366)
        self.assertAlmostEqual(result['effective_annual_irr_percent'], ((1.1 ** (365 / 366)) - 1) * 100, places=10)
        self.assertIsNone(result['periodic_irr_percent'])
        self.assertIsNone(result['nominal_annual_percent'])

    def test_upfront_fee_same_day_netting_is_equivalent(self):
        rows = [{'date': '2026-01-01', 'amount': 10000},
                {'date': '2026-01-01', 'amount': -300},
                {'date': '2027-01-01', 'amount': -10720}]
        actual = IRR.calculate({'mode': 'dated', 'cashflows': rows})
        expected = IRR.calculate({'mode': 'dated', 'cashflows': [
            {'date': '2026-01-01', 'amount': 9700}, rows[-1]]})
        self.assertEqual(actual['effective_annual_irr_percent'], expected['effective_annual_irr_percent'])
        self.assertEqual(actual['net_financing_cost'], 1020)
        self.assertEqual(actual['cashflows'][0]['amount'], 9700)

    def test_equally_spaced_days_match_dated_results(self):
        start = date(2026, 1, 1)
        flows = [1000, -340, -340, -340]
        dated = IRR.calculate({'mode': 'dated', 'cashflows': [
            {'date': (start + timedelta(days=i)).isoformat(), 'amount': amount}
            for i, amount in enumerate(flows)]})
        daily = IRR.calculate(periodic(flows, 365))
        self.assertAlmostEqual(dated['effective_annual_irr_percent'], daily['effective_annual_irr_percent'], places=8)

    def test_zero_negative_and_skipped_period_rates(self):
        self.assertEqual(IRR.calculate(periodic([1000, -500, -500]))['effective_annual_irr_percent'], 0)
        negative = IRR.calculate(periodic([1000, -900], 1))
        self.assertAlmostEqual(negative['effective_annual_irr_percent'], -10, places=10)
        self.assertEqual(negative['net_financing_cost'], -100)
        skipped = IRR.calculate(periodic([1000, 0, -1210], 1))
        self.assertAlmostEqual(skipped['effective_annual_irr_percent'], 10, places=10)

    def test_multiple_early_drawdowns_with_one_sign_change(self):
        result = IRR.calculate(periodic([100, 110, -242], 1))
        # At 10%: 100 + 110/1.1 - 242/1.1^2 == 0.
        self.assertAlmostEqual(result['effective_annual_irr_percent'], 10, places=10)

    def test_nonconventional_and_invalid_inputs_fail_closed(self):
        cases = [periodic([100, -230, 132], 1), periodic([100, 0, 50]),
                 periodic([-100, 110]), periodic([0, 0]), periodic([1000, True]),
                 periodic([1000, float('nan')]), periodic([1000, -1100], 0),
                 {'mode': 'periodic', 'cashflows': [1000, -1100]},
                 {'mode': 'dated', 'cashflows': [{'date': '2026-02-30', 'amount': 1000},
                                                 {'date': '2027-01-01', 'amount': -1100}]},
                 {'mode': 'dated', 'cashflows': [{'date': '2026-01-01', 'amount': 1000},
                                                 {'date': '2026-01-01', 'amount': -1100}]},
                 dict(periodic([1000, -1100]), service_fee=300)]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(ValueError):
                IRR.calculate(data)

    def test_early_settlement_can_raise_annual_rate_but_lower_total_cost(self):
        original = IRR.calculate(periodic([9700] + [-1000] * 11))
        settled = IRR.calculate(periodic([9700, -1000, -9400]))
        self.assertLess(settled['net_financing_cost'], original['net_financing_cost'])
        self.assertGreater(settled['effective_annual_irr_percent'], original['effective_annual_irr_percent'])

    def test_portable_cli_and_clear_failure(self):
        with tempfile.TemporaryDirectory(prefix='loan-xray-') as folder:
            work = Path(folder)
            installed = work / '独立安装/loan-cost-xray'
            shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns('__pycache__'))
            source = work / '分期.json'
            source.write_text(json.dumps(periodic([1000, -1100], 1)), encoding='utf-8')
            command = [sys.executable, str(installed / 'scripts/loan_irr.py'), '--input', str(source)]
            result = subprocess.run(command, cwd=work, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertAlmostEqual(json.loads(result.stdout)['effective_annual_irr_percent'], 10, places=9)
            source.write_text(json.dumps(periodic([100, -230, 132])), encoding='utf-8')
            failed = subprocess.run(command, cwd=work, text=True, capture_output=True)
            self.assertEqual(failed.returncode, 2)
            self.assertEqual(failed.stdout, '')
            self.assertIn('多次变号', failed.stderr)
            self.assertNotIn('Traceback', failed.stderr)


if __name__ == '__main__':
    unittest.main()
