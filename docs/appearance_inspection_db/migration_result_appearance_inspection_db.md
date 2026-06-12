# Access → PostgreSQL 移行結果

- 実行日時: 2026-06-12 12:02:41
- Access DB: \\192.168.1.200\共有\生産管理課\AccessDB\外観検査記録DB.accdb

| Accessテーブル名 | PostgreSQLテーブル名 | Access件数 | PostgreSQL件数 | 投入済み件数 | 状態 | エラー |
|---|---|---:|---:|---:|---|---|
| t_Excel現品票履歴 | excel_product_slip_history | 33987 | 33987 | 33987 | 成功 |  |
| t_チェックシートリスト | check_sheet_list | 119 | 119 | 119 | 成功 |  |
| t_不具合情報 | defect_information | 155725 | 155706 | 155706 | 件数差異 |  |
| t_外観検査記録 | appearance_inspection_records | 68864 | 68838 | 68838 | 件数差異 |  |
| t_外観検査記録保存 | appearance_inspection_record_archives | 225171 | 225171 | 225171 | 成功 |  |
| t_外観検査集計 | appearance_inspection_summaries | 51493 | 51467 | 51467 | 件数差異 |  |
| t_外観検査集計保存 | appearance_inspection_summary_archives | 171580 | 171580 | 171580 | 成功 |  |
| t_工程マスタ | process_master | 10 | 10 | 10 | 成功 |  |
| t_数値検査員マスタ | numeric_inspector_master | 14 | 14 | 14 | 成功 |  |
| t_数値検査記録 | numeric_inspection_records | 25906 | 25906 | 25906 | 成功 |  |
| t_検査中 | inspection_in_progress | 59 | 59 | 59 | 成功 |  |
| t_検査員マスタ | inspector_master | 76 | 76 | 76 | 成功 |  |
| t_検査者マスタ | inspection_person_master | 72 | 72 | 72 | 成功 |  |
