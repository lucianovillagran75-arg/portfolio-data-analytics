' ============================================================
' MACRO: InformeMensual
' FabriTec S.A. — Panel de Paros y OEE
'
' Cómo usar:
'   1. Abrir Panel_Paros_OEE_Portfolio.xlsx en Excel
'   2. Presionar Alt+F11 para abrir el editor de VBA
'   3. Insertar > Módulo
'   4. Pegar este código completo y cerrar el editor (Alt+Q)
'   5. Ejecutar con Alt+F8 > seleccionar "InformeMensual" > Ejecutar
'
' Qué hace:
'   Crea una copia del Dashboard con los valores congelados
'   (sin fórmulas) y la guarda como "Informe_<Mes>_<Año>.xlsx"
'   en la misma carpeta del archivo original.
' ============================================================

Sub InformeMensual()

    Dim wsOrigen    As Worksheet
    Dim wbNuevo     As Workbook
    Dim wsDestino   As Worksheet
    Dim strMes      As String
    Dim strAnio     As String
    Dim strRuta     As String
    Dim strNombre   As String

    ' --- Definir el mes/año del informe (mes anterior al actual) ---
    Dim fechaInforme As Date
    fechaInforme = DateSerial(Year(Now()), Month(Now()), 1) - 1  ' último día del mes anterior
    strMes  = Format(fechaInforme, "MM")
    strAnio = Format(fechaInforme, "YYYY")

    ' --- Hoja origen: Dashboard ---
    On Error GoTo ErrorHandler
    Set wsOrigen = ThisWorkbook.Sheets("Dashboard")

    ' --- Crear libro nuevo ---
    Set wbNuevo   = Workbooks.Add
    Set wsDestino = wbNuevo.Sheets(1)
    wsDestino.Name = "Informe_" & strMes & "_" & strAnio

    ' --- Copiar Dashboard completo (como imagen de valores) ---
    wsOrigen.UsedRange.Copy
    wsDestino.Range("A1").PasteSpecial Paste:=xlPasteValues
    wsDestino.Range("A1").PasteSpecial Paste:=xlPasteFormats
    wsDestino.Range("A1").PasteSpecial Paste:=xlPasteColumnWidths
    Application.CutCopyMode = False

    ' --- Copiar gráficos manualmente ---
    Dim obj As Object
    Dim nuevaPos As Long
    nuevaPos = 0
    For Each obj In wsOrigen.ChartObjects
        obj.Copy
        wsDestino.Paste Destination:=wsDestino.Cells(obj.TopLeftCell.Row, obj.TopLeftCell.Column)
        nuevaPos = nuevaPos + 1
    Next obj

    ' --- Agregar encabezado de período en celda libre ---
    With wsDestino.Range("A3")
        .Value = "Informe generado: " & Format(Now(), "DD/MM/YYYY HH:MM") & _
                 "  |  Período: " & MonthName(Month(fechaInforme)) & " " & strAnio
        .Font.Italic = True
        .Font.Size   = 9
        .Font.Color  = RGB(89, 89, 89)
    End With

    ' --- Guardar en la misma carpeta del archivo fuente ---
    strRuta   = ThisWorkbook.Path & "\"
    strNombre = "Informe_" & strMes & "_" & strAnio & ".xlsx"

    wbNuevo.SaveAs Filename:=strRuta & strNombre, _
                   FileFormat:=xlOpenXMLWorkbook

    MsgBox "Informe generado correctamente:" & vbCrLf & strRuta & strNombre, _
           vbInformation, "Informe Mensual — OK"

    wbNuevo.Close SaveChanges:=False
    Exit Sub

ErrorHandler:
    MsgBox "Error al generar el informe: " & Err.Description, vbCritical, "Error"

End Sub


' ============================================================
' MACRO AUXILIAR: ActualizarSemaforo
'
' Recalcula los colores de la hoja Equipos según la fecha
' actual (útil para abrir el archivo en meses futuros).
' Ejecutar manualmente desde Alt+F8 si los colores no se
' actualizaron solos.
' ============================================================

Sub ActualizarSemaforo()

    Dim ws      As Worksheet
    Dim lastRow As Long
    Dim i       As Long
    Dim dias    As Long
    Dim colorFondo As Long

    Set ws = ThisWorkbook.Sheets("Equipos")

    ' La columna G (7) tiene "Días Restantes", la H (8) tiene "Estado"
    ' Los datos empiezan en fila 4
    lastRow = ws.Cells(ws.Rows.Count, 2).End(xlUp).Row

    For i = 4 To lastRow
        dias = ws.Cells(i, 7).Value
        If dias < 0 Then
            colorFondo = RGB(255, 204, 204)   ' Rojo claro
            ws.Cells(i, 8).Value = "VENCIDO"
        ElseIf dias < 30 Then
            colorFondo = RGB(255, 204, 204)
            ws.Cells(i, 8).Value = "URGENTE"
        ElseIf dias < 60 Then
            colorFondo = RGB(255, 235, 156)   ' Amarillo
            ws.Cells(i, 8).Value = "PROXIMO"
        Else
            colorFondo = RGB(198, 239, 206)   ' Verde
            ws.Cells(i, 8).Value = "OK"
        End If
        ws.Cells(i, 7).Interior.Color = colorFondo
        ws.Cells(i, 8).Interior.Color = colorFondo
    Next i

    MsgBox "Semaforo actualizado al " & Format(Date, "DD/MM/YYYY"), vbInformation, "OK"

End Sub
