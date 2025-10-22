import tkinter as tk
from tkinter import ttk, messagebox
from plyer import notification
import subprocess
import time
import json
import re
import os
import traceback

from db import connect_db, save_client, save_tnps, ensure_credentials_table, get_credential, set_credential
from templates import templates
from utils import calculate_tnps_percentage
from modales import ModalManager

class Config:
    """Clase de configuración para centralizar constantes."""
    class Fonts:
        DEFAULT = ("Segoe UI", 10)
        DEFAULT_BOLD = ("Segoe UI", 10, "bold")
        H1 = ("Segoe UI", 12, "bold")
        H2 = ("Segoe UI", 11, "bold")
        SMALL_BOLD = ("Segoe UI", 9, "bold")
        COPY_BUTTON = ("Segoe UI", 9)

    class Window:
        TITLE = "Aplicación de Escritorio - Clientes"
        INITIAL_GEOMETRY = "324x600"

    class Timers:
        STANDUP_REMINDER_MS = 3600000  # 1 hora
        CALL_TIMER_WARNING_S = 420     # 7 minutos
        CALL_TIMER_ALERT_S = 600       # 10 minutos
        DB_STATUS_CHECK_MS = 10000     # 10 segundos
        CLIPBOARD_WATCHER_MS = 700

    class Colors:
        GREEN = "green"
        RED = "red"
        BLACK = "black"
        WHITE = "white"

    THEMES = {
        'modern': {
            'bg': '#fcfcfc', 'fg': '#212529', 'input_bg': '#ffffff', 'accent': '#0d6efd',
            'accent_hover': '#0b5ed7', 'accent_pressed': '#0a58ca', 'subtle': '#dee2e6',
            'border': '#dee2e6',  # Clave añadida para consistencia
            'notes_bg': '#ffffff', 'saludo_bg': '#fcfcfc', 'saludo_fg': '#0d6efd'
        },
        'dark': {
            'bg': '#212529', 'fg': '#f8f9fa', 'input_bg': '#343a40', 'pane_bg': '#212529',
            'accent': '#3391ff', 'accent_hover': '#5ca9ff', 'accent_pressed': '#1a75ff',
            'border': '#495057', 'subtle_fg': '#adb5bd', 'notes_bg': '#343a40',
            'saludo_bg': '#212529', 'saludo_fg': '#3391ff', 'db_ok': '#20c997'
        }
    }

