"""LLM 路由层 — 用户可在前端 / .env 自选模型提供商。

面试考点：OpenAI 兼容多模型接入。
CrewAI 底层用 LiteLLM 做 provider 路由。本模块把 "provider + model" 抽象成
统一入口，支持 DeepSeek / Agnes / OpenAI 及任意 OpenAI 兼容端点，切换零成本。

设计要点：
- provider -> LiteLLM 前缀 + 是否需要自定义 base_url / api_key
- 规划器/写手可用强模型，审稿/守护可用轻量模型（降本），同一实例多槽位
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from crewai import LLM

from core.config import settings

# provider 名 -> (litellm 模型前缀, 是否用自定义 base_url, base_url 环境变量, key 环境变量)
PROVIDER_MAP = {
    "deepseek": ("deepseek", True, "DEEPSEEK_BASE_URL", "DEEPSEEK_API_KEY"),
    "openai":   ("openai",   True, "OPENAI_BASE_URL",   "OPENAI_API_KEY"),
    "agnes":    ("openai",   True, "AGNES_BASE_URL",    "AGNES_API_KEY"),
    # 任意 OpenAI 兼容端点走 openai 前缀 + 自定义 base_url
}

# 允许用户直接传完整 litellm 模型名（如 "anthropic/claude-3"）的白名单前缀
LITELLM_PREFIXES = {"deepseek", "openai", "anthropic", "groq", "google", "ollama"}


def _resolve(provider: str, model: str) -> tuple[str, dict]:
    """把 provider+model 解析为 (litellm_model, extra_kwargs)。

    注意：base_url / api_key 优先读进程环境变量（便于测试注入），
    读不到再 fallback 到 settings（它才是真正解析 .env 的对象）。
    这样干净终端下也能正确加载 .env 里的 Agnes/DeepSeek 地址。
    """
    provider = (provider or settings.llm_provider).lower()

    if model and any(model.startswith(p + "/") for p in LITELLM_PREFIXES):
        # 用户已经给了完整 litellm 名
        return model, {}

    if provider in PROVIDER_MAP:
        prefix, use_base, base_env, key_env = PROVIDER_MAP[provider]
        litellm_model = f"{prefix}/{model}"
        extra: dict = {}

        # base_url：环境变量 → settings 兜底
        base_url = os.environ.get(base_env, "")
        if not base_url:
            # 例如 base_env="AGNES_BASE_URL" → settings.agnes_base_url（小写）
            base_url = str(getattr(settings, base_env.lower(), ""))
        if base_url:
            extra["base_url"] = base_url

        # api_key：环境变量 → settings 兜底
        api_key = os.environ.get(key_env, "")
        if not api_key:
            attr = key_env.lower()  # 例如 "AGNES_API_KEY" → settings.agnes_api_key
            api_key = str(getattr(settings, attr, ""))
        if api_key:
            extra["api_key"] = api_key
        return litellm_model, extra

    # 回退：当作 openai 兼容
    litellm_model = f"openai/{model}"
    return litellm_model, {}


@lru_cache(maxsize=32)
def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
) -> LLM:
    """返回一个 crewai.LLM 实例。带缓存避免重复建连接。"""
    litellm_model, extra = _resolve(provider or "", model or settings.llm_model)
    extra.setdefault("temperature", temperature)
    return LLM(model=litellm_model, **extra)


def get_slot_llm(slot: str, provider: Optional[str] = None, model: Optional[str] = None) -> LLM:
    """按角色槽位取 LLM。
    slot 可选: planner / critic / general。规划器与审稿可用不同模型档位。
    """
    if provider is None and model is None:
        if slot == "planner" and settings.planner_model:
            # 解析 planner_model（形如 "provider/model" 或纯 model 名）
            if "/" in settings.planner_model and settings.planner_model.split("/")[0] in PROVIDER_MAP:
                p, m = settings.planner_model.split("/", 1)
                return get_llm(p, m, temperature=0.0)
            model = settings.planner_model
        elif slot == "critic" and settings.critic_model:
            if "/" in settings.critic_model and settings.critic_model.split("/")[0] in PROVIDER_MAP:
                p, m = settings.critic_model.split("/", 1)
                return get_llm(p, m, temperature=0.0)
            model = settings.critic_model
    return get_llm(provider, model)
