# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox

try:
    # Intenta importar la función para obtener clientes desde el módulo de base de datos.
    from db import get_clients_grouped_by_day
except ImportError:
    # Si la importación falla, asigna None para manejar la ausencia de la función.
    get_clients_grouped_by_day = None

class BaseModal(tk.Toplevel):
    """Clase base para todas las ventanas modales de la aplicación."""
    def __init__(self, parent, title, ctx):
        super().__init__(parent)
        self.title(title)  # Título de la ventana.
        self.transient(parent)  # La modal siempre estará sobre la ventana principal.
        self.grab_set()  # Captura todos los eventos, bloqueando la ventana principal.
        self.root = parent  # Referencia a la ventana principal.
        self.ctx = ctx  # Contexto de la aplicación con helpers y variables.
        self.theme = self.ctx.get('current_theme', 'modern')  # Tema actual.
        self._apply_theme()  # Aplica el tema visual.
        self._get_helpers_from_context()  # Carga funciones de ayuda desde el contexto.

    def _apply_theme(self):
        """Aplica el color de fondo según el tema actual."""
        themes = self.ctx.get('THEMES', {})
        if themes and self.theme in themes:
            bg_color = themes[self.theme].get('bg', '#f8f9fa')
        else:
            # Colores por defecto si el tema no está definido.
            bg_color = '#1e1e1e' if self.theme == 'dark' else '#f8f9fa'
        self.configure(bg=bg_color)

    def _get_helpers_from_context(self):
        """Carga funciones de ayuda desde el contexto de la aplicación."""
        self.position_modal = self.ctx.get('position_modal')
        self.disable_mousewheel_on = self.ctx.get('disable_mousewheel_on')
        self.save_client_func = self.ctx.get('save_client')
        self.get_credential_func = self.ctx.get('get_credential')
        self.set_credential_func = self.ctx.get('set_credential')

    def _get_vars_from_context(self, var_names):
        """Obtiene un diccionario de variables de Tkinter desde el contexto."""
        return {name: self.ctx.get(name) for name in var_names}

    def _set_initial_geometry(self, width=None, height=None, side='right'):
        """Posiciona la modal en la pantalla usando una función de ayuda."""
        if self.position_modal: self.position_modal(self, width, height, side)

