Option Compare Database
Option Explicit

'表示ボタン
Private Sub btnDisp_Click()
    Dim strSQL As String
    Dim sMsg As String
    
    sMsg = ""
    If IsNull(Me.cboKensain) Then sMsg = "検査員の指定がありません"
    If IsNull(Me.txtKaishibi) Then sMsg = "表示開始日は必ず指定してください"
    
    If sMsg <> "" Then
        MsgBox sMsg, vbCritical + vbOKOnly, "確認"
        Me.txtKaishibi.SetFocus
        Exit Sub
    End If
        
    strSQL = "SELECT 検査員ID, 生産ロットID, 工程NO, 日付, 時刻, 品番, 品名, 客先 "
    strSQL = strSQL & "FROM t_外観検査記録 "
    strSQL = strSQL & "WHERE 検査員ID = '" & Me.cboKensain & "' "
    If Not IsNull(Me.txtShuryobi) Then
        strSQL = strSQL & "AND 日付 BETWEEN #" & Me.txtKaishibi & "# "
        strSQL = strSQL & "AND #" & Me.txtShuryobi & "# "
    Else
        strSQL = strSQL & "AND 日付 = #" & Me.txtKaishibi & "# "
    End If
    strSQL = strSQL & "ORDER BY 日付, 時刻;"
    Me.f_個人別照会のサブフォーム1.Form.RecordSource = strSQL
    
    strSQL = "SELECT 検査員ID, 生産ロットID, 工程NO, 日付, 品番, 品名, 作業時間, 数量 "
    strSQL = strSQL & "FROM t_外観検査集計 "
    strSQL = strSQL & "WHERE 検査員ID = '" & Me.cboKensain & "' "
    If Not IsNull(Me.txtShuryobi) Then
        strSQL = strSQL & "AND 日付 BETWEEN #" & Me.txtKaishibi & "# "
        strSQL = strSQL & "AND #" & Me.txtShuryobi & "# "
    Else
        strSQL = strSQL & "AND 日付 = #" & Me.txtKaishibi & "# "
    End If
    strSQL = strSQL & "ORDER BY 日付, ID;"
    Me.f_個人別照会のサブフォーム2.Form.RecordSource = strSQL
    
    Me.Refresh
    Me.txtKaishibi.SetFocus
    
End Sub

'戻るボタン
Private Sub btnToHome_Click()
    DoCmd.Close acForm, "f_個人別照会"
End Sub

'検査員が更新された
Private Sub cboKensain_AfterUpdate()
    Me.btnDisp.SetFocus
End Sub

'フォームを開く時
Private Sub Form_Open(Cancel As Integer)
    Dim strSQL As String
    
    Me.f_個人別照会のサブフォーム1.Form.検査員ID.ColumnHidden = True
    
    Me.f_個人別照会のサブフォーム1.Form.生産ロットID.ColumnWidth = 567 * 2
    Me.f_個人別照会のサブフォーム1.Form.工程NO.ColumnWidth = 567 * 1.4
    Me.f_個人別照会のサブフォーム1.Form.日付.ColumnWidth = 567 * 2.3
    Me.f_個人別照会のサブフォーム1.Form.時刻.ColumnWidth = 567 * 1.6
    Me.f_個人別照会のサブフォーム1.Form.品番.ColumnWidth = 567 * 4.5
    Me.f_個人別照会のサブフォーム1.Form.品名.ColumnWidth = 567 * 4.5
    Me.f_個人別照会のサブフォーム1.Form.客先.ColumnWidth = 567 * 3

    strSQL = "SELECT 検査員ID, 生産ロットID, 工程NO, 日付, 時刻, 品番, 品名, 客先 "
    strSQL = strSQL & "FROM t_外観検査記録 "
    strSQL = strSQL & "WHERE 検査員ID = 'ZZZZ';"
    Me.f_個人別照会のサブフォーム1.Form.RecordSource = strSQL
    
    Me.f_個人別照会のサブフォーム2.Form.検査員ID.ColumnHidden = True
    
    Me.f_個人別照会のサブフォーム2.Form.生産ロットID.ColumnWidth = 567 * 2
    Me.f_個人別照会のサブフォーム2.Form.工程NO.ColumnWidth = 567 * 1.4
    Me.f_個人別照会のサブフォーム2.Form.日付.ColumnWidth = 567 * 2.3
    Me.f_個人別照会のサブフォーム2.Form.品番.ColumnWidth = 567 * 4.5
    Me.f_個人別照会のサブフォーム2.Form.品名.ColumnWidth = 567 * 4.5
    Me.f_個人別照会のサブフォーム2.Form.作業時間.ColumnWidth = 567 * 1.6
    Me.f_個人別照会のサブフォーム2.Form.数量.ColumnWidth = 567 * 1.6
    
    strSQL = "SELECT 検査員ID, 生産ロットID, 工程NO, 日付, 品番, 品名, 作業時間, 数量 "
    strSQL = strSQL & "FROM t_外観検査集計 "
    strSQL = strSQL & "WHERE 検査員ID = 'ZZZZ';"
    Me.f_個人別照会のサブフォーム2.Form.RecordSource = strSQL
End Sub