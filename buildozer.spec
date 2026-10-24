[app]
title = Mis Gastos
package.name = misgastos
package.domain = org.tudominio
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0

# Librerías necesarias
requirements = python3,kivy==2.2.1,requests,urllib3,fpdf,et-xmlfile,openpyxl,plyer,pyjnius,android,pillow

# --- IMAGEN DEL ÍCONO DE LA APP ---
# Apuntamos al archivo que ya subiste
icon.filename = %(source.dir)s/mi_icono.png

# --- PANTALLA DE CARGA (SPLASH) ---
# Usamos tu logo para que aparezca mientras la app abre
presplash.filename = %(source.dir)s/logo.png

orientation = portrait
fullscreen = 0
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True

p4a.branch = v2024.01.21
