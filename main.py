from datetime import datetime, date
import os
import re
import threading
import base64
import math
import random
import traceback
import time

def escribir_log(mensaje):
    try:
        ruta_log = "/storage/emulated/0/Download/estado_inicio.txt"
        with open(ruta_log, "a") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {mensaje}\n")
    except:
        pass

escribir_log("--- INICIANDO APP ---")

try:
    import requests
    escribir_log("Librería requests OK")
except Exception as e:
    escribir_log(f"Error requests: {e}")

try:
    from fpdf import FPDF
    escribir_log("Librería fpdf OK")
except Exception as e:
    escribir_log(f"Error fpdf: {e}")

try:
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.INTERNET, 
        Permission.WRITE_EXTERNAL_STORAGE, 
        Permission.READ_EXTERNAL_STORAGE, 
        "android.permission.MANAGE_EXTERNAL_STORAGE"
    ])
    escribir_log("Permisos Android solicitados OK")
except Exception as e:
    escribir_log(f"Error permisos Android: {e}")

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

export_excel = None
try:
    from excel import export_excel
    escribir_log("Imports de excel OK")
except Exception as e:
    escribir_log(f"ERROR CRÍTICO EN EXCEL:\n{traceback.format_exc()}")

ruta_de_tu_app = os.path.dirname(os.path.abspath(__file__))
resource_add_path(ruta_de_tu_app)

# =========================================================================
# 👇 VARIABLES QUE GITHUB REEMPLAZARÁ CON TUS CLAVES REALES 👇
# =========================================================================
TU_API_KEY = "re_TU_CLAVE_AQUI" # Clave de Resend
CORREO_REMITENTE = "reportes@tusgastosapp.lat"

TU_CLAVE_GEMINI_AQUI = "TU_CLAVE_GEMINI_AQUI" # Clave de Google Gemini
# =========================================================================

try:
    ruta_fuente = os.path.join(ruta_de_tu_app, "fa-solid-900.ttf")
    LabelBase.register(name="FontAwesome", fn_regular=ruta_fuente)
