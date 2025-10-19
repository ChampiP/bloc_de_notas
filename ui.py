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
            style.configure('TLabel', background='#f5f5f5', foreground='#2c3e50', font=('Segoe UI', 10))
            style.configure('TButton', font=('Segoe UI', 10, 'bold'), relief='raised', borderwidth=2)
            style.map('TButton', background=[('active', '#3498db'), ('pressed', '#2980b9')])
            style.configure('TEntry', fieldbackground='white', borderwidth=2, relief='sunken', font=('Segoe UI', 10))
            style.configure('TCombobox', fieldbackground='white', font=('Segoe UI', 10))
            style.configure('TCheckbutton', background='#f5f5f5', font=('Segoe UI', 10))
            style.configure('TScrollbar', background='#bdc3c7', troughcolor='#ecf0f1')
            # El widget template_text se estiliza después de su creación

        def apply_dark_theme():
            root.configure(bg='#2c3e50')
            style.configure('TFrame', background='#2c3e50', relief='flat')
            style.configure('TLabel', background='#2c3e50', foreground='#ecf0f1', font=('Segoe UI', 10))
            style.configure('TButton', font=('Segoe UI', 10, 'bold'), relief='raised', borderwidth=2)
            style.map('TButton', background=[('active', '#e74c3c'), ('pressed', '#c0392b')])
            style.configure('TEntry', fieldbackground='#34495e', borderwidth=2, relief='sunken', font=('Segoe UI', 10))
            style.configure('TCombobox', fieldbackground='#34495e', font=('Segoe UI', 10))
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

        # GRAN CUADRO PRINCIPAL
        main_container = tk.LabelFrame(
            root,
            text="Gestión de Atención",
            padx=12,
            pady=12,
            font=("Arial", 12, "bold"),
            bg="#f0f0f0"
        )
        main_container.pack(fill="both", expand=True, padx=24, pady=24)

        # Top frame para saludo y timer (dentro del cuadro grande)
        top_frame = ttk.Frame(main_container)
        top_frame.pack(fill="x", pady=(0,18), padx=16)

        # Contenedor para todo el contenido scrollable
        container = ttk.Frame(main_container)
        container.pack(fill="both", expand=True, padx=12, pady=12)

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

        # Canvas and scrollbar for scrolling (más angosto)
        canvas = tk.Canvas(container, width=290, height=600, bg="#eaeaea", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="y")
        scrollbar.pack(side="right", fill="y")

        # Scrollable frame
        scrollable_frame = ttk.Frame(canvas, width=290)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Mouse wheel binding
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def on_canvas_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", on_canvas_configure)

        # Saludo personalizado (más pequeño)
        saludo_label = ttk.Label(top_frame, text=get_saludo_personalizado(nombre_cliente=nombre_var.get() or "Cliente"), wraplength=180, justify="center", font=("Arial", 9))
        saludo_label.pack(side="left")

        # Timer
        timer_label = ttk.Label(top_frame, textvariable=timer_var, font=("Arial", 9))
        timer_label.pack(side="right")

        def update_saludo(*args):
            saludo_label.config(text=get_saludo_personalizado(nombre_cliente=nombre_var.get() or "Cliente"))
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
        sep1.pack(fill='x', pady=5)

        # Caja: Datos del Cliente
        form_container = tk.LabelFrame(
            scrollable_frame,
            text="Datos del Cliente",
            padx=10,
            pady=10,
            font=("Arial", 11, "bold"),
            width=270,
            bg="#f8f8f8"
        )
        form_container.pack(fill="both", expand=True, pady=(0,18), padx=12, ipadx=4, ipady=4)
        form_container.config(width=270)

        form_frame = ttk.Frame(form_container)
        form_frame.pack(fill="x")
        form_frame.grid_columnconfigure(0, weight=0)
        form_frame.grid_columnconfigure(1, weight=1)
        form_frame.grid_columnconfigure(2, weight=0)

        # Nombre
        ttk.Label(form_frame, text="Nombre:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=(0,10))
        nombre_entry = ttk.Entry(form_frame, textvariable=nombre_var, font=("Arial", 10), width=20)
        nombre_entry.grid(row=0, column=1, sticky="ew", pady=(0,10))
        ttk.Button(form_frame, text="📋", command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(nombre_var.get())
        ]).grid(row=0, column=2, sticky="e", pady=(0,10))

        # Número
        ttk.Label(form_frame, text="Número:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=(0,10))
        numero_entry = ttk.Entry(form_frame, font=("Arial", 10))
        numero_entry.grid(row=1, column=1, sticky="ew", pady=(0,10))
        ttk.Button(form_frame, text="📋", command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(numero_entry.get())
        ]).grid(row=1, column=2, sticky="e", pady=(0,10))

        # SN
        ttk.Label(form_frame, text="SN:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=(0,10))
        sn_entry = ttk.Entry(form_frame, textvariable=sn_var, font=("Arial", 10))
        sn_entry.grid(row=2, column=1, sticky="ew", pady=(0,10))
        ttk.Button(form_frame, text="📋", command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(sn_var.get())
        ]).grid(row=2, column=2, sticky="e", pady=(0,10))

        # DNI
        ttk.Label(form_frame, text="DNI:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(0,10))
        dni_entry = ttk.Entry(form_frame, textvariable=dni_var, font=("Arial", 10))
        dni_entry.grid(row=3, column=1, sticky="ew", pady=(0,10))
        ttk.Button(form_frame, text="📋", command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(dni_var.get())
        ]).grid(row=3, column=2, sticky="e", pady=(0,10))

        # Aquí debería continuar el resto de la UI, pero como está incompleto, agregaré un placeholder
        # Para completar la app, necesito agregar más widgets: motivo, template, botones, etc.
        
        # Caja: Pasos del Proceso
        pasos_container = tk.LabelFrame(
            scrollable_frame,
            text="Pasos del Proceso",
            padx=10,
            pady=10,
            font=("Arial", 11, "bold"),
            width=270,
            bg="#f8f8f8"
        )
        pasos_container.pack(fill="both", expand=True, pady=(0,18), padx=12, ipadx=4, ipady=4)
        pasos_container.config(width=270)

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

        # Caja: Motivo de llamada
        motivo_container = tk.LabelFrame(
            scrollable_frame,
            text="Motivo de llamada",
            padx=10,
            pady=10,
            font=("Arial", 11, "bold"),
            width=270,
            bg="#f8f8f8"
        )
        motivo_container.pack(fill="both", expand=True, pady=(0,18), padx=12, ipadx=4, ipady=4)
        motivo_container.config(width=270)

        motivo_frame = ttk.Frame(motivo_container)
        motivo_frame.pack(fill="x")
        motivo_var = tk.StringVar(value="Selecciona motivo...")
        motivo_combo = ttk.Combobox(motivo_frame, textvariable=motivo_var, values=[
            "Selecciona motivo...",
            "Retención",
            "Bloqueo",
            "Cuestionamiento de recibo",
            "Atención técnica"
        ], state="readonly", font=("Arial", 10))
        motivo_combo.pack(side="left", fill="x", expand=True)
        ttk.Button(motivo_frame, text="📋", command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(motivo_var.get())
        ]).pack(side="right")

        def update_template(event=None):
            motivo = motivo_var.get()
            if motivo not in ["Retención", "Cuestionamiento de recibo"]:  # No actualizar para estos, ya que se setean manualmente
                template_text.delete(1.0, tk.END)
                template_text.insert(tk.END, templates.get(motivo, ""))

        motivo_combo.bind("<<ComboboxSelected>>", update_template)

        # Caja: Notas
        notas_container = tk.LabelFrame(
            scrollable_frame,
            text="Notas",
            padx=10,
            pady=10,
            font=("Arial", 11, "bold"),
            width=270,
            bg="#f8f8f8"
        )
        notas_container.pack(fill="both", expand=True, pady=(0,18), padx=12, ipadx=4, ipady=4)
        notas_container.config(width=270)

        template_text = tk.Text(notas_container, height=8, wrap="word", font=("Arial", 10), relief="solid", borderwidth=2, background="#fffbe6")
        template_text.pack(fill="both", expand=True)

        update_template()  # Inicial

        # Botón copiar
        ttk.Button(scrollable_frame, text="Copiar Notas", command=lambda: [
            root.clipboard_clear(),
            root.clipboard_append(template_text.get(1.0, tk.END))
        ]).pack(fill="x", pady=(5,0))

        # Caja: TNPS
        tnps_container = tk.LabelFrame(
            scrollable_frame,
            text="TNPS",
            padx=10,
            pady=10,
            font=("Arial", 11, "bold"),
            width=270,
            bg="#f8f8f8"
        )
        tnps_container.pack(fill="both", expand=True, pady=(0,18), padx=12, ipadx=4, ipady=4)
        tnps_container.config(width=270)

        tnps_frame = ttk.Frame(tnps_container)
        tnps_frame.pack(fill="x")

        ttk.Label(tnps_frame, text="TNPS:", font=("Arial", 10, "bold")).pack(side="left")
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
        ttk.Button(tnps_frame, text="📋 ", command=lambda: copy_tnps()).pack(side="left")

        # TNPS result display
        tnps_resultado = ttk.Label(tnps_container, text="", font=("Arial", 10, "bold"))
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
            if tnps_registros:
                positivos = sum(1 for r in tnps_registros if r == 9)
                porcentaje = round((positivos / len(tnps_registros)) * 100, 2)
                if porcentaje >= 77:
                    tnps_resultado.config(text=f"TNPS positivo: {porcentaje}%", foreground="green")
                else:
                    tnps_resultado.config(text=f"TNPS negativo: {porcentaje}%", foreground="red")
            else:
                tnps_resultado.config(text="No hay registros aún", foreground="black")

        # Buttons frame
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill="x", pady=(0,10))

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

        # Botón para cambiar tema
        ttk.Button(scrollable_frame, text="Cambiar Tema", command=toggle_theme).pack(pady=10)

        # Funciones de modales (simplificadas para esta versión)
        def open_retencion_modal():
            messagebox.showinfo("Retención", "Funcionalidad de retención - Implementar modal completo")

        def open_cuestionamiento_modal():
            messagebox.showinfo("Cuestionamiento", "Funcionalidad de cuestionamiento - Implementar modal completo")

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
