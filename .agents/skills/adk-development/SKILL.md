---
name: adk-development
description: >-
  Google Agent Development Kit (ADK) 2.0 を使用したマルチエージェント開発、プロジェクト構成のベストプラクティス、Workflow設計、Web UI (adk web) 起動設定、および 403/404 トラブルシューティングを行う際に使用する知見・手順集。
---

# ADK 2.0 開発ベストプラクティス & ガイド

Google Agent Development Kit (ADK) 2.0 によるマルチエージェントシステムの開発、適切なディレクトリ設計、Web UI 実行、トラブルシューティングのための実践的ガイドです。

---

## 🚀 クイックチェックリスト

1. **ディレクトリ名**: エージェントのパッケージフォルダ名は必ず **Python の有効な識別子（半角英数字と `_` のみ）** にする（ハイフン `-` は使用禁止）。
2. **Web UI 起動**: Cloud Shell やリモート開発環境では必ず `--allow_origins="regex:.*"` を付与する。
3. **ワークフロー構造**: 依存関係や並列処理は ADK 2.0 の `Workflow`, `FunctionNode`, `JoinNode` を用いてグラフ定義する。
4. **ステート管理**: 各エージェントに `output_key` を設定し、後続エージェントのプロンプトで `{output_key?}` として参照する。

---

## 📚 リファレンス一覧

詳細な手順と解説は以下のリファレンスを参照してください：

- [ディレクトリ構成と命名規則](./references/directory_structure_and_naming.md)
  - リポジトリ名にハイフンが含まれる場合の対処法
  - マルチエージェント構成と単一エージェント構成の使い分け
  - 相対インポートと `__init__.py` の配置
- [Web UI 起動と CORS / 403 対策](./references/web_ui_and_cors.md)
  - `adk web` コマンドオプション
  - Cloud Shell / リバースプロキシでの 403 Forbidden 回避策
- [ADK 2.0 Workflow 設計パターン](./references/workflow_and_nodes.md)
  - 条件分岐（Routing: `FunctionNode` + `ctx.route`）
  - 並列実行（Fan-Out）と同期・集約（Fan-In: `JoinNode`）
- [トラブルシューティング & 診断スクリプト](./references/troubleshooting.md)
  - `POST /run_sse 404 Not Found` (LLM が動かない) の原因特定
  - `AgentLoader` を使ったエージェント読み込み事前テスト
