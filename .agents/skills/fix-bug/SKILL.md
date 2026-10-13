---
name: fix-bug
description: この検査照会アプリの不具合を、発生条件とDBバックエンドを特定して原因調査・修正・回帰確認する。
---

1. 現象、期待値、使用exeかソース起動か、DB_BACKEND、対象期間を整理する。接続情報の実値は出力しない。
2. [構造](../../../docs/ARCHITECTURE.md)と[業務仕様](../../../docs/BUSINESS_RULES.md)、関連コード・Testsで再現と原因候補を分け、根拠のある原因を特定する。
3. UI重なり・設定・DB照会・集計計算のどこで発生するか切り分け、該当箇所を最小修正する。業務仕様が不明ならHuman Validation Requiredとする。
4. 発生経路を再確認し、必要な回帰テストを追加する。データ更新に関係するときのみ[更新検証](../development-workflow/references/data-update-verification.md)を使用する。
5. review-code、[Verification Gate](../../../docs/RELEASE.md)、Docs・変更履歴、diffを確認して原因・変更・未検証を報告する。再利用できる確認漏れは[学びの提案](../development-workflow/references/learning-feedback.md)へ進む。
