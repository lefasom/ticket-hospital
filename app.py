# main_app.py
import sys
import datetime
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QMainWindow
# Importa la clase de la UI generada
from PDCimpresora import Ui_MainWindow
# Importar el módulo de ID de hardware con protección
from hardware_id import get_unique_hardware_id, get_hardware_info, verify_authorized_hardware

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # VERIFICACIÓN CRÍTICA: Comprobar hardware autorizado ANTES de inicializar UI
        try:
            is_authorized, message = verify_authorized_hardware()
            if not is_authorized:
                self.show_unauthorized_access(message)
                sys.exit(1)  # Cerrar aplicación inmediatamente
            
            # Si llegamos aquí, el hardware está autorizado
            self.hardware_id = get_unique_hardware_id()
            
        except Exception as e:
            self.show_critical_error(str(e))
            sys.exit(1)  # Cerrar aplicación inmediatamente
        
        # Solo si pasa la verificación, inicializar la UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self) # Configura la UI en esta ventana principal
        
        # Mostrar información de autorización en la barra de título
        self.setWindowTitle(f"PDC Impresora [AUTORIZADO] - ID: {self.hardware_id[:8]}...")
        
        # Conectar señales (botones, etc.)
        self.ui.btnImprimir.clicked.connect(self.guardar_datos_en_txt)
    
    def show_unauthorized_access(self, message):
        """Muestra mensaje de acceso no autorizado"""
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("ACCESO DENEGADO")
        msg.setText("🚫 APLICACIÓN NO AUTORIZADA")
        msg.setInformativeText(f"""Esta aplicación solo puede ejecutarse en la computadora donde fue compilada.

Motivo: {message}

Para usar en esta computadora:
1. Obtenga el código fuente
2. Compile el ejecutable en ESTA máquina
3. Use el ejecutable generado localmente

ACCESO DENEGADO POR SEGURIDAD.""")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def show_critical_error(self, error_message):
        """Muestra mensaje de error crítico"""
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("ERROR CRÍTICO")
        msg.setText("⚠️ ERROR DE SISTEMA")
        msg.setInformativeText(f"""Error crítico en verificación de hardware:

{error_message}

La aplicación se cerrará por seguridad.""")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def get_hardware_summary(self):
        """Obtiene un resumen de la información de hardware para logging"""
        try:
            hw_info = get_hardware_info()
            return {
                'hardware_id': hw_info['hardware_id'],
                'platform': hw_info['system_info'].get('platform', 'Unknown'),
                'machine': hw_info['system_info'].get('machine', 'Unknown'),
                'generated_at': hw_info.get('generated_at', 'Unknown')
            }
        except:
            return {
                'hardware_id': self.hardware_id,
                'platform': 'Unknown',
                'machine': 'Unknown',
                'generated_at': 'Unknown'
            }

    def guardar_datos_en_txt(self):
        """
        Función para leer los datos de los QLineEdit y guardarlos en un archivo TXT.
        Incluye verificación de seguridad y el ID único de hardware autorizado.
        """
        # Verificación adicional de seguridad antes de cada operación crítica
        try:
            is_authorized, message = verify_authorized_hardware()
            if not is_authorized:
                QMessageBox.critical(self, "VIOLACIÓN DE SEGURIDAD", 
                                   f"Hardware no autorizado detectado: {message}\n\nLa aplicación se cerrará.")
                sys.exit(1)
        except Exception as e:
            QMessageBox.critical(self, "ERROR DE SEGURIDAD", f"Error en verificación: {e}")
            sys.exit(1)
        
        nombre_paciente = self.ui.txtNombrePaciente.text()
        dni_paciente = self.ui.txtDniPaciente.text()
        nacimiento_paciente = self.ui.txtNacimiento.text()
        nombre_hospital = self.ui.txtNombreHospital.text()
        dimension_impresion = self.ui.boxDimensionesImpresion.currentText()

        # Validar que los campos no estén vacíos
        if not nombre_paciente or not dni_paciente or not nacimiento_paciente or not nombre_hospital:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor, complete todos los campos antes de imprimir.")
            return

        nombre_archivo = "registro_impresiones.txt"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Obtener información de hardware para el registro
        hw_summary = self.get_hardware_summary()
        
        # Crear línea de datos con información de hardware AUTORIZADO
        linea_datos = f"""[{timestamp}] - Hardware AUTORIZADO ID: {hw_summary['hardware_id']}
Hospital: {nombre_hospital}
=>
Paciente: {nombre_paciente}
DNI: {dni_paciente}
Nacimiento: {nacimiento_paciente}
Tipo de ticket: {dimension_impresion}
Sistema: {hw_summary['platform']} ({hw_summary['machine']})
Estado: ✓ HARDWARE VERIFICADO Y AUTORIZADO
ID Hardware generado: {hw_summary['generated_at']}
{'='*70}

"""

        try:
            with open(nombre_archivo, 'a', encoding='utf-8') as f:
                f.write(linea_datos)

            # Mostrar mensaje de éxito con información de seguridad
            mensaje_exito = f"""✓ Datos guardados correctamente en '{nombre_archivo}'.

🔒 SISTEMA SEGURO ACTIVO
Hardware ID Autorizado: {self.hardware_id[:16]}...
Registro único para esta máquina autorizada."""

            QMessageBox.information(self, "✓ Éxito - Sistema Autorizado", mensaje_exito)

            # Limpiar los campos después de guardar
            self.ui.txtNombrePaciente.clear()
            self.ui.txtDniPaciente.clear()
            self.ui.txtNacimiento.clear()
            self.ui.txtNombreHospital.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo: {e}")
    
    def mostrar_info_seguridad(self):
        """
        Función para mostrar información de seguridad y hardware autorizado
        """
        try:
            hw_info = get_hardware_info()
            
            info_text = f"""🔒 SISTEMA DE SEGURIDAD ACTIVO

=== INFORMACIÓN DE AUTORIZACIÓN ===
✓ Hardware ID Autorizado: {hw_info['hardware_id']}
✓ Generado: {hw_info['generated_at']}
✓ Estado: ACCESO PERMITIDO

=== COMPONENTES VERIFICADOS ===
CPU ID: {hw_info['components'].get('cpu_id', 'N/A')}
Placa Madre: {hw_info['components'].get('motherboard_serial', 'N/A')}
Disco: {hw_info['components'].get('disk_serial', 'N/A')}
MAC: {hw_info['components'].get('mac_address', 'N/A')}

=== SISTEMA AUTORIZADO ===
Plataforma: {hw_info['system_info'].get('platform', 'N/A')}
Procesador: {hw_info['system_info'].get('processor', 'N/A')}
Máquina: {hw_info['system_info'].get('machine', 'N/A')}
Nodo: {hw_info['system_info'].get('node', 'N/A')}

⚠️  ADVERTENCIA DE SEGURIDAD:
Esta aplicación SOLO funciona en la computadora donde fue compilada.
Cualquier intento de uso en otra máquina será bloqueado."""

            QMessageBox.information(self, "🔒 Información de Seguridad", info_text)
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Seguridad", f"Error al obtener información de seguridad: {e}")

# Esto es lo que se ejecuta cuando corres este script
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    try:
        window = MyMainWindow()
        
        # Mostrar información de hardware autorizado al iniciar
        print(f"🔒 Aplicación AUTORIZADA iniciada con Hardware ID: {window.hardware_id}")
        print("✓ Sistema de seguridad activo")
        
        window.show()
        sys.exit(app.exec_())
        
    except SystemExit:
        # Salida controlada por falta de autorización
        pass
    except Exception as e:
        print(f"Error crítico al inicializar: {e}")
        sys.exit(1)