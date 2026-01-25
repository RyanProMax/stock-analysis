"""
LLM 封装模块 - 支持 DeepSeek reasoning_content
"""

import os
from typing import List, Optional, Union, AsyncGenerator, Tuple
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

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        provider: LLMProvider = LLMProvider.OPENAI,
    ):
        self.model = model
        self.provider = provider
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat_completion_stream(
        self,
        messages: List[ChatCompletionMessageParam],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        流式聊天完成

        Returns:
            AsyncGenerator[Tuple[str, Optional[str]], None]:
                - 第一个元素: content 文本片段
                - 第二个元素: reasoning_content 文本片段（仅 DeepSeek），其他模型为 None
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        async for chunk in stream:
            if not chunk.choices:
                continue

            delta = chunk.choices[0].delta

            # DeepSeek 使用 reasoning_content 字段返回推理过程
            if self.provider == LLMProvider.DEEPSEEK:
                reasoning = getattr(delta, "reasoning_content", None)
                content = delta.content

                # 优先返回 reasoning_content，标记为 "thinking"
                if reasoning:
                    yield ("", reasoning)
                # 然后返回正常 content
                elif content:
                    yield (content, "")
            else:
                # 其他模型只返回 content
                if delta.content:
                    yield (delta.content, "")


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

        return OpenAILLM(
            api_key=api_key, base_url=base_url, model=model, provider=provider, **kwargs
        )


class LLMManager:
    """LLM 管理器"""

    def __init__(self, default_provider: Union[str, LLMProvider] = LLMProvider.DEEPSEEK):
        self.default_provider = default_provider
        self.llm = self._initialize_llm()

    def _initialize_llm(self) -> OpenAILLM:
        """初始化默认 LLM，失败时直接抛出异常"""
        provider_name = (
            self.default_provider.value
            if isinstance(self.default_provider, LLMProvider)
            else self.default_provider
        )
        try:
            llm = LLMFactory.create_llm(self.default_provider)
            print(f"[LLM] 成功初始化 {provider_name} LLM")
            return llm
        except Exception as e:
            raise RuntimeError(f"LLM 初始化失败 ({provider_name}): {str(e)}") from e

    async def chat_completion_stream(
        self,
        messages: List[ChatCompletionMessageParam],
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
        """
        执行流式聊天完成

        Returns:
            AsyncGenerator[Tuple[str, Optional[str]], None]:
                - 第一个元素: content 文本片段
                - 第二个元素: reasoning_content 文本片段（仅 DeepSeek），其他模型为 None
        """
        async for chunk in self.llm.chat_completion_stream(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        ):
            yield chunk
