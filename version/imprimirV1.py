import socket
def enviar_a_impresora(ip, zpl_data):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((ip,9100))

        s.sendall(zpl_data.encode('utf-8'))

        s.close()

        print("Etiqueta enviada correctamente.")
    except Exception as e:
        print(f"Ërror al conectar con la impresora: {e}")


zpl = u"""^XA
^CI28
^CF0,30
^FO150,800^A0R,30,30^FDPaciente: {nombre}^FS
^FO190,800^A0R,30,30^FDHC: {hc}^FS
^FO230,800^A0R,30,30^FDCaso: {caso}^FS
^FO270,800^A0R,30,30^FDCopia: {copia}^FS
^XZ
""".format(nombre="Hospital Español", hc="45", caso="2", copia="3")



