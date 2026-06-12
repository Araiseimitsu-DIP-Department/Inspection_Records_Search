Option Compare Database

'検査記録ボタン
Private Sub btnKensakiroku_Click()
    Dim strSQL As String
    
    If IsNull(Me.txtDate) Then
        MsgBox "日付の指定がありません", vbCritical + vbOKOnly, "確認"
        Me.txtDate.SetFocus
        Exit Sub
    End If
    
    If MsgBox("外観検査記録データの移動を行いますか？", vbQuestion + vbYesNo, "確認") <> vbYes Then Exit Sub
    
    Me.ProgressBar1.max = 4
    Me.ProgressBar1.min = 0
    Me.ProgressBar1 = 0
    Me.ProgressBar1.Visible = True
    DoEvents
    
    strSQL = "INSERT INTO t_外観検査記録保存 (検査員ID, 生産ロットID, 工程NO, 日付, 時刻, 品番, 品名, 客先, 数量, 更新フラグ) "
    strSQL = strSQL & "SELECT 検査員ID, 生産ロットID, 工程NO, 日付, 時刻, 品番, 品名, 客先, 数量, 更新フラグ "
    strSQL = strSQL & "FROM t_外観検査記録 "
    strSQL = strSQL & "WHERE 日付 <= #" & Me.txtDate & "#;"
    DoCmd.RunSQL strSQL
    Me.ProgressBar1 = 1
    DoEvents
    
    strSQL = "DELETE FROM t_外観検査記録 WHERE 日付 <= #" & Me.txtDate & "#;"
    DoCmd.RunSQL strSQL
    Me.ProgressBar1 = 2
    DoEvents
    
    strSQL = "INSERT INTO t_外観検査集計保存 (検査員ID, 日付, 生産ロットID, 品番, 品名, 工程NO, 数量, 作業時間) "
    strSQL = strSQL & "SELECT 検査員ID, 日付, 生産ロットID, 品番, 品名, 工程NO, 数量, 作業時間 "
    strSQL = strSQL & "FROM t_外観検査集計 "
    strSQL = strSQL & "WHERE 日付 <= #" & Me.txtDate & "#;"
    DoCmd.RunSQL strSQL
    Me.ProgressBar1 = 3
    DoEvents
    
    strSQL = "DELETE FROM t_外観検査集計 WHERE 日付 <= #" & Me.txtDate & "#;"
    DoCmd.RunSQL strSQL
    Me.ProgressBar1 = 4
    DoEvents
    
    MsgBox "終了しました", vbInformation + vbOKOnly, "確認"
    Me.ProgressBar1.Visible = False
    
End Sub