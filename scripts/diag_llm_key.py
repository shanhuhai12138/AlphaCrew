"""诊断 get_llm 的 api_key 丢失点：_resolve → settings → extra。"""
import sys
sys.path.insert(0, ".")
import os

from core.llm.llm_router import _resolve, settings

print("CWD:", os.getcwd())
print("os.environ DEEPSEEK_API_KEY:", "yes" if os.environ.get("DEEPSEEK_API_KEY") else "NO")
print("settings.deepseek_api_key:", (settings.deepseek_api_key or "")[:8] + "..." if settings.deepseek_api_key else "EMPTY")
print("settings.deepseek_base_url:", settings.deepseek_base_url)

lm, extra = _resolve("deepseek", "deepseek-chat")
print("_resolve ->", lm)
print("extra keys:", list(extra.keys()))
print("extra api_key:", (extra.get("api_key", "")[:8] + "...") if extra.get("api_key") else "MISSING")
print("extra base_url:", extra.get("base_url"))
