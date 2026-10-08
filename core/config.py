"""AlphaCrew 全局配置 — 基于 pydantic-settings，从 .env 读取。"""
from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- LLM 路由 ----
    llm_provider: str = "deepseek"          # deepseek / agnes / openai / 自定义
    llm_model: str = "deepseek-chat"
    planner_model: str = ""                 # 留空则用 llm_model
    critic_model: str = ""

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    agnes_api_key: str = ""
    # Agnes 走 OpenAI 兼容协议；base_url 写到 /v1 为止，
    # SDK 会自动拼接 /chat/completions（不要把路径写进 base_url）
    agnes_base_url: str = "https://api.agnes-ai.cn/v1"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"

    # ---- 金融数据 ----
    alpha_vantage_api_key: str = ""

    # ---- 向量库 / 缓存 ----
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "alphacrew_financial"

    redis_url: str = "redis://localhost:6379/0"

    # ---- 嵌入 ----
    embedding_provider: str = "local"       # local / deepseek / openai
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    # ---- 可观测 ----
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "http://localhost:3001"

    # ---- 服务 ----
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000


settings = Settings()
