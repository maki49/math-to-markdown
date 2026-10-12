Set shell = CreateObject("WScript.Shell")
Set fs = CreateObject("Scripting.FileSystemObject")
base = fs.GetParentFolderName(WScript.ScriptFullName)
python = base & "\.venv312\Scripts\pythonw.exe"
If Not fs.FileExists(python) Then
    MsgBox "Please run setup.cmd first.", 48, "Math to Markdown"
    WScript.Quit 1
End If
shell.CurrentDirectory = base
shell.Run Chr(34) & python & Chr(34) & " " & Chr(34) & base & "\app.py" & Chr(34), 1, False
