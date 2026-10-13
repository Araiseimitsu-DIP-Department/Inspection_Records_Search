---
name: review-code
description: この検査照会プロジェクトの変更を、既存仕様、Access互換性、PostgreSQL照会、ビルド資源の観点でレビューする。
---

1. git diffと新規ファイルを読み、要求、[業務仕様](../../../docs/BUSINESS_RULES.md)、[DB境界](../../../docs/DATABASE.md)との整合を確認する。ユーザーの既存変更と今回の変更を区別する。
2. NULL / 空文字、日付境界、数値型、SQLパラメータ、DB接続終了、例外、設定優先順位、Access importの経路、必要なWindows UI資源を対象変更に応じて確認する。
3. Testsが仕様を検証しているか、GUIモック・DBサンプル・exe内部監査の限界が正しく報告されているかを確認する。
4. データ更新に関係するときのみ[共通検証](../development-workflow/references/data-update-verification.md)、確認漏れの再利用候補は[提案手順](../development-workflow/references/learning-feedback.md)を使用する。
5. 指摘をCritical / High / Medium / Lowに分類し、場所・発生条件・影響・修正案を示す。Critical / Highが残る場合はリリース可能と判断しない。指摘がなければ検証範囲と未確認事項を明記する。
