"""カスタマーサポート向け問い合わせ自動トリアージ＆回答ドラフト作成ワークフロー

本ファイルは、Google の Agent Development Kit (ADK) 2.0 の
最新グラフベース・オーケストレーション (Workflow / Edge / Node / JoinNode) を
使用したマルチエージェント・ワークフロー定義です。

【ワークフロー構造】
- (A) 条件分岐 (Routing):
    START -> triage_agent -> route_decision_node -> {
        "deep_check": parallel_trigger (詳細調査へ),
        "quick_reply": quick_response_agent (クイック返信へ)
    }
- (B) Fan-Out (並列実行):
    parallel_trigger から 3 つの独立した調査エージェントへ同時に分岐
    - knowledge_search_agent (社内ナレッジ検索)
    - customer_info_agent (顧客・契約情報照会)
    - risk_analysis_agent (感情・リスク分析)
- (C) Fan-In (同期・集約) & ドラフト作成:
    3 つの調査完了を gather_research (JoinNode) で集約 -> draft_creation_agent
- (D) 品質・ポリシーチェック:
    draft_creation_agent / quick_response_agent -> quality_check_agent -> 最終確定版
"""

import os
from typing import Any
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.models import Gemini
from google.adk.workflow import FunctionNode, JoinNode, START, Workflow

from .prompts import (
    CUSTOMER_INSTRUCTION,
    DRAFT_INSTRUCTION,
    KNOWLEDGE_INSTRUCTION,
    QUALITY_INSTRUCTION,
    QUICK_RESPONSE_INSTRUCTION,
    RISK_INSTRUCTION,
    TRIAGE_INSTRUCTION,
    TriageResult,
)
from .tools import get_customer_info, search_knowledge_base

# .env ファイルから環境変数を読み込み（override=True でコンテナ内環境変数を上書き可能にする）
load_dotenv(override=True)

# Gemini Enterprise Agent Platform（旧称 Vertex AI） バックエンドの有効化（デフォルトで Agent Platform を使用）
if os.getenv("GOOGLE_GENAI_USE_VERTEXAI") is None and os.getenv("GOOGLE_GENAI_USE_ENTERPRISE") is None:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

# 使用する Gemini モデル（デフォルト: gemini-3.7-flash）
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")

# モデル呼び出しのエンドポイントロケーション
# Agent Runtime は us-central1 などの実リージョンにデプロイされますが、
# gemini-3.7-flash 等のモデル推論は global エンドポイントを指定します。
MODEL_LOCATION = os.getenv("GEMINI_LOCATION", "global")
os.environ["GOOGLE_CLOUD_LOCATION"] = MODEL_LOCATION

# global エンドポイントを明示指定した Gemini モデルインスタンス
gemini_model = Gemini(
    model=MODEL_NAME,
    client_kwargs={"location": MODEL_LOCATION},
)

# ==============================================================================
# 1. 各専門エージェントの定義 (LlmAgent)
# ==============================================================================

# Step 1: トリアージエージェント (構造化出力: TriageResult)
triage_agent = LlmAgent(
    name="triage_agent",
    model=gemini_model,
    instruction=TRIAGE_INSTRUCTION,
    output_schema=TriageResult,
    output_key="triage_result",
    description="顧客からの問い合わせ内容を分析し、カテゴリ分類と緊急度を判定するエージェント",
)

# Step 2-A: ナレッジ検索エージェント (Tool: search_knowledge_base)
knowledge_search_agent = LlmAgent(
    name="knowledge_search_agent",
    model=gemini_model,
    instruction=KNOWLEDGE_INSTRUCTION,
    tools=[search_knowledge_base],
    output_key="knowledge_result",
    description="社内FAQやナレッジベースから解決に関連する技術情報・仕様を検索するエージェント",
)

# Step 2-B: 顧客情報・契約照会エージェント (Tool: get_customer_info)
customer_info_agent = LlmAgent(
    name="customer_info_agent",
    model=gemini_model,
    instruction=CUSTOMER_INSTRUCTION,
    tools=[get_customer_info],
    output_key="customer_result",
    description="顧客の契約プラン（Enterprise/Standard等）、SLA、担当TAM等の情報を照会するエージェント",
)

# Step 2-C: 感情・リスク分析エージェント
risk_analysis_agent = LlmAgent(
    name="risk_analysis_agent",
    model=gemini_model,
    instruction=RISK_INSTRUCTION,
    output_key="risk_result",
    description="顧客の感情トーン（怒り・焦り等）や解約・炎上リスクをスコアリングするエージェント",
)

# 分岐ルート: クイック返信エージェント（簡易な定型質問・挨拶用）
quick_response_agent = LlmAgent(
    name="quick_response_agent",
    model=gemini_model,
    instruction=QUICK_RESPONSE_INSTRUCTION,
    output_key="draft_result",
    description="詳細な調査が不要な簡易問い合わせに対して迅速な一次返信ドラフトを作成するエージェント",
)

