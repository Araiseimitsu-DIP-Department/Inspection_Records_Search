---
name: database-backend-build
description: PostgreSQLとAccessの切替、専用依存分離、PyInstaller構成変更や成果物監査を行う。
---

1. [DBと依存分類](../../../docs/DATABASE.md)、[ビルド仕様](../../../docs/RELEASE.md)、`config.py`、`repository_factory.py`、requirements、ビルドスクリプトを確認する。
2. 専用依存と共通業務/UI資源を呼出経路で区別する。共通定義をAccessモジュール経由で読み込まない。旧import先を使うAccess処理の互換性も調べる。
3. 実装を保持して分離し、`tests/test_runtime_profile.py`でAccess importを禁止したPostgreSQL起動、凍結版設定、切替、同梱設定の回帰を確認する。業務照会は`tests/test_postgres_repository.py`で確認する。
4. 通常版をビルドし、`scripts/verify_build.py`で実exeのPYZ・拡張・データを監査する。依存除外を変えた場合はAccess対応版も別フォルダでビルドして復帰経路を検証する。
5. 許可された接続環境で`scripts/smoke_postgres.py`を実行し、DB照会と一時Excelの読み戻しを確認する。実データの書き換えは不要。
6. 変更前後のサイズ、除外内容、保持したAccessコード、共通依存、DB・GUIの検証範囲を報告する。一般開発手順はdevelopment-workflow、配布判断はreleaseに委ねる。
