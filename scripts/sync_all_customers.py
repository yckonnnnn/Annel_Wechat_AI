#!/usr/bin/env python3
"""
全量同步企业客户数据脚本

用法：
    python scripts/sync_all_customers.py

注意：此脚本必须在服务器上运行（企微 API 有 IP 白名单限制）

功能：
    1. 拉取企业所有员工列表
    2. 逐个员工拉取客户列表和详情
    3. 缓存到 data/customers/ 目录
"""

import sys
import time
from datetime import datetime
from pathlib import Path


def ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root / "wecom"))

from wecom.user_service import user_service
from wecom.customer_cache import customer_cache


def sync_all_customers():
    """全量同步所有员工的所有客户"""
    print("=" * 60)
    print(f"[{ts()}] 开始全量同步企业客户数据")
    print("=" * 60)

    # 1. 获取所有员工
    print(f"\n[{ts()}] [1/2] 获取企业成员列表...")
    users = user_service.get_user_list(department_id=1)
    if not users:
        print(f"[{ts()}] ❌ 获取员工列表失败")
        print("\n可能原因:")
        print("  1. 企微 API 有 IP 白名单限制，此脚本必须在服务器上运行")
        print("  2. 检查 token 是否有效")
        return

    # 过滤出有企业微信账号的员工（有 userid）
    valid_users = [u for u in users if u.get("userid")]
    print(f"[{ts()}] ✓ 找到 {len(valid_users)} 名员工")

    # 2. 逐个员工同步客户
    print(f"\n[{ts()}] [2/2] 逐个同步员工客户...")
    print("-" * 60)

    total_customers = 0
    total_new = 0
    success_count = 0
    fail_count = 0

    for i, user in enumerate(valid_users, 1):
        userid = user.get("userid")
        name = user.get("name", userid)

        print(f"[{ts()}] [{i}/{len(valid_users)}] 开始同步 {name} ({userid})", flush=True)

        try:
            result = customer_cache.sync_user_customers(userid, force_full=True)

            if result["status"] == "ok":
                total_customers += result["total"]
                total_new += result["new_count"]
                success_count += 1
                print(f"[{ts()}] [{i}/{len(valid_users)}] ✓ {name} 完成，总客户={result['total']}, 新增={result['new_count']}", flush=True)
            else:
                fail_count += 1
                print(f"[{ts()}] [{i}/{len(valid_users)}] ❌ {name} 失败：{result['errmsg']}", flush=True)

        except Exception as e:
            fail_count += 1
            print(f"[{ts()}] [{i}/{len(valid_users)}] ❌ {name} 异常：{e}", flush=True)

        # 避免 API 限流，每同步一个员工稍作停顿
        if i < len(valid_users):
            time.sleep(0.2)

    # 3. 输出统计
    print("-" * 60)
    print(f"\n[{ts()}] 同步完成！")
    print(f"  • 成功同步：{success_count} 人")
    print(f"  • 失败：{fail_count} 人")
    print(f"  • 总客户数：{total_customers}")
    print(f"  • 新增客户：{total_new}")

    # 4. 缓存统计
    stats = customer_cache.get_stats()
    print(f"\n缓存统计:")
    print(f"  • 缓存员工数：{stats['employee_count']}")
    print(f"  • 缓存客户数：{stats['customer_count']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    sync_all_customers()
