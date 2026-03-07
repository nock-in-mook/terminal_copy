"""WT設定を自動更新: ライトテーマ・UDEV Gothic・タイトル維持"""
import json
import os

p = os.path.join(
    os.environ["LOCALAPPDATA"],
    "Packages", "Microsoft.WindowsTerminal_8wekyb3d8bbwe",
    "LocalState", "settings.json",
)
if not os.path.exists(p):
    print("WT settings not found")
    raise SystemExit

d = json.load(open(p, encoding="utf-8"))
df = d.setdefault("profiles", {}).setdefault("defaults", {})
changed = False

if df.get("colorScheme") != "One Half Light":
    df["colorScheme"] = "One Half Light"
    changed = True
if not df.get("suppressApplicationTitle"):
    df["suppressApplicationTitle"] = True
    changed = True
font = df.setdefault("font", {})
if font.get("face") != "UDEV Gothic":
    font["face"] = "UDEV Gothic"
    changed = True

if changed:
    json.dump(d, open(p, "w", encoding="utf-8"), indent=4, ensure_ascii=False)
    print("WT settings updated")
else:
    print("WT settings OK")
