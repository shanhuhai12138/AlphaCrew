"""Dump the full content of key CrewAI files for architecture study."""
import os

base = r"C:\Users\Violet\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages\crewai"

key_files = [
    os.path.join(base, "agents", "agent_builder", "base", "agent.py"),
    os.path.join(base, "crew.py"),
    os.path.join(base, "task.py"),
    os.path.join(base, "process.py"),
]

# Also try alternative layouts
alt = [
    os.path.join(base, "agent.py"),
    os.path.join(base, "agents", "base_agent.py"),
]

found = False
for f in key_files + alt:
    if os.path.exists(f):
        found = True
        print(f"\n\n########## {os.path.relpath(f, base)} ({os.path.getsize(f)} bytes) ##########")
        with open(f, encoding="utf-8") as fh:
            content = fh.read()
        print(content[:8000])

if not found:
    print("Key files not found at expected paths; dump directory listing instead:")
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "tests", "data")]
        for f in files:
            if f.endswith(".py"):
                rel = os.path.relpath(os.path.join(root, f), base)
                if any(k in rel for k in ("agent", "crew", "task", "process", "memory", "tool", "rag", "mcp", "knowledge", "security", "state")):
                    print(" ", rel, os.path.getsize(os.path.join(root, f)))