class RetencionModal(BaseModal):
    """Modal para gestionar un caso de retención de cliente."""
    def __init__(self, parent, ctx):
        super().__init__(parent, "Retención", ctx)
        # Carga las variables necesarias desde el contexto.
        self.vars = self._get_vars_from_context(['nombre_var', 'sn_var', 'dni_var', 'numero_var'])
        self._create_widgets()  # Crea los componentes de la interfaz.
        self._set_initial_geometry(width=324)  # Ajusta la geometría inicial.

    def _create_widgets(self):
        """Crea y posiciona los widgets en la ventana modal."""
        self.grid_columnconfigure(0, weight=1)
        # Variables de Tkinter para los campos del formulario.
        self.sn_modal_var = tk.StringVar(value=self.vars['sn_var'].get())
        self.tipo_solicitud_var = tk.StringVar(value='Cancelación')
        self.motivo_solicitud_var = tk.StringVar(value='Motivos Económicos')
        self.nombre_titular_var = tk.StringVar(value=self.vars['nombre_var'].get())
        self.dni_modal_var = tk.StringVar(value=self.vars['dni_var'].get())
        self.tel_contacto_var = tk.StringVar(value=self.vars['numero_var'].get())
        self.tel_afectado_var = tk.StringVar(value=self.vars['numero_var'].get())
        self.accion_var = tk.StringVar()

        # --- Creación de campos compactos ---
        row = 0
        # Campo SN
        ttk.Label(self, text="SN:", font=("Segoe UI", 10)).grid(row=row, column=0, sticky='w', padx=4, pady=(4,1)); row += 1
        ttk.Entry(self, textvariable=self.sn_modal_var).grid(row=row, column=0, padx=4, pady=(0,3), sticky='ew'); row += 1
        # Campo Tipo de Solicitud
        ttk.Label(self, text="Tipo de Solicitud:", font=("Segoe UI", 10)).grid(row=row, column=0, sticky='w', padx=4, pady=(4,1)); row += 1
        self.tipo_solicitud_combo = ttk.Combobox(self, textvariable=self.tipo_solicitud_var, state='readonly', values=['Cancelación', 'Migración', 'Portabilidad', 'Incumplimiento'])
        self.tipo_solicitud_combo.grid(row=row, column=0, padx=4, pady=(0,3), sticky='ew'); row += 1
        self.disable_mousewheel_on(self.tipo_solicitud_combo)
        # Campos dinámicos: Motivo de Solicitud y Teléfono
        self.motivo_label = ttk.Label(self, text="Motivo de Solicitud:", font=("Segoe UI", 10))
        self.motivo_label.grid(row=row, column=0, sticky='w', padx=4, pady=(4,1)); row += 1
        self.motivo_solicitud_combo = ttk.Combobox(self, textvariable=self.motivo_solicitud_var, state='readonly', values=['Cuestionamiento', 'Motivos Económicos', 'No usa el servicio', 'Inconveniente con el servicio', 'Inconforme con los beneficios', 'Otros'])
        self.motivo_solicitud_combo.grid(row=row, column=0, padx=4, pady=(0,3), sticky='ew'); row += 1
        self.disable_mousewheel_on(self.motivo_solicitud_combo)
        self.motivo_otro_var = tk.StringVar()
        self.motivo_otro_entry = ttk.Entry(self, textvariable=self.motivo_otro_var)
        self.motivo_incumplimiento_var = tk.StringVar(value='BONO')
        self.motivo_incumplimiento_combo = ttk.Combobox(self, textvariable=self.motivo_incumplimiento_var, state='readonly', values=['BONO', 'OCC', 'NC'])
        self.motivo_incumplimiento_label = ttk.Label(self, text="Seleccionar motivo de Incumplimiento:", font=("Segoe UI", 10))
        self.tel_label = ttk.Label(self, text="Teléfono de contacto:", font=("Segoe UI", 10))
        self.tel_entry = ttk.Entry(self, textvariable=self.tel_contacto_var)
        self.tel_entry.grid(row=row, column=0, padx=4, pady=(0,3), sticky='ew'); row += 1
        # Campo Acción ofrecida
        self.accion_label = ttk.Label(self, text="Acción ofrecida:", font=("Segoe UI", 10))
        self.accion_entry = ttk.Entry(self, textvariable=self.accion_var)
        self.accion_label.grid(row=row, column=0, sticky='w', padx=4, pady=(4,1)); row += 1
        self.accion_entry.grid(row=row, column=0, padx=4, pady=(0,3), sticky='ew'); row += 1
        
        # --- Lógica para mostrar/ocultar campos dinámicamente ---
        def update_motivo_combo(*a):
            """Ajusta la visibilidad de los campos según el tipo de solicitud."""
            if self.tipo_solicitud_var.get() == 'Incumplimiento':
                # Oculta campos de motivo general y muestra los de incumplimiento.
                self.motivo_label.grid_remove()
                self.motivo_solicitud_combo.grid_remove()
                self.motivo_otro_entry.grid_remove()
                self.motivo_incumplimiento_label.grid(row=6, column=0, sticky='w', padx=4, pady=(4,1))
                self.motivo_incumplimiento_combo.grid(row=7, column=0, padx=4, pady=(0,3), sticky='ew')
                self.tel_label.grid(row=8, column=0, sticky='w', padx=4, pady=(4,1))
                self.tel_entry.grid(row=9, column=0, padx=4, pady=(0,3), sticky='ew')
                self.accion_label.grid_remove() # Oculta acción ofrecida
                self.accion_entry.grid_remove()
            else:
                # Muestra campos de motivo general y oculta los de incumplimiento.
                self.motivo_incumplimiento_label.grid_remove()
                self.motivo_incumplimiento_combo.grid_remove()
                self.tel_label.grid_remove()
                self.motivo_label.grid(row=6, column=0, sticky='w', padx=4, pady=(4,1))
                self.motivo_solicitud_combo.grid(row=7, column=0, padx=4, pady=(0,3), sticky='ew')
                # Muestra campo de texto para "Otros".
                if self.motivo_solicitud_var.get() == 'Otros':
                    self.motivo_otro_entry.grid(row=8, column=0, padx=4, pady=(0,3), sticky='ew')
                else:
                    self.motivo_otro_entry.grid_remove()
                self.tel_entry.grid(row=9, column=0, padx=4, pady=(0,3), sticky='ew')
                self.accion_label.grid(row=10, column=0, sticky='w', padx=4, pady=(4,1)) # Muestra acción ofrecida
                self.accion_entry.grid(row=11, column=0, padx=4, pady=(0,3), sticky='ew')
        
        # Asocia la función de actualización a los cambios en las variables.
        self.tipo_solicitud_var.trace_add('write', update_motivo_combo)
        self.motivo_solicitud_var.trace_add('write', update_motivo_combo)
        update_motivo_combo()  # Llama a la función para el estado inicial.
        ttk.Button(self, text='Guardar', command=self._save).grid(row=12, column=0, pady=6)

    def _refresh_accion(self, *args):
        """(No utilizado actualmente) Sugiere una acción basada en el tipo y motivo."""
        acciones_map = {'Cancelación': {'Motivos Económicos': 'Ofrecer descuento / negociar ahorro', 'No usa el servicio': 'Ofrecer plan alternativo / pausar servicio', 'Inconveniente con el servicio': 'Solución técnica / crédito', 'Inconforme con los beneficios': 'Presentar alternativas / mejora de plan', 'Cuestionamiento': 'Revisar cargos y explicar detalles', 'Otros': 'Registrar caso y escalar'}, 'Migración': {'default': 'Ofrecer migración y validar compatibilidad'}, 'Portabilidad': {'default': 'Iniciar trámite de portabilidad y dar instrucciones'}}
        t, m = self.tipo_solicitud_var.get(), self.motivo_solicitud_var.get()
        self.accion_var.set(acciones_map.get(t, {}).get(m, acciones_map.get(t, {}).get('default', '')))

    def _save(self):
        """Valida los datos y genera la plantilla de texto para ser guardada."""
        if not self.nombre_titular_var.get().strip() or not self.dni_modal_var.get().strip():
            messagebox.showwarning('Validación', 'El nombre del titular y el DNI son obligatorios', parent=self)
            return
        
        if self.tipo_solicitud_var.get() == 'Incumplimiento':
            motivo = self.motivo_incumplimiento_var.get()
            plantilla = f"SN: {self.sn_modal_var.get()}\nTipo de Solicitud: Incumplimiento de Ofrecimiento\nMotivo de Solicitud: {motivo}\nNombre del titular: {self.nombre_titular_var.get()}\nDNI: {self.dni_modal_var.get()}\nTeléfono de contacto: {self.tel_contacto_var.get()}\nTeléfono afectado: {self.tel_afectado_var.get()}"
        else:
            motivo = self.motivo_solicitud_var.get()
            if motivo == 'Otros':
                motivo = self.motivo_otro_var.get()
            plantilla = f"SN: {self.sn_modal_var.get()}\nTipo de Solicitud: {self.tipo_solicitud_var.get()}\nMotivo de Solicitud: {motivo}\nNombre del titular: {self.nombre_titular_var.get()}\nDNI: {self.dni_modal_var.get()}\nTeléfono de contacto: {self.tel_contacto_var.get()}\nTeléfono afectado: {self.tel_afectado_var.get()}\nAcción ofrecida: {self.accion_var.get()}"
        
        # Actualiza el campo de texto principal en lugar de guardar directamente.
        template_text = self.ctx.get('template_text')
        if template_text:
            template_text.delete(1.0, tk.END)
            template_text.insert(tk.END, plantilla)
            self.root.clipboard_clear()
            self.root.clipboard_append(plantilla) # Copia al portapapeles.
        
        print('Retención preparada en plantilla y copiada al portapapeles')
        self.destroy() # Cierra la modal.

