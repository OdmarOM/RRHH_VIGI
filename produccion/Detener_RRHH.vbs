' ============================================================
'  Detiene el Sistema RRHH (SIN ventana de cmd)
'  Solo cierra el proceso que escucha en el puerto 8090.
' ============================================================
Option Explicit

Dim sh, cmd

Set sh = CreateObject("WScript.Shell")

' Busca el proceso que escucha en el puerto 8090 y lo detiene.
cmd = "powershell -NoProfile -ExecutionPolicy Bypass -Command """ & _
      "Get-NetTCPConnection -LocalPort 8090 -State Listen -ErrorAction SilentlyContinue " & _
      "| Select-Object -ExpandProperty OwningProcess -Unique " & _
      "| ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"""

' Ventana oculta, esperar a que termine.
sh.Run cmd, 0, True

sh.Popup "Sistema RRHH detenido.", 3, "RRHH - Apagado", 64
