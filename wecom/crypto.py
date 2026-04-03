import base64
import hashlib
import random
import struct
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from typing import Tuple, Dict, Any


class WeComCrypto:
    """企业微信消息加解密"""

    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        self.token = token
        self.corp_id = corp_id
        # AES Key 是 base64 编码的 32 字节
        self.aes_key = base64.b64decode(encoding_aes_key + "=" * (4 - len(encoding_aes_key) % 4))

    def verify_signature(self, timestamp: str, nonce: str, echostr: str, signature: str) -> bool:
        """
        验证回调签名（GET 请求验证）

        企业微信会用 SHA1 校验：sha1(token, timestamp, nonce, echostr)
        """
        values = [self.token, timestamp, nonce, echostr]
        values.sort()
        sha1 = hashlib.sha1("".join(values).encode("utf-8"))
        return sha1.hexdigest() == signature

    def _decrypt_aes(self, data: bytes) -> bytes:
        """企业微信标准AES-CBC解密：IV固定为aes_key前16字节"""
        iv = self.aes_key[:16]
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(data) + decryptor.finalize()
        pad_len = decrypted[-1]
        return decrypted[:-pad_len]

    def decrypt_echostr(self, echostr: str) -> str:
        """
        解密 GET 请求的 echostr
        返回解密后的字符串用于验证
        """
        decrypted = self._decrypt_aes(base64.b64decode(echostr))
        # 格式：16 字节随机前缀 + 4 字节消息长度 + 消息内容 + corp_id
        msg_len = struct.unpack(">I", decrypted[16:20])[0]
        return decrypted[20:20 + msg_len].decode("utf-8")

    def decrypt_message(self, encrypt_msg: str) -> str:
        """
        解密 POST 请求的消息体
        返回解密后的 XML 字符串
        """
        # _decrypt_aes 已去除 padding，结果格式：16字节随机前缀 + 4字节消息长度 + 消息内容 + corp_id
        decrypted = self._decrypt_aes(base64.b64decode(encrypt_msg))

        msg_len = struct.unpack(">I", decrypted[16:20])[0]
        msg_content = decrypted[20:20 + msg_len].decode("utf-8")

        # 验证 receiveid
        receiveid = decrypted[20 + msg_len:].decode("utf-8")
        if receiveid != self.corp_id:
            raise ValueError(f"Invalid receiveid: {receiveid}")

        return msg_content

    def encrypt_message(self, message: str) -> str:
        """
        加密要返回给企业微信的消息
        """
        # 生成 16 字节随机前缀
        random_prefix = bytes([random.randint(0, 255) for _ in range(16)])

        # 消息内容
        msg_bytes = message.encode("utf-8")

        # 4 字节消息长度
        msg_len = struct.pack(">I", len(msg_bytes))

        # 拼接：随机前缀 + 长度 + 消息 + corp_id
        payload = random_prefix + msg_len + msg_bytes + self.corp_id.encode("utf-8")

        # PKCS7 padding
        pad_len = 32 - (len(payload) % 32)
        payload = payload + bytes([pad_len] * pad_len)

        # 企业微信标准：IV固定为aes_key前16字节
        iv = self.aes_key[:16]

        # 加密
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(payload) + encryptor.finalize()

        # Base64 编码（无需prepend IV）
        return base64.b64encode(encrypted).decode("utf-8")


def verify_callback_signature(token: str, signature: str, timestamp: str, nonce: str, msg_encrypt: str) -> bool:
    """验证回调 URL 签名（用于 POST 请求）"""
    values = [token, timestamp, nonce, msg_encrypt]
    values.sort()
    sha1 = hashlib.sha1("".join(values).encode("utf-8"))
    return sha1.hexdigest() == signature
