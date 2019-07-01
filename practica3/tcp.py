import socket
from appJar import gui
import time
import peticiones as p
import udp as u

#URL y puerto del servidor
URL="vega.ii.uam.es"
PORT=8000



def enviarTCP(mensaje, usuario=False, IP=URL, PUERTO=PORT):
	"""
		Función que envía un mensaje tcp

		Args : mensaje -> mensaje a enviar
			   usuario (opcional) -> será true cuando devolvamos la lista
									 de usuarios del servidor

		Returns : respuesta al mensaje
	"""
	# Nos conectamos a la url por el puerto 8000
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.connect((IP, PUERTO))
	sock.sendall(mensaje.encode())
	respuesta = sock.recv(1024)
	# Si no hay usuario al que mandarselo devolvemos la respuesta
	if usuario == False:
		sock.close()
		return respuesta
	# Sino decodificamos la respuesta (lista de usuarios)
	else:
		while 1 :
			# Decodifica la lista y separa por '#'
			if respuesta.decode()[0] == "O":
				recv = respuesta.decode().split("#")
				pr = recv[0].split(" ")
				if int(pr[2]) != len(recv)-1 :
					respuesta = respuesta + sock.recv(120)
					continue
				else:
					sock.close()
					return respuesta
			# Mientras el mensaje sea OK
			else:
				sock.close()
				return respuesta



def conexioncontrol(ip, puerto, vc):
	"""
		Función que gestiona la conexión de control

		Args : ip -> ip de la conexión
			   puerto -> puerto de la conexión
			   vc -> interfaz gráfica de la aplicación
	"""
	#Crea el socket TCP y lo pone a escuchar
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	s.bind((ip, puerto))
	while 1:
		s.listen(1)
		# Acepta una conexión y recibe un mensaje
		conn, addr = s.accept()
		data = conn.recv(1024)
		mensaje = data.decode().split(" ")
		# Si es un mensaje de llamada, genera una pantalla de elección tras comprobar que no está ya en llamada
		if mensaje[0] == "CALLING":
			if vc.UDPcon is not None:
				m = "CALL_BUSY " + mensaje[1]
				conn.send(m.encode())
				break
			# Si se elige coger la llamada,se comprueba la versión, se envía la confirmación y se llama a la función pertinente
			elif vc.app.okBox("Llamada","Llamada entrante de " + mensaje[1]) == True:
				usuario = p.info_decode(mensaje[1])
				versiones = usuario[2].split("#")
				v = 0
				for i in range(0,len(versiones)):
					if vc.version == versiones[i]:
						m = "CALL_ACCEPTED " + mensaje[1] + " " + str(u.UDP_PORT)
						conn.send(m.encode())
						time.sleep(2)
						vc.llamada(mensaje[1],usuario[0],mensaje[2])
						v = 1
						break
				if v == 0:
					vc.app.warningBox("Error","Version no soportada")
					m = "CALL_DENIED " + mensaje[1]
					conn.send(m.encode())
			# En otro caso, la llamada es rechazada
			else:
				m = "CALL_DENIED " + mensaje[1]
				conn.send(m.encode())
		# Si se recibe el mensaje de pausa, se cambia la variable correspondiente y se quita el timeout del socket
		elif mensaje[0] == "CALL_HOLD":
			conn.send("Ok".encode())
			vc.UDPcon.pausa = True
			vc.UDPcon.sock_rcv.settimeout(None)
			vc.app.hideButton("Pausa")
			vc.app.showWidgetType(3,"Continua")
		# Si el mensaje es de continuar llamada, se cambia la variable Pausa y se restablece el timeout
		elif mensaje[0] == "CALL_RESUME":
			conn.send("Ok".encode())
			vc.UDPcon.pausa = False
			vc.UDPcon.sock_rcv.settimeout(10)
			vc.app.hideButton("Continua")
			vc.app.showWidgetType(3,"Pausa")
		# Si se quiere finalizar la llamada, se apunta UDPcon a None y se esconden los botones correspondientes
		elif mensaje[0] == "CALL_END":
			vc.UDPcon.llamada = False
			time.sleep(2)
			vc.UDPcon = None
			vc.app.hideButton("Colgar")
			vc.app.hideButton("Pausa")
			vc.app.hideButton("Video")
			vc.app.hideSubWindow("El otro")
			vc.app.showWidgetType(3,"Conectar")
		# Si el mensaje es de salir, se cierran los sockets y se sale
		elif mensaje[0] == "Salir":
			conn.close()
			s.shutdown(socket.SHUT_RDWR)
			s.close()
			return
		conn.close()

	s.shutdown(socket.SHUT_RDWR)
	s.close()

	return
