"""CLI エントリポイント。

使い方:
  python -m keep_bot login                 # 初回ログイン(手動)
  python -m keep_bot say "メモ 牛乳を買う"    # キーワード判定→追加/検索を実行
  python -m keep_bot add "牛乳を買う"        # メモを直接追加
  python -m keep_bot search "牛乳"           # メモを直接検索
"""

import sys

from . import keep_client
from .auth import login_and_save_state
from .trigger import Intent, parse


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]
    arg = " ".join(sys.argv[2:])

    if command == "login":
        login_and_save_state()
        return

    if command == "add":
        keep_client.add_note(arg)
        print("メモを追加しました。")
        return

    if command == "search":
        notes = keep_client.search_notes(arg)
        if not notes:
            print("該当するメモは見つかりませんでした。")
        for n in notes:
            print(f"- {n.title}: {n.text}")
        return

    if command == "say":
        parsed = parse(arg)
        if parsed.intent == Intent.ADD:
            keep_client.add_note(parsed.content)
            print(f"メモを追加しました: {parsed.content}")
        elif parsed.intent == Intent.SEARCH:
            notes = keep_client.search_notes(parsed.content)
            if not notes:
                print("該当するメモは見つかりませんでした。")
            for n in notes:
                print(f"- {n.title}: {n.text}")
        else:
            print("「メモ」キーワードが検出されませんでした。")
        return

    print(f"不明なコマンドです: {command}")
    print(__doc__)


if __name__ == "__main__":
    main()
