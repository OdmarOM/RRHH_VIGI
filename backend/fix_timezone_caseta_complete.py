# Script para corregir todos los errores de timezone en caseta.py
import re

file_path = r"c:\Users\SunyLibramineto\Documents\RRHH_APP\backend\app\api\caseta.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Corrección 1: datetime.combine sin tzinfo, luego agregar timezone
old_pattern1 = r"(hora_salida_oficial = datetime\.combine\(\s*fecha_turno,\s*turno\[\"hora_salida_oficial\"\],\s*)tzinfo=now\.tzinfo\s*\)"
new_pattern1 = r"\1)\n        # Asegurar que hora_salida_oficial tenga timezone\n        if hora_salida_oficial.tzinfo is None:\n            hora_salida_oficial = hora_salida_oficial.replace(tzinfo=now.tzinfo)"

content = re.sub(old_pattern1, new_pattern1, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Corrección completa aplicada exitosamente")
