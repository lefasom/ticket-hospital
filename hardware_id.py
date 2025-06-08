# hardware_id.py
import hashlib
import platform
import subprocess
import uuid
import os
import json
import sys
from datetime import datetime

# Archivo de configuración de ID autorizado
# Este archivo DEBE ser el mismo que el que se añade con --add-data en PyInstaller
AUTHORIZED_HARDWARE_FILE = 'authorized_hardware.json' 

def get_resource_path(relative_path):
    """Obtiene la ruta correcta de recursos tanto en desarrollo como en ejecutable empaquetado"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class HardwareID:
    def __init__(self):
        # super().__init__() # Tkinter no necesita esto aquí, ya que no hereda de un widget.
        self.hardware_id = None
        self.authorized_id = None
        self._load_authorized_id() # Cargar el ID autorizado al inicializar

    def get_cpu_id(self):
        """Obtiene información del procesador"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'cpu', 'get', 'ProcessorId'], 
                                      capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=10)
                cpu_id = result.stdout.split('\n')[1].strip()
                return cpu_id if cpu_id else "UNKNOWN_CPU"
            else:
                # Para Linux/Mac
                result = subprocess.run(['cat', '/proc/cpuinfo'], 
                                      capture_output=True, text=True, check=True, timeout=5)
                for line in result.stdout.split('\n'):
                    if 'Serial' in line:
                        return line.split(':')[1].strip()
                return str(uuid.getnode()) # Fallback para Linux/Mac
        except Exception:
            return str(uuid.getnode()) # Fallback general
    
    def get_motherboard_serial(self):
        """Obtiene el serial de la placa madre"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'baseboard', 'get', 'SerialNumber'], 
                                      capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=10)
                serial = result.stdout.split('\n')[1].strip()
                return serial if serial else "UNKNOWN_MB"
            else:
                # Para Linux/Mac, si no hay 'dmidecode', esto puede fallar
                result = subprocess.run(['sudo', 'dmidecode', '-s', 'baseboard-serial-number'], 
                                        capture_output=True, text=True, check=False, timeout=5) # check=False si 'sudo' puede requerir contraseña
                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    return str(uuid.getnode()) # Fallback
        except Exception:
            return str(uuid.getnode()) # Fallback general

    def get_disk_serial(self):
        """Obtiene el serial del disco principal (ej. C: en Windows)"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'diskdrive', 'get', 'SerialNumber'], 
                                      capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=10)
                # wmic puede devolver múltiples discos, tomamos el primero no vacío
                for line in result.stdout.split('\n')[1:]:
                    serial = line.strip()
                    if serial:
                        return serial
                return "UNKNOWN_DISK"
            else:
                # Para Linux/Mac, obtener serial del disco principal (ej. sda)
                result = subprocess.run(['sudo', 'hdparm', '-I', '/dev/sda'], 
                                        capture_output=True, text=True, check=False, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'Serial Number' in line:
                            return line.split(':')[1].strip()
                return str(uuid.uuid1()) # Fallback
        except Exception:
            return str(uuid.uuid1()) # Fallback general

    def get_mac_address(self):
        """Obtiene la dirección MAC de la primera interfaz de red activa."""
        try:
            mac_int = uuid.getnode()
            mac_hex = ':'.join(("%012X" % mac_int)[i:i+2] for i in range(0, 12, 2))
            return mac_hex
        except Exception:
            return "UNKNOWN_MAC"
            
    def get_system_info(self):
        """Obtiene información general del sistema."""
        return {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "node": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version()
        }

    def get_hardware_info(self):
        """Compila toda la información de hardware en un diccionario."""
        return {
            "components": {
                "cpu_id": self.get_cpu_id(),
                "motherboard_serial": self.get_motherboard_serial(),
                "disk_serial": self.get_disk_serial(),
                "mac_address": self.get_mac_address()
            },
            "system_info": self.get_system_info()
        }

    def get_hardware_id(self):
        """Genera un ID único basado en el hardware."""
        if self.hardware_id:
            return self.hardware_id

        hw_info = self.get_hardware_info()
        
        unique_string = (
            f"{hw_info['components']['cpu_id']}-"
            f"{hw_info['components']['motherboard_serial']}-"
            f"{hw_info['components']['disk_serial']}-"
            f"{hw_info['components']['mac_address']}"
        )
        
        self.hardware_id = hashlib.sha256(unique_string.encode('utf-8')).hexdigest()
        return self.hardware_id

    def _load_authorized_id(self):
        """Carga el ID de hardware autorizado desde el archivo JSON."""
        # Usa la función get_resource_path para manejar la ruta en PyInstaller
        file_path = get_resource_path(AUTHORIZED_HARDWARE_FILE)
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.authorized_id = json.load(f).get("authorized_id")
        except FileNotFoundError:
            self.authorized_id = None
        except json.JSONDecodeError:
            self.authorized_id = None
        except Exception:
            self.authorized_id = None


    def verify_hardware_authorization(self):
        """Verifica si el ID de hardware actual coincide con el ID autorizado."""
        current_hw_id = self.get_hardware_id()
        if self.authorized_id and current_hw_id == self.authorized_id:
            return True, "Hardware autorizado."
        elif not self.authorized_id:
            return False, "Hardware no autorizado. Archivo de autorización no encontrado o vacío."
        else:
            return False, f"Hardware no autorizado. ID actual: {current_hw_id[:8]}..."

# Funciones de utilidad para el uso externo del módulo
def get_unique_hardware_id():
    """Función de acceso externo para obtener el ID de hardware."""
    hw_id = HardwareID()
    return hw_id.get_hardware_id()

def get_hardware_info():
    """Función para obtener información completa verificada."""
    hw_id = HardwareID()
    return hw_id.get_hardware_info()

def verify_authorized_hardware():
    """Verifica explícitamente si el hardware está autorizado."""
    hw_id = HardwareID()
    return hw_id.verify_hardware_authorization()

def capture_authorized_hardware():
    """
    Captura el ID de hardware actual y lo guarda como autorizado.
    Esto debe hacerse en la máquina donde se compilará/usará la aplicación.
    """
    hw_id_obj = HardwareID()
    current_hw_id = hw_id_obj.get_hardware_id()
    
    # Asegúrate de que el archivo se guarde en el directorio actual para la compilación
    # Usa os.path.dirname(os.path.abspath(__file__)) para obtener la ruta del script
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), AUTHORIZED_HARDWARE_FILE)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({"authorized_id": current_hw_id}, f, indent=4)
        return True
    except Exception:
        return False

# Para testing y compilación
if __name__ == "__main__":
    # Esta sección no contiene 'print()' para evitar parpadeos en el ejecutable.
    
    # Si estamos en modo de captura (desarrollo)
    if len(sys.argv) > 1 and sys.argv[1] == "--capture":
        if capture_authorized_hardware():
            sys.exit(0) # Salir con éxito
        else:
            sys.exit(1) # Salir con error
    else:
        # Modo verificación normal
        try:
            is_authorized, message = verify_authorized_hardware()
            if is_authorized:
                sys.exit(0) # Salir con éxito
            else:
                sys.exit(1) # Salir con error
        except Exception:
            sys.exit(1) # Salir con error