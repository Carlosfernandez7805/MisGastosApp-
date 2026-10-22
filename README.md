# Mi Control de Gastos — versión inicial

Aplicación Android con Python 3 y Kivy para registrar gastos escribiendo texto libre, guardarlos localmente con SQLite y exportarlos a Excel.

## Ejemplos de entrada
- `Compré supermercado 150.000 pesos`
- `Servicios 200000`
- `Taxi 18.500 pesos`

Por ahora, el valor debe estar al final del texto. Los separadores `.` y `,` se interpretan como separadores de miles; escribe decimales solo si se amplía el analizador.

## Qué incluye esta versión
- Registro con Enter o botón.
- Almacenamiento local SQLite.
- Totales del día y del mes.
- Lista de últimos movimientos.
- Exportación de todos los movimientos a Excel `.xlsx`.

## Qué falta antes de producción
- Selector de correo destinatario.
- Envío diario de correo con autenticación segura.
- Programación Android persistente (WorkManager/AlarmManager), manejo de reinicios y optimización de batería.
- Compartir/guardar el Excel mediante el selector de archivos de Android.
- Pruebas de instalación y ejecución en un teléfono real.

El correo automático no está habilitado en esta versión inicial; no se debe considerar que ya envía correos.

## Crear APK
Buildozer funciona mejor en Linux o WSL2 con dependencias Android instaladas. En la carpeta del proyecto:

```bash
python3 -m pip install --user buildozer
buildozer android debug
```

El primer armado descarga herramientas de Android y puede tardar bastante. Para Windows, se recomienda usar WSL2 Ubuntu; no ejecutar Buildozer directamente en PowerShell.

## Probar lógica en PC
Instala dependencias con `pip install -r requirements.txt`. Kivy requiere soporte gráfico; en algunos entornos Windows puede ser necesario seguir la guía oficial de Kivy para instalarlo.
