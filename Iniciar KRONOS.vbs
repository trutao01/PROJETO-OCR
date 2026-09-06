Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "D:\Projetos\Projeto 1"
WshShell.Run "venv\Scripts\pythonw.exe src\main.py", 0, False
