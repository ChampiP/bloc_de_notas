
# Importamos tkinter y submódulos necesarios para la interfaz gráfica
import tkinter as tk
from tkinter import ttk, messagebox

class ModalManager:
    # Clase auxiliar para gestionar ventanas modales independientes de ui.py.
    # El objetivo es centralizar la lógica de los diálogos modales y evitar dependencias directas con la interfaz principal.
    def __init__(self, root, ctx):
        # Referencia a la ventana principal
        self.root = root
        # ctx es un diccionario con referencias a variables y funciones externas necesarias
        self.ctx = ctx

        try:
            # Si no, calculamos una posición por defecto (esquina derecha)
            modal.update_idletasks()
            sw = modal.winfo_screenwidth()
            sh = modal.winfo_screenheight()
            modal.geometry(f"{w or 400}x{h or 300}+{sw-420}+80")
        except Exception:
            pass

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

        # Campo para el motivo de la consulta
        ttk.Label(modal, text="El motivo de la consulta:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=(8,2))
        motivo_consulta_var = tk.StringVar()
        motivo_consulta_entry = ttk.Entry(modal, textvariable=motivo_consulta_var)
        motivo_consulta_entry.grid(row=1, column=0, padx=8, pady=(0,6), sticky='ew')

        # Campo para la solución brindada
        ttk.Label(modal, text="La solución o información brindada:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky='w', padx=8, pady=(6,2))
        solucion_text = tk.Text(modal, height=6)
        solucion_text.grid(row=3, column=0, padx=8, pady=(0,6), sticky='nsew')

        # Campo para el número de serie (SN)
        ttk.Label(modal, text="SN:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky='w', padx=8, pady=(6,2))
        sn_local_var = tk.StringVar(value=(sn_var.get() if sn_var else ''))
        sn_local_entry = ttk.Entry(modal, textvariable=sn_local_var)
        sn_local_entry.grid(row=5, column=0, padx=8, pady=(0,6), sticky='ew')

        def guardar_otros():
            # Valida y guarda los datos ingresados en el modal 'Otros'.
            # Validación de campos obligatorios
            if not motivo_consulta_var.get().strip():
                messagebox.showwarning('Validación', 'Ingresa el motivo de la consulta')
                return
            if not solucion_text.get(1.0, tk.END).strip():
                messagebox.showwarning('Validación', 'Ingresa la solución o información brindada')
                return

            # Construimos el texto final a guardar y copiar
            final = (
                f"El motivo de la consulta: {motivo_consulta_var.get().strip()}\n"
                + f"La solucion o informacion brindada: {solucion_text.get(1.0, tk.END).strip()}\n"
                + f"SN: {sn_local_var.get().strip()}"
            )

            try:
                # Guardamos el registro usando la función externa
                try:
                    self.save_client((nombre_var.get() if nombre_var else ''), (numero_entry.get() if numero_entry else ''), sn_local_var.get(), 'Otros', dni=(dni_var.get() if dni_var else ''), notas=final)
                except Exception:
                    pass
                # Copiamos el texto a la plantilla y al portapapeles
                try:
                    if template_text:
                        template_text.delete(1.0, tk.END)
                        template_text.insert(tk.END, final)
                        root.clipboard_clear()
                        root.clipboard_append(final)
                except Exception:
                    pass
                print('Registro "Otros" guardado y plantilla copiada al portapapeles')
                modal.destroy()
            except Exception as e:
                messagebox.showerror('Error', f'No se pudo guardar: {e}')

        # Botones de acción para guardar o cancelar
        btns = ttk.Frame(modal)
        btns.grid(row=6, column=0, sticky='ew', pady=8, padx=8)
        ttk.Button(btns, text='Guardar', command=guardar_otros).pack(side='right', padx=(4,0))
        ttk.Button(btns, text='Cancelar', command=modal.destroy).pack(side='right')

    def open_tecnica_modal(self):
        # Abre una ventana modal para registrar una atención técnica.
        root = self.root
        ctx = self.ctx
        # Obtenemos referencias a variables y widgets externos
        template_text = ctx.get('template_text')
        nombre_var = ctx.get('nombre_var')
        numero_var = ctx.get('numero_var')
        sn_var = ctx.get('sn_var')
        dni_var = ctx.get('dni_var')

        # Creamos la ventana modal
        modal = tk.Toplevel(root)
        modal.title("Atención Técnica")
        modal.transient(root)
        modal.grab_set()  # Bloquea la ventana principal hasta cerrar el modal
        try:
            # Calculamos tamaño y posición del modal
            root.update_idletasks()
            main_w = root.winfo_width() or 324
            main_h = root.winfo_height() or 600
            self.position_modal(modal, int(max(324, main_w)), int(max(360, int(main_h * 0.5))), side='right')
        except Exception:
            pass
        modal.grid_columnconfigure(0, weight=1)

        # Campo para el nombre del cliente
        ttk.Label(modal, text="Nombre del cliente:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky='w', padx=8, pady=(8,2))
        nombre_tec_var = tk.StringVar(value=(nombre_var.get() if nombre_var else ''))
        ttk.Entry(modal, textvariable=nombre_tec_var).grid(row=1, column=0, sticky='ew', padx=8, pady=(0,6))

        # Campo para la línea afectada
        ttk.Label(modal, text="Línea afectada:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky='w', padx=8, pady=(6,2))
        linea_var = tk.StringVar(value=(numero_var.get() if numero_var else ''))
        ttk.Entry(modal, textvariable=linea_var).grid(row=3, column=0, sticky='ew', padx=8, pady=(0,6))

        # Campo para el tipo de inconveniente
        ttk.Label(modal, text="Inconveniente reportado:", font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky='w', padx=8, pady=(6,2))
        tec_options = [
            'Inconvenientes con Llamadas e Internet',
            'Inconvenientes con Llamadas',
            'Inconvenientes con Internet',
            'Inconvenientes con Redes Sociales / Otras Apps',
            'Inconvenientes con SMS'
        ]
        tec_var = tk.StringVar(value=tec_options[0])
        tec_combo = ttk.Combobox(modal, textvariable=tec_var, values=tec_options, state='readonly')
        tec_combo.grid(row=5, column=0, sticky='ew', padx=8, pady=(0,6))
        self.disable_mousewheel_on(tec_combo)  # Deshabilita el scroll accidental

        # Campo para detalles adicionales
        ttk.Label(modal, text="Detalle / Observaciones:", font=("Segoe UI", 10, "bold")).grid(row=6, column=0, sticky='w', padx=8, pady=(6,2))
        detalle_text = tk.Text(modal, height=6)
        detalle_text.grid(row=7, column=0, sticky='nsew', padx=8, pady=(0,6))
        modal.grid_rowconfigure(7, weight=1)

        # Campo para línea adicional
        ttk.Label(modal, text="Línea adicional:", font=("Segoe UI", 10, "bold")).grid(row=8, column=0, sticky='w', padx=8, pady=(6,2))
        linea_add_var = tk.StringVar()
        ttk.Entry(modal, textvariable=linea_add_var).grid(row=9, column=0, sticky='ew', padx=8, pady=(0,6))

        def guardar_tecnica():
            # Valida y guarda los datos ingresados en el modal de atención técnica.
            # Validación de campos obligatorios
            if not nombre_tec_var.get().strip():
                messagebox.showwarning('Validación', 'Ingresa el nombre del cliente')
                return
            if not linea_var.get().strip():
                messagebox.showwarning('Validación', 'Ingresa la línea afectada')
                return
            # Si hay detalle, lo agregamos al tipo de inconveniente
            detalle = detalle_text.get(1.0, tk.END).strip()
            incon = tec_var.get()
            if detalle:
                incon = f"{incon} - {detalle}"

            linea_add = linea_add_var.get().strip()

            # Construimos el texto final a guardar y copiar
            final = (
                f"Nombre del cliente: {nombre_tec_var.get().strip()}\n"
                + f"Línea afectada: {linea_var.get().strip()}\n"
                + f"Inconveniente reportado: {incon}\n"
                + f"*Línea adicional: {linea_add}\n"
            )
            try:
                # Guardamos el registro usando la función externa
                try:
                    self.save_client(nombre_tec_var.get(), linea_var.get(), (sn_var.get() if sn_var else ''), 'Atención Técnica', dni=(dni_var.get() if dni_var else ''), notas=final)
                except Exception:
                    pass
                # Copiamos el texto a la plantilla y al portapapeles
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

        # Botones de acción para guardar o cancelar
        btns = ttk.Frame(modal)
        btns.grid(row=10, column=0, sticky='ew', padx=8, pady=8)
        ttk.Button(btns, text='Guardar', command=guardar_tecnica).pack(side='right', padx=(4,0))
        ttk.Button(btns, text='Cancelar', command=modal.destroy).pack(side='right')