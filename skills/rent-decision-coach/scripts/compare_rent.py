#!/usr/bin/env python3
"""Compare rental cash costs and commute time using a JSON input (Python 3.9+).

Author: 毛毛&luke. License: CC BY-NC-SA 4.0; see ../references/guide/LICENSE.
No housing search, policy lookup, external actions or third-party dependencies.
"""
import argparse
import json
import math
from pathlib import Path


def number(value, label, positive=False, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{label} 必须是数字')
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f'{label} 必须是有限的{"正数" if positive else "非负数"}')
    if integer and int(value) != value:
        raise ValueError(f'{label} 必须是整数')
    return value


def check_keys(data, required, optional, label):
    if not isinstance(data, dict):
        raise ValueError(f'{label} 必须是对象')
    missing = required - data.keys()
    extra = data.keys() - required - optional
    if missing or extra:
        raise ValueError(f'{label} 字段有误：缺少 {sorted(missing)}，未知 {sorted(extra)}')


def calculate(data):
    check_keys(data, {'months', 'workdays_per_month', 'plans'},
               {'time_value_per_hour'}, '输入')
    months = number(data['months'], 'months', positive=True, integer=True)
    days = number(data['workdays_per_month'], 'workdays_per_month')
    if days > 31:
        raise ValueError('workdays_per_month 不得超过 31')
    time_value = None
    if 'time_value_per_hour' in data:
        time_value = number(data['time_value_per_hour'], 'time_value_per_hour')
    if not isinstance(data['plans'], list) or len(data['plans']) < 2:
        raise ValueError('plans 至少需要两项，第一项作为基准')

    plans, names = [], set()
    required = {'name', 'rent', 'commute_minutes_one_way', 'transport_monthly'}
    optional = {'other_monthly', 'upfront_cost', 'deposit', 'prepaid_months'}
    for i, raw in enumerate(data['plans']):
        check_keys(raw, required, optional, f'plans[{i}]')
        name = raw['name']
        if not isinstance(name, str) or not name.strip() or name.strip() in names:
            raise ValueError('房源 name 必须是非空且不重复的字符串')
        name = name.strip()
        names.add(name)
        values = {key: number(raw.get(key, 0), f'{name}.{key}')
                  for key in (required - {'name'}) | (optional - {'prepaid_months'})}
        prepaid = number(raw.get('prepaid_months', 1), f'{name}.prepaid_months',
                         positive=True, integer=True)
        monthly = values['rent'] + values['transport_monthly'] + values['other_monthly']
        hours = 2 * values['commute_minutes_one_way'] * days / 60
        cost = months * monthly + values['upfront_cost']
        plans.append({
            'name': name,
            'monthly_cash_cost': monthly,
            'monthly_commute_hours': hours,
            'upfront_cost': values['upfront_cost'],
            'refundable_deposit': values['deposit'],
            'initial_housing_cash': prepaid * values['rent'] + values['deposit'] + values['upfront_cost'],
            'period_cash_cost': cost,
            'average_monthly_cash_cost': cost / months,
            'monthly_time_value': hours * time_value if time_value is not None else None,
            'period_cash_and_time_cost': cost + months * hours * time_value if time_value is not None else None,
        })

    base = plans[0]
    comparisons = []
    for plan in plans[1:]:
        saving = base['monthly_cash_cost'] - plan['monthly_cash_cost']
        extra = plan['upfront_cost'] - base['upfront_cost']
        hours = plan['monthly_commute_hours'] - base['monthly_commute_hours']
        period_saving = saving * months - extra
        payback = None
        if saving > 0:
            payback = max(0, extra / saving)
        elif saving == 0 and extra <= 0:
            payback = 0
        comparisons.append({
            'baseline': base['name'],
            'alternative': plan['name'],
            'monthly_cash_saving': saving,
            'extra_upfront_cost': extra,
            'period_cash_saving': period_saving,
            'extra_commute_hours_per_month': hours,
            'recurring_time_price_threshold': saving / hours if hours > 0 and saving > 0 else None,
            'period_time_price_threshold': period_saving / (months * hours) if hours > 0 and period_saving >= 0 else None,
            'cash_payback_months': payback,
            'cash_payback_full_months': math.ceil(payback) if payback is not None else None,
            'period_saving_after_time_value': period_saving - months * hours * time_value if time_value is not None else None,
        })

    result = {'currency': 'CNY', 'months': months, 'workdays_per_month': days,
              'time_value_per_hour': time_value, 'plans': plans, 'comparisons': comparisons}
    # Guard against arithmetic overflow even when individual inputs are finite.
    def rounded(value):
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError('输入数值过大，无法计算有限结果')
            return round(value, 4)
        if isinstance(value, dict):
            return {key: rounded(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rounded(item) for item in value]
        return value

    return rounded(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='UTF-8 JSON 比较条件')
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding='utf-8'))
        result = calculate(data)
    except (OSError, UnicodeError, ValueError, OverflowError) as error:
        parser.exit(2, f'输入错误：{error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
