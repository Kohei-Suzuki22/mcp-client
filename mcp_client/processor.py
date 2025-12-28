"""
クエリ処理モジュール

ユーザークエリを処理し、Claude API とツール実行を組み合わせて応答を生成する。
このモジュールは MCP Host の「LLM 統合」部分を担当する。

責務:
- Claude API との通信
- ツール実行の判断（Claude が行う）
- ツール実行結果の処理
- 最終応答の生成
"""

from anthropic import Anthropic

from .config import ANTHROPIC_MODEL, MAX_TOKENS
from .connection import MCPConnection


class QueryProcessor:
    """
    クエリ処理クラス

    ユーザーからのクエリを受け取り、以下のフローで処理する:
    1. MCP サーバーからツール一覧を取得
    2. クエリとツール定義を Claude API に送信
    3. Claude の応答を解析（テキスト or ツール使用リクエスト）
    4. 必要に応じてツールを実行し、結果を Claude に返送
    5. 最終応答を返す

    使用例:
        processor = QueryProcessor(connection)
        response = await processor.process("天気を教えて")
    """

    def __init__(self, connection: MCPConnection):
        """
        QueryProcessor のコンストラクタ

        Args:
            connection: MCP サーバーへの接続
        """
        self._connection = connection
        # Anthropic クライアント: 環境変数 ANTHROPIC_API_KEY を自動的に読み込む
        self._anthropic = Anthropic()

    async def process(self, query: str) -> str:
        """
        ユーザークエリを処理し、応答を生成する

        Args:
            query: ユーザーからの自然言語クエリ

        Returns:
            str: Claude からの応答テキスト

        処理フロー:
            1. ツール一覧を取得
            2. Claude API にクエリ送信
            3. 応答を解析してツール実行 or テキスト返却
        """
        # メッセージ履歴を初期化
        messages = [{"role": "user", "content": query}]

        # サーバーから利用可能なツール一覧を取得
        available_tools = await self._connection.list_tools()

        # Claude API にクエリを送信
        response = self._anthropic.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=MAX_TOKENS,
            messages=messages,
            tools=available_tools,
        )

        # 応答を処理
        return await self._handle_response(response, messages, available_tools)

    async def _handle_response(self, response, messages: list, tools: list) -> str:
        """
        Claude の応答を処理する

        Args:
            response: Claude API からの応答
            messages: メッセージ履歴
            tools: 利用可能なツール一覧

        Returns:
            str: 処理結果のテキスト
        """
        result_parts = []

        for content in response.content:
            if content.type == "text":
                # テキスト応答: そのまま結果に追加
                result_parts.append(content.text)

            elif content.type == "tool_use":
                # ツール使用リクエスト: ツールを実行
                tool_result = await self._execute_tool(content, messages)
                result_parts.append(tool_result)

        return "\n".join(result_parts)

    async def _execute_tool(self, tool_request, messages: list) -> str:
        """
        ツールを実行し、Claude から最終応答を取得する

        Args:
            tool_request: Claude からのツール使用リクエスト
            messages: メッセージ履歴（更新される）

        Returns:
            str: ツール実行結果を含む応答テキスト
        """
        tool_name = tool_request.name
        tool_args = tool_request.input

        # MCP サーバー経由でツールを実行
        result = await self._connection.call_tool(tool_name, tool_args)

        # デバッグ情報
        debug_info = f"[Calling tool {tool_name} with args {tool_args}]"

        # ツール実行結果を会話履歴に追加
        if hasattr(tool_request, "text") and tool_request.text:
            messages.append({"role": "assistant", "content": tool_request.text})

        messages.append({"role": "user", "content": result.content})

        # ツール結果を基に Claude から最終応答を取得
        response = self._anthropic.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=MAX_TOKENS,
            messages=messages,
        )

        final_response = response.content[0].text
        return f"{debug_info}\n{final_response}"
