# Blendarium（Blender アドオンひな形）

Blender 4.2 以降の **Extension（拡張機能）形式**による、学習用の最小アドオンのひな形です。
「ボタンを1つ押すとメッセージが出る」だけの構成で、アドオン開発の基本形
（Operator / Panel / register・unregister）を学べます。

## ファイル構成

```
blendarium/
├── blender_manifest.toml   # 拡張機能のメタ情報（名前・バージョン・ライセンスなど）
├── __init__.py             # アドオン本体（Operator + Panel + register/unregister）
├── dev_loader.py           # 開発用ブートストラップ（本番 ZIP には含まれない）
├── launch_blender.bat      # 開発用起動バッチ（dev_loader.py 経由で Blender を起動）
└── README.md               # このファイル
```

- **blender_manifest.toml**: 旧来の `bl_info` 辞書に代わる設定ファイル。TOML 形式。
- **__init__.py**: 有効化時に `register()`、無効化時に `unregister()` が呼ばれます。
- **dev_loader.py / launch_blender.bat**: 開発時専用。ビルド除外設定により本番 ZIP には入りません。

## 開発中の起動（インストール不要）

**`launch_blender.bat` をダブルクリック**すると、`dev_loader.py` がこのフォルダを
正しい Python パッケージとして import して `register()` を実行した状態で
Blender が起動します。ZIP 化もインストールも不要です。

- `__init__.py` を直接 `--python` で実行すると親パッケージが無いため、
  `from . import ...`（相対 import）が失敗します。`dev_loader.py` 経由なら
  複数ファイル構成に育てても問題ありません。
- 本番（ZIP インストール後）は Blender が通常どおり `__init__.py` から起動します。

## インストール手順（Blender 5.1）

1. この `blendarium` フォルダを ZIP に圧縮します（フォルダを右クリック →「ZIP に圧縮」）。
2. Blender を起動し、**Edit > Preferences（設定）> Get Extensions** を開きます。
3. 画面右上の **∨（ドロップダウン）> Install from Disk...** を選びます。
4. 手順1で作った ZIP を選択します。
5. 一覧に **「Blendarium」** が現れるので、チェックを入れて有効化します。

> メモ: 開発中は毎回 ZIP にせず、未圧縮フォルダをローカルのアドオン置き場に直接置く方法もあります。

## 使い方

1. **3D ビューポート**にマウスを置き、**N キー**を押してサイドバー（N パネル）を開きます。
2. **「Blendarium」タブ**を選びます。
3. **「Say Hello」ボタン**を押すと、画面下のステータスバーに
   `Hello from Blendarium` と表示されます。

## 機能を追加するには

`__init__.py` に新しい Operator や Panel クラスを追加し、
末尾の `classes` タプルにそのクラスを加えるだけで、
`register()` / `unregister()` が自動的に処理します。

```python
classes = (
    BLENDARIUM_OT_hello,
    BLENDARIUM_PT_panel,
    # ここに追加したクラスを書き足す
)
```

## ライセンス

MIT License（`LICENSE.md` を参照）。
`blender_manifest.toml` の `maintainer` は各自の名前・メールに書き換えてください。
