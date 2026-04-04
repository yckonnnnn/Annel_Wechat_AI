"""
企业微信会话内容存档 SDK 封装（subprocess 模式）

因 Python ctypes 调用 libWeWorkFinanceSdk_C.so 网络栈时 segfault，
改用两个 C helper 程序，通过 subprocess 调用：
  - chat_puller:     拉取加密消息 JSON
  - decrypt_helper:  通过 stdin 接收 AES 密钥（避免 null byte 问题），解密消息体

流程：
  1. chat_puller  → 加密消息 JSON
  2. Python RSA 解密 encrypt_random_key → AES 密钥（raw bytes）
  3. decrypt_helper（stdin=AES密钥）→ 明文 JSON
"""

import base64
import json
import subprocess
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

SDK_DIR          = Path(__file__).parent / "sdk" / "C_sdk"
CHAT_PULLER      = str(SDK_DIR / "chat_puller")
DECRYPT_HELPER   = str(SDK_DIR / "decrypt_helper")
PRIVATE_KEY_PATH = str(Path(__file__).parent / "sdk" / "private_key.pem")


class FinanceSDK:
    """企业微信会话内容存档 SDK（subprocess 模式）"""

    def __init__(self, corp_id: str, secret: str):
        self.corp_id = corp_id
        self.secret = secret
        self._private_key = None
        self._check_binaries()
        self._load_private_key()

    def _check_binaries(self):
        for p in [CHAT_PULLER, DECRYPT_HELPER]:
            if not Path(p).exists():
                raise FileNotFoundError(f"SDK 工具未找到: {p}")
        if not Path(PRIVATE_KEY_PATH).exists():
            raise FileNotFoundError(f"RSA 私钥未找到: {PRIVATE_KEY_PATH}")

    def _load_private_key(self):
        with open(PRIVATE_KEY_PATH, "rb") as f:
            self._private_key = serialization.load_pem_private_key(f.read(), password=None)
        print("[FinanceSDK] RSA 私钥加载成功")

    def _rsa_decrypt(self, encrypted_b64: str) -> bytes:
        """RSA 解密 base64 编码的加密内容，返回 raw bytes"""
        return self._private_key.decrypt(
            base64.b64decode(encrypted_b64),
            padding.PKCS1v15(),
        )

    def _decrypt_msg(self, aes_key: bytes, encrypt_chat_msg: str) -> Optional[dict]:
        """通过 decrypt_helper（stdin 传 AES 密钥）解密消息体"""
        try:
            result = subprocess.run(
                [DECRYPT_HELPER, encrypt_chat_msg],
                input=aes_key,           # 二进制通过 stdin 传入
                capture_output=True,
                cwd=str(SDK_DIR),
                timeout=10,
            )
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout.decode("utf-8"))
            else:
                err = result.stderr.decode("utf-8", errors="replace").strip()
                print(f"[FinanceSDK] decrypt_helper 失败: {err}")
        except Exception as e:
            print(f"[FinanceSDK] 解密异常: {e}")
        return None

    def get_chat_data(self, seq: int = 0, limit: int = 100, timeout: int = 30) -> list:
        """
        拉取并解密会话存档消息

        Args:
            seq:   从哪个序号开始拉（0=从头，增量拉取传上次 max_seq+1）
            limit: 每次最多拉取条数（最大 1000）

        Returns:
            解密后的消息列表，每条消息是 dict，附带 _seq 字段
        """
        # 1. 调 C helper 拉取加密消息
        try:
            result = subprocess.run(
                [CHAT_PULLER, self.corp_id, self.secret, str(seq), str(limit)],
                capture_output=True,
                cwd=str(SDK_DIR),
                timeout=timeout,
            )
            raw = result.stdout.decode("utf-8").strip()
            if result.returncode != 0 or not raw:
                err = result.stderr.decode("utf-8").strip()
                print(f"[FinanceSDK] chat_puller 失败: {err}")
                return []
        except subprocess.TimeoutExpired:
            print("[FinanceSDK] chat_puller 超时")
            return []

        data = json.loads(raw)
        if data.get("errcode", 0) != 0:
            print(f"[FinanceSDK] 接口错误: {data}")
            return []

        chat_data_list = data.get("chatdata", [])
        print(f"[FinanceSDK] 拉取到 {len(chat_data_list)} 条加密消息")

        # 2. 逐条解密
        messages = []
        for item in chat_data_list:
            seq_val      = item.get("seq", 0)
            pub_key_ver  = item.get("publickey_ver", 0)
            try:
                aes_key = self._rsa_decrypt(item["encrypt_random_key"])
                msg = self._decrypt_msg(aes_key, item["encrypt_chat_msg"])
                if msg:
                    msg["_seq"] = seq_val
                    messages.append(msg)
                else:
                    print(f"[FinanceSDK] 解密失败 seq={seq_val} pubkey_ver={pub_key_ver}")
            except Exception as e:
                print(f"[FinanceSDK] 异常 seq={seq_val}: {e}")

        return messages


_sdk_instance: Optional[FinanceSDK] = None


def get_finance_sdk(corp_id: str, secret: str) -> FinanceSDK:
    global _sdk_instance
    if _sdk_instance is None:
        _sdk_instance = FinanceSDK(corp_id, secret)
    return _sdk_instance
