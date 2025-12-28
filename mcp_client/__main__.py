"""
エントリーポイントモジュール

アプリケーションのエントリーポイントと CLI 引数処理を担当する。
`python -m mcp_client` で実行可能。

責務:
- CLI 引数の解析
- 各コンポーネントの組み立て（依存性注入）
- メインループの起動
"""

import asyncio
import sys

from .chat import ChatInterface
from .connection import MCPConnection
from .processor import QueryProcessor


def print_usage():
    """使用方法を表示"""
    print("Usage: python -m mcp_client <path_to_server_script>")
    print()
    print("Examples:")
    print("  python -m mcp_client ../mcp-server/server.py")
    print("  python -m mcp_client /path/to/weather-server.js")


async def main(server_path: str):
    """
    メインエントリーポイント

    各コンポーネントを組み立て、チャットループを開始する。

    Args:
        server_path: MCP サーバースクリプトのパス

    コンポーネント構成:
        MCPConnection (接続管理)
            ↓
        QueryProcessor (クエリ処理)
            ↓
        ChatInterface (ユーザー UI)
    """
    async with MCPConnection() as connection:
        # サーバーに接続
        tool_names = await connection.connect(server_path)
        print(f"\nConnected to server with tools: {tool_names}")

        # コンポーネントを組み立て
        processor = QueryProcessor(connection)
        chat = ChatInterface(processor)

        # チャットループを開始
        await chat.run()


def run():
    """CLI エントリーポイント"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    server_path = sys.argv[1]
    asyncio.run(main(server_path))


if __name__ == "__main__":
    run()
