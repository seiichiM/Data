import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from keep_bot.trigger import Intent, parse


def test_add_with_colon():
    result = parse("メモ: 牛乳を買う")
    assert result.intent == Intent.ADD
    assert result.content == "牛乳を買う"


def test_add_without_colon():
    result = parse("メモ 牛乳を買う")
    assert result.intent == Intent.ADD
    assert result.content == "牛乳を買う"


def test_search():
    result = parse("メモ検索 牛乳")
    assert result.intent == Intent.SEARCH
    assert result.content == "牛乳"


def test_search_with_wo():
    result = parse("メモを検索 牛乳")
    assert result.intent == Intent.SEARCH
    assert result.content == "牛乳"


def test_no_keyword():
    result = parse("こんにちは")
    assert result.intent == Intent.NONE


if __name__ == "__main__":
    test_add_with_colon()
    test_add_without_colon()
    test_search()
    test_search_with_wo()
    test_no_keyword()
    print("all tests passed")
