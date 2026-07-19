# Blendarium

Blendarium は、Blender 内で使う複数の自作ツールを 1 つのアドオンに統合して提供する**ツールプラットフォーム**です。
Blender 4.2 以降の **Extension（拡張機能）形式**で実装されており、個々のツールは共通基盤
（ツールレジストリ / UI シェル / 設定永続化 / ログ / エラー隔離）の上に載ります。

- 📖 **API リファレンス（自動生成）**: <https://genki1231.github.io/blendarium/>
- 📝 **変更履歴**: [CHANGELOG.md](CHANGELOG.md)（Conventional Commits から自動生成）
- 📋 **要件定義 / 詳細設計**: [blendarium_requirements.md](blendarium_requirements.md) / [blendarium_design.md](blendarium_design.md)

## ファイル構成

```
blendarium/
├── blender_manifest.toml    # Extension のメタ情報（名前・バージョン・ライセンス・ビルド除外）
├── __init__.py              # エントリポイント（register / unregister）
├── core/                    # 共通基盤
│   ├── registry.py          #   ツールの発見・契約検証・登録（エラー隔離付き）
│   ├── prefs.py             #   AddonPreferences（ツール有効/無効トグル）
│   ├── settings.py          #   設定の永続化
│   └── logger.py            #   ログ基盤
├── ui/
│   └── shell.py             # 共通 UI シェル（3D ビューポート N パネル「Blendarium」タブ）
├── tools/                   # 内蔵ツール群（1 ツール = 1 サブパッケージ）
│   ├── hello/               #   サンプルツール（ツール契約の最小例）
│   └── scene_stats/         #   シーン統計（オブジェクト数・ポリゴン数などを集計 / JSON・Markdown 出力）
├── dev/                     # 開発専用（本番 ZIP には含まれない）
│   └── run_scene_stats.py   #   scene_stats のヘッドレス実行スクリプト
├── dev_loader.py            # 開発用ブートストラップ（本番 ZIP には含まれない）
├── launch_blender.bat       # 開発用起動バッチ（dev_loader.py 経由で Blender を起動）
├── docs/ + mkdocs.yml       # ドキュメントサイト（MkDocs、API ページは docstring から自動生成）
└── .github/workflows/       # CI（docs: GitHub Pages デプロイ / changelog: CHANGELOG 自動更新）
```

各ツールは **logic 層**（`bpy` の UI/コンテキストに依存しない処理本体。ヘッドレス実行可能）と
**ui 層**（パネル・オペレーター等の薄い皮）に分離されています。

## 内蔵ツール

| ツール | 内容 |
|---|---|
| **Hello** | 「Say Hello」ボタンで挨拶を表示するサンプル。ツール契約の最小実装例 |
| **Scene Stats** | オブジェクト数（種別ごと）・ポリゴン数・メッシュ / マテリアル / コレクション / 画像数を集計し、JSON / Markdown でエクスポート |

### Scene Stats のヘッドレス実行（UI なし）

```
blender -b <file.blend> --python dev/run_scene_stats.py -- --output <path.json> [--format JSON|MARKDOWN]
```

## 開発中の起動（インストール不要）

**`launch_blender.bat` をダブルクリック**すると、`dev_loader.py` がこのフォルダを
正しい Python パッケージとして import して `register()` を実行した状態で Blender が起動します。
ZIP 化もインストールも不要です。

- `__init__.py` を直接 `--python` で実行すると親パッケージが無いため、
  `from . import ...`（相対 import）が失敗します。必ず `dev_loader.py` 経由で起動してください。
- **既知の制限**: `dev_loader` 起動時はアドオンとして有効化されていないため
  AddonPreferences が取得できず、ツールの有効/無効トグルは ZIP インストール時のみ機能します。

## インストール手順

1. リポジトリのルートで次を実行し、配布用 ZIP をビルドします
   （`blender_manifest.toml` の除外設定により、開発用ファイルは自動的に除かれます）:

   ```
   blender --command extension build
   ```

2. Blender を起動し、**Edit > Preferences（設定）> Get Extensions** を開きます。
3. 画面右上の **∨（ドロップダウン）> Install from Disk...** で手順 1 の ZIP を選択します。
4. 一覧に **「Blendarium」** が現れるので、チェックを入れて有効化します。
5. 有効化後、Preferences のアドオン設定からツールごとの有効/無効を切り替えられます。

## 使い方

1. **3D ビューポート**にマウスを置き、**N キー**でサイドバーを開きます。
2. **「Blendarium」タブ**を選ぶと、共通シェルと各ツールのパネル（Hello / Scene Stats）が表示されます。

## ツールを追加するには

`tools/` 直下に新しいサブパッケージ（例: `tools/my_tool/`）を作り、`__init__.py` で
**ツール契約**（モジュール属性 + 関数）を実装するだけで、レジストリが自動発見・登録します:

```python
TOOL_ID: str = "my_tool"          # フォルダ名と一致させる
TOOL_LABEL: str = "My Tool"       # 表示名
TOOL_DESCRIPTION: str = "..."     # 説明
TOOL_ORDER: int = 30              # 昇順の登録・表示順

def register() -> None: ...       # クラス登録
def unregister() -> None: ...     # クラス解除（逆順）
```

ツールの登録に失敗しても**エラーは隔離**され、他のツールとプラットフォーム本体は動き続けます。
`logic.py`（`bpy` UI 非依存）と `ui.py` を分けて実装してください。

## ドキュメントのビルド（任意・ローカル確認用）

GitHub の main ブランチへ push すると、GitHub Actions が自動でサイトをビルド・公開します。
ローカルでプレビューしたい場合:

```
pip install -r requirements-docs.txt
mkdocs serve
```

## ライセンス

GPL-3.0-or-later（[LICENSE.md](LICENSE.md) を参照）。
`bpy` に依存するアドオンは GPL 派生物と見なされるため、
Blender Extensions として配布する場合は GPL 互換ライセンスが必須です。
