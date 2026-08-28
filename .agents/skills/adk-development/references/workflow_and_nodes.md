# ADK 2.0 Workflow 設計パターン

ADK 2.0 では、従来の単純な逐次実行や転送（Transfer）モデルに加え、**グラフベースのオーケストレーション (`Workflow`)** が導入されました。これにより、条件分岐、並列処理（Fan-Out）、同期集約（Fan-In）を柔軟に構築できます。

---

## 1. 主要コンポーネント

| クラス | 役割 | 使用例 |
| :--- | :--- | :--- |
| **`START`** | ワークフローの開始エントリポイント | `(START, triage_agent)` |
| **`LlmAgent`** | LLM による推論・Tool Calling を行うエージェント | `triage_agent`, `draft_agent` |
| **`FunctionNode`** | Python 関数を実行する制御ノード（ルーティング判定、データ変換など） | `route_decision_node` |
| **`JoinNode`** | 複数の並列ブランチの完了を待機・同期する集約ノード (Fan-In) | `gather_research` |
| **`Workflow`** | エッジ（ノード間の接続関係）を束ねる最上位コンテナ | `root_agent = Workflow(...)` |

---

## 2. 設計パターン

### A. 条件分岐 (Routing)
`FunctionNode` の中で `ctx.route` に分岐先キーを設定し、`edges` で辞書形式で次のノードを指定します。

```python
def decide_route(ctx: Context, node_input: str = "") -> str:
    if "緊急度: 高" in ctx.state.get("triage_result", ""):
        ctx.route = "deep_check"
    else:
        ctx.route = "quick_reply"
    return f"Selected: {ctx.route}"

route_node = FunctionNode(name="route_node", func=decide_route)

edges = [
    (START, triage_agent, route_node, {
        "deep_check": parallel_trigger,
        "quick_reply": quick_response_agent,
    }),
]
```

### B. 並列実行 (Fan-Out) & 同期集約 (Fan-In)
1つのトリガーから複数のエージェントを同時に起動し、`JoinNode` で同期します。

```python
parallel_trigger = FunctionNode(name="trigger", func=lambda ctx, inp="": str(inp))
gather_node = JoinNode(name="gather")

edges = [
    # Fan-Out
    (parallel_trigger, search_agent, gather_node),
    (parallel_trigger, db_agent, gather_node),
    (parallel_trigger, risk_agent, gather_node),

    # Fan-In 完了後の後続処理
    (gather_node, draft_agent, quality_agent),
]
```

---

## 3. セッションステートとプレースホルダー連携

各 `LlmAgent` に `output_key` を指定することで、エージェントの出力結果が自動的にセッションステート（`ctx.state`）に保存されます。
後続エージェントのプロンプト内では、`{key?}` 構文で安全に参照可能です。

```python
# エージェント側
triage_agent = LlmAgent(
    name="triage_agent",
    output_key="triage_result",
    instruction="...",
)

# 後続プロンプト内
DRAFT_INSTRUCTION = """
以下のトリアージ結果および調査内容を踏まえて回答を作成してください。

【トリアージ結果】
{triage_result?}

【ナレッジ検索結果】
{knowledge_result?}
"""
```
