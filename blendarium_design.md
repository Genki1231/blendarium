# Blendarium 詳細設計書

| 項目 | 内容 |
|---|---|
| ドキュメントバージョン | v0.1(ドラフト・レビュー待ち) |
| 作成日 | 2026-07-18 |
| 対応する要件定義書 | `blendarium_requirements.md` v0.2 |
| ステータス | 承認後に実装フェーズ(Codex への実装指示)へ |

---

## 1. 本書の位置づけ

要件定義書 v0.2 で確定した要件(FR / NFR / CON)と決定事項(旧 TBD-01/02/05)を、
実装可能な粒度のモジュール設計・インターフェース定義に落とし込む。
コード・コード内コメントは英語、本書を含むドキュメントは日本語(NFR-003)。

## 2. パッケージ構成(確定版)

```
blendarium/
├── blender_manifest.toml        # Extensions metadata
├── __init__.py                  # register()/unregister() -> core.registry に委譲するだけの薄い入口
├── core/                        # 基盤層(原則 bpy 非依存。prefs.py のみ例外)
│   ├── __init__.py
│   ├── registry.py              # ツール発見・登録・解除・有効/無効・エラー隔離
│   ├── prefs.py                 # AddonPreferences(基盤設定。bpy 依存)
│   ├── settings.py              # ツール個別設定の JSON 永続化
│   └── logger.py                # 共通ロガー(stdlib logging の薄いラッパー)
├── tools/                       # ツール群(1 ツール = 1 サブパッケージ)
│   ├── __init__.py              # 空(スキャン対象マーカー)
│   ├── scene_stats/
│   │   ├── __init__.py          # ツールメタデータ + register/unregister
│   │   ├── logic.py             # ヘッドレス実行可能な処理本体
│   │   └── ui.py                # Panel / Operator(bpy UI 依存)
│   ├── naming_tools/            # 同上の 3 ファイル構成
│   └── data_purge/              # 同上の 3 ファイル構成
├── ui/
│   ├── __init__.py
│   └── shell.py                 # 共通シェル(ルート N-panel + 障害通知)
└── dev/                         # 開発専用(ビルド除外に追加する)
    ├── run_scene_stats.py       # ヘッドレス実行のサンプル(受け入れ基準 5 用)
    └── broken_tool_fixture/     # エラー隔離テスト用の「壊れたツール」(受け入れ基準 4 用)
```

- `dev_loader.py` / `launch_blender.bat` は従来どおりルートに置き、ビルド除外を維持する
- `blender_manifest.toml` の `paths_exclude_pattern` に `/dev/` を追加する

## 3. ツール共通インターフェース(契約)

各ツールの `__init__.py` は以下の**モジュールレベル属性**を必ず定義する。
レジストリはこの契約を検証し、欠落があればそのツールを FAILED として隔離する(FR-CORE-003)。

| 属性 | 型 | 意味 |
|---|---|---|
| `TOOL_ID` | `str` | 一意 ID。フォルダ名と一致必須(例: `"scene_stats"`) |
| `TOOL_LABEL` | `str` | UI 表示名(例: `"Scene Stats"`) |
| `TOOL_DESCRIPTION` | `str` | 1 行説明(パネルの tooltip 等に使用) |
| `TOOL_ORDER` | `int` | シェル内での表示順(昇順)。10 刻み推奨 |
| `register()` | callable | ツールの UI クラス群を Blender に登録する |
| `unregister()` | callable | 登録解除(register の逆順) |

追加規約:

- `logic.py` は `ui.py` を import してはならない(逆方向のみ可)
- `logic.py` は `bpy.context` / `bpy.ops` を使用してはならない。入力は引数
  (`bpy.data` や明示的なオブジェクトリスト)で受け取り、結果は dataclass で返す(FR-CORE-006)
- 破壊的ツールの Operator は `bl_options = {'REGISTER', 'UNDO'}` を必須とし、
  実行前に `invoke_props_dialog()` による確認を挟む(FR-CORE-007)

## 4. core/registry.py

### 4.1 データモデル

```python
class ToolState(Enum):
    DISCOVERED = auto()   # module found, not yet imported
    REGISTERED = auto()   # register() succeeded
    DISABLED = auto()     # user-disabled (import ok, UI not registered)
    FAILED = auto()       # import/contract/register error (isolated)

@dataclass
class ToolRecord:
    tool_id: str
    label: str            # falls back to tool_id when contract is broken
    order: int
    state: ToolState
    module: ModuleType | None
    error: str | None     # formatted traceback for FAILED tools
```

### 4.2 処理フロー

1. **発見**: `pkgutil.iter_modules(tools.__path__)` で `tools/` 直下のサブパッケージを列挙
   (FR-CORE-001。スキャン対象は内蔵フォルダのみだが、スキャン関数はパスを引数に取る形にし
   将来の外部フォルダ拡張を妨げない)
