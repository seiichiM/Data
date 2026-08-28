# keep_bot — Google Keep 自動メモツール

Google Keep には個人アカウント向けの公式APIが存在しないため、
Playwright によるブラウザ操作で `keep.google.com` を直接操作し、
「メモ」というキーワードをトリガーにメモの追加・検索を行うツールです。

## セットアップ

```bash
pip install -r requirements.txt
playwright install chromium
```

## 初回ログイン

ブラウザが表示されるので、その場でGoogleアカウントにログインしてください
(2段階認証もブラウザ上で対応)。ログイン後の状態は `.keep_bot_state/` に
保存され、以降はヘッドレスで再利用されます。

```bash
python -m keep_bot login
```

## 使い方

自然文からキーワードを判定して実行:

```bash
python -m keep_bot say "メモ 牛乳を買う"        # -> メモを追加
python -m keep_bot say "メモ検索 牛乳"          # -> メモを検索
```

直接コマンドを指定:

```bash
python -m keep_bot add "牛乳を買う"
python -m keep_bot search "牛乳"
```

## キーワードのパターン

- `メモ ...` / `メモ: ...` / `メモ： ...` → メモを追加
- `メモ検索 ...` / `メモを検索 ...` → メモを検索してタイトル・本文を一覧表示

## 注意事項

- Google Keep の画面のHTML構造は予告なく変わることがあり、要素のセレクタ
  (`keep_bot/keep_client.py`)が壊れる可能性があります。動作しない場合は
  実際の画面を見ながらセレクタを調整してください。
- ログインセッション(`.keep_bot_state/auth_state.json`)には認証情報が
  含まれるため、`.gitignore` に追加し、リポジトリにコミットしないでください。
- 非公式な手段(画面操作)のため、Googleの利用規約・自動化ポリシーに
  抵触するリスクがあります。個人利用の範囲で自己責任で使用してください。
- 定期実行したい場合は cron やタスクスケジューラから
  `python -m keep_bot say "メモ ..."` を呼び出す形で組み込めます。
