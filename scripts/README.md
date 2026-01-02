# Coworking Space Article Automation

GitHub Actions ベースの完全自動化システムで、コワーキングスペースに関する記事を自動生成します。

## 🤖 自動化システム

### 1. 週刊コワーキングスペース（毎週金曜日）
最新ニュースをまとめた週刊記事を自動生成

### 2. コワーキングの場づくり研究室（毎週水曜日）
学術的な研究記事を自動生成

## 📁 ディレクトリ構成

```
scripts/
├── weekly_news/             # 週刊ニュース記事生成
│   ├── __init__.py
│   ├── main.py              # メインオーケストレーター
│   ├── researcher.py        # AI リサーチ・執筆モジュール
│   └── config.py            # 設定定数
├── research_lab/            # 研究室記事生成
│   ├── __init__.py
│   ├── main.py              # メインオーケストレーター
│   ├── researcher.py        # AI リサーチ・執筆モジュール
│   └── config.py            # 設定定数
├── requirements.txt         # Python 依存関係
└── README.md               # このファイル
```

## 🚀 初期セットアップ

### 1. API キーの取得

#### Google Gemini API キー
1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. "Create API Key" をクリック
3. API キーをコピーして保管

#### Tavily API キー
1. [Tavily](https://tavily.com) にサインアップ
2. API キーを生成
3. コピーして保管

### 2. GitHub Secrets の設定

リポジトリの Settings → Secrets and variables → Actions で以下を追加:

| Secret 名 | 説明 | 例 |
|-----------|------|-----|
| `GEMINI_API_KEY` | Google Gemini API キー | `AIza...` |
| `TAVILY_API_KEY` | Tavily API キー | `tvly-...` |

### 3. GitHub Actions の有効化

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
```

### 実行

```bash
# 週刊ニュース記事生成
python -m scripts.weekly_news.main

# 研究室記事生成
python -m scripts.research_lab.main
```

## 📅 自動実行スケジュール

### 週刊コワーキングスペース
- **実行日時**: 毎週金曜日 9:00 JST (00:00 UTC)
- **実行内容**:
  1. 過去7日間のコワーキングスペース関連ニュースを Tavily で検索
  2. Google Gemini 3.0 Flash で 1,500-2,500文字のニュース記事を生成
  3. Markdown ファイルを `note/magazine/週刊コワーキングスペース/` に保存
  4. 変更を Git にコミット & プッシュ

### コワーキングの場づくり研究室
- **実行日時**: 毎週水曜日 9:00 JST (00:00 UTC)
- **実行内容**:
  1. 過去30日間のコワーキングスペース関連研究・トレンドを Tavily で検索
  2. Google Gemini 3.0 Flash で 5,000-8,000文字の学術的記事を生成
  3. Markdown ファイルを `note/magazine/コワーキングの場づくり研究室/` に保存
  4. 変更を Git にコミット & プッシュ

## 🔧 トラブルシューティング

### 429 エラー (API クォータ超過)

- Gemini または Tavily のプラン確認
- 使用量を確認し、必要に応じてアップグレード

### 検索結果なし

- Tavily のステータスを確認
- `scripts/weekly_news/config.py` または `scripts/research_lab/config.py` の `SEARCH_QUERIES` を調整

### 重複記事エラー

- 週番号計算を確認
- GitHub Actions の cron スケジュールを確認
- 既存ファイルを削除して再実行

## 📊 コスト見積もり

- **Google Gemini 3.0 Flash**: **無料** (2026年1月時点)
- **Tavily**:
  - 週刊ニュース: 週約 $0.020
  - 研究室: 週約 $0.028
  - 合計: 週約 $0.048
- **合計**: 週約 $0.048 = **年間約 $2.50**

※Gemini 3.0 Flash は現在無料で提供されています。将来的に有料化される可能性があります。

## 🔐 セキュリティ

- API キーは GitHub Secrets で暗号化保管
- API キーは環境変数経由でのみアクセス

## 📝 運用・保守

### 定期メンテナンス

| タスク | 頻度 | 重要度 |
|--------|------|--------|
| 記事品質レビュー | 週次 | 高 |
| API コスト監視 | 月次 | 中 |
| 検索クエリ調整 | 月次 | 中 |
| 依存関係更新 | 四半期 | 低 |

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
