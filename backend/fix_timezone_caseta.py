# Script para corregir el error de timezone en caseta.py
import re

file_path = r"c:\Users\SunyLibramineto\Documents\RRHH_APP\backend\app\api\caseta.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y reemplazar la línea específica en la función regreso_salida_temporal_por_empleado
# Esta es la línea 291 que causa el error
old_pattern = r"(    # Calcular minutos descontados según tipo de salida\n    if salida\.tipo_salida == TipoSalida\.PERMISO_PERSONAL:\n        )salida\.minutos_descontados = int\(\(now - salida\.hora_salida\)\.total_seconds\(\) / 60\)"
new_pattern = r"\1# Asegurar que salida.hora_salida tenga timezone\n        hora_salida_con_tz = salida.hora_salida\n        if hora_salida_con_tz.tzinfo is None:\n            hora_salida_con_tz = hora_salida_con_tz.replace(tzinfo=now.tzinfo)\n        salida.minutos_descontados = int((now - hora_salida_con_tz).total_seconds() / 60)"

content = re.sub(old_pattern, new_pattern, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Corrección aplicada exitosamente")
