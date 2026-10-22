"""Envío de correo: plantilla de la siguiente fase.

No guardes contraseñas personales ni credenciales de correo dentro del código.
Para Gmail, la integración de producción debe usar OAuth o un proveedor de correo
con credenciales protegidas. El envío diario fiable en Android requiere programar
una tarea nativa (por ejemplo WorkManager) y comprobar restricciones de batería/red.
"""


def send_daily_report(*args, **kwargs):
    raise NotImplementedError(
        'El correo automático se activa en la siguiente fase, después de configurar '
        'el proveedor de correo de forma segura.'
    )
