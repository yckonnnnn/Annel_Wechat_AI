#!/usr/bin/env python3
"""
提取咨询师名下客户的电话号码

从企业微信 API 获取客户信息，从备注名称中提取手机号码
适用于咨询师已将在客户名称/备注中添加手机号的场景
"""

import re
import json
from datetime import datetime
from pathlib import Path

# 本地开发环境路径调整
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from wecom.user_service import user_service
from wecom.token_manager import token_manager
import requests


PHONE_PATTERN = re.compile(r'(1[3-9]\d{9})')


def extract_phone_from_name(name: str) -> str | None:
    """从名称中提取手机号"""
    if not name:
        return None
    match = PHONE_PATTERN.search(name)
    return match.group(1) if match else None


def get_all_consultants_with_customers():
    """获取所有有客户的咨询师及其客户数量"""
    token = token_manager.get_token()
    r = requests.get('https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get_follow_user_list',
                     params={'access_token': token}, timeout=10)
    follow_users = r.json().get('follow_user', [])

    result = []
    for uid in follow_users:
        contacts = user_service.get_contact_list(uid)
        if len(contacts) > 0:
            result.append({'userid': uid, 'customer_count': len(contacts)})

    result.sort(key=lambda x: x['customer_count'], reverse=True)
    return result


def extract_phones_for_consultant(userid: str, verbose: bool = False) -> dict:
    """
    获取指定咨询师名下所有客户的电话号码

    Returns:
        {
            'userid': str,
            'total': int,
            'with_phone': int,
            'customers': [
                {
                    'external_userid': str,
                    'name': str,
                    'phone': str | None,
                    'remark': str | None
                },
                ...
            ]
        }
    """
    customer_ids = user_service.get_contact_list(userid)
    result = {
        'userid': userid,
        'total': len(customer_ids),
        'with_phone': 0,
        'customers': []
    }

    for cid in customer_ids:
        detail = user_service.get_external_contact(cid)
        if not detail:
            continue

        name = detail.get('name', '')
        phone = extract_phone_from_name(name)

        # 获取 follow_user 中的 remark
        remark = None
        follow_users = detail.get('follow_user', [])
        for fu in follow_users:
            if fu.get('userid') == userid:
                remark = fu.get('remark')
                break

        customer_info = {
            'external_userid': cid,
            'name': name,
            'phone': phone,
            'remark': remark
        }
        result['customers'].append(customer_info)

        if phone:
            result['with_phone'] += 1
            if verbose:
                print(f"  {name} -> {phone}")

    return result


def batch_extract_all_phones(output_dir: str = None):
    """批量提取所有咨询师的客户电话号码"""
    print("=" * 60)
    print("开始批量提取客户电话号码")
    print("=" * 60)

    consultants = get_all_consultants_with_customers()
    print(f"共有 {len(consultants)} 位咨询师有客户\n")

    summary = []
    all_customers_with_phones = []

    for idx, consultant in enumerate(consultants[:10]):  # 先处理前 10 位
        uid = consultant['userid']
        print(f"[{idx+1}/{len(consultants)}] 处理咨询师：{uid} ({consultant['customer_count']} 个客户)")

        result = extract_phones_for_consultant(uid, verbose=False)
        summary.append({
            'userid': uid,
            'total_customers': result['total'],
            'customers_with_phone': result['with_phone'],
            'phone_rate': f"{result['with_phone']/result['total']*100:.1f}%" if result['total'] > 0 else "0%"
        })

        for c in result['customers']:
            if c['phone']:
                all_customers_with_phones.append({
                    'consultant_userid': uid,
                    **c
                })

    # 输出汇总
    print("\n" + "=" * 60)
    print("汇总结果")
    print("=" * 60)
    print(f"{'咨询师 ID':<40} {'总客户数':>10} {'含手机号':>10} {'比例':>10}")
    print("-" * 60)

    total_customers = 0
    total_with_phone = 0
    for s in summary:
        print(f"{s['userid']:<40} {s['total_customers']:>10} {s['customers_with_phone']:>10} {s['phone_rate']:>10}")
        total_customers += s['total_customers']
        total_with_phone += s['customers_with_phone']

    print("-" * 60)
    print(f"{'总计':<40} {total_customers:>10} {total_with_phone:>10} {total_with_phone/total_customers*100:.1f}%")

    # 保存结果
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 保存汇总
        with open(output_path / f'summary_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        # 保存含手机号的客户列表
        with open(output_path / f'customers_with_phones_{timestamp}.json', 'w', encoding='utf-8') as f:
            json.dump(all_customers_with_phones, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存到：{output_path}")

    return summary, all_customers_with_phones


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='提取客户电话号码')
    parser.add_argument('--consultant', '-c', help='指定咨询师 userid，不传则处理所有')
    parser.add_argument('--output', '-o', default='./output', help='输出目录')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    if args.consultant:
        result = extract_phones_for_consultant(args.consultant, verbose=args.verbose)
        print(f"\n咨询师：{result['userid']}")
        print(f"总客户数：{result['total']}")
        print(f"含手机号：{result['with_phone']} ({result['with_phone']/result['total']*100:.1f}%)")
    else:
        batch_extract_all_phones(args.output)
