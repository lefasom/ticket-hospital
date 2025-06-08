# hardware_id.py
import hashlib
import platform
import subprocess
import uuid
import os
import json
import sys
from datetime import datetime
import psutil  # Para obtener información de hardware más confiable

class HardwareID:
    def __init__(self):
        self.hardware_id = None
        self.hardware_info_cache = None

    def get_cpu_id(self):
        """Obtiene información del procesador de manera más confiable"""
        try:
            if platform.system() == "Windows":
                # Método principal: WMIC
                try:
                    result = subprocess.run(
                        ['wmic', 'cpu', 'get', 'ProcessorId', '/format:value'], 
                        capture_output=True, text=True, check=True, 
                        encoding='utf-8', errors='ignore', timeout=15
                    )
                    for line in result.stdout.split('\n'):
                        if 'ProcessorId=' in line:
                            cpu_id = line.split('=')[1].strip()
                            if cpu_id and cpu_id != "":
                                return cpu_id
                except Exception:
                    pass
                
                # Método alternativo: Registry
                try:
                    result = subprocess.run([
                        'reg', 'query', 
                        'HKEY_LOCAL_MACHINE\\HARDWARE\\DESCRIPTION\\System\\CentralProcessor\\0',
                        '/v', 'Identifier'
                    ], capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=15)
                    for line in result.stdout.split('\n'):
                        if 'Identifier' in line:
                            return line.split('REG_SZ')[-1].strip()
                except Exception:
                    pass
            elif platform.system() == "Linux":
                # Intenta leer /proc/cpuinfo
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if 'processor' in line: # Toma el primer procesador
                                return hashlib.sha256(line.encode()).hexdigest()
                except Exception:
                    pass
            # Fallback para otros sistemas o si los métodos anteriores fallan
            return str(uuid.getnode()) # MAC address como fallback, menos fiable
        except Exception as e:
            # print(f"Error al obtener CPU ID: {e}")
            return "UNKNOWN_CPU"

    def get_motherboard_serial(self):
        """Obtiene el número de serie de la placa base."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'baseboard', 'get', 'SerialNumber', '/format:value'], capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=15)
                for line in result.stdout.split('\n'):
                    if 'SerialNumber=' in line:
                        serial = line.split('=')[1].strip()
                        if serial and serial != "":
                            return serial
            elif platform.system() == "Linux":
                # Intenta usar dmidecode para obtener el serial
                try:
                    result = subprocess.run(['sudo', 'dmidecode', '-s', 'baseboard-serial-number'], capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=15)
                    serial = result.stdout.strip()
                    if serial and serial != "":
                        return serial
                except Exception:
                    pass
            return "UNKNOWN_MB"
        except Exception as e:
            # print(f"Error al obtener serial de placa base: {e}")
            return "UNKNOWN_MB"

    def get_disk_serial(self):
        """Obtiene el número de serie del disco principal."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'diskdrive', 'get', 'SerialNumber', '/format:value'], capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=15)
                for line in result.stdout.split('\n'):
                    if 'SerialNumber=' in line:
                        serial = line.split('=')[1].strip()
                        if serial and serial != "":
                            return serial
            elif platform.system() == "Linux":
                # Usar lsblk o hdparm
                try:
                    result = subprocess.run(['lsblk', '-no', 'serial', '/dev/sda'], capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=15)
                    serial = result.stdout.strip()
                    if serial and serial != "":
                        return serial
                except Exception:
                    pass
            return "UNKNOWN_DISK"
        except Exception as e:
            # print(f"Error al obtener serial de disco: {e}")
            return "UNKNOWN_DISK"

    def get_mac_address(self):
        """Obtiene las direcciones MAC de las interfaces de red."""
        mac_addresses = []
        try:
            # Usar psutil para obtener direcciones MAC de manera robusta
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK: # AF_LINK es para MAC
                        if addr.address:
                            mac_addresses.append(addr.address)
            return sorted(list(set(mac_addresses))) # Eliminar duplicados y ordenar
        except Exception as e:
            # print(f"Error al obtener MAC addresses con psutil: {e}")
            # Fallback (menos robusto)
            try:
                # Método para Windows
                if platform.system() == "Windows":
                    result = subprocess.run(['getmac', '/v', '/fo', 'list'], capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=15)
                    for line in result.stdout.split('\n'):
                        if 'Physical Address:' in line:
                            mac_addresses.append(line.split(':')[1].strip())
                # Método para Linux
                elif platform.system() == "Linux":
                    result = subprocess.run(['ip', 'link'], capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=15)
                    for line in result.stdout.split('\n'):
                        if 'link/ether' in line:
                            mac_addresses.append(line.split(' ')[1].strip())
            except Exception:
                pass
            return sorted(list(set(mac_addresses))) if mac_addresses else ["UNKNOWN_MAC"]


    def get_system_uuid(self):
        """Obtiene el UUID del sistema (si está disponible)."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['wmic', 'csproduct', 'get', 'UUID', '/format:value'], capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', timeout=15)
                for line in result.stdout.split('\n'):
                    if 'UUID=' in line:
                        system_uuid = line.split('=')[1].strip()
                        if system_uuid and system_uuid != "":
                            return system_uuid
            elif platform.system() == "Linux":
                try:
                    with open('/sys/class/dmi/id/product_uuid', 'r') as f:
                        system_uuid = f.read().strip()
                        if system_uuid and system_uuid != "":
                            return system_uuid
                except Exception:
                    pass
            return "UNKNOWN_UUID"
        except Exception as e:
            # print(f"Error al obtener UUID del sistema: {e}")
            return "UNKNOWN_UUID"

    def get_os_info(self):
        """Obtiene información básica del sistema operativo y procesador."""
        return {
            "system": platform.system(),
            "node_name": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0]
        }

    def get_hardware_info_detailed(self):
        """Recopila toda la información de hardware relevante y la almacena en caché."""
        if self.hardware_info_cache:
            return self.hardware_info_cache

        info = {
            "cpu_id": self.get_cpu_id(),
            "motherboard_serial": self.get_motherboard_serial(),
            "disk_serial": self.get_disk_serial(),
            "mac_addresses": self.get_mac_address(),
            "system_uuid": self.get_system_uuid(),
            "os_info": self.get_os_info(),
            "timestamp": datetime.now().isoformat()
        }
        self.hardware_info_cache = info
        return info

    def get_hardware_id(self):
        """Genera un Hardware ID único basado en la información de hardware."""
        if self.hardware_id:
            return self.hardware_id

        # Obtener información detallada del hardware
        info = self.get_hardware_info_detailed()

        # Concatenar las partes más estables para formar la huella digital
        # Excluir el timestamp y la información del SO si queremos un ID más estable
        # ya que el SO y el timestamp pueden cambiar sin cambiar el hardware
        fingerprint_parts = [
            info["cpu_id"],
            info["motherboard_serial"],
            info["disk_serial"],
            # Unir las MACs de forma consistente
            ",".join(info["mac_addresses"]), 
            info["system_uuid"]
        ]
        
        # Filtrar partes que puedan ser "UNKNOWN" si se prefieren IDs más cortos y determinísticos
        # Si se desea un ID más robusto, se pueden incluir, pero con riesgo de ser "UNKNOWN"
        # y afectar la consistencia si esos datos no están disponibles.
        # Aquí, incluimos todo para mayor robustez.
        
        raw_fingerprint = ":".join(fingerprint_parts).strip()
        
        # Calcular el hash SHA-256 de la huella digital
        self.hardware_id = hashlib.sha256(raw_fingerprint.encode('utf-8')).hexdigest().upper()
        return self.hardware_id

    def save_hardware_info(self, filename: str) -> bool:
        """Guarda la información detallada del hardware en un archivo JSON."""
        try:
            info = self.get_hardware_info_detailed()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            return False

# Funciones de utilidad
def get_hardware_id():
    """Función simple para obtener el Hardware ID"""
    hw = HardwareID()
    return hw.get_hardware_id()

def get_hardware_info():
    """Función para obtener información completa de hardware"""
    hw = HardwareID()
    return hw.get_hardware_info_detailed()

# Script de prueba y generación
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generador de Hardware ID')
    parser.add_argument('--info', action='store_true', help='Mostrar información detallada')
    parser.add_argument('--save', type=str, help='Guardar información en archivo')
    
    args = parser.parse_args()
    
    hw = HardwareID()
    
    if args.info:
        info = hw.get_hardware_info_detailed()
        print("=== INFORMACIÓN DE HARDWARE ===")
        for key, value in info.items():
            print(f"{key}: {value}")
        print("\n=== HARDWARE ID ===")
        print(hw.get_hardware_id())
    
    elif args.save:
        if hw.save_hardware_info(args.save):
            print(f"Información de hardware guardada en '{args.save}'.")
        else:
            print(f"Error al guardar información de hardware en '{args.save}'.")
    else:
        print("Uso:")
        print("  python hardware_id.py --info       (para mostrar información detallada y el ID)")
        print("  python hardware_id.py --save <ruta> (para guardar la información en un archivo JSON)")