# createHID.py
import tkinter as tk
from tkinter import messagebox, ttk
import os
import sys
import datetime # Importamos datetime aquí
import traceback

# Importar el generador de Hardware ID de nuestro módulo
# CORRECCIÓN: Importamos la clase HardwareID, no HardwareIDGenerator
from hardware_id import HardwareID 

# --- Redirección de Salida de Errores (para diagnóstico sin consola) ---
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs_createhid")
os.makedirs(log_dir, exist_ok=True)
# CORRECCIÓN: Usar datetime.datetime.now()
log_file_path = os.path.join(log_dir, f"createhid_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

original_stdout = sys.stdout
original_stderr = sys.stderr

sys.stdout = open(log_file_path, 'a', encoding='utf-8')
sys.stderr = open(log_file_path, 'a', encoding='utf-8')
# --- Fin de Redirección de Salida de Errores ---


class CreateHIDApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Obtener Hardware ID FULLMED")
        self.root.geometry("500x200")
        self.root.resizable(False, False)
        self.root.configure(bg="#db4545")

        try:
            icon_path = self.get_resource_path("icon/icono.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            sys.stderr.write(f"Advertencia: No se pudo cargar el icono: {e}\n")

        self.hw_id_generator = HardwareID() # CORRECCIÓN: Instanciar HardwareID
        self.current_hardware_id_var = tk.StringVar(value="Generando ID...") # Usar StringVar para actualizar la UI
        self.generate_id_and_build_ui()

    def get_resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def generate_id_and_build_ui(self):
        try:
            generated_id = self.hw_id_generator.get_hardware_id() # Usar el método de la instancia
            self.current_hardware_id_var.set(generated_id)
        except Exception as e:
            error_msg = f"ERROR: {e}"
            self.current_hardware_id_var.set(error_msg)
            sys.stderr.write(f"Error al generar Hardware ID: {traceback.format_exc()}\n")
            messagebox.showerror("Error", f"No se pudo generar el Hardware ID.\nPor favor, contacte a soporte.\nError: {e}")

        self.build_ui()

    def build_ui(self):
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Su Hardware ID Único para FULLMED:",
                  font=("Arial", 12, "bold"), background="#f0f0f0").pack(pady=10)

        self.hw_id_entry = ttk.Entry(main_frame, width=60, justify='center',
                                     textvariable=self.current_hardware_id_var,
                                     state='readonly')
        self.hw_id_entry.pack(pady=10)

        btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Copiar al Portapapeles", command=self.copy_to_clipboard).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Salir", command=self.on_closing).pack(side="left", padx=5)

        ttk.Label(main_frame, text="Por favor, copie este ID y envíelo a su proveedor de software.",
                  background="#f0f0f0", font=("Arial", 9)).pack(pady=5)


    def copy_to_clipboard(self):
        try:
            id_to_copy = self.current_hardware_id_var.get()
            if id_to_copy.startswith("ERROR:") or id_to_copy == "Generando ID..." or not id_to_copy:
                 messagebox.showwarning("Advertencia", "No hay un Hardware ID válido para copiar.")
                 return

            self.root.clipboard_clear()
            self.root.clipboard_append(id_to_copy)
            messagebox.showinfo("Copiado", "Hardware ID copiado al portapapeles.")
        except Exception as e:
            sys.stderr.write(f"Error al copiar al portapapeles: {traceback.format_exc()}\n")
            messagebox.showerror("Error al Copiar", f"No se pudo copiar el ID: {e}")

    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Desea salir de la utilidad?"):
            self.root.destroy()
            sys.exit(0)

# Punto de entrada de la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = CreateHIDApp(root)
    root.mainloop()

    # Asegurarse de cerrar los archivos de log y restaurar las salidas originales
    if sys.stdout is not original_stdout:
        sys.stdout.close()
    if sys.stderr is not original_stderr:
        sys.stderr.close()
    sys.stdout = original_stdout
    sys.stderr = original_stderr