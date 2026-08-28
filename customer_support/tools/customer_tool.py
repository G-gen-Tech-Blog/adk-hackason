"""顧客情報・契約ステータス照会のモックツール

実際の運用では、CRM（Salesforce, HubSpot等）や契約管理データベースと連携する部分を
ハッカソン向けにインメモリの顧客データ検索で再現しています。
"""

from typing import Dict, Optional

# モック用の顧客データベース
CUSTOMER_DATABASE: Dict[str, Dict[str, str]] = {
    "サンプル商事": {
        "customer_id": "CUST-1001",
        "company_name": "株式会社サンプル商事",
        "plan": "Enterprise",
        "contract_status": "契約中 (利用期間: 3年4ヶ月)",
        "sla_response_time": "1時間以内 (24時間365日サポート)",
        "tam_assigned": "あり (担当TAM: 佐藤)",
        "monthly_spend": "¥500,000/月",
        "notes": "重要VIP顧客。直近でシステムリニューアルを控えており、安定稼働を強く要望されている。",
    },
    "テストテクノロジー": {
        "customer_id": "CUST-1002",
        "company_name": "テストテクノロジー株式会社",
        "plan": "Standard",
        "contract_status": "契約中 (利用期間: 6ヶ月)",
        "sla_response_time": "4営業時間以内 (平日 9:00-18:00)",
        "tam_assigned": "なし",
        "monthly_spend": "¥50,000/月",
        "notes": "直近でAPI利用量が増加傾向。Enterpriseプランへのアップグレード提案候補。",
    },
    "グローバルイノベーション": {
        "customer_id": "CUST-1003",
        "company_name": "グローバルイノベーション合同会社",
        "plan": "Enterprise",
        "contract_status": "契約更新月 (利用期間: 1年)",
        "sla_response_time": "1時間以内 (24時間365日サポート)",
        "tam_assigned": "あり (担当TAM: 高橋)",
        "monthly_spend": "¥800,000/月",
        "notes": "解約リスク警戒フラグあり。過去に障害対応の遅れで不満を持たれた経緯あり、最優先で丁寧な対応が必要。",
    },
    "スタートアップラボ": {
        "customer_id": "CUST-1004",
        "company_name": "スタートアップラボ",
        "plan": "Starter (トライアル)",
        "contract_status": "無料トライアル中 (残り7日)",
        "sla_response_time": "翌営業日以内",
        "tam_assigned": "なし",
        "monthly_spend": "¥0",
        "notes": "新規見込み顧客。導入検討中のため、迅速・親切なサポートで有料化を促す。",
    },
}


def get_customer_info(customer_id_or_name: str) -> str:
    """顧客IDまたは企業名・顧客名から、契約プランやSLA、対応時の特記事項を照会します。

    Args:
        customer_id_or_name: 顧客ID（例: "CUST-1001"）または会社名・顧客名（例: "サンプル商事", "グローバルイノベーション"）

    Returns:
        顧客の契約ステータスおよび対応考慮事項（Markdownテキスト形式）。特定できない場合は汎用顧客ステータスを返します。
    """
    cleaned_input = customer_id_or_name.strip()

    # IDまたは企業名での検索
    matched_cust = None
    for key, cust in CUSTOMER_DATABASE.items():
        if (
            cleaned_input.lower() in key.lower()
            or key.lower() in cleaned_input.lower()
            or cleaned_input.upper() == cust["customer_id"]
            or cleaned_input in cust["company_name"]
        ):
            matched_cust = cust
            break

    if not matched_cust:
        return (
            f"【顧客照会結果】\n"
            f"指定された顧客情報（'{customer_id_or_name}'）は見つかりませんでした。\n"
            f"・プラン: 一般（未登録 / スタンダード相当）\n"
            f"・SLA目安: 翌営業日以内\n"
            f"・対応方針: 問い合わせ元の会社名・ユーザーIDの確認を依頼してください。"
        )

    return (
        f"【顧客・契約照会結果】\n"
        f"・会社名: {matched_cust['company_name']} (ID: {matched_cust['customer_id']})\n"
        f"・契約プラン: {matched_cust['plan']}\n"
        f"・契約状況: {matched_cust['contract_status']}\n"
        f"・SLA保証時間: {matched_cust['sla_response_time']}\n"
        f"・専任TAM: {matched_cust['tam_assigned']}\n"
        f"・月額利用規模: {matched_cust['monthly_spend']}\n"
        f"・特記事項/注意事項: {matched_cust['notes']}"
    )
