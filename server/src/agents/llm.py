"""
LLM 封装模块 - 仅保留流式接口
"""

import os
from typing import List, Optional, Union, AsyncGenerator
from enum import Enum

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam

DEFAULT_TEMPERATURE = 1.0


class LLMProvider(Enum):
    """支持的 LLM 提供商"""

    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    ZHIPU = "zhipu"


class OpenAILLM:
    """OpenAI 兼容的 LLM 实现"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat_completion_stream(
        self,
        messages: List[ChatCompletionMessageParam],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class LLMFactory:
    """LLM 工厂类"""

    @staticmethod
    def create_llm(
        provider: Union[str, LLMProvider],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> OpenAILLM:
        """创建 LLM 实例"""
        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())

        if provider == LLMProvider.DEEPSEEK:
            api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
            base_url = base_url or "https://api.deepseek.com"
            model = model or "deepseek-reasoner"
        elif provider == LLMProvider.OPENAI:
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            model = model or "gpt-3.5-turbo"
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")

        if not api_key:
            raise ValueError(f"未找到 {provider} 的 API 密钥")

        return OpenAILLM(api_key=api_key, base_url=base_url, model=model, **kwargs)


class LLMManager:
    """LLM 管理器"""

    def __init__(self, default_provider: Union[str, LLMProvider] = LLMProvider.DEEPSEEK):
        self.default_provider = default_provider
        self.llm: Optional[OpenAILLM] = None
        self.is_available = False
        self._initialize_llm()

    def _initialize_llm(self):
        """初始化默认 LLM"""
        try:
            self.llm = LLMFactory.create_llm(self.default_provider)
            self.is_available = True
            provider_name = (
                self.default_provider.value
                if isinstance(self.default_provider, LLMProvider)
                else self.default_provider
            )
            print(f"[LLM] 成功初始化 {provider_name} LLM")
        except Exception as e:
            self.is_available = False
            print(f"[LLM] 初始化失败: {str(e)}")

    async def chat_completion_stream(
        self,
        messages: List[ChatCompletionMessageParam],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """执行流式聊天完成"""
        if not self.is_available or not self.llm:
            raise RuntimeError("LLM 未初始化或不可用")

        assert self.llm is not None  # Type narrowing for type checker

        async for chunk in self.llm.chat_completion_stream(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            yield chunk
