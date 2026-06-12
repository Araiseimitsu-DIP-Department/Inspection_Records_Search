-- PostgreSQL DDL 草案（Access メタデータから自動生成）
-- ※ 型・制約は必ず手動で確認・修正してください

CREATE TABLE "t_Excel現品票履歴" (
    "生産ロットID" VARCHAR(7),
    "号機" VARCHAR(5),
    "品番" VARCHAR(30),
    "品名" VARCHAR(30),
    "客先" VARCHAR(30),
    "材質" VARCHAR(50),
    "材料ロットNO" VARCHAR(30),
    "数量" INTEGER,
    "備考" VARCHAR(50),
    "指示日" TIMESTAMP,
    "完了フラグ" VARCHAR(1)
);


CREATE TABLE "t_チェックシートリスト" (
    "No" INTEGER,
    "客先" VARCHAR(25),
    "ファイルNo" VARCHAR(10)
);


CREATE TABLE "t_不具合情報" (
    "ID" BIGSERIAL,
    "生産ロットID" VARCHAR(7),
    "品番" VARCHAR(30),
    "指示日" TIMESTAMP,
    "号機" VARCHAR(5),
    "検査者1" VARCHAR(6),
    "検査者2" VARCHAR(6),
    "検査者3" VARCHAR(6),
    "検査者4" VARCHAR(6),
    "検査者5" VARCHAR(20),
    "時間" INTEGER,
    "数量" INTEGER,
    "総不具合数" INTEGER,
    "不良率" DOUBLE PRECISION,
    "外観キズ" INTEGER,
    "圧痕" INTEGER,
    "切粉" INTEGER,
    "毟れ" INTEGER,
    "穴大" INTEGER,
    "穴小" INTEGER,
    "穴キズ" INTEGER,
    "バリ" INTEGER,
    "短寸" INTEGER,
    "面粗" INTEGER,
    "サビ" INTEGER,
    "ボケ" INTEGER,
    "挽目" INTEGER,
    "汚れ" INTEGER,
    "メッキ" INTEGER,
    "落下" INTEGER,
    "フクレ" INTEGER,
    "ツブレ" INTEGER,
    "ボッチ" INTEGER,
    "段差" INTEGER,
    "バレル石" INTEGER,
    "径プラス" INTEGER,
    "径マイナス" INTEGER,
    "ゲージ" INTEGER,
    "異物混入" INTEGER,
    "形状不良" INTEGER,
    "こすれ" INTEGER,
    "変色シミ" INTEGER,
    "材料キズ" INTEGER,
    "ゴミ" INTEGER,
    "その他" INTEGER,
    "その他内容" VARCHAR(10)
);


CREATE TABLE "t_外観検査記録" (
    "ID" BIGSERIAL,
    "検査員ID" VARCHAR(4),
    "生産ロットID" VARCHAR(7),
    "工程NO" VARCHAR(2),
    "日付" TIMESTAMP,
    "時刻" TIMESTAMP,
    "品番" VARCHAR(30),
    "品名" VARCHAR(30),
    "客先" VARCHAR(25),
    "数量" INTEGER,
    "更新フラグ" VARCHAR(1),
    "集計除外フラグ" BOOLEAN NOT NULL
);


CREATE TABLE "t_外観検査記録保存" (
    "ID" BIGSERIAL,
    "検査員ID" VARCHAR(4),
    "生産ロットID" VARCHAR(7),
    "工程NO" VARCHAR(2),
    "日付" TIMESTAMP,
    "時刻" TIMESTAMP,
    "品番" VARCHAR(30),
    "品名" VARCHAR(30),
    "客先" VARCHAR(25),
    "数量" INTEGER,
    "更新フラグ" VARCHAR(1),
    "集計除外フラグ" BOOLEAN NOT NULL
);


CREATE TABLE "t_外観検査集計" (
    "ID" BIGSERIAL,
    "検査員ID" VARCHAR(4),
    "日付" TIMESTAMP,
    "生産ロットID" VARCHAR(7),
    "品番" VARCHAR(30),
    "品名" VARCHAR(30),
    "工程NO" VARCHAR(2),
    "数量" INTEGER,
    "作業時間" INTEGER,
    "集計除外フラグ" BOOLEAN NOT NULL
);


CREATE TABLE "t_外観検査集計保存" (
    "ID" BIGSERIAL,
    "検査員ID" VARCHAR(4),
    "日付" TIMESTAMP,
    "生産ロットID" VARCHAR(7),
    "品番" VARCHAR(30),
    "品名" VARCHAR(30),
    "工程NO" VARCHAR(2),
    "数量" INTEGER,
    "作業時間" INTEGER,
    "集計除外フラグ" BOOLEAN NOT NULL
);


CREATE TABLE "t_工程マスタ" (
    "工程NO" INTEGER,
    "工程名" VARCHAR(10)
);


CREATE TABLE "t_数値検査員マスタ" (
    "検査員ID" VARCHAR(4),
    "検査員名" VARCHAR(5),
    "区別" VARCHAR(5),
    "表示フラグ" BOOLEAN NOT NULL
);


CREATE TABLE "t_数値検査記録" (
    "ID" BIGSERIAL,
    "日付時刻" TIMESTAMP,
    "生産ロットID" VARCHAR(7),
    "検査員ID" VARCHAR(4),
    "工程名" VARCHAR(30),
    "号機" VARCHAR(5)
);


CREATE TABLE "t_検査中" (
    "検査員ID" VARCHAR(4),
    "生産ロットID" VARCHAR(7),
    "時刻" TIMESTAMP,
    "表示フラグ" VARCHAR(1)
);


CREATE TABLE "t_検査員マスタ" (
    "検査員ID" VARCHAR(4),
    "検査員名" VARCHAR(10),
    "表示位置" VARCHAR(3),
    "チーム" VARCHAR(1),
    "ふりがな" VARCHAR(1)
);


CREATE TABLE "t_検査者マスタ" (
    "ID" BIGSERIAL,
    "検査者" VARCHAR(6),
    "ふりがな" VARCHAR(1)
);

