---
name: implement-feature
description: この検査照会アプリの新機能または既存機能変更を、業務仕様とDB境界を確認して実装する。
---

1. [構造](../../../docs/ARCHITECTURE.md)、[業務仕様とテスト対応](../../../docs/BUSINESS_RULES.md)、関連Testsを読み、要求と既存機能への影響を特定する。
2. UIは`web/index.html`と`webview_app.py`、業務入口はUseCase、SQLは各リポジトリという既存境界を維持して最小実装する。
3. DBを変更する場合は[DATABASE.md](../../../docs/DATABASE.md)、バックエンド分離ならdatabase-backend-buildを参照する。
4. データ更新を含む場合のみ[共通検証](../development-workflow/references/data-update-verification.md)を適用する。
5. 影響を受ける仕様のテスト、review-code、[Verification Gate](../../../docs/RELEASE.md)、Docs・履歴の更新を完了する。未知の業務仕様は推測で実装せず確認事項として報告する。
