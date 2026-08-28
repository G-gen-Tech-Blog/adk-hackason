# ディレクトリ構成とモジュール命名規則

## 1. エージェント命名と Python 識別子規則（最重要）

ADK はエージェントを読み込む際、Python の `importlib` を使用して動的にモジュールをインポートします。そのため、**エージェントディレクトリ名（パッケージ名）は Python の有効な識別子（半角英数字とアンダースコア `_` のみ）** である必要があります。

### ⚠️ よくある落とし穴: ハイフン (`-`) の混入
GitHub リポジトリ名にはハイフンがよく使われます（例: `adk-hackason`、`customer-support-bot`）。
リポジトリ直下に `agent.py` を配置すると、ADK はカレントディレクトリ名（`adk-hackason`）をエージェント名として認識し、以下のエラーが発生してロードに失敗します：

```text
ValueError: Invalid agent name: 'adk-hackason'. Agent names must be valid Python identifiers (letters, digits, and underscores only).
```

### ✅ 推奨される標準ディレクトリ構成（マルチエージェント / パッケージ形式）

リポジトリ名にハイフンが含まれていても問題ないよう、**リポジトリルート配下に有効な Python 識別子名のパッケージディレクトリ（例: `customer_support/`）を作成する構成** が ADK のベストプラクティスです。

```text
<repository-root>/                # 例: adk-hackason/ (ハイフンがあってもOK)
├── <agent_package_name>/         # 例: customer_support/ (アンダースコアを使用)
│   ├── __init__.py               # root_agent をエクスポート
│   ├── agent.py                  # Workflow または LlmAgent (root_agent) の定義
│   ├── prompts/                  # プロンプト定義モジュール
│   │   ├── __init__.py
│   │   └── ...
│   └── tools/                    # ツール・関数定義モジュール
│       ├── __init__.py
│       └── ...
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
└── README.md
```

---

## 2. インポートと `__init__.py` の書き方

エージェントパッケージ内では、**相対インポート** を使用することで、モジュールの可搬性とクリーンな構造を保ちます。

### `customer_support/__init__.py`
```python
from .agent import root_agent

__all__ = ["root_agent"]
```

### `customer_support/agent.py`
```python
from google.adk.workflow import Workflow, FunctionNode, JoinNode, START
from .prompts import TRIAGE_INSTRUCTION, DRAFT_INSTRUCTION
from .tools import search_knowledge_base, get_customer_info

# root_agent を定義
root_agent = Workflow(...)
```

---

## 3. 単一エージェント vs マルチエージェント

| 形式 | 起動コマンド | 特徴・使いどころ |
| :--- | :--- | :--- |
| **マルチエージェントディレクトリ** (推奨) | `adk web` または `adk web .` | リポジトリ直下の各サブパッケージ（`customer_support` 等）を自動探索。UI 上でエージェントを切り替え可能。 |
| **単一エージェント指定** | `adk web customer_support` | 特定のエージェントフォルダのみを対象として起動する。 |