# Step 3: 回答ドラフト作成エージェント (Fan-In 後の集約)
draft_creation_agent = LlmAgent(
    name="draft_creation_agent",
    model=gemini_model,
    instruction=DRAFT_INSTRUCTION,
    output_key="draft_result",
    description="3つの分析結果を集約し、オペレーター向けサマリと顧客向け返信ドラフトを作成するエージェント",
)

# Step 4: 品質・ポリシーチェックエージェント
quality_check_agent = LlmAgent(
    name="quality_check_agent",
    model=gemini_model,
    instruction=QUALITY_INSTRUCTION,
    output_key="final_result",
    description="ビジネスマナー、トーン＆マナー、NG表現をチェックし、確定版の最終回答パッケージを出力するエージェント",
)

# ==============================================================================
# 2. ルーティング & 制御ノードの定義 (FunctionNode / JoinNode)
# ==============================================================================


def decide_route(ctx: Context, node_input: Any = None) -> str:
    """トリアージ結果に基づいて後続のルート（詳細調査 or クイック返信）を決定します。

    - カテゴリが「その他」かつ緊急度が「低」の場合: quick_reply
    - 技術的課題、不具合、契約/請求、または中〜高緊急度の場合: deep_check
    """
    triage_raw = ctx.state.get("triage_result") or node_input

    category = ""
    urgency = ""

    # 1. Pydantic モデルインスタンスの場合
    if isinstance(triage_raw, TriageResult):
        category = triage_raw.category
        urgency = triage_raw.urgency
    # 2. 辞書形式の場合
    elif isinstance(triage_raw, dict):
        category = triage_raw.get("category", "")
        urgency = triage_raw.get("urgency", "")
    # 3. 文字列形式（JSON 文字列 または プレーンテキスト）の場合
    elif isinstance(triage_raw, str):
        try:
            parsed = TriageResult.model_validate_json(triage_raw)
            category = parsed.category
            urgency = parsed.urgency
        except Exception:
            # フォールバック（プレーンテキスト形式の解析）
            if "カテゴリ: その他" in triage_raw or "その他" in triage_raw:
                category = "その他"
            if "緊急度: 低" in triage_raw or "低" in triage_raw:
                urgency = "低"

    # カテゴリが「その他」かつ緊急度が「低」の場合はクイック返信へ
    if category == "その他" and urgency == "低":
        ctx.route = "quick_reply"
    else:
        ctx.route = "deep_check"

    return f"Selected route: {ctx.route}"


def pass_through_trigger(ctx: Context, node_input: Any = None) -> str:
    """Fan-Out（並列実行）用のトリガーノード。入力をそのまま後続エージェントへ中継します。"""
    return str(node_input)


# ルーティング決定ノード
route_decision_node = FunctionNode(
    name="route_decision_node",
    func=decide_route,
)

# 並列実行トリガーノード
parallel_trigger = FunctionNode(
    name="parallel_trigger",
    func=pass_through_trigger,
)

# 並列調査の同期・集約ノード (Fan-In)
gather_research = JoinNode(
    name="gather_research",
)

# ==============================================================================
# 3. ADK 2.0 ワークフロー定義 (Workflow & Edges)
# ==============================================================================

root_agent = Workflow(
    name="customer_support_workflow",
    description="ADK 2.0 グラフベースのカスタマーサポート問い合わせ自動トリアージ＆回答ドラフト作成ワークフロー",
    edges=[
        # --- (A) 条件分岐 (Routing) ---
        # 開始 -> トリアージエージェント -> ルート判定ノード -> ルーティング
        (
            START,
            triage_agent,
            route_decision_node,
            {
                "deep_check": parallel_trigger,       # 詳細調査時は並列トリガーへ
                "quick_reply": quick_response_agent, # 簡易回答時はクイック返信エージェントへ
            },
        ),

        # --- (B) Fan-Out（並列実行） ---
        # parallel_trigger から 3 つの独立した調査へ同時に分岐
        (parallel_trigger, knowledge_search_agent, gather_research),
        (parallel_trigger, customer_info_agent, gather_research),
        (parallel_trigger, risk_analysis_agent, gather_research),

        # --- (C) Fan-In（同期・集約） & ドラフト作成 ---
        # 3つの調査がすべて完了したら gather_research から回答ドラフト作成エージェントへ接続
        (gather_research, draft_creation_agent, quality_check_agent),

        # --- (D) クイック返信ルートの品質チェック ---
        # クイック返信ルートも最終的に品質チェックエージェントを通る
        (quick_response_agent, quality_check_agent),
    ],
)

# エイリアス
workflow = root_agent
