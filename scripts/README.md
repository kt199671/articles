# Weekly Coworking Space News Automation

毎週金曜日に自動実行され、コワーキングスペースの最新ニュースを調査・執筆・投稿する GitHub Actions ベースの完全自動化システムです。

## 📁 ディレクトリ構成

```
scripts/
├── weekly_news/
│   ├── __init__.py
│   ├── main.py              # メインオーケストレーター
│   ├── researcher.py        # AI リサーチ・執筆モジュール
│   ├── note_api.py          # note.com API クライアント
│   ├── markdown_utils.py    # Markdown → HTML 変換
│   └── config.py            # 設定定数
├── requirements.txt         # Python 依存関係
└── README.md               # このファイル
```

## 🚀 初期セットアップ

### 1. note.com でマガジン作成

1. [note.com](https://note.com) にログイン
2. マガジンセクションで新規作成: **週刊コワーキングスペース**
3. マガジン ID を URL から取得: `https://note.com/kentaro/m/m[MAGAZINE_ID]`

### 2. API キーの取得

#### Google Gemini API キー
1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. "Create API Key" をクリック
3. API キーをコピーして保管

#### Tavily API キー
1. [Tavily](https://tavily.com) にサインアップ
2. API キーを生成
3. コピーして保管

### 3. GitHub Secrets の設定

リポジトリの Settings → Secrets and variables → Actions で以下を追加:

| Secret 名 | 説明 | 例 |
|-----------|------|-----|
| `GEMINI_API_KEY` | Google Gemini API キー | `AIza...` |
| `TAVILY_API_KEY` | Tavily API キー | `tvly-...` |
| `NOTE_EMAIL` | note.com ログインメール | `your-email@example.com` |
| `NOTE_PASSWORD` | note.com ログインパスワード | `your-password` |
| `NOTE_MAGAZINE_ID` | note.com マガジン ID | `m1234567890` |

### 4. GitHub Actions の有効化

1. リポジトリの Actions タブを開く
2. "Weekly Coworking Space News" ワークフローを確認
3. "Run workflow" で手動テスト実行

## 🧪 ローカルテスト

### 環境構築

```bash
# 仮想環境作成
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r scripts/requirements.txt
```

### 環境変数設定

```bash
export GEMINI_API_KEY="AIza..."
export TAVILY_API_KEY="tvly-..."
export NOTE_EMAIL="your-email@example.com"
export NOTE_PASSWORD="your-password"
export NOTE_MAGAZINE_ID="m1234567890"
```

### ドライラン実行

```bash
# note.com 投稿をスキップ、ローカルファイルのみ生成
python -m scripts.weekly_news.main --dry-run
```

### 本番実行 (ローカル)

```bash
# 完全実行 (ファイル生成 + note.com 下書き作成)
python -m scripts.weekly_news.main
```

## 📅 自動実行スケジュール

- **実行日時**: 毎週金曜日 9:00 JST (00:00 UTC)
- **実行内容**:
  1. 過去7日間のコワーキングスペース関連ニュースを Tavily で検索
  2. OpenAI GPT-4 で 1,500-2,500文字の記事を生成
  3. Markdown ファイルを `note/magazine/週刊コワーキングスペース/` に保存
  4. note.com に下書きとして投稿
  5. 変更を Git にコミット & プッシュ

## 🔧 トラブルシューティング

### 401 エラー (ログイン失敗)

- note.com のメールアドレス・パスワードを確認
- GitHub Secrets の `NOTE_EMAIL` と `NOTE_PASSWORD` を更新

### 429 エラー (API クォータ超過)

- OpenAI または Tavily のプラン確認
- 使用量を確認し、必要に応じてアップグレード

### 検索結果なし

- Tavily のステータスを確認
- `scripts/weekly_news/config.py` の `SEARCH_QUERIES` を調整

### 重複記事エラー

- 週番号計算を確認
- GitHub Actions の cron スケジュールを確認
- 既存ファイルを削除して再実行

## 📊 コスト見積もり

- **Google Gemini 2.0 Flash**: **無料** (2026年1月時点)
- **Tavily**: 週約 $0.020
- **合計**: 週約 $0.020 = **年間約 $1.04**

※Gemini 2.0 Flash は現在無料で提供されています。将来的に有料化される可能性があります。

## 🔐 セキュリティ

- パスワードは GitHub Secrets で暗号化保管
- note.com へは毎回新規ログインでセッション取得
- API キーは環境変数経由でのみアクセス

## 📝 運用・保守

### 定期メンテナンス

| タスク | 頻度 | 重要度 |
|--------|------|--------|
| API コスト監視 | 週次 | 高 |
| 記事品質レビュー | 週次 | 中 |
| 検索クエリ調整 | 月次 | 中 |
| 依存関係更新 | 四半期 | 低 |

### パスワード変更時の対応

1. note.com でパスワード変更
2. GitHub Secrets の `NOTE_PASSWORD` を更新
3. 次回実行時に自動で新パスワードでログイン

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
