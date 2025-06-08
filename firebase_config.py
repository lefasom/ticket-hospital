# firebase_config.py
import firebase_admin
from firebase_admin import credentials, firestore
import sys
import os

class FirebaseConfig:
    """Clase para manejar la configuración y conexión a Firebase"""
    
    _instance = None # Para implementar el patrón Singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseConfig, cls).__new__(cls)
            cls._instance._initialized = False # Para asegurar que la inicialización solo corra una vez
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.db = None
            self.app = None
            self._initialized = True
        
    def initialize_with_service_account(self, service_account_path='serviceAccountKey.json'):
        """
        Inicializa Firebase Admin SDK con credenciales de servicio
        Usado para el gestor de licencias (firebase_license_manager.py) y app.py
        """
        try:
            if self.db is not None: # Ya inicializado
                return True, "Firebase Admin SDK ya inicializado."

            if not firebase_admin._apps: # Si no hay apps de Firebase inicializadas globalmente
                # DEBUGGING TEMPORAL (mantenido aquí para que lo veas)
                # print(f"DEBUG: Directorio de trabajo actual: {os.getcwd()}")
                # full_path = os.path.abspath(service_account_path)
                # print(f"DEBUG: Intentando encontrar archivo en: {full_path}")
                # if os.path.exists(full_path):
                #     print(f"DEBUG: ¡Archivo '{service_account_path}' ENCONTRADO!")
                # else:
                #     print(f"DEBUG: Archivo '{service_account_path}' NO ENCONTRADO en esta ruta.")
                # FIN DEBUGGING TEMPORAL
                
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred)
            else:
                self.app = firebase_admin.get_app()

            self.db = firestore.client()
            return True, "Firebase Admin SDK inicializado correctamente"

        except FileNotFoundError:
            return False, f"Archivo de credenciales no encontrado: {service_account_path}"
        except Exception as e:
            return False, f"Error al inicializar Firebase Admin SDK: {str(e)}"
    
    def initialize_with_config(self, config_dict):
        """
        Inicializa Firebase con configuración básica (NO USADO EN ESTE PROYECTO PYTHON DIRECTAMENTE CON ESTOS VALORES)
        Nota: En Python, no podemos usar las credenciales web de Firebase directamente
        como se haría en JavaScript. Para aplicaciones de servidor/escritorio,
        el enfoque recomendado es el 'serviceAccountKey.json'.
        Este método se mantiene para compatibilidad conceptual o si se extiende
        a otros entornos que lo necesiten.
        """
        # Para aplicaciones cliente Python, también necesitamos el service account
        # No podemos usar apiKey, authDomain, etc. como en JavaScript
        service_account_path = 'serviceAccountKey.json'
        
        if os.path.exists(service_account_path):
            return self.initialize_with_service_account(service_account_path)
        else:
            return False, "Para aplicaciones Python se requiere serviceAccountKey.json"
            
    def get_firestore_client(self):
        """Retorna el cliente de Firestore"""
        return self.db
    
    def is_initialized(self):
        """Verifica si Firebase está inicializado"""
        return self.db is not None

# Función para obtener la instancia Singleton de FirebaseConfig
def get_firebase_instance():
    return FirebaseConfig()

# Configuración para la aplicación cliente
# Nota: Estos valores no se usan directamente en Python, 
# pero los mantenemos para referencia
CLIENT_FIREBASE_CONFIG = {
    "apiKey": "AIzaSyC5jvy2WELzGdcBPZGJhFfaI2da7EZ3hvI",
    "authDomain": "stock-native-fd1da.firebaseapp.com",
    "projectId": "stock-native-fd1da",
    "storageBucket": "stock-native-fd1da.appspot.com",
    "messagingSenderId": "546289091375",
    "appId": "1:546289091375:web:8e3d08c5c701777d13b41e"
}