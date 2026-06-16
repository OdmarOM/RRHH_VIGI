' ============================================================
'  Inicia el Sistema RRHH en segundo plano (SIN ventana de cmd)
'  Doble clic para arrancar el servidor.
' ============================================================
Option Explicit

Dim sh, fso, scriptDir, runBat

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
runBat = scriptDir & "\run_server.bat"

' El segundo parametro 0 = ventana oculta. False = no esperar.
sh.Run """" & runBat & """", 0, False

' Mensaje breve de confirmacion
sh.Popup "Sistema RRHH iniciado en segundo plano." & vbCrLf & _
         "Acceso: http://" & sh.ExpandEnvironmentStrings("%COMPUTERNAME%") & ":8090" & vbCrLf & _
         "(o http://localhost:8090 en este equipo)", 4, "RRHH - Encendido", 64
