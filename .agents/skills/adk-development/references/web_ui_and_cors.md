# Web UI 起動と CORS / 403 Forbidden 対策

## 1. `adk web` コマンドの基本

ADK は FastAPI + Angular (Dev UI) を内蔵したローカル Web サーバーを提供します。

```bash
# 基本起動コマンド
adk web --port 8080 --allow_origins="regex:.*"
```

---

## 2. 403 Forbidden エラーの原因と対策

### 発生現象
ブラウザから `http://127.0.0.1:8080/dev-ui/` にアクセスした際、HTML や CSS は正常に 200 OK で返るが、**JavaScript ファイル (`chunk-*.js`, `main-*.js`) のみが `403 Forbidden` となり画面が真っ白になる** 現象。

### 原因
1. **Google Cloud Shell / リモート開発環境でのアクセス:**
   - Cloud Shell の「ウェブでプレビュー」機能（`https://*.cloudshell.dev`）やリバースプロキシ経由でアクセスすると、ブラウザが ES Modules を CORS モードで取得します。
   - ADK 内の `_OriginCheckMiddleware` はデフォルトで loopback (`localhost`, `127.0.0.1`) のみを許可しているため、外部オリジンからのリクエストが `403 Forbidden` で拒絶されます。
2. **ブラウザ拡張機能（広告ブロック・スクリプトブロッカー）:**
   - `uBlock Origin` や `Brave Shields` などの拡張機能が `chunk-*.js` を誤認してブロックすることがあります。

### 解決策
1. **`--allow_origins` フラグを付けて起動する (推奨):**
   ```bash
   # 全てのオリジンを許可（開発環境用）
   adk web --port 8080 --allow_origins="regex:.*"

   # Google Cloud Shell のみを許可する場合
   adk web --port 8080 --allow_origins="regex:https://.*\.cloudshell\.dev"
   ```
2. **ブラウザ拡張機能を一時停止する / シークレットウィンドウで開く**
3. **ブラウザの強制再読み込み（スーパーリロード）:**
   - `Ctrl + Shift + R` (Win/Linux) または `Cmd + Shift + R` (Mac)

---

## 3. ホスト指定 (`--host`)

外部ホストやローカルネットワーク上の別マシンからアクセスしたい場合は、`--host 0.0.0.0` を指定します。

```bash
adk web --host 0.0.0.0 --port 8080 --allow_origins="regex:.*"
```
