# hardware_id.py
import hashlib
import platform
import subprocess
import uuid
import os
import json
import sys
from datetime import datetime

class HardwareID:
    def __init__(self):
        self.hardware_id = None
        self.authorized_id = None
        
    def get_cpu_id(self):
        """Obtiene información del procesador"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'cpu', 'get', 'ProcessorId'], 
                                      capture_output=True, text=True)
                cpu_id = result.stdout.split('\n')[1].strip()
                return cpu_id
            else:
                # Para Linux/Mac
                result = subprocess.run(['cat', '/proc/cpuinfo'], 
                                      capture_output=True, text=True)
                for line in result.stdout.split('\n'):
                    if 'Serial' in line:
                        return line.split(':')[1].strip()
                return str(uuid.getnode())
        except:
            return str(uuid.getnode())
    
    def get_motherboard_serial(self):
        """Obtiene el serial de la placa madre"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'baseboard', 'get', 'SerialNumber'], 
                                      capture_output=True, text=True)
                serial = result.stdout.split('\n')[1].strip()
                return serial
            else:
                result = subprocess.run(['sudo', 'dmidecode', '-s', 'baseboard-serial-number'], 
                                      capture_output=True, text=True)
                return result.stdout.strip()
        except:
            return "UNKNOWN"
    
    def get_disk_serial(self):
        """Obtiene el serial del disco duro principal"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'diskdrive', 'get', 'SerialNumber'], 
                                      capture_output=True, text=True)
                serials = [line.strip() for line in result.stdout.split('\n') if line.strip() and 'SerialNumber' not in line]
                return serials[0] if serials else "UNKNOWN"
            else:
                result = subprocess.run(['lsblk', '-o', 'SERIAL'], 
                                      capture_output=True, text=True)
                return result.stdout.split('\n')[1].strip()
        except:
            return "UNKNOWN"
    
    def get_mac_address(self):
        """Obtiene la dirección MAC de la primera interfaz de red"""
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0,2*6,2)][::-1])
            return mac
        except:
            return "UNKNOWN"
    
    def generate_hardware_fingerprint(self):
        """Genera una huella digital única del hardware"""
        try:
            # Recopilar información del hardware
            cpu_id = self.get_cpu_id()
            motherboard_serial = self.get_motherboard_serial()
            disk_serial = self.get_disk_serial()
            mac_address = self.get_mac_address()
            
            # Información adicional del sistema
            system_info = {
                'platform': platform.platform(),
                'processor': platform.processor(),
                'machine': platform.machine(),
                'node': platform.node()
            }
            
            # Combinar toda la información
            hardware_string = f"{cpu_id}-{motherboard_serial}-{disk_serial}-{mac_address}-{system_info['machine']}-{system_info['processor']}"
            
            # Crear hash SHA256 para generar ID único
            hardware_hash = hashlib.sha256(hardware_string.encode()).hexdigest()
            
            # Formatear como ID más legible (dividir en grupos)
            formatted_id = f"{hardware_hash[:8]}-{hardware_hash[8:16]}-{hardware_hash[16:24]}-{hardware_hash[24:32]}"
            
            return {
                'hardware_id': formatted_id,
                'full_hash': hardware_hash,
                'components': {
                    'cpu_id': cpu_id,
                    'motherboard_serial': motherboard_serial,
                    'disk_serial': disk_serial,
                    'mac_address': mac_address
                },
                'system_info': system_info,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            # Si hay error, generar ID basado en UUID del nodo
            fallback_id = str(uuid.uuid4())
            return {
                'hardware_id': fallback_id,
                'full_hash': fallback_id,
                'components': {'error': str(e)},
                'system_info': {'platform': platform.platform()},
                'generated_at': datetime.now().isoformat(),
                'fallback': True
            }
    
    def capture_compilation_hardware(self):
        """
        SOLO para usar durante la compilación del ejecutable.
        Captura el ID de hardware de la máquina donde se compila.
        """
        hardware_data = self.generate_hardware_fingerprint()
        self.authorized_id = hardware_data['hardware_id']
        
        # Guardar el ID autorizado en un archivo que se incluirá en el ejecutable
        auth_file = "authorized_hardware.json"
        auth_data = {
            'authorized_hardware_id': self.authorized_id,
            'compilation_date': datetime.now().isoformat(),
            'compilation_machine': {
                'platform': platform.platform(),
                'node': platform.node()
            }
        }
        
        try:
            with open(auth_file, 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, indent=2, ensure_ascii=False)
            print(f"✓ ID de hardware autorizado guardado: {self.authorized_id}")
            print(f"✓ Archivo de autorización creado: {auth_file}")
            return True
        except Exception as e:
            print(f"✗ Error al crear archivo de autorización: {e}")
            return False
    
    def verify_hardware_authorization(self):
        """
        Verifica si el hardware actual coincide con el hardware autorizado
        durante la compilación.
        """
        try:
            # Buscar el archivo de autorización
            auth_file = "authorized_hardware.json"
            if getattr(sys, 'frozen', False):
                # Si es ejecutable, buscar en la carpeta del ejecutable
                auth_file = os.path.join(os.path.dirname(sys.executable), auth_file)
            
            # Intentar cargar el archivo de autorización
            if not os.path.exists(auth_file):
                return False, "Archivo de autorización no encontrado"
            
            with open(auth_file, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
            
            authorized_id = auth_data.get('authorized_hardware_id')
            if not authorized_id:
                return False, "ID de hardware autorizado no válido"
            
            # Obtener el ID de hardware actual
            current_hardware = self.generate_hardware_fingerprint()
            current_id = current_hardware['hardware_id']
            
            # Verificar si coinciden
            if current_id == authorized_id:
                self.hardware_id = current_id
                self.authorized_id = authorized_id
                return True, "Hardware autorizado"
            else:
                return False, f"Hardware no autorizado. Actual: {current_id[:16]}... vs Autorizado: {authorized_id[:16]}..."
                
        except Exception as e:
            return False, f"Error en verificación: {str(e)}"
    
    def get_hardware_id(self):
        """Obtiene el ID de hardware verificado"""
        if not self.hardware_id:
            is_authorized, message = self.verify_hardware_authorization()
            if not is_authorized:
                raise Exception(f"ACCESO DENEGADO: {message}")
        return self.hardware_id
    
    def get_hardware_info(self):
        """Obtiene información completa del hardware verificado"""
        if not self.hardware_id:
            is_authorized, message = self.verify_hardware_authorization()
            if not is_authorized:
                raise Exception(f"ACCESO DENEGADO: {message}")
        
        return self.generate_hardware_fingerprint()

# Función para usar durante la compilación
def capture_authorized_hardware():
    """
    SOLO llamar durante la compilación del ejecutable.
    Captura el hardware de la máquina donde se compila.
    """
    hw_id = HardwareID()
    return hw_id.capture_compilation_hardware()

# Función de verificación para uso en la aplicación
def get_unique_hardware_id():
    """
    Función para obtener el ID único SOLO si el hardware está autorizado.
    """
    hw_id = HardwareID()
    return hw_id.get_hardware_id()

# Función para obtener información completa verificada
def get_hardware_info():
    """Función para obtener información completa del hardware autorizado"""
    hw_id = HardwareID()
    return hw_id.get_hardware_info()

# Función de verificación explícita
def verify_authorized_hardware():
    """Verifica explícitamente si el hardware está autorizado"""
    hw_id = HardwareID()
    return hw_id.verify_hardware_authorization()

# Para testing y compilación
if __name__ == "__main__":
    print("=== SISTEMA DE PROTECCIÓN POR HARDWARE ===")
    
    # Si estamos en modo de captura (desarrollo)
    if len(sys.argv) > 1 and sys.argv[1] == "--capture":
        print("MODO CAPTURA: Guardando ID de hardware para compilación...")
        if capture_authorized_hardware():
            print("✓ Hardware capturado exitosamente")
            print("✓ Ahora puedes compilar el ejecutable")
        else:
            print("✗ Error al capturar hardware")
    else:
        # Modo verificación normal
        try:
            is_authorized, message = verify_authorized_hardware()
            if is_authorized:
                hw_id = get_unique_hardware_id()
                print(f"✓ ACCESO AUTORIZADO")
                print(f"✓ Hardware ID: {hw_id}")
            else:
                print(f"✗ ACCESO DENEGADO: {message}")
        except Exception as e:
            print(f"✗ ERROR CRÍTICO: {e}")