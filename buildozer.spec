[app]
title = Mis Gastos
package.name = misgastos
package.domain = org.tudominio
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0

requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0,requests,urllib3,fpdf2,openpyxl,plyer,pyjnius,android,pillow

orientation = portrait
fullscreen = 0

# AQUÍ ESTÁ EL CAMBIO CLAVE:
# Añadimos MANAGE_EXTERNAL_STORAGE para Android 11+
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.accept_sdk_license = True

p4a.branch = v2024.01.21