class CuestionamientoModal(BaseModal):
    """Modal para gestionar un cuestionamiento de recibo."""
    def __init__(self, parent, ctx):
        super().__init__(parent, "Cuestionamiento de recibo", ctx)
        self.vars = self._get_vars_from_context(['nombre_var', 'sn_var', 'dni_var', 'numero_var'])
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea los widgets, incluyendo los frames para SVA y Otros."""
        self.grid_columnconfigure(0, weight=1)
        self.submotivo_var = tk.StringVar(value='SVA')
        submotivo_combo = ttk.Combobox(self, textvariable=self.submotivo_var, values=['SVA', 'Otros', 'Ajuste'], state='readonly')
        submotivo_combo.grid(row=1, column=0, padx=8, pady=(0,8), sticky='ew')
        self.disable_mousewheel_on(submotivo_combo)

        self.sva_frame = self._create_sva_frame() # Frame para submotivo SVA.
        self.otros_frame = self._create_otros_frame() # Frame para otros submotivos.
        
        self.submotivo_var.trace_add('write', self._refresh_visibility)
        self._refresh_visibility() # Ajusta visibilidad inicial.
        ttk.Button(self, text='Guardar', command=self._save).grid(row=4, column=0, pady=8)

    def _create_sva_frame(self):
        """Crea el frame con los campos específicos para SVA."""
        frame = ttk.Frame(self); frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=4); frame.grid_columnconfigure(0, weight=1)
        self.titular_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text='Titular (si no está marcado = Usuario)', variable=self.titular_var).grid(row=0, column=0, sticky='w', pady=(0,6))
        ttk.Label(frame, text="Servicios facturados:").grid(row=1, column=0, sticky='w')
        services_frame = ttk.Frame(frame); services_frame.grid(row=2, column=0, sticky='nsew', pady=(4,6))
        
        SVA_SERVICES = ['Abaco', 'Babbel', 'Busuu', 'Challenges Arena', 'Claro Juegos', 'CLD_GM Cloud Gaming', 'Club apps by claro', 'Club Ciencia', 'Contenta', 'Fuze Force', 'Gameeasy', 'Gokids', 'Goles L1 Max', 'Google play', 'Había una vez', 'Iedukar', 'Inglés Mágico', 'Jenius', 'Norton Cykadas', 'Pfl', 'Play Kids', 'Rescatel', 'Tono de Espera', 'Zenapp', 'Zenit']
        self.service_vars = []
        # Crea checkboxes para cada servicio SVA.
        for i, svc in enumerate(SVA_SERVICES):
            var = tk.BooleanVar(value=(svc == 'Club Ciencia')); self.service_vars.append((svc, var))
            ttk.Checkbutton(services_frame, text=svc, variable=var, command=self._update_services_selection).grid(row=i//3, column=i%3, sticky='w', padx=(0,8), pady=2)

        self.otro_var = tk.BooleanVar(); self.otro_text_var = tk.StringVar()
        otro_row = (len(SVA_SERVICES) + 2) // 3
        ttk.Checkbutton(services_frame, text='Otro', variable=self.otro_var, command=self._update_services_selection).grid(row=otro_row, column=0, sticky='w', pady=(6,0))
        ttk.Entry(services_frame, textvariable=self.otro_text_var).grid(row=otro_row, column=1, columnspan=2, sticky='ew', padx=(6,0), pady=(6,0))

        ttk.Label(frame, text="Información entregada:").grid(row=3, column=0, sticky='w'); self.info_text = tk.Text(frame, height=4); self.info_text.grid(row=4, column=0, sticky='nsew', pady=(4,6))
        ttk.Label(frame, text="SN:").grid(row=5, column=0, sticky='w'); self.sn_modal_var = tk.StringVar(value=self.vars['sn_var'].get()); ttk.Entry(frame, textvariable=self.sn_modal_var).grid(row=6, column=0, sticky='ew', pady=(4,6))
        self._update_services_selection()
        return frame

    def _create_otros_frame(self):
        """Crea el frame para submotivos 'Otros' o 'Ajuste'."""
        frame = ttk.Frame(self); frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=4); frame.grid_remove()
        ttk.Label(frame, text="Acción tomada / Observaciones:").grid(row=0, column=0, sticky='w')
        self.otros_text = tk.Text(frame, height=6); self.otros_text.grid(row=1, column=0, sticky='nsew')
        return frame

    def _update_services_selection(self):
        """Actualiza la lista de servicios SVA seleccionados."""
        self.selected_services = [name for name, var in self.service_vars if var.get()]
        if self.otro_var.get() and self.otro_text_var.get().strip(): self.selected_services.append(self.otro_text_var.get().strip())

    def _refresh_visibility(self, *args):
        """Muestra u oculta los frames según el submotivo seleccionado."""
        if self.submotivo_var.get() == 'SVA': self.sva_frame.grid(); self.otros_frame.grid_remove()
        else: self.sva_frame.grid_remove(); self.otros_frame.grid()
        self.root.update_idletasks(); self._set_initial_geometry(width=324)

    def _save(self):
        """Genera la plantilla de texto según el submotivo y los datos ingresados."""
        if self.submotivo_var.get() == 'SVA':
            if not self.sn_modal_var.get().strip(): messagebox.showwarning('Validación', 'La SN debe estar presente', parent=self); return
            cuantos = 'Uno' if len(self.selected_services) == 1 else 'Varios'
            detalle = self.selected_services[0] if cuantos == 'Uno' and self.selected_services else (', '.join(self.selected_services) if self.selected_services else '')
            final = f"1: Indicar quien se comunica (Usuario o Titular): {'Titular' if self.titular_var.get() else 'Usuario'}\n2: Cuantos servicio tiene facturado (Uno o Varios) detalla: {cuantos}{f' - {detalle}' if detalle else ''}\n3: Detalla la información entregada al cliente: {self.info_text.get(1.0, tk.END).strip()}\n4: SN: {self.sn_modal_var.get().strip()}"
            motivo = 'Cuestionamiento de recibo - SVA'
        else:
            final = self.otros_text.get(1.0, tk.END).strip()
            if not final: messagebox.showwarning('Validación', 'Ingresa la acción tomada o la observación', parent=self); return
            motivo = f'Cuestionamiento de recibo - {self.submotivo_var.get()}'
        
        # Actualiza el campo de texto principal y copia al portapapeles.
        template_text = self.ctx.get('template_text')
        if template_text:
            template_text.delete(1.0, tk.END)
            template_text.insert(tk.END, final)
            self.root.clipboard_clear()
            self.root.clipboard_append(final)
        
        print('Registro preparado en plantilla y copiado al portapapeles')
        self.destroy()

class TecnicaModal(BaseModal):
    """Modal para registrar una atención técnica."""
    def __init__(self, parent, ctx):
        super().__init__(parent, "Atención Técnica", ctx)
        self.vars = self._get_vars_from_context(['nombre_var', 'numero_var', 'sn_var', 'dni_var'])
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea los campos para el registro de atención técnica."""
        self.grid_columnconfigure(0, weight=1)
        self.nombre_tec_var = tk.StringVar(value=self.vars['nombre_var'].get())
        self.linea_var = tk.StringVar(value=self.vars['numero_var'].get())
        self.linea_add_var = tk.StringVar()
        tec_options = ['Inconvenientes con Llamadas e Internet', 'Inconvenientes con Llamadas', 'Inconvenientes con Internet', 'Inconvenientes con Redes Sociales / Otras Apps', 'Inconvenientes con SMS']
        self.tec_var = tk.StringVar(value=tec_options[0])

        fields = [("Nombre del cliente:", self.nombre_tec_var, ttk.Entry), ("Línea afectada:", self.linea_var, ttk.Entry), ("Inconveniente reportado:", self.tec_var, ttk.Combobox, {'state': 'readonly', 'values': tec_options}), ("Línea adicional:", self.linea_add_var, ttk.Entry)]
        row = 0
        # Crea los campos de forma iterativa.
        for label, var, widget_class, *opts in fields:
            ttk.Label(self, text=label, font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky='w', padx=8, pady=(8,2)); row += 1
            w = widget_class(self, textvariable=var, **(opts[0] if opts else {})); w.grid(row=row, column=0, padx=8, pady=(0,6), sticky='ew'); row += 1
            if widget_class == ttk.Combobox: self.disable_mousewheel_on(w)
        
        ttk.Button(self, text='Guardar', command=self._save).grid(row=row, column=0, pady=8)

    def _save(self):
        """Valida y genera la plantilla para la atención técnica."""
        if not self.nombre_tec_var.get().strip() or not self.linea_var.get().strip(): messagebox.showwarning('Validación', 'El nombre y la línea son obligatorios', parent=self); return
        linea_add = self.linea_add_var.get().strip()
        final = f"Nombre del cliente: {self.nombre_tec_var.get().strip()}\nLínea afectada: {self.linea_var.get().strip()}\nInconveniente reportado: {self.tec_var.get()}" + (f"\n*Línea adicional: {linea_add}" if linea_add else "")
        
        # Actualiza la plantilla principal.
        template_text = self.ctx.get('template_text')
        if template_text:
            template_text.delete(1.0, tk.END)
            template_text.insert(tk.END, final)
            self.root.clipboard_clear()
            self.root.clipboard_append(final)
        
        print('Atención Técnica preparada en plantilla y copiada'); self.destroy()

