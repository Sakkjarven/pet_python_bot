Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & WshShell.CurrentDirectory & "\run_agent.bat" & Chr(34), 0
Set WshShell = Nothing