class App:
    def _open_detalles_generico(self):
        if hasattr(self, 'modal_manager') and self.modal_manager:
            self.modal_manager.open_detalles_generico_modal()

    def __init__(self, root):
        self.root = root
        self._initialize_state()
        self._configure_root_window()
        self._configure_styles()
        self._create_widgets()
        self._load_initial_data()
        self._setup_event_bindings()
        self._start_background_tasks()

    def _initialize_state(self):
        self.timer_running = False; self.timer_seconds = 0; self.alert_10min_shown = False
        self.standup_timer_id = None; self.last_client_id = None; self.tnps_registros = []
        self.current_theme = 'modern'; self.clipboard_history = []; self.last_clip_text = ''
        self.clip_mode = 'preguntar'; self.session = {'id': None, 'start': None, 'active': False}
        # Generar session_id único para la sesión actual (se mantiene hasta 'Limpiar')
        try:
            import uuid
            self.session['id'] = str(uuid.uuid4())
            self.session['start'] = time.time()
            self.session['active'] = True
        except Exception:
            # fallback a None si uuid no está disponible
            self.session['id'] = None
        self.nombre_var = tk.StringVar(); self.numero_var = tk.StringVar(); self.sn_var = tk.StringVar()
        self.dni_var = tk.StringVar(); self.timer_var = tk.StringVar(value="00:00"); self.db_status_var = tk.StringVar(value="DB: ?")
        self.motivo_var = tk.StringVar(value="Selecciona motivo..."); self.tnps_var = tk.StringVar()
        self.clipboard_watcher_on = tk.BooleanVar(value=True)
        self.saludo_var, self.sondeo_var, self.empatia_var, self.titularidad_var, self.oferta_var, self.proceso_var, self.encuesta_var = (tk.BooleanVar() for _ in range(7))

    def _configure_root_window(self):
        self.root.title(Config.Window.TITLE); self.root.geometry(Config.Window.INITIAL_GEOMETRY)
        self.root.resizable(True, True); self.root.attributes('-topmost', True); self.root._icons = {}

    def _configure_styles(self):
        self.style = ttk.Style(); self.style.theme_use('clam')
        self.style.configure('Copy.TButton', font=Config.Fonts.COPY_BUTTON, padding=(4,2))
        self._apply_theme('modern')

    def _load_initial_data(self):
        try:
            conn = connect_db()
            with conn.cursor() as cursor:
                cursor.execute("SELECT tnps_score FROM tnps WHERE DATE(fecha_tnps) = CURDATE()")
                self.tnps_registros = [row['tnps_score'] for row in cursor.fetchall()]
            conn.close()
        except Exception as db_error:
            print(f"[WARNING] Error al cargar TNPS: {db_error}")
        self._update_tnps_percentage()
        try: ensure_credentials_table()
        except Exception as cred_err: print(f"[WARNING] No se pudo asegurar tabla de credenciales: {cred_err}")

    def _create_widgets(self):
        self._create_header(); self._create_scrollable_area()
        # Crear la seccion de flags/checks (compacta) arriba para acceso rápido
        self._create_flags_section()
        self._create_client_form()
        self._create_call_reason_section(); self._create_action_buttons(); self._create_notes_section()
        self._create_tnps_section(); self._create_theme_button(); self._initialize_modal_manager()

    def _create_header(self):
        header_frame = ttk.Frame(self.root); header_frame.pack(fill="x", padx=8, pady=(8,0))
        creds_frame = ttk.Frame(header_frame); creds_frame.pack(side='right')
        # Botones notorios para acciones secundarias (VPN, SIAC, Editar credenciales, Cerrar Excel)
        try:
            accent = Config.THEMES[self.current_theme]['accent']
        except Exception:
            accent = '#0d6efd'
        # estilo temporal para botones notorios (más compactos)
        # reducimos padding y fijamos un ancho corto para que sean menos largos
        self.style.configure('Accent.TButton', background=accent, foreground=Config.Colors.WHITE, relief='flat', padding=(4,4))
        # Botón para ver registros (lista de atenciones) - restaurado a la izquierda
        ttk.Button(header_frame, text='📋', style='Accent.TButton', width=3, command=lambda: self.modal_manager.open_lista_atenciones_modal()).pack(side='left', padx=(0,6))
        ttk.Button(creds_frame, text='🔒', style='Accent.TButton', width=3, command=lambda: self._copy_credential('vpn_password', 'VPN')).pack(side='right', padx=(4,2))
        ttk.Button(creds_frame, text='🔑', style='Accent.TButton', width=3, command=lambda: self._copy_credential('siac_password', 'SIAC')).pack(side='right', padx=(4,2))
        ttk.Button(creds_frame, text='✏️', style='Accent.TButton', width=3, command=lambda: self.modal_manager.open_credentials_modal()).pack(side='right', padx=(4,2))
        ttk.Button(creds_frame, text='🗙', style='Accent.TButton', width=3, command=self._close_all_excel).pack(side='right', padx=(4,6))
        top_frame = ttk.Frame(self.root); top_frame.pack(fill="x", pady=(4,8), padx=8)
        theme_colors = Config.THEMES[self.current_theme]
        saludo_bg_frame = tk.Frame(top_frame, bg=theme_colors['saludo_bg'], bd=0); saludo_bg_frame.pack(side='left', padx=(0,4))
        self.saludo_label = tk.Label(saludo_bg_frame, text=f"Buenas noches, Sr. {self.nombre_var.get() or 'Cliente'}", wraplength=260, justify="center", font=Config.Fonts.H2, bg=theme_colors['saludo_bg'], fg=theme_colors['saludo_fg'], padx=6, pady=4); self.saludo_label.pack()
        self.timer_label = ttk.Label(top_frame, textvariable=self.timer_var, font=Config.Fonts.DEFAULT); self.timer_label.pack(side="right")
        self.db_status_label = ttk.Label(top_frame, textvariable=self.db_status_var, font=Config.Fonts.SMALL_BOLD); self.db_status_label.pack(side="right", padx=(8,0))

    def _create_scrollable_area(self):
        container = ttk.Frame(self.root); container.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas = tk.Canvas(container, highlightthickness=0); self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview); scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

    def _create_client_form(self):
        ttk.Label(self.scrollable_frame, text="Datos del Cliente", font=Config.Fonts.H1).pack(anchor='w', padx=8, pady=(4,2))
        form_container = ttk.Frame(self.scrollable_frame); form_container.pack(fill="both", expand=True, pady=(0,8), padx=8)
        form_frame = ttk.Frame(form_container); form_frame.pack(fill="x"); form_frame.grid_columnconfigure(1, weight=1)
        # Reordenado: primero Teléfono, luego SN, luego Nombre, por último DNI
        self.numero_entry = self._create_form_row(form_frame, 0, "Número:", self.numero_var)
        self.sn_entry = self._create_form_row(form_frame, 1, "SN:", self.sn_var)
        self.nombre_entry = self._create_form_row(form_frame, 2, "Nombre:", self.nombre_var)
        self.dni_entry = self._create_form_row(form_frame, 3, "DNI:", self.dni_var)

    def _create_form_row(self, parent, row, label_text, variable):
        # Asignar icono y placeholder según el campo
        icon_map = {
            'Nombre:': '👤',
            'Número:': '📞',
            'SN:': '🔢',
            'DNI:': '🆔',
        }
        placeholder_map = {
            'Nombre:': 'Nombre completo',
            'Número:': 'Teléfono de contacto',
            'SN:': 'Número de serie',
            'DNI:': 'DNI del cliente',
        }
        icon = icon_map.get(label_text, '')
        placeholder = placeholder_map.get(label_text, label_text)

        entry_var = variable
        entry = ttk.Entry(parent, textvariable=entry_var, font=Config.Fonts.DEFAULT, width=25)
        entry.grid(row=row, column=1, sticky="ew", pady=(0,6), padx=(0,0))
        # Insertar placeholder si está vacío
        def on_focus_in(event, e=entry, p=placeholder):
            if e.get() == p:
                e.delete(0, tk.END)
                e.config(foreground='#212529')
        def on_focus_out(event, e=entry, p=placeholder):
            if not e.get():
                e.insert(0, p)
                e.config(foreground='#888888')
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        entry.insert(0, placeholder)
        entry.config(foreground='#888888')
        # Icono a la izquierda (como label pequeño)
        icon_label = ttk.Label(parent, text=icon, font=Config.Fonts.H2)
        icon_label.grid(row=row, column=0, sticky="e", pady=(0,6), padx=(0,4))
        ttk.Button(parent, text="📋", style='Copy.TButton', width=3, command=lambda: self._copy_to_clipboard(entry_var.get())).grid(row=row, column=2, sticky="e", pady=(0,12))
        return entry



    def _create_call_reason_section(self):
        ttk.Label(self.scrollable_frame, text="Motivo de llamada", font=Config.Fonts.H1).pack(anchor='w', padx=8, pady=(4,2))
        container = ttk.Frame(self.scrollable_frame); container.pack(fill="both", expand=True, pady=(0,8), padx=8)
        frame = ttk.Frame(container); frame.pack(fill="x")
        motivo_values = self._get_normalized_motivos()
        self.motivo_combo = ttk.Combobox(frame, textvariable=self.motivo_var, values=motivo_values, state="readonly", font=Config.Fonts.DEFAULT)
        self.motivo_combo.pack(side="left", fill="x", expand=True); self._disable_mousewheel_on(self.motivo_combo)

    def _create_action_buttons(self):
        frame = ttk.Frame(self.scrollable_frame); frame.pack(fill="x", pady=(4,10), padx=8)
        ttk.Button(frame, text="Agregar Cliente", command=self._add_client).pack(side="left", padx=(0,10))
        ttk.Button(frame, text="Limpiar", command=self._clear_form).pack(side="left")

    def _create_notes_section(self):
        ttk.Label(self.scrollable_frame, text="Notas", font=Config.Fonts.H1).pack(anchor='w', padx=8, pady=(4,2))
        container = ttk.Frame(self.scrollable_frame); container.pack(fill="both", expand=True, pady=(0,8), padx=8)
        theme_colors = Config.THEMES[self.current_theme]
        self.template_text = tk.Text(container, height=8, wrap="word", font=Config.Fonts.DEFAULT, relief="flat", borderwidth=2, background=theme_colors['notes_bg'], foreground=theme_colors['fg'], insertbackground=theme_colors['accent'])
        self.template_text.pack(fill="both", expand=True)
        ttk.Button(self.scrollable_frame, text="Copiar Plantilla", command=lambda: self._copy_to_clipboard(self.template_text.get(1.0, tk.END))).pack(fill="x", pady=(5,0))

    def _create_tnps_section(self):
        ttk.Label(self.scrollable_frame, text="TNPS", font=Config.Fonts.H1).pack(anchor='w', padx=8, pady=(4,2))
        container = ttk.Frame(self.scrollable_frame); container.pack(fill="both", expand=True, pady=(0,8), padx=8)
        frame = ttk.Frame(container); frame.pack(fill="x")
        ttk.Label(frame, text="TNPS:", font=Config.Fonts.DEFAULT_BOLD).pack(side="left")
        self.tnps_combo = ttk.Combobox(frame, textvariable=self.tnps_var, values=[str(i) for i in range(10)], state="readonly", width=5)
        self.tnps_combo.pack(side="left", padx=(5,5)); self._disable_mousewheel_on(self.tnps_combo)
        ttk.Button(frame, text="Guardar TNPS", command=self._save_tnps_action).pack(side="left", padx=(0,5))
        ttk.Button(frame, text="📋 ", style='Copy.TButton', width=3, command=self._copy_tnps).pack(side="left")
        self.tnps_resultado = ttk.Label(container, text="", font=Config.Fonts.DEFAULT_BOLD); self.tnps_resultado.pack(anchor="w", pady=(0,5))

    def _create_theme_button(self):
        ttk.Button(self.scrollable_frame, text="Cambiar Tema", command=self._toggle_theme).pack(pady=10)

    def _initialize_modal_manager(self):
        context = { 'template_text': self.template_text, 'nombre_var': self.nombre_var, 'numero_var': self.numero_var, 'sn_var': self.sn_var, 'dni_var': self.dni_var, 'save_client': save_client, 'get_credential': get_credential, 'set_credential': set_credential, 'position_modal': self._position_modal, 'disable_mousewheel_on': self._disable_mousewheel_on, 'current_theme': self.current_theme }
        try: self.modal_manager = ModalManager(self.root, context)
        except Exception as e: print(f"[ERROR] Failed to initialize ModalManager: {e}"); self.modal_manager = None

    def _setup_event_bindings(self):
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure); self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel_to_canvas); self.canvas.bind("<Leave>", self._unbind_mousewheel_from_canvas)
        self.nombre_var.trace_add("write", self._update_saludo); self.numero_var.trace_add("write", lambda *a: self._start_timer())
    # No autosave al cambiar motivo: el guardado se hace solo con el botón 'Limpiar'
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_background_tasks(self):
        self._check_db_status(); self._clipboard_watcher(); self._start_standup_reminder(); self._update_template()

    def _apply_theme(self, theme_name):
        theme = Config.THEMES[theme_name]

        # Configuración base
        self.root.configure(bg=theme['bg'])
        self.style.configure('.', background=theme['bg'], foreground=theme['fg'])
        self.style.configure('TFrame', background=theme['bg'])
        self.style.configure('TLabel', background=theme['bg'], foreground=theme['fg'], font=Config.Fonts.H2)
        self.style.configure('TCheckbutton', background=theme['bg'], foreground=theme['fg'], font=Config.Fonts.DEFAULT)

        # Botones
        self.style.configure('TButton', font=Config.Fonts.DEFAULT_BOLD, relief='flat', borderwidth=0, padding=(12,6), background=theme['accent'], foreground=Config.Colors.WHITE)
        self.style.map('TButton', background=[('active', theme['accent_hover']), ('pressed', theme['accent_pressed'])])

        # Botón de copiar (más pequeño y sutil)
        self.style.configure('Copy.TButton', font=Config.Fonts.COPY_BUTTON, padding=(4,2), background=theme['accent'], foreground=Config.Colors.WHITE)

        # Entradas y Combobox
        self.style.configure('TEntry', fieldbackground=theme['input_bg'], foreground=theme['fg'], font=Config.Fonts.DEFAULT, padding=(8,6), relief='flat', borderwidth=1)
        self.style.configure('TCombobox', fieldbackground=theme['input_bg'], foreground=theme['fg'], font=Config.Fonts.DEFAULT, padding=(8,6))
        self.style.map('TEntry', bordercolor=[('focus', theme['accent']), ('!focus', theme.get('border', theme.get('subtle', '#CCCCCC')))])
        self.style.map('TCombobox', bordercolor=[('focus', theme['accent']), ('!focus', theme.get('border', theme.get('subtle', '#CCCCCC')))])

        # Scrollbar
        self.style.configure('TScrollbar', troughcolor=theme['bg'], background=theme.get('pane_bg', theme.get('subtle', '#CCCCCC')), borderwidth=0, arrowsize=0, relief='flat')
        self.style.map('TScrollbar', background=[('active', theme['accent'])])

        # Actualizar widgets que no se actualizan solos
        if hasattr(self, 'canvas'): self.canvas.config(bg=theme.get('pane_bg', theme['bg']))
        if hasattr(self, 'template_text'): self.template_text.config(background=theme['notes_bg'], foreground=theme['fg'], insertbackground=theme['accent'])
        if hasattr(self, 'saludo_label'): 
            self.saludo_label.master.config(bg=theme['saludo_bg'])
            self.saludo_label.config(bg=theme['saludo_bg'], fg=theme['saludo_fg'])
        # El color del status de la DB depende de su estado, no del tema, por lo que no se toca aquí.

    def _toggle_theme(self):
        self.current_theme = 'dark' if self.current_theme == 'modern' else 'modern'
        self._apply_theme(self.current_theme)
        if hasattr(self, 'modal_manager') and self.modal_manager: self.modal_manager.ctx['current_theme'] = self.current_theme

    def _load_icon(self, name):
        path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', f"{name}.png")
        if not os.path.exists(path): return None
        try: img = tk.PhotoImage(file=path); self.root._icons[name] = img; return img
        except Exception: return None

    def _create_icon_button(self, parent, icon_name, emoji_text, command):
        img = self._load_icon(icon_name)
        return ttk.Button(parent, image=img, command=command, style='Copy.TButton') if img else ttk.Button(parent, text=emoji_text, command=command, style='Copy.TButton')

    def _create_flags_section(self):
        # Seccion compacta con checkbuttons: saludo, sondeo, empatia, titularidad, oferta, proceso, encuesta
        container = ttk.Frame(self.scrollable_frame)
        container.pack(fill="x", padx=8, pady=(4,6))
        # usar una fuente mas pequeña
        small_font = Config.Fonts.COPY_BUTTON
        flags = [
            ("Saludo", self.saludo_var),
            ("Sondeo", self.sondeo_var),
            ("Empatía", self.empatia_var),
            ("Titularidad", self.titularidad_var),
            ("Oferta", self.oferta_var),
            ("Proceso", self.proceso_var),
            ("Encuesta", self.encuesta_var),
        ]
        # distribuir en dos filas si es necesario para mantener compacto
        row1 = ttk.Frame(container); row1.pack(fill='x')
        row2 = ttk.Frame(container); row2.pack(fill='x')
        for i, (label, var) in enumerate(flags):
            parent = row1 if i < 4 else row2
            cb = ttk.Checkbutton(parent, text=label, variable=var)
            cb.pack(side='left', padx=(4,6), pady=2)

    def _on_frame_configure(self, event): self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_canvas_configure(self, event): self.canvas.itemconfigure(self.window_id, width=event.width); self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def _on_mousewheel(self, event): self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    def _bind_mousewheel_to_canvas(self, event): self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    def _unbind_mousewheel_from_canvas(self, event): self.canvas.unbind_all("<MouseWheel>")

    def _update_saludo(self, *args):
        self.saludo_label.config(text=f"Buenas noches, Sr. {self.nombre_var.get().strip() or 'Cliente'}"); self._start_timer()

    def _start_timer(self):
        if (self.nombre_var.get().strip() or self.numero_var.get().strip()) and not self.timer_running:
            self.timer_running = True; self.timer_seconds = 0; self._update_timer()

    def _stop_timer(self): self.timer_running = False; self.alert_10min_shown = False

    def _update_timer(self):
        if self.timer_running:
            self.timer_seconds += 1
            minutes, seconds = divmod(self.timer_seconds, 60)
            self.timer_var.set(f"{minutes:02d}:{seconds:02d}")
            self.timer_label.config(foreground=Config.Colors.RED if self.timer_seconds >= Config.Timers.CALL_TIMER_WARNING_S else Config.Colors.BLACK)
            if self.timer_seconds == Config.Timers.CALL_TIMER_ALERT_S and not self.alert_10min_shown:
                notification.notify(title="Alerta de Llamada", message="La llamada ha superado los 10 minutos", timeout=5); self.alert_10min_shown = True
            self.root.after(1000, self._update_timer)

    def _add_client(self, open_modal=True):
        nombre, motivo = self.nombre_var.get(), self.motivo_var.get()
        if motivo == 'Atención técnica': self.modal_manager.open_tecnica_modal(); return
        if nombre and motivo != "Selecciona motivo...":
            if open_modal and motivo in ["Retención", "Cuestionamiento de recibo"]:
                if motivo == "Retención": self.modal_manager.open_retencion_modal()
                else: self.modal_manager.open_cuestionamiento_modal()
            elif open_modal:
                def guard_cb(extra_notas):
                        # Si el motivo es genérico, reemplazar exactamente con lo enviado por el modal
                        try:
                            motivo_norm = (motivo or '').strip().lower()
                        except Exception:
                            motivo_norm = ''
                        if motivo_norm in ('otros', 'motivo generico', 'motivo genérico', 'motivo generico'.lower()):
                            notas = extra_notas.strip()
                        else:
                            notas = (self.template_text.get(1.0, tk.END).strip() + '\n' + extra_notas).strip()
                        # No guardar aún: solo actualizar la plantilla para que se conserve hasta 'Limpiar'
                        template_text = self.template_text
                        if template_text is not None:
                            template_text.delete(1.0, tk.END)
                            template_text.insert(tk.END, notas)
                        self._stop_timer(); self._update_template()
                self.modal_manager.open_motivo_modal(motivo, guard_cb)
            else:
                try:
                    # En modo "rápido" no guardamos ahora; solo preparamos la plantilla y mantenemos datos en el formulario
                    self._stop_timer(); self._update_template()
                except Exception as e: messagebox.showerror("Error", f"Error interno: {e}")

    def _clear_form(self):
        # Guardar los datos actuales antes de limpiar. Se guarda si hay cualquier dato en los campos
        try:
            nombre = self.nombre_var.get().strip()
            numero = self.numero_var.get().strip()
            sn = self.sn_var.get().strip()
            dni = self.dni_var.get().strip()
            motivo = self.motivo_var.get()
            notas_base = self.template_text.get(1.0, tk.END).strip()

            should_save = any([nombre, numero, sn, dni, notas_base]) or (motivo and motivo != "Selecciona motivo...")
            if should_save:
                # Construir notas completas incluyendo metadatos del formulario
                meta_lines = []
                # Temporizador
                try:
                    meta_lines.append(f"Duracion llamada: {self.timer_var.get()}")
                except Exception:
                    pass
                # Checkboxes y flags relevantes
                try:
                    flags = {
                        'saludo': getattr(self, 'saludo_var', None),
                        'sondeo': getattr(self, 'sondeo_var', None),
                        'empatia': getattr(self, 'empatia_var', None),
                        'titularidad': getattr(self, 'titularidad_var', None),
                        'oferta': getattr(self, 'oferta_var', None),
                        'proceso': getattr(self, 'proceso_var', None),
                        'encuesta': getattr(self, 'encuesta_var', None),
                    }
                    for k, v in flags.items():
                        if isinstance(v, tk.BooleanVar):
                            meta_lines.append(f"{k}: {'SI' if v.get() else 'NO'}")
                except Exception:
                    pass

                # Adjuntar otros datos útiles
                meta_lines.append(f"Motivo seleccionado: {motivo if motivo else ''}")
                meta_lines.append(f"SN: {sn}")
                meta_lines.append(f"DNI: {dni}")
                meta_lines.append(f"Numero: {numero}")

                notas_full = notas_base
                if notas_full:
                    notas_full = notas_full + "\n\n--- METADATOS ---\n" + "\n".join(meta_lines)
                else:
                    notas_full = "--- METADATOS ---\n" + "\n".join(meta_lines)

                # El esquema requiere `nombre NOT NULL` — si no hay nombre, usar un placeholder razonable
                nombre_save = nombre if nombre else 'Sin nombre'
                motivo_save = motivo if motivo and motivo != "Selecciona motivo..." else 'Sin motivo'
                try:
                    session_id_val = self.session.get('id') if getattr(self, 'session', None) else None
                    self.last_client_id = save_client(nombre_save, numero or None, sn or None, motivo_save, dni=dni or None, notas=notas_full, session_id=session_id_val)
                except Exception as e:
                    # Mostrar error pero permitir que el limpiado continúe
                    try:
                        messagebox.showerror("Error", f"Error al guardar cliente antes de limpiar: {e}")
                    except Exception:
                        print(f"Error al mostrar dialogo de error: {e}")
        except Exception as exc:
            print(f"[WARNING] Error al intentar guardar antes de limpiar: {exc}")

        # Limpiar campos del formulario
        self.nombre_var.set("")
        self.numero_var.set("")
        self.sn_var.set("")
        self.dni_var.set("")
        self.motivo_var.set("Selecciona motivo...")
        try:
            self.template_text.delete(1.0, tk.END)
        except Exception:
            pass

        # Deseleccionar flags/checks
        try:
            for v in (self.saludo_var, self.sondeo_var, self.empatia_var, self.titularidad_var, self.oferta_var, self.proceso_var, self.encuesta_var):
                if isinstance(v, tk.BooleanVar):
                    v.set(False)
        except Exception:
            pass

        # Iniciar nueva sesión (marcar inicio de sesión en este punto)
        try:
            self.session['id'] = None
            self.session['start'] = time.time()
            self.session['active'] = True
        except Exception:
            pass

        self._stop_timer(); self._update_template()

    def _update_template(self, event=None):
        motivo = self.motivo_var.get()
        if motivo == 'Atención técnica': self.modal_manager.open_tecnica_modal(); return
        if motivo not in ["Retención", "Cuestionamiento de recibo"]:
            self.template_text.delete(1.0, tk.END); self.template_text.insert(tk.END, templates.get(motivo, ""))

    # Autosave al cambiar motivo eliminado: el guardado solo ocurre con el botón 'Limpiar'.

    def _get_normalized_motivos(self):
        motivo_values = list(templates.keys());
        if 'Otros' not in motivo_values: motivo_values.append('Otros')
        seen = set(); normalized = []
        for v in motivo_values:
            if not v: continue
            low = v.strip().lower()
            if low in seen or low == 'ajuste': continue
            seen.add(low)
            if low in ('atención técnica', 'atención tecnica', 'atencion tecnica'):
                if 'Atención técnica' not in normalized: normalized.append('Atención técnica')
            else: normalized.append(v)
        if 'Atención técnica' not in normalized: normalized.append('Atención técnica')
        return normalized

    def _save_tnps_action(self):
        if score_str := self.tnps_var.get():
            self.tnps_registros.append(int(score_str)); save_tnps(int(score_str)); self.tnps_var.set(""); self._update_tnps_percentage()
        else: messagebox.showwarning("TNPS", "Selecciona un TNPS")

    def _update_tnps_percentage(self):
        if self.tnps_registros:
            porcentaje = calculate_tnps_percentage(self.tnps_registros)
            color = Config.Colors.GREEN if porcentaje >= 77 else Config.Colors.RED
            estado = "positivo" if porcentaje >= 77 else "negativo"
            self.tnps_resultado.config(text=f"TNPS {estado}: {porcentaje}%", foreground=color)
        else: self.tnps_resultado.config(text="No hay registros aún", foreground=Config.Colors.BLACK)

    def _copy_tnps(self):
        if self.tnps_registros: self._copy_to_clipboard('\n'.join(map(str, self.tnps_registros)), "TNPS")
        else: messagebox.showwarning("TNPS", "No hay registros para copiar")

    def _on_close(self):
        has_data = any([self.nombre_var.get(), self.numero_var.get(), self.sn_var.get(), self.dni_var.get(), self.motivo_var.get() != "Selecciona motivo..."])
        if has_data and not messagebox.askyesno("Guardar datos", "¿Tienes datos sin guardar? ¿Quieres cerrar?"): self.root.iconify()
        else: self._shutdown()

    def _shutdown(self):
        if self.standup_timer_id: self.root.after_cancel(self.standup_timer_id)
        self.root.destroy()

    def _check_db_status(self):
        try: conn = connect_db(); conn.close(); self.db_status_var.set("DB: OK"); self.db_status_label.config(foreground=Config.Colors.GREEN)
        except Exception: self.db_status_var.set("DB: Offline"); self.db_status_label.config(foreground=Config.Colors.RED)
        self.root.after(Config.Timers.DB_STATUS_CHECK_MS, self._check_db_status)

    def _start_standup_reminder(self):
        if self.standup_timer_id is None: self.standup_timer_id = self.root.after(Config.Timers.STANDUP_REMINDER_MS, self._show_standup_reminder)

    def _show_standup_reminder(self):
        notification.notify(title="Recordatorio de Salud", message="¡Levántate y estira las piernas!", timeout=10)
        self.standup_timer_id = self.root.after(Config.Timers.STANDUP_REMINDER_MS, self._show_standup_reminder)

    def _clipboard_watcher(self):
        if self.clipboard_watcher_on.get():
            try: clip = self.root.clipboard_get()
            except Exception: clip = ''
            if clip and clip != self.last_clip_text:
                parsed = self._parse_clipboard(clip)
                if parsed: self._handle_parsed_clipboard(parsed)
                self.last_clip_text = clip
        self.root.after(Config.Timers.CLIPBOARD_WATCHER_MS, self._clipboard_watcher)

    def _handle_parsed_clipboard(self, parsed):
        ts = time.time()
        self.clipboard_history.insert(0, {'text': self.last_clip_text, 'parsed': parsed, 'ts': ts})
        if len(self.clipboard_history) > 50: self.clipboard_history.pop()
        any_empty = not all(v.get().strip() for v in [self.nombre_var, self.numero_var, self.sn_var, self.dni_var]) or not self.template_text.get(1.0, tk.END).strip()
        in_session = not self.session['active'] or (ts - self.session['start']) <= 180
        if in_session and any_empty:
            if self.clip_mode in ['autofill_always', 'autofill_empty']: self._fill_fields(parsed)
            else: self._show_suggestion_dialog(parsed)

    def _parse_clipboard(self, text):
        # Basic key-value and regex parsing logic
        return {}

    def _fill_fields(self, parsed, replace=False):
        # Logic to fill form fields from parsed data
        pass

    def _show_suggestion_dialog(self, parsed):
        # Dialog to ask user about autofill
        pass

    def _apply_last_clip(self):
        if self.clipboard_history and self.clipboard_history[0].get('parsed'): self._fill_fields(self.clipboard_history[0]['parsed'])

    def _copy_to_clipboard(self, text, name=None):
        self.root.clipboard_clear(); self.root.clipboard_append(text)
        if name: print(f"{name} copiado al portapapeles")

    def _copy_credential(self, key, name):
        try:
            val = get_credential(key)
            if val: self._copy_to_clipboard(val, name)
            else: messagebox.showwarning("Vacío", f"No hay valor para {name}")
        except Exception as e: messagebox.showerror("Error", f"Error al obtener credencial: {e}")

    def _close_all_excel(self):
        try: subprocess.run(["taskkill", "/IM", "EXCEL.EXE", "/F"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError): pass

    def _position_modal(self, modal, width=None, height=None, side='right'):
        self.root.update_idletasks(); modal.update_idletasks()
        scr_w, scr_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        r_x, r_y, r_w, r_h = self.root.winfo_rootx(), self.root.winfo_rooty(), self.root.winfo_width(), self.root.winfo_height()
        m_w, m_h = (width or modal.winfo_reqwidth()), (height or modal.winfo_reqheight())
        y = r_y + max(0, (r_h - m_h) // 2)
        x = (r_x + r_w + 8) if side == 'right' else max(0, r_x - m_w - 8)
        if (side == 'right' and x + m_w > scr_w) or (side != 'right' and x < 0): x = (r_x + r_w + 8) if x < 0 else max(0, r_x - m_w - 8)
        modal.geometry(f"{m_w}x{m_h}+{max(0, min(x, scr_w - m_w))}+{max(0, min(y, scr_h - m_h))}")

    def _disable_mousewheel_on(self, widget): widget.bind('<MouseWheel>', lambda e: 'break')

    def run(self):
        self.root.mainloop()

def run_app():
    try:
        root = tk.Tk()
        app = App(root)
        app.run()
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ERROR] Excepción fatal en la aplicación: {tb}")
        messagebox.showerror("Error Fatal", f"Ocurrió un error irrecuperable:\n{e}")

if __name__ == '__main__':
    run_app()
