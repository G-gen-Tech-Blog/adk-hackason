"""社内FAQ・ナレッジベース検索のモックツール

実際の運用では、社内ドキュメント検索APIやVector DB (RAG) 等と連携する部分を
ハッカソン向けにインメモリの辞書検索で再現しています。
"""

from typing import Dict, List

# モック用の社内ナレッジベースデータ
KNOWLEDGE_BASE: List[Dict[str, str]] = [
    {
        "id": "KB-001",
        "category": "技術的課題",
        "title": "APIレート制限（429 Too Many Requests）の仕様と対処法",
        "content": (
            "【概要】Standardプランは1分あたり60リクエスト、Enterpriseプランは1分あたり300リクエストの制限があります。\n"
            "【エラー対処】HTTP 429が発生した場合は、レスポンスヘッダーの 'Retry-After' を参照して待機後、指数バックオフで再試行してください。\n"
            "【上限緩和】Enterpriseプランのお客様は、管理画面の「クォータ拡張申請」または専任担当経由で上限引き上げが可能です。"
        ),
    },
    {
        "id": "KB-002",
        "category": "技術的課題",
        "title": "二要素認証（2FA）の再設定・リセット手順",
        "content": (
            "【概要】端末紛失等で2FA認証コードが受信できない場合の対応フローです。\n"
            "【手順】1. 契約管理者のメールアドレスから本人確認書類の提出を依頼する。\n"
            "2. 管理者権限で管理画面 '設定 > ユーザー管理' から該当ユーザーの2FAを無効化する。\n"
            "3. ユーザーに再ログインおよび再設定の案内メールを送信する。"
        ),
    },
    {
        "id": "KB-003",
        "category": "不具合報告",
        "title": "ダッシュボードのデータ同期遅延・表示エラー",
        "content": (
            "【概要】深夜バッチ処理（JST 02:00〜04:00）中や大量データ集計時に表示遅延（最大15分程度）が発生することがあります。\n"
            "【切り分け】ブラウザキャッシュのクリア、またはシークレットウィンドウでの再現性を確認してください。\n"
            "【エスカレーション】15分以上遅延が継続している、または500 Internal Server Errorが表示されている場合は、SREチームへ緊急連絡してください。"
        ),
    },
    {
        "id": "KB-004",
        "category": "契約/請求",
        "title": "プラン変更（アップグレード/ダウングレード）の適用タイミングと日割り計算",
        "content": (
            "【アップグレード】即時反映され、当月の残日数分の日割り差額が翌月請求に合算されます。\n"
            "【ダウングレード】申請月の末日まで現在のプランが適用され、翌月1日より新プランへ切り替わります（日割り返金は行いません）。\n"
            "【手続き】契約者アカウントにて 'アカウント設定 > 契約プラン' よりオンラインで即時変更可能です。"
        ),
    },
    {
        "id": "KB-005",
        "category": "契約/請求",
        "title": "請求書払い（後払い）の要件と発行サイクル",
        "content": (
            "【利用条件】Enterpriseプランをご契約の法人企業様のみ請求書払いに対応しています（Standardプランはクレジットカード決済のみ）。\n"
            "【請求書発行日】毎月末締め、翌月第2営業日にPDF請求書をメール送付します。お支払い期日は翌月末日です。"
        ),
    },
    {
        "id": "KB-006",
        "category": "機能要望",
        "title": "新機能要望・ロードマップへのフィードバック手順",
        "content": (
            "【概要】顧客から新機能要望を受領した場合は、プロダクトフィードバックボードに登録します。\n"
            "【回答テンプレート】「貴重なご意見ありがとうございます。開発チームのロードマップ検討会議にて共有させていただきます。個別機能の実装確約はいたしかねますが、リリース予定が決まり次第お知らせします。」と案内してください。"
        ),
    },
    {
        "id": "KB-007",
        "category": "全般",
        "title": "サービス稼働状況（ステータスページ）および障害連絡窓口",
        "content": (
            "【ステータスページ】https://status.example.com にてリアルタイムの稼働状況を公開しています。\n"
            "【緊急連絡先】SLA保証のあるEnterpriseプランの重大障害（Severity 1）時は、24時間365日対応のホットラインをご利用いただけます。"
        ),
    },
]


def search_knowledge_base(query: str, category: str = "") -> str:
    """社内ナレッジベースおよびFAQから、問い合わせ内容に関連する記事を検索します。

    Args:
        query: 検索キーワードや問い合わせ内容の要約（例: "レート制限 429", "プラン変更 日割り"）
        category: 絞り込みカテゴリ（オプション。例: "技術的課題", "契約/請求", "不具合報告", "機能要望"）

    Returns:
        検索結果の一覧（Markdownテキスト形式）。該当記事がない場合は汎用案内を返します。
    """
    query_lower = query.lower()
    keywords = [kw for kw in query_lower.replace("、", " ").replace("。", " ").split() if len(kw) > 1]

    matched_articles = []
    for article in KNOWLEDGE_BASE:
        # カテゴリの一致チェック（指定がある場合）
        if category and category != "その他" and category not in article["category"]:
            continue

        # キーワードマッチングスコア計算
        score = 0
        search_target = f"{article['title']} {article['content']} {article['category']}".lower()

        for kw in keywords:
            if kw in search_target:
                score += 1

        if score > 0 or not keywords:
            matched_articles.append((score, article))

    # スコア順にソート（スコア降順）
    matched_articles.sort(key=lambda x: x[0], reverse=True)

    # 結果のフォーマット
    if not matched_articles:
        # カテゴリ縛りでヒットしなかった場合はカテゴリ無視で再検索
        if category:
            return search_knowledge_base(query=query, category="")
        return (
            "【ナレッジ検索結果】\n"
            "該当するナレッジ記事が見つかりませんでした。\n"
            "一般的なサポート対応手順に従い、顧客への詳細ヒアリングまたはテクニカルサポートへのエスカレーションを検討してください。"
        )

    results_text = ["【社内ナレッジ検索結果】"]
    for score, article in matched_articles[:3]:  # 上位最大3件
        results_text.append(
            f"■ [{article['id']}] {article['title']} (カテゴリ: {article['category']})\n"
            f"{article['content']}\n"
        )

    return "\n".join(results_text)
