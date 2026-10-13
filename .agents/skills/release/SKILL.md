---
name: release
description: このWindows検査照会アプリの配布前にテスト、PyInstaller成果物、設定、UI確認と未検証事項を整理する。
---

1. [RELEASE.md](../../../docs/RELEASE.md)と[safety.mdc](../../../.cursor/rules/safety.mdc)を読み、対象バックエンドと配布予定を確認する。
2. README、.env.example、Docs、update.mdの整合を確認し、既存の[Verification Gate](../../../docs/RELEASE.md)を実行する。
3. バックエンドや依存関係を変更した場合はdatabase-backend-buildで、両プロファイルの成果物と必要資源を監査する。
4. データ更新を含むリリースだけ[更新検証](../development-workflow/references/data-update-verification.md)を適用する。
5. 配布先PCのWebView2 / .NET、実exeの3画面、候補選択、Excel保存を確認する。未実施なら理由と人間確認項目を残す。
6. 生成物、サイズ、テスト、起動・機能確認、未検証、復帰方法を報告する。ローカルビルドの成功を本番配布許可として扱わず、Approval Gateに従う。
