# 外観検査記録照会

Microsoft Access（`.accdb` / `.mdb`）の運用データを参照し、検索・集計表示・Excel 出力を行う Windows 用デスクトップアプリです。

画面は `pywebview`、業務処理は `services/` と `infrastructure/` に分離しています。  
配布版は onefile の `外観検査記録照会.exe` を想定しています。

## 主な機能

| 画面 | 内容 |
|------|------|
| 検査員集計 | 表示開始日・表示終了日・品番で明細を検索し、Excel 出力できます。 |
| ロットID集計 | 品番と工程でロットの集計結果を表示し、Excel 出力できます。 |
| 検査員別照会 | 検査員と日付範囲で明細と集計を横並び表示します。 |

## 現在の構成

```text
Inspection_Records_Search/
├─ main.py
├─ build_exe.ps1
├─ requirements.txt
├─ README.md
├─ docs/
│  ├─ VBA.txt
│  ├─ code_2.html
│  ├─ DESIGN_1.md
│  ├─ DESIGN_2.md
│  └─ 精密部品の品質検査.png
├─ scripts/
│  ├─ generate_app_ico.py
│  └─ pyinstaller_build.py
└─ src/inspection_records_search/
   ├─ app.py
   ├─ config.py
   ├─ webview_app.py
   ├─ web/
   │  └─ index.html
   ├─ application/
   │  └─ inspection_use_case.py
   ├─ infrastructure/
   │  ├─ access_gateway.py
   │  ├─ postgres_repository.py
   │  └─ repository_factory.py
   ├─ services/
   │  ├─ inspection_service.py
   │  └─ export_service.py
   ├─ domain/
   │  ├─ models.py
   │  └─ repositories.py
   └─ shared/
      └─ errors.py
```

## 処理の流れ

1. `main.py` から `inspection_records_search.app.main()` を起動します。
2. `config.py` で `.env` を読み、DB 設定を検証します。
3. `webview_app.py` が Python ブリッジを公開し、画面からの操作を `InspectionService` に渡します。
4. `web/index.html` が画面本体で、検索条件、一覧、確認ダイアログ、Excel 出力の UI を担います。
5. `services/` と `infrastructure/` が DB アクセスと Excel 生成を処理します。

## 設定

`.env` で次の変数を使用します。

| 変数 | 説明 |
|------|------|
| `ACCESS_DB_PATH` | Access ファイルのフルパス |
| `DATABASE_BACKEND` | `access` または `postgres` |
| `POSTGRES_DSN` | `postgres` を使う場合の接続文字列 |
| `EXPORT_DIR` | Excel 出力先の任意フォルダ |

### Access を使う場合

```env
ACCESS_DB_PATH=C:\path\to\外観検査記録照会.accdb
```

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 開発起動

```powershell
.\.venv\Scripts\python.exe .\main.py
```

## onefile ビルド

```powershell
.\build_exe.ps1
```

ビルド結果は `dist\外観検査記録照会.exe` のみです。  
`build\app_icon.ico` と `build/` / `dist/` 配下はビルド途中で生成される中間成果物で、配布対象ではありません。

onefile ビルドのため、配布時に必要なのは EXE 1 ファイルだけです。

## アイコン

- デスクトップアイコンとタスクバーアイコンの元画像: `docs/精密部品の品質検査.png`
- ビルド時にこの PNG から Windows 用 `.ico` を生成して exe に埋め込みます。

## 補足

- 現在の画面は `pywebview` の Edge WebView2 バックエンドを使っています（exe 容量削減のため Qt は同梱しません）。実行PCに [WebView2 ランタイム](https://developer.microsoft.com/ja-jp/microsoft-edge/webview2/) が必要です。WinForms 側の制約により、ウィンドウ／タスクバー用アイコンは `.ico`（ビルドで `docs/app_icon.ico` として同梱）を使います。
- 配布版は onefile のため、実行時に別途 Python を入れる必要はありません。
- Access / ODBC の接続可否は利用環境に依存します。