2. **import + 契約検証**: 1 ツールずつ `try/except` で import し、§3 の属性の存在と型を検証。
   失敗時は traceback を `ToolRecord.error` に保存して次のツールへ進む(FR-CORE-003)
3. **登録**: 有効設定(prefs)のツールのみ `register()` を呼ぶ。ここも 1 ツールずつ `try/except`
4. **解除**: アドオン無効化時、REGISTERED の全ツールを登録の逆順で `unregister()`。
   例外が出ても残りの解除を続行する
5. **有効/無効切替**: `set_tool_enabled(tool_id, enabled)` を公開。prefs の update コールバックから
   呼ばれ、対象ツールの register/unregister のみを行う(FR-CORE-002)

### 4.3 エラー隔離の保証(受け入れ基準 4)

- import 失敗・契約違反・register 例外のいずれでも、他ツールと基盤の登録処理は完走する
- FAILED ツールは一覧 API `iter_tools()` に含めて返し、シェルが警告表示に使う(§7)
- 検証手順: `dev/broken_tool_fixture/` を `tools/` へコピーして起動 →
  他ツールが正常動作し、シェルに警告が出ることを確認 → コピーを削除

## 5. core/prefs.py(基盤設定 = AddonPreferences)

```python
class ToolToggle(bpy.types.PropertyGroup):
    # `name` (built-in) holds the tool_id
    enabled: BoolProperty(default=True, update=_on_toggle)  # -> registry.set_tool_enabled

class BlendariumPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__.split(".")[0]
    tool_toggles: CollectionProperty(type=ToolToggle)
    log_level: EnumProperty(items=[DEBUG/INFO/WARNING/ERROR], default='INFO')

    def draw(self, context):
        # one row per tool: label + enabled checkbox
        # FAILED tools are shown greyed-out with an error icon
```

- 保存先は Blender 標準の `userpref.blend`(自動保存)。基盤設定はこの 2 項目のみで開始する
- 起動時、レジストリの発見結果と `tool_toggles` を同期する
  (新ツールは既定 ON で追加、消えたツールのエントリは残置し無視)

## 6. core/settings.py(ツール個別設定 = JSON)

### 6.1 保存場所とファイル形式

- ディレクトリ: `bpy.utils.extension_path_user(__package__, path="settings", create=True)`
- ファイル: `<tool_id>.json`(UTF-8、インデント 2)

```json
{
  "schema_version": 1,
  "data": { }
}
```

### 6.2 公開 API

```python
def load(tool_id: str, defaults: dict) -> dict: ...
def save(tool_id: str, data: dict) -> None: ...
```

- **読込**: ファイルなし → defaults を返す。JSON 破損 → `<tool_id>.json.broken-<UTC timestamp>` に
  退避してから defaults を返し、WARNING ログ(ユーザーデータを黙って捨てない)
- **書込(アトミック)**: 同ディレクトリの一時ファイルに書いてから `os.replace()` で差し替える。
  書き込み途中のクラッシュで既存設定が壊れることを防ぐ
- **マイグレーション**: `schema_version` が古い場合の変換フックを v1 では tool 側関数
  `migrate(old_version, data) -> dict` として任意実装可にする(未実装なら defaults に戻す)

## 7. ui/shell.py(共通シェル)

```python
class BLENDARIUM_PT_shell(bpy.types.Panel):
    bl_label = "Blendarium"
    bl_idname = "BLENDARIUM_PT_shell"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Blendarium"
```

- 各ツールのパネルは `bl_parent_id = "BLENDARIUM_PT_shell"` のサブパネルとして
  `TOOL_ORDER` 順に登録する(旧 TBD-01 決定)
- シェル本体の draw は最小限とし、FAILED ツールが 1 つ以上あるときのみ
  `layout.alert` の警告ボックスで「N tool(s) failed to load — see Preferences」を表示(FR-CORE-003 の通知)
- ツール無効化時はサブパネルが unregister されるため UI から消える(受け入れ基準 3)

## 8. core/logger.py(共通ログ)

- stdlib `logging` を使用。ルートロガー名 `"blendarium"`、ツールは `get_logger(tool_id)` で
  `"blendarium.<tool_id>"` の子ロガーを取得(FR-CORE-005)
- ハンドラ: コンソール + `extension_path_user(... path="logs")/blendarium.log`
  への `RotatingFileHandler`(1 MB × 3 世代)。**出力先はローカルのみ**(NFR-002)
- レベルは prefs の `log_level` に追従。ハンドラ二重登録防止のため、setup は冪等にする

## 9. ヘッドレス実行規約(FR-CORE-006 実装ガイドライン)

- logic 層の関数シグネチャ例(scene_stats):
  `collect_stats(data: bpy.types.BlendData) -> SceneStatsReport`
