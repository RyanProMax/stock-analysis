"""
LLM 封装模块
提供统一的 LLM 接口，支持多种 LLM 提供商
"""

import os
from abc import ABC, abstractmethod
from typing import List, Optional, Union
from enum import Enum

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam


class LLMProvider(Enum):
    """支持的 LLM 提供商"""

    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    ZHIPU = "zhipu"


class BaseLLM(ABC):
    """LLM 基类"""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        pass


class OpenAILLM(BaseLLM):
    """OpenAI 兼容的 LLM 实现（支持 OpenAI、DeepSeek 等）"""

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
    ):
        """初始化 OpenAI LLM

        Args:
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
        """
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        if not self.client:
            raise ValueError("LLM 客户端未初始化")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return response.choices[0].message.content


class LLMFactory:
    """LLM 工厂类"""

    @staticmethod
    def create_llm(
        provider: Union[str, LLMProvider],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ) -> BaseLLM:
        """创建 LLM 实例

        Args:
            provider: LLM 提供商
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            LLM 实例
        """
        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())

        # 根据环境变量或默认值获取配置
        if provider == LLMProvider.DEEPSEEK:
            api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
            base_url = base_url or "https://api.deepseek.com/v1"
            model = model or "deepseek-chat"
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

    def __init__(self, default_provider: Optional[Union[str, LLMProvider]] = None):
        """初始化 LLM 管理器

        Args:
            default_provider: 默认 LLM 提供商
        """
        self.default_provider = default_provider or LLMProvider.DEEPSEEK
        self.llm = None
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

    def switch_provider(
        self,
        provider: Union[str, LLMProvider],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """切换 LLM 提供商

        Args:
            provider: 新的 LLM 提供商
            api_key: API 密钥
            base_url: API 基础 URL
            model: 模型名称
        """
        self.default_provider = provider
        try:
            self.llm = LLMFactory.create_llm(
                provider=provider, api_key=api_key, base_url=base_url, model=model
            )
            self.is_available = True
            print(f"[LLM] 成功切换到 {provider}")
        except Exception as e:
            self.is_available = False
            print(f"[LLM] 切换失败: {str(e)}")

    async def chat_completion(
        self,
        messages: List[ChatCompletionMessageParam],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """执行聊天完成"""
        if not self.is_available or not self.llm:
            raise RuntimeError("LLM 未初始化或不可用")

        return await self.llm.chat_completion(
            messages=messages, temperature=temperature, max_tokens=max_tokens, **kwargs
        )
