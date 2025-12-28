"""
MCP Host アプリケーション パッケージ

MCP サーバーに接続し、Claude AI を介してツールを自然言語で操作できる
チャットボットアプリケーション。

【MCP アーキテクチャにおける位置づけ】

    ┌─────────────────────────────────────┐
    │            MCP Host                 │  ← 本パッケージ
    │  ┌─────────────────────────────┐   │
    │  │        MCP Client           │   │  ← connection.py (ClientSession)
    │  └──────────────┬──────────────┘   │
    └─────────────────┼──────────────────┘
                      │ stdio
                      ▼
              ┌──────────────┐
              │  MCP Server  │               ← 外部スクリプト
              └──────────────┘

モジュール構成:
- config.py: 設定値の一元管理
- connection.py: MCP 接続管理（MCP Client 層）
- processor.py: クエリ処理（Claude API 統合）
- chat.py: ユーザーインターフェース
- __main__.py: エントリーポイント

【未実装の機能】
- Sampling: Server が Host の LLM を使用する機能
- Elicitation: Server がユーザーに追加情報を求める機能
- Roots: Host がアクセス可能なディレクトリを通知する機能

使用方法:
    python -m mcp_client path/to/server.py
"""

from .chat import ChatInterface
from .connection import MCPConnection
from .processor import QueryProcessor

__all__ = ["MCPConnection", "QueryProcessor", "ChatInterface"]
