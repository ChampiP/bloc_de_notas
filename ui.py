import tkinter as tk
from tkinter import ttk, messagebox
from plyer import notification
import subprocess
from db import connect_db, save_client, save_tnps
from templates import templates
from utils import get_saludo_personalizado, evaluar_tnps
from modales import ModalManager

def run_app():
    print("[DEBUG] run_app() iniciado")
    import tkinter.messagebox as tkmb
    try:
        # Removido el showinfo de debug para que no bloquee la interfaz
        # tkmb.showinfo("Depuración", "La app inició run_app() correctamente")
        
        # Definir variables globales al inicio
        timer_running = False
        timer_seconds = 0
        alert_10min_shown = False
        standup_timer_id = None
        last_client_id = None
        tnps_registros = []
        current_theme = 'modern'
        style = None
        
        # Crear la ventana principal primero
        root = tk.Tk()
        root.title("Aplicación de Escritorio - Clientes")
        root.geometry("324x600")  # Tamaño inicial
        root.resizable(True, True)
        root.attributes('-topmost', True)  # Siempre encima

        style = ttk.Style()
        style.theme_use('clam')  # Tema moderno
        current_theme = 'modern'

        style.configure('Ajuste.TEntry', fieldbackground='lightblue', borderwidth=2, relief='solid')
        # Contenedor de iconos cargados para evitar que PhotoImage sea recolectado
        root._icons = {}

        def load_icon(name, size=(20,20)):
            """Intenta cargar assets/icons/{name}.png y los guarda en root._icons. Devuelve PhotoImage o None."""
            import os
            path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', f"{name}.png")
            if not os.path.exists(path):
                return None
            try:
                img = tk.PhotoImage(file=path)
                # opcional: redimensionar no trivial con PhotoImage; asume PNG ya con tamaño adecuado
                root._icons[name] = img
                return img
            except Exception:
                return None

        def create_icon_button(parent, icon_name=None, emoji_text=None, **kwargs):
            """Crea un ttk.Button que usa una imagen si existe, o texto emoji como fallback.
            Retorna el widget Button creado (no empaqueta automáticamente).
            """
            img = None
            if icon_name:
                img = load_icon(icon_name)
            if img:
                btn = ttk.Button(parent, image=img, command=kwargs.get('command'), style=kwargs.get('style', 'Copy.TButton'))
            else:
                text = emoji_text or icon_name or ''
                btn = ttk.Button(parent, text=text, command=kwargs.get('command'), style=kwargs.get('style', 'Copy.TButton'))
            return btn

        def apply_modern_theme():
            # Tema moderno (claro): limpio, profesional y de alta visibilidad
            bg = '#f8f9fa'          # Soft background for main window
            fg = "#000000"          # Dark text for high contrast
            input_bg = '#ffffff'    # White inputs
            accent = '#007acc'      # Blue accent (consistent with dark)
            subtle = '#e9ecef'      # Subtle borders/separators

            root.configure(bg=bg)
            style.configure('TFrame', background=bg, relief='flat')
            style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI', 11))
            style.configure('TButton', font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, padding=(12,6))
            # Botón grande apilado (estilo para la columna de opciones tipo la captura)
            style.configure('Big.TButton', font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=1, padding=(8,10), background='#f0f0f0')
            style.map('TButton', background=[('active', accent), ('pressed', '#005a9e')], foreground=[('!disabled', 'white')])
            # Primary accent button for modern theme
            style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), background=accent, foreground='white', padding=(12,6))
            style.map('Accent.TButton', background=[('active', '#005a9e'), ('pressed', '#004275')])
            style.configure('TEntry', fieldbackground=input_bg, foreground=fg, borderwidth=2, relief='flat', font=('Segoe UI', 10), padding=(8,6))
            style.configure('TCombobox', fieldbackground=input_bg, foreground=fg, font=('Segoe UI', 10), padding=(8,6))
            style.configure('TCheckbutton', background=bg, foreground=fg, font=('Segoe UI', 10))
            style.configure('TScrollbar', background='#bdc3c7', troughcolor=subtle)
            # Asegurar que los widgets Text sigan el tema moderno si existen
            try:
                t = locals().get('template_text')
                if t is not None:
                    t.config(background="#fffbe6", foreground="#000000", insertbackground='#007acc')
            except Exception:
                pass

        def apply_dark_theme():
            # Tema moderno (oscuro): armónico, de alta visibilidad y aspecto profesional (inspirado en VS Code)
            bg = '#1e1e1e'          # Deep background for main window
            pane_bg = '#121212'     # Much darker for panels and canvas
            input_bg = '#1b1b1b'    # Darker input fields background
            fg = '#e6e6e6'          # Primary text color (soft white)
            subtle_fg = '#999999'   # Subtle text for hints/help
            border = '#454545'      # Borders and separators
            accent = '#007acc'      # Soft blue accent (professional, visible)
            accent_hover = '#005a9e' # Hover state
            accent_pressed = '#004275' # Pressed state

            root.configure(bg=bg)
            style.theme_use('clam')
            style.configure('.', background=bg, foreground=fg, bordercolor=border)
            style.configure('TFrame', background=bg)
            style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI', 11))
            style.configure('TCheckbutton', background=bg, foreground=fg, font=('Segoe UI', 10))
            style.map('TCheckbutton',
                indicatorcolor=[('selected', accent), ('active', accent_hover)],
                background=[('active', bg)]
            )
            style.configure('TSeparator', background=border)

            # Estilo de botón: apariencia acolchada y padding para mantener armonía
            style.configure('TButton', font=('Segoe UI', 10, 'bold'),
                            background=accent, foreground='white',
                            borderwidth=0, padding=(12, 8), relief='flat')
            style.map('TButton',
                background=[('pressed', accent_pressed), ('active', accent_hover)],
                foreground=[('!disabled', 'white')]
            )
            # Botón de copiar: más pequeño y sutil
            style.configure('Copy.TButton', font=('Segoe UI', 9), padding=(4,2), background=accent, foreground='white')
            style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), background=accent, foreground='white', padding=(12,8))

            # Entry/Combobox: limpio y de alto contraste
            style.configure('TEntry', fieldbackground=input_bg, foreground=fg,
                            borderwidth=1, relief='flat', font=('Segoe UI', 10), padding=(8, 6))
            style.map('TEntry',
                bordercolor=[('focus', accent), ('!focus', border)],
                fieldbackground=[('focus', input_bg)]
            )
            style.configure('TCombobox',
                fieldbackground=input_bg,
                foreground=fg,
                arrowcolor=fg,
                background=input_bg,
                borderwidth=0,
                padding=(8, 6),
                font=('Segoe UI', 10))
            style.map('TCombobox',
                bordercolor=[('focus', accent), ('!focus', border)],
                fieldbackground=[('readonly', input_bg), ('focus', input_bg)],
                selectbackground=[('readonly', input_bg)],
                selectforeground=[('readonly', fg)]
            )

            # Barra de desplazamiento: sutil y moderna
            style.configure('TScrollbar',
                background=pane_bg,
                troughcolor=bg,
                borderwidth=0,
                arrowsize=0,
                relief='flat'
            )
            style.map('TScrollbar',
                background=[('active', subtle_fg)]
            )

            # Canvas/paneles: fondo consistente para paneles
            try:
                c = locals().get('canvas')
                if c is not None:
                    c.config(bg=pane_bg)
            except Exception:
                pass

            # Widgets Text: alta legibilidad con el fondo de panel
            try:
                t = locals().get('template_text')
                if t is not None:
                    # Usar un fondo más profundo para el área principal de notas y reducir el contraste
                    t.config(background='#0f1112', foreground=fg, insertbackground=accent)
            except Exception:
                pass
            for name in ('info_text', 'otros_text', 'obs_text', 'extra_text', 'solucion_text'):
                try:
                    w = locals().get(name)
                    if w is not None:
                        # Mantener widgets auxiliares ligeramente más claros que el fondo profundo de notas
                        w.config(background=input_bg, foreground=fg, insertbackground=accent)
                except Exception:
                    pass

            # Labels de saludo y estado: acento para el saludo, color verde para el estado
            try:
                if 'saludo_label' in locals():
                    saludo_label.config(bg=bg, fg=accent)
            except Exception:
                pass
            try:
                if 'db_status_label' in locals():
                    db_status_label.config(foreground='#4caf50')  # Green for OK
            except Exception:
                pass

        def toggle_theme():
            nonlocal current_theme
            if current_theme == 'modern':
                apply_dark_theme()
                current_theme = 'dark'
            else:
                apply_modern_theme()
                current_theme = 'modern'
            # Actualizar el tema en el administrador de modales
            if modal_manager:
                modal_manager.ctx['current_theme'] = current_theme

        apply_modern_theme()

        # Estilos adicionales: boton de copiar pequeño y label de saludo resaltado
        style.configure('Copy.TButton', font=('Segoe UI', 9), padding=(4,2))

        def close_all_excel():
            """Cerrar todos los procesos de Excel (Windows)."""
            try:
                subprocess.run(["taskkill", "/IM", "EXCEL.EXE", "/F"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("Todos los procesos de Excel han sido terminados.")
            except subprocess.CalledProcessError as e:
                print(f"No se pudieron cerrar todos los procesos de Excel o no había procesos: {e}")
            except Exception as e:
                print(f"Error al intentar cerrar Excel: {e}")

        # Header (replacing the big framed box) to keep a cleaner look
        header_frame = ttk.Frame(root)
        header_frame.pack(fill="x", padx=8, pady=(8,0))
        # Title removed per user request (was: 'Gestión de Atención')

        # Move credentials buttons to the header (top-right)
        creds_frame = ttk.Frame(header_frame)
        creds_frame.pack(side='right')
        # Usar iconos concretos si existen en assets/icons/*.png, sino usar emojis como fallback
        create_icon_button(creds_frame, icon_name='lista', emoji_text='📄', command=lambda: modal_manager.open_lista_atenciones_modal() if 'modal_manager' in locals() or 'modal_manager' in globals() else None).pack(side='right', padx=(4,2))
        create_icon_button(creds_frame, icon_name='vpn', emoji_text='🔒', command=lambda: copy_credential('vpn_password', 'VPN')).pack(side='right', padx=(2,0))
        create_icon_button(creds_frame, icon_name='siac', emoji_text='🔑', command=lambda: copy_credential('siac_password', 'SIAC')).pack(side='right', padx=(2,0))
        create_icon_button(creds_frame, icon_name='edit', emoji_text='✏️', command=lambda: open_credentials_modal()).pack(side='right', padx=(2,6))
        # Button to close all open Excel processes (Windows)
        create_icon_button(creds_frame, icon_name='excel_close', emoji_text='🗙', command=close_all_excel).pack(side='right', padx=(6,2))

        # Top frame para saludo y timer
        top_frame = ttk.Frame(root)
        top_frame.pack(fill="x", pady=(4,8), padx=8)

        # Contenedor para todo el contenido scrollable
        container = ttk.Frame(root)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # Variables
        nombre_var = tk.StringVar()
        numero_var = tk.StringVar()
        sn_var = tk.StringVar()
        dni_var = tk.StringVar()
        timer_var = tk.StringVar(value="00:00")

        # Cargar TNPS del día actual desde DB (en try separado para no fallar la UI)
        try:
            conn = connect_db()
            with conn.cursor() as cursor:
                cursor.execute("SELECT tnps_score FROM tnps WHERE DATE(fecha_tnps) = CURDATE()")
                tnps_registros = [row['tnps_score'] for row in cursor.fetchall()]
            conn.close()
        except Exception as db_error:
            print(f"[WARNING] Error al cargar TNPS: {db_error}. Continuando sin datos de TNPS.")
            tnps_registros = []

        # Canvas and scrollbar for scrolling (responsive)
        canvas = tk.Canvas(container, bg="#eaeaea", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scrollable frame
        scrollable_frame = ttk.Frame(canvas)
        # create window and keep reference to item id so we can update its width on resize
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def _on_frame_configure(event):
            # update scrollregion when the inner frame changes size
            canvas.configure(scrollregion=canvas.bbox("all"))

        scrollable_frame.bind("<Configure>", _on_frame_configure)

        # Keep inner window width in sync with canvas width so widgets don't get cut off
        def _on_canvas_configure(event):
            try:
                canvas.itemconfigure(window_id, width=event.width)
            except Exception:
                pass
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _on_canvas_configure)

        # Mouse wheel binding (Windows) — solo activa el scroll global cuando
        # el cursor está dentro del canvas para evitar que Combobox cambie
        # su selección al scrollear.
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        def _bind_mousewheel_to_canvas(event):
            try:
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            except Exception:
                pass

        def _unbind_mousewheel_from_canvas(event):
            try:
                canvas.unbind_all("<MouseWheel>")
            except Exception:
                pass

        canvas.bind("<Enter>", _bind_mousewheel_to_canvas)
        canvas.bind("<Leave>", _unbind_mousewheel_from_canvas)

        # Helper: evitar que el mousewheel cambie la selección de Comboboxs cuando se scrollea
        def disable_mousewheel_on(widget):
            try:
                # Ensure widget handles mousewheel first to prevent global canvas bindings from changing selection
                # Put the widget itself at the front of its bindtags
                current = widget.bindtags()
                if current and current[0] != str(widget):
                    widget.bindtags((str(widget),) + current)
                # We'll allow wheel events only after an explicit click on the widget.
                # Use a small per-widget flag that is set when the widget is clicked
                # and cleared on focus out.
                try:
                    setattr(widget, '_wheel_enabled', False)
                except Exception:
                    pass

                def _enable_on_click(event=None):
                    try:
                        setattr(widget, '_wheel_enabled', True)
                    except Exception:
                        pass

                def _disable_on_focusout(event=None):
                    try:
                        setattr(widget, '_wheel_enabled', False)
                    except Exception:
                        pass

                def _wheel_handler(event):
                    try:
                        if getattr(widget, '_wheel_enabled', False):
                            # allow normal processing
                            return None
                    except Exception:
                        pass
                    return 'break'

                # enable after mouse click (user explicit interaction)
                widget.bind('<Button-1>', _enable_on_click, add='+')
                # disable when the widget loses focus
                widget.bind('<FocusOut>', _disable_on_focusout, add='+')

                widget.bind('<MouseWheel>', _wheel_handler)
                widget.bind('<Button-4>', _wheel_handler)
                widget.bind('<Button-5>', _wheel_handler)
            except Exception:
                pass

        # Saludo simplificado y resaltado: "Buenas noches, Sr. {Nombre}"
        # Fondo del saludo en modo claro usa un acento muy sutil para mejorar apariencia
        saludo_color = '#e7f3ff' if current_theme == 'modern' else '#1e1e1e'
        saludo_fg = '#154a6b' if current_theme == 'modern' else '#007acc'
        saludo_bg = tk.Frame(top_frame, bg=saludo_color, bd=0)
        saludo_bg.pack(side='left', padx=(0,4))
        saludo_label = tk.Label(saludo_bg, text=f"Buenas noches, Sr. {nombre_var.get() or 'Cliente'}", wraplength=260, justify="center", font=("Segoe UI", 11, "bold"), bg=saludo_color, fg=saludo_fg, padx=6, pady=4)
        saludo_label.pack()

        # Timer
        timer_label = ttk.Label(top_frame, textvariable=timer_var, font=("Segoe UI", 10))
        timer_label.pack(side="right")

        # Indicador de estado de la base de datos (arranca como desconocido)
        db_status_var = tk.StringVar(value="DB: ?")
        db_status_label = ttk.Label(top_frame, textvariable=db_status_var, font=("Segoe UI", 9, "bold"))
        db_status_label.pack(side="right", padx=(8,0))

        # Credenciales: asegurar tabla y cargar valores
        try:
            from db import ensure_credentials_table, get_credential, set_credential
            ensure_credentials_table()
        except Exception as cred_err:
            print(f"[WARNING] No se pudo asegurar tabla de credenciales: {cred_err}")

        # Helper para copiar credenciales al portapapeles
        def copy_credential(key, friendly_name=None):
            try:
                val = get_credential(key)
                if val:
                    root.clipboard_clear()
                    root.clipboard_append(val)
                    # popup eliminado: copiar al portapapeles silenciosamente
                    print(f"{friendly_name or key} copiado al portapapeles")
                else:
                    messagebox.showwarning("Vacío", f"No hay valor guardado para {friendly_name or key}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al obtener credencial: {e}")

        

    # (moved) creds_frame defined in header_frame above

        def check_db_status():
            try:
                conn = connect_db()
                conn.close()
                db_status_var.set("DB: OK")
                db_status_label.config(foreground='green')
            except Exception:
                db_status_var.set("DB: Offline")
                db_status_label.config(foreground='red')
            # programar para que se ejecute cada 10 segundos
            root.after(10000, check_db_status)

        # iniciar la comprobación periódica
        check_db_status()

        # Helper para posicionar modales al lado de la ventana principal
        def position_modal(modal, width=None, height=None, side='right'):
            try:
                root.update_idletasks()
                # let the modal compute its requested size if width/height not provided
                try:
                    modal.update_idletasks()
                except Exception:
                    pass

                req_w = modal.winfo_reqwidth() or 0
                req_h = modal.winfo_reqheight() or 0

                screen_w = root.winfo_screenwidth()
                screen_h = root.winfo_screenheight()
                root_x = root.winfo_rootx()
                root_y = root.winfo_rooty()
                root_w = root.winfo_width()
                root_h = root.winfo_height()

                # final width/height
                final_w = width if width is not None else max(300, req_w)
                final_h = height if height is not None else max(120, req_h)

                # prefer center vertically relative to root
                y = root_y + max(0, (root_h - final_h) // 2)
                if side == 'right':
                    x = root_x + root_w + 8
                    if x + final_w > screen_w:
                        x = max(0, root_x - final_w - 8)
                else:
                    x = max(0, root_x - final_w - 8)
                    if x < 0:
                        x = root_x + root_w + 8

                # ensure within screen
                x = max(0, min(x, screen_w - final_w))
                y = max(0, min(y, screen_h - final_h))

                modal.geometry(f"{final_w}x{final_h}+{x}+{y}")
            except Exception:
                try:
                    if width is not None and height is not None:
                        modal.geometry(f"{width}x{height}")
                except Exception:
                    pass

        def update_saludo(*args):
            # Mostrar solo "Buenas noches, Sr. {nombre}" y resaltar
            nombre = nombre_var.get().strip() or 'Cliente'
            saludo_label.config(text=f"Buenas noches, Sr. {nombre}")
            start_timer()

        def start_timer():
            nonlocal timer_running, timer_seconds
            # start timer if either nombre or numero has content
            try:
                has_name = bool(nombre_var.get().strip())
            except Exception:
                has_name = False
            try:
                has_num = bool(numero_var.get().strip())
            except Exception:
                has_num = False

            if (has_name or has_num) and not timer_running:
                timer_running = True
                timer_seconds = 0
                update_timer()

        def stop_timer():
            nonlocal timer_running, alert_10min_shown
            timer_running = False
            alert_10min_shown = False

        def start_standup_reminder():
            nonlocal standup_timer_id
            if standup_timer_id is None:
                standup_timer_id = root.after(3600000, show_standup_reminder)  # 1 hour

        def show_standup_reminder():
            nonlocal standup_timer_id
            notification.notify(
                title="Recordatorio de Salud",
                message="¡Levántate y estira las piernas! El trabajo cansa estar sentado.",
                timeout=10
            )
            standup_timer_id = root.after(3600000, show_standup_reminder)

        def update_timer():
            nonlocal timer_seconds, alert_10min_shown
            if timer_running:
                timer_seconds += 1
                minutes = timer_seconds // 60
                seconds = timer_seconds % 60
                timer_var.set(f"{minutes:02d}:{seconds:02d}")
                if timer_seconds >= 420:  # 7 minutes
                    timer_label.config(foreground="red")
                else:
                    timer_label.config(foreground="black")
                if timer_seconds == 600:  # 10 minutes
                    notification.notify(
                        title="Alerta de Llamada",
                        message="La llamada ha superado los 10 minutos",
                        timeout=5
                    )
                    alert_10min_shown = True
                root.after(1000, update_timer)

        nombre_var.trace_add("write", update_saludo)
        # start timer also when the numero field gets data
        try:
            numero_var.trace_add("write", lambda *a: start_timer())
        except Exception:
            pass

        # Separator
        sep1 = ttk.Separator(scrollable_frame, orient='horizontal')
        sep1.pack(fill='x', pady=3)

        # Encabezado: Datos del Cliente (sin marco)
        ttk.Label(scrollable_frame, text="Datos del Cliente", font=("Segoe UI", 12, "bold")).pack(anchor='w', padx=8, pady=(4,2))
        form_container = ttk.Frame(scrollable_frame)
        form_container.pack(fill="both", expand=True, pady=(0,8), padx=8)

        form_frame = ttk.Frame(form_container)
        form_frame.pack(fill="x")
        form_frame.grid_columnconfigure(0, weight=0)
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(2, weight=0)

        # Nombre
        ttk.Label(form_frame, text="Nombre:", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0,6))
        nombre_entry = ttk.Entry(form_frame, textvariable=nombre_var, font=("Segoe UI", 10), width=25)
        nombre_entry.grid(row=0, column=1, sticky="ew", pady=(0,6))
        ttk.Button(form_frame, text="📋", style='Copy.TButton', width=3, command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(nombre_var.get())
        ]).grid(row=0, column=2, sticky="e", pady=(0,12))

        # Número
        ttk.Label(form_frame, text="Número:", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", pady=(0,6))
        numero_entry = ttk.Entry(form_frame, textvariable=numero_var, font=("Segoe UI", 10), width=25)
        numero_entry.grid(row=1, column=1, sticky="ew", pady=(0,6))
        ttk.Button(form_frame, text="📋", style='Copy.TButton', width=3, command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(numero_entry.get())
        ]).grid(row=1, column=2, sticky="e", pady=(0,12))

        # SN
        ttk.Label(form_frame, text="SN:", font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w", pady=(0,6))
        sn_entry = ttk.Entry(form_frame, textvariable=sn_var, font=("Segoe UI", 10), width=25)
        sn_entry.grid(row=2, column=1, sticky="ew", pady=(0,6))
        ttk.Button(form_frame, text="📋", style='Copy.TButton', width=3, command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(sn_var.get())
        ]).grid(row=2, column=2, sticky="e", pady=(0,12))

        # DNI
        ttk.Label(form_frame, text="DNI:", font=("Segoe UI", 11, "bold")).grid(row=3, column=0, sticky="w", pady=(0,6))
        dni_entry = ttk.Entry(form_frame, textvariable=dni_var, font=("Segoe UI", 10), width=25)
        dni_entry.grid(row=3, column=1, sticky="ew", pady=(0,6))
        ttk.Button(form_frame, text="📋", style='Copy.TButton', width=3, command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(dni_var.get())
        ]).grid(row=3, column=2, sticky="e", pady=(0,12))

        # Aquí debería continuar el resto de la UI, pero como está incompleto, agregaré un placeholder
        # Para completar la app, necesito agregar más widgets: motivo, template, botones, etc.
        
        # Encabezado: Pasos del Proceso (sin marco)
        ttk.Label(scrollable_frame, text="Pasos del Proceso", font=("Segoe UI", 12, "bold")).pack(anchor='w', padx=8, pady=(4,2))
        pasos_container = ttk.Frame(scrollable_frame)
        pasos_container.pack(fill="both", expand=True, pady=(0,8), padx=8)

        pasos_frame = ttk.Frame(pasos_container)
        pasos_frame.pack(fill="x")

        saludo_var = tk.BooleanVar()
        sondeo_var = tk.BooleanVar()
        empatia_var = tk.BooleanVar()
        titularidad_var = tk.BooleanVar()
        oferta_var = tk.BooleanVar()
        proceso_var = tk.BooleanVar()
        encuesta_var = tk.BooleanVar()

        ttk.Checkbutton(pasos_frame, text="Saludo", variable=saludo_var, command=update_saludo).grid(row=0, column=0, sticky="w", padx=(0,10))
        ttk.Checkbutton(pasos_frame, text="Sondeo", variable=sondeo_var, command=update_saludo).grid(row=0, column=1, sticky="w", padx=(0,10))
        ttk.Checkbutton(pasos_frame, text="Frase Empatía", variable=empatia_var, command=update_saludo).grid(row=0, column=2, sticky="w", padx=(0,10))
        ttk.Checkbutton(pasos_frame, text="Titularidad", variable=titularidad_var, command=update_saludo).grid(row=0, column=3, sticky="w")
        ttk.Checkbutton(pasos_frame, text="Oferta Comercial", variable=oferta_var, command=update_saludo).grid(row=1, column=0, sticky="w", padx=(0,10))
        ttk.Checkbutton(pasos_frame, text="Proceso", variable=proceso_var, command=update_saludo).grid(row=1, column=1, sticky="w", padx=(0,10))
        ttk.Checkbutton(pasos_frame, text="Invitación a Encuesta", variable=encuesta_var, command=update_saludo).grid(row=1, column=2, sticky="w")

        # Encabezado: Motivo de llamada (sin marco)
        ttk.Label(scrollable_frame, text="Motivo de llamada", font=("Segoe UI", 12, "bold")).pack(anchor='w', padx=8, pady=(4,2))
        motivo_container = ttk.Frame(scrollable_frame)
        motivo_container.pack(fill="both", expand=True, pady=(0,8), padx=8)

        motivo_frame = ttk.Frame(motivo_container)
        motivo_frame.pack(fill="x")
        motivo_var = tk.StringVar(value="Selecciona motivo...")
        # include an 'Otros' option in the motivo list
        motivo_values = list(templates.keys())
        # ensure 'Otros' is available
        if 'Otros' not in motivo_values:
            motivo_values.append('Otros')

        # normalize: remove duplicates case-insensitively and remove 'Ajuste'
        seen = set()
        normalized = []
        for v in motivo_values:
            if not v:
                continue
            low = v.strip().lower()
            if low == 'ajuste':
                # remove this entry
                continue
            if low in seen:
                continue
            seen.add(low)
            # canonicalize variants of Atención técnica
            if low in ('atención técnica', 'atención tecnica', 'atencion tecnica'):
                normalized.append('Atención técnica')
            else:
                normalized.append(v)
        motivo_values = normalized
        # ensure canonical Atención técnica exists
        if not any(x.lower() == 'atención técnica' for x in motivo_values):
            motivo_values.append('Atención técnica')
        motivo_combo = ttk.Combobox(motivo_frame, textvariable=motivo_var, values=motivo_values, state="readonly", font=("Segoe UI", 10))
        motivo_combo.pack(side="left", fill="x", expand=True)
        disable_mousewheel_on(motivo_combo)

        def update_template(event=None):
            motivo = motivo_var.get()
            # Para motivos que requieren modal, abrir modal específico y no sobrescribir plantilla
            if motivo == 'Atención técnica':
                try:
                    if modal_manager:
                        modal_manager.open_tecnica_modal()
                except Exception:
                    pass
                return

            if motivo not in ["Retención", "Cuestionamiento de recibo"]:
                try:
                    template_text.delete(1.0, tk.END)
                    template_text.insert(tk.END, templates.get(motivo, ""))
                except Exception:
                    # template_text aún no creado en algunos flujos; ignorar
                    pass

        # Bind the combobox selection to the consolidated update_template
        try:
            motivo_combo.bind("<<ComboboxSelected>>", update_template)
        except Exception:
            pass

        # Llamar a los modales a través de ModalManager
        def add_client(open_modal=True):
            nonlocal last_client_id
            nombre = nombre_var.get()
            numero = numero_entry.get()
            sn = sn_var.get()
            motivo = motivo_var.get()
            # Si el motivo es Atención técnica, abrir siempre el modal correspondiente
            if motivo == 'Atención técnica':
                try:
                    if modal_manager:
                        modal_manager.open_tecnica_modal()
                except Exception:
                    pass
                return
            if nombre and motivo != "Selecciona motivo...":
                if open_modal and motivo == "Retención":
                    if modal_manager:
                        modal_manager.open_retencion_modal()
                elif open_modal and motivo == "Cuestionamiento de recibo":
                    if modal_manager:
                        modal_manager.open_cuestionamiento_modal()
                elif open_modal and motivo == "Atención técnica":
                    if modal_manager:
                        modal_manager.open_tecnica_modal()
                    return
                elif open_modal:
                    def guardar_desde_modal(extra_notas):
                        notas = (template_text.get(1.0, tk.END).strip() + '\n' + extra_notas).strip()
                        try:
                            last_id = save_client(nombre, numero, sn, motivo, dni=dni_var.get(), notas=notas)
                            print(f"Cliente guardado con ID: {last_id}")
                            stop_timer()
                            update_template()
                        except Exception as e:
                            messagebox.showerror("Error", f"Error al guardar cliente: {e}")
                    if modal_manager:
                        modal_manager.open_motivo_modal(motivo, guardar_desde_modal)
                else:
                    notas = template_text.get(1.0, tk.END).strip()
                    try:
                        last_client_id = save_client(nombre, numero, sn, motivo, dni=dni_var.get(), notas=notas)
                        print(f"Cliente guardado con ID: {last_client_id}")
                        stop_timer()
                        update_template()
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al guardar cliente: {e}")

        # Botones bajo Motivo de llamada
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill="x", pady=(4,10), padx=8)
        ttk.Button(buttons_frame, text="Agregar Cliente", command=add_client).pack(side="left", padx=(0,10))
        ttk.Button(buttons_frame, text="Limpiar", command=lambda: [
            add_client(open_modal=False) if (nombre_var.get() and motivo_var.get() != "Selecciona motivo...") else None,
            nombre_var.set(""),
            numero_var.set(""),
            sn_var.set(""),
            dni_var.set(""),
            motivo_var.set("Selecciona motivo..."),
            template_text.delete(1.0, tk.END),
            stop_timer(),
            update_template()
        ]).pack(side="left")

        # Encabezado: Notas (sin marco)
        ttk.Label(scrollable_frame, text="Notas", font=("Segoe UI", 12, "bold")).pack(anchor='w', padx=8, pady=(4,2))
        notas_container = ttk.Frame(scrollable_frame)
        notas_container.pack(fill="both", expand=True, pady=(0,8), padx=8)

        # Create template_text with colors according to current theme to avoid a very bright box in dark mode
        try:
            if current_theme == 'dark':
                tpl_bg = '#0f1112'  # Very deep background for notes in dark mode
                tpl_fg = '#e6e6e6'
            else:
                tpl_bg = '#fffbe6'
                tpl_fg = '#000000'
        except Exception:
            tpl_bg = '#fffbe6'
            tpl_fg = '#000000'

        template_text = tk.Text(notas_container, height=8, wrap="word", font=("Segoe UI", 10), relief="flat", borderwidth=2, background=tpl_bg, foreground=tpl_fg, insertbackground='#007acc')
        template_text.pack(fill="both", expand=True)
        
        update_template()  # Inicial

        # Modal manager: instantiate and pass necessary references
        try:
            modal_manager = ModalManager(root, {
                'template_text': template_text,
                'nombre_var': nombre_var,
                'numero_var': numero_var,
                'sn_var': sn_var,
                'dni_var': dni_var,
                'numero_entry': numero_entry,
                'save_client': save_client,
                'position_modal': position_modal,
                'disable_mousewheel_on': disable_mousewheel_on,
                'current_theme': current_theme
            })
        except Exception:
            modal_manager = None

        # ----------------------
        # Clipboard autollenado
        # ----------------------
        clipboard_history = []  # list of { 'text', 'parsed', 'ts' }
        last_clip_text = ''
        import time, json, re

        SESSION_WINDOW = 180  # segundos
        session = {'id': None, 'start': None, 'active': False}

        # modo inicial: 'preguntar', 'autofill_empty', 'autofill_always'
        clip_mode = 'preguntar'
        clipboard_watcher_on = tk.BooleanVar(value=True)

        def parse_clipboard(text):
            parsed = {}
            if not text or not text.strip():
                return parsed
            # intentar JSON
            try:
                obj = json.loads(text)
                if isinstance(obj, dict):
                    # mapear claves comunes
                    for k in ('name','nombre','telefono','numero','sn','dni','email','notas'):
                        if k in obj and obj[k]:
                            parsed[k if k!='telefono' else 'numero'] = str(obj[k])
                    return parsed
            except Exception:
                pass

            # buscar email
            m = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
            if m:
                parsed['email'] = m.group(0)

            # teléfono (bastante flexible)
            m = re.search(r'(?:\+?\d{1,3}[-.\s]?)?(?:\d{6,12})', text)
            if m:
                phone = m.group(0).strip()
                # evitar capturar partes de largos serials si parecen muy cortos
                if len(re.sub(r'\D','',phone)) >= 6:
                    parsed['numero'] = phone

            # dni (7-9 dígitos)
            m = re.search(r'\b\d{7,9}\b', text)
            if m:
                val = m.group(0)
                # si ya detectamos un número telefónico, no sobreescribir
                if 'numero' not in parsed:
                    parsed['dni'] = val

            # SN alfanumérico (heurística)
            m = re.search(r'\b[A-Z0-9\-]{6,20}\b', text.upper())
            if m:
                parsed['sn'] = m.group(0)

            # Nombre heurístico: dos palabras con inicial mayúscula
            m = re.search(r'([A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)+)', text)
            if m:
                parsed['nombre'] = m.group(1).strip()

            # si nada estimable y el texto es largo -> notas
            if not parsed and len(text.strip()) > 10:
                parsed['notas'] = text.strip()

            return parsed

        def fill_fields(parsed, replace=False):
            """Rellena los widgets con parsed. Si replace=False solo llena campos vacíos."""
            try:
                if 'nombre' in parsed:
                    if replace or not nombre_var.get().strip():
                        nombre_var.set(parsed['nombre'])
                if 'numero' in parsed:
                    if replace or not numero_var.get().strip():
                        numero_var.set(parsed['numero'])
                if 'sn' in parsed:
                    if replace or not sn_var.get().strip():
                        sn_var.set(parsed['sn'])
                if 'dni' in parsed:
                    if replace or not dni_var.get().strip():
                        dni_var.set(parsed['dni'])
                if 'notas' in parsed:
                    if replace:
                        try:
                            template_text.delete(1.0, tk.END)
                            template_text.insert(tk.END, parsed['notas'])
                        except Exception:
                            pass
                    else:
                        try:
                            cur = template_text.get(1.0, tk.END).strip()
                            if not cur:
                                template_text.insert(tk.END, parsed['notas'])
                        except Exception:
                            pass
            except Exception:
                pass

        def show_suggestion_dialog(parsed):
            # Small non-blocking dialog showing detected fields and asking user to Apply/Replace/Ignore
            try:
                dlg = tk.Toplevel(root)
                dlg.title('Autollenado detectado')
                dlg.transient(root)
                dlg.resizable(False, False)
                row = 0
                ttk.Label(dlg, text='Se detectaron estos datos en el portapapeles:', font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, columnspan=2, padx=8, pady=(8,4), sticky='w')
                row += 1
                for k, v in parsed.items():
                    ttk.Label(dlg, text=f"{k.capitalize()}:", font=('Segoe UI', 9, 'bold')).grid(row=row, column=0, sticky='e', padx=6, pady=2)
                    ttk.Label(dlg, text=v).grid(row=row, column=1, sticky='w', padx=6, pady=2)
                    row += 1

                def _apply():
                    fill_fields(parsed, replace=False)
                    dlg.destroy()

                def _replace():
                    fill_fields(parsed, replace=True)
                    dlg.destroy()

                def _ignore():
                    dlg.destroy()

                btns = ttk.Frame(dlg)
                btns.grid(row=row, column=0, columnspan=2, pady=8)
                ttk.Button(btns, text='Aplicar (solo vacíos)', command=_apply).pack(side='right', padx=6)
                ttk.Button(btns, text='Reemplazar', command=_replace).pack(side='right', padx=6)
                ttk.Button(btns, text='Ignorar', command=_ignore).pack(side='right', padx=6)
            except Exception:
                pass

        def clipboard_watcher():
            nonlocal last_clip_text
            try:
                clip = root.clipboard_get()
            except Exception:
                clip = ''
            if not clipboard_watcher_on.get():
                root.after(700, clipboard_watcher)
                return
            if clip and clip != last_clip_text:
                ts = time.time()
                parsed = parse_clipboard(clip)
                clipboard_history.insert(0, {'text': clip, 'parsed': parsed, 'ts': ts})
                # mantener historial corto
                if len(clipboard_history) > 50:
                    clipboard_history.pop()
                # Si hay parsed y hay al menos un campo vacío en el formulario, sugerir
                if parsed:
                    any_empty = (not nombre_var.get().strip() or not numero_var.get().strip() or not sn_var.get().strip() or not dni_var.get().strip() or not template_text.get(1.0, tk.END).strip())
                    # Si hay sesión activa, limitar al tiempo de sesión
                    in_session = True
                    if session['active'] and session['start']:
                        in_session = (ts - session['start']) <= SESSION_WINDOW
                    if in_session and any_empty:
                        if clip_mode == 'autofill_always':
                            fill_fields(parsed, replace=False)
                        elif clip_mode == 'autofill_empty':
                            fill_fields(parsed, replace=False)
                        else:
                            # preguntar
                            show_suggestion_dialog(parsed)
                last_clip_text = clip
            root.after(700, clipboard_watcher)

        # botón en header para aplicar último clip manualmente
        def apply_last_clip():
            if clipboard_history:
                parsed = clipboard_history[0].get('parsed', {})
                if parsed:
                    fill_fields(parsed, replace=False)

        # checkbox y botón en header (añadimos al creds_frame)
        try:
            ttk.Checkbutton(creds_frame, text='Auto', variable=clipboard_watcher_on).pack(side='right', padx=(6,2))
            ttk.Button(creds_frame, text='📎', width=3, command=apply_last_clip).pack(side='right', padx=(4,2))
        except Exception:
            pass

        # iniciar watcher
        root.after(700, clipboard_watcher)

        # Botón copiar plantilla
        ttk.Button(scrollable_frame, text="Copiar Plantilla", command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(template_text.get(1.0, tk.END))
        ]).pack(fill="x", pady=(5,0))

        # Encabezado: TNPS (sin marco)
        ttk.Label(scrollable_frame, text="TNPS", font=("Segoe UI", 12, "bold")).pack(anchor='w', padx=8, pady=(4,2))
        tnps_container = ttk.Frame(scrollable_frame)
        tnps_container.pack(fill="both", expand=True, pady=(0,8), padx=8)

        tnps_frame = ttk.Frame(tnps_container)
        tnps_frame.pack(fill="x")

        ttk.Label(tnps_frame, text="TNPS:", font=("Segoe UI", 10, "bold")).pack(side="left")
        tnps_var = tk.StringVar()
        tnps_combo = ttk.Combobox(tnps_frame, textvariable=tnps_var, values=[str(i) for i in range(10)], state="readonly", width=5)
        tnps_combo.pack(side="left", padx=(5,5))
        disable_mousewheel_on(tnps_combo)
        ttk.Button(tnps_frame, text="Guardar TNPS", command=lambda: [
            tnps_registros.append(int(tnps_var.get())) if tnps_var.get() else None,
            save_tnps(int(tnps_var.get())) if tnps_var.get() else None,
            tnps_var.set(""),
            update_tnps_percentage(),
            messagebox.showwarning("TNPS", "Selecciona un TNPS") if not tnps_var.get() else None
        ]).pack(side="left", padx=(0,5))
        ttk.Button(tnps_frame, text="📋 ", style='Copy.TButton', width=3, command=lambda: copy_tnps()).pack(side="left")

        # TNPS result display
        tnps_resultado = ttk.Label(tnps_container, text="", font=("Segoe UI", 10, "bold"))
        tnps_resultado.pack(anchor="w", pady=(0,5))

        def copy_tnps():
            nonlocal tnps_registros
            if tnps_registros:
                text = '\n'.join(map(str, tnps_registros))
                root.clipboard_clear()
                root.clipboard_append(text)
                # popup eliminado: TNPS copiado silenciosamente
                print("TNPS copiado al portapapeles")
            else:
                messagebox.showwarning("TNPS", "No hay registros para copiar")

        def update_tnps_percentage():
            nonlocal tnps_registros
            try:
                from utils import calculate_tnps_percentage
            except Exception:
                calculate_tnps_percentage = None

            if tnps_registros:
                if calculate_tnps_percentage:
                    porcentaje = calculate_tnps_percentage(tnps_registros)
                else:
                    # fallback to previous logic
                    puntos = []
                    for r in tnps_registros:
                        try:
                            val = int(r)
                        except Exception:
                            continue
                        if val >= 8:
                            puntos.append(100)
                        elif val >= 6:
                            puntos.append(50)
                        else:
                            puntos.append(0)
                    porcentaje = round((sum(puntos) / (len(puntos) or 1)), 2)

                color = "green" if porcentaje >= 77 else "red"
                estado = "positivo" if porcentaje >= 77 else "negativo"
                tnps_resultado.config(text=f"TNPS {estado}: {porcentaje}%", foreground=color)
            else:
                tnps_resultado.config(text="No hay registros aún", foreground="black")

        # Buttons frame moved earlier (see above)

        # Botón para cambiar tema
        ttk.Button(scrollable_frame, text="Cambiar Tema", command=toggle_theme).pack(pady=10)

        # Funciones de modales (simplificadas para esta versión)
        def open_retencion_modal():
            # Modal de Retención: autocompletar desde formulario principal y generar plantilla
            modal = tk.Toplevel(root)
            modal.title("Retención")
            modal.transient(root)
            modal.grab_set()

            # usar tamaño principal exacto y layout vertical (label encima de control)
            try:
                root.update_idletasks()
                main_w = root.winfo_width() or 324
                main_h = root.winfo_height() or 600
                position_modal(modal, int(main_w), int(main_h), side='right')
            except Exception:
                pass
            modal.grid_columnconfigure(0, weight=1)

            # Campos (label arriba, control abajo)
            sn_modal_var = tk.StringVar(value=sn_var.get())
            ttk.Label(modal, text="SN:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=(8,2))
            sn_modal_entry = ttk.Entry(modal, textvariable=sn_modal_var)
            sn_modal_entry.grid(row=1, column=0, padx=8, pady=(0,6), sticky='ew')

            tipo_solicitud_var = tk.StringVar(value='Cancelación')
            ttk.Label(modal, text="Tipo de Solicitud:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky='w', padx=8, pady=(6,2))
            tipo_solicitud_combo = ttk.Combobox(modal, textvariable=tipo_solicitud_var, state='readonly', values=['Cancelación', 'Migración', 'Portabilidad'])
            tipo_solicitud_combo.grid(row=3, column=0, padx=8, pady=(0,6), sticky='ew')
            disable_mousewheel_on(tipo_solicitud_combo)

            motivo_solicitud_var = tk.StringVar(value='Motivos Económicos')
            ttk.Label(modal, text="Motivo de Solicitud:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky='w', padx=8, pady=(6,2))
            motivo_solicitud_combo = ttk.Combobox(modal, textvariable=motivo_solicitud_var, state='readonly', values=['Cuestionamiento', 'Motivos Económicos', 'No usa el servicio', 'Inconveniente con el servicio', 'Inconforme con los beneficios', 'Otros'])
            motivo_solicitud_combo.grid(row=5, column=0, padx=8, pady=(0,6), sticky='ew')
            disable_mousewheel_on(motivo_solicitud_combo)

            nombre_titular_var = tk.StringVar(value=nombre_var.get())
            ttk.Label(modal, text="Nombre del titular:", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky='w', padx=8, pady=(6,2))
            nombre_titular_entry = ttk.Entry(modal, textvariable=nombre_titular_var)
            nombre_titular_entry.grid(row=7, column=0, padx=8, pady=(0,6), sticky='ew')

            dni_modal_var = tk.StringVar(value=dni_var.get())
            ttk.Label(modal, text="DNI:", font=("Segoe UI", 10, "bold")).grid(row=8, column=0, sticky='w', padx=8, pady=(6,2))
            dni_modal_entry = ttk.Entry(modal, textvariable=dni_modal_var)
            dni_modal_entry.grid(row=9, column=0, padx=8, pady=(0,6), sticky='ew')

            tel_contacto_var = tk.StringVar(value=numero_entry.get())
            ttk.Label(modal, text="Teléfono de contacto:", font=("Segoe UI", 10, "bold")).grid(row=10, column=0, sticky='w', padx=8, pady=(6,2))
            tel_contacto_entry = ttk.Entry(modal, textvariable=tel_contacto_var)
            tel_contacto_entry.grid(row=11, column=0, padx=8, pady=(0,6), sticky='ew')

            tel_afectado_var = tk.StringVar(value=numero_entry.get())
            ttk.Label(modal, text="Teléfono afectado:", font=("Segoe UI", 10, "bold")).grid(row=12, column=0, sticky='w', padx=8, pady=(6,2))
            tel_afectado_entry = ttk.Entry(modal, textvariable=tel_afectado_var)
            tel_afectado_entry.grid(row=13, column=0, padx=8, pady=(0,6), sticky='ew')

            accion_var = tk.StringVar()
            ttk.Label(modal, text="Acción ofrecida:", font=("Segoe UI", 10, "bold")).grid(row=14, column=0, sticky='w', padx=8, pady=(6,2))
            accion_entry = ttk.Entry(modal, textvariable=accion_var)
            accion_entry.grid(row=15, column=0, padx=8, pady=(0,6), sticky='ew')

            # Observaciones libres
            ttk.Label(modal, text="Observaciones:", font=("Segoe UI", 10, "bold")).grid(row=16, column=0, sticky='w', padx=8, pady=(6,2))
            obs_text = tk.Text(modal, height=6)
            obs_text.grid(row=17, column=0, padx=8, pady=(0,6), sticky='nsew')
            modal.grid_rowconfigure(17, weight=1)

            # Map default acciones
            acciones_map = {
                'Cancelación': {
                    'Motivos Económicos': 'Ofrecer descuento / negociar ahorro',
                    'No usa el servicio': 'Ofrecer plan alternativo / pausar servicio',
                    'Inconveniente con el servicio': 'Solución técnica / crédito',
                    'Inconforme con los beneficios': 'Presentar alternativas / mejora de plan',
                    'Cuestionamiento': 'Revisar cargos y explicar detalles',
                    'Otros': 'Registrar caso y escalar'
                },
                'Migración': {'default': 'Ofrecer migración y validar compatibilidad'},
                'Portabilidad': {'default': 'Iniciar trámite de portabilidad y dar instrucciones'}
            }

            def refresh_accion(event=None):
                t = tipo_solicitud_var.get()
                m = motivo_solicitud_var.get()
                accion = ''
                if t in acciones_map:
                    if m in acciones_map[t]:
                        accion = acciones_map[t][m]
                    else:
                        accion = acciones_map[t].get('default', '')
                accion_var.set(accion)

            tipo_solicitud_combo.bind('<<ComboboxSelected>>', refresh_accion)
            motivo_solicitud_combo.bind('<<ComboboxSelected>>', refresh_accion)
            refresh_accion()

            def guardar_retencion():
                # validations
                if not nombre_titular_var.get().strip():
                    messagebox.showwarning('Validación', 'Ingresa el nombre del titular')
                    return
                if not dni_modal_var.get().strip():
                    messagebox.showwarning('Validación', 'Ingresa el DNI')
                    return

                plantilla = []
                plantilla.append(f"SN: {sn_modal_var.get()}")
                plantilla.append(f"Tipo de Solicitud: {tipo_solicitud_var.get()}")
                plantilla.append(f"Motivo de Solicitud: {motivo_solicitud_var.get()}")
                plantilla.append(f"Nombre del titular: {nombre_titular_var.get()}")
                plantilla.append(f"DNI: {dni_modal_var.get()}")
                plantilla.append(f"Teléfono de contacto: {tel_contacto_var.get()}")
                plantilla.append(f"Teléfono afectado: {tel_afectado_var.get()}")
                plantilla.append(f"Acción ofrecida: {accion_var.get()}")
                if obs_text.get(1.0, tk.END).strip():
                    plantilla.append(f"Observaciones: {obs_text.get(1.0, tk.END).strip()}")

                final = '\n'.join(plantilla)

                try:
                    # guardar con campos específicos para facilitar búsquedas
                    save_client(nombre_var.get(), numero_entry.get(), sn_var.get(), 'Retención', tipo_solicitud=tipo_solicitud_var.get(), motivo_solicitud=motivo_solicitud_var.get(), nombre_titular=nombre_titular_var.get(), dni=dni_modal_var.get(), telefono_contacto=tel_contacto_var.get(), telefono_afectado=tel_afectado_var.get(), accion_ofrecida=accion_var.get(), notas=final)
                    # colocar plantilla en el editor principal y copiar
                    try:
                        template_text.delete(1.0, tk.END)
                        template_text.insert(tk.END, final)
                        root.clipboard_clear()
                        root.clipboard_append(final)
                    except Exception:
                        pass
                    # popup eliminado: retención guardada silenciosamente
                    print('Retención guardada y plantilla copiada al portapapeles')
                    modal.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo guardar retención: {e}')

            ttk.Button(modal, text='Guardar', command=guardar_retencion).grid(row=9, column=0, columnspan=2, pady=8)

        def open_cuestionamiento_modal():
            # Modal de Cuestionamiento: campos avanzados (SVA u Otros)
            modal = tk.Toplevel(root)
            modal.title("Cuestionamiento de recibo")
            modal.transient(root)
            modal.grab_set()

            # usar tamaño principal para mostrar todo
            try:
                root.update_idletasks()
                main_w = root.winfo_width() or 324
                main_h = root.winfo_height() or 600
                position_modal(modal, int(main_w), int(main_h), side='right')
            except Exception:
                pass
            modal.grid_columnconfigure(0, weight=1)

            # Submotivo (titulo arriba, control abajo)
            ttk.Label(modal, text="Motivo de cuestionamiento:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=(8,2))
            submotivo_var = tk.StringVar(value='SVA')
            submotivo_combo = ttk.Combobox(modal, textvariable=submotivo_var, values=['SVA', 'Otros', 'Ajuste'], state='readonly')
            submotivo_combo.grid(row=1, column=0, padx=8, pady=(0,8), sticky='ew')
            disable_mousewheel_on(submotivo_combo)

            # SVA area stacked vertically
            sva_frame = ttk.Frame(modal)
            sva_frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=4)
            sva_frame.grid_columnconfigure(0, weight=1)

            titular_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(sva_frame, text='Titular (si no está marcado = Usuario)', variable=titular_var).grid(row=0, column=0, sticky='w', pady=(0,6))

            ttk.Label(sva_frame, text="Servicios facturados:", font=("Segoe UI", 10)).grid(row=1, column=0, sticky='w')
            services_frame = ttk.Frame(sva_frame)
            services_frame.grid(row=2, column=0, sticky='nsew', pady=(4,6))

            SVA_SERVICES = [
                'Abaco',
                'Babbel',
                'Busuu',
                'Challenges Arena',
                'Claro Juegos',
                'CLD_GM Cloud Gaming',
                'Club apps by claro',
                'Club Ciencia',
                'Contenta',
                'Fuze Force',
                'Gameeasy',
                'Gokids',
                'Goles L1 Max',
                'Google play',
                'Había una vez',
                'Iedukar',
                'Inglés Mágico',
                'Jenius',
                'Norton Cykadas',
                'Pfl',
                'Play Kids',
                'Rescatel',
                'Tono de Espera',
                'Zenapp',
                'Zenit'
            ]

            service_vars = []
            cols = 3
            # configure columns so checkboxes distribute evenly
            for ci in range(cols):
                try:
                    services_frame.grid_columnconfigure(ci, weight=1)
                except Exception:
                    pass

            for idx, svc in enumerate(SVA_SERVICES):
                var = tk.BooleanVar(value=(svc == 'Club Ciencia'))
                service_vars.append((svc, var))
                r = idx // cols
                c = idx % cols
                cb = ttk.Checkbutton(services_frame, text=svc, variable=var, command=lambda: update_services_selection())
                cb.grid(row=r, column=c, sticky='w', padx=(0,8), pady=2)

            # place 'Otro' on the next row, its entry spans the remaining columns
            otro_var = tk.BooleanVar(value=False)
            otro_text_var = tk.StringVar()
            rows = (len(SVA_SERVICES) + cols - 1) // cols
            otro_row = rows
            otro_cb = ttk.Checkbutton(services_frame, text='Otro (especificar)', variable=otro_var, command=lambda: update_services_selection())
            otro_cb.grid(row=otro_row, column=0, sticky='w', pady=(6,0))
            otro_entry = ttk.Entry(services_frame, textvariable=otro_text_var)
            # span the rest of the columns so it has room
            otro_entry.grid(row=otro_row, column=1, columnspan=(cols-1), sticky='ew', padx=(6,0), pady=(6,0))

            # cuantos / detalle variables (compatibility)
            cuantos_var = tk.StringVar(value='Uno')
            varios_detalle_var = tk.StringVar()

            def update_services_selection():
                # collect selected services and set detalle variable
                selected = [name for (name, v) in service_vars if v.get()]
                if otro_var.get() and otro_text_var.get().strip():
                    selected.append(otro_text_var.get().strip())

                if len(selected) <= 1:
                    cuantos_var.set('Uno')
                    varios_detalle_var.set(selected[0] if selected else '')
                else:
                    cuantos_var.set('Varios')
                    varios_detalle_var.set(', '.join(selected))

            # detalles y SN
            ttk.Label(sva_frame, text="Información entregada al cliente:", font=("Segoe UI", 10)).grid(row=3, column=0, sticky='w')
            info_text = tk.Text(sva_frame, height=4)
            info_text.grid(row=4, column=0, sticky='nsew', pady=(4,6))
            ttk.Label(sva_frame, text="SN:", font=("Segoe UI", 10)).grid(row=5, column=0, sticky='w')
            sn_modal_var = tk.StringVar(value=sn_var.get())
            sn_modal_entry = ttk.Entry(sva_frame, textvariable=sn_modal_var)
            sn_modal_entry.grid(row=6, column=0, sticky='ew', pady=(4,6))

            # initialize services selection state
            update_services_selection()

            # Otros/Ajuste area stacked
            otros_frame = ttk.Frame(modal)
            otros_frame.grid(row=3, column=0, sticky='nsew', padx=8, pady=4)
            ttk.Label(otros_frame, text="Acción tomada / Observaciones:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky='w')
            otros_text = tk.Text(otros_frame, height=6)
            otros_text.grid(row=1, column=0, sticky='nsew')

            # Hide/show logic: fully show SVA or Otros/Ajuste (grid/grid_remove)
            def refresh_visibility(event=None):
                try:
                    if submotivo_var.get() == 'SVA':
                        sva_frame.grid()
                        otros_frame.grid_remove()
                    else:
                        otros_frame.grid()
                        sva_frame.grid_remove()
                    # después de cambiar visibilidad, recalcular tamaño/posición para asegurar que todo se vea
                    try:
                        root.update_idletasks()
                        position_modal(modal, max(324, int(root.winfo_width() or 324)), None, side='right')
                    except Exception:
                        pass
                except Exception:
                    pass

            submotivo_combo.bind('<<ComboboxSelected>>', refresh_visibility)
            refresh_visibility()

            def guardar_cuestionamiento():
                # validation
                # Branch by submotivo
                if submotivo_var.get() == 'SVA':
                    # validations
                    if not sn_modal_var.get().strip():
                        messagebox.showwarning('Validación', 'La SN debe estar presente')
                        return

                    # recopilar servicios seleccionados
                    selected = [name for (name, v) in service_vars if v.get()]
                    if otro_var.get() and otro_text_var.get().strip():
                        selected.append(otro_text_var.get().strip())

                    cuantos_val = 'Uno' if len(selected) == 1 else 'Varios'

                    # Plantilla fija de 4 puntos (no se cambia la plantilla, solo se rellenan los datos)
                    quien_text = 'Titular' if titular_var.get() else 'Usuario'
                    detalle_servicios = selected[0] if cuantos_val == 'Uno' and selected else (', '.join(selected) if selected else '')
                    info_entregada = info_text.get(1.0, tk.END).strip()
                    sn_final = sn_modal_var.get().strip()

                    final = (
                        "1: Indicar quien se comunica (Usuario o Titular): " + quien_text + "\n"
                        + "2: Cuantos servicio tiene facturado (Uno o Varios) detalla: " + cuantos_val + (" - " + detalle_servicios if detalle_servicios else "") + "\n"
                        + "3: Detalla la información entregada al cliente: " + (info_entregada.replace('\n', ' ').strip() if info_entregada else "") + "\n"
                        + "4: SN: " + sn_final
                    )

                    try:
                        # guardar registro en DB con nota final
                        save_client(nombre_var.get(), numero_entry.get(), sn_var.get(), 'Cuestionamiento de recibo - SVA', dni=dni_var.get(), notas=final)
                        # colocar plantilla en el editor principal y copiar
                        try:
                            template_text.delete(1.0, tk.END)
                            template_text.insert(tk.END, final)
                            root.clipboard_clear()
                            root.clipboard_append(final)
                        except Exception:
                            pass
                        # popup eliminado: cuestionamiento guardado silenciosamente
                        print('Registro guardado y plantilla copiada al portapapeles')
                        modal.destroy()
                    except Exception as e:
                        messagebox.showerror('Error', f'No se pudo guardar: {e}')
                else:
                    # Otros / Ajuste: texto libre
                    if not otros_text.get(1.0, tk.END).strip():
                        messagebox.showwarning('Validación', 'Ingresa la acción tomada o la observación')
                        return
                    final = f"CUESTIONAMIENTO - {submotivo_var.get()}\n" + otros_text.get(1.0, tk.END).strip()
                    try:
                        save_client(nombre_var.get(), numero_entry.get(), sn_var.get(), f'Cuestionamiento de recibo - {submotivo_var.get()}', dni=dni_var.get(), notas=final)
                        root.clipboard_clear()
                        root.clipboard_append(final)
                        # popup eliminado: cuestionamiento guardado silenciosamente
                        print('Registro guardado y plantilla copiada al portapapeles')
                        modal.destroy()
                    except Exception as e:
                        messagebox.showerror('Error', f'No se pudo guardar: {e}')

            ttk.Button(modal, text='Guardar', command=guardar_cuestionamiento).grid(row=4, column=0, pady=8)

        # Modal para editar credenciales VPN/SIAC
        def open_credentials_modal():
            modal = tk.Toplevel(root)
            modal.title("Editar credenciales")
            modal.transient(root)
            modal.grab_set()

            # position credentials modal beside main window and stack labels/entries
            try:
                root.update_idletasks()
                main_w = root.winfo_width() or 324
                main_h = root.winfo_height() or 600
                position_modal(modal, int(main_w * 0.6), int(main_h * 0.4), side='right')
            except Exception:
                position_modal(modal, 420, None, side='right')
            modal.grid_columnconfigure(0, weight=1)

            ttk.Label(modal, text="Contraseña VPN:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=(8,2))
            vpn_var = tk.StringVar(value=(get_credential('vpn_password') if 'get_credential' in globals() else ''))
            vpn_entry = ttk.Entry(modal, textvariable=vpn_var, show='*')
            vpn_entry.grid(row=1, column=0, padx=8, pady=(0,8), sticky='ew')

            ttk.Label(modal, text="Contraseña SIAC:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky='w', padx=8, pady=(6,2))
            siac_var = tk.StringVar(value=(get_credential('siac_password') if 'get_credential' in globals() else ''))
            siac_entry = ttk.Entry(modal, textvariable=siac_var, show='*')
            siac_entry.grid(row=3, column=0, padx=8, pady=(0,8), sticky='ew')

            def guardar_credenciales():
                try:
                    set_credential('vpn_password', vpn_var.get())
                    set_credential('siac_password', siac_var.get())
                    # popup eliminado: credenciales guardadas silenciosamente
                    print('Credenciales guardadas correctamente')
                    modal.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudieron guardar las credenciales: {e}')

            ttk.Button(modal, text='Guardar', command=guardar_credenciales).grid(row=4, column=0, pady=8)

        # Evitar cierre accidental: solo minimizar o botón X
        def on_close():
            if nombre_var.get() or numero_entry.get() or sn_var.get() or dni_var.get() or motivo_var.get() != "Selecciona motivo...":
                if messagebox.askyesno("Guardar datos", "¿Tienes datos sin guardar? ¿Quieres cerrar de todos modos?"):
                    if standup_timer_id:
                        root.after_cancel(standup_timer_id)
                    root.destroy()
                else:
                    root.iconify()
            else:
                if standup_timer_id:
                    root.after_cancel(standup_timer_id)
                root.destroy()
        root.protocol("WM_DELETE_WINDOW", on_close)

        start_standup_reminder()

        update_tnps_percentage()  # Mostrar porcentaje inicial

        # Iniciar el loop principal
        root.mainloop()
        
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print("[ERROR] Excepción en run_app():", tb)
        tkmb.showerror("Error en la app", f"Ocurrió un error:\n{e}\n\n{tb}")
        raise
