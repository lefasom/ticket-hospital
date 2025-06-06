import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import sys

from hardware_id import get_unique_hardware_id, get_hardware_info, verify_authorized_hardware


class PDCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Panel de control IMPRESORA")
        
        # Configurar el tamaño de ventana similar al diseño de Qt
        self.root.geometry("550x300")
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(False, False)

        # Verificación de hardware
        is_authorized, message = verify_authorized_hardware()
        if not is_authorized:
            messagebox.showerror("ACCESO DENEGADO", f"🚫 Aplicación no autorizada\n\nMotivo: {message}")
            root.destroy()
            sys.exit(1)

        self.hardware_id = get_unique_hardware_id()
        self.build_ui()

    def build_ui(self):
        # Frame principal con padding similar al diseño Qt
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Configurar grid weights para centrar el contenido
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)

        # Campo Hospital
        tk.Label(main_frame, text="hospital:", bg="#f0f0f0", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w", pady=(0, 15), padx=(0, 10)
        )
        self.nombre_hospital = tk.Entry(main_frame, font=("Segoe UI", 9), width=35)
        self.nombre_hospital.grid(row=0, column=1, sticky="w", pady=(0, 15))

        # Campo Dimensiones
        tk.Label(main_frame, text="dimensiones:", bg="#f0f0f0", font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="w", pady=(0, 15), padx=(0, 10)
        )
        self.dimensiones_combo = ttk.Combobox(main_frame, font=("Segoe UI", 9), width=35, values=[
            "2.25 x 1.25 (Pulsera hospitalaria)",
            "ninguna",
            "3 x 2 (mediana)",
            "4 x 6 (grande, típica de envíos)"
        ])
        self.dimensiones_combo.grid(row=1, column=1, sticky="w", pady=(0, 15))
        self.dimensiones_combo.current(0)

        # Campo Nombre
        tk.Label(main_frame, text="Nombre:", bg="#f0f0f0", font=("Segoe UI", 9)).grid(
            row=2, column=0, sticky="w", pady=(0, 15), padx=(0, 10)
        )
        self.nombre_paciente = tk.Entry(main_frame, font=("Segoe UI", 9), width=35)
        self.nombre_paciente.grid(row=2, column=1, sticky="w", pady=(0, 15))

        # Campo DNI
        tk.Label(main_frame, text="dni:", bg="#f0f0f0", font=("Segoe UI", 9)).grid(
            row=3, column=0, sticky="w", pady=(0, 15), padx=(0, 10)
        )
        self.dni_paciente = tk.Entry(main_frame, font=("Segoe UI", 9), width=35)
        self.dni_paciente.grid(row=3, column=1, sticky="w", pady=(0, 15))

        # Campo Fecha de nacimiento
        tk.Label(main_frame, text="fecha de nacimiento:", bg="#f0f0f0", font=("Segoe UI", 9)).grid(
            row=4, column=0, sticky="w", pady=(0, 25), padx=(0, 10)
        )
        self.nacimiento_paciente = tk.Entry(main_frame, font=("Segoe UI", 9), width=35)
        self.nacimiento_paciente.grid(row=4, column=1, sticky="w", pady=(0, 25))

        # Botón Imprimir - centrado
        btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        self.imprimir_btn = tk.Button(
            btn_frame, 
            text="Imprimir", 
            command=self.guardar_datos,
            font=("Segoe UI", 9),
            width=12,
            height=1,
            relief="raised",
            bd=1
        )
        self.imprimir_btn.pack()

    def guardar_datos(self):
        is_authorized, message = verify_authorized_hardware()
        if not is_authorized:
            messagebox.showerror("VIOLACIÓN DE SEGURIDAD", f"Hardware no autorizado: {message}")
            self.root.destroy()
            sys.exit(1)

        nombre = self.nombre_paciente.get()
        dni = self.dni_paciente.get()
        nacimiento = self.nacimiento_paciente.get()
        hospital = self.nombre_hospital.get()
        dimension = self.dimensiones_combo.get()

        if not all([nombre, dni, nacimiento, hospital]):
            messagebox.showwarning("Campos Vacíos", "Por favor complete todos los campos.")
            return

        hw_info = get_hardware_info()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = "registro_impresiones.txt"

        contenido = f"""[{timestamp}] - Hardware AUTORIZADO ID: {hw_info['hardware_id']}
Hospital: {hospital}
=>
Paciente: {nombre}
DNI: {dni}
Nacimiento: {nacimiento}
Tipo de ticket: {dimension}
Sistema: {hw_info['system_info'].get('platform')} ({hw_info['system_info'].get('machine')})
Estado: ✓ HARDWARE VERIFICADO Y AUTORIZADO
ID Hardware generado: {hw_info.get('generated_at')}
{'='*70}

"""
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(contenido)
            messagebox.showinfo("✓ Éxito - Sistema Autorizado", f"Datos guardados correctamente en '{filename}'.\n\n🔒 ID: {self.hardware_id[:16]}...")
            self.limpiar_campos()
        except Exception as e:
            messagebox.showerror("Error al Guardar", str(e))

    def limpiar_campos(self):
        self.nombre_paciente.delete(0, tk.END)
        self.dni_paciente.delete(0, tk.END)
        self.nacimiento_paciente.delete(0, tk.END)
        self.nombre_hospital.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = PDCApp(root)
    root.mainloop()