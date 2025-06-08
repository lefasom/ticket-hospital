import tkinter as tk
from tkinter import messagebox, ttk
import datetime
import sys
import os
import traceback
import platform
import json
import threading
import time

# Importa el módulo de ID de hardware
from hardware_id import get_hardware_id # Usaremos get_hardware_id directamente
# NOTA: Las funciones verify_authorized_hardware, get_unique_hardware_id (si es diferente a get_hardware_id)
# no son necesarias si la lógica de autorización se basa completamente en Firebase.
# Si aún necesitas una lista blanca de Hardware ID locales, mantén verify_authorized_hardware.
# Para este ejemplo, asumimos que Firebase es la única fuente de verdad para la autorización.

# Importar la configuración de Firebase
from firebase_config import get_firebase_instance # Nueva forma de obtener la instancia Firebase

# --- Configuración Local de Licencia ---
LICENSE_FILE_NAME = 'license.json'
# Directorio para guardar el archivo de licencia (AppData/Local en Windows)
APP_LOCAL_DATA_DIR = os.path.join(os.getenv('LOCALAPPDATA') or os.path.expanduser("~"), "FULLMED_Impresora")
os.makedirs(APP_LOCAL_DATA_DIR, exist_ok=True)
LOCAL_LICENSE_PATH = os.path.join(APP_LOCAL_DATA_DIR, LICENSE_FILE_NAME)

# --- Redirección de Salida de Errores (para diagnóstico sin consola) ---
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs_app")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, f"app_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

original_stdout = sys.stdout
original_stderr = sys.stderr

try:
    sys.stdout = open(log_file_path, 'a', encoding='utf-8')
    sys.stderr = open(log_file_path, 'a', encoding='utf-8')
except Exception as e:
    # Si la redirección falla, al menos intentamos imprimir el error a la salida original
    original_stderr.write(f"Error al redirigir stdout/stderr: {e}\n")

# --- Clases y Funciones del Sistema de Licenciamiento ---

