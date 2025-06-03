import socket


def enviar_a_impresora(ip, zpl_data):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((ip, 9100))

        s.sendall(zpl_data.encode('utf-8'))

        s.close()

        print("Etiqueta enviada correctamente.")
    except Exception as e:
        print(f"Ërror al conectar con la impresora: {e}")




nombre_mama = "Victoria Benavente"
dni_mama = "37582154"
fecha_nac_mama = "20/10/1990"

nombre_hospital = "ESPAÑOL"

zpl = """

^XA
^PW360  
^LL2100

^CI28
^FWB

; Nombre Hospital (arriba de Caja Bebé)
^FO200,460
^FB550,1,0,L,0
^A0B,25,25
^FDHospital: {nombre_hospital}^FS

; Caja Bebé
^FO240,460
^FB550,1,0,L,0
^A0B,25,25
^FDNombre: {nombre_mama}^FS

^FO280,460
^FB550,1,0,L,0
^A0B,25,25
^FDDNI: {dni_mama}^FS

^FO320,460
^FB550,1,0,L,0
^A0B,25,25
^FDFecha Nac.: {fecha_nac_mama}^FS

; Nombre Hospital (arriba de Datos Mamá)
^FO30,1260
^FB550,1,0,L,0
^A0B,25,25
^FDHospital: {nombre_hospital}^FS

; Datos de MAMÁ
^FO70,1260
^FB550,1,0,L,0
^A0B,25,25
^FDNombre: {nombre_mama}^FS

^FO110,1260
^FB550,1,0,L,0
^A0B,25,25
^FDDNI: {dni_mama}^FS

^FO150,1260
^FB550,1,0,L,0
^A0B,25,25
^FDFecha Nac.: {fecha_nac_mama}^FS

^XZ
""".format(
    nombre_mama=nombre_mama,
    dni_mama=dni_mama,
    fecha_nac_mama=fecha_nac_mama,
    nombre_hospital=nombre_hospital
)

print(zpl)




enviar_a_impresora("192.168.1.50", zpl)
