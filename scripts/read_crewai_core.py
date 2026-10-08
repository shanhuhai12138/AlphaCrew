"""Read core CrewAI source files to understand the framework architecture."""
import os

base = r"C:\Users\Violet\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages\crewai"

# List all .py files in top-level and key subpackages
target_dirs = [
    base,
    os.path.join(base, "agents"),
    os.path.join(base, "memory"),
    os.path.join(base, "tools"),
    os.path.join(base, "rag"),
    os.path.join(base, "mcp"),
    os.path.join(base, "knowledge"),
    os.path.join(base, "security"),
    os.path.join(base, "state"),
    os.path.join(base, "core"),
]

for d in target_dirs:
    if os.path.isdir(d):
        rel = os.path.relpath(d, base)
        rel = "." if rel == "." else rel
        print(f"===== DIR: {rel} =====")
        for f in sorted(os.listdir(d)):
            if f.endswith(".py"):
                print(" ", f)
        print()