- 禁止: `bpy.context`、`bpy.ops`、`ui.py` の import、UI への直接通知
- 許可: `bpy.data` の読み書き(呼び出し元から引数で受け取る形を推奨)、`core.settings` / `core.logger`
- 検証スクリプト `dev/run_scene_stats.py`(受け入れ基準 5):

```
blender -b <file.blend> --python dev/run_scene_stats.py -- --output stats.json
```

(`--` 以降は Blender ではなくスクリプト側の引数として `sys.argv` から取り出す)

## 10. v1.0 ツール個別設計

### 10.1 scene_stats(読み取り専用・最初に実装)

- logic: `collect_stats(data) -> SceneStatsReport`(dataclass)。集計項目:
  オブジェクト数(タイプ別内訳)、総ポリゴン数(未評価メッシュ基準)、マテリアル数、
  画像テクスチャ数と解像度一覧、コレクション数
- logic: `to_json(report) -> str` / `to_markdown(report) -> str`(ローカル書き出し用シリアライザ)
- ui: 集計結果表示 + Refresh ボタン + Export JSON / Export Markdown
  (`ExportHelper` によるファイル選択ダイアログ)
- 設定(JSON): 前回のエクスポート形式のみ(最小構成)

### 10.2 naming_tools(設定永続型・2 番目)

- 設定(JSON)= ルールセット: `rules: [{target: OBJECT|MESH|MATERIAL|..., pattern: <regex>,
  description}]` + 組み込みプリセット(コードに内蔵、JSON はユーザー編集分)
- logic: `scan(data, rules) -> list[Violation]` / `build_rename_plan(violations, rule) -> list[RenameAction]`
  / `apply_plan(plan, dry_run: bool) -> ApplyResult`(dry_run=True では名前変更せず結果のみ返す)
- ui: 違反一覧(`UIList`)、ドライラン結果表示 → 確認ダイアログ → 適用(UNDO 対応)

### 10.3 data_purge(破壊的・最後)

- logic: `find_orphans(data) -> list[OrphanItem]`(全 ID コレクションを走査し
  `users == 0 and not use_fake_user` を抽出。削除で新たに孤児化するものは反復走査で検出 = 再帰対応)
- logic: `purge(data, items) -> PurgeResult`(`bpy.data.<collection>.remove()` で削除)
- ui: プレビュー一覧(タイプ別グループ表示)→ `invoke_props_dialog` で確認 → 実行(UNDO 対応)
- `bpy.ops.outliner.orphans_purge` はコンテキスト依存のため使用しない(ヘッドレス規約と整合)

## 11. 実装マイルストーン(Codex への発注単位)

| # | 内容 | 検証する受け入れ基準 |
|---|---|---|
| M1 | core(registry/prefs/settings/logger)+ shell + `dev/broken_tool_fixture` + 既存 hello をツール化したサンプル | 1, 3, 4 |
| M2 | scene_stats + `dev/run_scene_stats.py` | 2(部分), 5 |
| M3 | naming_tools | 2(部分), 6(部分) |
| M4 | data_purge + hello サンプルツール削除 | 2, 6 |
| M5 | 仕上げ: README 全面改訂(英日)、manifest 整備(version=0.1.0, tagline, maintainer)、4.2 LTS での動作確認、ZIP ビルド検証 | 1–7 |

各マイルストーン完了時に Claude がコードレビュー(契約遵守・エラー隔離・ヘッドレス規約・NFR-002 のネットワーク非使用)を行い、問題があれば Codex に修正指示を出す。

## 12. コーディング規約(Codex への指示に含める)

- コード・コメント・docstring は英語。型ヒント必須。docstring は Google style
- UI の表示文字列(`bl_label` / `bl_description` / report メッセージ等)はすべて英語(TBD-03 決定)
- コミットは Conventional Commits(`feat:` / `fix:` / `docs:` / `refactor:` / `test:`)
- ネットワーク通信を行うコードの混入禁止(NFR-002)。`urllib` / `requests` 等の import を禁止
- OS 依存パスは `pathlib` を使用し、パス区切りをハードコードしない(NFR-005)

## 13. 未決事項(本設計で新たに確定が必要なもの)

| ID | 事項 | 推奨 | 決定期限 |
|---|---|---|---|
| TBD-04 | パフォーマンス目標 | 「10 万オブジェクト / 500 万ポリゴンのシーンで scene_stats 集計 5 秒以内・UI フリーズなし」を仮目標とし、M2 で実測後に確定 | M2 完了時 |

※ TBD-03(UI 言語)は 2026-07-18 に「英語のみ」で決定済み(§12 の規約に反映)。

## 改訂履歴

| 版 | 日付 | 内容 |
|---|---|---|
| v0.1 | 2026-07-18 | 初版ドラフト(要件定義書 v0.2 の決定事項を反映) |
