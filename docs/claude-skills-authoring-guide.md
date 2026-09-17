# Claude スキル作成ガイド（教本）

Claude 向け Skill（Agent Skills）を作るときに参照する手引き。公式ドキュメントの内容を要約・整理したもの。

## 出典と取得状況（事実）

- 指定された URL `https://claude.com/blog/complete-guide-to-building-skills-for-claude` は、本作業環境のネットワーク送信ポリシー（egress proxy）により `claude.com` / `www.claude.com` ドメインごと遮断されており、本文を取得できなかった。
- そのため、同一内容の一次情報源である公式ドキュメントから内容を取得し、本ガイドを構成した。
  - Skill authoring best practices: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
  - Agent Skills overview: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
  - Use Skills in Claude Code: https://code.claude.com/docs/en/skills
- 公式スキル集（参考実装）: https://github.com/anthropics/skills

## 目次

- [1. Skill とは](#1-skill-とは)
- [2. Progressive disclosure（段階的開示）](#2-progressive-disclosure段階的開示)
- [3. 中核原則](#3-中核原則)
- [4. ディレクトリ構成](#4-ディレクトリ構成)
- [5. frontmatter](#5-frontmatter)
- [6. description の書き方](#6-description-の書き方)
- [7. 構成パターン](#7-構成パターン)
- [8. ワークフローとフィードバックループ](#8-ワークフローとフィードバックループ)
- [9. 記述内容のルール](#9-記述内容のルール)
- [10. 実行スクリプトを含む場合](#10-実行スクリプトを含む場合)
- [11. 評価（eval）と反復開発](#11-評価evalと反復開発)
- [12. アンチパターン](#12-アンチパターン)
- [13. 配布・共有と制約](#13-配布共有と制約)
- [14. セキュリティ](#14-セキュリティ)
- [15. 完成前チェックリスト](#15-完成前チェックリスト)

## 1. Skill とは

- `SKILL.md`（YAML frontmatter + Markdown 本文）を含むフォルダ。特定の作業のやり方を Claude に教える再利用可能な単位。
- プロンプト（その場かぎりの指示）と違い、必要になったときだけ読み込まれる。会話ごとに同じ説明を繰り返さなくて済む。
- 複数の Skill を同時に読み込める。組み合わせて使う前提で作る（モジュール性）。
- claude.ai / Claude Code / API で同じ形式が動く（依存関係が実行環境で満たされる限り）。

## 2. Progressive disclosure（段階的開示）

| レベル | 読み込まれる時点 | トークン費用 | 内容 |
|---|---|---|---|
| L1 メタデータ | 起動時（常時） | 1 Skill あたり約 100 トークン | frontmatter の `name` と `description` |
| L2 本文 | Skill が起動したとき | 5k トークン未満が目安 | `SKILL.md` の本文 |
| L3 付随ファイル | 必要になったとき | 参照するまで 0 | 追加 md、参照資料、スクリプト（実行なら出力のみ） |

- Claude は VM 上のファイルシステムを bash で辿る。参照されないファイルは文脈を消費しない。
- スクリプトは「実行」すればコード本体は文脈に入らず、出力だけが入る。

## 3. 中核原則

### 簡潔であること

コンテキストウィンドウは公共財。システムプロンプト、会話履歴、他 Skill のメタデータ、ユーザーの依頼と取り合いになる。

- 前提：**Claude はすでに賢い**。Claude が知らない情報だけを足す。
- 各記述に問いを立てる。「この説明は本当に必要か」「Claude は既に知っているのでは」「このトークン費用に見合うか」。
- 悪い例：PDF とは何か、ライブラリとは何かから説明する（約 150 トークン）。
- 良い例：使うライブラリと最小コードだけ示す（約 50 トークン）。

### 自由度を作業に合わせる

| 自由度 | 手段 | 使う場面 |
|---|---|---|
| 高 | 文章による指示 | 複数の正解がある、文脈で判断が変わる |
| 中 | 擬似コード、引数付きスクリプト | 推奨パターンはあるが変化も許容 |
| 低 | 具体的スクリプト、引数ほぼ無し | 壊れやすい、一貫性が critical、手順が固定 |

比喩：両側が崖の細い橋なら厳密な手順（低自由度）、障害物のない平原なら方向だけ示して任せる（高自由度）。

### 使う予定のモデル全部で試す

Skill はモデルへの追加物なので、効き方はモデルに依存する。Haiku では情報が足りるか、Sonnet では明快か、Opus では過剰説明になっていないか。

## 4. ディレクトリ構成

```
pdf-processing/
├── SKILL.md          # 主指示（起動時に読まれる）
├── FORMS.md          # 必要時のみ
├── REFERENCE.md      # 必要時のみ
├── EXAMPLES.md       # 必要時のみ
└── scripts/
    ├── analyze_form.py   # 実行される（読み込まれない）
    ├── fill_form.py
    └── validate.py
```

- フォルダ名は kebab-case。ファイル名は `SKILL.md`（大文字小文字は厳密）。
- 任意で `scripts/` `references/` `assets/`。
- ファイル名は内容が分かる名前にする（`form_validation_rules.md`、`doc2.md` は不可）。
- ドメイン別に分ける（`reference/finance.md`、`reference/sales.md`。`docs/file1.md` は不可）。

置き場所（Claude Code）:

| 種別 | パス | 読み込まれる範囲 |
|---|---|---|
| 個人 | `~/.claude/skills/<name>/SKILL.md` | このマシンの全プロジェクト |
| プロジェクト | `.claude/skills/<name>/SKILL.md` | そのリポジトリのセッション |
| ネスト | `<subdir>/.claude/skills/<name>/SKILL.md` | そのディレクトリ配下 |
| プラグイン | `<plugin>/skills/<name>/SKILL.md` | `/plugin-name:skill-name` で起動 |

## 5. frontmatter

必須は `name` と `description` の 2 つ（Claude Code では `description` のみ推奨で他は任意）。

```yaml
---
name: pdf-processing
description: Extracts text and tables from PDF files, fills forms, and merges documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
---
```

制約:

- `name`: 最大 64 文字 / 小文字英数字とハイフンのみ / XML タグ不可 / 予約語 `anthropic`, `claude` を含められない。
- `description`: 空でないこと / 最大 1,024 文字 / XML タグ不可 / 「何をするか」と「いつ使うか」の両方を書く。

命名は動名詞（gerund）を推奨：`processing-pdfs`, `analyzing-spreadsheets`, `managing-databases`, `testing-code`, `writing-documentation`。名詞句（`pdf-processing`）や動詞形（`process-pdfs`）も可。`helper`, `utils`, `tools`, `documents`, `data`, `files` のような曖昧・汎用名は避ける。

Claude Code の任意フィールド（主要なもの）:

| フィールド | 用途 |
|---|---|
| `disable-model-invocation: true` | 人間だけが起動できる（deploy、commit など副作用のある処理向け） |
| `user-invocable: false` | Claude だけが起動できる（背景知識として） |
| `allowed-tools` | そのターンだけ権限確認なしで使えるツールを事前承認（例 `Bash(git *)`） |
| `disallowed-tools` | Skill 有効中に外すツール |
| `context: fork` / `agent` / `background` | 隔離したサブエージェントで実行。`agent` で種別指定、`background: false` で結果を待つ |
| `model` / `effort` | セッションのモデル・効力レベルを上書き |
| `paths` | 自動読み込みを限定する glob（例 `*.py,*.js`） |
| `arguments` / `argument-hint` | 名前付き引数と補完ヒント |
| `metadata` | 自分のツール用の自由記述 |

動的コンテキスト注入（Claude Code）: 本文中の <code>!&#96;git diff HEAD&#96;</code> は Claude が読む前にシェルで実行され、出力が埋め込まれる。非ゼロ終了で起動全体が失敗するため必要なら `|| true`。1 コマンド 2 分でタイムアウト。claude.ai から同期された Skill では実行されない。

プレースホルダ: `$ARGUMENTS`, `$0`/`$1`, `$name`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`, `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_PLUGIN_ROOT}`。

## 6. description の書き方

- **必ず三人称で書く**。システムプロンプトに差し込まれるため、視点が混ざると発見に失敗する。
  - 良い: `Processes Excel files and generates reports`
  - 不可: `I can help you process Excel files` / `You can use this to process Excel files`
- 具体的に、検索語になるキーワードを入れる。「何をするか」＋「いつ使うか（トリガー語、文脈）」。
- 100 個以上の Skill から選ばれる前提。選定に足る情報を description に、実装詳細は本文に。

良い例:

```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
description: Analyze Excel spreadsheets, create pivot tables, generate charts. Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.
description: Generate descriptive commit messages by analyzing git diffs. Use when the user asks for help writing commit messages or reviewing staged changes.
```

避ける例: `Helps with documents` / `Processes data` / `Does stuff with files`

## 7. 構成パターン

- 本文は **500 行未満**に収める。超えそうなら別ファイルへ分割する。
- パターン 1: 概要＋参照。「Quick start」を本文に、詳細は `FORMS.md` / `REFERENCE.md` / `EXAMPLES.md` へリンク。
- パターン 2: ドメイン別分割。`SKILL.md` をナビゲーションにし、`reference/finance.md` などに分ける。grep での検索方法も書いておく。
- パターン 3: 条件付き詳細。基本操作は本文、特殊機能（tracked changes、OOXML 詳細など）はリンク先。
- **参照は SKILL.md から 1 階層まで**。入れ子の参照（SKILL.md → advanced.md → details.md）は避ける。Claude が `head -100` のような部分読みをして情報が欠ける。
- 100 行を超える参照ファイルには先頭に目次を置く。部分読みでも全体像が見えるようにする。

## 8. ワークフローとフィードバックループ

- 複雑な作業は順序のある手順に分解する。特に複雑なものは、Claude が回答へコピーして進捗をチェックできるチェックリスト形式にする。
- 例（コード無し）: 資料読了 → 主題抽出 → 主張の相互参照 → 構造化要約 → 引用検証。検証に失敗したら手順 3 へ戻る。
- 例（コード有り）: `analyze_form.py` 実行 → `fields.json` 編集 → `validate_fields.py` で検証 → `fill_form.py` で記入 → `verify_output.py` で確認。失敗したら手順 2 へ戻る。
- フィードバックループの型：**検証を走らせる → エラーを直す → 繰り返す**。通るまで次へ進ませない。検証器はスクリプトでも `STYLE_GUIDE.md` のような文書でもよい。

## 9. 記述内容のルール

- **時限的な情報を書かない**。「2025 年 8 月より前なら旧 API」のような記述は必ず古くなる。現行の方法を本文に書き、旧方式は `<details>` で囲った "Old patterns" セクションに退避させる。
- **用語を統一する**。`API endpoint` と `URL`/`API route`/`path` を混在させない。`field` と `box`/`element`/`control` を混ぜない。`extract` と `pull`/`get`/`retrieve` を混ぜない。
- テンプレートパターン: 出力形式を示す。厳密に守らせたいときは「ALWAYS use this exact template structure」、柔軟でよいときは「sensible default だが判断して調整せよ」と明示する。
- 例示パターン: 出力品質が例に依存する場合、入力と出力の対を複数示す（コミットメッセージ生成など）。説明より例のほうが伝わる。
- 条件分岐パターン: 「新規作成なら Creation workflow、既存編集なら Editing workflow」のように分岐点を明示する。手順が膨れるなら別ファイルへ出し、状況に応じて読ませる。

## 10. 実行スクリプトを含む場合

- **委ねずに解決する**。スクリプト側でエラー条件を処理する。`FileNotFoundError` なら既定値で作る、`PermissionError` なら代替を返す。失敗させて Claude に丸投げしない。
- **voodoo constants を作らない**（Ousterhout の法則）。定数には根拠をコメントで書く。`TIMEOUT = 47  # なぜ 47?` は不可。
- ユーティリティスクリプトを同梱する利点：生成コードより信頼できる、トークン節約、生成時間の節約、一貫性。
- **実行なのか参照なのかを明示する**。「Run `analyze_form.py` to extract fields」（実行）か「See `analyze_form.py` for the algorithm」（参照）。通常は実行が望ましい。
- 画像化できる入力は画像にして視覚解析させる（PDF → 画像 → フィールド位置の判断）。
- **検証可能な中間成果物**を作る（plan-validate-execute）。計画を `changes.json` などに書き出し、スクリプトで検証してから適用する。バッチ処理、破壊的変更、複雑な検証規則、高リスク作業で使う。検証スクリプトのエラーは具体的に（「'signature_date' が無い。利用可能: customer_name, order_total, ...」）。
- 依存パッケージは SKILL.md に明記し、実行環境で利用可能か確認する。インストール済みと決めつけない。
- MCP ツールは**完全修飾名**で書く（`ServerName:tool_name`、例 `BigQuery:bigquery_schema`、`GitHub:create_issue`）。プレフィックス無しだと見つけられないことがある。

## 11. 評価（eval）と反復開発

**大量に書く前に評価を作る。**

1. 欠落の特定：Skill 無しで代表的なタスクを走らせ、失敗や足りない文脈を記録する。
2. 評価の作成：その欠落を突く 3 つのシナリオを作る。
3. ベースライン測定：Skill 無しの性能を測る。
4. 最小の指示を書く：評価を通すのに足るだけ書く。
5. 反復：評価を実行し、ベースラインと比較して直す。

評価の構造例:

```json
{
  "skills": ["pdf-processing"],
  "query": "Extract all text from this PDF file and save it to output.txt",
  "files": ["test-files/document.pdf"],
  "expected_behavior": [
    "Successfully reads the PDF file using an appropriate PDF processing library or command-line tool",
    "Extracts text content from all pages in the document without missing any pages",
    "Saves the extracted text to a file named output.txt in a clear, readable format"
  ]
}
```

（注：公式ドキュメント時点では、この評価を走らせる組み込みの仕組みは無い。実行系は自作する。）

**Claude と一緒に反復する。** Skill を設計・改訂する相手（Claude A）と、その Skill を使って実務をする側（Claude B）を分ける。

1. Skill 無しで課題を一度やり切る。繰り返し与えている文脈に気づく。
2. 再利用できるパターンを特定する（テーブル名、フィールド定義、「テストアカウントは常に除外」などの規則、よく使うクエリ）。
3. Claude A に Skill 化を依頼する。Claude は Skill 形式を理解しているので特別な指示は不要。
4. 冗長さを削る（「勝率の説明は不要、Claude は知っている」）。
5. 情報設計を直す（「スキーマは別の参照ファイルへ」）。
6. 新しいセッションの Claude B で類似タスクを試す。
7. 観察を Claude A に戻す（「Q4 の日付フィルタを忘れた。日付フィルタの節を足すべきか」）。改訂案は「always」より「MUST」のような強い語、規則の配置の見直しなど。

**Claude の辿り方を観察する。** 想定外の読み順（構造が直感的でない）、参照を辿らない（リンクが目立たない）、同じファイルばかり読む（本文に移すべき）、一度も読まれないファイル（不要か合図が弱い）。推測ではなく観察に基づいて直す。

## 12. アンチパターン

- Windows 形式のパス（`scripts\helper.py`）。常に `/` を使う。
- 選択肢を並べすぎる（「pypdf でも pdfplumber でも PyMuPDF でも…」）。既定を 1 つ示し、逃げ道を 1 つ添える（「スキャン PDF の OCR には pdf2image + pytesseract」）。
- パッケージが入っている前提で書く。インストール手順を明示する。
- 入れ子の深い参照。
- 時限的な記述、用語の揺れ、抽象的な例。

## 13. 配布・共有と制約

- **サーフェス間で同期しない**。claude.ai にアップした Skill は API では使えず、その逆も同様。Claude Code はファイルシステム上で両者から独立。使う場所ごとに配置する。
- 共有範囲：claude.ai は個人単位（各メンバーが個別にアップロード、管理者の一括管理は不可）、API はワークスペース全体、Claude Code は個人 `~/.claude/skills/` かプロジェクト `.claude/skills/`（Plugin でも共有可）。
- 実行環境の制約：
  - claude.ai: ネットワークアクセスは設定次第（全面/部分/不可）。npm・PyPI・GitHub からの取得が可能な場合がある。
  - Claude API: **ネットワークアクセス無し、実行時のパッケージ導入不可**。事前導入済みパッケージのみ。
  - Claude Code: ネットワークは利用者のマシンと同等。グローバルなパッケージ導入は避け、ローカルに留める。
- Claude Code の運用補助：`/skill-doctor` で使用状況とトークン費用を確認（未使用 Skill、Skill ごとの費用、起動頻度）。`skillOverrides` で個別に `off` / `name-only` などに設定。権限規則（`Skill(commit)` など）でアクセスを制限できる。
- 名前衝突の優先順位：Enterprise > Personal > Project。自作は同名の bundled skill を置き換える。ローカルと同期版が衝突した場合、ローカルが `/name`、同期版が `/anthropic-skills:name`。

## 14. セキュリティ

- **信頼できる出自の Skill だけを使う**（自作か Anthropic 提供）。Skill は指示とコードで Claude に新しい能力を与えるため、悪意ある Skill は宣言された目的と異なるツール実行を誘導できる。
- 出自不明なものを使う場合は全ファイル（SKILL.md、スクリプト、画像、資料）を監査する。想定外のネットワーク通信、不審なファイルアクセス、目的と無関係な操作を探す。
- 外部 URL から取得する Skill は特にリスクが高い。取得内容に悪意ある指示が混じりうるし、依存先が後から変質することもある。
- ソフトウェアを導入するのと同じ扱いをする。機密データや重要操作に触れる本番系では特に慎重に。

## 15. 完成前チェックリスト

品質:

- [ ] description が具体的で、キーワードを含む
- [ ] description に「何をするか」と「いつ使うか」の両方がある
- [ ] SKILL.md 本文が 500 行未満
- [ ] 詳細は別ファイルへ分離（必要な場合）
- [ ] 時限的情報が無い（あれば "Old patterns" に退避）
- [ ] 用語が一貫している
- [ ] 例が具体的（抽象的でない）
- [ ] ファイル参照が 1 階層まで
- [ ] progressive disclosure を適切に使っている
- [ ] ワークフローの手順が明確

コードとスクリプト:

- [ ] スクリプトが問題を解決している（Claude に委ねていない）
- [ ] エラー処理が明示的で有用
- [ ] 根拠のない定数が無い
- [ ] 必要パッケージを明記し、利用可能性を確認済み
- [ ] スクリプトに説明がある
- [ ] Windows 形式のパスが無い
- [ ] 重要操作に検証・確認の手順がある
- [ ] 品質が重要な作業にフィードバックループがある

テスト:

- [ ] 評価を 3 つ以上作成した
- [ ] Haiku / Sonnet / Opus で試した
- [ ] 実際の利用場面で試した
- [ ] チームのフィードバックを反映した（該当する場合）
