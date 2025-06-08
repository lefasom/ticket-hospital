import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import sys
import os
import traceback
import platform

# Importa el módulo de ID de hardware con protección
from hardware_id import get_unique_hardware_id, get_hardware_info, verify_authorized_hardware

# --- Inicio de la Redirección de Salida de Errores (para diagnóstico sin consola) ---
# Se recomienda eliminar esta sección una vez que la aplicación sea estable.
# Directorio para los logs (junto al ejecutable)
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f"error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

# Guardamos las salidas originales para restaurarlas después
original_stdout = sys.stdout
original_stderr = sys.stderr

# Redirigir stdout y stderr a un archivo
sys.stdout = open(log_file_path, 'a', encoding='utf-8')
sys.stderr = open(log_file_path, 'a', encoding='utf-8')
# --- Fin de la Redirección de Salida de Errores ---


class PDCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FULLMED")
        
        # Intentar cargar el icono. Si falla, la aplicación continuará sin icono.
        # Asegúrate de que 'icono.ico' esté en la misma carpeta que el ejecutable
        # o que PyInstaller lo haya incluido correctamente.
        try:
            icon_path = self.get_resource_path("icon/icono.ico") # Asume que el icono está en una subcarpeta 'icon'
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # Si el icono no se encuentra, puedes loggear esto pero no detener la app
                sys.stderr.write(f"Advertencia: Icono no encontrado en {icon_path}\n")
        except Exception as e:
            sys.stderr.write(f"Error al cargar el icono: {e}\n")


        self.root.geometry("550x300")
        self.root.configure(bg="#db4545")
        self.root.resizable(False, False)

        # Verificación de hardware CRÍTICA y TEMPRANA
        try:
            is_authorized, message = verify_authorized_hardware()
            if not is_authorized:
                messagebox.showerror("ACCESO DENEGADO", f"🚫 Aplicación no autorizada\n\nMotivo: {message}")
                self.root.destroy() # Cierra la ventana de Tkinter
                sys.exit(1) # Cierra el proceso Python
            
            # Si la verificación es exitosa, obtenemos el ID
            self.hardware_id = get_unique_hardware_id()

        except Exception as e:
            # Captura errores durante la verificación de hardware
            messagebox.showerror("ERROR CRÍTICO", f"Ocurrió un error inesperado al verificar el hardware: {e}")
            sys.stderr.write(f"Error crítico en verificación de hardware: {traceback.format_exc()}\n")
            self.root.destroy()
            sys.exit(1)
            

        # Si llegamos aquí, el hardware está autorizado y la aplicación puede continuar
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing) # Asegura el cierre limpio

    def get_resource_path(self, relative_path):
        """Obtiene la ruta correcta de recursos tanto en desarrollo como en ejecutable empaquetado"""
        try:
            # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)

    def build_ui(self):
        # Frame principal con padding similar al diseño Qt
        main_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Configurar grid weights para centrar el contenido
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_columnconfigure(2, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_rowconfigure(5, weight=1)

        # LABELS Y ENTRY PARA EL FORMULARIO
        # Label y Entry para Nombre del Paciente
        ttk.Label(main_frame, text="Nombre Paciente:", background="#f0f0f0").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.txtNombrePaciente = ttk.Entry(main_frame, width=40)
        self.txtNombrePaciente.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        # Label y Entry para DNI del Paciente
        ttk.Label(main_frame, text="DNI Paciente:", background="#f0f0f0").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.txtDniPaciente = ttk.Entry(main_frame, width=40)
        self.txtDniPaciente.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        # Label y Entry para Fecha de Nacimiento
        ttk.Label(main_frame, text="Fecha de Nacimiento (DD/MM/AAAA):", background="#f0f0f0").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.txtNacimiento = ttk.Entry(main_frame, width=40)
        self.txtNacimiento.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        # Label y Entry para Nombre del Hospital
        ttk.Label(main_frame, text="Nombre del Hospital:", background="#f0f0f0").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.txtNombreHospital = ttk.Entry(main_frame, width=40)
        self.txtNombreHospital.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        # Label y ComboBox para Dimensiones de Impresión
        ttk.Label(main_frame, text="Dimensiones de Impresión:", background="#f0f0f0").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.dimensiones_combo = ttk.Combobox(main_frame, values=["Ticket 50x50", "Ticket 80x80", "Ticket 100x100"], state="readonly", width=38)
        self.dimensiones_combo.grid(row=4, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        self.dimensiones_combo.set("Ticket 80x80") # Valor por defecto

        # BOTONES
        btn_frame = tk.Frame(main_frame, bg="#f0f0f0")
        btn_frame.grid(row=5, column=0, columnspan=3, pady=10)

        self.btnImprimir = ttk.Button(btn_frame, text="Imprimir Ticket", command=self.imprimir_ticket)
        self.btnImprimir.pack(side="left", padx=5)

        self.btnInfoSeguridad = ttk.Button(btn_frame, text="Info Seguridad", command=self.mostrar_info_seguridad)
        self.btnInfoSeguridad.pack(side="left", padx=5)

        # Etiqueta de estado en la parte inferior
        self.status_label = ttk.Label(self.root, text=f"🔒 Hardware ID: {self.hardware_id[:8]}... - Autorizado", background="#db4545", foreground="white", anchor="w")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)


    def imprimir_ticket(self):
        nombre = self.txtNombrePaciente.get()
        dni = self.txtDniPaciente.get()
        nacimiento = self.txtNacimiento.get()
        hospital = self.txtNombreHospital.get()
        dimension = self.dimensiones_combo.get()

        if not all([nombre, dni, nacimiento, hospital]):
            messagebox.showwarning("Campos Vacíos", "Por favor complete todos los campos.")
            return

        # Aquí obtendrás la información de hardware actual para el registro
        hw_info = get_hardware_info() 
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ruta para guardar el archivo de registro en AppData/Local (Windows) o ~/.pdc_impresora_data (Linux/macOS)
        if platform.system() == "Windows":
            data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'PDC Impresora')
        else:
            data_dir = os.path.join(os.path.expanduser('~'), '.pdc_impresora_data')

        os.makedirs(data_dir, exist_ok=True) # Crea el directorio si no existe

        filename = os.path.join(data_dir, 'registro_impresiones.txt')

        contenido = f"""[{timestamp}] - Hardware AUTORIZADO ID: {self.hardware_id}
Hospital: {hospital}
=>
Paciente: {nombre}
DNI: {dni}
Nacimiento: {nacimiento}
Tipo de ticket: {dimension}
Sistema: {hw_info['system_info'].get('platform', 'N/A')} ({hw_info['system_info'].get('machine', 'N/A')})
Estado: ✓ HARDWARE VERIFICADO Y AUTORIZADO
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
        self.txtNombrePaciente.delete(0, tk.END)
        self.txtDniPaciente.delete(0, tk.END)
        self.txtNacimiento.delete(0, tk.END)
        self.txtNombreHospital.delete(0, tk.END)
        self.dimensiones_combo.set("Ticket 80x80") # Restablecer al valor por defecto
    
    def mostrar_info_seguridad(self):
        """Muestra un messagebox con la información detallada de seguridad."""
        try:
            hw_info = get_hardware_info()
            info_text = f"""