except Exception as e:
    pass

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
            
    Button:
        text: '[font=FontAwesome]\\uf544[/font] PREGUNTAR A LA IA'
        markup: True
        size_hint_y: None
        height: dp(45)
        background_normal: ''
        background_color: (0.5, 0.2, 0.8, 1)
        bold: True
        on_release: app.abrir_chat_ia()
        
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
            init_db(self.db_path)
            return Builder.load_string(KV)
        except Exception as e:
            return Label(text=f"Error Crítico:\n{e}")

    def on_start(self):
        Clock.schedule_once(self.iniciar_app, 0.5)

    def iniciar_app(self, dt):
        try:
            if not self.verificar_pin(): return
            if not get_tutorial_shown(self.db_path):
                self.mostrar_bienvenida()
                save_tutorial_shown(self.db_path)
            self.actualizar_meses_spinner()
            self.actualizar_pantalla()
        except Exception as e:
            self.aviso(f"Error al iniciar:\n{str(e)}", "Error Crítico")

    # =========================================================================
    # CHAT CON LA IA (GEMINI)
    # =========================================================================
    def abrir_chat_ia(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # 👇 Icono del robot seguro DENTRO de la ventana, no en el título 👇
        lbl_titulo = Label(text="[font=FontAwesome]\\uf544[/font] Asesor Financiero IA", markup=True, size_hint_y=None, height=dp(30), color=(0.5, 0.2, 0.8, 1), font_size='18sp')
        contenido.add_widget(lbl_titulo)
        
        scroll = ScrollView(size_hint_y=0.7)
        lbl_respuesta = Label(text="Hola, soy tu asesor financiero. ¿En qué te puedo ayudar hoy?", 
                              halign='left', valign='top', size_hint_y=None, color=(1,1,1,1))
        lbl_respuesta.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
        lbl_respuesta.bind(texture_size=lambda inst, val: setattr(inst, 'height', val[1]))
        scroll.add_widget(lbl_respuesta)
        
        input_pregunta = TextInput(
            hint_text="Ej: ¿Cómo puedo ahorrar este mes?",
            multiline=False,
            size_hint_y=None,
            height=dp(45),
            background_normal='',
            background_color=(1, 1, 1, 1),
            foreground_color=(0, 0, 0, 1),
            padding=dp(8)
        )
        
        btn_enviar = Button(text="Enviar a la IA", size_hint_y=None, height=dp(45), background_color=(0.5, 0.2, 0.8, 1), bold=True)
        
        contenido.add_widget(scroll)
        contenido.add_widget(input_pregunta)
        contenido.add_widget(btn_enviar)
        
        # Título del Popup normal, sin modificar propiedades privadas
        popup = Popup(title='Asesor Financiero', content=contenido, size_hint=(0.95, 0.8))
        popup.open()
        
        def enviar(instance):
            pregunta = input_pregunta.text.strip()
            if not pregunta: return
            
            lbl_respuesta.text = "Pensando..."
            input_pregunta.text = ""
            
            # Evitar que el usuario haga clic múltiples veces
            btn_enviar.disabled = True
            btn_enviar.text = "Consultando..."
            
            threading.Thread(target=self.consultar_ia, args=(pregunta, lbl_respuesta, btn_enviar)).start()
            
        btn_enviar.bind(on_release=enviar)

    def consultar_ia(self, pregunta, label_respuesta, btn_enviar):
        try:
            mes_actual = datetime.now().strftime('%Y-%m')
            gastos = get_expenses_for_month(self.db_path, mes_actual)
            
            resumen = ""
            for _, _, desc, amount, cat, _ in gastos:
                resumen += f"- {desc} ({cat}): ${amount}\n"
                
            if not resumen:
                resumen = "El usuario no tiene gastos registrados este mes."

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={TU_CLAVE_GEMINI_AQUI}"
            
            prompt = f"""Eres un asesor financiero experto y amigable. 
            El usuario te hace esta pregunta: "{pregunta}".
            Aquí está el resumen de los gastos del usuario este mes:
            {resumen}
            
            Responde de forma concisa, práctica y motivadora en español. Máximo 3 párrafos."""
            
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{
                    "parts":[{"text": prompt}]
                }]
            }
            
            # Petición con timeout un poco más corto para evitar bloqueos
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            if response.status_code == 200:
                json_resp = response.json()
                # Verificación segura de la estructura de respuesta
                if 'candidates' in json_resp and len(json_resp['candidates']) > 0:
                    texto_ia = json_resp['candidates'][0]['content']['parts'][0]['text']
                    Clock.schedule_once(lambda dt: setattr(label_respuesta, 'text', texto_ia), 0)
                else:
                    Clock.schedule_once(lambda dt: setattr(label_respuesta, 'text', "La IA no devolvió una respuesta válida."), 0)
            elif response.status_code == 503:
                Clock.schedule_once(lambda dt: setattr(label_respuesta, 'text', "El servidor de Google está saturado. Por favor, intenta de nuevo en unos minutos."), 0)
            else:
                error_msg = f"Error de Google (Código {response.status_code}). Revisa tu conexión."
                Clock.schedule_once(lambda dt: setattr(label_respuesta, 'text', error_msg), 0)
                
        except Exception as e:
            error_msg = f"Error de conexión: {str(e)}"
            Clock.schedule_once(lambda dt: setattr(label_respuesta, 'text', error_msg), 0)
        finally:
            # Volver a habilitar el botón pase lo que pase
            Clock.schedule_once(lambda dt: (setattr(btn_enviar, 'disabled', False), setattr(btn_enviar, 'text', "Enviar a la IA")), 0)
    # =========================================================================

    def mostrar_bienvenida(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        logo_img = Image(source='logo.png', size_hint_y=0.35, fit_mode='contain')
        contenido.add_widget(logo_img)
        texto = """
        [b]¡Bienvenido a Gestión de Gastos![/b]
        
        1. Configura tu [b]Correo[/b] y tu [b]Salario[/b].
        2. Escribe tu gasto abajo y dale [b]GUARDAR[/b].
        3. Usa el botón morado para hablar con la [b]IA[/b].
        
        ¡Empieza a controlar tus finanzas hoy!
        """
        lbl = Label(text=texto, markup=True, halign='center', valign='middle', size_hint_y=0.5)
        lbl.bind(size=lambda inst, val: setattr(inst, 'text_size', val))
        contenido.add_widget(lbl)
        btn_ok = Button(text="¡Empezar!", size_hint_y=None, height=dp(50), background_color=(0.06, 0.72, 0.5, 1), bold=True)
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
        btn_entrar = Button(text="Desbloquear", size_hint_y=None, height=dp(45), background_color=(0.06, 0.72, 0.5, 1))
        btn_olvido = Button(text="¿Olvidaste tu PIN?", size_hint_y=None, height=dp(30), background_normal='', background_color=(0.3, 0.3, 0.3, 1))
        contenido.add_widget(Label(text="Ingresa tu PIN:", halign='center'))
        contenido.add_widget(inp_pin)
        contenido.add_widget(btn_entrar)
        contenido.add_widget(btn_olvido)
        
        if self.otp_solicitado:
            btn_ingresar_otp = Button(text="Ya tengo el código", size_hint_y=None, height=dp(35), background_normal='', background_color=(0.1, 0.5, 0.8, 1))
            contenido.add_widget(btn_ingresar_otp)
            btn_ingresar_otp.bind(on_release=lambda x: (popup.dismiss(), self.ingresar_codigo_otp()))
        
        popup = Popup(title='🔒 App Bloqueada', content=contenido, size_hint=(0.8, 0.55), auto_dismiss=False)
        def desbloquear(instance):
            if inp_pin.text == pin_guardado:
                self.acceso_concedido = True
                self.otp_solicitado = False
                self.codigo_otp = None
                popup.dismiss()
                self.actualizar_meses_spinner()
                self.actualizar_pantalla()
            else:
                inp_pin.text = ""
                self.aviso("PIN incorrecto", "Error")
        def recuperar(instance):
            popup.dismiss()
            self.solicitar_correo_recuperacion()
        btn_entrar.bind(on_release=desbloquear)
        btn_olvido.bind(on_release=recuperar)
        popup.open()
        return False

    def solicitar_correo_recuperacion(self):
        correo_registrado = get_user_email(self.db_path)
        if not correo_registrado:
            self.aviso("No has configurado un correo.", "Sin correo")
            return
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        inp_correo = TextInput(hint_text="Ingresa tu correo registrado", multiline=False, size_hint_y=None, height=dp(40))
        btn_validar = Button(text="Enviar Código", size_hint_y=None, height=dp(45), background_color=(0.1, 0.5, 0.8, 1))
        contenido.add_widget(Label(text="Escribe tu correo para recibir un código:", size_hint_y=None, height=dp(40)))
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
        btn_validar = Button(text="Verificar", size_hint_y=None, height=dp(45), background_color=(0.1, 0.5, 0.8, 1))
        contenido.add_widget(Label(text="Ingresa el código de 6 dígitos:", size_hint_y=None, height=dp(40)))
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
        btn_guardar = Button(text="Guardar Nuevo PIN", size_hint_y=None, height=dp(45), background_color=(0.06, 0.72, 0.5, 1))
        contenido.add_widget(Label(text="Ingresa tu nuevo PIN:", size_hint_y=None, height=dp(20)))
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
            html_content = f"<h2>Recuperación de PIN</h2><p>Tu código es:</p><h1 style='color: #1e88e5; font-size: 32px;'>{codigo}</h1>"
            data = {"from": f"Seguridad App <{CORREO_REMITENTE}>", "to": [correo_destino], "subject": "Código de Seguridad", "html": html_content}
            requests.post("https://api.resend.com/emails", headers=headers, json=data, timeout=30)
        except Exception as e:
            print(f"Error al enviar OTP: {e}")

    def configurar_pin(self):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        pin_actual = get_user_pin(self.db_path)
        inp_pin = TextInput(text=pin_actual if pin_actual else "", hint_text="Nuevo PIN (vacío para quitar)", password=True, input_filter='int', multiline=False, size_hint_y=None, height=dp(40))
        btn_guardar = Button(text="Guardar PIN", size_hint_y=None, height=dp(45), background_color=(0.06, 0.72, 0.5, 1))
        contenido.add_widget(Label(text="Configurar PIN:", size_hint_y=None, height=dp(20)))
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
        btn_guardar = Button(text="Guardar Correo", size_hint_y=None, height=dp(45), background_color=(0.06, 0.72, 0.5, 1))
        contenido.add_widget(Label(text="Correo para reportes y PIN:", size_hint_y=None, height=dp(30)))
        contenido.add_widget(entrada_correo)
        contenido.add_widget(btn_guardar)
        popup = Popup(title='Mi Correo', content=contenido, size_hint=(0.9, 0.4))
        def guardar(instance):
            nuevo_correo = entrada_correo.text.strip()
            if "@" in nuevo_correo:
                save_user_email(self.db_path, nuevo_correo)
                self.aviso("¡Correo guardado!", "Éxito")
                popup.dismiss()
            else:
                self.aviso("Ingresa un correo válido.", "Error")
        btn_guardar.bind(on_release=guardar)
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
        btn_aplicar = Button(text="Aplicar Filtro", background_color=(0.2, 0.4, 0.6, 1))
        btn_borrar = Button(text="Quitar Filtro", background_color=(0.8, 0.2, 0.2, 1))
        botones.add_widget(btn_aplicar)
        botones.add_widget(btn_borrar)
        
        contenido.add_widget(Label(text="Desde:", size_hint_y=None, height=dp(20), halign='left'))
        contenido.add_widget(row_inicio)
        contenido.add_widget(Label(text="Hasta:", size_hint_y=None, height=dp(20), halign='left'))
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
            from plyer import stt
            self.root.ids.estado.text = "Escuchando..."
            stt.start()
            if self._stt_clock: self._stt_clock.cancel()
            self._stt_clock = Clock.schedule_interval(self._revisar_resultado_voz, 0.5)
        except Exception as e:
            self.aviso(f"Error de micrófono: {e}", "Error")

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
        btn_guardar = Button(text="Guardar Salario", size_hint_y=None, height=dp(45), background_color=(0.06, 0.72, 0.5, 1))
        contenido.add_widget(Label(text="Tu salario mensual:", size_hint_y=None, height=dp(30)))
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
                texto = f"{cat}: Límite {self.formato(monto_limite)} | Gastado {self.formato(gastado)}"
                color = (0.9, 0.3, 0.3, 1) if gastado > monto_limite else (0.2, 0.9, 0.5, 1)
                lbl = Label(text=texto, halign='left', valign='middle', size_hint_y=None, height=dp(30), color=color, text_size=(dp(250), None))
                lista.add_widget(lbl)
                
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        spinner_cat = Spinner(text='General', values=('General', 'Comida', 'Transporte', 'Servicios', 'Salud', 'Ocio', 'Otros'), size_hint_y=None, height=dp(35), background_normal='', background_color=(0.3, 0.35, 0.45, 1))
        inp_monto = TextInput(hint_text="Límite (Ej: 500000)", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        btn_add = Button(text="Establecer Límite", size_hint_y=None, height=dp(40), background_color=(0.6, 0.2, 0.4, 1))
        
        def agregar(instance):
            if inp_monto.text:
                save_category_budget(self.db_path, spinner_cat.text, int(inp_monto.text))
                inp_monto.text = ""
                recargar_lista()
                
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
                btn_del = Button(text="X", size_hint_x=None, width=dp(40), background_color=(0.8, 0.2, 0.2, 1))
                btn_del.bind(on_release=lambda instance, x=i_id: (delete_income(self.db_path, x), recargar_lista(), self.actualizar_pantalla()))
                fila.add_widget(lbl); fila.add_widget(btn_del); lista.add_widget(fila)
                
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        inp_desc = TextInput(hint_text="Descripción (Ej: Bono)", multiline=False, size_hint_y=None, height=dp(35))
        inp_monto = TextInput(hint_text="Monto extra", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        btn_add = Button(text="Registrar Ingreso", size_hint_y=None, height=dp(40), background_color=(0.1, 0.5, 0.2, 1))
        
        def agregar(instance):
            if inp_desc.text and inp_monto.text:
                add_income(self.db_path, inp_desc.text, int(inp_monto.text), datetime.now().isoformat(timespec='seconds'))
                inp_desc.text = ""; inp_monto.text = ""
                recargar_lista()
                self.actualizar_pantalla()
                
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
        
        lineas = [line.strip() for line in re.split(r'\n|,', text) if line.strip()]
        total_guardado = 0; gastos_guardados = 0; errores = []
        for linea in lineas:
            try:
                result = parse_expense(linea)
                if result:
                    description, amount = result
                    add_expense(self.db_path, description, amount, datetime.now().isoformat(timespec='seconds'), categoria, moneda)
                    if moneda == 'COP':
                        total_guardado += amount
                    gastos_guardados += 1
            except ValueError as exc:
                errores.append(str(exc))
                
        if gastos_guardados > 0:
            self.root.ids.gasto.text = ''
            self.root.ids.estado.text = f'Guardados {gastos_guardados} gastos.'
            
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
        
        for expense_id, created_at, description, amount, category, currency in rows:
            moneda_str = f" ({currency})" if currency != 'COP' else ""
            text = f'[{category}]  {created_at[:16].replace("T", " ")}  |  {description}  |  {self.formato(amount)}{moneda_str}'
            btn = Button(text=text, size_hint_y=None, background_normal='', background_color=(0.12, 0.16, 0.22, 1), color=(0.88, 0.92, 0.95, 1), halign='left', valign='middle', padding=(dp(6), 0))
            btn.bind(width=lambda inst, val: setattr(inst, 'text_size', (val, None)))
            btn.bind(texture_size=lambda inst, val: setattr(inst, 'height', max(val[1], dp(36))))
            btn.bind(on_release=lambda instance, x=expense_id, d=description, a=amount, c=category: self.opciones_gasto(x, d, a, c))
            grid.add_widget(btn)

    def opciones_gasto(self, expense_id, desc, amount, cat):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text="¿Qué deseas hacer?", halign='center', size_hint_y=None, height=dp(30)))
        botones = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
        btn_editar = Button(text="Editar", background_color=(0.1, 0.5, 0.8, 1))
        btn_eliminar = Button(text="Eliminar", background_color=(0.8, 0.2, 0.2, 1))
        btn_cancelar = Button(text="Cancelar", background_color=(0.3, 0.3, 0.3, 1))
        botones.add_widget(btn_editar); botones.add_widget(btn_eliminar); botones.add_widget(btn_cancelar)
        contenido.add_widget(botones)
        popup = Popup(title='Opciones', content=contenido, size_hint=(0.9, 0.4))
        popup.open()
        btn_editar.bind(on_release=lambda x: (popup.dismiss(), self.abrir_editar(expense_id, desc, amount, cat)))
        btn_eliminar.bind(on_release=lambda x: (popup.dismiss(), self.preguntar_eliminar(expense_id)))
        btn_cancelar.bind(on_release=popup.dismiss)

    def abrir_editar(self, expense_id, desc, amount, cat):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        entrada_texto = TextInput(text=f"{desc} {amount}", multiline=False, size_hint_y=None, height=dp(40))
        spinner_cat = Spinner(text=cat, values=('General', 'Comida', 'Transporte', 'Servicios', 'Salud', 'Ocio', 'Otros'), size_hint_y=None, height=dp(40), background_normal='', background_color=(0.3, 0.35, 0.45, 1), color=(1, 1, 1, 1))
        btn_guardar = Button(text="Guardar Cambios", size_hint_y=None, height=dp(45), background_color=(0.06, 0.72, 0.5, 1))
        contenido.add_widget(Label(text="Editar monto y descripción:", size_hint_y=None, height=dp(20)))
        contenido.add_widget(entrada_texto); contenido.add_widget(Label(text="Categoría:", size_hint_y=None, height=dp(20))); contenido.add_widget(spinner_cat); contenido.add_widget(btn_guardar)
        popup = Popup(title='Editar', content=contenido, size_hint=(0.9, 0.6))
        popup.open()
        def guardar(instance):
            try:
                result = parse_expense(entrada_texto.text)
                if result:
                    nueva_desc, nuevo_monto = result
                    update_expense(self.db_path, expense_id, nueva_desc, nuevo_monto, spinner_cat.text)
                    popup.dismiss()
                    self.actualizar_pantalla()
                    self.root.ids.estado.text = "Gasto editado."
            except ValueError as e:
                self.aviso(str(e), "Error")
        btn_guardar.bind(on_release=guardar)

    def preguntar_eliminar(self, expense_id):
        contenido = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        contenido.add_widget(Label(text="¿Eliminar este gasto?", halign='center'))
        botones = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(10))
        btn_si = Button(text="Sí", background_color=(0.8, 0.2, 0.2, 1))
        btn_no = Button(text="No", background_color=(0.3, 0.3, 0.3, 1))
        botones.add_widget(btn_si); botones.add_widget(btn_no); contenido.add_widget(botones)
        popup = Popup(title='Eliminar', content=contenido, size_hint=(0.8, 0.3), title_align='center')
        def eliminar(instance):
            delete_expense(self.db_path, expense_id)
            popup.dismiss()
            self.actualizar_pantalla()
            self.root.ids.estado.text = "Gasto eliminado."
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
                btn_del = Button(text="X", size_hint_x=None, width=dp(40), background_color=(0.8, 0.2, 0.2, 1))
                btn_del.bind(on_release=lambda instance, x=r_id: (delete_recurring_expense(self.db_path, x), recargar_lista()))
                fila.add_widget(lbl); fila.add_widget(btn_del); lista.add_widget(fila)
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        inp_desc = TextInput(hint_text="Ej: Netflix", multiline=False, size_hint_y=None, height=dp(35))
        inp_monto = TextInput(hint_text="Monto", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        inp_dia = TextInput(hint_text="Día (1-31)", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        btn_add = Button(text="Agregar Fijo", size_hint_y=None, height=dp(40), background_color=(0.6, 0.4, 0.2, 1))
        def agregar(instance):
            if inp_desc.text and inp_monto.text and inp_dia.text:
                add_recurring_expense(self.db_path, inp_desc.text, int(inp_monto.text), "General", int(inp_dia.text))
                inp_desc.text = ""; inp_monto.text = ""; inp_dia.text = ""
                recargar_lista()
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
                btn_abonar = Button(text="Abonar", size_hint_x=None, width=dp(70), background_color=(0.2, 0.6, 0.6, 1))
                btn_del = Button(text="Borrar", size_hint_x=None, width=dp(60), background_color=(0.8, 0.2, 0.2, 1))
                def abonar(instance, x=g_id, inp=inp_abono):
                    if inp.text:
                        add_to_savings_goal(self.db_path, x, int(inp.text))
                        inp.text = ""; recargar_lista(); self.actualizar_pantalla()
                def borrar(instance, x=g_id):
                    delete_savings_goal(self.db_path, x); recargar_lista(); self.actualizar_pantalla()
                btn_abonar.bind(on_release=abonar); btn_del.bind(on_release=borrar)
                botones.add_widget(inp_abono); botones.add_widget(btn_abonar); botones.add_widget(btn_del)
                fila.add_widget(lbl); fila.add_widget(botones); lista.add_widget(fila)
        recargar_lista()
        scroll.add_widget(lista); contenido.add_widget(scroll)
        form = BoxLayout(orientation='vertical', size_hint_y=0.4, spacing=dp(5))
        inp_nombre = TextInput(hint_text="Nombre meta", multiline=False, size_hint_y=None, height=dp(35))
        inp_meta = TextInput(hint_text="Monto meta", multiline=False, input_filter='int', size_hint_y=None, height=dp(35))
        btn_add = Button(text="Crear Meta", size_hint_y=None, height=dp(40), background_color=(0.2, 0.6, 0.6, 1))
        def agregar(instance):
            if inp_nombre.text and inp_meta.text:
                add_savings_goal(self.db_path, inp_nombre.text, int(inp_meta.text))
                inp_nombre.text = ""; inp_meta.text = ""; recargar_lista()
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
                    btn_pagar = Button(text="Pagada", size_hint_x=None, width=dp(60), background_color=(0.2, 0.8, 0.5, 1))
                    btn_del = Button(text="X", size_hint_x=None, width=dp(30), background_color=(0.8, 0.2, 0.2, 1))
                    def hacer_pago(instance, x=d_id):
                        update_debt_status(self.db_path, x, 'paid')
                        recargar_lista()
                        self.actualizar_pantalla()
                    def hacer_borrado(instance, x=d_id):
                        delete_debt(self.db_path, x)
                        recargar_lista()
                        self.actualizar_pantalla()
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
            btn_me_deben = Button(text="Me deben", background_color=(0.2, 0.8, 0.6, 1))
            btn_yo_debo = Button(text="Yo debo", background_color=(0.4, 0.4, 0.4, 1))
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
            btn_add = Button(text="Registrar Deuda", size_hint_y=None, height=dp(40), background_color=(0.8, 0.5, 0.2, 1))
            def agregar(instance):
                p = inp_person.text.strip(); m = inp_monto.text.strip()
                if p and m:
                    add_debt(self.db_path, p, int(m), tipo_seleccionado[0])
                    inp_person.text = ""; inp_monto.text = ""
                    recargar_lista()
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
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "Reporte de Gastos", ln=True, align='C')
            pdf.set_font("Arial", 'I', 10)
            pdf.cell(0, 10, f"Generado el: {date.today().isoformat()}", ln=True, align='C')
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(40, 10, "Fecha", 1); pdf.cell(70, 10, "Descripcion", 1); pdf.cell(30, 10, "Categoria", 1); pdf.cell(30, 10, "Monto", 1); pdf.ln()
            pdf.set_font("Arial", '', 10)
            rows = get_expenses_for_month(self.db_path, datetime.now().strftime('%Y-%m'))
            for _, created_at, desc, amount, cat, curr in rows:
                d_clean = desc.encode('latin-1', 'replace').decode('latin-1')
                c_clean = cat.encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(40, 10, created_at[:10], 1); pdf.cell(70, 10, d_clean, 1); pdf.cell(30, 10, c_clean, 1); pdf.cell(30, 10, f"{self.formato(amount)} {curr}", 1); pdf.ln()
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
