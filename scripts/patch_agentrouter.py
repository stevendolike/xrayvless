
import re
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "ddgksf2013/Scripts/master/agentrouter_checkin.js"
)

OUTPUT = Path("dist/agentrouter_checkin.js")

def main():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "GitHub-Actions-AgentRouter-Updater"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read().decode("utf-8")

    # 1. 在 CONFIG 前加入 Loon Script v2 參數讀取
    marker = "const CONFIG = {"

    if marker not in source:
        raise RuntimeError(
            "找不到 CONFIG 定義，上游腳本結構可能已變更。"
        )

    if "const LOON_ARGUMENT =" in source:
        raise RuntimeError(
            "上游腳本已包含 LOON_ARGUMENT，請檢查是否需要更新補丁。"
        )

    source = source.replace(
        marker,
        '''const LOON_ARGUMENT =
  typeof $argument !== "undefined" &&
  $argument &&
  typeof $argument === "object"
    ? $argument
    : {};

const CONFIG = {''',
        1,
    )

    # 2. 將空白 account 改為讀取 Loon 傳入的帳密
    pattern = r'(?m)^([ \t]*)account:\s*""\s*,.*$'

    replacement = (
        r'\1account: ('
        'typeof LOON_ARGUMENT.AgentRouterEmail === "string" && '
        'typeof LOON_ARGUMENT.AgentRouterPassword === "string" && '
        'LOON_ARGUMENT.AgentRouterEmail.trim() && '
        'LOON_ARGUMENT.AgentRouterPassword'
        ') ? '
        '`${LOON_ARGUMENT.AgentRouterEmail.trim()}#'
        '${LOON_ARGUMENT.AgentRouterPassword}` : "",'
    )

    source, count = re.subn(pattern, replacement, source)

    if count != 1:
        raise RuntimeError(
            f"預期修改一個 CONFIG.account，實際匹配 {count} 個；"
            "請檢查上游腳本是否已變更。"
        )

    # 3. 輸出修改後的腳本
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")

    print(f"Updated: {OUTPUT}")
    print("Loon Script v2 account arguments enabled.")

if __name__ == "__main__":
    main()
