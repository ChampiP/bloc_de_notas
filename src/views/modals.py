# -*- coding: utf-8 -*-
"""
Módulo de ventanas modales para la aplicación.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from src.models.database import get_clients_grouped_by_day


class BaseModal(tk.Toplevel):
    """Clase base para todas las ventanas modales."""
    
    def __init__(self, parent, title, ctx):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.root = parent
        self.ctx = ctx
        self.theme = self.ctx.get('current_theme', 'modern')
        self._apply_theme()
        self._get_helpers_from_context()

    def _apply_theme(self):
        """Aplica el color de fondo según el tema."""
        bg_color = '#1e1e1e' if self.theme == 'dark' else '#f8f9fa'
        self.configure(bg=bg_color)

    def _get_helpers_from_context(self):
        """Carga funciones de ayuda desde el contexto."""
        self.position_modal = self.ctx.get('position_modal')
        self.disable_mousewheel_on = self.ctx.get('disable_mousewheel_on')
        self.save_client_func = self.ctx.get('save_client')
        self.get_credential_func = self.ctx.get('get_credential')
        self.set_credential_func = self.ctx.get('set_credential')

    def _get_vars_from_context(self, var_names):
        """Obtiene variables de Tkinter desde el contexto."""
        return {name: self.ctx.get(name) for name in var_names}

    def _set_initial_geometry(self, width=None, height=None, side='right'):
        """Posiciona la modal en la pantalla."""
        if self.position_modal:
            self.position_modal(self, width, height, side)


class RetencionModal(BaseModal):
    """Modal para gestionar un caso de retención."""
    
    def __init__(self, parent, ctx):
        super().__init__(parent, "Retención", ctx)
        self.vars = self._get_vars_from_context(['nombre_var', 'sn_var', 'dni_var', 'numero_var'])
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea los widgets del formulario."""
        self.grid_columnconfigure(0, weight=1)
        
        # Variables
        self.sn_modal_var = tk.StringVar(value=self.vars['sn_var'].get())
        self.tipo_solicitud_var = tk.StringVar(value='Cancelación')
        self.motivo_solicitud_var = tk.StringVar(value='Motivos Económicos')
        self.nombre_titular_var = tk.StringVar(value=self.vars['nombre_var'].get())
        self.dni_modal_var = tk.StringVar(value=self.vars['dni_var'].get())
        self.tel_contacto_var = tk.StringVar(value=self.vars['numero_var'].get())
        self.tel_afectado_var = tk.StringVar(value=self.vars['numero_var'].get())
        self.accion_var = tk.StringVar()
        self.motivo_otro_var = tk.StringVar()
        self.motivo_incumplimiento_var = tk.StringVar(value='BONO')

        row = 0
        
        # SN
        ttk.Label(self, text="SN:").grid(row=row, column=0, sticky='w', padx=4, pady=(4, 1))
        row += 1
        ttk.Entry(self, textvariable=self.sn_modal_var).grid(row=row, column=0, padx=4, pady=(0, 3), sticky='ew')
        row += 1
        
        # Tipo de Solicitud
        ttk.Label(self, text="Tipo de Solicitud:").grid(row=row, column=0, sticky='w', padx=4, pady=(4, 1))
        row += 1
        self.tipo_solicitud_combo = ttk.Combobox(
            self, textvariable=self.tipo_solicitud_var, state='readonly',
            values=['Cancelación', 'Migración', 'Portabilidad', 'Incumplimiento']
        )
        self.tipo_solicitud_combo.grid(row=row, column=0, padx=4, pady=(0, 3), sticky='ew')
        row += 1
        if self.disable_mousewheel_on:
            self.disable_mousewheel_on(self.tipo_solicitud_combo)
        
        # Motivo de Solicitud
        self.motivo_label = ttk.Label(self, text="Motivo de Solicitud:")
        self.motivo_label.grid(row=row, column=0, sticky='w', padx=4, pady=(4, 1))
        row += 1
        self.motivo_solicitud_combo = ttk.Combobox(
            self, textvariable=self.motivo_solicitud_var, state='readonly',
            values=['Cuestionamiento', 'Motivos Económicos', 'No usa el servicio',
                   'Inconveniente con el servicio', 'Inconforme con los beneficios', 'Otros']
        )
        self.motivo_solicitud_combo.grid(row=row, column=0, padx=4, pady=(0, 3), sticky='ew')
        row += 1
        if self.disable_mousewheel_on:
            self.disable_mousewheel_on(self.motivo_solicitud_combo)
        
        # Campos adicionales
        self.motivo_otro_entry = ttk.Entry(self, textvariable=self.motivo_otro_var)
        self.motivo_incumplimiento_combo = ttk.Combobox(
            self, textvariable=self.motivo_incumplimiento_var, state='readonly',
            values=['BONO', 'OCC', 'NC']
        )
        self.motivo_incumplimiento_label = ttk.Label(self, text="Motivo de Incumplimiento:")
        self.tel_label = ttk.Label(self, text="Teléfono de contacto:")
        self.tel_entry = ttk.Entry(self, textvariable=self.tel_contacto_var)
        self.tel_entry.grid(row=row, column=0, padx=4, pady=(0, 3), sticky='ew')
        row += 1
        
        self.accion_label = ttk.Label(self, text="Acción ofrecida:")
        self.accion_entry = ttk.Entry(self, textvariable=self.accion_var)
        self.accion_label.grid(row=row, column=0, sticky='w', padx=4, pady=(4, 1))
        row += 1
        self.accion_entry.grid(row=row, column=0, padx=4, pady=(0, 3), sticky='ew')
        row += 1
        
        # Configurar callbacks
        self.tipo_solicitud_var.trace_add('write', self._update_visibility)
        self.motivo_solicitud_var.trace_add('write', self._update_visibility)
        self._update_visibility()
        
        ttk.Button(self, text='Guardar', command=self._save).grid(row=12, column=0, pady=6)

    def _update_visibility(self, *args):
        """Ajusta la visibilidad de campos según el tipo de solicitud."""
        if self.tipo_solicitud_var.get() == 'Incumplimiento':
            self.motivo_label.grid_remove()
            self.motivo_solicitud_combo.grid_remove()
            self.motivo_otro_entry.grid_remove()
            self.motivo_incumplimiento_label.grid(row=6, column=0, sticky='w', padx=4, pady=(4, 1))
            self.motivo_incumplimiento_combo.grid(row=7, column=0, padx=4, pady=(0, 3), sticky='ew')
            self.tel_label.grid(row=8, column=0, sticky='w', padx=4, pady=(4, 1))
            self.tel_entry.grid(row=9, column=0, padx=4, pady=(0, 3), sticky='ew')
            self.accion_label.grid_remove()
            self.accion_entry.grid_remove()
        else:
            self.motivo_incumplimiento_label.grid_remove()
            self.motivo_incumplimiento_combo.grid_remove()
            self.tel_label.grid_remove()
            self.motivo_label.grid(row=6, column=0, sticky='w', padx=4, pady=(4, 1))
            self.motivo_solicitud_combo.grid(row=7, column=0, padx=4, pady=(0, 3), sticky='ew')
            
            if self.motivo_solicitud_var.get() == 'Otros':
                self.motivo_otro_entry.grid(row=8, column=0, padx=4, pady=(0, 3), sticky='ew')
            else:
                self.motivo_otro_entry.grid_remove()
            
            self.tel_entry.grid(row=9, column=0, padx=4, pady=(0, 3), sticky='ew')
            self.accion_label.grid(row=10, column=0, sticky='w', padx=4, pady=(4, 1))
            self.accion_entry.grid(row=11, column=0, padx=4, pady=(0, 3), sticky='ew')

    def _save(self):
        """Guarda la información de retención."""
        if not self.nombre_titular_var.get().strip() or not self.dni_modal_var.get().strip():
            messagebox.showwarning('Validación', 'El nombre y DNI son obligatorios', parent=self)
            return
        
        if self.tipo_solicitud_var.get() == 'Incumplimiento':
            motivo = self.motivo_incumplimiento_var.get()
            plantilla = (
                f"SN: {self.sn_modal_var.get()}\n"
                f"Tipo de Solicitud: Incumplimiento de Ofrecimiento\n"
                f"Motivo de Solicitud: {motivo}\n"
                f"Nombre del titular: {self.nombre_titular_var.get()}\n"
                f"DNI: {self.dni_modal_var.get()}\n"
                f"Teléfono de contacto: {self.tel_contacto_var.get()}\n"
                f"Teléfono afectado: {self.tel_afectado_var.get()}"
            )
        else:
            motivo = self.motivo_solicitud_var.get()
            if motivo == 'Otros':
                motivo = self.motivo_otro_var.get()
            plantilla = (
                f"SN: {self.sn_modal_var.get()}\n"
                f"Tipo de Solicitud: {self.tipo_solicitud_var.get()}\n"
                f"Motivo de Solicitud: {motivo}\n"
                f"Nombre del titular: {self.nombre_titular_var.get()}\n"
                f"DNI: {self.dni_modal_var.get()}\n"
                f"Teléfono de contacto: {self.tel_contacto_var.get()}\n"
                f"Teléfono afectado: {self.tel_afectado_var.get()}\n"
                f"Acción ofrecida: {self.accion_var.get()}"
            )
        
        template_text = self.ctx.get('template_text')
        if template_text:
            template_text.delete(1.0, tk.END)
            template_text.insert(tk.END, plantilla)
            self.root.clipboard_clear()
            self.root.clipboard_append(plantilla)
        
        self.destroy()


