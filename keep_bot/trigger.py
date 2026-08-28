"""「メモ」というキーワードを含む文章から、Keep操作の意図を判定するモジュール。

対応パターン:
  - "メモ 買い物リストを書く"      -> 追加: "買い物リストを書く"
  - "メモ: 買い物リストを書く"     -> 追加: "買い物リストを書く"
  - "メモ検索 買い物"             -> 検索: "買い物"
  - "メモを検索 買い物"           -> 検索: "買い物"
"""

import re
from dataclasses import dataclass
from enum import Enum, auto


class Intent(Enum):
    ADD = auto()
    SEARCH = auto()
    NONE = auto()


@dataclass
class ParsedCommand:
    intent: Intent
    content: str = ""


_SEARCH_PATTERN = re.compile(r"^メモ(?:を)?検索[:：]?\s*(.+)$")
_ADD_PATTERN = re.compile(r"^メモ[:：]?\s*(.+)$")


def parse(text: str) -> ParsedCommand:
    text = text.strip()

    m = _SEARCH_PATTERN.match(text)
    if m:
        return ParsedCommand(intent=Intent.SEARCH, content=m.group(1).strip())

    m = _ADD_PATTERN.match(text)
    if m:
        return ParsedCommand(intent=Intent.ADD, content=m.group(1).strip())

    return ParsedCommand(intent=Intent.NONE)
