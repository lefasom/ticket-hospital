import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import sys
import datetime
import uuid
import re
from typing import Dict, List, Optional, Tuple

# Importar la configuración de Firebase para mantener consistencia
from firebase_config import get_firebase_instance
from hardware_id import get_hardware_id # Importa esta función

class LicenseManager:
    """Gestor de licencias para Firebase Firestore"""
    
    def __init__(self):
        self.db = None
        self.firebase_instance = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Inicializa la conexión a Firebase"""
        try:
            self.firebase_instance = get_firebase_instance()
            success, message = self.firebase_instance.initialize_with_service_account()
            
            if success:
                self.db = self.firebase_instance.get_firestore_client()
                print("✅ Conexión a Firebase establecida con éxito.")
                return True
            else:
                print(f"❌ Error al conectar con Firebase: {message}")
                return False
                
        except Exception as e:
            print(f"❌ Error crítico al inicializar Firebase: {e}")
            print("Asegúrate de que 'serviceAccountKey.json' esté presente y sea válido.")
            return False
    
    def generate_license_code(self, prefix: str = "FULLMED") -> str:
        """Genera un código de licencia único basado en UUID."""
        # Genera un UUID y toma los primeros 8 caracteres hexadecimales
        unique_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"{prefix}-{unique_part}"

    def add_license(self):
        """Añade una nueva licencia a Firestore."""
        print("\n--- Añadir Nueva Licencia ---")
        license_code = input("📝 Ingrese el código de licencia (Enter para autogenerar): ").strip().upper()
        
        if not license_code:
            license_code = self.generate_license_code()
            print(f"✨ Código autogenerado: {license_code}")

        customer_name = input("👤 Nombre del Cliente: ").strip()
        notes = input("📝 Notas (opcional): ").strip()
        
        # Validar fecha de expiración
        expiration_date_str = input("📅 Fecha de expiración (YYYY-MM-DD, Enter para ilimitado): ").strip()
        expiration_date = None
        if expiration_date_str:
            try:
                expiration_date = datetime.datetime.strptime(expiration_date_str, '%Y-%m-%d')
            except ValueError:
                print("⚠️ Formato de fecha inválido. La licencia no tendrá fecha de expiración.")
        
        # Inicialmente, no vinculamos a un Hardware ID
        # Se vinculará cuando la aplicación cliente la active por primera vez
        license_data = {
            'code': license_code,
            'customer_name': customer_name,
            'hardware_id': '', # Vacío al crear, se llena en la activación del cliente
            'status': 'active',
            'created_at': datetime.datetime.now(),
            'activated_at': None, # Vacío al crear, se llena en la activación del cliente
            'expires_at': expiration_date,
            'notes': notes
        }

        try:
            self.db.collection('licenses').document(license_code).set(license_data)
            print(f"🎉 Licencia '{license_code}' añadida con éxito.")
        except Exception as e:
            print(f"❌ Error al añadir licencia: {e}")

    def view_license(self):
        """Muestra los detalles de una licencia específica."""
        print("\n--- Ver Detalles de Licencia ---")
        license_code = input("📝 Ingrese el código de licencia: ").strip().upper()

        try:
            doc = self.db.collection('licenses').document(license_code).get()
            if doc.exists:
                data = doc.to_dict()
                print(f"\n--- Detalles de la Licencia: {license_code} ---")
                print(f"  Código: {data.get('code', 'N/A')}")
                print(f"  Cliente: {data.get('customer_name', 'N/A')}")
                print(f"  Estado: {data.get('status', 'N/A')}")
                print(f"  Hardware ID: {data.get('hardware_id', 'N/A')}")
                print(f"  Creada: {data.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if data.get('created_at') else 'N/A'}")
                print(f"  Activada: {data.get('activated_at').strftime('%Y-%m-%d %H:%M:%S') if data.get('activated_at') else 'N/A'}")
                print(f"  Expira: {data.get('expires_at').strftime('%Y-%m-%d') if data.get('expires_at') else 'Nunca'}")
                print(f"  Notas: {data.get('notes', 'N/A')}")
            else:
                print(f"❌ La licencia '{license_code}' no encontrada.")
        except Exception as e:
            print(f"❌ Error al ver licencia: {e}")

    def update_license(self):
        """Actualiza campos de una licencia existente."""
        print("\n--- Actualizar Licencia ---")
        license_code = input("📝 Ingrese el código de licencia a actualizar: ").strip().upper()

        try:
            doc_ref = self.db.collection('licenses').document(license_code)
            doc = doc_ref.get()

            if not doc.exists:
                print(f"❌ La licencia '{license_code}' no encontrada.")
                return

            print(f"🔎 Licencia encontrada. Deje en blanco los campos que no desea cambiar.")
            current_data = doc.to_dict()
            update_data = {}

            # Nombre del cliente
            new_customer_name = input(f"👤 Nuevo Nombre del Cliente (actual: {current_data.get('customer_name', 'N/A')}): ").strip()
            if new_customer_name:
                update_data['customer_name'] = new_customer_name
            
            # Hardware ID
            new_hardware_id = input(f"🖥️ Nuevo Hardware ID (actual: {current_data.get('hardware_id', 'N/A')}, dejar en blanco para quitar): ").strip()
            # Si se deja en blanco, establecer como string vacío para quitar el valor
            update_data['hardware_id'] = new_hardware_id 
            
            # Estado
            new_status = input(f"🚦 Nuevo Estado (active/inactive, actual: {current_data.get('status', 'N/A')}): ").strip().lower()
            if new_status in ['active', 'inactive']:
                update_data['status'] = new_status
            elif new_status:
                print("⚠️ Estado no válido. Se mantendrá el actual.")
            
            # Fecha de activación (se actualiza solo si se cambia el hardware_id o se activa/desactiva)
            if 'hardware_id' in update_data and update_data['hardware_id']: # Si se asigna un ID
                if not current_data.get('activated_at'): # Y no estaba activada
                    update_data['activated_at'] = datetime.datetime.now()
            elif 'hardware_id' in update_data and not update_data['hardware_id']: # Si se quita el ID
                update_data['activated_at'] = None # Desactivar la fecha de activación

            # Fecha de expiración
            current_expires_at = current_data.get('expires_at')
            current_expires_at_str = current_expires_at.strftime('%Y-%m-%d') if current_expires_at else 'Nunca'
            new_expiration_date_str = input(f"📅 Nueva Fecha de expiración (YYYY-MM-DD, Enter para ilimitado, 'X' para quitar): (actual: {current_expires_at_str}): ").strip()
            
            if new_expiration_date_str.upper() == 'X':
                update_data['expires_at'] = None
            elif new_expiration_date_str:
                try:
                    update_data['expires_at'] = datetime.datetime.strptime(new_expiration_date_str, '%Y-%m-%d')
                except ValueError:
                    print("⚠️ Formato de fecha inválido. Se mantendrá la fecha de expiración actual.")
            
            # Notas
            new_notes = input(f"📝 Nuevas Notas (actual: {current_data.get('notes', 'N/A')}): ").strip()
            if new_notes:
                update_data['notes'] = new_notes

            if update_data:
                doc_ref.update(update_data)
                print(f"🎉 Licencia '{license_code}' actualizada con éxito.")
            else:
                print("ℹ️ No se realizaron cambios.")

        except Exception as e:
            print(f"❌ Error al actualizar licencia: {e}")

    def delete_license(self):
        """Elimina una licencia de Firestore."""
        print("\n--- Eliminar Licencia ---")
        license_code = input("📝 Ingrese el código de licencia a eliminar: ").strip().upper()

        confirm = input(f"⚠️ ¿Está seguro de eliminar la licencia '{license_code}'? (s/N): ").strip().lower()
        if confirm == 's':
            try:
                self.db.collection('licenses').document(license_code).delete()
                print(f"🗑️ Licencia '{license_code}' eliminada con éxito.")
            except Exception as e:
                print(f"❌ Error al eliminar licencia: {e}")
        else:
            print("🚫 Eliminación cancelada.")

    def list_licenses(self, filter_active: Optional[bool] = None, customer_filter: Optional[str] = None):
        """Lista todas las licencias, con opciones de filtro."""
        print("\n--- Listado de Licencias ---")
        query = self.db.collection('licenses')

        if filter_active is True:
            query = query.where('status', '==', 'active')
            print("Mostrando solo licencias activas.")
        elif filter_active is False:
            query = query.where('status', '==', 'inactive')
            print("Mostrando solo licencias inactivas.")

        if customer_filter:
            # Firestore no soporta "LIKE", así que haremos una búsqueda simple de "contiene"
            # y luego filtraremos en el cliente para coincidencias parciales.
            # Podríamos añadir un where('customer_name', '>=', customer_filter)
            # y then where('customer_name', '<=', customer_filter + '\uf8ff')
            # pero para simplicidad inicial, filtramos después de obtener.
            print(f"Filtrando por cliente: '{customer_filter}'")
            
        try:
            docs = query.stream()
            licenses = []
            for doc in docs:
                data = doc.to_dict()
                # Aplicar filtro de cliente si se especificó
                if customer_filter:
                    if customer_filter.lower() not in data.get('customer_name', '').lower():
                        continue # Saltar si no coincide con el filtro de cliente
                licenses.append(data)

            if not licenses:
                print("No se encontraron licencias con los criterios especificados.")
                return

            # Ordenar por código de licencia para una mejor lectura
            licenses.sort(key=lambda x: x.get('code', ''))

            print(f"\nTotal de licencias mostradas: {len(licenses)}\n")
            print("{:<15} {:<25} {:<10} {:<20} {:<15} {:<15} {:<25}".format(
                "CÓDIGO", "CLIENTE", "ESTADO", "EXPIRA", "ACTIVADA", "HW ID (parcial)", "NOTAS"))
            print("-" * 140)

            for lic in licenses:
                code = lic.get('code', 'N/A')
                customer = lic.get('customer_name', 'N/A')
                status = lic.get('status', 'N/A')
                
                expires_at = lic.get('expires_at')
                expires_str = expires_at.strftime('%Y-%m-%d') if expires_at else 'Nunca'
                
                activated_at = lic.get('activated_at')
                activated_str = activated_at.strftime('%Y-%m-%d') if activated_at else 'No'
                
                # Mostrar solo una parte del Hardware ID para mayor legibilidad
                hardware_id_full = lic.get('hardware_id', '')
                hardware_id_display = hardware_id_full[:8] + '...' if len(hardware_id_full) > 8 else hardware_id_full
                
                notes = lic.get('notes', 'N/A')
                notes_display = notes[:20] + '...' if len(notes) > 20 else notes


                print(f"{code:<15} {customer:<25} {status:<10} {expires_str:<20} {activated_str:<15} {hardware_id_display:<15} {notes_display:<25}")
            print("-" * 140)

        except Exception as e:
            print(f"❌ Error al listar licencias: {e}")

    def activate_license_on_current_machine(self):
        """
        Vincula una licencia existente al Hardware ID de la máquina actual.
        Útil para reasignar o reactivar.
        """
        print("\n--- Vincular Licencia a Máquina Actual (Sobrescribir Hardware ID) ---")
        license_code = input("📝 Ingrese el código de licencia a vincular: ").strip().upper()

        if not license_code:
            print("❌ Código de licencia no puede estar vacío.")
            return

        try:
            doc_ref = self.db.collection('licenses').document(license_code)
            doc = doc_ref.get()

            if not doc.exists:
                print(f"❌ La licencia '{license_code}' no existe en Firebase.")
                return

            current_hardware_id = get_hardware_id() # Obtiene el ID de la máquina actual

            if not current_hardware_id:
                print("❌ No se pudo obtener el Hardware ID de esta máquina. Verifique el módulo hardware_id.py")
                return

            print(f"✅ Hardware ID de esta máquina: {current_hardware_id}")
            print(f"⏳ Vinculando licencia '{license_code}' al Hardware ID de esta máquina...")

            # Actualizar la licencia
            update_data = {
                'hardware_id': current_hardware_id,
                'status': 'active', # Aseguramos que esté activa
                'activated_at': datetime.datetime.now() # Actualizamos la fecha de activación
            }
            doc_ref.update(update_data)
            print(f"🎉 Licencia '{license_code}' vinculada y activada con éxito a esta máquina.")
            print("⚠️ Asegúrese de eliminar el archivo 'license.json' local en la máquina cliente si hubo problemas previos.")

        except Exception as e:
            print(f"❌ Error al intentar vincular la licencia: {e}")
            
    def export_licenses_to_json(self, filename: Optional[str] = None):
        """Exporta todas las licencias a un archivo JSON."""
        print("\n--- Exportar Licencias a JSON ---")
        try:
            docs = self.db.collection('licenses').stream()
            licenses_data = []
            for doc in docs:
                data = doc.to_dict()
                # Convertir objetos datetime a strings para JSON
                for key, value in data.items():
                    if isinstance(value, datetime.datetime):
                        data[key] = value.isoformat()
                licenses_data.append(data)

            if not filename:
                filename = f"licenses_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            elif not filename.endswith('.json'):
                filename += '.json'

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(licenses_data, f, indent=4, ensure_ascii=False)
            print(f"✅ Todas las licencias exportadas a '{filename}' con éxito.")
        except Exception as e:
            print(f"❌ Error al exportar licencias: {e}")

    def check_expired_licenses(self):
        """Verifica y lista las licencias expiradas, con opción de desactivarlas."""
        print("\n--- Verificar y Desactivar Licencias Expiradas ---")
        try:
            # Obtener solo licencias activas que tienen una fecha de expiración
            docs = self.db.collection('licenses') \
                         .where('status', '==', 'active') \
                         .where('expires_at', '<', datetime.datetime.now()) \
                         .stream()
            
            expired_licenses = []
            for doc in docs:
                expired_licenses.append(doc)

            if not expired_licenses:
                print("No se encontraron licencias activas y expiradas.")
                return

            print("\n🚨 Se encontraron las siguientes licencias expiradas y activas:")
            for doc in expired_licenses:
                data = doc.to_dict()
                expires_str = data.get('expires_at').strftime('%Y-%m-%d') if data.get('expires_at') else 'N/A'
                print(f"  - Código: {data.get('code')}, Cliente: {data.get('customer_name')}, Expiró el: {expires_str}")

            confirm = input("\n¿Desea desactivar estas licencias ahora? (s/N): ").strip().lower()
            if confirm == 's':
                batch = self.db.batch()
                for doc in expired_licenses:
                    doc_ref = self.db.collection('licenses').document(doc.id)
                    batch.update(doc_ref, {'status': 'inactive'})
                batch.commit()
                print(f"🎉 Se desactivaron {len(expired_licenses)} licencias expiradas.")
            else:
                print("🚫 Desactivación cancelada.")

        except Exception as e:
            print(f"❌ Error al verificar/desactivar licencias expiradas: {e}")


def main():
    manager = LicenseManager()
    if not manager.db:
        print("No se pudo conectar a Firebase. Saliendo.")
        sys.exit(1)

    while True:
        print("\n--- Menú del Gestor de Licencias ---")
        print("1. Añadir Nueva Licencia")
        print("2. Ver Detalles de Licencia")
        print("3. Actualizar Licencia")
        print("4. Eliminar Licencia")
        print("5. Listar Todas las Licencias Activas")
        print("6. Listar Todas las Licencias Inactivas")
        print("7. Vincular Licencia a Máquina Actual (Sobrescribir Hardware ID)") # <--- NUEVA OPCIÓN
        print("8. Listar Licencias por Cliente")
        print("9. Verificar y Desactivar Licencias Expiradas")
        print("E. Exportar Licencias a JSON")
        print("S. Salir")

        choice = input("👉 Seleccione una opción: ").strip().upper()

        try:
            if choice == '1':
                manager.add_license()
            elif choice == '2':
                manager.view_license()
            elif choice == '3':
                manager.update_license()
            elif choice == '4':
                manager.delete_license()
            elif choice == '5':
                manager.list_licenses(filter_active=True)
            elif choice == '6':
                manager.list_licenses(filter_active=False)
            elif choice == '7': # <--- Llama al nuevo método
                manager.activate_license_on_current_machine()
            elif choice == '8':
                customer_filter = input("\n🔍 Ingrese parte del nombre del cliente: ").strip()
                manager.list_licenses(customer_filter=customer_filter)
            elif choice == '9':
                manager.check_expired_licenses()
            elif choice == 'E':
                filename = input("\n💾 Nombre del archivo (Enter para automático): ").strip()
                manager.export_licenses_to_json(filename if filename else None)
            elif choice == 'S':
                print("👋 Saliendo del gestor de licencias. ¡Hasta luego!")
                break
            else:
                print("❌ Opción no válida. Por favor, intente de nuevo.")

        except KeyboardInterrupt:
            print("\n\n🛑 Operación interrumpida por el usuario.")
            continue
        except Exception as e:
            print(f"\n❌ Error inesperado: {e}")
            continue
        
        input("\n📱 Presione Enter para continuar...") # Mantener la pausa para leer el resultado


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        sys.exit(1)
