from datetime import datetime, date
import os
import re
import threading
import base64
import math
import random
import traceback
import time
import json
import urllib.parse

def escribir_log(mensaje):
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {mensaje}")
    except:
        pass

escribir_log("--- INICIANDO APP ---")

try:
    import requests
    from fpdf import FPDF
    from PIL import Image, ImageDraw
except Exception as e:
    escribir_log(f"Error importando librerías: {e}")

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.spinner import Spinner
from kivy.uix.image import Image as KivyImage
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.resources import resource_add_path
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Line, Triangle
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.animation import Animation

try:
    Window.softinput_mode = 'below_target'
except:
    pass

from database import (
    init_db, add_expense, totals_for_period, delete_expense, update_expense,
    get_available_months, get_totals_for_month, get_expenses_for_month, get_expenses_by_category_month, get_expenses_for_date_range,
    add_recurring_expense, get_recurring_expenses, delete_recurring_expense, process_recurring_expenses,
    add_savings_goal, get_savings_goals, add_to_savings_goal, delete_savings_goal, get_total_saved,
    add_debt, get_debts, update_debt_status, delete_debt, get_total_debts,
    add_income, get_income_for_month, get_all_incomes_month, delete_income,
    save_category_budget, get_category_budget, get_all_category_budgets, get_total_category_expense,
    save_user_email, get_user_email, save_user_salary, get_user_salary, save_user_pin, get_user_pin,
    save_tutorial_shown, get_tutorial_shown,
    get_all_categories, add_custom_category, delete_category
)

export_excel = None
try:
    from excel import export_excel
except Exception as e:
    pass

ruta_de_tu_app = os.path.dirname(os.path.abspath(__file__))
resource_add_path(ruta_de_tu_app)

# =========================================================================
# 👇 VARIABLES DE CONFIGURACIÓN 👇
# =========================================================================
TU_API_KEY = "re_TU_CLAVE_AQUI" 
CORREO_REMITENTE = "reportes@tusgastosapp.lat"
TU_CLAVE_GEMINI_AQUI = "TU_CLAVE_GEMINI_AQUI"
URL_FIREBASE = "https://mis-gastos-app-87b40-default-rtdb.firebaseio.com/" 
# =========================================================================

# 👇 REGISTRAMOS LA NUEVA FUENTE DE EMOJIS 👇
try:
    ruta_emoji = os.path.join(ruta_de_tu_app, "NotoEmoji-Regular.ttf")
    LabelBase.register(name="NotoEmoji", fn_regular=ruta_emoji)
except Exception as e:
    print(f"Error cargando fuente de emojis: {e}")

# =========================================================================
# 👇 CLASE NATIVA PARA LA HUELLA DACTILAR 👇
# =========================================================================
class BiometricAuth:
    def __init__(self):
        self.disponible = False
        try:
            from jnius import autoclass
            self.Context = autoclass('android.content.Context')
            self.PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.activity = self.PythonActivity.mActivity
            
            km = self.activity.getSystemService(self.Context.KEYGUARD_SERVICE)
            if km.isKeyguardSecure():
                self.disponible = True
        except Exception as e:
            self.disponible = False

    def autenticar(self, callback):
        if not self.disponible:
            callback(False)
            return
        try:
            from jnius import autoclass
            from android import activity
            
            self.KeyguardManager = autoclass('android.app.KeyguardManager')
            km = self.activity.getSystemService(self.Context.KEYGUARD_SERVICE)
            
            intent = km.createConfirmDeviceCredentialIntent(
                "Desbloquear Mis Gastos", 
                "Usa tu huella o PIN del teléfono"
            )
            
            def on_activity_result(requestCode, resultCode, data):
                if requestCode == 1001:
                    if resultCode == -1:
                        callback(True)
                    else:
                        callback(False)
                    activity.unbind(on_activity_result=on_activity_result)
            
            activity.bind(on_activity_result=on_activity_result)
            self.activity.startActivityForResult(intent, 1001)
            
        except Exception as e:
            callback(False)
# =========================================================================

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: (0.06, 0.09, 0.16, 1) 
        Rectangle:
            pos: self.pos
            size: self.size
            
    BoxLayout:
        size_hint_y: None
        height: dp(60)
        spacing: dp(5)
        Image:
            source: 'logo.png'
            size_hint_x: None
            width: dp(40)
            fit_mode: 'contain'
        Label:
            text: '[b]Mis Gastos[/b]'
            markup: True
            font_size: '20sp'
            color: (0.97, 0.98, 0.99, 1)
            halign: 'left'
            valign: 'middle'
            text_size: self.size
        
        # BOTONES CON EMOJIS UNICODE Y FUENTE NOTOEMOJI
        Button:
            text: '[font=NotoEmoji]🔒[/font]'
            markup: True
            size_hint_x: None
            width: dp(45)
            font_size: '22sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: 0, 0, 0, 0
            on_release: app.configurar_pin()
            canvas.before:
                Color:
                    rgba: (0.3, 0.35, 0.45, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(8)]
        Button:
            text: '[font=NotoEmoji]💵[/font]'
            markup: True
            size_hint_x: None
            width: dp(45)
            font_size: '22sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: 0, 0, 0, 0
            on_release: app.abrir_configuracion_salario()
            canvas.before:
                Color:
                    rgba: (0.3, 0.35, 0.45, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(8)]
        Button:
            text: '[font=NotoEmoji]✉️[/font]'
            markup: True
            size_hint_x: None
            width: dp(45)
            font_size: '22sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: 0, 0, 0, 0
            on_release: app.abrir_configuracion_correo()
            canvas.before:
                Color:
                    rgba: (0.3, 0.35, 0.45, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(8)]
                    
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: dp(145)
        padding: dp(12)
        spacing: dp(5)
        canvas.before:
            Color:
                rgba: (0.12, 0.16, 0.22, 1)
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            spacing: dp(5)
            
            Spinner:
                id: categoria
                text: 'Categoría: General'
                values: app.lista_categorias
                background_normal: ''
                background_color: (0.3, 0.35, 0.45, 1)
                color: (1, 1, 1, 1)
                on_text: self.text = 'Categoría: ' + self.text if not self.text.startswith('Categoría:') else self.text
            
            Button:
                text: '[font=NotoEmoji]➕[/font]'
                markup: True
                size_hint_x: None
                width: dp(40)
                font_size: '20sp'
                color: (1, 1, 1, 1) 
                background_normal: ''
                background_color: (0.4, 0.45, 0.55, 1)
                on_release: app.abrir_gestion_categorias()
                
            TextInput:
                id: tag_input
                hint_text: '# Etiqueta'
                hint_text_color: (0.6, 0.6, 0.6, 1)
                multiline: False
                background_normal: ''
                background_color: (0.2, 0.25, 0.3, 1)
                foreground_color: (1, 1, 1, 1)
                padding: dp(4)
                size_hint_x: 0.35
                
            Spinner:
                id: moneda
                text: 'COP'
                values: ('COP', 'USD', 'EUR')
                size_hint_x: 0.25
                background_normal: ''
                background_color: (0.2, 0.6, 0.6, 1)
                color: (1, 1, 1, 1)
            
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(50)
            spacing: dp(8)
            
            TextInput:
                id: gasto
                hint_text: 'Escribe el gasto aquí...'
                hint_text_color: (0.5, 0.5, 0.5, 1)
                multiline: True
                background_normal: ''
                background_color: (1, 1, 1, 1)
                foreground_color: (0.06, 0.09, 0.16, 1)
                padding: dp(8)
                
            Button:
                text: '[font=NotoEmoji]🎤[/font]'
                markup: True
                size_hint_x: None
                width: dp(55)
                font_size: '24sp'
                color: (1, 1, 1, 1) 
                background_normal: ''
                background_color: 0, 0, 0, 0
                on_release: app.activar_microfono()
                canvas.before:
                    Color:
                        rgba: (0.3, 0.35, 0.45, 1)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(8)]
            
    Button:
        text: '[font=NotoEmoji]💾[/font] GUARDAR GASTOS'
        markup: True
        size_hint_y: None
        height: dp(48)
        background_normal: ''
        background_color: 0, 0, 0, 0
        bold: True
        font_size: '16sp'
        color: (1, 1, 1, 1)
        on_release: app.registrar_gasto()
        canvas.before:
            Color:
                rgba: (0.06, 0.72, 0.5, 1)
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(10)]
                
    Label:
        id: estado
        text: 'Listo para registrar gastos.'
        size_hint_y: None
        height: dp(25)
        color: (0.58, 0.64, 0.69, 1)
        text_size: self.width, None
        halign: 'center'
        
    GridLayout:
        cols: 3
        size_hint_y: None
        height: dp(70)
        spacing: dp(5)
        canvas.before:
            Color:
                rgba: (0.12, 0.16, 0.22, 1)
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
                
        Label:
            text: '[b]Hoy[/b]\\n' + app.formato(app.total_hoy)
            markup: True
            color: (0.97, 0.98, 0.99, 1)
            halign: 'center'
            valign: 'middle'
            text_size: self.size
            font_size: '14sp'
            
        BoxLayout:
            orientation: 'vertical'
            Label:
                text: '[b]Mes[/b]'
                markup: True
                color: (0.97, 0.98, 0.99, 1)
                size_hint_y: None
                height: dp(20)
                font_size: '11sp'
                halign: 'center'
                text_size: self.size
            Spinner:
                id: mes_spinner
                text: 'Mes Actual'
                values: ('Mes Actual',)
                background_normal: ''
                background_color: (0.3, 0.35, 0.45, 1)
                color: (1, 1, 1, 1)
                font_size: '12sp'
                on_text: app.cambiar_mes(self.text)

        BoxLayout:
            orientation: 'vertical'
            Label:
                text: '[b]Filtro[/b]'
                markup: True
                color: (0.97, 0.98, 0.99, 1)
                size_hint_y: None
                height: dp(20)
                font_size: '11sp'
                halign: 'center'
                text_size: self.size
            Button:
                text: '[font=NotoEmoji]📅[/font]'
                markup: True
                font_size: '14sp'
                background_normal: ''
                background_color: (0.2, 0.4, 0.6, 1)
                color: (1, 1, 1, 1) 
                on_release: app.abrir_filtro_fechas()

    BoxLayout:
        id: tarjeta_saldo
        orientation: 'vertical'
        size_hint_y: None
        height: app.altura_salario
        opacity: app.opacidad_salario
        padding: dp(10)
        spacing: dp(5)
        canvas.before:
            Color:
                rgba: (0.12, 0.16, 0.22, 1)
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(12)]
        
        Label:
            id: saldo_label
            text: app.texto_saldo
            markup: True
            font_size: '14sp'
            color: app.color_saldo
            halign: 'center'
            valign: 'middle'
            text_size: self.size

    GridLayout:
        cols: 3
        size_hint_y: None
        height: dp(140)
        spacing: dp(5)
        Button:
            text: '[font=NotoEmoji]📌[/font]\\nFijos'
            markup: True
            font_size: '12sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: (0.6, 0.4, 0.2, 1)
            on_release: app.abrir_gastos_recurrentes()
        Button:
            text: '[font=NotoEmoji]🎯[/font]\\nMetas'
            markup: True
            font_size: '12sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: (0.2, 0.6, 0.6, 1)
            on_release: app.abrir_metas_ahorro()
        Button:
            text: '[font=NotoEmoji]💸[/font]\\nDeudas'
            markup: True
            font_size: '12sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: (0.8, 0.4, 0.1, 1)
            on_release: app.abrir_deudas()
        Button:
            text: '[font=NotoEmoji]💰[/font]\\nIngresos'
            markup: True
            font_size: '12sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: (0.1, 0.5, 0.2, 1)
            on_release: app.abrir_ingresos()
        Button:
            text: '[font=NotoEmoji]📋[/font]\\nPresupuesto'
            markup: True
            font_size: '12sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: (0.6, 0.2, 0.4, 1)
            on_release: app.abrir_presupuestos()
        Button:
            text: '[font=NotoEmoji]📊[/font]\\nComparar'
            markup: True
            font_size: '12sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: (0.9, 0.5, 0.1, 1)
            on_release: app.mostrar_comparacion()
        Button:
            text: '[font=NotoEmoji]📈[/font]\\nGráfico'
            markup: True
            font_size: '12sp'
            color: (1, 1, 1, 1)
            background_normal: ''
            background_color: (0.6, 0.3, 0.8, 1)
            on_release: app.mostrar_grafico()
            
    BoxLayout:
        size_hint_y: None
        height: dp(35)
        spacing: dp(5)
        
        TextInput:
            id: buscar_texto
            hint_text: '🔍 Buscar por etiqueta...'
            hint_text_color: (0.5, 0.5, 0.5, 1)
            multiline: False
            background_normal: ''
            background_color: (1, 1, 1, 0.1)
            foreground_color: (1, 1, 1, 1)
            padding: dp(4)
            on_text: app.buscar_gastos(self.text)
        
    ScrollView:
        do_scroll_x: False
        GridLayout:
            id: movimientos
            cols: 1
            spacing: dp(6)
            size_hint_y: None
            height: self.minimum_height
            
    Button:
        text: '[font=NotoEmoji]🤖[/font] PREGUNTAR A LA IA'
        markup: True
        size_hint_y: None
        height: dp(45)
        background_normal: ''
        background_color: (0.5, 0.2, 0.8, 1)
        bold: True
        font_size: '14sp'
        color: (1, 1, 1, 1)
        on_release: app.abrir_chat_ia()
        
    GridLayout:
        cols: 3
        size_hint_y: None
        height: dp(45)
        spacing: dp(5)
        
        Button:
            text: '[font=NotoEmoji]📗[/font] EXCEL'
            markup: True
            font_size: '14sp'
            background_normal: ''
            background_color: (0.1, 0.5, 0.8, 1)
            color: (1, 1, 1, 1)
            on_release: app.generar_excel()
            
        Button:
            text: '[font=NotoEmoji]📕[/font] PDF'
            markup: True
            font_size: '14sp'
            background_normal: ''
            background_color: (0.8, 0.2, 0.2, 1)
            color: (1, 1, 1, 1)
            on_release: app.generar_pdf()
            
        Button:
            text: '[font=NotoEmoji]☁️[/font] BACKUP'
            markup: True
            font_size: '14sp'
            background_normal: ''
            background_color: (0.3, 0.35, 0.45, 1)
            color: (1, 1, 1, 1)
            on_release: app.generar_respaldo()
