import requests
from typing import Optional, Dict, Any
from wecom.token_manager import token_manager
from config import wecom_config


class UserService:
    """企业微信用户服务"""

    # 获取客户详情 API
    GET_EXTERNAL_CONTACT_URL = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get"

    def get_external_contact(self, external_userid: str) -> Optional[Dict[str, Any]]:
        """
        获取客户详情

        Args:
            external_userid: 客户的外部联系人 userid

        Returns:
            客户信息字典，失败返回 None
        """
        token = token_manager.get_token()
        if not token:
            print("[UserService] 无法获取 access_token")
            return None

        params = {
            "access_token": token,
            "external_userid": external_userid
        }

        try:
            response = requests.get(self.GET_EXTERNAL_CONTACT_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") == 0:
                return data.get("external_contact", {})
            else:
                print(f"[UserService] 获取客户详情失败：{data}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"[UserService] 请求失败：{e}")
            return None

    def get_contact_info(self, external_userid: str) -> str:
        """
        获取用于大模型的客户信息摘要

        Returns:
            格式化的客户信息字符串
        """
        contact = self.get_external_contact(external_userid)
        if not contact:
            return "未知用户"

        name = contact.get("name", "未知")
        gender = contact.get("gender", 0)
        gender_map = {0: "未知", 1: "男", 2: "女"}

        info_parts = [f"姓名：{name}", f"性别：{gender_map.get(gender, '未知')}"]

        # 其他可用信息
        if contact.get("position"):
            info_parts.append(f"职位：{contact['position']}")
        if contact.get("corp_name"):
            info_parts.append(f"企业：{contact['corp_name']}")

        return "\n".join(info_parts)


# 全局单例
user_service = UserService()