class CuestionamientoModal(BaseModal):
    """Modal para cuestionamiento de recibo."""
    
    SVA_SERVICES = [
        'Abaco', 'Babbel', 'Busuu', 'Challenges Arena', 'Claro Juegos',
        'CLD_GM Cloud Gaming', 'Club apps by claro', 'Club Ciencia', 'Contenta',
        'Fuze Force', 'Gameeasy', 'Gokids', 'Goles L1 Max', 'Google play',
        'Había una vez', 'Iedukar', 'Inglés Mágico', 'Jenius', 'Norton Cykadas',
        'Pfl', 'Play Kids', 'Rescatel', 'Tono de Espera', 'Zenapp', 'Zenit'
    ]

    def __init__(self, parent, ctx):
        super().__init__(parent, "Cuestionamiento de recibo", ctx)
        self.vars = self._get_vars_from_context(['nombre_var', 'sn_var', 'dni_var', 'numero_var'])
        self.selected_services = []
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea los widgets del formulario."""
        self.grid_columnconfigure(0, weight=1)
        
        self.submotivo_var = tk.StringVar(value='SVA')
        submotivo_combo = ttk.Combobox(
            self, textvariable=self.submotivo_var,
            values=['SVA', 'Otros', 'Ajuste'], state='readonly'
        )
        submotivo_combo.grid(row=1, column=0, padx=8, pady=(0, 8), sticky='ew')
        if self.disable_mousewheel_on:
            self.disable_mousewheel_on(submotivo_combo)

        self.sva_frame = self._create_sva_frame()
        self.otros_frame = self._create_otros_frame()
        
        self.submotivo_var.trace_add('write', self._refresh_visibility)
        self._refresh_visibility()
        
        ttk.Button(self, text='Guardar', command=self._save).grid(row=4, column=0, pady=8)

    def _create_sva_frame(self):
        """Crea el frame para SVA."""
        frame = ttk.Frame(self)
        frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=4)
        frame.grid_columnconfigure(0, weight=1)
        
        self.titular_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text='Titular', variable=self.titular_var).grid(row=0, column=0, sticky='w', pady=(0, 6))
        
        ttk.Label(frame, text="Servicios facturados:").grid(row=1, column=0, sticky='w')
        services_frame = ttk.Frame(frame)
        services_frame.grid(row=2, column=0, sticky='nsew', pady=(4, 6))
        
        self.service_vars = []
        for i, svc in enumerate(self.SVA_SERVICES):
            var = tk.BooleanVar(value=(svc == 'Club Ciencia'))
            self.service_vars.append((svc, var))
            ttk.Checkbutton(
                services_frame, text=svc, variable=var,
                command=self._update_services_selection
            ).grid(row=i // 3, column=i % 3, sticky='w', padx=(0, 8), pady=2)

        self.otro_var = tk.BooleanVar()
        self.otro_text_var = tk.StringVar()
        otro_row = (len(self.SVA_SERVICES) + 2) // 3
        ttk.Checkbutton(
            services_frame, text='Otro', variable=self.otro_var,
            command=self._update_services_selection
        ).grid(row=otro_row, column=0, sticky='w', pady=(6, 0))
        ttk.Entry(services_frame, textvariable=self.otro_text_var).grid(
            row=otro_row, column=1, columnspan=2, sticky='ew', padx=(6, 0), pady=(6, 0)
        )

        ttk.Label(frame, text="Información entregada:").grid(row=3, column=0, sticky='w')
        self.info_text = tk.Text(frame, height=4)
        self.info_text.grid(row=4, column=0, sticky='nsew', pady=(4, 6))
        
        ttk.Label(frame, text="SN:").grid(row=5, column=0, sticky='w')
        self.sn_modal_var = tk.StringVar(value=self.vars['sn_var'].get())
        ttk.Entry(frame, textvariable=self.sn_modal_var).grid(row=6, column=0, sticky='ew', pady=(4, 6))
        
        self._update_services_selection()
        return frame

    def _create_otros_frame(self):
        """Crea el frame para otros submotivos."""
        frame = ttk.Frame(self)
        frame.grid(row=2, column=0, sticky='nsew', padx=8, pady=4)
        frame.grid_remove()
        
        ttk.Label(frame, text="Acción tomada / Observaciones:").grid(row=0, column=0, sticky='w')
        self.otros_text = tk.Text(frame, height=6)
        self.otros_text.grid(row=1, column=0, sticky='nsew')
        
        return frame

    def _update_services_selection(self):
        """Actualiza la lista de servicios seleccionados."""
        self.selected_services = [name for name, var in self.service_vars if var.get()]
        if self.otro_var.get() and self.otro_text_var.get().strip():
            self.selected_services.append(self.otro_text_var.get().strip())

    def _refresh_visibility(self, *args):
        """Muestra u oculta frames según el submotivo."""
        if self.submotivo_var.get() == 'SVA':
            self.sva_frame.grid()
            self.otros_frame.grid_remove()
        else:
            self.sva_frame.grid_remove()
            self.otros_frame.grid()
        self.update_idletasks()
        self._set_initial_geometry(width=324)

    def _save(self):
        """Guarda la información de cuestionamiento."""
        if self.submotivo_var.get() == 'SVA':
            if not self.sn_modal_var.get().strip():
                messagebox.showwarning('Validación', 'La SN es requerida', parent=self)
                return
            
            cuantos = 'Uno' if len(self.selected_services) == 1 else 'Varios'
            detalle = self.selected_services[0] if cuantos == 'Uno' else ', '.join(self.selected_services)
            
            final = (
                f"1: Quien se comunica: {'Titular' if self.titular_var.get() else 'Usuario'}\n"
                f"2: Servicios facturados: {cuantos} - {detalle}\n"
                f"3: Información entregada: {self.info_text.get(1.0, tk.END).strip()}\n"
                f"4: SN: {self.sn_modal_var.get().strip()}"
            )
        else:
            final = self.otros_text.get(1.0, tk.END).strip()
            if not final:
                messagebox.showwarning('Validación', 'Ingresa la observación', parent=self)
                return
        
        template_text = self.ctx.get('template_text')
        if template_text:
            template_text.delete(1.0, tk.END)
            template_text.insert(tk.END, final)
            self.root.clipboard_clear()
            self.root.clipboard_append(final)
        
        self.destroy()


class TecnicaModal(BaseModal):
    """Modal para atención técnica."""
    
    INCONVENIENTES = [
        'Inconvenientes con Llamadas e Internet',
        'Inconvenientes con Llamadas',
        'Inconvenientes con Internet',
        'Inconvenientes con Redes Sociales / Otras Apps',
        'Inconvenientes con SMS'
    ]

    def __init__(self, parent, ctx):
        super().__init__(parent, "Atención Técnica", ctx)
        self.vars = self._get_vars_from_context(['nombre_var', 'numero_var', 'sn_var', 'dni_var'])
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea los widgets del formulario."""
        self.grid_columnconfigure(0, weight=1)
        
        self.nombre_tec_var = tk.StringVar(value=self.vars['nombre_var'].get())
        self.linea_var = tk.StringVar(value=self.vars['numero_var'].get())
        self.linea_add_var = tk.StringVar()
        self.tec_var = tk.StringVar(value=self.INCONVENIENTES[0])

        fields = [
            ("Nombre del cliente:", self.nombre_tec_var, ttk.Entry, {}),
            ("Línea afectada:", self.linea_var, ttk.Entry, {}),
            ("Inconveniente reportado:", self.tec_var, ttk.Combobox,
             {'state': 'readonly', 'values': self.INCONVENIENTES}),
            ("Línea adicional:", self.linea_add_var, ttk.Entry, {}),
        ]
        
        row = 0
        for label, var, widget_class, opts in fields:
            ttk.Label(self, text=label, font=("Segoe UI", 10, "bold")).grid(
                row=row, column=0, sticky='w', padx=8, pady=(8, 2)
            )
            row += 1
            w = widget_class(self, textvariable=var, **opts)
            w.grid(row=row, column=0, padx=8, pady=(0, 6), sticky='ew')
            row += 1
            if widget_class == ttk.Combobox and self.disable_mousewheel_on:
                self.disable_mousewheel_on(w)
        
        ttk.Button(self, text='Guardar', command=self._save).grid(row=row, column=0, pady=8)

    def _save(self):
        """Guarda la información técnica."""
        if not self.nombre_tec_var.get().strip() or not self.linea_var.get().strip():
            messagebox.showwarning('Validación', 'Nombre y línea son obligatorios', parent=self)
            return
        
        linea_add = self.linea_add_var.get().strip()
        final = (
            f"Nombre del cliente: {self.nombre_tec_var.get().strip()}\n"
            f"Línea afectada: {self.linea_var.get().strip()}\n"
            f"Inconveniente reportado: {self.tec_var.get()}"
        )
        if linea_add:
            final += f"\n*Línea adicional: {linea_add}"
        
        template_text = self.ctx.get('template_text')
        if template_text:
            template_text.delete(1.0, tk.END)
            template_text.insert(tk.END, final)
            self.root.clipboard_clear()
            self.root.clipboard_append(final)
        
        self.destroy()


