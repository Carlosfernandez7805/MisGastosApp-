from datetime import datetime, date
import os
import re
import threading
import base64
import math
import random
import traceback

# =========================================================================
# LOG DE INICIO (Escribe en Descargas para que puedas verlo si falla)
# =========================================================================
try:
    ruta_log_inicio = "/storage/emulated/0/Download/estado_inicio.txt"
    with open(ruta_log_inicio, "w") as f:
        f.write("Iniciando la app...\n")
except Exception as e:
    pass # Si falla el log, seguimos
# =========================================================================

try:
    import requests
except:
    pass

try:
    from fpdf import FPDF
except Exception as e:
    with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write(f"Error importando FPDF: {e}\n")

try:
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE, Permission.MANAGE_EXTERNAL_STORAGE])
    with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write("Permisos de Android OK.\n")
except Exception as e:
    with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write(f"Error pidiendo permisos: {e}\n")

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
from kivy.uix.image import Image
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

# ... (Aquí van tus imports de database y excel igual que antes) ...
from database import (
    init_db, add_expense, totals_for_period, delete_expense, update_expense,
    get_available_months, get_totals_for_month, get_expenses_for_month, get_expenses_by_category_month, get_expenses_for_date_range,
    add_recurring_expense, get_recurring_expenses, delete_recurring_expense, process_recurring_expenses,
    add_savings_goal, get_savings_goals, add_to_savings_goal, delete_savings_goal, get_total_saved,
    add_debt, get_debts, update_debt_status, delete_debt, get_total_debts,
    add_income, get_income_for_month, get_all_incomes_month, delete_income,
    save_category_budget, get_category_budget, get_all_category_budgets, get_total_category_expense,
    save_user_email, get_user_email, save_user_salary, get_user_salary, save_user_pin, get_user_pin,
    save_tutorial_shown, get_tutorial_shown
)
from excel import export_excel

ruta_de_tu_app = os.path.dirname(os.path.abspath(__file__))
resource_add_path(ruta_de_tu_app)

TU_API_KEY = "re_TU_CLAVE_AQUI"
CORREO_REMITENTE = "reportes@tusgastosapp.lat"

ruta_fuente = os.path.join(ruta_de_tu_app, "fa-solid-900.ttf")
try:
    LabelBase.register(name="FontAwesome", fn_regular=ruta_fuente)
except Exception as e:
    with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write(f"Error cargando fuente: {e}\n")

