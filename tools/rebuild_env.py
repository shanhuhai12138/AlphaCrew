"""一次性修复脚本：重建 D:\\Alphacrew\\.env 为干净的 UTF-8（无 BOM）。

背景：PowerShell 5.1 用 Get-Content/Set-Content 改 .env 时，把无 BOM 的 UTF-8
文件按系统 GBK 误读再写回，导致中文注释乱码 + 加了 BOM。
但纯 ASCII 的 KEY=VALUE 行完好，本脚本把它们抢救出来，重建干净文件。
"""
import re

SRC = r"D:\Alphacrew\.env"

# 1. 抢救现有 KEY=VALUE（ASCII 行完好，中文注释行可能已损坏 → 全部丢弃重写）
raw = open(SRC, "rb").read()
if raw[:3] == b"\xef\xbb\xbf":
    raw = raw[3:]
text = raw.decode("utf-8", errors="replace")
kv = {}
for line in text.splitlines():
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", line)
    if m:
        kv[m.group(1)] = m.group(2)

g = lambda k, d="": kv.get(k, d)

content = f"""# ===================== AlphaCrew 配置 =====================
# UTF-8（无 BOM）。填入你的密钥。请勿用 PowerShell 的 Get/Set-Content 编辑本文件。

# ---------- LLM 模型路由（默认值，前端 UI 可覆盖）----------
ALPHACREW_LLM_PROVIDER={g('ALPHACREW_LLM_PROVIDER','deepseek')}
ALPHACREW_LLM_MODEL={g('ALPHACREW_LLM_MODEL','deepseek-chat')}

# --- DeepSeek ---
DEEPSEEK_API_KEY={g('DEEPSEEK_API_KEY')}
DEEPSEEK_BASE_URL={g('DEEPSEEK_BASE_URL','https://api.deepseek.com/v1')}

# --- Agnes（Sapiens AI，OpenAI 兼容协议）---
AGNES_API_KEY={g('AGNES_API_KEY','your-agnes-key')}
AGNES_BASE_URL={g('AGNES_BASE_URL','https://api.agnes-ai.cn/v1')}

# --- OpenAI（可选备用）---
OPENAI_API_KEY={g('OPENAI_API_KEY')}
OPENAI_BASE_URL={g('OPENAI_BASE_URL','https://api.openai.com/v1')}

# 规划器/写手用较强模型，审稿/守护用轻量模型可降本
ALPHACREW_PLANNER_MODEL={g('ALPHACREW_PLANNER_MODEL')}
ALPHACREW_CRITIC_MODEL={g('ALPHACREW_CRITIC_MODEL')}

# ---------- 金融数据 ----------
ALPHA_VANTAGE_API_KEY={g('ALPHA_VANTAGE_API_KEY','your-alphavantage-key')}
# Yahoo Finance 无需 key，留空即可

# ---------- 向量库 / 缓存 ----------
QDRANT_URL={g('QDRANT_URL','http://localhost:6333')}
QDRANT_API_KEY={g('QDRANT_API_KEY')}
QDRANT_COLLECTION={g('QDRANT_COLLECTION','alphacrew_financial')}
REDIS_URL={g('REDIS_URL','redis://localhost:6379/0')}

# ---------- 嵌入模型（本地 3060 可跑 bge-small，或改用 API 嵌入）----------
EMBEDDING_PROVIDER={g('EMBEDDING_PROVIDER','local')}
EMBEDDING_MODEL={g('EMBEDDING_MODEL','BAAI/bge-small-zh-v1.5')}

# ---------- 可观测（可选）----------
LANGFUSE_PUBLIC_KEY={g('LANGFUSE_PUBLIC_KEY')}
LANGFUSE_SECRET_KEY={g('LANGFUSE_SECRET_KEY')}
LANGFUSE_HOST={g('LANGFUSE_HOST','http://localhost:3001')}

# ---------- 服务 ----------
BACKEND_HOST={g('BACKEND_HOST','0.0.0.0')}
BACKEND_PORT={g('BACKEND_PORT','8000')}
FRONTEND_PORT={g('FRONTEND_PORT','5173')}
"""

# UTF-8 无 BOM（open 默认不加 BOM），LF 换行
open(SRC, "w", encoding="utf-8", newline="\n").write(content)

# 验证：首 3 字节不应是 BOM，中文应正常
chk = open(SRC, "rb").read()
print("首3字节:", chk[:3].hex())
print("有 BOM ?", chk[:3] == b"\xef\xbb\xbf")
rescued = sorted(kv.keys())
print("抢救到的 KEY:", rescued)
print("DEEPSEEK_API_KEY 保留?", "DEEPSEEK_API_KEY" in kv and bool(kv.get("DEEPSEEK_API_KEY")))
