#!/usr/bin/env python3
"""同步所有员工列表及其客户数量，保存到 data/employees.json"""

import sys
import time
import json
import requests
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from wecom.token_manager import token_manager
from wecom.user_service import user_service


def sync_employees():
    token = token_manager.get_token()
    resp = requests.get(
        "https://qyapi.weixin.qq.com/cgi-bin/user/list",
        params={"access_token": token, "department_id": 1, "fetch_child": 1},
    ).json()
    users = resp.get("userlist", [])
    print(f"员工总数: {len(users)}")

    result = []
    for i, u in enumerate(users, 1):
        userid = u.get("userid", "")
        name = u.get("name", "")
        contacts = user_service.get_contact_list(userid)
        count = len(contacts) if contacts else 0
        result.append({"name": name, "userid": userid, "customer_count": count})
        print(f"[{i}/{len(users)}] {name} ({userid}) - 客户数: {count}")
        time.sleep(0.05)

    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    out = {
        "total_employees": len(result),
        "total_customers": sum(r["customer_count"] for r in result),
        "synced_at": int(time.time()),
        "employees": result,
    }
    out_path = data_dir / "employees.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\n完成！已保存 {len(result)} 名员工，总客户数 {out['total_customers']}")
    print(f"文件：{out_path}")


if __name__ == "__main__":
    sync_employees()
