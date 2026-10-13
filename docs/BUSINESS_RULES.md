# 確認済み業務ロジックと検証対応

業務仕様の根拠はコードとテスト。運用全体の正当性を推測で追加しない。

| 確認済み処理 | 根拠・自動検証 |
|---|---|
| 開始日が終了日より後の場合は照会しない | `domain/models.py`のDateRange。専用自動テストなし |
| 数量は画面でカンマ表示、Excelは数値 | `web/index.html`、`export_service.py`。Excelはsmokeで読み戻し |
| 検査員候補は氏名のみ、空欄名は除外、IDは検索用に保持 | `webview_app.py`、`web/index.html`。UI操作は人間確認 |
| 保存済み集計と最新記録から計算する集計を併用 | `postgres_repository.py`、`test_lot_aggregate_includes_calculated_live_summary` |
| ロット数量はdelivery_label_historyを参照 | 既存リポジトリテスト・実DB smoke |
| 数値検査員はqr_historyの最新該当履歴のpositionから解決 | `test_main_detail_uses_latest_numeric_inspector_from_qr_history` |
| 数量DB接続が未設定なら数値検査員名は空欄 | `test_main_detail_without_delivery_dsn_leaves_numeric_name_empty` |
| 作業時間は秒を切り捨て、10:30–10:35、12:15–13:00、15:00–15:10を完全に跨ぐ場合に控除し、負数は0 | `_calculate_work_minutes`、`test_work_time_subtracts_access_break_periods`（10時台・昼の2例） |
| 工程入力はコードと名称の両方を照合 | `domain/process_options.py`。移動前後の処理を保持 |
| PostgreSQL版起動でAccess依存を読み込まない | `tests/test_runtime_profile.py`の新規プロセスでimportを禁止した起動経路検証 |
| 専用版にAccess設定を渡しても接続しない | 同上、凍結版マーカー・設定エラー検証 |

休憩の部分重複、全日付境界、全UI操作・全データのAccessとの結果一致は今回のテストだけでは確認できない。業務ロジックの変更が必要な場合は別途対象ケースを確認する。
