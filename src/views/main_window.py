"""
Ventana principal de la aplicación.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from plyer import notification
import subprocess
import time
import re
import uuid
import traceback

from src.models.database import (
    save_client, save_tnps, ensure_credentials_table, 
    get_credential, set_credential, get_tnps_today, get_connection
)
from src.models.templates import templates
from src.utils.helpers import calculate_tnps_percentage, get_saludo_dinamico
from src.views.modals import ModalManager


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
        TITLE = "Bloc de Notas - Atención al Cliente"
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
            'bg': '#fcfcfc', 'fg': '#212529', 'input_bg': '#ffffff', 
            'accent': '#0d6efd', 'accent_hover': '#0b5ed7', 'accent_pressed': '#0a58ca',
            'subtle': '#dee2e6', 'border': '#dee2e6',
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
    """Aplicación principal de gestión de atención al cliente."""

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
        """Inicializa el estado de la aplicación."""
        # Estado del timer
        self.timer_running = False
        self.timer_seconds = 0
        self.alert_10min_shown = False
        self.standup_timer_id = None
        
        # Estado de datos
        self.last_client_id = None
        self.tnps_registros = []
        self.current_theme = 'modern'
        self.clipboard_history = []
        self.last_clip_text = ''
        self.clip_mode = 'autofill_empty'
        
        # Sesión
        self.session = {
            'id': str(uuid.uuid4()),
            'start': time.time(),
            'active': True
        }
        
        # Variables de formulario
        self.nombre_var = tk.StringVar()
        self.numero_var = tk.StringVar()
        self.sn_var = tk.StringVar()
        self.dni_var = tk.StringVar()
        self.timer_var = tk.StringVar(value="00:00")
        self.db_status_var = tk.StringVar(value="DB: ?")
        self.motivo_var = tk.StringVar(value="Selecciona motivo...")
        self.tnps_var = tk.StringVar()
        self.clipboard_watcher_on = tk.BooleanVar(value=True)
        
        # Flags de checklist
        self.saludo_var = tk.BooleanVar()
        self.sondeo_var = tk.BooleanVar()
        self.empatia_var = tk.BooleanVar()
        self.titularidad_var = tk.BooleanVar()
        self.oferta_var = tk.BooleanVar()
        self.proceso_var = tk.BooleanVar()
        self.encuesta_var = tk.BooleanVar()

    def _configure_root_window(self):
        """Configura la ventana principal."""
        self.root.title(Config.Window.TITLE)
        self.root.geometry(Config.Window.INITIAL_GEOMETRY)
        self.root.resizable(True, True)
        self.root.attributes('-topmost', True)
        self.root._icons = {}

    def _configure_styles(self):
        """Configura los estilos ttk."""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('Copy.TButton', font=Config.Fonts.COPY_BUTTON, padding=(4, 2))
        self._apply_theme('modern')

    def _load_initial_data(self):
        """Carga datos iniciales desde la base de datos."""
        try:
            self.tnps_registros = get_tnps_today()
        except Exception as e:
            print(f"[WARNING] Error al cargar TNPS: {e}")
            self.tnps_registros = []
        self._update_tnps_percentage()
        ensure_credentials_table()

    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        self._create_header()
        self._create_scrollable_area()
        self._create_flags_section()
        self._create_client_form()
        self._create_call_reason_section()
        self._create_action_buttons()
        self._create_notes_section()
        self._create_tnps_section()
        self._create_theme_button()
        self._initialize_modal_manager()

    def _create_header(self):
        """Crea la cabecera con botones de acceso rápido."""
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=8, pady=(8, 0))
        
        creds_frame = ttk.Frame(header_frame)
        creds_frame.pack(side='right')
        
        accent = Config.THEMES[self.current_theme]['accent']
        self.style.configure('Accent.TButton', background=accent, 
                           foreground=Config.Colors.WHITE, relief='flat', padding=(4, 4))
        
        # Botón lista de atenciones
        ttk.Button(header_frame, text='📋', style='Accent.TButton', width=3,
                  command=lambda: self.modal_manager.open_lista_atenciones_modal()).pack(side='left', padx=(0, 6))
        
        # Botón de ajustes (⚙️)
        ttk.Button(header_frame, text='⚙️', style='Accent.TButton', width=3,
                  command=self._open_settings_modal).pack(side='left', padx=(0, 6))
        
        # Botones de credenciales
        ttk.Button(creds_frame, text='🔒', style='Accent.TButton', width=3,
                  command=lambda: self._copy_credential('vpn_password', 'VPN')).pack(side='right', padx=(4, 2))
        ttk.Button(creds_frame, text='🔑', style='Accent.TButton', width=3,
                  command=lambda: self._copy_credential('siac_password', 'SIAC')).pack(side='right', padx=(4, 2))
        ttk.Button(creds_frame, text='✏️', style='Accent.TButton', width=3,
                  command=lambda: self.modal_manager.open_credentials_modal()).pack(side='right', padx=(4, 2))
        ttk.Button(creds_frame, text='🗙', style='Accent.TButton', width=3,
                  command=self._close_all_excel).pack(side='right', padx=(4, 6))
        
        # Frame de saludo y timer
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", pady=(4, 8), padx=8)
        
        theme_colors = Config.THEMES[self.current_theme]
        saludo_bg_frame = tk.Frame(top_frame, bg=theme_colors['saludo_bg'], bd=0)
        saludo_bg_frame.pack(side='left', padx=(0, 4))
        
        saludo_texto = get_saludo_dinamico(self.nombre_var.get() or 'Nombre completo')
        self.saludo_label = tk.Label(
            saludo_bg_frame,
            text=saludo_texto,
            wraplength=260, justify="center", font=Config.Fonts.H2,
            bg=theme_colors['saludo_bg'], fg=theme_colors['saludo_fg'], padx=6, pady=4
        )
        self.saludo_label.pack()
        
        self.timer_label = ttk.Label(top_frame, textvariable=self.timer_var, font=Config.Fonts.DEFAULT)
        self.timer_label.pack(side="right")
        
        self.db_status_label = ttk.Label(top_frame, textvariable=self.db_status_var, font=Config.Fonts.SMALL_BOLD)
        self.db_status_label.pack(side="right", padx=(8, 0))

    def _create_scrollable_area(self):
        """Crea el área scrollable."""
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.canvas = tk.Canvas(container, highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

    def _create_flags_section(self):
        """Crea la sección de checkboxes de control de llamada."""
        container = ttk.Frame(self.scrollable_frame)
        container.pack(fill="x", padx=8, pady=(4, 6))
        
        flags = [
            ("Saludo", self.saludo_var),
            ("Sondeo", self.sondeo_var),
            ("Empatía", self.empatia_var),
            ("Titularidad", self.titularidad_var),
            ("Oferta", self.oferta_var),
            ("Proceso", self.proceso_var),
            ("Encuesta", self.encuesta_var),
        ]
        
        row1 = ttk.Frame(container)
        row1.pack(fill='x')
        row2 = ttk.Frame(container)
        row2.pack(fill='x')
        
        for i, (label, var) in enumerate(flags):
            parent = row1 if i < 4 else row2
            cb = ttk.Checkbutton(parent, text=label, variable=var)
            cb.pack(side='left', padx=(4, 6), pady=2)

    def _create_client_form(self):
        """Crea el formulario de datos del cliente con iconos azules."""
        ttk.Label(self.scrollable_frame, text="Datos del Cliente", font=Config.Fonts.H1).pack(anchor='w', padx=8, pady=(4, 2))
        
        form_container = ttk.Frame(self.scrollable_frame)
        form_container.pack(fill="both", expand=True, pady=(0, 8), padx=8)
        
        form_frame = ttk.Frame(form_container)
        form_frame.pack(fill="x")
        form_frame.grid_columnconfigure(1, weight=1)
        
        # Campos ordenados como en la imagen: Teléfono, SN, Nombre, DNI
        self.numero_entry = self._create_form_row(form_frame, 0, "📞", self.numero_var, 'Teléfono de contacto')
        self.sn_entry = self._create_form_row(form_frame, 1, "🔲", self.sn_var, 'SN')
        self.nombre_entry = self._create_form_row(form_frame, 2, "👤", self.nombre_var, 'Nombre completo')
        self.dni_entry = self._create_form_row(form_frame, 3, "🆔", self.dni_var, 'DNI del cliente')

    def _create_form_row(self, parent, row, icon, variable, placeholder):
        """Crea una fila del formulario con icono azul a la izquierda."""
        # Botón icono azul (como en la imagen)
        icon_btn = tk.Button(
            parent, text=icon, font=("Segoe UI", 10),
            bg='#0d6efd', fg='white', relief='flat',
            width=2, height=1, cursor='hand2',
            command=lambda: self._copy_to_clipboard(variable.get())
        )
        icon_btn.grid(row=row, column=0, sticky="w", pady=(0, 6), padx=(0, 4))
        
        # Entry
        entry = ttk.Entry(parent, textvariable=variable, font=Config.Fonts.DEFAULT, width=25)
        entry.grid(row=row, column=1, sticky="ew", pady=(0, 6))
        
        # Placeholder
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                entry.config(foreground='#212529')
        
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.config(foreground='#888888')
        
        entry.bind('<FocusIn>', on_focus_in)
        entry.bind('<FocusOut>', on_focus_out)
        entry.insert(0, placeholder)
        entry.config(foreground='#888888')
        
        return entry

    def _create_call_reason_section(self):
        """Crea la sección de motivo de llamada."""
        ttk.Label(self.scrollable_frame, text="Motivo de llamada", font=Config.Fonts.H1).pack(anchor='w', padx=8, pady=(4, 2))
        
        container = ttk.Frame(self.scrollable_frame)
        container.pack(fill="both", expand=True, pady=(0, 8), padx=8)
        
        frame = ttk.Frame(container)
        frame.pack(fill="x")
        
        motivo_values = self._get_normalized_motivos()
        self.motivo_combo = ttk.Combobox(frame, textvariable=self.motivo_var, values=motivo_values,
                                         state="readonly", font=Config.Fonts.DEFAULT)
        self.motivo_combo.pack(side="left", fill="x", expand=True)
        self._disable_mousewheel_on(self.motivo_combo)

    def _create_action_buttons(self):
        """Crea los botones de acción."""
        frame = ttk.Frame(self.scrollable_frame)
        frame.pack(fill="x", pady=(4, 10), padx=8)
        
        ttk.Button(frame, text="Agregar Cliente", command=self._add_client).pack(side="left", padx=(0, 10))
        ttk.Button(frame, text="Limpiar", command=self._clear_form).pack(side="left")

    def _create_notes_section(self):
        """Crea la sección de notas."""
        ttk.Label(self.scrollable_frame, text="Notas", font=Config.Fonts.H1).pack(anchor='w', padx=8, pady=(4, 2))
        
        container = ttk.Frame(self.scrollable_frame)
        container.pack(fill="both", expand=True, pady=(0, 8), padx=8)
        
        theme_colors = Config.THEMES[self.current_theme]
        self.template_text = tk.Text(
            container, height=8, wrap="word", font=Config.Fonts.DEFAULT,
            relief="flat", borderwidth=2, background=theme_colors['notes_bg'],
            foreground=theme_colors['fg'], insertbackground=theme_colors['accent']
        )
        self.template_text.pack(fill="both", expand=True)
        
        ttk.Button(self.scrollable_frame, text="Copiar Plantilla",
                  command=lambda: self._copy_to_clipboard(self.template_text.get(1.0, tk.END))).pack(fill="x", pady=(5, 0))

    def _create_tnps_section(self):
        """Crea la sección de TNPS."""
        ttk.Label(self.scrollable_frame, text="TNPS", font=Config.Fonts.H1).pack(anchor='w', padx=8, pady=(4, 2))
        
        container = ttk.Frame(self.scrollable_frame)
        container.pack(fill="both", expand=True, pady=(0, 8), padx=8)
        
        frame = ttk.Frame(container)
        frame.pack(fill="x")
        
        ttk.Label(frame, text="TNPS:", font=Config.Fonts.DEFAULT_BOLD).pack(side="left")
        
        self.tnps_combo = ttk.Combobox(frame, textvariable=self.tnps_var,
                                       values=[str(i) for i in range(10)], state="readonly", width=5)
        self.tnps_combo.pack(side="left", padx=(5, 5))
        self._disable_mousewheel_on(self.tnps_combo)
        
        ttk.Button(frame, text="Guardar TNPS", command=self._save_tnps_action).pack(side="left", padx=(0, 5))
        ttk.Button(frame, text="📋", style='Copy.TButton', width=3, command=self._copy_tnps).pack(side="left")
        
        self.tnps_resultado = ttk.Label(container, text="", font=Config.Fonts.DEFAULT_BOLD)
        self.tnps_resultado.pack(anchor="w", pady=(0, 5))

    def _create_theme_button(self):
        """Crea el botón de cambio de tema."""
        ttk.Button(self.scrollable_frame, text="Cambiar Tema", command=self._toggle_theme).pack(pady=10)

    def _initialize_modal_manager(self):
        """Inicializa el gestor de modales."""
        context = {
            'template_text': self.template_text,
            'nombre_var': self.nombre_var,
            'numero_var': self.numero_var,
            'sn_var': self.sn_var,
            'dni_var': self.dni_var,
            'save_client': save_client,
            'get_credential': get_credential,
            'set_credential': set_credential,
            'position_modal': self._position_modal,
            'disable_mousewheel_on': self._disable_mousewheel_on,
            'current_theme': self.current_theme
        }
        try:
            self.modal_manager = ModalManager(self.root, context)
        except Exception as e:
            print(f"[ERROR] Failed to initialize ModalManager: {e}")
            self.modal_manager = None

    def _setup_event_bindings(self):
        """Configura los bindings de eventos."""
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Enter>", self._bind_mousewheel_to_canvas)
        self.canvas.bind("<Leave>", self._unbind_mousewheel_from_canvas)
        self.nombre_var.trace_add("write", self._update_saludo)
        self.numero_var.trace_add("write", lambda *a: self._start_timer())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_background_tasks(self):
        """Inicia las tareas en segundo plano."""
        self._check_db_status()
        self._clipboard_watcher()
        self._start_standup_reminder()
        self._update_template()

    # ==================== Métodos de tema ====================

    def _apply_theme(self, theme_name):
        """Aplica un tema visual."""
        theme = Config.THEMES[theme_name]
        
        self.root.configure(bg=theme['bg'])
        self.style.configure('.', background=theme['bg'], foreground=theme['fg'])
        self.style.configure('TFrame', background=theme['bg'])
        self.style.configure('TLabel', background=theme['bg'], foreground=theme['fg'], font=Config.Fonts.H2)
        self.style.configure('TCheckbutton', background=theme['bg'], foreground=theme['fg'], font=Config.Fonts.DEFAULT)
        
        self.style.configure('TButton', font=Config.Fonts.DEFAULT_BOLD, relief='flat',
                           borderwidth=0, padding=(12, 6), background=theme['accent'],
                           foreground=Config.Colors.WHITE)
        self.style.map('TButton', background=[('active', theme['accent_hover']), ('pressed', theme['accent_pressed'])])
        
        self.style.configure('Copy.TButton', font=Config.Fonts.COPY_BUTTON, padding=(4, 2),
                           background=theme['accent'], foreground=Config.Colors.WHITE)
        
        self.style.configure('TEntry', fieldbackground=theme['input_bg'], foreground=theme['fg'],
                           font=Config.Fonts.DEFAULT, padding=(8, 6), relief='flat', borderwidth=1)
        self.style.configure('TCombobox', fieldbackground=theme['input_bg'], foreground=theme['fg'],
                           font=Config.Fonts.DEFAULT, padding=(8, 6))
        
        border_color = theme.get('border', theme.get('subtle', '#CCCCCC'))
        self.style.map('TEntry', bordercolor=[('focus', theme['accent']), ('!focus', border_color)])
        self.style.map('TCombobox', bordercolor=[('focus', theme['accent']), ('!focus', border_color)])
        
        self.style.configure('TScrollbar', troughcolor=theme['bg'],
                           background=theme.get('pane_bg', theme.get('subtle', '#CCCCCC')),
                           borderwidth=0, arrowsize=0, relief='flat')
        self.style.map('TScrollbar', background=[('active', theme['accent'])])
        
        if hasattr(self, 'canvas'):
            self.canvas.config(bg=theme.get('pane_bg', theme['bg']))
        if hasattr(self, 'template_text'):
            self.template_text.config(background=theme['notes_bg'], foreground=theme['fg'],
                                     insertbackground=theme['accent'])
        if hasattr(self, 'saludo_label'):
            self.saludo_label.master.config(bg=theme['saludo_bg'])
            self.saludo_label.config(bg=theme['saludo_bg'], fg=theme['saludo_fg'])

    def _toggle_theme(self):
        """Alterna entre temas claro y oscuro."""
        self.current_theme = 'dark' if self.current_theme == 'modern' else 'modern'
        self._apply_theme(self.current_theme)
        if self.modal_manager:
            self.modal_manager.ctx['current_theme'] = self.current_theme

    def _open_settings_modal(self):
        """Abre el modal de ajustes."""
        modal = tk.Toplevel(self.root)
        modal.title("Ajustes")
        modal.transient(self.root)
        modal.grab_set()
        modal.resizable(False, False)
        
        theme = Config.THEMES[self.current_theme]
        modal.configure(bg=theme['bg'])
        
        # Frame principal
        main_frame = ttk.Frame(modal)
        main_frame.pack(fill='both', expand=True, padx=16, pady=16)
        
        # Tema
        ttk.Label(main_frame, text="Tema", font=Config.Fonts.H2).pack(anchor='w', pady=(0, 8))
        
        theme_frame = ttk.Frame(main_frame)
        theme_frame.pack(fill='x', pady=(0, 16))
        
        ttk.Button(theme_frame, text="☀️ Claro", 
                  command=lambda: self._apply_theme_from_settings('modern')).pack(side='left', padx=(0, 8))
        ttk.Button(theme_frame, text="🌙 Oscuro",
                  command=lambda: self._apply_theme_from_settings('dark')).pack(side='left')
        
        # Botón cerrar
        ttk.Button(main_frame, text="Cerrar", command=modal.destroy).pack(pady=(16, 0))
        
        # Posicionar modal
        self._position_modal(modal, width=250, height=120)

    def _apply_theme_from_settings(self, theme_name):
        """Aplica un tema desde el modal de ajustes."""
        self.current_theme = theme_name
        self._apply_theme(theme_name)
        if self.modal_manager:
            self.modal_manager.ctx['current_theme'] = theme_name

    # ==================== Métodos de eventos ====================

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.window_id, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _bind_mousewheel_to_canvas(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel_from_canvas(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _disable_mousewheel_on(self, widget):
        widget.bind('<MouseWheel>', lambda e: 'break')

    # ==================== Métodos de timer ====================

    def _update_saludo(self, *args):
        nombre = self.nombre_var.get().strip()
        # No actualizar si es el placeholder
        if nombre == 'Nombre completo' or not nombre:
            nombre = 'Nombre completo'
        saludo = get_saludo_dinamico(nombre)
        self.saludo_label.config(text=saludo)
        # Solo iniciar timer si hay datos reales (no placeholder)
        self._try_start_timer()

    def _has_real_data(self):
        """Verifica si hay datos reales (no placeholders) en los campos."""
        nombre = self.nombre_var.get().strip()
        numero = self.numero_var.get().strip()
        
        nombre_real = nombre and nombre != 'Nombre completo'
        numero_real = numero and numero != 'Teléfono de contacto'
        
        return nombre_real or numero_real

    def _try_start_timer(self):
        """Intenta iniciar el timer solo si hay datos reales."""
        if self._has_real_data() and not self.timer_running:
            self.timer_running = True
            self.timer_seconds = 0
            self._update_timer()

    def _start_timer(self):
        if self._has_real_data() and not self.timer_running:
            self.timer_running = True
            self.timer_seconds = 0
            self._update_timer()

    def _stop_timer(self):
        self.timer_running = False
        self.alert_10min_shown = False

    def _update_timer(self):
        if self.timer_running:
            self.timer_seconds += 1
            minutes, seconds = divmod(self.timer_seconds, 60)
            self.timer_var.set(f"{minutes:02d}:{seconds:02d}")
            
            color = Config.Colors.RED if self.timer_seconds >= Config.Timers.CALL_TIMER_WARNING_S else Config.Colors.BLACK
            self.timer_label.config(foreground=color)
            
            if self.timer_seconds == Config.Timers.CALL_TIMER_ALERT_S and not self.alert_10min_shown:
                notification.notify(title="Alerta de Llamada",
                                  message="La llamada ha superado los 10 minutos", timeout=5)
                self.alert_10min_shown = True
            
            self.root.after(1000, self._update_timer)

    # ==================== Métodos de cliente ====================

    def _validate_inputs(self):
        """Valida los campos de entrada. Retorna (is_valid, error_message)."""
        errors = []
        
        # Obtener valores limpios (sin placeholders)
        telefono = self.numero_var.get().strip()
        if telefono == 'Teléfono de contacto':
            telefono = ''
        dni = self.dni_var.get().strip()
        if dni == 'DNI del cliente':
            dni = ''
        sn = self.sn_var.get().strip()
        if sn == 'SN':
            sn = ''
        nombre = self.nombre_var.get().strip()
        if nombre == 'Nombre completo':
            nombre = ''
        
        # Validar teléfono (9 dígitos)
        if telefono and not re.match(r'^\d{9}$', telefono):
            errors.append('Teléfono debe tener 9 dígitos')
        
        # Validar DNI (8 dígitos)
        if dni and not re.match(r'^\d{8}$', dni):
            errors.append('DNI debe tener 8 dígitos')
        
        # Validar SN (alfanumérico, mínimo 5 caracteres)
        if sn and not re.match(r'^[A-Za-z0-9]{5,}$', sn):
            errors.append('SN debe ser alfanumérico (mín. 5 caracteres)')
        
        return (len(errors) == 0, '\n'.join(errors))

    def _add_client(self, open_modal=True):
        """Abre el modal correspondiente al motivo seleccionado."""
        nombre = self.nombre_var.get()
        motivo = self.motivo_var.get()
        
        if motivo == 'Atención técnica':
            self.modal_manager.open_tecnica_modal()
            return
        
        if nombre and motivo != "Selecciona motivo...":
            if open_modal and motivo == "Retención":
                self.modal_manager.open_retencion_modal()
            elif open_modal and motivo == "Cuestionamiento de recibo":
                self.modal_manager.open_cuestionamiento_modal()
            elif open_modal:
                def guard_cb(extra_notas):
                    motivo_norm = (motivo or '').strip().lower()
                    if motivo_norm == 'otros':
                        notas = extra_notas.strip()
                    else:
                        notas = (self.template_text.get(1.0, tk.END).strip() + '\n' + extra_notas).strip()
                    
                    self.template_text.delete(1.0, tk.END)
                    self.template_text.insert(tk.END, notas)
                    self._stop_timer()
                    self._update_template()
                
                self.modal_manager.open_motivo_modal(motivo, guard_cb)
            else:
                self._stop_timer()
                self._update_template()

    def _clear_form(self):
        """Guarda los datos y limpia el formulario."""
        # Validar antes de guardar
        is_valid, error_msg = self._validate_inputs()
        if not is_valid:
            if not messagebox.askyesno('Validación', f'Hay errores en los datos:\n\n{error_msg}\n\n¿Desea guardar de todos modos?'):
                return
        
        try:
            self._save_current_client()
        except Exception as exc:
            print(f"[WARNING] Error al guardar: {exc}")
        
        # Restaurar placeholders en los campos
        self._restore_placeholders()
        
        self.motivo_var.set("Selecciona motivo...")
        self.template_text.delete(1.0, tk.END)
        
        # Limpiar flags
        for var in (self.saludo_var, self.sondeo_var, self.empatia_var,
                   self.titularidad_var, self.oferta_var, self.proceso_var, self.encuesta_var):
            var.set(False)
        
        # Nueva sesión
        self.session = {
            'id': str(uuid.uuid4()),
            'start': time.time(),
            'active': True
        }
        
        # Resetear timer
        self.timer_var.set("00:00")
        self._stop_timer()
        self._update_template()

    def _restore_placeholders(self):
        """Restaura los placeholders en todos los campos del formulario."""
        # Lista de tuplas: (variable, placeholder, entry)
        fields = [
            (self.numero_var, 'Teléfono de contacto', self.numero_entry),
            (self.sn_var, 'SN', self.sn_entry),
            (self.nombre_var, 'Nombre completo', self.nombre_entry),
            (self.dni_var, 'DNI del cliente', self.dni_entry),
        ]
        
        for var, placeholder, entry in fields:
            var.set(placeholder)
            entry.config(foreground='#888888')

    def _save_current_client(self):
        """Guarda el cliente actual en la base de datos."""
        nombre = self.nombre_var.get().strip()
        numero = self.numero_var.get().strip()
        sn = self.sn_var.get().strip()
        dni = self.dni_var.get().strip()
        motivo = self.motivo_var.get()
        notas_base = self.template_text.get(1.0, tk.END).strip()
        
        # Verificar si hay datos para guardar
        has_data = any([nombre, numero, sn, dni, notas_base]) or (motivo and motivo != "Selecciona motivo...")
        if not has_data:
            return
        
        # Construir metadatos
        meta_lines = [f"Duración llamada: {self.timer_var.get()}"]
        
        flags = {
            'saludo': self.saludo_var, 'sondeo': self.sondeo_var,
            'empatia': self.empatia_var, 'titularidad': self.titularidad_var,
            'oferta': self.oferta_var, 'proceso': self.proceso_var, 'encuesta': self.encuesta_var
        }
        for k, v in flags.items():
            meta_lines.append(f"{k}: {'SI' if v.get() else 'NO'}")
        
        meta_lines.extend([
            f"Motivo: {motivo}",
            f"SN: {sn}",
            f"DNI: {dni}",
            f"Número: {numero}"
        ])
        
        notas_full = notas_base
        if notas_full:
            notas_full += "\n\n--- METADATOS ---\n" + "\n".join(meta_lines)
        else:
            notas_full = "--- METADATOS ---\n" + "\n".join(meta_lines)
        
        nombre_save = nombre or 'Sin nombre'
        motivo_save = motivo if motivo != "Selecciona motivo..." else 'Sin motivo'
        
        self.last_client_id = save_client(
            nombre_save, numero or None, sn or None, motivo_save,
            dni=dni or None, notas=notas_full, session_id=self.session.get('id')
        )

    def _update_template(self, event=None):
        """Actualiza la plantilla según el motivo seleccionado."""
        motivo = self.motivo_var.get()
        
        if motivo == 'Atención técnica':
            self.modal_manager.open_tecnica_modal()
            return
        
        if motivo not in ["Retención", "Cuestionamiento de recibo"]:
            self.template_text.delete(1.0, tk.END)
            self.template_text.insert(tk.END, templates.get(motivo, ""))

    def _get_normalized_motivos(self):
        """Obtiene la lista normalizada de motivos."""
        motivo_values = list(templates.keys())
        if 'Otros' not in motivo_values:
            motivo_values.append('Otros')
        if 'Atención técnica' not in motivo_values:
            motivo_values.append('Atención técnica')
        return motivo_values

    # ==================== Métodos de TNPS ====================

    def _save_tnps_action(self):
        """Guarda un registro TNPS."""
        score_str = self.tnps_var.get()
        if score_str:
            self.tnps_registros.append(int(score_str))
            save_tnps(int(score_str))
            self.tnps_var.set("")
            self._update_tnps_percentage()
        else:
            messagebox.showwarning("TNPS", "Selecciona un TNPS")

    def _update_tnps_percentage(self):
        """Actualiza el porcentaje TNPS mostrado."""
        if self.tnps_registros:
            porcentaje = calculate_tnps_percentage(self.tnps_registros)
            color = Config.Colors.GREEN if porcentaje >= 77 else Config.Colors.RED
            estado = "positivo" if porcentaje >= 77 else "negativo"
            self.tnps_resultado.config(text=f"TNPS {estado}: {porcentaje}%", foreground=color)
        else:
            self.tnps_resultado.config(text="No hay registros aún", foreground=Config.Colors.BLACK)

    def _copy_tnps(self):
        """Copia los registros TNPS al portapapeles."""
        if self.tnps_registros:
            self._copy_to_clipboard('\n'.join(map(str, self.tnps_registros)), "TNPS")
        else:
            messagebox.showwarning("TNPS", "No hay registros para copiar")

    # ==================== Métodos de utilidad ====================

    def _copy_to_clipboard(self, text, name=None):
        """Copia texto al portapapeles."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if name:
            print(f"{name} copiado al portapapeles")

    def _copy_credential(self, key, name):
        """Copia una credencial al portapapeles."""
        try:
            val = get_credential(key)
            if val:
                self._copy_to_clipboard(val, name)
            else:
                messagebox.showwarning("Vacío", f"No hay valor para {name}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener credencial: {e}")

    def _close_all_excel(self):
        """Cierra todas las instancias de Excel."""
        try:
            subprocess.run(["taskkill", "/IM", "EXCEL.EXE", "/F"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    def _position_modal(self, modal, width=None, height=None, side='right'):
        """Posiciona un modal relativo a la ventana principal."""
        self.root.update_idletasks()
        modal.update_idletasks()
        
        scr_w, scr_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        r_x, r_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        r_w, r_h = self.root.winfo_width(), self.root.winfo_height()
        m_w = width or modal.winfo_reqwidth()
        m_h = height or modal.winfo_reqheight()
        
        y = r_y + max(0, (r_h - m_h) // 2)
        x = (r_x + r_w + 8) if side == 'right' else max(0, r_x - m_w - 8)
        
        if (side == 'right' and x + m_w > scr_w) or (side != 'right' and x < 0):
            x = (r_x + r_w + 8) if x < 0 else max(0, r_x - m_w - 8)
        
        modal.geometry(f"{m_w}x{m_h}+{max(0, min(x, scr_w - m_w))}+{max(0, min(y, scr_h - m_h))}")

    # ==================== Tareas en segundo plano ====================

    def _check_db_status(self):
        """Verifica el estado de la conexión a la base de datos."""
        try:
            with get_connection() as conn:
                conn.execute("SELECT 1")
            self.db_status_var.set("DB: OK")
            self.db_status_label.config(foreground=Config.Colors.GREEN)
        except Exception:
            self.db_status_var.set("DB: Error")
            self.db_status_label.config(foreground=Config.Colors.RED)
        
        self.root.after(Config.Timers.DB_STATUS_CHECK_MS, self._check_db_status)

    def _start_standup_reminder(self):
        """Inicia el recordatorio de ponerse de pie."""
        if self.standup_timer_id is None:
            self.standup_timer_id = self.root.after(Config.Timers.STANDUP_REMINDER_MS, self._show_standup_reminder)

    def _show_standup_reminder(self):
        """Muestra el recordatorio de salud."""
        notification.notify(title="Recordatorio de Salud",
                          message="¡Levántate y estira las piernas!", timeout=10)
        self.standup_timer_id = self.root.after(Config.Timers.STANDUP_REMINDER_MS, self._show_standup_reminder)

    def _clipboard_watcher(self):
        """Vigila el portapapeles buscando datos de cliente."""
        if self.clipboard_watcher_on.get():
            try:
                clip = self.root.clipboard_get()
            except Exception:
                clip = ''
            
            if clip and clip != self.last_clip_text:
                parsed = self._parse_clipboard(clip)
                if parsed:
                    self._handle_parsed_clipboard(parsed)
                self.last_clip_text = clip
        
        self.root.after(Config.Timers.CLIPBOARD_WATCHER_MS, self._clipboard_watcher)

    def _parse_clipboard(self, text):
        """Parsea texto del portapapeles buscando datos de cliente."""
        parsed = {}
        patterns = {
            'telefono': r'(?:tel[eé]fono|numero|cel)\s*[:\-]?\s*(\d{9,})',
            'dni': r'(?:dni|documento)\s*[:\-]?\s*(\d{8})',
            'sn': r'(?:sn|serie)\s*[:\-]?\s*([A-Z0-9]{10,})',
            'nombre': r'(?:nombre|cliente)\s*[:\-]?\s*([A-Za-z\s]+)'
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parsed[key] = match.group(1).strip()
        return parsed

    def _handle_parsed_clipboard(self, parsed):
        """Maneja datos parseados del portapapeles."""
        if not parsed:
            return
        
        ts = time.time()
        self.clipboard_history.insert(0, {'text': self.last_clip_text, 'parsed': parsed, 'ts': ts})
        if len(self.clipboard_history) > 50:
            self.clipboard_history.pop()
        
        if self.clip_mode == 'autofill_empty':
            if 'telefono' in parsed and not self.numero_var.get().strip():
                self.numero_var.set(parsed['telefono'])
            if 'dni' in parsed and not self.dni_var.get().strip():
                self.dni_var.set(parsed['dni'])
            if 'sn' in parsed and not self.sn_var.get().strip():
                self.sn_var.set(parsed['sn'])
            if 'nombre' in parsed and not self.nombre_var.get().strip():
                self.nombre_var.set(parsed['nombre'])

    # ==================== Cierre ====================

    def _on_close(self):
        """Maneja el cierre de la aplicación."""
        has_data = any([
            self.nombre_var.get(), self.numero_var.get(),
            self.sn_var.get(), self.dni_var.get(),
            self.motivo_var.get() != "Selecciona motivo..."
        ])
        
        if has_data and not messagebox.askyesno("Guardar datos", "¿Tienes datos sin guardar? ¿Quieres cerrar?"):
            self.root.iconify()
        else:
            self._shutdown()

    def _shutdown(self):
        """Cierra la aplicación."""
        if self.standup_timer_id:
            self.root.after_cancel(self.standup_timer_id)
        self.root.destroy()

    def run(self):
        """Inicia el loop principal."""
        self.root.mainloop()


def run_app():
    """Función de entrada principal."""
    try:
        root = tk.Tk()
        app = App(root)
        app.run()
    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ERROR] Excepción fatal: {tb}")
        messagebox.showerror("Error Fatal", f"Ocurrió un error irrecuperable:\n{e}")


if __name__ == '__main__':
    run_app()