'''

class PieChart(Widget):
    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)
        self.data = data 
        self.bind(pos=self.redraw, size=self.redraw)
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        if not self.data: return
        total = sum(item[1] for item in self.data)
        if total == 0: return

        cx, cy = self.center_x, self.center_y
        radius = min(self.width, self.height) / 2 * 0.85
        start_angle = 0

        with self.canvas:
            Color(0.2, 0.2, 0.2, 1)
            Line(circle=(cx, cy, radius), width=2)
            for label, value, color in self.data:
                angle = (value / total) * 2 * math.pi
                end_angle = start_angle + angle
                Color(*color)
                segments = max(int(angle * 180 / math.pi), 2)
                for i in range(segments):
                    a1 = start_angle + (end_angle - start_angle) * i / segments
                    a2 = start_angle + (end_angle - start_angle) * (i + 1) / segments
                    x1 = cx + radius * math.cos(a1)
                    y1 = cy + radius * math.sin(a1)
                    x2 = cx + radius * math.cos(a2)
                    y2 = cy + radius * math.sin(a2)
                    Triangle(points=[cx, cy, x1, y1, x2, y2])
                start_angle = end_angle

class BarChart(Widget):
    def __init__(self, data, **kwargs):
        super().__init__(**kwargs)
        self.data = data 
        self.bind(pos=self.redraw, size=self.redraw)
        self.redraw()

    def redraw(self, *args):
        self.canvas.clear()
        if not self.data: return
        max_val = max([d[1] for d in self.data]) if self.data else 1
        if max_val == 0: max_val = 1
        
        width_per_bar = self.width / (len(self.data) * 1.5)
        spacing = width_per_bar * 0.25
        
        with self.canvas:
            Color(0.5, 0.5, 0.5, 1)
            Line(points=[self.x, self.y, self.right, self.y], width=1.5)
            
            for i, (label, value, color) in enumerate(self.data):
                Color(*color)
                bar_height = (value / max_val) * (self.height * 0.8)
                x = self.x + spacing + (i * (width_per_bar + spacing))
                y = self.y
                Rectangle(pos=(x, y), size=(width_per_bar, bar_height))

def parse_expense(text):
    cleaned = text.strip()
    if not cleaned: return None
    pattern = re.compile(r'(?P<pre>\$)?\s*(?P<amount>\d+(?:[\s.,]\d{3})*(?:[\.,]\d{1,2})?)(?:\s*(?P<cur>pesos?|cop))?', re.IGNORECASE)
    matches = [m for m in pattern.finditer(cleaned) if m.group('amount')]
    if not matches: raise ValueError(f'No encontré un valor numérico en: "{cleaned}"')
    def score(m):
        s = 0
        if m.group('pre') or m.group('cur'): s += 2
        if re.search(r'[.,]', m.group('amount')): s += 1
        return s
    chosen = max(matches, key=lambda m: (score(m), m.start()))
    raw = chosen.group('amount')
    raw_clean = raw.replace(' ', '')
    m = re.match(r'^(\d+)[.,](\d{1,2})$', raw_clean)
    if m: amount = int(round(int(m.group(1)) + float(f'0.{m.group(2)}')))
    else: amount = int(re.sub(r'[.,]', '', raw_clean))
    description = (cleaned[:chosen.start()] + ' ' + cleaned[chosen.end():])
    description = re.sub(r'\s+', ' ', description).strip(' ,.-$')
    if not description: description = "Gasto sin descripción"
    if amount <= 0: raise ValueError(f'El valor debe ser mayor que cero en: "{cleaned}"')
    return description, amount

class GastosApp(App):
    total_hoy = NumericProperty(0)
    total_mes = NumericProperty(0)
    texto_saldo = StringProperty("")
    color_saldo = ListProperty([0.97, 0.98, 0.99, 1])
    altura_salario = NumericProperty(0)
    opacidad_salario = NumericProperty(0)
    lista_categorias = ListProperty(['General', 'Comida', 'Transporte', 'Servicios', 'Salud', 'Ocio', 'Otros'])
    _stt_clock = None
    mes_actual_seleccionado = None
    filtro_inicio = None
    filtro_fin = None
    codigo_otp = None
    otp_solicitado = False

    def build(self):
        self.title = 'Mi Control de Gastos'
        self.db_path = os.path.join(self.user_data_dir, 'gastos.db')
        self.seguridad = BiometricAuth()
        try:
            init_db(self.db_path)
            return Builder.load_string(KV)
        except Exception as e:
            return Label(text=f"Error Crítico:\n{e}")

    def on_start(self):
        try:
            from android.permissions import request_permissions, Permission, check_permission
            perms = [Permission.INTERNET]
            if not check_permission(Permission.RECORD_AUDIO):
                perms.append(Permission.RECORD_AUDIO)
            request_permissions(perms)
        except Exception as e:
            pass
            
        Clock.schedule_once(self.iniciar_app, 0.5)

    def iniciar_app(self, dt):
        try:
            if not self.verificar_pin(): return
            if not get_tutorial_shown(self.db_path):
                self.mostrar_bienvenida()
                save_tutorial_shown(self.db_path)
            self.actualizar_categorias() 
            self.actualizar_meses_spinner()
            self.actualizar_pantalla()
        except Exception as e:
            self.aviso(f"Error al iniciar:\n{str(e)}", "Error Crítico")

    def actualizar_categorias(self):
        cats = get_all_categories(self.db_path)
        self.lista_categorias = cats
        if self.root and 'categoria' in self.root.ids:
            self.root.ids.categoria.values = tuple(cats)

    def abrir_gestion_categorias(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        scroll = ScrollView(size_hint_y=0.6)
        lista = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        lista.bind(minimum_height=lista.setter('height'))
        
        def recargar_lista():
            lista.clear_widgets()
            for cat in get_all_categories(self.db_path):
                fila = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
                lbl = Label(text=cat, halign='left', valign='middle', text_size=(dp(200), None))
                btn_del = Button(text="[font=NotoEmoji]🗑️[/font]", markup=True, size_hint_x=None, width=dp(40), font_size='18sp', background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1))
                
                if cat not in ['General', 'Comida', 'Transporte', 'Servicios', 'Salud', 'Ocio', 'Otros']:
                    btn_del.bind(on_release=lambda instance, c=cat: (delete_category(self.db_path, c), recargar_lista(), self.actualizar_categorias()))
                else:
                    btn_del.disabled = True
                    btn_del.opacity = 0.3
                    
                fila.add_widget(lbl); fila.add_widget(btn_del); lista.add_widget(fila)
                
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        inp_nueva_cat = TextInput(hint_text="Nueva Categoría (Ej: Mascotas)", multiline=False, size_hint_y=None, height=dp(40))
        btn_add = Button(text="[font=NotoEmoji]➕[/font] Agregar Categoría", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.06, 0.72, 0.5, 1), color=(1,1,1,1))
        
        def agregar(instance):
            nueva = inp_nueva_cat.text.strip().capitalize()
            if nueva:
                if add_custom_category(self.db_path, nueva):
                    inp_nueva_cat.text = ""
                    recargar_lista()
                    self.actualizar_categorias()
                else:
                    self.aviso("Esa categoría ya existe.", "Error")
                    
        btn_add.bind(on_release=agregar)
        form.add_widget(inp_nueva_cat); form.add_widget(btn_add)
        contenido.add_widget(form)
        Popup(title='Gestionar Categorías', content=contenido, size_hint=(0.95, 0.8)).open()

    def subir_a_la_nube(self):
        correo = get_user_email(self.db_path)
        if not correo or not URL_FIREBASE.startswith("http"): return
        def tarea():
            try:
                correo_seguro = urllib.parse.quote(correo, safe='')
                url = f"{URL_FIREBASE}/backups/{correo_seguro}.json"
                with open(self.db_path, "rb") as f:
                    db_b64 = base64.b64encode(f.read()).decode('utf-8')
                data = {"db": db_b64, "fecha": datetime.now().isoformat()}
                requests.put(url, json=data, timeout=15)
            except Exception as e:
                pass
        threading.Thread(target=tarea).start()

    def descargar_de_la_nube(self, callback=None):
        correo = get_user_email(self.db_path)
        if not correo or not URL_FIREBASE.startswith("http"):
            if callback: callback(False, "Configura tu correo o la URL de Firebase.")
            return
        def tarea():
            try:
                correo_seguro = urllib.parse.quote(correo, safe='')
                url = f"{URL_FIREBASE}/backups/{correo_seguro}.json"
                res = requests.get(url, timeout=15)
                if res.status_code == 200 and res.json() and "db" in res.json():
                    db_b64 = res.json()["db"]
                    db_bytes = base64.b64decode(db_b64)
                    if os.path.exists(self.db_path):
                        os.rename(self.db_path, self.db_path + ".bak")
                    with open(self.db_path, "wb") as f:
                        f.write(db_bytes)
                    Clock.schedule_once(lambda dt: self.actualizar_categorias(), 0)
                    Clock.schedule_once(lambda dt: self.actualizar_meses_spinner(), 0)
                    Clock.schedule_once(lambda dt: self.actualizar_pantalla(), 0)
                    if callback: Clock.schedule_once(lambda dt: callback(True, "Datos restaurados."), 0)
                else:
                    if callback: Clock.schedule_once(lambda dt: callback(False, "No hay datos en la nube."), 0)
            except Exception as e:
                if callback: Clock.schedule_once(lambda dt: callback(False, f"Error: {e}"), 0)
        threading.Thread(target=tarea).start()

    def abrir_chat_ia(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        lbl_titulo = Label(text="[font=NotoEmoji]🤖[/font] Asesor Financiero IA", markup=True, size_hint_y=None, height=dp(40), color=(0.5, 0.2, 0.8, 1), font_size='18sp')
        contenido.add_widget(lbl_titulo)
        
        scroll = ScrollView(size_hint_y=0.7)
        lbl_respuesta = Label(text="Hola, soy tu asesor financiero. ¿En qué te puedo ayudar hoy?", halign='left', valign='top', size_hint_y=None, color=(1,1,1,1))
        lbl_respuesta.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        lbl_respuesta.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(lbl_respuesta)
        
        input_pregunta = TextInput(hint_text="Ej: ¿Cómo puedo ahorrar este mes?", multiline=False, size_hint_y=None, height=dp(45), background_normal='', background_color=(1, 1, 1, 1), foreground_color=(0, 0, 0, 1), padding=dp(8))
        btn_enviar = Button(text="[font=NotoEmoji]✈️[/font] Enviar a la IA", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.5, 0.2, 0.8, 1), bold=True, color=(1,1,1,1))
        
        contenido.add_widget(scroll)
        contenido.add_widget(input_pregunta)
        contenido.add_widget(btn_enviar)
        
        popup = Popup(title='Asesor Financiero', content=contenido, size_hint=(0.95, 0.8))
        popup.open()
        
        def enviar(instance):
            pregunta = input_pregunta.text.strip()
            if not pregunta: return
            lbl_respuesta.text = "Pensando..."
            input_pregunta.text = ""
            btn_enviar.disabled = True
            btn_enviar.text = "Consultando..."
            threading.Thread(target=self.consultar_ia, args=(pregunta, lbl_respuesta, btn_enviar)).start()
            
        btn_enviar.bind(on_release=enviar)

    def consultar_ia(self, pregunta, label_respuesta, btn_enviar):
        try:
            mes_actual = datetime.now().strftime('%Y-%m')
            gastos = get_expenses_for_month(self.db_path, mes_actual)
            resumen = ""
            for row in gastos:
                desc, amount, cat = row[2], row[3], row[4]
                tags = row[6] if len(row) > 6 else ""
                etiqueta = f" #{tags}" if tags else ""
                resumen += f"- {desc}{etiqueta} ({cat}): ${amount}\n"
            if not resumen: resumen = "El usuario no tiene gastos registrados este mes."
            prompt = f"Eres un asesor financiero experto y amigable. Pregunta: '{pregunta}'. Gastos: {resumen}. Responde en español, máx 3 párrafos."
            
            headers = {'Content-Type': 'application/json'}
            data = {"contents": [{"parts":[{"text": prompt}]}]}
            
            # LISTA COMPLETA DE MODELOS GEMINI GRATUITOS VIGENTES
            modelos = [
                "gemini-1.5-flash",
                "gemini-1.5-flash-8b",
                "gemini-1.5-pro",
                "gemini-2.0-flash-exp",
                "gemini-1.0-pro",
                "gemini-pro"
            ]
            
            respuesta_exitosa = False
            texto_final = ""
            for modelo in modelos:
                Clock.schedule_once(lambda dt, m=modelo: setattr(label_respuesta, 'text', f"Conectando con {m}..."), 0)
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={TU_CLAVE_GEMINI_AQUI}"
                try:
                    response = requests.post(url, headers=headers, json=data, timeout=15)
                    if response.status_code == 200:
                        json_resp = response.json()
                        if 'candidates' in json_resp and len(json_resp['candidates']) > 0:
                            texto_final = json_resp['candidates'][0]['content']['parts'][0]['text']
                            respuesta_exitosa = True
                            break
                except Exception:
                    continue 
            if respuesta_exitosa:
                Clock.schedule_once(lambda dt: setattr(label_respuesta, 'text', texto_final), 0)
            else:
                Clock.schedule_once(lambda dt: setattr(label_respuesta, 'text', "❌ Modelos saturados o clave incorrecta. Espera 1 min."), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(label_respuesta, 'text', f"Error: {str(e)}"), 0)
        finally:
            Clock.schedule_once(lambda dt: (setattr(btn_enviar, 'disabled', False), setattr(btn_enviar, 'text', "[font=NotoEmoji]✈️[/font] Enviar a la IA")), 0)

    def mostrar_bienvenida(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        logo_img = KivyImage(source='logo.png', size_hint_y=0.35, fit_mode='contain')
        contenido.add_widget(logo_img)
        texto = "[b]¡Bienvenido a Gestión de Gastos![/b]\n\n1. Configura tu Correo y Salario.\n2. Registra tus gastos.\n3. Usa el botón IA."
        lbl = Label(text=texto, markup=True, halign='center', valign='middle', size_hint_y=0.5)
        lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        contenido.add_widget(lbl)
        btn_ok = Button(text="[font=NotoEmoji]✔️[/font] ¡Empezar!", markup=True, size_hint_y=None, height=dp(50), font_size='16sp', background_color=(0.06, 0.72, 0.5, 1), bold=True, color=(1,1,1,1))
        contenido.add_widget(btn_ok)
        popup = Popup(title='Bienvenido', content=contenido, size_hint=(0.9, 0.8), auto_dismiss=False)
        btn_ok.bind(on_release=popup.dismiss)
        popup.open()

    def verificar_pin(self):
        pin_guardado = get_user_pin(self.db_path)
        if not pin_guardado: return True
        
        self.acceso_concedido = False
        contenido = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        inp_pin = TextInput(hint_text="****", password=True, multiline=False, input_filter='int', halign='center', font_size='24sp', size_hint_y=None, height=dp(50))
        
        btn_entrar = Button(text="[font=NotoEmoji]🔓[/font] Desbloquear", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.06, 0.72, 0.5, 1), color=(1,1,1,1))
        
        contenido.add_widget(Label(text="Ingresa tu PIN o usa tu huella:", halign='center'))
        contenido.add_widget(inp_pin)
        contenido.add_widget(btn_entrar)
        
        if self.seguridad.disponible:
            btn_huella = Button(text="[font=NotoEmoji]👆[/font] Usar Huella", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.2, 0.4, 0.8, 1), color=(1,1,1,1))
            contenido.add_widget(btn_huella)
            
            def exito_huella(exito):
                if exito:
                    self.acceso_concedido = True
                    popup.dismiss()
                    self.actualizar_meses_spinner()
                    self.actualizar_pantalla()
                else:
                    self.aviso("Huella cancelada o incorrecta.", "Error")
                    
            btn_huella.bind(on_release=lambda x: self.seguridad.autenticar(exito_huella))
        
        btn_olvido = Button(text="¿Olvidaste tu PIN?", size_hint_y=None, height=dp(30), background_normal='', background_color=(0.3, 0.3, 0.3, 1), color=(1,1,1,1))
        contenido.add_widget(btn_olvido)
        
        popup = Popup(title='App Bloqueada', content=contenido, size_hint=(0.8, 0.65), auto_dismiss=False)
        
        def desbloquear(instance):
            if inp_pin.text == pin_guardado:
                self.acceso_concedido = True
                popup.dismiss()
                self.actualizar_meses_spinner()
                self.actualizar_pantalla()
            else:
                inp_pin.text = ""
                self.aviso("PIN incorrecto", "Error")
                
        btn_entrar.bind(on_release=desbloquear)
        btn_olvido.bind(on_release=lambda x: (popup.dismiss(), self.solicitar_correo_recuperacion()))
        popup.open()
        return False

    def solicitar_correo_recuperacion(self):
        correo_registrado = get_user_email(self.db_path)
        if not correo_registrado:
            self.aviso("No has configurado un correo.", "Sin correo")
            return
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        inp_correo = TextInput(hint_text="Ingresa tu correo registrado", multiline=False, size_hint_y=None, height=dp(40))
        btn_validar = Button(text="[font=NotoEmoji]✉️[/font] Enviar Código", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.1, 0.5, 0.8, 1), color=(1,1,1,1))
        contenido.add_widget(Label(text="Escribe tu correo para recibir un código:"))
        contenido.add_widget(inp_correo)
        contenido.add_widget(btn_validar)
        popup = Popup(title='Recuperar PIN', content=contenido, size_hint=(0.9, 0.4))
        def validar(instance):
            if inp_correo.text.strip().lower() == correo_registrado.lower():
                popup.dismiss()
                self.codigo_otp = str(random.randint(100000, 999999))
                self.otp_solicitado = True
                self.aviso("Enviando código...", "Procesando")
                threading.Thread(target=self._enviar_otp_email, args=(correo_registrado, self.codigo_otp)).start()
                Clock.schedule_once(lambda dt: self.ingresar_codigo_otp(), 2)
            else:
                self.aviso("El correo no coincide.", "Error")
        btn_validar.bind(on_release=validar)
        popup.open()

    def ingresar_codigo_otp(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        inp_codigo = TextInput(hint_text="Código de 6 dígitos", multiline=False, input_filter='int', size_hint_y=None, height=dp(40), halign='center')
        btn_validar = Button(text="[font=NotoEmoji]✔️[/font] Verificar", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.1, 0.5, 0.8, 1), color=(1,1,1,1))
        contenido.add_widget(Label(text="Ingresa el código de 6 dígitos:"))
        contenido.add_widget(inp_codigo)
        contenido.add_widget(btn_validar)
        popup = Popup(title='Verificación', content=contenido, size_hint=(0.9, 0.45), auto_dismiss=False)
        def validar(instance):
            if self.codigo_otp and inp_codigo.text.strip() == self.codigo_otp:
                popup.dismiss()
                self.crear_nuevo_pin()
            else:
                self.aviso("Código incorrecto.", "Error")
        btn_validar.bind(on_release=validar)
        popup.open()

    def crear_nuevo_pin(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        inp_nuevo_pin = TextInput(hint_text="Nuevo PIN de 4 dígitos", password=True, multiline=False, input_filter='int', size_hint_y=None, height=dp(40))
        btn_guardar = Button(text="[font=NotoEmoji]📝[/font] Guardar Nuevo PIN", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.06, 0.72, 0.5, 1), color=(1,1,1,1))
        contenido.add_widget(Label(text="Ingresa tu nuevo PIN:"))
        contenido.add_widget(inp_nuevo_pin)
        contenido.add_widget(btn_guardar)
        popup = Popup(title='Nuevo PIN', content=contenido, size_hint=(0.9, 0.35))
        def guardar(instance):
            nuevo_pin = inp_nuevo_pin.text.strip()
            if len(nuevo_pin) >= 4:
                save_user_pin(self.db_path, nuevo_pin)
                self.aviso("PIN actualizado.", "Éxito")
                popup.dismiss()
                self.otp_solicitado = False
                self.codigo_otp = None
                self.verificar_pin()
            else:
                self.aviso("El PIN debe tener al menos 4 dígitos.", "Error")
        btn_guardar.bind(on_release=guardar)
        popup.open()

    def _enviar_otp_email(self, correo_destino, codigo):
        try:
            headers = {"Authorization": f"Bearer {TU_API_KEY}", "Content-Type": "application/json"}
            html_content = f"<h2>Recuperación de PIN</h2><p>Tu código es:</p><h1>{codigo}</h1>"
            data = {"from": f"Seguridad App <{CORREO_REMITENTE}>", "to": [correo_destino], "subject": "Código de Seguridad", "html": html_content}
            requests.post("https://api.resend.com/emails", headers=headers, json=data, timeout=30)
        except Exception as e:
            pass

    def configurar_pin(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        pin_actual = get_user_pin(self.db_path)
        inp_pin = TextInput(text=pin_actual if pin_actual else "", hint_text="Nuevo PIN (vacío para quitar)", password=True, input_filter='int', multiline=False, size_hint_y=None, height=dp(40))
        btn_guardar = Button(text="[font=NotoEmoji]💾[/font] Guardar PIN", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.06, 0.72, 0.5, 1), color=(1,1,1,1))
        contenido.add_widget(Label(text="Configurar PIN:"))
        contenido.add_widget(inp_pin)
        contenido.add_widget(btn_guardar)
        popup = Popup(title='Seguridad', content=contenido, size_hint=(0.9, 0.35))
        def guardar(instance):
            save_user_pin(self.db_path, inp_pin.text.strip())
            self.aviso("PIN actualizado." if inp_pin.text.strip() else "Seguridad desactivada.", "Éxito")
            popup.dismiss()
        btn_guardar.bind(on_release=guardar)
        popup.open()

    def abrir_configuracion_correo(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        correo_actual = get_user_email(self.db_path) or ""
        entrada_correo = TextInput(text=correo_actual, hint_text="tucorreo@gmail.com", multiline=False, size_hint_y=None, height=dp(40))
        btn_guardar = Button(text="[font=NotoEmoji]☁️[/font] Guardar y Sincronizar", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.06, 0.72, 0.5, 1), color=(1,1,1,1))
        btn_descargar = Button(text="[font=NotoEmoji]📥[/font] Descargar Datos", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.2, 0.4, 0.8, 1), color=(1,1,1,1))
        
        contenido.add_widget(Label(text="Correo para reportes y respaldo en la nube:"))
        contenido.add_widget(entrada_correo)
        contenido.add_widget(btn_guardar)
        contenido.add_widget(btn_descargar)
        
        popup = Popup(title='Mi Correo', content=contenido, size_hint=(0.9, 0.45))
        
        def guardar(instance):
            nuevo_correo = entrada_correo.text.strip()
            if "@" in nuevo_correo:
                save_user_email(self.db_path, nuevo_correo)
                self.aviso("¡Correo guardado!\nSincronizando...", "Éxito")
                popup.dismiss()
                def callback_descarga(exito, msj):
                    if exito: self.aviso(msj, "Sincronización Exitosa")
                self.descargar_de_la_nube(callback_descarga)
            else:
                self.aviso("Ingresa un correo válido.", "Error")
                
        def descargar_manual(instance):
            if not entrada_correo.text.strip():
                self.aviso("Primero escribe tu correo.", "Error")
                return
            save_user_email(self.db_path, entrada_correo.text.strip())
            popup.dismiss()
            self.aviso("Buscando datos...", "Procesando")
            def callback_descarga(exito, msj):
                self.aviso(msj, "Nube" if exito else "Error")
            self.descargar_de_la_nube(callback_descarga)
            
        btn_guardar.bind(on_release=guardar)
        btn_descargar.bind(on_release=descargar_manual)
        popup.open()

    def abrir_filtro_fechas(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        row_inicio = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        d1 = Spinner(text='1', values=[str(i) for i in range(1, 32)], size_hint_x=0.3)
        m1 = Spinner(text='1', values=[str(i) for i in range(1, 13)], size_hint_x=0.3)
        y1 = Spinner(text=str(datetime.now().year), values=[str(i) for i in range(2020, 2031)], size_hint_x=0.4)
        row_inicio.add_widget(d1); row_inicio.add_widget(m1); row_inicio.add_widget(y1)
        
        row_fin = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        d2 = Spinner(text=str(datetime.now().day), values=[str(i) for i in range(1, 32)], size_hint_x=0.3)
        m2 = Spinner(text=str(datetime.now().month), values=[str(i) for i in range(1, 13)], size_hint_x=0.3)
        y2 = Spinner(text=str(datetime.now().year), values=[str(i) for i in range(2020, 2031)], size_hint_x=0.4)
        row_fin.add_widget(d2); row_fin.add_widget(m2); row_fin.add_widget(y2)

        botones = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
        btn_aplicar = Button(text="[font=NotoEmoji]✔️[/font] Aplicar", markup=True, font_size='16sp', background_color=(0.2, 0.4, 0.6, 1), color=(1,1,1,1))
        btn_borrar = Button(text="[font=NotoEmoji]❌[/font] Quitar", markup=True, font_size='16sp', background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1))
        botones.add_widget(btn_aplicar)
        botones.add_widget(btn_borrar)
        
        contenido.add_widget(Label(text="Desde:"))
        contenido.add_widget(row_inicio)
        contenido.add_widget(Label(text="Hasta:"))
        contenido.add_widget(row_fin)
        contenido.add_widget(botones)
        
        popup = Popup(title='Filtro de Fechas', content=contenido, size_hint=(0.9, 0.5))
        
        def aplicar(instance):
            try:
                fecha1 = f"{y1.text}-{int(m1.text):02d}-{int(d1.text):02d}"
                fecha2 = f"{y2.text}-{int(m2.text):02d}-{int(d2.text):02d}"
                self.filtro_inicio = fecha1
                self.filtro_fin = fecha2
                self.mes_actual_seleccionado = None
                popup.dismiss()
                self.actualizar_pantalla()
            except Exception as e:
                self.aviso(f"Error en fechas: {e}", "Error")
                
        def borrar(instance):
            self.filtro_inicio = None
            self.filtro_fin = None
            popup.dismiss()
            self.actualizar_pantalla()
            
        btn_aplicar.bind(on_release=aplicar)
        btn_borrar.bind(on_release=borrar)
        popup.open()

    @staticmethod
    def formato(value):
        return '$ ' + f'{int(round(value)):,}'.replace(',', '.')

    def aviso(self, mensaje, titulo='Mi Control de Gastos'):
        lbl = Label(text=mensaje, halign='center', valign='middle')
        lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        popup = Popup(title=titulo, content=lbl, size_hint=(0.9, 0.5), title_align='center', separator_color=(0.08, 0.43, 0.32, 1))
        popup.opacity = 0
        popup.open()
        anim = Animation(opacity=1, duration=0.3)
        anim.start(popup)

    def activar_microfono(self):
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.RECORD_AUDIO])
            
            from plyer import stt
            self.root.ids.estado.text = "Escuchando..."
            stt.start()
            if self._stt_clock: self._stt_clock.cancel()
            self._stt_clock = Clock.schedule_interval(self._revisar_resultado_voz, 0.5)
        except Exception as e:
            self.aviso(f"Error de micrófono: Asegúrate de dar permisos manualmente en Ajustes de Android.", "Error de Voz")

    def _revisar_resultado_voz(self, dt):
        try:
            from plyer import stt
            if stt.results:
                texto_reconocido = stt.results[0]
                texto_actual = self.root.ids.gasto.text
                self.root.ids.gasto.text = f"{texto_actual} {texto_reconocido}".strip()
                self.root.ids.estado.text = "¡Texto agregado!"
                if self._stt_clock:
                    self._stt_clock.cancel()
                    self._stt_clock = None
                stt.stop()
                return
            if stt.errors:
                self.root.ids.estado.text = "No se escuchó nada."
                if self._stt_clock:
                    self._stt_clock.cancel()
                    self._stt_clock = None
                stt.stop()
                return
        except Exception:
            if self._stt_clock:
                self._stt_clock.cancel()
                self._stt_clock = None

    def actualizar_meses_spinner(self):
        if not self.root or 'mes_spinner' not in self.root.ids: return
        meses_db = get_available_months(self.db_path)
        valores = ['Mes Actual'] + meses_db
        self.root.ids.mes_spinner.values = valores
        if self.mes_actual_seleccionado and self.mes_actual_seleccionado not in valores:
            self.root.ids.mes_spinner.text = 'Mes Actual'
            self.mes_actual_seleccionado = None

    def cambiar_mes(self, texto):
        if not self.root or 'movimientos' not in self.root.ids: return
        self.filtro_inicio = None
        self.filtro_fin = None
        if texto == 'Mes Actual': self.mes_actual_seleccionado = None
        else: self.mes_actual_seleccionado = texto
        self.actualizar_pantalla()

    def buscar_gastos(self, texto):
        if not self.root or 'movimientos' not in self.root.ids: return
        self.actualizar_pantalla()

    def mostrar_comparacion(self):
        now = datetime.now()
        mes_actual_str = now.strftime('%Y-%m')
        total_mes_actual = get_totals_for_month(self.db_path, mes_actual_str)
        
        if now.month == 1:
            mes_anterior_str = f"{now.year - 1}-12"
            nombre_mes_ant = "Dic"
        else:
            mes_anterior_str = f"{now.year}-{now.month - 1:02d}"
            nombre_mes_ant = now.replace(month=now.month - 1).strftime('%b')
            
        total_mes_anterior = get_totals_for_month(self.db_path, mes_anterior_str)
        nombre_mes_act = now.strftime('%b')

        if total_mes_actual == 0 and total_mes_anterior == 0:
            self.aviso("No hay gastos registrados en ninguno de los dos meses.", "Sin datos")
            return

        datos_barras = [
            (nombre_mes_anterior, total_mes_anterior, (0.8, 0.3, 0.3, 1)),
            (nombre_mes_act, total_mes_actual, (0.2, 0.6, 0.8, 1))
        ]

        contenido = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        contenido.add_widget(Label(text="[b]Comparación de Gastos[/b]", markup=True, size_hint_y=None, height=dp(40), font_size='18sp', color=(1,1,1,1)))
        contenido.add_widget(BarChart(datos_barras, size_hint_y=0.6))
        
        leyenda = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50), spacing=dp(10))
        for label, val, color in datos_barras:
            box = BoxLayout(orientation='vertical')
            box.add_widget(Label(text=f"[b]{label}[/b]", markup=True, color=color))
            box.add_widget(Label(text=self.formato(val), color=(1,1,1,1)))
            leyenda.add_widget(box)
            
        contenido.add_widget(leyenda)
        Popup(title='Comparación Mensual', content=contenido, size_hint=(0.9, 0.7)).open()

    def mostrar_grafico(self):
        if self.mes_actual_seleccionado:
            year_month = self.mes_actual_seleccionado
            titulo_mes = year_month
        else:
            now = datetime.now()
            year_month = now.strftime('%Y-%m')
            titulo_mes = "Este mes"
        datos = get_expenses_by_category_month(self.db_path, year_month)
        if not datos:
            self.aviso("No hay gastos registrados.", "Sin datos")
            return
        if len(datos) == 1:
            self.aviso(f"Todos tus gastos están en '{datos[0][0]}'.", "Solo una categoría")
        total_mes = sum([fila[1] for fila in datos])
        colores = [(0.9, 0.3, 0.3, 1), (0.3, 0.7, 0.9, 1), (0.3, 0.9, 0.5, 1), (0.9, 0.8, 0.3, 1), (0.7, 0.4, 0.9, 1), (0.9, 0.5, 0.1, 1)]
        datos_grafico = [(cat, monto, colores[i % len(colores)]) for i, (cat, monto) in enumerate(datos)]
        contenido = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        contenido.add_widget(Label(text=f"[b]Gastos de {titulo_mes}[/b]", markup=True, size_hint_y=None, height=dp(40), font_size='18sp', color=(1,1,1,1)))
        contenido.add_widget(PieChart(datos_grafico, size_hint_y=0.6))
        scroll_leyenda = ScrollView(size_hint_y=0.4)
        leyenda = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8))
        leyenda.bind(minimum_height=leyenda.setter('height'))
        for cat, monto, color_actual in datos_grafico:
            porcentaje = (monto / total_mes) * 100
            fila = BoxLayout(size_hint_y=None, height=dp(25), spacing=dp(10))
            cuadro = Widget(size_hint_x=None, width=dp(20), height=dp(20))
            with cuadro.canvas:
                Color(*color_actual)
                rect = Rectangle(pos=cuadro.pos, size=cuadro.size)
            cuadro.bind(pos=lambda inst, val, r=rect: setattr(r, 'pos', val))
            cuadro.bind(size=lambda inst, val, r=rect: setattr(r, 'size', val))
            lbl = Label(text=f"{cat}: {self.formato(monto)} ({porcentaje:.1f}%)", halign='left', valign='middle', color=(1,1,1,1))
            lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
            fila.add_widget(cuadro)
            fila.add_widget(lbl)
            leyenda.add_widget(fila)
        scroll_leyenda.add_widget(leyenda)
        contenido.add_widget(scroll_leyenda)
        Popup(title='Estadísticas', content=contenido, size_hint=(0.95, 0.8)).open()

    def abrir_configuracion_salario(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        salario_actual = get_user_salary(self.db_path)
        entrada_salario = TextInput(text=str(int(salario_actual)) if salario_actual > 0 else "", hint_text="Ej: 1500000", multiline=False, input_filter='int', size_hint_y=None, height=dp(40))
        btn_guardar = Button(text="[font=NotoEmoji]💾[/font] Guardar Salario", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.06, 0.72, 0.5, 1), color=(1,1,1,1))
        contenido.add_widget(Label(text="Tu salario mensual:"))
        contenido.add_widget(entrada_salario)
        contenido.add_widget(btn_guardar)
        popup = Popup(title='Mi Salario', content=contenido, size_hint=(0.9, 0.4))
        def guardar(instance):
            texto_salario = entrada_salario.text.strip()
            if texto_salario == "":
                save_user_salary(self.db_path, 0)
                self.aviso("Salario desactivado.", "Eliminado")
            else:
                save_user_salary(self.db_path, float(texto_salario))
                self.aviso(f"Salario guardado: {self.formato(float(texto_salario))}", "Éxito")
            popup.dismiss()
            self.actualizar_pantalla()
            self.subir_a_la_nube()
        btn_guardar.bind(on_release=guardar)
        popup.open()

    def abrir_presupuestos(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        scroll = ScrollView(size_hint_y=0.6)
        lista = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        lista.bind(minimum_height=lista.setter('height'))
        
        def recargar_lista():
            lista.clear_widgets()
            presupuestos = get_all_category_budgets(self.db_path)
            mes_actual = datetime.now().strftime('%Y-%m')
            for cat, monto_limite in presupuestos:
                gastado = get_total_category_expense(self.db_path, mes_actual, cat)
                porcentaje = (gastado / monto_limite) * 100 if monto_limite > 0 else 0
                color = (0.9, 0.3, 0.3, 1) if gastado > monto_limite else (0.2, 0.9, 0.5, 1)
                texto = f"[b]{cat}[/b]: Límite {self.formato(monto_limite)}\nGastado {self.formato(gastado)} ({porcentaje:.1f}%)"
                lbl = Label(text=texto, markup=True, halign='left', valign='middle', size_hint_y=None, height=dp(45), color=color, text_size=(dp(300), None))
                lista.add_widget(lbl)
                
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        spinner_cat = Spinner(text='General', values=tuple(self.lista_categorias), size_hint_y=None, height=dp(35), background_normal='', background_color=(0.3, 0.35, 0.45, 1))
        inp_monto = TextInput(hint_text="Límite (Ej: 500000)", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        btn_add = Button(text="[font=NotoEmoji]➕[/font] Establecer Límite", markup=True, size_hint_y=None, height=dp(40), font_size='16sp', background_color=(0.6, 0.2, 0.4, 1), color=(1,1,1,1))
        
        def agregar(instance):
            if inp_monto.text:
                save_category_budget(self.db_path, spinner_cat.text, int(inp_monto.text))
                inp_monto.text = ""
                recargar_lista()
                self.subir_a_la_nube()
                
        btn_add.bind(on_release=agregar)
        form.add_widget(spinner_cat); form.add_widget(inp_monto); form.add_widget(btn_add)
        contenido.add_widget(form)
        
        Popup(title='Presupuestos', content=contenido, size_hint=(0.95, 0.8)).open()

    def abrir_ingresos(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        scroll = ScrollView(size_hint_y=0.6)
        lista = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        lista.bind(minimum_height=lista.setter('height'))
        
        def recargar_lista():
            lista.clear_widgets()
            mes_actual = datetime.now().strftime('%Y-%m')
            for i_id, desc, amount, date_str in get_all_incomes_month(self.db_path, mes_actual):
                fila = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
                lbl = Label(text=f"{desc} - {self.formato(amount)}", halign='left', valign='middle', color=(0.2, 0.9, 0.5, 1), text_size=(dp(200), None))
                btn_del = Button(text="[font=NotoEmoji]🗑️[/font]", markup=True, size_hint_x=None, width=dp(40), font_size='16sp', background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1))
                btn_del.bind(on_release=lambda instance, x=i_id: (delete_income(self.db_path, x), recargar_lista(), self.actualizar_pantalla(), self.subir_a_la_nube()))
                fila.add_widget(lbl); fila.add_widget(btn_del); lista.add_widget(fila)
                
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        inp_desc = TextInput(hint_text="Descripción (Ej: Bono)", multiline=False, size_hint_y=None, height=dp(35))
        inp_monto = TextInput(hint_text="Monto extra", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        btn_add = Button(text="[font=NotoEmoji]➕[/font] Registrar Ingreso", markup=True, size_hint_y=None, height=dp(40), font_size='16sp', background_color=(0.1, 0.5, 0.2, 1), color=(1,1,1,1))
        
        def agregar(instance):
            if inp_desc.text and inp_monto.text:
                add_income(self.db_path, inp_desc.text, int(inp_monto.text), datetime.now().isoformat(timespec='seconds'))
                inp_desc.text = ""; inp_monto.text = ""
                recargar_lista()
                self.actualizar_pantalla()
                self.subir_a_la_nube()
                
        btn_add.bind(on_release=agregar)
        form.add_widget(inp_desc); form.add_widget(inp_monto); form.add_widget(btn_add)
        contenido.add_widget(form)
        Popup(title='Ingresos Extra', content=contenido, size_hint=(0.95, 0.8)).open()

    def registrar_gasto(self):
        text = self.root.ids.gasto.text.strip()
        if not text: return
        
        cat_text = self.root.ids.categoria.text
        categoria = cat_text.replace('Categoría: ', '').strip()
        moneda = self.root.ids.moneda.text
        tags = self.root.ids.tag_input.text.strip()
        
        lineas = [line.strip() for line in re.split(r'\n|,', text) if line.strip()]
        total_guardado = 0; gastos_guardados = 0; errores = []
        
        for linea in lineas:
            try:
                result = parse_expense(linea)
                if result:
                    description, amount = result
                    add_expense(self.db_path, description, amount, datetime.now().isoformat(timespec='seconds'), categoria, moneda, tags)
                    if moneda == 'COP':
                        total_guardado += amount
                    gastos_guardados += 1
            except ValueError as exc:
                errores.append(str(exc))
                
        if gastos_guardados > 0:
            self.root.ids.gasto.text = ''
            self.root.ids.tag_input.text = ''
            self.root.ids.estado.text = f'Guardados {gastos_guardados} gastos.'
            self.subir_a_la_nube() 

            limite_cat = get_category_budget(self.db_path, categoria)
            if limite_cat > 0 and moneda == 'COP':
                mes_actual = datetime.now().strftime('%Y-%m')
                gastado_cat = get_total_category_expense(self.db_path, mes_actual, categoria)
                if gastado_cat > limite_cat:
                    self.aviso(f"¡Límite superado en {categoria}!\nLímite: {self.formato(limite_cat)}", "Excedido")
                elif gastado_cat >= limite_cat * 0.9:
                    self.aviso(f"¡Cuidado con {categoria}!\nHas usado el 90% de tu límite.", "Cerca")

            salario = get_user_salary(self.db_path)
            if salario > 0 and total_guardado > 0:
                now = datetime.now()
                total_actual_mes = totals_for_period(self.db_path, now.date().replace(day=1).isoformat(), now.date().isoformat())
                total_ahorrado = get_total_saved(self.db_path)
                ingresos_extra = get_income_for_month(self.db_path, now.strftime('%Y-%m'))
                
                restante = salario + ingresos_extra - total_actual_mes - total_ahorrado
                if restante < 0:
                    self.aviso(f"¡ALERTA DE SOBREGIRO!\nDéficit: {self.formato(abs(restante))}", "Sobregirado")
                elif restante <= (salario * 0.1):
                    self.aviso(f"¡Cuidado!\nSaldo: {self.formato(restante)}", "Límite")
                    
            self.actualizar_meses_spinner()
            self.actualizar_pantalla()
        if errores:
            self.aviso('\n'.join(errores), 'Error')

    def actualizar_pantalla(self):
        if not self.root or 'movimientos' not in self.root.ids: return
        now = datetime.now()
        self.total_hoy = totals_for_period(self.db_path, now.date().isoformat(), now.date().isoformat())
        
        if self.filtro_inicio and self.filtro_fin:
            total_mes_vista = totals_for_period(self.db_path, self.filtro_inicio, self.filtro_fin)
            rows = get_expenses_for_date_range(self.db_path, self.filtro_inicio, self.filtro_fin, self.root.ids.buscar_texto.text)
            self.root.ids.mes_spinner.text = 'Mes Actual'
            self.mes_actual_seleccionado = None
        else:
            if self.mes_actual_seleccionado:
                year_month = self.mes_actual_seleccionado
                total_mes_vista = get_totals_for_month(self.db_path, year_month)
            else:
                year_month = now.strftime('%Y-%m')
                total_mes_vista = totals_for_period(self.db_path, now.date().replace(day=1).isoformat(), now.date().isoformat())
            rows = get_expenses_for_month(self.db_path, year_month, self.root.ids.buscar_texto.text)

        salario = get_user_salary(self.db_path)
        total_ahorrado = get_total_saved(self.db_path)
        ingresos_extra = get_income_for_month(self.db_path, year_month)

        if salario > 0 or ingresos_extra > 0:
            self.altura_salario = dp(60)
            self.opacidad_salario = 1.0
            restante = salario + ingresos_extra - total_mes_vista - total_ahorrado
            if restante < 0:
                self.texto_saldo = f"[b]Saldo: -{self.formato(abs(restante))}[/b]\n(¡Sobregirado!)"
                self.color_saldo = [0.9, 0.2, 0.2, 1]
            elif restante <= ((salario + ingresos_extra) * 0.1):
                self.texto_saldo = f"[b]Saldo: {self.formato(restante)}[/b]\n(¡Cuidado!)"
                self.color_saldo = [0.9, 0.7, 0.1, 1]
            else:
                self.texto_saldo = f"[b]Saldo disp: {self.formato(restante)}[/b]\n(Ingresos Extra: {self.formato(ingresos_extra)})"
                self.color_saldo = [0.06, 0.72, 0.5, 1]
        else:
            self.altura_salario = 0
            self.opacidad_salario = 0.0

        grid = self.root.ids.movimientos
        grid.clear_widgets()
        if not rows:
            grid.add_widget(Label(text='No hay gastos registrados.', size_hint_y=None, height=dp(35), color=(0.58, 0.64, 0.69, 1)))
            return
        
        for row in rows:
            expense_id, created_at, description, amount, category, currency = row[:6]
            tags = row[6] if len(row) > 6 else ""
            
            moneda_str = f" ({currency})" if currency != 'COP' else ""
            tag_str = f" [color=5b9bd5]#{tags}[/color]" if tags else ""
            
            text = f'[{category}] {description}{tag_str} | {self.formato(amount)}{moneda_str}'
            btn = Button(text=text, markup=True, size_hint_y=None, background_normal='', background_color=(0.12, 0.16, 0.22, 1), color=(0.88, 0.92, 0.95, 1), halign='left', valign='middle', padding=(dp(6), 0))
            btn.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
            btn.bind(texture_size=lambda inst, val: setattr(inst, 'height', max(val[1], dp(36))))
            btn.bind(on_release=lambda instance, x=expense_id, d=description, a=amount, c=category, t=tags: self.opciones_gasto(x, d, a, c, t))
            grid.add_widget(btn)

    def opciones_gasto(self, expense_id, desc, amount, cat, tags=""):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text="¿Qué deseas hacer?", halign='center', size_hint_y=None, height=dp(30)))
        botones = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
        
        # AQUI ESTAN LOS BOTONES DE EDITAR Y ELIMINAR
        btn_editar = Button(text="[font=NotoEmoji]📝[/font] Editar", markup=True, font_size='16sp', background_color=(0.1, 0.5, 0.8, 1), color=(1,1,1,1))
        btn_eliminar = Button(text="[font=NotoEmoji]🗑️[/font] Eliminar", markup=True, font_size='16sp', background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1))
        btn_cancelar = Button(text="[font=NotoEmoji]❌[/font] Cancelar", markup=True, font_size='16sp', background_color=(0.3, 0.3, 0.3, 1), color=(1,1,1,1))
        
        botones.add_widget(btn_editar); botones.add_widget(btn_eliminar); botones.add_widget(btn_cancelar)
        contenido.add_widget(botones)
        popup = Popup(title='Opciones', content=contenido, size_hint=(0.9, 0.4))
        popup.open()
        btn_editar.bind(on_release=lambda x: (popup.dismiss(), self.abrir_editar(expense_id, desc, amount, cat, tags)))
        btn_eliminar.bind(on_release=lambda x: (popup.dismiss(), self.preguntar_eliminar(expense_id)))
        btn_cancelar.bind(on_release=popup.dismiss)

    def abrir_editar(self, expense_id, desc, amount, cat, tags=""):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        entrada_texto = TextInput(text=f"{desc} {amount}", multiline=False, size_hint_y=None, height=dp(40))
        inp_tags = TextInput(text=tags, hint_text="Etiqueta (Ej: Cumple)", multiline=False, size_hint_y=None, height=dp(40))
        spinner_cat = Spinner(text=cat, values=tuple(self.lista_categorias), size_hint_y=None, height=dp(40), background_normal='', background_color=(0.3, 0.35, 0.45, 1), color=(1, 1, 1, 1))
        btn_guardar = Button(text="[font=NotoEmoji]💾[/font] Guardar Cambios", markup=True, size_hint_y=None, height=dp(45), font_size='16sp', background_color=(0.06, 0.72, 0.5, 1), color=(1,1,1,1))
        
        contenido.add_widget(Label(text="Editar monto y descripción:"))
        contenido.add_widget(entrada_texto)
        contenido.add_widget(Label(text="Editar Etiqueta:"))
        contenido.add_widget(inp_tags)
        contenido.add_widget(Label(text="Categoría:"))
        contenido.add_widget(spinner_cat)
        contenido.add_widget(btn_guardar)
        
        popup = Popup(title='Editar', content=contenido, size_hint=(0.9, 0.65))
        popup.open()
        
        def guardar(instance):
            try:
                result = parse_expense(entrada_texto.text)
                if result:
                    nueva_desc, nuevo_monto = result
                    update_expense(self.db_path, expense_id, nueva_desc, nuevo_monto, spinner_cat.text, inp_tags.text.strip())
                    popup.dismiss()
                    self.actualizar_pantalla()
                    self.root.ids.estado.text = "Gasto editado."
                    self.subir_a_la_nube() 
            except ValueError as e:
                self.aviso(str(e), "Error")
        btn_guardar.bind(on_release=guardar)

    def preguntar_eliminar(self, expense_id):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text="¿Eliminar este gasto?", halign='center'))
        botones = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
        btn_si = Button(text="[font=NotoEmoji]✔️[/font] Sí", markup=True, font_size='16sp', background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1))
        btn_no = Button(text="[font=NotoEmoji]❌[/font] No", markup=True, font_size='16sp', background_color=(0.3, 0.3, 0.3, 1), color=(1,1,1,1))
        botones.add_widget(btn_si); botones.add_widget(btn_no); contenido.add_widget(botones)
        popup = Popup(title='Eliminar', content=contenido, size_hint=(0.8, 0.3), title_align='center')
        def eliminar(instance):
            delete_expense(self.db_path, expense_id)
            popup.dismiss()
            self.actualizar_pantalla()
            self.root.ids.estado.text = "Gasto eliminado."
            self.subir_a_la_nube()
        btn_si.bind(on_release=eliminar); btn_no.bind(on_release=popup.dismiss)
        popup.open()

    def abrir_gastos_recurrentes(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        scroll = ScrollView(size_hint_y=0.6)
        lista = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
        lista.bind(minimum_height=lista.setter('height'))
        def recargar_lista():
            lista.clear_widgets()
            for r_id, desc, amount, cat, day in get_recurring_expenses(self.db_path):
                fila = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
                lbl = Label(text=f"Día {day}: {desc} - {self.formato(amount)}", halign='left', valign='middle', text_size=(dp(250), None))
                btn_del = Button(text="[font=NotoEmoji]🗑️[/font]", markup=True, size_hint_x=None, width=dp(40), font_size='16sp', background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1))
                btn_del.bind(on_release=lambda instance, x=r_id: (delete_recurring_expense(self.db_path, x), recargar_lista(), self.subir_a_la_nube()))
                fila.add_widget(lbl); fila.add_widget(btn_del); lista.add_widget(fila)
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        inp_desc = TextInput(hint_text="Ej: Netflix", multiline=False, size_hint_y=None, height=dp(35))
        inp_monto = TextInput(hint_text="Monto", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        inp_dia = TextInput(hint_text="Día (1-31)", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        btn_add = Button(text="[font=NotoEmoji]➕[/font] Agregar Fijo", markup=True, size_hint_y=None, height=dp(40), font_size='16sp', background_color=(0.6, 0.4, 0.2, 1), color=(1,1,1,1))
        def agregar(instance):
            if inp_desc.text and inp_monto.text and inp_dia.text:
                add_recurring_expense(self.db_path, inp_desc.text, int(inp_monto.text), "General", int(inp_dia.text))
                inp_desc.text = ""; inp_monto.text = ""; inp_dia.text = ""
                recargar_lista()
                self.subir_a_la_nube()
        btn_add.bind(on_release=agregar)
        form.add_widget(inp_desc); form.add_widget(inp_monto); form.add_widget(inp_dia); form.add_widget(btn_add)
        contenido.add_widget(form)
        Popup(title='Gastos Fijos', content=contenido, size_hint=(0.95, 0.8)).open()

    def abrir_metas_ahorro(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        scroll = ScrollView(size_hint_y=0.6)
        lista = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        lista.bind(minimum_height=lista.setter('height'))
        def recargar_lista():
            lista.clear_widgets()
            for g_id, name, target, saved in get_savings_goals(self.db_path):
                fila = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(70), spacing=dp(2))
                porcentaje = (saved / target) * 100 if target > 0 else 0
                lbl = Label(text=f"{name} ({porcentaje:.0f}%)\nAhorrado: {self.formato(saved)} / {self.formato(target)}", halign='left', valign='middle', size_hint_y=None, height=dp(40), text_size=(dp(250), None))
                botones = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(5))
                inp_abono = TextInput(hint_text="Abonar $", multiline=False, input_filter='int')
                btn_abonar = Button(text="[font=NotoEmoji]➕[/font] Abonar", markup=True, size_hint_x=None, width=dp(80), font_size='14sp', background_color=(0.2, 0.6, 0.6, 1), color=(1,1,1,1))
                btn_del = Button(text="[font=NotoEmoji]🗑️[/font]", markup=True, size_hint_x=None, width=dp(40), font_size='16sp', background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1))
                def abonar(instance, x=g_id, inp=inp_abono):
                    if inp.text:
                        add_to_savings_goal(self.db_path, x, int(inp.text))
                        inp.text = ""; recargar_lista(); self.actualizar_pantalla(); self.subir_a_la_nube()
                def borrar(instance, x=g_id):
                    delete_savings_goal(self.db_path, x); recargar_lista(); self.actualizar_pantalla(); self.subir_a_la_nube()
                btn_abonar.bind(on_release=abonar); btn_del.bind(on_release=borrar)
                botones.add_widget(inp_abono); botones.add_widget(btn_abonar); botones.add_widget(btn_del)
                fila.add_widget(lbl); fila.add_widget(botones); lista.add_widget(fila)
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        inp_nombre = TextInput(hint_text="Nombre meta", multiline=False, size_hint_y=None, height=dp(35))
        inp_meta = TextInput(hint_text="Monto meta", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        btn_add = Button(text="[font=NotoEmoji]➕[/font] Crear Meta", markup=True, size_hint_y=None, height=dp(40), font_size='16sp', background_color=(0.2, 0.6, 0.6, 1), color=(1,1,1,1))
        def agregar(instance):
            if inp_nombre.text and inp_meta.text:
                add_savings_goal(self.db_path, inp_nombre.text, int(inp_meta.text))
                inp_nombre.text = ""; inp_meta.text = ""; recargar_lista(); self.subir_a_la_nube()
        btn_add.bind(on_release=agregar)
        form.add_widget(inp_nombre); form.add_widget(inp_meta); form.add_widget(btn_add)
        contenido.add_widget(form)
        Popup(title='Mis Metas', content=contenido, size_hint=(0.95, 0.8)).open()

    def abrir_deudas(self):
        try:
            contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
            lbl_me_deben = Label(text="[b]Me deben: $0[/b]", markup=True, size_hint_y=None, height=dp(25), color=(0.2, 0.9, 0.5, 1))
            lbl_yo_debo = Label(text="[b]Yo debo: $0[/b]", markup=True, size_hint_y=None, height=dp(25), color=(0.9, 0.3, 0.3, 1))
            contenido.add_widget(lbl_me_deben)
            contenido.add_widget(lbl_yo_debo)
            
            scroll = ScrollView(size_hint_y=0.5)
            lista = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(5))
            lista.bind(minimum_height=lista.setter('height'))
            
            def recargar_lista():
                lista.clear_widgets()
                total_me_deben = get_total_debts(self.db_path, 'me_deben')
                total_yo_debo = get_total_debts(self.db_path, 'yo_debo')
                lbl_me_deben.text = f"[b]Me deben: {self.formato(total_me_deben)}[/b]"
                lbl_yo_debo.text = f"[b]Yo debo: {self.formato(total_yo_debo)}[/b]"
                
                deudas = get_debts(self.db_path, "pending")
                for d_id, person, amount, type_d, desc in deudas:
                    amount = amount if amount is not None else 0
                    person = person if person is not None else "Desconocido"
                    color = (0.2, 0.9, 0.5, 1) if type_d == 'me_deben' else (0.9, 0.3, 0.3, 1)
                    texto = f"{'Te debe' if type_d == 'me_deben' else 'Debes a'}: {person} - {self.formato(amount)}"
                    fila = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(5))
                    lbl = Label(text=texto, color=color, text_size=(dp(180), None))
                    btn_pagar = Button(text="Pagada", size_hint_x=None, width=dp(60), background_color=(0.2, 0.8, 0.5, 1), color=(1,1,1,1), font_size='12sp')
                    btn_del = Button(text="[font=NotoEmoji]🗑️[/font]", markup=True, size_hint_x=None, width=dp(30), font_size='16sp', background_color=(0.8, 0.2, 0.2, 1), color=(1,1,1,1))
                    def hacer_pago(instance, x=d_id):
                        update_debt_status(self.db_path, x, 'paid')
                        recargar_lista()
                        self.actualizar_pantalla()
                        self.subir_a_la_nube()
                    def hacer_borrado(instance, x=d_id):
                        delete_debt(self.db_path, x)
                        recargar_lista()
                        self.actualizar_pantalla()
                        self.subir_a_la_nube()
                    btn_pagar.bind(on_release=hacer_pago)
                    btn_del.bind(on_release=hacer_borrado)
                    fila.add_widget(lbl); fila.add_widget(btn_pagar); fila.add_widget(btn_del)
                    lista.add_widget(fila)
                    
            recargar_lista()
            scroll.add_widget(lista)
            contenido.add_widget(scroll)
            
            form = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(160), spacing=dp(5))
            inp_person = TextInput(hint_text="Nombre", multiline=False, size_hint_y=None, height=dp(35))
            inp_monto = TextInput(hint_text="Monto", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
            botones_tipo = BoxLayout(size_hint_y=None, height=dp(35), spacing=dp(5))
            btn_me_deben = Button(text="Me deben", background_color=(0.2, 0.8, 0.6, 1), color=(1,1,1,1), font_size='12sp')
            btn_yo_debo = Button(text="Yo debo", background_color=(0.4, 0.4, 0.4, 1), color=(1,1,1,1), font_size='12sp')
            tipo_seleccionado = ["me_deben"]
            def set_me_deben(instance):
                tipo_seleccionado[0] = "me_deben"
                btn_me_deben.background_color = (0.2, 0.8, 0.6, 1)
                btn_yo_debo.background_color = (0.4, 0.4, 0.4, 1)
            def set_yo_debo(instance):
                tipo_seleccionado[0] = "yo_debo"
                btn_me_deben.background_color = (0.4, 0.4, 0.4, 1)
                btn_yo_debo.background_color = (0.8, 0.2, 0.2, 1)
            btn_me_deben.bind(on_release=set_me_deben)
            btn_yo_debo.bind(on_release=set_yo_debo)
            botones_tipo.add_widget(btn_me_deben); botones_tipo.add_widget(btn_yo_debo)
            btn_add = Button(text="[font=NotoEmoji]➕[/font] Registrar Deuda", markup=True, size_hint_y=None, height=dp(40), font_size='16sp', background_color=(0.8, 0.5, 0.2, 1), color=(1,1,1,1))
            def agregar(instance):
                p = inp_person.text.strip(); m = inp_monto.text.strip()
                if p and m:
                    add_debt(self.db_path, p, int(m), tipo_seleccionado[0])
                    inp_person.text = ""; inp_monto.text = ""
                    recargar_lista()
                    self.subir_a_la_nube()
            btn_add.bind(on_release=agregar)
            form.add_widget(inp_person); form.add_widget(inp_monto); form.add_widget(botones_tipo); form.add_widget(btn_add)
            contenido.add_widget(form)
            Popup(title='Deudas', content=contenido, size_hint=(0.95, 0.8)).open()
        except Exception as e:
            self.aviso(f"Error Deudas: {e}", "Error")

    def generar_pdf(self):
        try:
            correo_del_usuario = get_user_email(self.db_path)
            if not correo_del_usuario:
                self.aviso("Configura tu correo primero.", "Falta correo")
                return
            path_pdf = os.path.join(self.user_data_dir, f'reporte_{date.today().isoformat()}.pdf')
            path_img = os.path.join(self.user_data_dir, "grafico_temp.png")
            
            path_img_valido = False
            try:
                mes_actual = datetime.now().strftime('%Y-%m')
                datos = get_expenses_by_category_month(self.db_path, mes_actual)
                if datos:
                    img = Image.new('RGB', (400, 400), color='white')
                    draw = ImageDraw.Draw(img)
                    total = sum(d[1] for d in datos)
                    start_angle = 0
                    colores = ['#e74c3c', '#3498db', '#2ecc71', '#f1c40f', '#9b59b6', '#e67e22', '#1abc9c']
                    for i, d in enumerate(datos):
                        angle = (d[1] / total) * 360
                        end_angle = start_angle + angle
                        draw.pieslice([50, 50, 350, 350], start=start_angle, end=end_angle, fill=colores[i % len(colores)])
                        start_angle = end_angle
                    img.save(path_img)
                    path_img_valido = True
            except Exception as e_graf:
                pass

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 18)
            pdf.cell(0, 10, "Reporte Financiero Completo", ln=True, align='C')
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(0, 10, f"Generado el: {date.today().isoformat()}", ln=True, align='C')
            pdf.ln(5)
            
            if path_img_valido and os.path.exists(path_img):
                pdf.image(path_img, x=60, y=35, w=90)
                pdf.ln(90) 
                os.remove(path_img)
            else:
                pdf.ln(10)

            pdf.set_font("Arial", 'B', 14)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(0, 10, "1. Gastos del Mes", ln=True, fill=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(30, 8, "Fecha", 1); pdf.cell(70, 8, "Descripcion", 1); pdf.cell(40, 8, "Categoria", 1); pdf.cell(40, 8, "Monto", 1); pdf.ln()
            pdf.set_font("Arial", '', 10)
            rows = get_expenses_for_month(self.db_path, datetime.now().strftime('%Y-%m'))
            for row in rows:
                _, created_at, desc, amount, cat, curr = row[:6]
                d_clean = desc.encode('latin-1', 'replace').decode('latin-1')
                c_clean = cat.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(30, 8, created_at[:10], 1); pdf.cell(70, 8, d_clean[:30], 1); pdf.cell(40, 8, c_clean, 1); pdf.cell(40, 8, f"{self.formato(amount)} {curr}", 1); pdf.ln()
            pdf.ln(5)

            if pdf.get_y() > 230: pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "2. Gastos Fijos Programados", ln=True, fill=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 8, "Descripcion", 1); pdf.cell(40, 8, "Monto", 1); pdf.cell(40, 8, "Dia de Cobro", 1); pdf.ln()
            pdf.set_font("Arial", '', 10)
            fijos = get_recurring_expenses(self.db_path)
            if fijos:
                for f in fijos:
                    d_clean = f[1].encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(100, 8, d_clean[:40], 1); pdf.cell(40, 8, self.formato(f[2]), 1); pdf.cell(40, 8, f"Día {f[4]}", 1); pdf.ln()
            else:
                pdf.cell(0, 8, "No hay gastos fijos registrados.", ln=True)
            pdf.ln(5)

            if pdf.get_y() > 230: pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "3. Ingresos Extra", ln=True, fill=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 8, "Descripcion", 1); pdf.cell(40, 8, "Monto", 1); pdf.cell(40, 8, "Fecha", 1); pdf.ln()
            pdf.set_font("Arial", '', 10)
            ingresos = get_all_incomes_month(self.db_path, datetime.now().strftime('%Y-%m'))
            if ingresos:
                for i in ingresos:
                    d_clean = i[1].encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(100, 8, d_clean[:40], 1); pdf.cell(40, 8, self.formato(i[2]), 1); pdf.cell(40, 8, i[3][:10], 1); pdf.ln()
            else:
                pdf.cell(0, 8, "No hay ingresos extra este mes.", ln=True)
            pdf.ln(5)

            if pdf.get_y() > 230: pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "4. Presupuestos", ln=True, fill=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 8, "Categoria", 1); pdf.cell(40, 8, "Limite", 1); pdf.ln()
            pdf.set_font("Arial", '', 10)
            presupuestos = get_all_category_budgets(self.db_path)
            if presupuestos:
                for p in presupuestos:
                    c_clean = p[0].encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(100, 8, c_clean, 1); pdf.cell(40, 8, self.formato(p[1]), 1); pdf.ln()
            else:
                pdf.cell(0, 8, "No hay presupuestos definidos.", ln=True)
            pdf.ln(5)

            if pdf.get_y() > 230: pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "5. Metas de Ahorro", ln=True, fill=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 8, "Nombre", 1); pdf.cell(40, 8, "Meta", 1); pdf.cell(40, 8, "Ahorrado", 1); pdf.ln()
            pdf.set_font("Arial", '', 10)
            metas = get_savings_goals(self.db_path)
            if metas:
                for m in metas:
                    n_clean = m[1].encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(100, 8, n_clean[:40], 1); pdf.cell(40, 8, self.formato(m[2]), 1); pdf.cell(40, 8, self.formato(m[3]), 1); pdf.ln()
            else:
                pdf.cell(0, 8, "No hay metas de ahorro.", ln=True)
            pdf.ln(5)

            if pdf.get_y() > 230: pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "6. Deudas Pendientes", ln=True, fill=True)
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(80, 8, "Persona", 1); pdf.cell(40, 8, "Monto", 1); pdf.cell(60, 8, "Tipo", 1); pdf.ln()
            pdf.set_font("Arial", '', 10)
            deudas = get_debts(self.db_path, "pending")
            if deudas:
                for d in deudas:
                    p_clean = d[1].encode('latin-1', 'replace').decode('latin-1')
                    t_clean = d[3].encode('latin-1', 'replace').decode('latin-1')
                    pdf.cell(80, 8, p_clean[:30], 1); pdf.cell(40, 8, self.formato(d[2]), 1); pdf.cell(60, 8, "Me deben" if t_clean == 'me_deben' else "Yo debo", 1); pdf.ln()
            else:
                pdf.cell(0, 8, "No hay deudas pendientes.", ln=True)

            pdf.output(path_pdf)
            self.aviso("Generando PDF y enviando...", "Procesando")
            threading.Thread(target=self._enviar_archivo_resend, args=(correo_del_usuario, path_pdf, "Reporte PDF")).start()
        except Exception as e:
            self.aviso(f"Error al generar PDF: {e}", "Error")

    def generar_respaldo(self):
        correo_del_usuario = get_user_email(self.db_path)
        if not correo_del_usuario:
            self.aviso("Configura tu correo primero.", "Falta correo")
            return
        self.aviso("Preparando respaldo...", "Procesando")
        threading.Thread(target=self._enviar_archivo_resend, args=(correo_del_usuario, self.db_path, "Copia de Seguridad")).start()

    def generar_excel(self):
        try:
            correo_del_usuario = get_user_email(self.db_path)
            if not correo_del_usuario:
                self.aviso("Configura tu correo primero.", "Falta correo")
                return
            if export_excel is None:
                self.aviso("La librería de Excel no cargó.", "Error interno")
                return
            path_xlsx = os.path.join(self.user_data_dir, f'gastos_{date.today().isoformat()}.xlsx')
            export_excel(self.db_path, path_xlsx)
            self.aviso("Generando Excel y enviando...", "Procesando")
            threading.Thread(target=self._enviar_archivo_resend, args=(correo_del_usuario, path_xlsx, "Reporte Excel")).start()
        except Exception as exc:
            self.aviso(f'Error al generar Excel: {exc}', 'Error')

    def _enviar_archivo_resend(self, correo_del_usuario, path, tipo_reporte):
        try:
            with open(path, "rb") as f:
                contenido_base64 = base64.b64encode(f.read()).decode('utf-8')
            headers = {"Authorization": f"Bearer {TU_API_KEY}", "Content-Type": "application/json"}
            data = {
                "from": f"Mi App de Gastos <{CORREO_REMITENTE}>",
                "to": [correo_del_usuario],
                "subject": f"{tipo_reporte} - {date.today().isoformat()}",
                "html": f"<p>Hola, adjunto encontrarás tu {tipo_reporte}.</p>",
                "attachments": [{"filename": os.path.basename(path), "content": contenido_base64}]
            }
            response = requests.post("https://api.resend.com/emails", headers=headers, json=data, timeout=30)
            if response.status_code in (200, 201):
                Clock.schedule_once(lambda dt: self.aviso(f"¡{tipo_reporte} enviado!", "¡Éxito!"), 0)
            else:
                Clock.schedule_once(lambda dt: self.aviso(f"Error: {response.text}", "Error"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.aviso(f"Error al enviar: {e}", "Error"), 0)

if __name__ == '__main__':
    GastosApp().run()
