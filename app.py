# main_app.py
import sys
import datetime
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QMainWindow
# Importa la clase de la UI generada
from PDCimpresora import Ui_MainWindow

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self) # Configura la UI en esta ventana principal

        # Conectar señales (botones, etc.) aquí, NO en el archivo UI generado
        self.ui.pushButton.clicked.connect(self.guardar_datos_en_txt)

    def guardar_datos_en_txt(self):
        """
        Función para leer los datos de los QLineEdit y guardarlos en un archivo TXT.
        """
        nombre = self.ui.lineEditNombre.text()
        apellido = self.ui.lineEditApellido.text()
        nro_de_turno = self.ui.lineEditNroDeTurno.text()

        # Validar que los campos no estén vacíos
        if not nombre or not apellido or not nro_de_turno:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor, complete todos los campos antes de imprimir.")
            return

        nombre_archivo = "registro_impresiones.txt"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea_datos = f"[{timestamp}] Nombre: {nombre}, Apellido: {apellido}, Nro de Turno: {nro_de_turno}\n"

        try:
            with open(nombre_archivo, 'a', encoding='utf-8') as f:
                f.write(linea_datos)

            QMessageBox.information(self, "Éxito", f"Datos guardados en '{nombre_archivo}' correctamente.")

            # Limpiar los campos después de guardar
            self.ui.lineEditNombre.clear()
            self.ui.lineEditApellido.clear()
            self.ui.lineEditNroDeTurno.clear()

        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo: {e}")

# Esto es lo que se ejecuta cuando corres este script
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())