# ... EL BLOQUE KV SE MANTIENE EXACTAMENTE IGUAL ...
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
        Button:
            text: '[font=FontAwesome]\\uf023[/font]'
            markup: True
            size_hint_x: None
            width: dp(40)
            font_size: '16sp'
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
            text: '[font=FontAwesome]\\uf555[/font]'
            markup: True
            size_hint_x: None
            width: dp(40)
            font_size: '16sp'
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
            text: '[font=FontAwesome]\\uf0e0[/font]'
            markup: True
            size_hint_x: None
            width: dp(40)
            font_size: '16sp'
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
            height: dp(25)
            spacing: dp(5)
            Spinner:
                id: categoria
                text: 'Categoría: General'
                values: ('General', 'Comida', 'Transporte', 'Servicios', 'Salud', 'Ocio', 'Otros')
                background_normal: ''
                background_color: (0.3, 0.35, 0.45, 1)
                color: (1, 1, 1, 1)
                on_text: self.text = 'Categoría: ' + self.text if not self.text.startswith('Categoría:') else self.text
            Spinner:
                id: moneda
                text: 'COP'
                values: ('COP', 'USD', 'EUR')
                size_hint_x: 0.3
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
                hint_text: 'Escribe o usa el micrófono...'
                hint_text_color: (0.5, 0.5, 0.5, 1)
                multiline: True
                background_normal: ''
                background_color: (1, 1, 1, 1)
                foreground_color: (0.06, 0.09, 0.16, 1)
                padding: dp(8)
            Button:
                text: '[font=FontAwesome]\\uf130[/font]'
                markup: True
                size_hint_x: None
                width: dp(50)
                font_size: '20sp'
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
        text: 'GUARDAR GASTOS'
        size_hint_y: None
        height: dp(48)
        background_normal: ''
        background_color: 0, 0, 0, 0
        bold: True
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
                text: 'Calendario'
                font_size: '12sp'
                background_normal: ''
                background_color: (0.2, 0.4, 0.6, 1)
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
        height: dp(70)
        spacing: dp(5)
        Button:
            text: 'Fijos'
            font_size: '11sp'
            background_normal: ''
            background_color: (0.6, 0.4, 0.2, 1)
            on_release: app.abrir_gastos_recurrentes()
        Button:
            text: 'Metas'
            font_size: '11sp'
            background_normal: ''
            background_color: (0.2, 0.6, 0.6, 1)
            on_release: app.abrir_metas_ahorro()
        Button:
            text: 'Deudas'
            font_size: '11sp'
            background_normal: ''
            background_color: (0.8, 0.4, 0.1, 1)
            on_release: app.abrir_deudas()
        Button:
            text: 'Ingresos'
            font_size: '11sp'
            background_normal: ''
            background_color: (0.1, 0.5, 0.2, 1)
            on_release: app.abrir_ingresos()
        Button:
            text: 'Presupuesto'
            font_size: '11sp'
            background_normal: ''
            background_color: (0.6, 0.2, 0.4, 1)
            on_release: app.abrir_presupuestos()
        Button:
            text: 'Gráfico'
            font_size: '11sp'
            background_normal: ''
            background_color: (0.6, 0.3, 0.8, 1)
            on_release: app.mostrar_grafico()
    BoxLayout:
        size_hint_y: None
        height: dp(35)
        spacing: dp(5)
        TextInput:
            id: buscar_texto
            hint_text: 'Buscar movimientos...'
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
    GridLayout:
        cols: 3
        size_hint_y: None
        height: dp(45)
        spacing: dp(5)
        Button:
            text: '[font=FontAwesome]\\uf0e0[/font] EXCEL'
            markup: True
            background_normal: ''
            background_color: (0.1, 0.5, 0.8, 1)
            on_release: app.generar_excel()
        Button:
            text: '[font=FontAwesome]\\uf1c1[/font] PDF'
            markup: True
            background_normal: ''
            background_color: (0.8, 0.2, 0.2, 1)
            on_release: app.generar_pdf()
        Button:
            text: '[font=FontAwesome]\\uf0c7[/font] BACKUP'
            markup: True
            background_normal: ''
            background_color: (0.3, 0.35, 0.45, 1)
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
    _stt_clock = None
    mes_actual_seleccionado = None
    filtro_inicio = None
    filtro_fin = None
    codigo_otp = None
    otp_solicitado = False

    def build(self):
        self.title = 'Mi Control de Gastos'
        self.db_path = os.path.join(self.user_data_dir, 'gastos.db')
        
        try:
            with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write("En build()...\n")
            init_db(self.db_path)
            with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write("Base de datos OK.\n")
            
            # Intentar cargar la pantalla
            root = Builder.load_string(KV)
            with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write("Pantalla KV cargada OK.\n")
            return root
        except Exception as e:
            error_completo = traceback.format_exc()
            with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: 
                f.write(f"ERROR CRITICO EN BUILD:\n{error_completo}\n")
            return Label(text=f"Error Crítico:\n{e}")

    def on_start(self):
        try:
            with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write("En on_start()...\n")
            if not self.verificar_pin(): return
            
            if not get_tutorial_shown(self.db_path):
                self.mostrar_bienvenida()
                save_tutorial_shown(self.db_path)
                
            alertas = process_recurring_expenses(self.db_path)
            if alertas:
                mensaje = "\n".join(alertas)
                Clock.schedule_once(lambda dt: self.aviso(f"🔔 RECORDATORIOS:\n\n{mensaje}", "Próximos cobros"), 2)
            self.actualizar_meses_spinner()
            self.actualizar_pantalla()
            with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: f.write("on_start OK.\n")
        except Exception as e:
            error_completo = traceback.format_exc()
            with open("/storage/emulated/0/Download/estado_inicio.txt", "a") as f: 
                f.write(f"ERROR CRITICO EN ON_START:\n{error_completo}\n")
            self.aviso(f"Error al iniciar la app:\n{str(e)}", "Error Crítico")

    # ... (El resto de las funciones del código anterior van aquí abajo sin cambios) ...
    # Por espacio, asumo que tienes las funciones de mostrar_bienvenida, verificar_pin, etc.
