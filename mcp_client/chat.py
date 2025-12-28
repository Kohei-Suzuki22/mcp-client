"""
チャットインターフェースモジュール

ユーザーとの対話インターフェースを提供する。
このモジュールは MCP Host の「ユーザー UI」部分を担当する。

責務:
- 対話ループの実行
- ユーザー入力の取得
- 応答の表示
- エラーハンドリング
"""

from .processor import QueryProcessor


class ChatInterface:
    """
    対話型チャットインターフェース

    ユーザーからの入力を繰り返し受け付け、QueryProcessor を通じて処理する。

    使用例:
        chat = ChatInterface(processor)
        await chat.run()
    """

    # 終了コマンド
    QUIT_COMMAND = "quit"

    def __init__(self, processor: QueryProcessor):
        """
        ChatInterface のコンストラクタ

        Args:
            processor: クエリ処理を行う QueryProcessor
        """
        self._processor = processor

    async def run(self):
        """
        対話ループを実行する

        'quit' と入力するとループを終了する。
        エラーが発生しても、メッセージを表示して続行する。
        """
        self._print_welcome()

        while True:
            try:
                query = self._get_input()

                if self._should_quit(query):
                    break

                if not query:
                    continue

                response = await self._processor.process(query)
                self._print_response(response)

            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except Exception as e:
                self._print_error(e)

    def _print_welcome(self):
        """ウェルカムメッセージを表示"""
        print("\nMCP Client Started!")
        print(f"Type your queries or '{self.QUIT_COMMAND}' to exit.")

    def _get_input(self) -> str:
        """ユーザー入力を取得"""
        return input("\nQuery: ").strip()

    def _should_quit(self, query: str) -> bool:
        """終了すべきかどうかを判定"""
        return query.lower() == self.QUIT_COMMAND

    def _print_response(self, response: str):
        """応答を表示"""
        print("\n" + response)

    def _print_error(self, error: Exception):
        """エラーメッセージを表示"""
        print(f"\nError: {str(error)}")
