"""去掉 .env 的 BOM（PS5.1 Set-Content 残留），保证 pydantic-settings 读干净。"""
from pathlib import Path

p = Path(r"D:\Alphacrew\.env")
raw = p.read_bytes()
if raw[:3] == b"\xef\xbb\xbf":
    p.write_bytes(raw[3:])
    print("BOM removed")
else:
    print("no BOM, untouched")
