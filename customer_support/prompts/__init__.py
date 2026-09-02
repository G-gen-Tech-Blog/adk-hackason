"""各エージェントのプロンプト定義パッケージ

ハッカソン参加者がプロンプトの調整や業務シナリオの差し替えを容易に行えるよう、
プロンプト定義をモジュールとして分離して管理しています。
"""

from .customer import CUSTOMER_INSTRUCTION
from .draft import DRAFT_INSTRUCTION
from .knowledge import KNOWLEDGE_INSTRUCTION
from .quality import QUALITY_INSTRUCTION
from .quick import QUICK_RESPONSE_INSTRUCTION
from .risk import RISK_INSTRUCTION
from .triage import TRIAGE_INSTRUCTION, TriageResult

__all__ = [
    "TRIAGE_INSTRUCTION",
    "TriageResult",
    "QUICK_RESPONSE_INSTRUCTION",
    "KNOWLEDGE_INSTRUCTION",
    "CUSTOMER_INSTRUCTION",
    "RISK_INSTRUCTION",
    "DRAFT_INSTRUCTION",
    "QUALITY_INSTRUCTION",
]
