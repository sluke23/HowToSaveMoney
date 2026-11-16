#!/usr/bin/env python3
"""Borrower cash-flow IRR / ACT-365F XIRR. Python 3.9+, standard library only.

Author: 毛毛&luke. CC BY-NC-SA 4.0; see ../references/guide/LICENSE.
Positive amounts are receipts, negative amounts are payments.
"""
import argparse
from datetime import date
import json
import math
from pathlib import Path
import re


def check_keys(value, required, optional, label):
    if not isinstance(value, dict):
        raise ValueError(f'{label} 必须是对象')
    missing = required - value.keys()
    extra = value.keys() - required - optional
    if missing or extra:
        raise ValueError(f'{label} 字段有误：缺少 {sorted(missing)}，未知 {sorted(extra)}')


def number(value, label, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label} 必须是数字')
    try:
        value = float(value)
    except OverflowError:
        raise ValueError(f'{label} 数值过大') from None
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f'{label} 必须是有限的{"正数" if positive else "数字"}')
    return value


def normalize(data):
    if not isinstance(data, dict) or data.get('mode') not in ('periodic', 'dated'):
        raise ValueError('mode 必须是 periodic 或 dated')
    mode = data['mode']
    required = {'mode', 'cashflows'} | ({'periods_per_year'} if mode == 'periodic' else set())
    check_keys(data, required, set(), '输入')
    raw = data['cashflows']
    if not isinstance(raw, list) or len(raw) < 2:
        raise ValueError('cashflows 至少需要两笔收付')
    periods_per_year = None
    if mode == 'periodic':
        periods_per_year = number(data['periods_per_year'], 'periods_per_year', positive=True)
        rows = [(i, number(amount, f'cashflows[{i}]')) for i, amount in enumerate(raw)]
    else:
        grouped = {}
        for i, row in enumerate(raw):
            check_keys(row, {'date', 'amount'}, {'label'}, f'cashflows[{i}]')
            if not isinstance(row['date'], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', row['date']):
                raise ValueError(f'cashflows[{i}].date 必须是 YYYY-MM-DD')
            day = date.fromisoformat(row['date'])
            if 'label' in row and not isinstance(row['label'], str):
                raise ValueError(f'cashflows[{i}].label 必须是字符串')
            grouped.setdefault(day, []).append(number(row['amount'], f'cashflows[{i}].amount'))
        rows = [(day, math.fsum(amounts)) for day, amounts in sorted(grouped.items())]

    active = [(when, amount) for when, amount in rows if amount != 0]
    if len(active) < 2 or active[0][1] <= 0 or not any(amount < 0 for _, amount in active):
        raise ValueError('合并后必须先有正净流入、后有负净流出，且融资时间大于零')
    negative_seen = False
    for _, amount in active:
        if amount < 0:
            negative_seen = True
        elif negative_seen:
            raise ValueError('现金流多次变号，可能无解或多解；不能输出未经全根判别的单一 IRR')
    origin = active[0][0]
    timed = [(((when - origin) / periods_per_year) if mode == 'periodic'
              else ((when - origin).days / 365), amount) for when, amount in active]
    if not all(math.isfinite(time) for time, _ in timed) or timed[-1][0] <= 0:
        raise ValueError('时间范围无法表示为有限的正融资期间')
    return mode, periods_per_year, rows, timed


def solve(timed):
    """One sign change gives monotonic log(PV inflows) - log(PV outflows)."""
    positive = [(time, math.log(amount)) for time, amount in timed if amount > 0]
    negative = [(time, math.log(-amount)) for time, amount in timed if amount < 0]

    def log_pv(entries, y):
        terms = [log_amount - time * y for time, log_amount in entries]
        largest = max(terms)
        return largest + math.log(math.fsum(math.exp(term - largest) for term in terms))

    def gap(y):
        return log_pv(positive, y) - log_pv(negative, y)

    if abs(gap(0)) <= 1e-14:
        return 0.0, abs(math.expm1(gap(0)))
    low, high = -1.0, 1.0
    while gap(low) > 0 and low > -1024:
        low *= 2
    while gap(high) < 0 and high < 1024:
        high *= 2
    if gap(low) > 0 or gap(high) < 0:
        raise ValueError('IRR 超出当前求解数值范围，请核对金额及时间单位')
    for _ in range(256):
        y = (low + high) / 2
        value = gap(y)
        if abs(value) <= 1e-14:
            break
        if value < 0:
            low = y
        else:
            high = y
    residual = abs(math.expm1(gap(y)))
    if not math.isfinite(residual) or residual > 1e-10:
        raise ValueError('未能可靠求解 IRR，请核对现金流或采用其他核验方法')
    return y, residual


def calculate(data):
    mode, periods, rows, timed = normalize(data)
    y, residual = solve(timed)
    effective = math.expm1(y)
    if not math.isfinite(effective) or effective <= -1:
        raise ValueError('年化结果超出浮点范围或过于接近 -100%，无法可靠显示')
    periodic = math.expm1(y / periods) if periods is not None else None
    nominal = periodic * periods if periods is not None else None
    inflows = math.fsum(amount for _, amount in rows if amount > 0)
    outflows = math.fsum(-amount for _, amount in rows if amount < 0)
    # fsum on the signed original amounts avoids cancellation in cost totals.
    cost = -math.fsum(amount for _, amount in rows)
    result = {
        'mode': mode,
        'time_basis': f'{periods:g} equal periods per year' if periods is not None else 'ACT/365F',
        'periods_per_year': periods,
        'effective_annual_irr_percent': effective * 100,
        'periodic_irr_percent': periodic * 100 if periodic is not None else None,
        'nominal_annual_percent': nominal * 100 if nominal is not None else None,
        'net_inflows': inflows,
        'net_outflows': outflows,
        'net_financing_cost': cost,
        'peak_net_outflow': max(-amount for _, amount in rows if amount < 0),
        'relative_npv_residual': residual,
        'cashflows': [dict(period=when, amount=amount) if mode == 'periodic'
                      else dict(date=when.isoformat(), amount=amount) for when, amount in rows],
    }
    # Check derived values, too: finite inputs can overflow during annualization.
    def verify(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError('计算结果超出有限数值范围，请核对输入')
        if isinstance(value, dict):
            for item in value.values():
                verify(item)
        if isinstance(value, list):
            for item in value:
                verify(item)
    verify(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='UTF-8 JSON 现金流')
    args = parser.parse_args()
    try:
        result = calculate(json.loads(args.input.read_text(encoding='utf-8')))
    except (OSError, UnicodeError, ValueError, OverflowError) as error:
        parser.exit(2, f'输入或计算错误：{error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
