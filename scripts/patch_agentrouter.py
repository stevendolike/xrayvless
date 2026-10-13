
import re
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "ddgksf2013/Scripts/master/agentrouter_checkin.js"
)

OUTPUT = Path("Loon/scripts/agentrouter_checkin.js")


def main():
    request = urllib.request.Request(
        SOURCE_URL,
        headers={
            "User-Agent": "GitHub-Actions-AgentRouter-Updater"
        },
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        source = response.read().decode("utf-8-sig")

    # 1. 在 CONFIG 前加入 Loon Script v2 參數物件
    config_marker = "const CONFIG = {"

    if source.count(config_marker) != 1:
        raise RuntimeError(
            "找不到唯一的 CONFIG 定義；"
            "上游腳本可能已變更，請檢查補丁。"
        )

    if "const LOON_ARGUMENT =" in source:
        raise RuntimeError(
            "上游已包含 LOON_ARGUMENT，請檢查補丁是否需要更新。"
        )

    argument_code = """const LOON_ARGUMENT =
  typeof $argument !== "undefined" &&
  $argument &&
  typeof $argument === "object"
    ? $argument
    : {};

"""

    source = source.replace(
        config_marker,
        argument_code + config_marker,
        1,
    )

    # 2. 優先使用 Loon 插件傳入的帳號密碼
    function_pattern = r"function\s+collectAccounts\s*\(\s*\)\s*\{"

    match = re.search(function_pattern, source)

    if not match:
        raise RuntimeError(
            "找不到 collectAccounts()；"
            "上游腳本結構可能已變更。"
        )

    argument_override = r"""
  const loonEmail =
    typeof LOON_ARGUMENT.AgentRouterEmail === "string"
      ? LOON_ARGUMENT.AgentRouterEmail.trim()
      : "";

  const loonPassword =
    typeof LOON_ARGUMENT.AgentRouterPassword === "string"
      ? LOON_ARGUMENT.AgentRouterPassword
      : "";

  if (loonEmail && loonPassword) {
    log("已读取 Loon 插件参数");
    return [{
      name: "Loon账号",
      email: loonEmail,
      password: loonPassword
    }];
  }

"""

    source = (
        source[:match.end()]
        + argument_override
        + source[match.end():]
    )

    # 3. 輸出修改後的腳本
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(source, encoding="utf-8")

    print(f"Updated: {OUTPUT}")
    print("Loon Script v2 arguments injected.")


if __name__ == "__main__":
    main()
