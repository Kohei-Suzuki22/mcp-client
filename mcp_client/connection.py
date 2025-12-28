"""
MCP 接続管理モジュール

MCP サーバーへの接続確立とセッション管理を担当する。
このモジュールが MCP アーキテクチャにおける「MCP Client」層に最も近い部分。

責務:
- サーバープロセスの起動
- stdio トランスポートの確立
- MCP セッション（ClientSession）の管理
- リソースのクリーンアップ
"""

from contextlib import AsyncExitStack
from pathlib import Path
from typing import Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPConnection:
    """
    MCP サーバーへの接続を管理するクラス

    このクラスは MCP の「Client」層をラップし、以下を提供する:
    - サーバーへの接続確立
    - セッションのライフサイクル管理
    - 利用可能なツール一覧の取得

    使用例:
        async with MCPConnection() as connection:
            await connection.connect("path/to/server.py")
            tools = await connection.list_tools()
    """

    def __init__(self):
        """MCPConnection のコンストラクタ"""
        # MCP サーバーとのセッション（connect で初期化される）
        # これが MCP アーキテクチャにおける「MCP Client」に該当
        self.session: Optional[ClientSession] = None

        # AsyncExitStack: 複数の非同期コンテキストマネージャーを管理
        self._exit_stack = AsyncExitStack()

        # 接続状態
        self._connected = False

    async def __aenter__(self):
        """非同期コンテキストマネージャーのエントリー"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了時にクリーンアップ"""
        await self.close()

    async def connect(self, server_script_path: str) -> list[str]:
        """
        MCP サーバーに接続する

        Args:
            server_script_path: サーバースクリプトのパス（.py または .js）

        Returns:
            list[str]: 利用可能なツール名のリスト

        Raises:
            ValueError: サポートされていないファイル形式の場合

        通信の仕組み:
            クライアント <--stdin/stdout--> サーバープロセス
        """
        server_params = self._create_server_params(server_script_path)

        # stdio トランスポートを確立
        # サーバープロセスを起動し、stdin/stdout を介した通信チャネルを作成
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio, write = stdio_transport

        # MCP セッション（= MCP Client 層）を作成
        self.session = await self._exit_stack.enter_async_context(
            ClientSession(stdio, write)
        )

        # セッションを初期化（MCP ハンドシェイク）
        await self.session.initialize()
        self._connected = True

        # 利用可能なツール名を返す
        tools = await self.list_tools()
        return [tool["name"] for tool in tools]

    async def list_tools(self) -> list[dict]:
        """
        サーバーが提供するツール一覧を取得する

        Returns:
            list[dict]: ツール情報のリスト（name, description, input_schema を含む）

        Raises:
            RuntimeError: 接続されていない場合
        """
        self._ensure_connected()

        response = await self.session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]

    async def call_tool(self, name: str, arguments: dict):
        """
        ツールを実行する

        Args:
            name: ツール名
            arguments: ツールに渡す引数

        Returns:
            ツールの実行結果

        Raises:
            RuntimeError: 接続されていない場合
        """
        self._ensure_connected()
        return await self.session.call_tool(name, arguments)

    async def close(self):
        """リソースをクリーンアップする"""
        await self._exit_stack.aclose()
        self._connected = False

    def _ensure_connected(self):
        """接続されていることを確認する"""
        if not self._connected or self.session is None:
            raise RuntimeError("Not connected to MCP server")

    def _create_server_params(self, server_script_path: str) -> StdioServerParameters:
        """
        サーバー起動パラメータを作成する

        Args:
            server_script_path: サーバースクリプトのパス

        Returns:
            StdioServerParameters: サーバー起動パラメータ

        Raises:
            ValueError: サポートされていないファイル形式の場合
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")

        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        if is_python:
            # Python サーバー: uv を使用して実行
            path = Path(server_script_path).resolve()
            return StdioServerParameters(
                command="uv",
                args=["--directory", str(path.parent), "run", path.name],
                env=None,
            )
        else:
            # JavaScript サーバー: node で直接実行
            return StdioServerParameters(
                command="node",
                args=[server_script_path],
                env=None,
            )
