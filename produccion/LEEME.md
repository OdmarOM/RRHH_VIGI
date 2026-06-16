# Sistema RRHH — Guía de Producción

La aplicación corre en **un solo puerto: `8090`** (no usa los puertos 8000, 8001, 8002 ni 8003).
El backend FastAPI sirve también el frontend ya compilado, así que **no hace falta tener Node corriendo** en producción.

## Requisitos del servidor (una sola vez)

- **Python 3.11+** instalado y en el PATH.
- **Node.js 18+** instalado (solo se usa para compilar el frontend durante la instalación/actualización).

## Instalación (una sola vez)

1. Copia toda la carpeta del proyecto al servidor de producción.
2. Entra en la carpeta `produccion`.
3. Doble clic en **`Instalar.bat`**.
   - Crea el entorno virtual de Python.
   - Instala dependencias de backend y frontend.
   - Genera una `SECRET_KEY` aleatoria.
   - Compila el frontend (`frontend/dist`).

## Uso diario

| Acción | Archivo | Notas |
|--------|---------|-------|
| **Encender** | `Iniciar_RRHH.vbs` | Arranca en segundo plano, **sin ventana de cmd**. |
| **Apagar** | `Detener_RRHH.vbs` | Cierra solo el proceso del puerto 8090. |
| **Ver estado** | `Estado_RRHH.bat` | Indica si está encendido o apagado. |
| **Actualizar** | `Actualizar.bat` | Tras cambios de código: recompila y actualiza dependencias. |

## Acceso

- En el propio servidor: `http://localhost:8090`
- Desde otros equipos / dispositivos Zebra en la red: `http://IP_DEL_SERVIDOR:8090`
  - Asegúrate de permitir el puerto **8090** en el Firewall de Windows (entrada).

## Encendido automático al iniciar Windows (opcional)

1. Pulsa `Win + R`, escribe `shell:startup` y Enter.
2. Crea un acceso directo a `Iniciar_RRHH.vbs` dentro de esa carpeta.

Así el sistema arrancará solo cada vez que se encienda el servidor.

## Logs

- Los registros del servidor se guardan en `produccion/logs/server.log`.

## Notas

- La base de datos por defecto es SQLite (`backend/rrhh_dev.db`).
  Para alta concurrencia futura puedes migrar a PostgreSQL editando `DATABASE_URL` en `backend/.env`.
- El puerto se puede cambiar en `backend/.env` (variable `PORT`) **y** en
  `produccion/run_server.bat`, `Iniciar_RRHH.vbs`, `Detener_RRHH.vbs`, `Estado_RRHH.bat`.
