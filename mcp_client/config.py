"""
設定値モジュール

アプリケーション全体で使用する設定値を一元管理する。
環境変数や定数はここで定義し、他のモジュールからインポートして使用する。
"""

from dotenv import load_dotenv

# .env ファイルから環境変数を読み込む
# ANTHROPIC_API_KEY などの機密情報はここで読み込まれる
load_dotenv()

# 使用する Claude モデル
# claude-sonnet-4-5 は高速かつ高性能なモデル
ANTHROPIC_MODEL = "claude-sonnet-4-5"

# Claude API のデフォルト設定
MAX_TOKENS = 1000
