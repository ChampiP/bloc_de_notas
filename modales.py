
# Importamos tkinter y submódulos necesarios para la interfaz gráfica
import tkinter as tk
from tkinter import ttk, messagebox

class ModalManager:
    def open_cuestionamiento_modal(self):
        root = self.root
        ctx = self.ctx
        template_text = ctx.get('template_text')
        nombre_var = ctx.get('nombre_var')
        sn_var = ctx.get('sn_var')
        dni_var = ctx.get('dni_var')
        numero_entry = ctx.get('numero_entry')
        save_client = ctx.get('save_client')
        position_modal = ctx.get('position_modal')
        disable_mousewheel_on = ctx.get('disable_mousewheel_on')

        import tkinter as tk
        from tkinter import ttk, messagebox

        modal = tk.Toplevel(root)
        modal.title("Cuestionamiento de recibo")
        modal.transient(root)
        modal.grab_set()
        try:
            root.update_idletasks()
            main_w = root.winfo_width() or 324
            main_h = root.winfo_height() or 600
            position_modal(modal, int(main_w), int(main_h), side='right')
        except Exception:
            pass
        modal.grid_columnconfigure(0, weight=1)

    # Aplicar tema
        theme = ctx.get('current_theme', 'modern')
        if theme == 'dark':
            modal.configure(bg='#1e1e1e')
        else:
            modal.configure(bg='#f8f9fa')
        submotivo_var = tk.StringVar(value='SVA')
        submotivo_combo = ttk.Combobox(modal, textvariable=submotivo_var, values=['SVA', 'Otros', 'Ajuste'], state='readonly')
        submotivo_combo.grid(row=1, column=0, padx=8, pady=(0,8), sticky='ew')
        disable_mousewheel_on(submotivo_combo)

        sva_frame = ttk.Frame(modal)
        sva_frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=4)
        sva_frame.grid_columnconfigure(0, weight=1)

        titular_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sva_frame, text='Titular (si no está marcado = Usuario)', variable=titular_var).grid(row=0, column=0, sticky='w', pady=(0,6))

        ttk.Label(sva_frame, text="Servicios facturados:", font=("Segoe UI", 10)).grid(row=1, column=0, sticky='w')
        services_frame = ttk.Frame(sva_frame)
        services_frame.grid(row=2, column=0, sticky='nsew', pady=(4,6))

        SVA_SERVICES = [
            'Abaco', 'Babbel', 'Busuu', 'Challenges Arena', 'Claro Juegos', 'CLD_GM Cloud Gaming',
            'Club apps by claro', 'Club Ciencia', 'Contenta', 'Fuze Force', 'Gameeasy', 'Gokids',
            'Goles L1 Max', 'Google play', 'Había una vez', 'Iedukar', 'Inglés Mágico', 'Jenius',
            'Norton Cykadas', 'Pfl', 'Play Kids', 'Rescatel', 'Tono de Espera', 'Zenapp', 'Zenit'
        ]
        service_vars = []
        cols = 3
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
            cb = ttk.Checkbutton(services_frame, text=svc, variable=var)
            cb.grid(row=r, column=c, sticky='w', padx=(0,8), pady=2)

        otro_var = tk.BooleanVar(value=False)
        otro_text_var = tk.StringVar()
        rows = (len(SVA_SERVICES) + cols - 1) // cols
        otro_row = rows
        otro_cb = ttk.Checkbutton(services_frame, text='Otro (especificar)', variable=otro_var)
        otro_cb.grid(row=otro_row, column=0, sticky='w', pady=(6,0))
        otro_entry = ttk.Entry(services_frame, textvariable=otro_text_var)
        otro_entry.grid(row=otro_row, column=1, columnspan=(cols-1), sticky='ew', padx=(6,0), pady=(6,0))

        cuantos_var = tk.StringVar(value='Uno')
        varios_detalle_var = tk.StringVar()

        def update_services_selection():
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
        if theme == 'dark':
            info_text.config(bg='#252526', fg='#cccccc', insertbackground='#007acc')
        else:
            info_text.config(bg='#fffbe6', fg='#000000', insertbackground='#007acc')
        ttk.Label(sva_frame, text="SN:", font=("Segoe UI", 10)).grid(row=5, column=0, sticky='w')
        sn_modal_var = tk.StringVar(value=sn_var.get())
        sn_modal_entry = ttk.Entry(sva_frame, textvariable=sn_modal_var)
        sn_modal_entry.grid(row=6, column=0, sticky='ew', pady=(4,6))

        update_services_selection()

        otros_frame = ttk.Frame(modal)
        otros_frame.grid(row=3, column=0, sticky='nsew', padx=8, pady=4)
        ttk.Label(otros_frame, text="Acción tomada / Observaciones:", font=("Segoe UI", 10)).grid(row=0, column=0, sticky='w')
        otros_text = tk.Text(otros_frame, height=6)
        otros_text.grid(row=1, column=0, sticky='nsew')
        if theme == 'dark':
            otros_text.config(bg='#252526', fg='#cccccc', insertbackground='#007acc')
        else:
            otros_text.config(bg='#fffbe6', fg='#000000', insertbackground='#007acc')

        def refresh_visibility(event=None):
            try:
                if submotivo_var.get() == 'SVA':
                    sva_frame.grid()
                    otros_frame.grid_remove()
                else:
                    otros_frame.grid()
                    sva_frame.grid_remove()
                root.update_idletasks()
                position_modal(modal, max(324, int(root.winfo_width() or 324)), None, side='right')
            except Exception:
                pass

        submotivo_combo.bind('<<ComboboxSelected>>', refresh_visibility)
        refresh_visibility()

        def guardar_cuestionamiento():
            if submotivo_var.get() == 'SVA':
                if not sn_modal_var.get().strip():
                    messagebox.showwarning('Validación', 'La SN debe estar presente')
                    return
                selected = [name for (name, v) in service_vars if v.get()]
                if otro_var.get() and otro_text_var.get().strip():
                    selected.append(otro_text_var.get().strip())
                cuantos_val = 'Uno' if len(selected) == 1 else 'Varios'
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
                    # Usar el método de instancia que delega en ctx['save_client'] si está disponible
                    self.save_client(nombre_var.get(), numero_entry.get(), sn_var.get(), 'Cuestionamiento de recibo - SVA', dni=dni_var.get(), notas=final)
                    try:
                        template_text.delete(1.0, tk.END)
                        template_text.insert(tk.END, final)
                        root.clipboard_clear()
                        root.clipboard_append(final)
                    except Exception:
                        pass
                    print('Registro guardado y plantilla copiada al portapapeles')
                    modal.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo guardar el cuestionamiento: {e}')
            else:
                if not otros_text.get(1.0, tk.END).strip():
                    messagebox.showwarning('Validación', 'Ingresa la acción tomada o la observación')
                    return
                final = f"CUESTIONAMIENTO - {submotivo_var.get()}\n" + otros_text.get(1.0, tk.END).strip()
                try:
                    self.save_client(nombre_var.get(), numero_entry.get(), sn_var.get(), f'Cuestionamiento de recibo - {submotivo_var.get()}', dni=dni_var.get(), notas=final)
                    root.clipboard_clear()
                    root.clipboard_append(final)
                    print('Registro guardado y plantilla copiada al portapapeles')
                    modal.destroy()
                except Exception as e:
                    messagebox.showerror('Error', f'No se pudo guardar el cuestionamiento: {e}')

        ttk.Button(modal, text='Guardar', command=guardar_cuestionamiento).grid(row=4, column=0, pady=8)

    def open_credentials_modal(self):
        root = self.root
        ctx = self.ctx
        from tkinter import ttk, messagebox
        import tkinter as tk
        get_credential = ctx.get('get_credential') if 'get_credential' in ctx else None
        set_credential = ctx.get('set_credential') if 'set_credential' in ctx else None
        position_modal = ctx.get('position_modal')

        modal = tk.Toplevel(root)
        modal.title("Editar credenciales")
        modal.transient(root)
        modal.grab_set()
        try:
            root.update_idletasks()
            main_w = root.winfo_width() or 324
            main_h = root.winfo_height() or 600
            position_modal(modal, int(main_w * 0.6), int(main_h * 0.4), side='right')
        except Exception:
            pass
        modal.grid_columnconfigure(0, weight=1)

    # Aplicar tema
        theme = ctx.get('current_theme', 'modern')
        if theme == 'dark':
            modal.configure(bg='#1e1e1e')
        else:
            modal.configure(bg='#f8f9fa')

        ttk.Label(modal, text="Contraseña VPN:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=(8,2))
        vpn_var = tk.StringVar(value=(get_credential('vpn_password') if get_credential else ''))
        vpn_entry = ttk.Entry(modal, textvariable=vpn_var, show='*')
        vpn_entry.grid(row=1, column=0, padx=8, pady=(0,8), sticky='ew')

        ttk.Label(modal, text="Contraseña SIAC:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky='w', padx=8, pady=(6,2))
        siac_var = tk.StringVar(value=(get_credential('siac_password') if get_credential else ''))
        siac_entry = ttk.Entry(modal, textvariable=siac_var, show='*')
        siac_entry.grid(row=3, column=0, padx=8, pady=(0,8), sticky='ew')

        def guardar_credenciales():
            try:
                if set_credential:
                    set_credential('vpn_password', vpn_var.get())
                    set_credential('siac_password', siac_var.get())
                print('Credenciales guardadas correctamente')
                modal.destroy()
            except Exception as e:
                messagebox.showerror('Error', f'No se pudieron guardar las credenciales: {e}')

        ttk.Button(modal, text='Guardar', command=guardar_credenciales).grid(row=4, column=0, pady=8)

    def open_motivo_modal(self, motivo_name, on_save_callback):
        root = self.root
        ctx = self.ctx
        from tkinter import ttk
        import tkinter as tk
        position_modal = ctx.get('position_modal')

        modal = tk.Toplevel(root)
        modal.title(motivo_name)
        modal.transient(root)
        modal.grab_set()
        try:
            root.update_idletasks()
            main_w = root.winfo_width() or 324
            main_h = root.winfo_height() or 600
            modal_h = max(700, int(main_h * 1.1))
            position_modal(modal, int(max(324, main_w)), int(modal_h), side='right')
        except Exception:
            pass

        header = ttk.Frame(modal)
        header.grid(row=0, column=0, sticky='ew', padx=12, pady=(8,4))
        ttk.Label(header, text=f"Opciones para: {motivo_name}", font=("Segoe UI", 11, "bold")).pack(side='left')

        extra_frame = ttk.Frame(modal)
        extra_frame.grid(row=1, column=0, sticky='nsew', padx=12, pady=4)
        modal.grid_columnconfigure(0, weight=1)
        modal.grid_rowconfigure(1, weight=1)

    # Aplicar tema
        theme = ctx.get('current_theme', 'modern')
        if theme == 'dark':
            modal.configure(bg='#1e1e1e')
        else:
            modal.configure(bg='#f8f9fa')

        extra_label = ttk.Label(extra_frame, text="Detalles:")
        extra_label.grid(row=0, column=0, sticky='w')
        extra_text = tk.Text(extra_frame, height=8, wrap='word')
        extra_text.grid(row=1, column=0, sticky='nsew')
        if theme == 'dark':
            extra_text.config(bg='#252526', fg='#cccccc', insertbackground='#007acc')
        else:
            extra_text.config(bg='#fffbe6', fg='#000000', insertbackground='#007acc')
        extra_frame.grid_rowconfigure(1, weight=1)

        btns = ttk.Frame(modal)
        btns.grid(row=2, column=0, sticky='ew', pady=8, padx=12)

        def _save():
            extra = extra_text.get(1.0, tk.END).strip()
            on_save_callback(extra)
            modal.destroy()

        ttk.Button(btns, text='Guardar', command=_save).pack(side='right', padx=(4,0))
        ttk.Button(btns, text='Cancelar', command=modal.destroy).pack(side='right')
    def open_retencion_modal(self):
        # Modal de Retención: autocompletar desde formulario principal y generar plantilla
        root = self.root
        ctx = self.ctx
        template_text = ctx.get('template_text')
        nombre_var = ctx.get('nombre_var')
        sn_var = ctx.get('sn_var')
        dni_var = ctx.get('dni_var')
        numero_entry = ctx.get('numero_entry')
        save_client = ctx.get('save_client')
        position_modal = ctx.get('position_modal')
        disable_mousewheel_on = ctx.get('disable_mousewheel_on')

        import tkinter as tk
        from tkinter import ttk, messagebox

        modal = tk.Toplevel(root)
        modal.title("Retención")
        modal.transient(root)
        modal.grab_set()
        try:
            root.update_idletasks()
            main_w = root.winfo_width() or 324
            main_h = root.winfo_height() or 600
            position_modal(modal, int(main_w), int(main_h), side='right')
        except Exception:
            pass
        modal.grid_columnconfigure(0, weight=1)

    # Aplicar tema
        theme = ctx.get('current_theme', 'modern')
        if theme == 'dark':
            modal.configure(bg='#1e1e1e')
        else:
            modal.configure(bg='#f8f9fa')

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

        ttk.Label(modal, text="Observaciones:", font=("Segoe UI", 10, "bold")).grid(row=16, column=0, sticky='w', padx=8, pady=(6,2))
        obs_text = tk.Text(modal, height=6)
        obs_text.grid(row=17, column=0, padx=8, pady=(0,6), sticky='nsew')
        if theme == 'dark':
            obs_text.config(bg='#252526', fg='#cccccc', insertbackground='#007acc')
        else:
            obs_text.config(bg='#fffbe6', fg='#000000', insertbackground='#007acc')
        modal.grid_rowconfigure(17, weight=1)

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
                self.save_client(nombre_var.get(), numero_entry.get(), sn_var.get(), 'Retención', tipo_solicitud=tipo_solicitud_var.get(), motivo_solicitud=motivo_solicitud_var.get(), nombre_titular=nombre_titular_var.get(), dni=dni_modal_var.get(), telefono_contacto=tel_contacto_var.get(), telefono_afectado=tel_afectado_var.get(), accion_ofrecida=accion_var.get(), notas=final)
                try:
                    template_text.delete(1.0, tk.END)
                    template_text.insert(tk.END, final)
                    root.clipboard_clear()
                    root.clipboard_append(final)
                except Exception:
                    pass
                print('Retención guardada y plantilla copiada al portapapeles')
                modal.destroy()
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo guardar retención: {e}')

        ttk.Button(modal, text='Guardar', command=guardar_retencion).grid(row=18, column=0, columnspan=2, pady=8)

    # Clase auxiliar para gestionar ventanas modales independientes de ui.py.
    # El objetivo es centralizar la lógica de los diálogos modales y evitar dependencias directas con la interfaz principal.
    def __init__(self, root, ctx):
        # Referencia a la ventana principal
        self.root = root
        # ctx es un diccionario con referencias a variables y funciones externas necesarias
        self.ctx = ctx

        # Posicionamiento por defecto eliminado (no se usa aquí)

    def disable_mousewheel_on(self, widget):
        # Deshabilita el scroll con la rueda del mouse en un widget, si hay helper externo.
        try:
            fn = self.ctx.get('disable_mousewheel_on')
            if callable(fn):
                fn(widget)
        except Exception:
            pass

    def save_client(self, *args, **kwargs):
        # Guarda los datos del cliente usando una función externa pasada en el contexto.
        try:
            fn = self.ctx.get('save_client')
            if callable(fn):
                return fn(*args, **kwargs)
        except Exception:
            raise

    def open_otros_modal(self):
        # Abre una ventana modal para registrar consultas de tipo 'Otros'.
        root = self.root
        ctx = self.ctx
        # Obtenemos referencias a variables y widgets externos
        template_text = ctx.get('template_text')
        nombre_var = ctx.get('nombre_var')
        sn_var = ctx.get('sn_var')
        dni_var = ctx.get('dni_var')
        numero_entry = ctx.get('numero_entry')

        # Creamos la ventana modal
        modal = tk.Toplevel(root)
        modal.title("Otros - Detalle")
        modal.transient(root)
        modal.grab_set()  # Bloquea la ventana principal hasta cerrar el modal
        try:
            # Calculamos tamaño y posición del modal
            root.update_idletasks()
            main_w = root.winfo_width() or 324
            main_h = root.winfo_height() or 600
            self.position_modal(modal, int(max(324, main_w)), int(max(400, int(main_h * 0.6))), side='right')
        except Exception:
            pass
        modal.grid_columnconfigure(0, weight=1)

    def open_lista_atenciones_modal(self):
        """Muestra un modal con las atenciones registradas, ordenadas por fecha.
        Left: Treeview con fecha, nombre, numero y motivo. Right: panel detalle con notas completas.
        """
        root = self.root
        ctx = self.ctx
        position_modal = ctx.get('position_modal')

        import tkinter as tk
        from tkinter import ttk, messagebox
        try:
            from db import get_clients_grouped_by_day
        except Exception:
            get_clients_grouped_by_day = None

        modal = tk.Toplevel(root)
        modal.title('Lista de Atenciones')
        modal.transient(root)
        modal.grab_set()
        try:
            root.update_idletasks()
            main_w = root.winfo_width() or 800
            main_h = root.winfo_height() or 600
            position_modal(modal, int(main_w * 0.8), int(main_h * 0.8), side='right')
        except Exception:
            pass
        modal.grid_columnconfigure(0, weight=1)
        modal.grid_rowconfigure(0, weight=1)

        container = ttk.Frame(modal)
        container.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)

        # Treeview a la izquierda
        cols = ('fecha', 'nombre', 'numero', 'motivo')
        tree = ttk.Treeview(container, columns=cols, show='headings', selectmode='browse')
        for c in cols:
            tree.heading(c, text=c.capitalize())
            tree.column(c, width=150, anchor='w')
        tree.grid(row=0, column=0, sticky='nsew', padx=(0,8))

        # Panel de detalle a la derecha
        detail_frame = ttk.Frame(container)
        detail_frame.grid(row=0, column=1, sticky='nsew')
        ttk.Label(detail_frame, text='Detalle', font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        detail_text = tk.Text(detail_frame, wrap='word')
        detail_text.pack(fill='both', expand=True, pady=(6,0))

        # Cargar datos desde DB
        rows = []
        try:
            if get_clients_grouped_by_day:
                rows = get_clients_grouped_by_day(1000)
            else:
                rows = []
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo cargar la lista: {e}')

        # Insertar en el treeview
        for r in rows:
            fecha = r.get('fecha_llamada')
            if fecha is None:
                fecha_str = ''
            else:
                fecha_str = str(fecha)
            tree.insert('', 'end', iid=str(r.get('id')), values=(fecha_str, r.get('nombre'), r.get('numero'), r.get('motivo_llamada')))

        def on_select(event=None):
            sel = tree.selection()
            if not sel:
                return
            iid = sel[0]
            # Encontrar fila
            for r in rows:
                if str(r.get('id')) == iid:
                    detail_text.delete(1.0, tk.END)
                    detail_text.insert(tk.END, f"ID: {r.get('id')}\n")
                    detail_text.insert(tk.END, f"Nombre: {r.get('nombre')}\n")
                    detail_text.insert(tk.END, f"Número: {r.get('numero')}\n")
                    detail_text.insert(tk.END, f"SN: {r.get('sn')}\n")
                    detail_text.insert(tk.END, f"DNI: {r.get('dni')}\n")
                    detail_text.insert(tk.END, f"Motivo: {r.get('motivo_llamada')}\n")
                    detail_text.insert(tk.END, "\nNotas:\n")
                    detail_text.insert(tk.END, r.get('notas') or '')
                    break

        tree.bind('<<TreeviewSelect>>', on_select)

        # Botón de cerrar
        btns = ttk.Frame(modal)
        btns.grid(row=1, column=0, sticky='ew', padx=8, pady=8)
        ttk.Button(btns, text='Cerrar', command=modal.destroy).pack(side='right')

    # Aplicar tema
        theme = ctx.get('current_theme', 'modern')
        if theme == 'dark':
            modal.configure(bg='#1e1e1e')
        else:
            modal.configure(bg='#f8f9fa')

        # Campo para el motivo de la consulta
        ttk.Label(modal, text="El motivo de la consulta:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=(8,2))
        motivo_consulta_var = tk.StringVar()
        motivo_consulta_entry = ttk.Entry(modal, textvariable=motivo_consulta_var)
        motivo_consulta_entry.grid(row=1, column=0, padx=8, pady=(0,6), sticky='ew')

        # Campo para la solución brindada
        ttk.Label(modal, text="La solución o información brindada:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky='w', padx=8, pady=(6,2))
        solucion_text = tk.Text(modal, height=6)
        solucion_text.grid(row=3, column=0, padx=8, pady=(0,6), sticky='nsew')
        if theme == 'dark':
            solucion_text.config(bg='#252526', fg='#cccccc', insertbackground='#007acc')
        else:
            solucion_text.config(bg='#fffbe6', fg='#000000', insertbackground='#007acc')

        # Campo para el número de serie (SN)
        ttk.Label(modal, text="SN:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky='w', padx=8, pady=(6,2))
        sn_local_var = tk.StringVar(value=(sn_var.get() if sn_var else ''))
        sn_local_entry = ttk.Entry(modal, textvariable=sn_local_var)
        sn_local_entry.grid(row=5, column=0, padx=8, pady=(0,6), sticky='ew')
 
    def open_tecnica_modal(self):
        """Abre el modal de Atención Técnica con ancho fijo 324, sin campo de detalle y sin botón Cancelar."""
        root = self.root
        ctx = self.ctx
        template_text = ctx.get('template_text')
        nombre_var = ctx.get('nombre_var')
        numero_var = ctx.get('numero_var')
        sn_var = ctx.get('sn_var')
        dni_var = ctx.get('dni_var')
        position_modal = ctx.get('position_modal')
        disable_mousewheel_on = ctx.get('disable_mousewheel_on')

        import tkinter as tk
        from tkinter import ttk, messagebox

        modal = tk.Toplevel(root)
        modal.title("Atención Técnica")
        modal.transient(root)
        modal.grab_set()
        modal.minsize(324, 220)
        try:
            root.update_idletasks()
            main_h = root.winfo_height() or 600
            # ancho fijo 324
            self.position_modal(modal, 324, int(max(360, int(main_h * 0.5))), side='right')
        except Exception:
            pass
        modal.grid_columnconfigure(0, weight=1)

        # Aplicar tema
        theme = ctx.get('current_theme', 'modern')
        if theme == 'dark':
            modal.configure(bg='#1e1e1e')
        else:
            modal.configure(bg='#f8f9fa')

        # Encabezado
        header = ttk.Frame(modal)
        header.grid(row=0, column=0, sticky='ew', padx=8, pady=(8,4))
        ttk.Label(header, text="Atención Técnica", font=("Segoe UI", 11, "bold")).pack(side='left')
        ttk.Separator(modal, orient='horizontal').grid(row=1, column=0, sticky='ew', padx=8, pady=(0,8))

        # Campos
        ttk.Label(modal, text="Nombre del cliente:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky='w', padx=8, pady=(6,2))
        nombre_tec_var = tk.StringVar(value=(nombre_var.get() if nombre_var else ''))
        ttk.Entry(modal, textvariable=nombre_tec_var).grid(row=3, column=0, sticky='ew', padx=8, pady=(0,6))

        ttk.Label(modal, text="Línea afectada:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky='w', padx=8, pady=(6,2))
        linea_var = tk.StringVar(value=(numero_var.get() if numero_var else ''))
        ttk.Entry(modal, textvariable=linea_var).grid(row=5, column=0, sticky='ew', padx=8, pady=(0,6))

        ttk.Label(modal, text="Inconveniente reportado:", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky='w', padx=8, pady=(6,2))
        tec_options = [
            'Inconvenientes con Llamadas e Internet',
            'Inconvenientes con Llamadas',
            'Inconvenientes con Internet',
            'Inconvenientes con Redes Sociales / Otras Apps',
            'Inconvenientes con SMS'
        ]
        tec_var = tk.StringVar(value=tec_options[0])
        tec_combo = ttk.Combobox(modal, textvariable=tec_var, values=tec_options, state='readonly')
        tec_combo.grid(row=7, column=0, sticky='ew', padx=8, pady=(0,6))
        # Deshabilitar scroll accidental
        try:
            if callable(disable_mousewheel_on):
                disable_mousewheel_on(tec_combo)
        except Exception:
            pass

        ttk.Label(modal, text="Línea adicional:", font=("Segoe UI", 10, "bold")).grid(row=8, column=0, sticky='w', padx=8, pady=(6,2))
        linea_add_var = tk.StringVar()
        ttk.Entry(modal, textvariable=linea_add_var).grid(row=9, column=0, sticky='ew', padx=8, pady=(0,6))

        def guardar_tecnica():
            # Validaciones mínimas
            if not nombre_tec_var.get().strip():
                messagebox.showwarning('Validación', 'Ingresa el nombre del cliente')
                return
            if not linea_var.get().strip():
                messagebox.showwarning('Validación', 'Ingresa la línea afectada')
                return

            incon = tec_var.get()
            linea_add = linea_add_var.get().strip()

            # Construimos el texto final a guardar y copiar
            final = (
                f"Nombre del cliente: {nombre_tec_var.get().strip()}\n"
                + f"Línea afectada: {linea_var.get().strip()}\n"
                + f"Inconveniente reportado: {incon}\n"
                + (f"*Línea adicional: {linea_add}\n" if linea_add else "")
            )
            try:
                try:
                    self.save_client(nombre_tec_var.get(), linea_var.get(), (sn_var.get() if sn_var else ''), 'Atención Técnica', dni=(dni_var.get() if dni_var else ''), notas=final)
                except Exception:
                    pass
                try:
                    if template_text:
                        template_text.delete(1.0, tk.END)
                        template_text.insert(tk.END, final)
                        root.clipboard_clear()
                        root.clipboard_append(final)
                except Exception:
                    pass
                print('Atención Técnica guardada y plantilla copiada al portapapeles')
                modal.destroy()
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo guardar: {e}')

        # Botones: solo Guardar (sin Cancelar)
        btns = ttk.Frame(modal)
        btns.grid(row=10, column=0, sticky='ew', padx=8, pady=8)
        guardar_btn = ttk.Button(btns, text='Guardar', command=guardar_tecnica, style='TButton')
        guardar_btn.pack(side='right', padx=(4,0))