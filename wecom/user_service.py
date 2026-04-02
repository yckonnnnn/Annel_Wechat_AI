import requests
from typing import List, Dict, Optional, Any
from wecom.token_manager import token_manager


class UserService:
    """企业微信用户与客户服务"""

    API_BASE = "https://qyapi.weixin.qq.com/cgi-bin"

    def _get(self, url: str, params: dict = None) -> dict:
        params = params or {}
        params["access_token"] = token_manager.get_token()
        try:
            return requests.get(url, params=params, timeout=10).json()
        except Exception as e:
            return {"errcode": -1, "errmsg": str(e)}

    def get_contact_list(self, userid: str) -> List[str]:
        """获取咨询师的外部客户列表"""
        data = self._get(f"{self.API_BASE}/externalcontact/list", {"userid": userid})
        return data.get("external_userid", []) if data.get("errcode") == 0 else []

    def get_external_contact(self, external_userid: str) -> Optional[Dict[str, Any]]:
        """获取客户详情"""
        data = self._get(f"{self.API_BASE}/externalcontact/get", {"external_userid": external_userid})
        return data.get("external_contact", {}) if data.get("errcode") == 0 else None

    def get_user_list(self, department_id: int = 1) -> List[Dict[str, Any]]:
        """获取企业成员列表"""
        data = self._get(f"{self.API_BASE}/user/list", {"department_id": department_id})
        return data.get("userlist", []) if data.get("errcode") == 0 else []

    def get_contact_info(self, external_userid: str) -> str:
        """获取用于大模型的客户信息摘要"""
        contact = self.get_external_contact(external_userid)
        if not contact:
            return "未知用户"

        name = contact.get("name", "未知")
        gender = contact.get("gender", 0)
        gender_map = {0: "未知", 1: "男", 2: "女"}

        info_parts = [f"姓名：{name}", f"性别：{gender_map.get(gender, '未知')}"]

        if contact.get("position"):
            info_parts.append(f"职位：{contact['position']}")
        if contact.get("corp_name"):
            info_parts.append(f"企业：{contact['corp_name']}")

        return "\n".join(info_parts)


user_service = UserService()
