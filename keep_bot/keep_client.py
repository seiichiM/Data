"""Playwright を使って Google Keep の画面を操作するクライアント。

公式APIが無いため、Web UI (keep.google.com) をヘッドレスブラウザで
直接操作して「メモの追加」「メモの検索」を行う。
"""

from dataclasses import dataclass

from playwright.sync_api import sync_playwright

from .auth import STATE_FILE, KEEP_URL, has_saved_state


class NotLoggedInError(RuntimeError):
    pass


@dataclass
class Note:
    title: str
    text: str


def _require_state() -> None:
    if not has_saved_state():
        raise NotLoggedInError(
            "ログイン状態が見つかりません。先に `python -m keep_bot login` を実行してください。"
        )


def add_note(text: str, title: str = "") -> None:
    """新しいメモを1件追加する。"""
    _require_state()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(STATE_FILE))
        page = context.new_page()
        page.goto(KEEP_URL)

        # 「メモを入力…」の新規作成ボックスを開く
        page.get_by_text("メモを入力…", exact=False).first.click()

        if title:
            title_box = page.get_by_placeholder("タイトル")
            if title_box.count() > 0:
                title_box.fill(title)

        page.get_by_placeholder("メモを入力…").fill(text)

        # ボックス外をクリックして保存を確定
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)

        browser.close()


def search_notes(query: str) -> list[Note]:
    """キーワードでメモを検索し、タイトルと本文の一覧を返す。"""
    _require_state()

    results: list[Note] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(STATE_FILE))
        page = context.new_page()
        page.goto(KEEP_URL)

        search_box = page.get_by_placeholder("検索")
        search_box.click()
        search_box.fill(query)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1500)

        note_cards = page.locator("[role='listitem']")
        count = note_cards.count()
        for i in range(count):
            card = note_cards.nth(i)
            title_el = card.locator("[aria-label*='タイトル'], .title")
            text_el = card.locator("[aria-label*='メモ'], .text")
            title = title_el.first.inner_text() if title_el.count() > 0 else ""
            text = text_el.first.inner_text() if text_el.count() > 0 else ""
            if title or text:
                results.append(Note(title=title, text=text))

        browser.close()

    return results