class CredentialsModal(BaseModal):
    """Modal para editar credenciales."""
    
    def __init__(self, parent, ctx):
        super().__init__(parent, "Editar credenciales", ctx)
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea los widgets del formulario."""
        self.grid_columnconfigure(0, weight=1)
        
        self.vpn_var = tk.StringVar(value=(self.get_credential_func('vpn_password') or ''))
        self.siac_var = tk.StringVar(value=(self.get_credential_func('siac_password') or ''))
        
        ttk.Label(self, text="Contraseña VPN:").grid(row=0, column=0, sticky='w', padx=8, pady=(8, 2))
        ttk.Entry(self, textvariable=self.vpn_var, show='*').grid(row=1, column=0, padx=8, pady=(0, 8), sticky='ew')
        
        ttk.Label(self, text="Contraseña SIAC:").grid(row=2, column=0, sticky='w', padx=8, pady=(6, 2))
        ttk.Entry(self, textvariable=self.siac_var, show='*').grid(row=3, column=0, padx=8, pady=(0, 8), sticky='ew')
        
        ttk.Button(self, text='Guardar', command=self._save).grid(row=4, column=0, pady=8)

    def _save(self):
        """Guarda las credenciales."""
        try:
            self.set_credential_func('vpn_password', self.vpn_var.get())
            self.set_credential_func('siac_password', self.siac_var.get())
            self.destroy()
        except Exception as e:
            messagebox.showerror('Error', f'No se pudieron guardar: {e}', parent=self)


class ListaAtencionesModal(BaseModal):
    """Modal para lista de atenciones."""
    
    def __init__(self, parent, ctx):
        super().__init__(parent, "Lista de Atenciones", ctx)
        self._create_widgets()
        self._set_initial_geometry(width=800, height=600)

    def _create_widgets(self):
        """Crea los widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky='nsew', padx=8, pady=8)
        container.grid_columnconfigure(0, weight=3)
        container.grid_columnconfigure(1, weight=2)
        container.grid_rowconfigure(0, weight=1)
        
        # Treeview
        cols = ('fecha', 'nombre', 'numero', 'motivo')
        self.tree = ttk.Treeview(container, columns=cols, show='headings', selectmode='browse')
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=150, anchor='w')
        self.tree.grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        
        # Detalle
        detail_frame = ttk.Frame(container)
        detail_frame.grid(row=0, column=1, sticky='nsew')
        ttk.Label(detail_frame, text='Detalle').pack(anchor='w')
        self.detail_text = tk.Text(detail_frame, wrap='word')
        self.detail_text.pack(fill='both', expand=True, pady=(6, 0))
        
        self._load_data()
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        
        ttk.Button(self, text='Cerrar', command=self.destroy).grid(row=1, column=0, sticky='e', padx=8, pady=8)

    def _load_data(self):
        """Carga los datos desde la base de datos."""
        try:
            self.rows = get_clients_grouped_by_day(1000)
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo cargar: {e}')
            self.rows = []
        
        for r in self.rows:
            self.tree.insert('', 'end', iid=str(r.get('id')), values=(
                str(r.get('fecha_llamada', '')),
                r.get('nombre'),
                r.get('numero'),
                r.get('motivo_llamada')
            ))

    def _on_select(self, event=None):
        """Muestra el detalle de la selección."""
        sel = self.tree.selection()
        if not sel:
            return
        
        for r in self.rows:
            if str(r.get('id')) == sel[0]:
                self.detail_text.delete(1.0, tk.END)
                self.detail_text.insert(tk.END, (
                    f"ID: {r.get('id')}\n"
                    f"Nombre: {r.get('nombre')}\n"
                    f"Número: {r.get('numero')}\n"
                    f"SN: {r.get('sn')}\n"
                    f"DNI: {r.get('dni')}\n"
                    f"Motivo: {r.get('motivo_llamada')}\n\n"
                    f"Notas:\n{r.get('notas') or ''}"
                ))
                break


