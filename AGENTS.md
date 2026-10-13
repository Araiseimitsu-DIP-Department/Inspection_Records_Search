# 外観検査記録照会 開発ガイド

Windows / pywebview / PostgreSQL の検査照会アプリ。Access実装もソースに保持している。

## 参照先

- 入口と環境変数: [README.md](README.md)
- 調査分類・構造・未確定事項: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 業務ロジック・テスト対応: [docs/BUSINESS_RULES.md](docs/BUSINESS_RULES.md)
- DB・依存関係の境界: [docs/DATABASE.md](docs/DATABASE.md)
- ビルド・Verification Gate: [docs/RELEASE.md](docs/RELEASE.md)
- 恒常的制約・Approval Gate: [.cursor/rules/development.mdc](.cursor/rules/development.mdc), [.cursor/rules/safety.mdc](.cursor/rules/safety.mdc)
- 変更履歴: [docs/update.md](docs/update.md)

## 作業手順

[development-workflow](.agents/skills/development-workflow/SKILL.md)を入口にし、実装は[implement-feature](.agents/skills/implement-feature/SKILL.md)、不具合は[fix-bug](.agents/skills/fix-bug/SKILL.md)、レビューは[review-code](.agents/skills/review-code/SKILL.md)、配布準備は[release](.agents/skills/release/SKILL.md)を参照する。
バックエンドや成果物の依存関係を変更するときは[database-backend-build](.agents/skills/database-backend-build/SKILL.md)を使用する。

データ更新・Excel出力・移行処理を変更するときだけ[データ更新検証](.agents/skills/development-workflow/references/data-update-verification.md)を適用する。
再利用できる確認漏れが判明したときは[学びの提案手順](.agents/skills/development-workflow/references/learning-feedback.md)を参照する。

検証結果と未検証事項を分け、日本語で簡潔に報告する。
