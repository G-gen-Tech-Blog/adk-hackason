# トラブルシューティング & 診断ガイド

## 1. POST `/run_sse` 404 Not Found (プロンプトを送信してもLLMが動かない)

### 現象
- Web UI でメッセージを送信すると、ログに以下が出力され、応答が返ってこない。
  ```text
  INFO: 127.0.0.1:xxxxx - "POST /apps/<app_name>/users/user/sessions HTTP/1.1" 200 OK
  INFO: 127.0.0.1:xxxxx - "POST /run_sse HTTP/1.1" 404 Not Found
  ```

### 原因
1. **ディレクトリ名 / エージェント名にハイフン (`-`) が含まれている:**
   - ADK の `AgentLoader` はエージェントを動的インポートする際、Python の有効な識別子（英数字・`_`）のみを受け付けます。
   - ハイフンが含まれていると `ValueError: Invalid agent name` が発生し、FastAPI サーバーが `404 Not Found` を返します。
2. **`root_agent` がエクスポートされていない:**
   - パッケージ内の `agent.py` または `__init__.py` に `root_agent` 変数が定義されていない。

### 診断コマンド
以下の Python スクリプトを実行することで、プロジェクト内のエージェントが正しく読み込めるかを即座にテストできます。

```bash
python3 -c "
from google.adk.cli.utils.agent_loader import AgentLoader
loader = AgentLoader('.')
print('検出されたエージェント一覧:', loader.list_agents())
for app_info in loader.list_agents_detailed():
    print('  - アプリ名:', app_info['name'], '| Root Agent:', app_info['root_agent_name'])
"
```

---

## 2. GET `/dev-ui/chunk-*.js` 403 Forbidden (UI画面が真っ白・崩れる)

### 原因
Cloud Shell やリモート開発環境などの未許可オリジンからアクセスしているため、`_OriginCheckMiddleware` で拒否されています。

### 解決策
`--allow_origins` を指定して起動します。
```bash
adk web --port 8080 --allow_origins="regex:.*"
```

---

## 3. Gemini Enterprise Agent Platform（旧称 Vertex AI） 認証・プロジェクト設定エラー

### 現象
- LLM 呼び出し時に `DefaultCredentialsError` や `PermissionDenied` が発生する。

### 解決策
1. `.env` の設定を確認する：
   ```env
   GOOGLE_GENAI_USE_VERTEXAI=1
   GOOGLE_CLOUD_PROJECT="your-project-id"
   GOOGLE_CLOUD_LOCATION="global"
   ```
2. Cloud Shell / ローカル端末で Gemini Enterprise Agent Platform（旧称 Vertex AI） API が有効化されているか確認：
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

---

## 4. Agent Runtime デプロイ時のハング / モデル呼び出し 404 エラー

### 現象 1: デプロイコマンド（`adk deploy agent_engine`）を実行すると処理が固まる
- **原因**: `--region="global"` を指定している。Agent Runtime（Reasoning Engine）は `global` リージョンへのデプロイに対応していません。
- **解決策**: `--region="us-central1"` などのサポートされている物理リージョンを指定します。

### 現象 2: `us-central1` にデプロイ後、モデル呼び出しで 404 エラーになる
- **原因**: `adk deploy agent_engine --region=us-central1` でデプロイすると、コンテナ環境変数に `GOOGLE_CLOUD_LOCATION=us-central1` が自動設定され、`gemini-3.7-flash` 等の global エンドポイント対応モデルが `us-central1` を参照してしまう。
- **解決策**: `agent.py` 内で `Gemini(model=MODEL_NAME, client_kwargs={"location": "global"})` を使用し、モデル呼び出しエンドポイントを明示的に `global` に指定します。
