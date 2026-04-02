import requests
import time
from typing import Optional
from backend.core_config import wecom_config


class TokenManager:
    """企业微信 Access Token 管理器"""

    # 获取 access_token 的 API 端点
    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"

    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0
        self._lock = False

    def get_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        获取 access_token

        Args:
            force_refresh: 是否强制刷新（默认使用缓存）

        Returns:
            access_token 字符串，失败返回 None
        """
        # 检查缓存是否有效（提前 5 分钟刷新）
        if not force_refresh and self._token and time.time() < self._expires_at - 300:
            return self._token

        if self._lock:
            # 防止并发请求
            time.sleep(0.1)
            return self.get_token(force_refresh)

        self._lock = True
        try:
            return self._fetch_token()
        finally:
            self._lock = False

    def _fetch_token(self) -> Optional[str]:
        """从企业微信 API 获取 access_token"""
        params = {
            "corpid": wecom_config["corp_id"],
            "corpsecret": wecom_config["secret"]
        }

        try:
            response = requests.get(self.TOKEN_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("errcode") == 0:
                self._token = data["access_token"]
                # API 返回的 expires_in 是 7200 秒（2 小时）
                self._expires_at = time.time() + data.get("expires_in", 7200)
                print(f"[TokenManager] 成功获取 access_token，过期时间：{self._expires_at}")
                return self._token
            else:
                print(f"[TokenManager] 获取 token 失败：{data}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"[TokenManager] 请求失败：{e}")
            return None

    def invalidate(self):
        """使缓存失效（用于错误处理时）"""
        self._token = None
        self._expires_at = 0


# 全局单例
token_manager = TokenManager()
