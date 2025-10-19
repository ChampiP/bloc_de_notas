import tkinter as tk
from tkinter import ttk, messagebox
from plyer import notification
from db import connect_db, save_client, save_tnps
from templates import templates
from utils import get_saludo_personalizado, evaluar_tnps

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

        def apply_modern_theme():
            root.configure(bg='#f5f5f5')
            style.configure('TFrame', background='#f5f5f5', relief='flat')
            style.configure('TLabel', background='#f5f5f5', foreground='#2c3e50', font=('Segoe UI', 11))
            style.configure('TButton', font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, padding=(15,8))
            style.map('TButton', background=[('active', '#4CAF50'), ('pressed', '#45a049')], 
                      foreground=[('active', 'white'), ('pressed', 'white')])
            style.configure('TEntry', fieldbackground='white', borderwidth=2, relief='flat', font=('Segoe UI', 10), padding=(8,6))
            style.configure('TCombobox', fieldbackground='white', font=('Segoe UI', 10), padding=(8,6))
            style.configure('TCheckbutton', background='#f5f5f5', font=('Segoe UI', 10))
            style.configure('TScrollbar', background='#bdc3c7', troughcolor='#ecf0f1')
            # El widget template_text se estiliza después de su creación

        def apply_dark_theme():
            root.configure(bg='#2c3e50')
            style.configure('TFrame', background='#2c3e50', relief='flat')
            style.configure('TLabel', background='#2c3e50', foreground='#ecf0f1', font=('Segoe UI', 11))
            style.configure('TButton', font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0, padding=(15,8))
            style.map('TButton', background=[('active', '#e74c3c'), ('pressed', '#c0392b')], 
                      foreground=[('active', 'white'), ('pressed', 'white')])
            style.configure('TEntry', fieldbackground='#34495e', borderwidth=2, relief='flat', font=('Segoe UI', 10), padding=(8,6))
            style.configure('TCombobox', fieldbackground='#34495e', font=('Segoe UI', 10), padding=(8,6))
            style.configure('TCheckbutton', background='#2c3e50', font=('Segoe UI', 10))
            style.configure('TScrollbar', background='#7f8c8d', troughcolor='#34495e')
            # El widget template_text se estiliza después de su creación

        def toggle_theme():
            nonlocal current_theme
            if current_theme == 'modern':
                apply_dark_theme()
                current_theme = 'dark'
            else:
                apply_modern_theme()
                current_theme = 'modern'

        apply_modern_theme()

        # Estilos adicionales: boton de copiar pequeño y label de saludo resaltado
        style.configure('Copy.TButton', font=('Segoe UI', 9), padding=(4,2))

        # Header (replacing the big framed box) to keep a cleaner look
        header_frame = ttk.Frame(root)
        header_frame.pack(fill="x", padx=8, pady=(8,0))
        ttk.Label(header_frame, text="Gestión de Atención", font=("Segoe UI", 14, "bold")).pack(side="left")

        # Move credentials buttons to the header (top-right)
        creds_frame = ttk.Frame(header_frame)
        creds_frame.pack(side='right')

        ttk.Button(creds_frame, text="🔒VPN", width=5, style='Copy.TButton', command=lambda: copy_credential('vpn_password', 'VPN')).pack(side='right', padx=(2,0))
        ttk.Button(creds_frame, text="🔑SIAC", width=5, style='Copy.TButton', command=lambda: copy_credential('siac_password', 'SIAC')).pack(side='right', padx=(2,0))
        ttk.Button(creds_frame, text="✏️", width=3, style='Copy.TButton', command=lambda: open_credentials_modal()).pack(side='right', padx=(2,6))

        # Top frame para saludo y timer
        top_frame = ttk.Frame(root)
        top_frame.pack(fill="x", pady=(4,8), padx=8)

        # Contenedor para todo el contenido scrollable
        container = ttk.Frame(root)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # Variables
        nombre_var = tk.StringVar()
        sn_var = tk.StringVar()
        dni_var = tk.StringVar()
        timer_var = tk.StringVar(value="00:00")
        timer_running = False
        timer_seconds = 0
        alert_10min_shown = False
        standup_timer_id = None
        last_client_id = None
        tnps_registros = []

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

        # Saludo simplificado y resaltado: "Buenas noches, Sr. {Nombre}"
        # Fondo del saludo igual al del contenedor para evitar el efecto de cuadro
        saludo_bg = tk.Frame(top_frame, bg='#f5f5f5', bd=0)
        saludo_bg.pack(side='left', padx=(0,4))
        saludo_label = tk.Label(saludo_bg, text=f"Buenas noches, Sr. {nombre_var.get() or 'Cliente'}", wraplength=260, justify="center", font=("Segoe UI", 11, "bold"), bg='#f5f5f5', fg='#154a6b', padx=6, pady=4)
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
                    messagebox.showinfo("Copiado", f"{friendly_name or key} copiado al portapapeles")
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

        def update_saludo(*args):
            # Mostrar solo "Buenas noches, Sr. {nombre}" y resaltar
            nombre = nombre_var.get().strip() or 'Cliente'
            saludo_label.config(text=f"Buenas noches, Sr. {nombre}")
            start_timer()

        def start_timer():
            nonlocal timer_running, timer_seconds
            if nombre_var.get() and not timer_running:
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
        numero_entry = ttk.Entry(form_frame, font=("Segoe UI", 10), width=25)
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
        motivo_combo = ttk.Combobox(motivo_frame, textvariable=motivo_var, values=list(templates.keys()), state="readonly", font=("Segoe UI", 10))
        motivo_combo.pack(side="left", fill="x", expand=True)

        def update_template(event=None):
            motivo = motivo_var.get()
            if motivo not in ["Retención", "Cuestionamiento de recibo"]:
                template_text.delete(1.0, tk.END)
                template_text.insert(tk.END, templates.get(motivo, ""))

        motivo_combo.bind("<<ComboboxSelected>>", update_template)

        def update_template(event=None):
            motivo = motivo_var.get()
            # Para motivos que requieren modal, no sobrescribimos si se quiere manejar de otra forma
            if motivo not in ["Retención", "Cuestionamiento de recibo"]:
                try:
                    template_text.delete(1.0, tk.END)
                    template_text.insert(tk.END, templates.get(motivo, ""))
                except Exception:
                    # template_text aún no creado en algunos flujos; ignorar
                    pass

        # función para agregar cliente (colocada aquí para que los botones referencien el nombre)
        def add_client(open_modal=True):
            nonlocal last_client_id
            nombre = nombre_var.get()
            numero = numero_entry.get()
            sn = sn_var.get()
            motivo = motivo_var.get()
            if nombre and motivo != "Selecciona motivo...":
                if open_modal and motivo == "Retención":
                    open_retencion_modal()
                elif open_modal and motivo == "Cuestionamiento de recibo":
                    open_cuestionamiento_modal()
                else:
                    # Para otros motivos, guardar con notas
                    notas = template_text.get(1.0, tk.END).strip()
                    try:
                        last_client_id = save_client(nombre, numero, sn, motivo, dni=dni_var.get(), notas=notas)
                        messagebox.showinfo("Éxito", f"Cliente guardado con ID: {last_client_id}")
                        stop_timer()
                        update_template()
                    except Exception as e:
                        messagebox.showerror("Error", f"Error al guardar cliente: {e}")

        # Buttons below Motivo de llamada (moved as requested)
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill="x", pady=(4,10), padx=8)

        ttk.Button(buttons_frame, text="Agregar Cliente", command=add_client).pack(side="left", padx=(0,10))
        ttk.Button(buttons_frame, text="Limpiar", command=lambda: [
            add_client(open_modal=False) if (nombre_var.get() and motivo_var.get() != "Selecciona motivo...") else None,
            nombre_var.set(""),
            numero_entry.delete(0, tk.END),
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

        template_text = tk.Text(notas_container, height=8, wrap="word", font=("Segoe UI", 10), relief="flat", borderwidth=2, background="#fffbe6")
        template_text.pack(fill="both", expand=True)

        update_template()  # Inicial

        # Botón copiar
        ttk.Button(scrollable_frame, text="Copiar Notas", command=lambda: [
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
                messagebox.showinfo("Copiado", "TNPS copiado al portapapeles")
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
            # Modal de Retención: campos básicos y botón guardar
            modal = tk.Toplevel(root)
            modal.title("Retención")
            modal.transient(root)
            modal.grab_set()

            ttk.Label(modal, text="Tipo de retención:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=8)
            tipo_var = tk.StringVar(value="Ofrecer descuento")
            tipo_entry = ttk.Combobox(modal, textvariable=tipo_var, values=["Ofrecer descuento", "Mejora de plan", "Otra"], state='readonly')
            tipo_entry.grid(row=0, column=1, padx=8, pady=8)

            ttk.Label(modal, text="Observaciones:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky='nw', padx=8, pady=8)
            obs_text = tk.Text(modal, height=6, width=40)
            obs_text.grid(row=1, column=1, padx=8, pady=8)

            def guardar_retencion():
                notas_modal = f"RETENCION - {tipo_var.get()}\n" + obs_text.get(1.0, tk.END).strip()
                try:
                    save_client(nombre_var.get(), numero_entry.get(), sn_var.get(), 'Retención', dni=dni_var.get(), notas=notas_modal)
                    messagebox.showinfo('Retención', 'Retención guardada correctamente')
                    modal.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo guardar retención: {e}')

            ttk.Button(modal, text='Guardar', command=guardar_retencion).grid(row=2, column=0, columnspan=2, pady=8)

        def open_cuestionamiento_modal():
            # Modal de Cuestionamiento: campos para referencia y acción tomada
            modal = tk.Toplevel(root)
            modal.title("Cuestionamiento")
            modal.transient(root)
            modal.grab_set()

            ttk.Label(modal, text="Referencia recibo:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=8)
            ref_var = tk.StringVar()
            ref_entry = ttk.Entry(modal, textvariable=ref_var)
            ref_entry.grid(row=0, column=1, padx=8, pady=8)

            ttk.Label(modal, text="Acción tomada:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky='nw', padx=8, pady=8)
            accion_text = tk.Text(modal, height=6, width=40)
            accion_text.grid(row=1, column=1, padx=8, pady=8)

            def guardar_cuestionamiento():
                notas_modal = f"CUESTIONAMIENTO - Ref: {ref_var.get()}\n" + accion_text.get(1.0, tk.END).strip()
                try:
                    save_client(nombre_var.get(), numero_entry.get(), sn_var.get(), 'Cuestionamiento de recibo', dni=dni_var.get(), notas=notas_modal)
                    messagebox.showinfo('Cuestionamiento', 'Registro guardado correctamente')
                    modal.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo guardar: {e}')

            ttk.Button(modal, text='Guardar', command=guardar_cuestionamiento).grid(row=2, column=0, columnspan=2, pady=8)

        # Modal para editar credenciales VPN/SIAC
        def open_credentials_modal():
            modal = tk.Toplevel(root)
            modal.title("Editar credenciales")
            modal.transient(root)
            modal.grab_set()

            ttk.Label(modal, text="Contraseña VPN:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=8)
            vpn_var = tk.StringVar(value=(get_credential('vpn_password') if 'get_credential' in globals() else ''))
            vpn_entry = ttk.Entry(modal, textvariable=vpn_var, show='*', width=40)
            vpn_entry.grid(row=0, column=1, padx=8, pady=8)

            ttk.Label(modal, text="Contraseña SIAC:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky='w', padx=8, pady=8)
            siac_var = tk.StringVar(value=(get_credential('siac_password') if 'get_credential' in globals() else ''))
            siac_entry = ttk.Entry(modal, textvariable=siac_var, show='*', width=40)
            siac_entry.grid(row=1, column=1, padx=8, pady=8)

            def guardar_credenciales():
                try:
                    set_credential('vpn_password', vpn_var.get())
                    set_credential('siac_password', siac_var.get())
                    messagebox.showinfo('Credenciales', 'Credenciales guardadas correctamente')
                    modal.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudieron guardar las credenciales: {e}')

            ttk.Button(modal, text='Guardar', command=guardar_credenciales).grid(row=2, column=0, columnspan=2, pady=8)

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
