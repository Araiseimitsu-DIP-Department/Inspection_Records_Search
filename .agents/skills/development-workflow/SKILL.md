---
name: development-workflow
description: この検査照会プロジェクトの機能追加、修正、ビルド改善で参照Docsと検証を選び、作業を完了する。
---

1. [AGENTS.md](../../../AGENTS.md)から関連DocsとRulesを確認し、依頼を機能追加・不具合・小規模改善に分類する。
2. 新機能はimplement-feature、不具合はfix-bugへ進む。バックエンドやビルド依存を触る場合はdatabase-backend-buildも使用する。
3. 実装後はreview-codeと[Verification Gate](../../../docs/RELEASE.md)を適用し、Docsと[変更履歴](../../../docs/update.md)の更新要否を判断する。
4. DB・ファイル・Excel等のデータ更新を変更する場合だけ[データ更新検証](references/data-update-verification.md)を読む。本番データを使った更新テストを勝手に実行しない。
5. 確認漏れから再利用できる学びが判明した場合は[提案・承認・反映](references/learning-feedback.md)を使用する。
6. 変更ファイル、検証範囲、PASS / FAIL / NOT RUN、未確定の業務仕様、残存課題を分けて報告する。本番配布を行う場合はreleaseを参照する。