class ActivationWindow(tk.Toplevel):
    def __init__(self, parent, firebase_db, current_hardware_id):
        super().__init__(parent)
        self.parent = parent
        self.firebase_db = firebase_db
        self.current_hardware_id = current_hardware_id
        self.license_activated = False

        self.title("Activación de FULLMED Impresora")
        self.geometry("400x200")
        self.resizable(False, False)
        self.grab_set() # Hacer que esta ventana sea modal
        self.protocol("WM_DELETE_WINDOW", self.on_closing) # Manejar el cierre de la ventana

        # Centrar la ventana
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

        # Estilo
        style = ttk.Style(self)
        style.theme_use('clam') # O 'alt', 'default', 'classic'
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', foreground='#333333', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10, 'bold'))

        main_frame = ttk.Frame(self, padding="15 15 15 15")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="La aplicación requiere activación.", font=('Arial', 11, 'bold')).pack(pady=10)
        ttk.Label(main_frame, text="Ingrese su código de licencia:").pack(pady=5)

        self.license_entry = ttk.Entry(main_frame, width=35, justify='center')
        self.license_entry.pack(pady=5)
        self.license_entry.bind("<Return>", lambda event: self.activate_license()) # Activar con Enter

        self.activate_button = ttk.Button(main_frame, text="Activar", command=self.activate_license)
        self.activate_button.pack(pady=10)
        
        # Etiqueta para mostrar mensajes de estado
        self.status_label = ttk.Label(main_frame, text="", foreground="red")
        self.status_label.pack(pady=5)
        
        self.license_entry.focus_set() # Poner el foco en el campo de entrada

    def activate_license(self):
        license_code = self.license_entry.get().strip().upper()
        if not license_code:
            self.status_label.config(text="⚠️ Ingrese un código de licencia.")
            return

        self.status_label.config(text="⏳ Verificando licencia...")
        self.update_idletasks() # Actualizar la UI inmediatamente

        try:
            doc_ref = self.firebase_db.collection('licenses').document(license_code)
            doc = doc_ref.get()

            if not doc.exists:
                self.status_label.config(text="❌ Licencia no encontrada.")
                return

            license_data = doc.to_dict()
            status = license_data.get('status')
            stored_hardware_id = license_data.get('hardware_id')
            expires_at = license_data.get('expires_at')

            if status == 'inactive':
                self.status_label.config(text="❌ Licencia inactiva. Contacte al soporte.")
                return

            if expires_at and expires_at < datetime.datetime.now():
                self.status_label.config(text="❌ Licencia expirada. Contacte al soporte.")
                doc_ref.update({'status': 'inactive'}) # Marcar como inactiva si no lo estaba
                return
            
            # Lógica de vinculación de Hardware ID
            if stored_hardware_id and stored_hardware_id != self.current_hardware_id:
                self.status_label.config(text="❌ Ya existe otra máquina vinculada a esta licencia.")
                return
            elif not stored_hardware_id: # Primera activación de esta licencia
                # Vincula la licencia al Hardware ID de esta máquina
                doc_ref.update({
                    'hardware_id': self.current_hardware_id,
                    'activated_at': datetime.datetime.now(),
                    'status': 'active'
                })
                print(f"DEBUG: Licencia '{license_code}' vinculada y activada a HW ID: {self.current_hardware_id}")
                self.status_label.config(text="✅ Licencia activada con éxito!")
            else: # stored_hardware_id == self.current_hardware_id
                # La licencia ya está vinculada a esta máquina, simplemente se revalida
                self.status_label.config(text="✅ Licencia revalidada con éxito!")
                print(f"DEBUG: Licencia '{license_code}' revalidada para HW ID: {self.current_hardware_id}")
            
            # Guardar la licencia localmente
            self.save_local_license(license_data)
            self.license_activated = True
            self.after(500, self.destroy) # Cerrar ventana de activación después de un breve retraso

        except Exception as e:
            sys.stderr.write(f"Error durante la activación de licencia: {traceback.format_exc()}\n")
            self.status_label.config(text=f"❌ Error al conectar/activar: {e}")

    def save_local_license(self, license_data):
        try:
            # Asegúrate de que los objetos datetime se conviertan a string para JSON
            serializable_data = {k: (v.isoformat() if isinstance(v, datetime.datetime) else v) 
                                 for k, v in license_data.items()}
            with open(LOCAL_LICENSE_PATH, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=4)
            print(f"DEBUG: Licencia guardada localmente en: {LOCAL_LICENSE_PATH}")
        except Exception as e:
            sys.stderr.write(f"Error al guardar licencia local: {traceback.format_exc()}\n")
            messagebox.showwarning("Error Local", f"No se pudo guardar la licencia localmente: {e}")

    def on_closing(self):
        # Si el usuario cierra la ventana de activación, salir de la aplicación
        if not self.license_activated:
            if messagebox.askokcancel("Salir", "¿Desea salir de la aplicación sin activar?"):
                self.parent.destroy()
                sys.exit(0)
        else:
            self.destroy() # Si ya se activó, simplemente cerrar la ventana de activación

class PDCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FULLMED - Impresora")
        self.root.geometry("550x300")
        self.root.configure(bg="#db4545")
        self.root.resizable(False, False)

        # Cargar icono
        try:
            icon_path = self.get_resource_path("icon/icono.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                sys.stderr.write(f"Advertencia: Icono no encontrado en {icon_path}\n")
        except Exception as e:
            sys.stderr.write(f"Error al cargar el icono: {e}\n")

        self.hardware_id = None
        self.firebase_db = None
        self.license_data = None
        self.is_licensed = False
        self.license_code = None

        # 1. Obtener Hardware ID
        try:
            self.hardware_id = get_hardware_id()
            if not self.hardware_id:
                messagebox.showerror("Error de Hardware", "No se pudo obtener un ID de hardware único. La aplicación no puede iniciar.")
                self.root.destroy()
                sys.exit(1)
            print(f"DEBUG: Hardware ID de la máquina: {self.hardware_id}")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Ocurrió un error al obtener el Hardware ID: {e}")
            sys.stderr.write(f"Error crítico al obtener Hardware ID: {traceback.format_exc()}\n")
            self.root.destroy()
            sys.exit(1)

        # 2. Inicializar Firebase
        try:
            firebase_instance = get_firebase_instance()
            success, message = firebase_instance.initialize_with_service_account() # Para usar Admin SDK
            # success, message = firebase_instance.initialize_with_config(firebase_instance.CLIENT_FIREBASE_CONFIG) # Si usáramos web SDK (NO para este caso)
            if success:
                self.firebase_db = firebase_instance.get_firestore_client()
                print("DEBUG: Firebase Admin SDK inicializado.")
            else:
                messagebox.showerror("Error de Conexión", f"No se pudo conectar a Firebase: {message}")
                self.root.destroy()
                sys.exit(1)
        except Exception as e:
            messagebox.showerror("Error Crítico", f"Ocurrió un error al inicializar Firebase: {e}")
            sys.stderr.write(f"Error crítico al inicializar Firebase: {traceback.format_exc()}\n")
            self.root.destroy()
            sys.exit(1)

        # 3. Validar Licencia (local y online)
        self.check_and_activate_license()

        if self.is_licensed:
            self.build_ui()
            self.start_revalidation_thread()
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        else:
            # Si no se licenció, la ventana de activación ya cerró la app o se destruyó.
            pass

    def get_resource_path(self, relative_path):
        """Obtiene la ruta correcta de recursos tanto en desarrollo como en ejecutable empaquetado"""
        try:
            base_path = sys._MEIPASS
        except AttributeError: # Si no está empaquetado con PyInstaller
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def check_and_activate_license(self):
        """
        Verifica la licencia localmente y luego online.
        Si no es válida, abre la ventana de activación.
        """
        print("DEBUG: Iniciando verificación de licencia...")
        local_license = self.load_local_license()
        
        if local_license:
            print("DEBUG: Licencia local encontrada. Verificando...")
            self.license_code = local_license.get('code')
            if self.validate_license_online(self.license_code):
                self.is_licensed = True
                print("DEBUG: Licencia local validada online. Aplicación autorizada.")
                return

        print("DEBUG: No hay licencia local válida o la validación online falló. Abriendo ventana de activación.")
        # Si no hay licencia local válida o la validación online falla, muestra la ventana de activación
        activation_window = ActivationWindow(self.root, self.firebase_db, self.hardware_id)
        self.root.wait_window(activation_window) # Espera a que la ventana de activación se cierre

        self.is_licensed = activation_window.license_activated
        if self.is_licensed:
            self.license_data = self.load_local_license() # Recargar datos de la licencia activada
            self.license_code = self.license_data.get('code')
            print("DEBUG: Licencia activada a través de la ventana de activación.")
        else:
            # Si la ventana de activación se cerró sin activar la licencia, salir
            messagebox.showinfo("Activación", "Activación cancelada. Saliendo de la aplicación.")
            self.root.destroy()
            sys.exit(0)

    def load_local_license(self):
        """Carga la licencia desde el archivo local si existe."""
        if os.path.exists(LOCAL_LICENSE_PATH):
            try:
                with open(LOCAL_LICENSE_PATH, 'r', encoding='utf-8') as f:
                    license_data = json.load(f)
                
                # Convertir strings de fecha de vuelta a objetos datetime si existen
                if 'created_at' in license_data and isinstance(license_data['created_at'], str):
                    license_data['created_at'] = datetime.datetime.fromisoformat(license_data['created_at'])
                if 'activated_at' in license_data and isinstance(license_data['activated_at'], str):
                    license_data['activated_at'] = datetime.datetime.fromisoformat(license_data['activated_at'])
                if 'expires_at' in license_data and isinstance(license_data['expires_at'], str):
                    license_data['expires_at'] = datetime.datetime.fromisoformat(license_data['expires_at'])
                
                return license_data
            except Exception as e:
                sys.stderr.write(f"Error al cargar/paralizar licencia local: {traceback.format_exc()}\n")
                os.remove(LOCAL_LICENSE_PATH) # Borrar archivo corrupto
                messagebox.showwarning("Licencia Corrupta", "El archivo de licencia local está corrupto y ha sido eliminado. Necesitará activar la aplicación de nuevo.")
                return None
        return None

    def validate_license_online(self, license_code):
        """
        Valida el código de licencia con Firebase Firestore.
        Retorna True si la licencia es válida para esta máquina, False en caso contrario.
        """
        if not self.firebase_db:
            print("ERROR: Cliente de Firebase no disponible para validación online.")
            return False

        try:
            doc_ref = self.firebase_db.collection('licenses').document(license_code)
            doc = doc_ref.get()

            if not doc.exists:
                print(f"DEBUG: Licencia '{license_code}' no encontrada en Firebase.")
                return False

            license_data = doc.to_dict()
            status = license_data.get('status')
            stored_hardware_id = license_data.get('hardware_id')
            expires_at = license_data.get('expires_at')

            if status != 'active':
                print(f"DEBUG: Licencia '{license_code}' inactiva.")
                return False

            if expires_at and expires_at < datetime.datetime.now():
                print(f"DEBUG: Licencia '{license_code}' expirada.")
                # Actualizar estado en Firebase si está expirada
                doc_ref.update({'status': 'inactive'})
                return False

            if stored_hardware_id != self.hardware_id:
                print(f"DEBUG: Licencia '{license_code}' vinculada a otro HW ID ('{stored_hardware_id}') vs actual ('{self.hardware_id}').")
                return False
            
            # Si todo es correcto, actualiza la licencia localmente por si ha habido cambios en Firebase
            self.license_data = license_data
            self.save_local_license(license_data)
            print(f"DEBUG: Licencia '{license_code}' validada online y actualizada localmente.")
            return True

        except Exception as e:
            sys.stderr.write(f"Error en validación online de licencia: {traceback.format_exc()}\n")
            print(f"ERROR: Falló la validación online de licencia: {e}")
            # Si hay un error de conexión, se puede considerar como licencia no válida o intentar usar la local si es muy reciente
            messagebox.showwarning("Conexión Firebase", f"No se pudo verificar la licencia en línea. Si el problema persiste, contacte al soporte. Error: {e}")
            return False

    def start_revalidation_thread(self):
        """Inicia un hilo para revalidar la licencia periódicamente."""
        self.revalidation_interval_hours = 24 # Cada 24 horas
        self.revalidation_thread_running = True
        self.revalidation_thread = threading.Thread(target=self._revalidate_license_periodically, daemon=True)
        self.revalidation_thread.start()
        print(f"DEBUG: Hilo de revalidación de licencia iniciado (cada {self.revalidation_interval_hours} horas).")

    def _revalidate_license_periodically(self):
        while self.revalidation_thread_running:
            time.sleep(self.revalidation_interval_hours * 3600) # Convertir horas a segundos
            print("DEBUG: Iniciando revalidación periódica de licencia...")
            if self.is_licensed:
                if not self.validate_license_online(self.license_code):
                    # Si la revalidación falla, deshabilitar la aplicación y notificar
                    print("DEBUG: Revalidación periódica fallida. La licencia ya no es válida.")
                    self.is_licensed = False
                    messagebox.showerror("Licencia Inválida", "Su licencia ha sido revocada o ha expirado. La aplicación se cerrará.")
                    self.root.after(100, self.on_closing) # Cerrar la app desde el hilo principal

    def build_ui(self):
        """Construye la interfaz de usuario principal de la aplicación (campos de impresión)."""
        # Limpiar cualquier widget anterior si se reconstruye la UI (no aplica aquí normalmente)
        for widget in self.root.winfo_children():
            if widget.winfo_class() != 'Toplevel': # No destruir la ventana de activación si aún está abierta
                widget.destroy()

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
        ttk.Label(main_frame, text="Nombre Paciente:", background="#f0f0f0").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.txtNombrePaciente = ttk.Entry(main_frame, width=40)
        self.txtNombrePaciente.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        ttk.Label(main_frame, text="DNI Paciente:", background="#f0f0f0").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.txtDniPaciente = ttk.Entry(main_frame, width=40)
        self.txtDniPaciente.grid(row=1, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        ttk.Label(main_frame, text="Fecha de Nacimiento (DD/MM/AAAA):", background="#f0f0f0").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.txtNacimiento = ttk.Entry(main_frame, width=40)
        self.txtNacimiento.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

        ttk.Label(main_frame, text="Nombre del Hospital:", background="#f0f0f0").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.txtNombreHospital = ttk.Entry(main_frame, width=40)
        self.txtNombreHospital.grid(row=3, column=1, columnspan=2, sticky="ew", pady=5, padx=5)

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
        license_status_text = "Activada" if self.is_licensed else "No Licenciada"
        if self.license_data and self.license_data.get('customer_name'):
            customer_info = f" ({self.license_data['customer_name']})"
        else:
            customer_info = ""

        self.status_label = ttk.Label(self.root, 
                                      text=f"🔒 Hardware ID: {self.hardware_id[:8]}... - Licencia: {license_status_text}{customer_info}", 
                                      background="#db4545", foreground="white", anchor="w")
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)


    def imprimir_ticket(self):
        if not self.is_licensed:
            messagebox.showwarning("Acceso Denegado", "La aplicación no está licenciada o la licencia ha expirado/sido revocada.")
            return

        nombre = self.txtNombrePaciente.get()
        dni = self.txtDniPaciente.get()
        nacimiento = self.txtNacimiento.get()
        hospital = self.txtNombreHospital.get()
        dimension = self.dimensiones_combo.get()

        if not all([nombre, dni, nacimiento, hospital]):
            messagebox.showwarning("Campos Vacíos", "Por favor complete todos los campos.")
            return

        hw_info = self.get_detailed_hardware_info() # Obtener información de hardware para registro
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Ruta para guardar el archivo de registro en AppData/Local (Windows) o ~/.fullmed_impresora_data (Linux/macOS)
        # Usamos el mismo directorio de licencia para consistencia
        data_dir = APP_LOCAL_DATA_DIR 
        os.makedirs(data_dir, exist_ok=True) # Crea el directorio si no existe

        filename = os.path.join(data_dir, 'registro_impresiones.txt')

        # Incluir detalles de licencia en el log
        license_code_log = self.license_data.get('code', 'N/A') if self.license_data else 'N/A'
        customer_name_log = self.license_data.get('customer_name', 'N/A') if self.license_data else 'N/A'

        contenido = f"""[{timestamp}] - Hardware ID: {self.hardware_id}
Licencia: {license_code_log} (Cliente: {customer_name_log})
Hospital: {hospital}
=>
Paciente: {nombre}
DNI: {dni}
Nacimiento: {nacimiento}
Tipo de ticket: {dimension}
Sistema: {hw_info.get('system_info', {}).get('platform', 'N/A')} ({hw_info.get('system_info', {}).get('machine', 'N/A')})
Estado: ✓ LICENCIA Y HARDWARE VERIFICADOS Y AUTORIZADOS
{'='*70}

"""
        try:
            with open(filename, 'a', encoding='utf-8') as f:
                f.write(contenido)
            messagebox.showinfo("✓ Éxito - Sistema Autorizado", f"Datos guardados correctamente en '{filename}'.\n\n🔒 ID: {self.hardware_id[:16]}...")
            self.limpiar_campos()
        except Exception as e:
            messagebox.showerror("Error al Guardar", str(e))
            sys.stderr.write(f"Error al guardar registro de impresión: {traceback.format_exc()}\n")

    def limpiar_campos(self):
        self.txtNombrePaciente.delete(0, tk.END)
        self.txtDniPaciente.delete(0, tk.END)
        self.txtNacimiento.delete(0, tk.END)
        self.txtNombreHospital.delete(0, tk.END)
        self.dimensiones_combo.set("Ticket 80x80") # Restablecer al valor por defecto
    
    def get_detailed_hardware_info(self):
        """Retorna la información detallada del hardware (simulada o real)."""
        # Aquí puedes llamar a get_hardware_info() de hardware_id.py si lo necesitas
        # O usar un diccionario simulado para pruebas si hardware_id.py no retorna todo el detalle
        try:
            from hardware_id import get_hardware_info # Importa la función si está disponible
            return get_hardware_info()
        except ImportError:
            sys.stderr.write("Advertencia: No se pudo importar get_hardware_info de hardware_id.py. Usando info simulada.\n")
            return {
                'components': {
                    'cpu_id': 'SIM_CPU_ID',
                    'motherboard_serial': 'SIM_MB_SERIAL',
                    'disk_serial': 'SIM_DISK_SERIAL',
                    'mac_address': 'SIM_MAC_ADDRESS'
                },
                'system_info': {
                    'platform': platform.system(),
                    'processor': platform.processor(),
                    'machine': platform.machine(),
                    'node': platform.node()
                }
            }
        except Exception as e:
            sys.stderr.write(f"Error al obtener info detallada de hardware: {e}\n")
            return {}

    def mostrar_info_seguridad(self):
        """Muestra un messagebox con la información detallada de seguridad y licencia."""
        try:
            hw_info = self.get_detailed_hardware_info()
            
            license_info_text = "N/A"
            if self.license_data:
                lic_code = self.license_data.get('code', 'N/A')
                lic_customer = self.license_data.get('customer_name', 'N/A')
                lic_status = self.license_data.get('status', 'N/A')
                lic_expires = self.license_data.get('expires_at')
                lic_expires_str = lic_expires.strftime('%Y-%m-%d') if lic_expires else 'Nunca'
                license_info_text = f"""
Código de Licencia: {lic_code}
Cliente: {lic_customer}
Estado: {lic_status}
Expira: {lic_expires_str}
"""

            info_text = f"""
Hardware ID de esta Máquina: {self.hardware_id}

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

--- Información de Licencia ---
{license_info_text}

⚠️  ADVERTENCIA DE SEGURIDAD:
Esta aplicación está protegida por licencia de hardware.
Solo funcionará en la máquina autorizada con la licencia activa.
Cualquier intento de uso no autorizado será bloqueado.
"""
            messagebox.showinfo("🔒 Información de Seguridad y Licencia", info_text)
        except Exception as e:
            messagebox.showerror("Error de Seguridad", f"Error al obtener información de seguridad: {e}")
            sys.stderr.write(f"Error al mostrar info de seguridad: {traceback.format_exc()}\n")

    def on_closing(self):
        """Maneja el evento de cierre de la ventana para asegurar un cierre limpio."""
        if messagebox.askokcancel("Salir", "¿Desea salir de la aplicación?"):
            self.revalidation_thread_running = False # Detener el hilo de revalidación
            self.root.destroy()
            sys.exit(0) # Salida limpia
            
# Punto de entrada de la aplicación
if __name__ == "__main__":
    app_instance = None
    root = tk.Tk()
    
    try:
        app_instance = PDCApp(root)
        root.mainloop()

    except Exception as e:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write("\n--- ERROR NO MANEJADO (fuera del mainloop) ---\n")
            traceback.print_exc(file=f)
            f.write(f"\nError: {e}\n")

        try:
            messagebox.showerror("Error Crítico de Aplicación",
                                 f"Ha ocurrido un error inesperado. Consulte el archivo de log para más detalles: {log_file_path}\nError: {e}")
        except Exception:
            # Si el messagebox también falla, al menos imprimir en la consola original si es posible
            print(f"Error crítico: {e}\nConsulte el log: {log_file_path}", file=original_stderr)
            traceback.print_exc(file=original_stderr)

        sys.exit(1)
    finally:
        # Asegurarse de cerrar los archivos de log y restaurar las salidas originales
        if sys.stdout is not original_stdout and not sys.stdout.closed:
            sys.stdout.close()
        if sys.stderr is not original_stderr and not sys.stderr.closed:
            sys.stderr.close()
        sys.stdout = original_stdout
        sys.stderr = original_stderr