class MotivoModal(BaseModal):
    """Modal para detalles adicionales de un motivo."""
    
    def __init__(self, parent, ctx, motivo, on_save_callback):
        super().__init__(parent, f"Detalles: {motivo}", ctx)
        self.on_save_callback = on_save_callback
        self.motivo = motivo
        self._create_widgets()
        self._set_initial_geometry(width=324)

    def _create_widgets(self):
        """Crea los widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        motivo_norm = (self.motivo or '').strip().lower()
        
        if motivo_norm == 'otros':
            ttk.Label(self, text="Motivo de consulta:").grid(row=1, column=0, sticky='w', padx=12, pady=(4, 2))
            self.motivo_consulta_var = tk.StringVar()
            ttk.Entry(self, textvariable=self.motivo_consulta_var).grid(row=2, column=0, sticky='ew', padx=12)

            ttk.Label(self, text="Información brindada:").grid(row=3, column=0, sticky='w', padx=12, pady=(8, 2))
            self.informacion_var = tk.StringVar()
            ttk.Entry(self, textvariable=self.informacion_var).grid(row=4, column=0, sticky='ew', padx=12)

            sn_val = self.ctx.get('sn_var', tk.StringVar()).get() or ''
            ttk.Label(self, text=f"SN: {sn_val}").grid(row=5, column=0, sticky='w', padx=12, pady=(8, 4))

            btns = ttk.Frame(self)
            btns.grid(row=6, column=0, sticky='e', pady=8, padx=12)
            ttk.Button(btns, text='Guardar', command=self._save).pack(side='right')
        else:
            ttk.Label(self, text="Detalles Adicionales:").grid(row=0, column=0, sticky='w', padx=12, pady=(8, 4))
            self.extra_text = tk.Text(self, height=8, wrap='word')
            self.extra_text.grid(row=1, column=0, sticky='nsew', padx=12, pady=4)
            
            btns = ttk.Frame(self)
            btns.grid(row=2, column=0, sticky='e', pady=8, padx=12)
            ttk.Button(btns, text='Guardar', command=self._save).pack(side='right', padx=(4, 0))
            ttk.Button(btns, text='Cancelar', command=self.destroy).pack(side='right')

    def _save(self):
        """Guarda y ejecuta el callback."""
        try:
            if hasattr(self, 'extra_text'):
                extra = self.extra_text.get(1.0, tk.END).strip()
            else:
                motivo_consulta = self.motivo_consulta_var.get().strip()
                informacion = self.informacion_var.get().strip()
                sn_val = self.ctx.get('sn_var', tk.StringVar()).get() or ''
                extra = f"Motivo: {motivo_consulta}\nInformación: {informacion}\nSN: {sn_val}"
            
            self.root.clipboard_clear()
            self.root.clipboard_append(extra)
            self.on_save_callback(extra)
        finally:
            self.destroy()


class ModalManager:
    """Gestor de ventanas modales."""
    
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
        ListaAtencionesModal(self.root, self.ctx)

    def open_motivo_modal(self, motivo, callback):
        MotivoModal(self.root, self.ctx, motivo, callback)
