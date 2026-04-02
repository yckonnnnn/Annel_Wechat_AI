import json
import os
import time
from pathlib import Path
from typing import Optional, List, Dict

class ConversationStore:
    """
    会话存储服务 - 保存客户对话历史

    数据结构：
    data/
    └── conversations/
        ├── {external_userid}.json
        └── {external_userid}.json

    每个客户一个 JSON 文件，包含对话列表
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.conv_dir = self.data_dir / "conversations"
        self.conv_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, external_userid: str) -> Path:
        """获取客户对话文件路径"""
        # 文件名可能包含特殊字符，用 base64 编码
        import base64
        safe_name = base64.urlsafe_b64encode(external_userid.encode()).decode().rstrip('=')
        return self.conv_dir / f"{safe_name}.json"

    def add_message(self, external_userid: str, msg_type: str, content: str,
                    from_user: str = "user", extra: dict = None) -> dict:
        """
        添加一条消息到对话历史

        Args:
            external_userid: 客户的外部联系人 ID
            msg_type: 消息类型 (text, image, event 等)
            content: 消息内容
            from_user: "user" 表示客户发的，"system" 表示系统回复的
            extra: 额外信息（如事件类型、图片 URL 等）

        Returns:
            添加的消息记录
        """
        file_path = self._get_file_path(external_userid)

        # 加载现有对话
        messages = []
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                messages = data.get('messages', [])

        # 创建新消息记录
        msg_record = {
            "timestamp": int(time.time()),
            "from": from_user,
            "type": msg_type,
            "content": content,
        }
        if extra:
            msg_record["extra"] = extra

        messages.append(msg_record)

        # 保存
        data = {
            "external_userid": external_userid,
            "last_updated": int(time.time()),
            "message_count": len(messages),
            "messages": messages
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return msg_record

    def get_messages(self, external_userid: str, limit: int = 50) -> List[dict]:
        """获取客户的对话历史"""
        file_path = self._get_file_path(external_userid)
        if not file_path.exists():
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            messages = data.get('messages', [])
            return messages[-limit:]  # 返回最近 N 条

    def get_conversation_summary(self, external_userid: str) -> Optional[dict]:
        """获取对话摘要信息"""
        file_path = self._get_file_path(external_userid)
        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {
                "external_userid": data.get("external_userid"),
                "last_updated": data.get("last_updated"),
                "message_count": data.get("message_count"),
                "first_message_time": data.get("messages", [{}])[0].get("timestamp") if data.get("messages") else None
            }

    def list_all_customers(self) -> List[dict]:
        """列出所有有对话记录的客户"""
        customers = []
        for file_path in self.conv_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                customers.append({
                    "external_userid": data.get("external_userid"),
                    "message_count": data.get("message_count"),
                    "last_updated": data.get("last_updated")
                })
        return sorted(customers, key=lambda x: x.get('last_updated', 0), reverse=True)

    def clear_conversation(self, external_userid: str):
        """清空某个客户的对话历史"""
        file_path = self._get_file_path(external_userid)
        if file_path.exists():
            file_path.unlink()


# 全局单例
conversation_store = ConversationStore()
cs = conversation_store  # 别名用于导入
