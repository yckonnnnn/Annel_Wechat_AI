import json
import os
import time
import base64
from pathlib import Path
from typing import List, Dict, Optional, Set
from wecom.user_service import user_service


class CustomerCache:
    """
    客户数据缓存服务 - 缓存员工客户列表和客户详情

    数据结构：
    data/customers/
    ├── {userid}.json              # 员工客户列表缓存
    │   - external_userids: string[]
    │   - last_sync: timestamp
    │   - total_count: int
    │
    └── detail/
        ├── {external_userid}.json  # 客户详情缓存
        │   - name, avatar, gender, corp_name, position
        │   - updated_at: timestamp
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.customer_dir = self.data_dir / "customers"
        self.detail_dir = self.customer_dir / "detail"
        self.customer_dir.mkdir(parents=True, exist_ok=True)
        self.detail_dir.mkdir(parents=True, exist_ok=True)

    def _encode_userid(self, external_userid: str) -> str:
        """将 external_userid 编码为安全文件名"""
        return base64.urlsafe_b64encode(external_userid.encode()).decode().rstrip('=')

    def _decode_userid(self, safe_name: str) -> str:
        """将安全文件名解码回 external_userid"""
        padding = 4 - len(safe_name) % 4
        if padding != 4:
            safe_name += '=' * padding
        return base64.urlsafe_b64decode(safe_name.encode()).decode()

    # ========== 员工客户列表缓存 ==========

    def get_user_customer_ids(self, userid: str) -> List[str]:
        """获取员工名下的客户 ID 列表（从缓存）"""
        file_path = self.customer_dir / f"{userid}.json"
        if not file_path.exists():
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("external_userids", [])
        except:
            return []

    def save_user_customer_ids(self, userid: str, external_ids: List[str]):
        """保存员工客户 ID 列表到缓存"""
        file_path = self.customer_dir / f"{userid}.json"
        data = {
            "userid": userid,
            "external_userids": external_ids,
            "total_count": len(external_ids),
            "last_sync": int(time.time()),
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_last_sync_time(self, userid: str) -> int:
        """获取员工客户列表上次同步时间"""
        file_path = self.customer_dir / f"{userid}.json"
        if not file_path.exists():
            return 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("last_sync", 0)
        except:
            return 0

    # ========== 客户详情缓存 ==========

    def get_customer_detail(self, external_userid: str) -> Optional[Dict]:
        """获取客户详情（从缓存）"""
        file_path = self.detail_dir / f"{self._encode_userid(external_userid)}.json"
        if not file_path.exists():
            return None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None

    def save_customer_detail(self, external_userid: str, detail: Dict):
        """保存客户详情到缓存"""
        file_path = self.detail_dir / f"{self._encode_userid(external_userid)}.json"
        data = {
            "external_userid": external_userid,
            "name": detail.get("name", ""),
            "avatar": detail.get("avatar", ""),
            "gender": detail.get("gender", 0),
            "corp_name": detail.get("corp_name", ""),
            "position": detail.get("position", ""),
            "updated_at": int(time.time()),
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_customer_details(self, external_userids: List[str]) -> Dict[str, Dict]:
        """批量获取客户详情，返回 {external_userid: detail}，缺失的返回 None"""
        result = {}
        for eid in external_userids:
            detail = self.get_customer_detail(eid)
            result[eid] = detail
        return result

    def list_all_customer_details(self) -> List[Dict]:
        """列出所有缓存的客户详情"""
        details = []
        for file_path in self.detail_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    details.append(data)
            except:
                continue
        return details

    # ========== 增量同步 ==========

    def sync_user_customers(self, userid: str, force_full: bool = False) -> Dict:
        """
        同步员工客户数据

        Args:
            userid: 员工 userid
            force_full: 是否强制全量同步（忽略缓存）

        Returns:
            {
                "total": int,          # 总客户数
                "new_count": int,      # 新增客户数
                "updated_count": int,  # 更新的客户数
                "status": "ok" | "error",
                "errmsg": str
            }
        """
        result = {"total": 0, "new_count": 0, "updated_count": 0, "status": "ok", "errmsg": ""}

        # 1. 从企微 API 获取该员工名下所有客户 ID
        api_ids = user_service.get_contact_list(userid)
        if not api_ids:
            result["status"] = "error"
            result["errmsg"] = "API 返回空客户列表"
            return result

        result["total"] = len(api_ids)

        # 2. 获取本地已缓存的 ID
        cached_ids = set(self.get_user_customer_ids(userid))
        api_ids_set = set(api_ids)

        # 3. 计算差集
        new_ids = api_ids_set - cached_ids
        removed_ids = cached_ids - api_ids_set

        # 4. 如果是增量同步且没有新增，直接返回
        if not force_full and not new_ids:
            # 更新 last_sync 时间
            self.save_user_customer_ids(userid, api_ids)
            return result

        # 5. 拉取新增客户的详情
        print(f"[CustomerCache] 员工 {userid}: 总客户={len(api_ids)}, 新增={len(new_ids)}, 移除={len(removed_ids)}")

        for i, eid in enumerate(new_ids):
            detail = user_service.get_external_contact(eid)
            if detail:
                self.save_customer_detail(eid, detail)
                result["new_count"] += 1
            # 避免频繁请求，每 100 个稍微停顿
            if (i + 1) % 100 == 0:
                time.sleep(0.1)

        # 6. 更新员工客户列表缓存
        self.save_user_customer_ids(userid, api_ids)

        return result

    # ========== 工具方法 ==========

    def find_owner_by_external_userid(self, external_userid: str) -> Optional[str]:
        """
        根据客户 external_userid 查找归属的员工 userid
        遍历所有已缓存的员工客户列表
        """
        for file_path in self.customer_dir.glob("*.json"):
            # 跳过 detail 目录下的文件（detail 也在 customer_dir 下，但 glob 模式是 *.json 不会递归）
            if file_path.name.endswith(".json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if external_userid in data.get("external_userids", []):
                            return data.get("userid")
                except:
                    continue
        return None

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        user_files = list(self.customer_dir.glob("*.json"))
        detail_files = list(self.detail_dir.glob("*.json"))
        return {
            "employee_count": len(user_files),
            "customer_count": len(detail_files),
        }

    def clear_cache(self, userid: str = None):
        """清空缓存"""
        if userid:
            # 清空单个员工
            file_path = self.customer_dir / f"{userid}.json"
            if file_path.exists():
                file_path.unlink()
        else:
            # 清空所有
            for f in self.customer_dir.glob("*.json"):
                f.unlink()
            for f in self.detail_dir.glob("*.json"):
                f.unlink()

    def sync_all_customers_full(self) -> Dict:
        """
        全量同步企业所有员工的所有客户

        Returns:
            {
                "employees_synced": int,
                "total_customers": int,
                "new_customers": int,
                "failed_employees": List[str],
                "status": "ok" | "error",
                "errmsg": str
            }
        """
        result = {
            "employees_synced": 0,
            "total_customers": 0,
            "new_customers": 0,
            "failed_employees": [],
            "status": "ok",
            "errmsg": "",
        }

        # 1. 获取所有员工
        users = user_service.get_user_list(department_id=1)
        if not users:
            result["status"] = "error"
            result["errmsg"] = "获取员工列表失败"
            return result

        valid_users = [u for u in users if u.get("userid")]

        # 2. 逐个同步
        for user in valid_users:
            userid = user.get("userid")
            try:
                sync_result = self.sync_user_customers(userid, force_full=True)
                if sync_result["status"] == "ok":
                    result["employees_synced"] += 1
                    result["total_customers"] += sync_result["total"]
                    result["new_customers"] += sync_result["new_count"]
                else:
                    result["failed_employees"].append(userid)
            except Exception as e:
                result["failed_employees"].append(userid)
                result["errmsg"] = f"{userid}: {str(e)}"

            # 避免 API 限流
            time.sleep(0.1)

        return result


# 全局单例
customer_cache = CustomerCache()
