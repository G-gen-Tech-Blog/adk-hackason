"""モックツール定義パッケージ

ハッカソン参加者が外部APIやDB連携の代わりに利用できる、
簡易的なナレッジ検索ツールおよび顧客情報照会ツールを提供します。
"""

from .customer_tool import get_customer_info
from .knowledge_tool import search_knowledge_base

__all__ = [
    "search_knowledge_base",
    "get_customer_info",
]
