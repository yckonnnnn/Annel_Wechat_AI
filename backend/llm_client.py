from openai import OpenAI
from backend.core_config import llm_config


class LLMClient:
    """大模型调用客户端（兼容 OpenAI 格式）"""

    def __init__(self):
        self.client = OpenAI(
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
        )
        self.model = llm_config["model"]
        self.system_prompt = llm_config["system_prompt"]

    def chat(self, messages: list) -> str:
        """
        调用大模型生成回复

        Args:
            messages: OpenAI 格式的消息列表，每项为 {"role": "user"/"assistant", "content": "..."}

        Returns:
            模型生成的文本回复
        """
        # Mock 模式：直接返回固定话术（用于测试企微发送链路）
        if llm_config["mock_mode"]:
            return llm_config["mock_reply"]

        if not llm_config["api_key"]:
            return "（大模型 API Key 未配置，无法生成回复）"

        full_messages = [{"role": "system", "content": self.system_prompt}] + messages

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=1024,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            print(f"[LLMClient] 调用失败: {e}")
            return f"（AI 回复失败，请稍后重试）"


llm_client = LLMClient()