class CredentialsModal(BaseModal):
    """Modal para editar y guardar las credenciales del usuario."""
    def __init__(self, parent, ctx):
        super().__init__(parent, "Editar credenciales", ctx)
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea los campos para las contraseñas de VPN y SIAC."""
        self.grid_columnconfigure(0, weight=1)
        self.vpn_var = tk.StringVar(value=(self.get_credential_func('vpn_password') or ''))
        self.siac_var = tk.StringVar(value=(self.get_credential_func('siac_password') or ''))
        ttk.Label(self, text="Contraseña VPN:").grid(row=0, column=0, sticky='w', padx=8, pady=(8,2))
        ttk.Entry(self, textvariable=self.vpn_var, show='*').grid(row=1, column=0, padx=8, pady=(0,8), sticky='ew')
        ttk.Label(self, text="Contraseña SIAC:").grid(row=2, column=0, sticky='w', padx=8, pady=(6,2))
        ttk.Entry(self, textvariable=self.siac_var, show='*').grid(row=3, column=0, padx=8, pady=(0,8), sticky='ew')
        ttk.Button(self, text='Guardar', command=self._save).grid(row=4, column=0, pady=8)

    def _save(self):
        """Guarda las credenciales utilizando la función del contexto."""
        try:
            self.set_credential_func('vpn_password', self.vpn_var.get())
            self.set_credential_func('siac_password', self.siac_var.get())
            print('Credenciales guardadas'); self.destroy()
        except Exception as e:
            messagebox.showerror('Error', f'No se pudieron guardar: {e}', parent=self)

class ListaAtencionesModal(BaseModal):
    """Modal para mostrar una lista de atenciones pasadas desde la base de datos."""
    def __init__(self, parent, ctx):
        super().__init__(parent, "Lista de Atenciones", ctx)
        self._create_widgets()
        self._set_initial_geometry(width=800, height=600) # Geometría más grande

    def _create_widgets(self):
        """Crea un Treeview para mostrar la lista y un área de texto para los detalles."""
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        container = ttk.Frame(self); container.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
        container.grid_columnconfigure(0, weight=3); container.grid_columnconfigure(1, weight=2); container.grid_rowconfigure(0, weight=1)
        
        cols = ('fecha', 'nombre', 'numero', 'motivo'); self.tree = ttk.Treeview(container, columns=cols, show='headings', selectmode='browse')
        for c in cols: self.tree.heading(c, text=c.capitalize()); self.tree.column(c, width=150, anchor='w')
        self.tree.grid(row=0, column=0, sticky='nsew', padx=(0,8))
        
        detail_frame = ttk.Frame(container); detail_frame.grid(row=0, column=1, sticky='nsew')
        ttk.Label(detail_frame, text='Detalle').pack(anchor='w')
        self.detail_text = tk.Text(detail_frame, wrap='word'); self.detail_text.pack(fill='both', expand=True, pady=(6,0))
        
        self._load_data()
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        ttk.Button(self, text='Cerrar', command=self.destroy).grid(row=1, column=0, sticky='e', padx=8, pady=8)

    def _load_data(self):
        """Carga los datos de atenciones desde la base de datos y los inserta en el Treeview."""
        try: self.rows = get_clients_grouped_by_day(1000) if get_clients_grouped_by_day else []
        except Exception as e: messagebox.showerror('Error', f'No se pudo cargar la lista: {e}'); self.rows = []
        for r in self.rows: self.tree.insert('', 'end', iid=str(r.get('id')), values=(str(r.get('fecha_llamada','')), r.get('nombre'), r.get('numero'), r.get('motivo_llamada')))

    def _on_select(self, event=None):
        """Muestra los detalles de la atención seleccionada en el área de texto."""
        sel = self.tree.selection();
        if not sel: return
        for r in self.rows:
            if str(r.get('id')) == sel[0]:
                self.detail_text.delete(1.0, tk.END)
                self.detail_text.insert(tk.END, f"ID: {r.get('id')}\nNombre: {r.get('nombre')}\nNúmero: {r.get('numero')}\nSN: {r.get('sn')}\nDNI: {r.get('dni')}\nMotivo: {r.get('motivo_llamada')}\n\nNotas:\n{r.get('notas') or ''}")
                break

class MotivoModal(BaseModal):
    """Modal para capturar detalles adicionales para un motivo de llamada específico."""
    def __init__(self, parent, ctx, motivo, on_save_callback):
        super().__init__(parent, f"Detalles para: {motivo}", ctx)
        self.on_save_callback = on_save_callback # Función a llamar al guardar.
        self.motivo = motivo
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea un formulario simple o un campo de texto según el motivo."""
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(1, weight=1)
        motivo_norm = (self.motivo or '').strip().lower()
        # Si el motivo es genérico, muestra un formulario estructurado.
        if motivo_norm in ('otros', 'motivo generico', 'motivo genérico'):
            ttk.Label(self, text="Motivo de consulta:").grid(row=1, column=0, sticky='w', padx=12, pady=(4,2))
            self.motivo_consulta_var = tk.StringVar()
            ttk.Entry(self, textvariable=self.motivo_consulta_var).grid(row=2, column=0, sticky='ew', padx=12)

            ttk.Label(self, text="Información brindada:").grid(row=3, column=0, sticky='w', padx=12, pady=(8,2))
            self.informacion_var = tk.StringVar()
            ttk.Entry(self, textvariable=self.informacion_var).grid(row=4, column=0, sticky='ew', padx=12)

            sn_val = self.ctx.get('sn_var', tk.StringVar()).get() or ''
            ttk.Label(self, text=f"SN: {sn_val}").grid(row=5, column=0, sticky='w', padx=12, pady=(8,4))

            btns = ttk.Frame(self); btns.grid(row=6, column=0, sticky='e', pady=8, padx=12)
            ttk.Button(btns, text='Guardar', command=self._save).pack(side='right')
        else:
            # Para otros motivos, muestra un campo de texto libre.
            ttk.Label(self, text="Detalles Adicionales:").grid(row=0, column=0, sticky='w', padx=12, pady=(8,4))
            self.extra_text = tk.Text(self, height=8, wrap='word'); self.extra_text.grid(row=1, column=0, sticky='nsew', padx=12, pady=4)
            btns = ttk.Frame(self); btns.grid(row=2, column=0, sticky='e', pady=8, padx=12)
            ttk.Button(btns, text='Guardar', command=self._save).pack(side='right', padx=(4,0))
            ttk.Button(btns, text='Cancelar', command=self.destroy).pack(side='right')

    def _save(self):
        """Construye el texto final, lo copia y llama al callback."""
        try:
            if hasattr(self, 'extra_text'):
                extra = self.extra_text.get(1.0, tk.END).strip()
            else:
                # Construye el texto desde el formulario de motivo genérico.
                motivo_consulta = (getattr(self, 'motivo_consulta_var', tk.StringVar()).get() or '').strip()
                informacion = (getattr(self, 'informacion_var', tk.StringVar()).get() or '').strip()
                sn_val = (self.ctx.get('sn_var', tk.StringVar()).get() or '')
                extra = f"motivo de consulta: {motivo_consulta}\ninformacion brindada : {informacion}\nsn:{sn_val}"
            
            # Copia al portapapeles.
            self.root.clipboard_clear()
            self.root.clipboard_append(extra)
            
            # Llama a la función de callback para actualizar la nota en la ventana principal.
            self.on_save_callback(extra)
        finally:
            self.destroy()

class ModalManager:
    """Gestor para abrir las diferentes ventanas modales de la aplicación."""
    def __init__(self, root, ctx):
        self.root = root
        self.ctx = ctx

    def open_retencion_modal(self):
        RetencionModal(self.root, self.ctx)

    def open_cuestionamiento_modal(self):
        CuestionamientoModal(self.root, self.ctx)

    def open_tecnica_modal(self):
        TecnicaModal(self.root, self.ctx)

    def open_credentials_modal(self):
        CredentialsModal(self.root, self.ctx)

    def open_lista_atenciones_modal(self):
        if get_clients_grouped_by_day is None: messagebox.showerror("Error", "Función de DB no encontrada."); return
        ListaAtencionesModal(self.root, self.ctx)

    def open_motivo_modal(self, motivo, callback):
        MotivoModal(self.root, self.ctx, motivo, callback)