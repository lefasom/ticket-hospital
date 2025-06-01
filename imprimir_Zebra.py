import sys
import datetime
import socket
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QMainWindow, QInputDialog
# Importa la clase de la UI generada
from PDCimpresora import Ui_MainWindow

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self) # Configura la UI en esta ventana principal

        # Configuración por defecto de la impresora (puede ser modificada)
        self.printer_ip = "192.168.1.100"  # IP por defecto de la impresora ZPL
        self.printer_port = 9100  # Puerto estándar para impresoras ZPL

        # Conectar señales (botones, etc.) aquí, NO en el archivo UI generado
        self.ui.btnImprimir.clicked.connect(self.procesar_impresion)

    def procesar_impresion(self):
        """
        Función principal que guarda los datos y luego procede a imprimir según la dimensión seleccionada.
        """
        # Primero guardamos los datos
        if not self.guardar_datos_en_txt():
            return  # Si hay error al guardar, no continuar con la impresión
        
        # Luego procedemos con la impresión ZPL
        self.imprimir_segun_dimension_zpl()

    def guardar_datos_en_txt(self):
        """
        Función para leer los datos de los QLineEdit y guardarlos en un archivo TXT.
        Retorna True si se guardó correctamente, False si hubo error.
        """
        nombre_paciente = self.ui.txtNombrePaciente.text()
        dni_paciente = self.ui.txtDniPaciente.text()
        nacimiento_paciente = self.ui.txtNacimiento.text()
        nombre_hospital = self.ui.txtNombreHospital.text()
        dimension_impresion = self.ui.boxDimensionesImpresion.currentText()

        # Validar que los campos no estén vacíos
        if not nombre_paciente or not dni_paciente or not nacimiento_paciente or not nombre_hospital:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor, complete todos los campos antes de imprimir.")
            return False

        nombre_archivo = "registro_impresiones.txt"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea_datos = f"[{timestamp}] \n Hospital: {nombre_hospital} \n=> \n Paciente: {nombre_paciente}, \n Dni: {dni_paciente}, \n Nacimiento: {nacimiento_paciente}, \n ticket: {dimension_impresion}\n"

        try:
            with open(nombre_archivo, 'a', encoding='utf-8') as f:
                f.write(linea_datos)

            QMessageBox.information(self, "Éxito", f"Datos guardados en '{nombre_archivo}' correctamente.")
            return True

        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo: {e}")
            return False

    def imprimir_segun_dimension_zpl(self):
        """
        Función que maneja la impresión ZPL según la dimensión seleccionada.
        """
        dimension_impresion = self.ui.boxDimensionesImpresion.currentText()
        
        # Obtener los datos para imprimir
        nombre_paciente = self.ui.txtNombrePaciente.text()
        dni_paciente = self.ui.txtDniPaciente.text()
        nacimiento_paciente = self.ui.txtNacimiento.text()
        nombre_hospital = self.ui.txtNombreHospital.text()
        
        # Usar if/elif para manejar diferentes dimensiones ZPL
        if dimension_impresion == "80x80mm":
            zpl_code = self.generar_zpl_80x80(nombre_paciente, dni_paciente, nacimiento_paciente, nombre_hospital)
        elif dimension_impresion == "58x58mm":
            zpl_code = self.generar_zpl_58x58(nombre_paciente, dni_paciente, nacimiento_paciente, nombre_hospital)
        elif dimension_impresion == "100x80mm":
            zpl_code = self.generar_zpl_100x80(nombre_paciente, dni_paciente, nacimiento_paciente, nombre_hospital)
        elif dimension_impresion == "4x2 pulgadas":
            zpl_code = self.generar_zpl_4x2_pulgadas(nombre_paciente, dni_paciente, nacimiento_paciente, nombre_hospital)
        elif dimension_impresion == "2.25 x 1.25 (Pulsera hospitalaria)":
            zpl_code = self.generar_zpl_pulsera_hospitalaria(nombre_paciente, dni_paciente, nacimiento_paciente, nombre_hospital)
        else:
            # Dimensión por defecto o no reconocida
            QMessageBox.warning(self, "Dimensión no reconocida", f"La dimensión '{dimension_impresion}' no está configurada.")
            return
        
        # Enviar código ZPL a la impresora
        if self.enviar_zpl_a_impresora(zpl_code):
            # Limpiar los campos después de imprimir exitosamente
            self.limpiar_campos()

    def generar_zpl_80x80(self, nombre, dni, nacimiento, hospital):
        """
        Genera código ZPL para etiqueta de 80x80mm
        """
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        zpl = f"""^XA
^MMT
^PW609
^LL609
^LS0

^FT50,50^A0N,28,28^FDTICKET MEDICO^FS
^FT50,100^GB500,3,3^FS

^FT50,140^A0N,20,20^FDHospital:^FS
^FT50,170^A0N,18,18^FD{hospital[:30]}^FS

^FT50,220^A0N,20,20^FDPaciente:^FS
^FT50,250^A0N,18,18^FD{nombre[:25]}^FS

^FT50,300^A0N,20,20^FDDNI: {dni}^FS

^FT50,340^A0N,20,20^FDNacimiento:^FS
^FT50,370^A0N,18,18^FD{nacimiento}^FS

^FT50,420^A0N,16,16^FD{timestamp}^FS

^FT50,460^GB500,3,3^FS
^FT50,490^A0N,14,14^FDFormato: 80x80mm^FS

^XZ"""
        return zpl

    def generar_zpl_58x58(self, nombre, dni, nacimiento, hospital):
        """
        Genera código ZPL para etiqueta de 58x58mm (más compacta)
        """
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y")
        
        zpl = f"""^XA
^MMT
^PW435
^LL435
^LS0

^FT30,30^A0N,24,24^FDTICKET MED.^FS
^FT30,65^GB375,2,2^FS

^FT30,95^A0N,16,16^FDHospital:^FS
^FT30,120^A0N,14,14^FD{hospital[:20]}^FS

^FT30,155^A0N,16,16^FDPaciente:^FS
^FT30,180^A0N,14,14^FD{nombre[:18]}^FS

^FT30,210^A0N,16,16^FDDNI: {dni}^FS

^FT30,240^A0N,16,16^FDNac: {nacimiento}^FS

^FT30,280^A0N,12,12^FD{timestamp}^FS

^FT30,310^GB375,2,2^FS
^FT30,335^A0N,12,12^FD58x58mm^FS

^XZ"""
        return zpl

    def generar_zpl_100x80(self, nombre, dni, nacimiento, hospital):
        """
        Genera código ZPL para etiqueta de 100x80mm
        """
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        zpl = f"""^XA
^MMT
^PW754
^LL609
^LS0

^FT50,40^A0N,32,32^FDREGISTRO MEDICO^FS
^FT50,80^GB650,4,4^FS

^FT50,120^A0N,22,22^FDHOSPITAL:^FS
^FT200,120^A0N,20,20^FD{hospital[:35]}^FS

^FT50,170^A0N,22,22^FDPACIENTE:^FS
^FT200,170^A0N,20,20^FD{nombre[:30]}^FS

^FT50,220^A0N,22,22^FDDNI:^FS
^FT200,220^A0N,20,20^FD{dni}^FS

^FT50,270^A0N,22,22^FDNACIMIENTO:^FS
^FT200,270^A0N,20,20^FD{nacimiento}^FS

^FT50,330^A0N,18,18^FDFecha de impresion:^FS
^FT50,360^A0N,16,16^FD{timestamp}^FS

^FT50,420^GB650,3,3^FS
^FT50,450^A0N,16,16^FDFormato: 100x80mm^FS

^XZ"""
        return zpl

    def generar_zpl_4x2_pulgadas(self, nombre, dni, nacimiento, hospital):
        """
        Genera código ZPL para etiqueta de 4x2 pulgadas (estándar médico)
        """
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
        zpl = f"""^XA
^MMT
^PW812
^LL406
^LS0

^FT50,35^A0N,28,28^FDIDENTIFICACION PACIENTE^FS
^FT50,70^GB712,3,3^FS

^FT50,110^A0N,20,20^FDHOSPITAL: {hospital[:40]}^FS

^FT50,150^A0N,20,20^FDPACIENTE: {nombre[:35]}^FS

^FT50,190^A0N,20,20^FDDNI: {dni}     NACIMIENTO: {nacimiento}^FS

^FT50,240^A0N,16,16^FDImpreso: {timestamp}^FS

^FT50,280^GB712,2,2^FS
^FT50,310^A0N,14,14^FDFormato: 4x2 pulgadas^FS

^XZ"""
        return zpl

    def generar_zpl_pulsera_hospitalaria(self, nombre, dni, nacimiento, hospital):
        """
        Genera código ZPL para pulsera hospitalaria de 2.25 x 1.25 pulgadas
        """
        timestamp = datetime.datetime.now().strftime("%d/%m/%Y")
        
        zpl = f"""^XA
^MMT
^PW576
^LL300
^LS0

^FT20,25^A0N,18,18^FDPULSERA HOSPITALARIA^FS
^FT20,50^GB536,2,2^FS

^FT20,75^A0N,16,16^FD{hospital[:25]}^FS

^FT20,105^A0N,14,14^FD{nombre[:22]}^FS
^FT20,130^A0N,14,14^FDDNI: {dni}^FS
^FT20,155^A0N,14,14^FDNac: {nacimiento}^FS

^FT20,185^A0N,12,12^FD{timestamp}^FS

^FT20,210^GB536,2,2^FS
^FT20,235^A0N,10,10^FDPulsera 2.25x1.25^FS

^XZ"""
        return zpl

    def enviar_zpl_a_impresora(self, zpl_code):
        """
        Envía el código ZPL a la impresora a través de red o puerto.
        Retorna True si se envió correctamente, False si hubo error.
        """
        try:
            # Preguntar al usuario el método de envío
            items = ("Red (IP)", "Puerto COM", "Archivo ZPL", "Cancelar")
            item, ok = QInputDialog.getItem(self, "Método de Impresión", 
                                          "Selecciona cómo enviar a la impresora:", items, 0, False)
            
            if not ok or item == "Cancelar":
                return False
            
            if item == "Red (IP)":
                return self.enviar_por_red(zpl_code)
            elif item == "Puerto COM":
                return self.enviar_por_puerto_serie(zpl_code)
            elif item == "Archivo ZPL":
                return self.guardar_archivo_zpl(zpl_code)
                
        except Exception as e:
            QMessageBox.critical(self, "Error de Impresión", f"Error al enviar a la impresora: {e}")
            return False

    def enviar_por_red(self, zpl_code):
        """
        Envía ZPL por red TCP/IP
        """
        try:
            # Permitir al usuario cambiar la IP si es necesario
            ip, ok = QInputDialog.getText(self, "IP de Impresora", 
                                        f"IP de la impresora ZPL:", text=self.printer_ip)
            if not ok:
                return False
                
            self.printer_ip = ip
            
            # Crear socket y enviar
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)  # Timeout de 10 segundos
            sock.connect((self.printer_ip, self.printer_port))
            sock.send(zpl_code.encode('utf-8'))
            sock.close()
            
            QMessageBox.information(self, "Éxito", f"Etiqueta enviada a impresora {self.printer_ip}")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Red", f"No se pudo conectar a la impresora: {e}")
            return False

    def enviar_por_puerto_serie(self, zpl_code):
        """
        Envía ZPL por puerto serie/COM
        """
        try:
            import serial
            
            # Permitir al usuario especificar el puerto COM
            puerto, ok = QInputDialog.getText(self, "Puerto COM", 
                                            "Puerto COM (ej: COM1, COM3):", text="COM1")
            if not ok:
                return False
            
            # Configurar y enviar por puerto serie
            ser = serial.Serial(puerto, 9600, timeout=5)
            ser.write(zpl_code.encode('utf-8'))
            ser.close()
            
            QMessageBox.information(self, "Éxito", f"Etiqueta enviada a puerto {puerto}")
            return True
            
        except ImportError:
            QMessageBox.critical(self, "Módulo Requerido", 
                               "Para usar puerto COM, instala: pip install pyserial")
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error Puerto COM", f"Error en puerto serie: {e}")
            return False

    def guardar_archivo_zpl(self, zpl_code):
        """
        Guarda el código ZPL en un archivo para revisión o envío manual
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"etiqueta_{timestamp}.zpl"
            
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(zpl_code)
            
            QMessageBox.information(self, "Archivo Guardado", 
                                  f"Código ZPL guardado en: {nombre_archivo}\n\n"
                                  "Puedes enviar este archivo directamente a tu impresora ZPL.")
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar ZPL", f"No se pudo guardar el archivo ZPL: {e}")
            return False

    def limpiar_campos(self):
        """
        Función para limpiar todos los campos de entrada después de una impresión exitosa.
        """
        self.ui.txtNombrePaciente.clear()
        self.ui.txtDniPaciente.clear()
        self.ui.txtNacimiento.clear()
        self.ui.txtNombreHospital.clear()

# Esto es lo que se ejecuta cuando corres este script
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())