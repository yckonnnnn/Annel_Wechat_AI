import requests
from typing import Optional, Dict, Any
from wecom.token_manager import token_manager
from config import wecom_config, app_config


class MessageSender:
    """企业微信消息发送服务"""

    # 发送应用消息 API
    SEND_MESSAGE_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
    # 代员工发消息给外部联系人 API（企业群发单聊模式）
    SEND_MSG_ON_BEHALF_URL = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/add_msg_template"

    def send_text_message(
        self,
        to_user: str,
        content: str,
        agent_id: Optional[str] = None
    ) -> bool:
        """
        发送文本消息给客户

        Args:
            to_user: 接收者的 userid（外部联系人用 external_userid）
            content: 消息内容
            agent_id: 应用 ID（默认使用配置的 agent_id）

        Returns:
            发送成功返回 True
        """
        token = token_manager.get_token()
        if not token:
            print("[MessageSender] 无法获取 access_token")
            return False

        agent_id = agent_id or wecom_config["agent_id"]

        payload = {
            "touser": to_user,
            "msgtype": "text",
            "agentid": int(agent_id),
            "text": {
                "content": content
            },
            "safe": 0
        }

        params = {"access_token": token}

        try:
            response = requests.post(
                self.SEND_MESSAGE_URL,
                params=params,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") == 0:
                print(f"[MessageSender] 消息发送成功：{to_user}")
                return True
            else:
                print(f"[MessageSender] 消息发送失败：{data}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"[MessageSender] 请求失败：{e}")
            return False

    def send_markdown_message(
        self,
        to_user: str,
        content: str,
        agent_id: Optional[str] = None
    ) -> bool:
        """
        发送 Markdown 消息（仅支持部分语法）

        Args:
            to_user: 接收者的 userid
            content: Markdown 格式的消息内容

        Returns:
            发送成功返回 True
        """
        token = token_manager.get_token()
        if not token:
            return False

        agent_id = agent_id or wecom_config["agent_id"]

        payload = {
            "touser": to_user,
            "msgtype": "markdown",
            "agentid": int(agent_id),
            "markdown": {
                "content": content
            }
        }

        params = {"access_token": token}

        try:
            response = requests.post(
                self.SEND_MESSAGE_URL,
                params=params,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return data.get("errcode") == 0

        except requests.exceptions.RequestException as e:
            print(f"[MessageSender] 请求失败：{e}")
            return False


    def send_external_text_message(
        self,
        sender_userid: str,
        external_userid: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        代员工发文本消息给外部联系人（场景2）

        Args:
            sender_userid: 员工的 userid（代发者）
            external_userid: 外部联系人的 userid（接收者）
            content: 消息内容

        Returns:
            {"success": bool, "errcode": int, "errmsg": str}
        """
        token = token_manager.get_token()
        if not token:
            return {"success": False, "errcode": -1, "errmsg": "无法获取 access_token"}

        payload = {
            "chat_type": "single",
            "external_userid": [external_userid],
            "sender": sender_userid,
            "text": {
                "content": content,
            },
        }

        params = {"access_token": token}

        try:
            response = requests.post(
                self.SEND_MSG_ON_BEHALF_URL,
                params=params,
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") == 0:
                print(f"[MessageSender] 代发消息成功：{sender_userid} → {external_userid}")
                return {"success": True, "errcode": 0, "errmsg": "ok"}
            else:
                print(f"[MessageSender] 代发消息失败：{data}")
                return {"success": False, "errcode": data.get("errcode"), "errmsg": data.get("errmsg", "")}

        except requests.exceptions.RequestException as e:
            print(f"[MessageSender] 代发请求失败：{e}")
            return {"success": False, "errcode": -1, "errmsg": str(e)}


# 全局单例
message_sender = MessageSender()