Hardware ID Autorizado: {self.hardware_id}

Componentes Registrados:
CPU: {hw_info['components'].get('cpu_id', 'N/A')}
Placa Madre: {hw_info['components'].get('motherboard_serial', 'N/A')}
Disco: {hw_info['components'].get('disk_serial', 'N/A')}
MAC: {hw_info['components'].get('mac_address', 'N/A')}

Información del Sistema:
Plataforma: {hw_info['system_info'].get('platform', 'N/A')}
Procesador: {hw_info['system_info'].get('processor', 'N/A')}
Máquina: {hw_info['system_info'].get('machine', 'N/A')}
Nodo: {hw_info['system_info'].get('node', 'N/A')}

⚠️  ADVERTENCIA DE SEGURIDAD:
Esta aplicación SOLO funciona en la computadora donde fue compilada.
Cualquier intento de uso en otra máquina será bloqueado.
"""
            messagebox.showinfo("🔒 Información de Seguridad", info_text)
        except Exception as e:
            messagebox.showerror("Error de Seguridad", f"Error al obtener información de seguridad: {e}")
            sys.stderr.write(f"Error al mostrar info de seguridad: {traceback.format_exc()}\n")

    def on_closing(self):
        """Maneja el evento de cierre de la ventana para asegurar un cierre limpio."""
        if messagebox.askokcancel("Salir", "¿Desea salir de la aplicación?"):
            self.root.destroy()
            sys.exit(0) # Salida limpia
            
# Punto de entrada de la aplicación
if __name__ == "__main__":
    app_instance = None # Inicializa app_instance fuera del try
    root = tk.Tk()
    
    try:
        app_instance = PDCApp(root)
        root.mainloop()

    except Exception as e:
        # Esto capturará errores que ocurran ANTES o DURANTE el mainloop
        # o que no sean manejados por los try/except internos.
        # Restaurar salidas antes de imprimir el error al log y potencialmente a la consola original.
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        # Imprimir el traceback completo al log para depuración
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write("\n--- ERROR NO MANEJADO (fuera del mainloop) ---\n")
            traceback.print_exc(file=f)
            f.write(f"\nError: {e}\n")

        # Intentar mostrar un mensaje de error al usuario si la GUI aún es funcional
        try:
            messagebox.showerror("Error Crítico de Aplicación", 
                                 f"Ha ocurrido un error inesperado. Consulte el archivo de log para más detalles: {log_file_path}\nError: {e}")
        except Exception:
            pass # Si el messagebox falla, no podemos mostrar un mensaje al usuario.

        sys.exit(1) # Salir con un código de error
    finally:
        # Asegurarse de cerrar los archivos de log y restaurar las salidas originales
        if sys.stdout is not original_stdout:
            sys.stdout.close()
        if sys.stderr is not original_stderr:
            sys.stderr.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr