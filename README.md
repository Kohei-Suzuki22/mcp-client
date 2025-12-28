# MCP Client

Model Context Protocol (MCP) を使用したチャットボットアプリケーションの Python 実装です。MCP サーバーに接続し、Claude AI を使用してサーバーのツールを自然言語で操作できます。

## MCP アーキテクチャにおける位置づけ

> **注意**: このリポジトリ名は "mcp-client" ですが、MCP の厳密な用語では **MCP Host** に該当します。

MCP は以下の 3 層アーキテクチャで構成されます：

```
┌─────────────────────────────────────────────────────┐
│                    MCP Host                         │
│  （Claude Desktop、IDE、本リポジトリの実装など）       │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐                  │
│  │ MCP Client  │  │ MCP Client  │  ← Server と 1:1 │
│  └──────┬──────┘  └──────┬──────┘                  │
└─────────┼────────────────┼──────────────────────────┘
          │                │
          ▼                ▼
   ┌──────────────┐ ┌──────────────┐
   │  MCP Server  │ │  MCP Server  │
   │  (天気API)    │ │  (DB接続)    │
   └──────────────┘ └──────────────┘
```

| レイヤー | 説明 | 本リポジトリでの対応 |
|---------|------|---------------------|
| **MCP Host** | ユーザーインターフェースを提供し、LLM と統合するアプリケーション | `mcp_client` パッケージ全体 |
| **MCP Client** | Host 内に存在し、Server との 1:1 接続を管理するプロトコル層 | `connection.py` (`ClientSession`) |
| **MCP Server** | ツール、リソース、プロンプトを提供する外部サービス | 引数で指定するスクリプト |

### Claude Desktop との関係

本リポジトリは Claude Desktop とは **独立した別の Host アプリケーション** です：

- Claude Desktop が本コードを使用するわけではない
- 両方とも MCP Server に接続できる別々の Host
- 同じ MCP Server を両方から利用することは可能

### 未実装の機能

本実装は最小限の Host であり、以下の MCP 機能は未実装です：

| 機能 | 説明 | 状態 |
|-----|------|------|
| **Sampling** | Server が Host の LLM を使用できる機能 | 未実装 |
| **Elicitation** | Server がユーザーに追加情報や確認を求める機能 | 未実装 |
| **Roots** | Host がアクセス可能なディレクトリを Server に通知する機能 | 未実装 |

これらは Server → Host 方向のリクエストを可能にする双方向機能です。

### 学習上の注意

このチュートリアルは「MCP Client を作る」と題されていますが、実際に作るのは **Host アプリケーション** です。純粋な MCP Client（`ClientSession`）の内部動作やプロトコルの詳細を学ぶには、MCP SDK のソースコードを読むか、プロトコル仕様を参照する必要があります。

## 概要

このアプリケーションは以下の機能を提供します：

- MCP サーバーへの接続管理
- サーバーが提供するツールの自動検出
- Claude API を使用したクエリ処理
- ツールの実行と結果のハンドリング

## セットアップ

### 前提条件

- Python 3.13 以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- Anthropic API キー

### インストール

1. 依存関係のインストール：

```bash
uv sync
```

2. 環境変数の設定：

`.env` ファイルを作成し、Anthropic API キーを設定します：

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

## 使い方

MCP サーバーのスクリプトパスを引数に指定して実行します：

```bash
# Python サーバーの場合
uv run python -m mcp_client path/to/server.py

# JavaScript サーバーの場合
uv run python -m mcp_client path/to/server.js
```

起動後、対話的なチャットループが開始されます。`quit` と入力すると終了します。

## 動作の仕組み

クライアントは以下のフローで動作します：

```
┌─────────────────────────────────────────────────────────────────┐
│                        実行フロー                                │
└─────────────────────────────────────────────────────────────────┘

1. 初期化
   └─→ クライアントが stdio トランスポートを介して MCP サーバーに接続

2. ツール検出
   └─→ サーバーから利用可能なツール一覧を取得

3. ユーザー入力
   └─→ ユーザーが自然言語でクエリを入力

4. Claude 処理
   └─→ クエリとツール定義を Claude API に送信

5. ツール判断
   └─→ Claude が回答にツールが必要かどうかを判断

6. ツール実行（必要な場合）
   └─→ クライアントがサーバー経由でツールを実行

7. 結果の集約
   └─→ ツールの実行結果を Claude に返送

8. 応答生成
   └─→ Claude がツールの出力を使用して最終応答を生成

9. 表示
   └─→ 応答をユーザーに表示
```

### クエリ処理の詳細

```
ユーザークエリ
    │
    ▼
サーバーから利用可能なツールを取得
    │
    ▼
クエリ + ツール定義を Claude に送信
    │
    ▼
Claude がどのツールを使用するか決定
    │
    ▼
サーバー経由でツールを実行
    │
    ▼
結果を Claude に返送
    │
    ▼
Claude が自然言語で応答を生成
    │
    ▼
ユーザーに応答を表示
```

## アーキテクチャ

### パッケージ構造

```text
mcp_client/
├── __init__.py      # パッケージ初期化、公開 API 定義
├── __main__.py      # エントリーポイント（CLI 引数処理）
├── config.py        # 設定値の一元管理
├── connection.py    # MCP 接続管理（MCP Client 層）
├── processor.py     # クエリ処理（Claude API 統合）
└── chat.py          # ユーザーインターフェース
```

### モジュールの責務

| モジュール | 責務 |
|-----------|------|
| `config.py` | 設定値（モデル名、トークン数など）の一元管理 |
| `connection.py` | MCP サーバーへの接続、セッション管理、ツール実行 |
| `processor.py` | Claude API との通信、ツール実行のオーケストレーション |
| `chat.py` | 対話ループ、ユーザー入出力 |
| `__main__.py` | CLI 引数解析、コンポーネントの組み立て |

### コンポーネント間の関係

```text
__main__.py (エントリーポイント)
    │
    ├── MCPConnection (connection.py)
    │       └── ClientSession (MCP SDK)
    │
    ├── QueryProcessor (processor.py)
    │       └── Anthropic Client
    │
    └── ChatInterface (chat.py)
```

### 依存関係

- `mcp` - Model Context Protocol SDK
- `anthropic` - Anthropic API クライアント
- `python-dotenv` - 環境変数の読み込み

## トラブルシューティング

| 問題 | 解決策 |
|-----|--------|
| サーバーパスエラー | 絶対パスを使用し、正しいファイル拡張子を確認 |
| 接続拒否 | サーバーが実行可能でパスが正しいことを確認 |
| ツール実行失敗 | 環境変数が正しく設定されているか確認 |
| 応答が遅い | 初回は30秒程度かかることがあります。中断せずお待ちください |

## 参考

- [MCP Client Documentation](https://modelcontextprotocol.io/docs/develop/build-client)
- [Anthropic API Documentation](https://docs.anthropic.com/)
