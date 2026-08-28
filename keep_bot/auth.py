"""Google Keep へのログインセッションを管理するモジュール。

Google Keep には個人アカウント向けの公式APIが無いため、Playwright による
ブラウザ操作でログインし、Cookie / storage_state をファイルに保存して
以降の操作(ヘッドレス実行)を再利用できるようにする。
"""

from pathlib import Path

from playwright.sync_api import sync_playwright

STATE_DIR = Path(__file__).resolve().parent.parent / ".keep_bot_state"
STATE_FILE = STATE_DIR / "auth_state.json"
KEEP_URL = "https://keep.google.com/"


def login_and_save_state() -> None:
    """手動ログイン用。ブラウザを表示してユーザーにログインしてもらい、
    ログイン後のセッション状態を STATE_FILE に保存する。

    2段階認証やパスワード入力はユーザー自身がブラウザ上で行う必要がある
    (自動入力は行わない)。
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(KEEP_URL)

        print("ブラウザでGoogleアカウントにログインしてください。")
        print(f"Keepのメモ一覧が表示されたら、このターミナルで Enter キーを押してください。")
        input()

        context.storage_state(path=str(STATE_FILE))
        browser.close()

    print(f"ログイン状態を保存しました: {STATE_FILE}")


def has_saved_state() -> bool:
    return STATE_FILE.exists()
