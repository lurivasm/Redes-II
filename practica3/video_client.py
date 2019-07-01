# import the library
from appJar import gui
from PIL import Image, ImageTk
import numpy as np
import cv2
import peticiones as p
import threading
import tcp as t
import socket
import time
import udp as u
import os


class VideoClient(object):
	"""
		Clase que controla la interfaz de gestión del video
		Funciones:
				init -> inicia la clase con un tamaño de ventana
				start -> inicia la aplicación
				reproduceVideo -> reproduce el video recibido
				capturaVideo -> reproduce y envia el video del usuario
				buttonsCallback -> controla las acciones de cada botón
								   (aceptar, cancelar y registrarse)
				llamada -> establece la llamada
				menuPress -> determina las acciones de los botones del menu

	"""
	def __init__(self, window_size, user, pwd, ip, puerto, version):

		"""
			Función que inicia la Clase
			Args:
				  self -> la misma clase
				  window_size -> tamaño que queremos para la ventana
				  user -> nick del usuario
				  pwd -> contraseña del usuario
				  ip -> ip del usuario
				  puerto > puerto TCP del usuario
				  version -> version de la aplicacion

			Returns : la clase incializada
		"""
		self.user = user
		self.ip = ip
		self.puerto = puerto
		self.pwd = pwd
		self.version = version
		self.salir = False
		thread = threading.Thread(target=t.conexioncontrol, args=(ip,int(puerto),self,))	#Inicializamos el thread de la conexión TCP de control
		thread.start()

		self.UDPcon = None

		# Creamos una variable que contenga el GUI principal
		self.app = gui("VideoIsComing", window_size)
		self.app.setGuiPadding(10,10)
		self.app.setBg("Light Green")
		self.app.setLabelFont(14, "Times")
		self.app.setButtonFont(14, "Times", )

		# Añadimos un menu con el perfil y full screen
		fileMenus = ["Cerrar Sesión", "Cerrar"]
		self.app.addMenuList("Perfil", fileMenus, self.menuPress)
		ajustesMenu = ["Cambiar Nombre", "Pantalla Completa", "Pantalla Normal"]
		self.app.addMenuList("Ajustes", ajustesMenu, self.menuPress)

		self.app.addLabel("nombre", "Bienvenido " + self.user, 1,0)
		atr = "Usuario: " + user + "\nDirección IP: " + ip + "\nPuerto: " + puerto + "\nVersión: " + version
		self.app.addLabel("atr", atr, 2, 0)
		self.app.setLabelBg("atr", "White")
		users = p.usuarios_decode()

		self.app.addGrid("g1", users, 3, 0, 4, 3)
		self.app.addImage("video", "imgs/webcam.gif", 1, 2, 5, 5)

		# Registramos la función de captura de video
		# Esta misma función también sirve para enviar un vídeo
		self.cap = cv2.VideoCapture(0)
		self.videoThread = threading.Thread(target=self.capturaVideo)	#Inicializamos el thread que envía video
		self.videoThread.daemon = True					#Poniendo este valor en True, el hilo se cerrará al acabar el proceso principal
		self.videoThread.start()

		#Creamos la SubWindow donde se reproducirá el video recibido
		self.app.startSubWindow("El otro")
		self.app.addImage("El otro", "imgs/webcam.gif", 1, 2, 5, 5)
		self.app.setGeometry(640,480)
		self.app.stopSubWindow()
		self.app.hideSubWindow("El otro")


		# Añadir los botones
		self.app.addButtons(["Video","Continua","Pausa","Colgar","Conectar", "Salir"], self.buttonsCallback, 6,1,3,5)
		self.app.hideButton("Colgar")
		self.app.hideButton("Pausa")
		self.app.hideButton("Continua")
		self.app.hideButton("Video")


		# Barra de estado
		self.app.addStatusbar(fields=2)



	def start(self):
		"""
			Función que inicia la aplicación
		"""
		self.app.go()


	def reproduceVideo(self):
		"""
			Función que reproduce el video recibido
			Args:
				  self -> la misma clase

		"""
		self.app.showSubWindow("El otro")		# Establece la subwindow como visible
		inicio = time.time()					# Almacena el tiempo de inicio de la llamada
		while self.UDPcon != None:				# El bucle se mantiene mientras el objeto que gestiona la conexión no sea None
			if len(self.UDPcon.buffer) == 0:	# Si al leer del buffer circular no hay nada, sigue
				continue
			dict = self.UDPcon.buffer.pop(0)	# Extrae el primer frame del buffer y lo reproduce en la SubWindow
			ts = dict['ts']
			img_tk = dict['imagen']

			self.app.setStatusbar("Duración: " + str(time.time()-inicio), 0)		#Imprime en la barra de estado la duración de la llamada
			self.app.openSubWindow("El otro")
			self.app.setImageSize("El otro", 640, 480)
			self.app.setImageData("El otro", img_tk, fmt = 'PhotoImage')
			self.app.stopSubWindow()
			self.app.setStatusbar("Retraso: " + str(time.time()-float(ts.decode())),1) #Imprime en la barra de estado el retraso de la llamada




	def capturaVideo(self):
		"""
			Función que captura y envia el video
			Args:
				  self -> la misma clase

		"""
		paquete = 0			# Inicializa el contador de paquetes

		while self.salir == False:
			# Capturamos un frame de la cámara o del vídeo
			ret, frame = self.cap.read()
			try:
				len(frame)							# Mientras el array frame no sea None, len no devolverá ninguna excepcion
			except TypeError as t:
				self.cap = cv2.VideoCapture(0)		# Cambia el origen del video a la camara
				continue
			frame = cv2.resize(frame, (640,480))
			cv2_im = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
			img_tk = ImageTk.PhotoImage(Image.fromarray(cv2_im))

			# Lo mostramos en el GUI
			self.app.setImageData("video", img_tk, fmt = 'PhotoImage')

			# Si hay conexion establecida comprimimos y enviamos
			if self.UDPcon is not None:
				if self.UDPcon.pausa == False:
					paquete += 1
					encode_param = [cv2.IMWRITE_JPEG_QUALITY, 50]
					result, encimg = cv2.imencode('.jpg', frame, encode_param)
					if result == False:
						print('Error al codificar imagen')
					img = encimg.tobytes()
					data = '{}#{}#{}#{}#'.format(str(paquete), str(time.time()), "640x480", "10")	#Formamos la cabecera
					data = data.encode() + img

					self.UDPcon.enviarVideo(data)	#Enviamos el paquete


	def buttonsCallback(self, button):
		"""
			Función que asocia acciones a los botones
			Args: self -> clase
				  button -> tipo de botón que hemos pulsado
		"""
		if button == "Salir":
			# Salimos de la aplicación
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			PORT = int(self.puerto)
			sock.connect((self.ip, PORT))
			sock.sendall("Salir".encode())								# Enviamos un mensaje a nuestra conexión de control para que salga
			sock.close()
			self.salir = True
			self.app.stop()


		elif button == "Conectar":
			# Entrada del nick del usuario a conectar
			nick = self.app.textBox("Conexión", "Introduce el nick del usuario a buscar")
			#Si el nick es incorrecto, pasa
			if not nick:
				pass
			# Sino, busca su información en el servidor
			else:
				res = p.info_decode(nick)
				# Si hay mensaje de error, el nick es incorrecto
				if res[0] == "N":
					self.app.warningBox("Error","Nick incorrecto")
				# Sino, llama a la función de llamada con el nick propio, y la ip y el puerto del destinatario
				else:
					respuesta = p.llamar(self.user, res[0], int(res[1]))
					# Si se recibe un False, puede ser llamada rechazada o usuario ocupado
					if respuesta[0] == False:
						if respuesta[1] == "DENIED":
							self.app.warningBox("Rechazado", "El usuario rechazó la llamada")
						else:
							self.app.warningBox("Ocupado", "El usuario está ocupado")
					# Sino, es llamada aceptada, se llama a la función que establece la conexión
					else:
						self.llamada(nick,res[0],respuesta[1])

		# Envia a la conexión de control del destinatario el memsaje de final, y cierra la llamada
		elif button == "Colgar":
			res = p.info_decode(self.UDPcon.dest)
			t.enviarTCP("CALL_END " + self.user,False,res[0],int(res[1]))
			self.UDPcon.llamada = False
			time.sleep(2)
			self.UDPcon = None
			self.app.hideButton("Colgar")
			self.app.hideButton("Pausa")
			self.app.hideButton("Video")
			self.app.hideSubWindow("El otro")
			self.app.showWidgetType(3,"Conectar")

		# Establece el parámetro pausa a True, y envia a la conexión de control el mensaje de pausa
		elif button == "Pausa":
			self.UDPcon.pausa = True
			#Eliminamos el timeout para evitar problemas
			self.UDPcon.sock_rcv.settimeout(None)
			res = p.info_decode(self.UDPcon.dest)
			t.enviarTCP("CALL_HOLD " + self.user,False,res[0],int(res[1]))
			self.app.hideButton("Pausa")
			self.app.showWidgetType(3,"Continua")

		# Cambia el valor del parámetro de pausa, e informa a la conexion de control de que la llamada continúa
		elif button == "Continua":
			self.UDPcon.pausa = False
			#Restablece el timeout
			self.UDPcon.sock_rcv.settimeout(10)
			res = p.info_decode(self.UDPcon.dest)
			t.enviarTCP("CALL_RESUME " + self.user,False,res[0],int(res[1]))
			self.app.hideButton("Continua")
			self.app.showWidgetType(3,"Pausa")

		# Abre un cuadro de elección de ficheros en el directorio actual,  y establece el video elegido como el origen de los frames
		elif button == "Video":
			filename = self.app.openBox(title="Directorio", dirName=os.getcwd(), fileTypes=[('video', '*.avi'), ('video', '*.mp4')], asFile=False, parent=None)
			self.cap = cv2.VideoCapture(filename)


	def llamada(self,dest,ip,puerto):
		"""
			Función que establece la llamada
			Args:
				  self -> la misma clase
				  dest -> el nick del destinatario de la llamada
				  ip -> ip de destino de la llamada
				  puerto -> puerto UDP destino de la llamada

		"""
		# Muestra los botones necesarios para colgar, pausar y mandar video
		self.app.showWidgetType(3,"Colgar")
		self.app.showWidgetType(3,"Pausa")
		self.app.showWidgetType(3,"Video")
		self.app.hideButton("Conectar")
		# Inicializa el objeto de conexiones UDP
		self.UDPcon = u.conexionUDP(self.ip,dest,ip,puerto)
		self.UDPcon.llamada = True
		# Crea el hilo que recibe video y lo almacena en el buffer, y el que lo reproduce tras sacarlo del buffer
		buffert = threading.Thread(target=self.UDPcon.recibirVideoBuffer, args=(self,))
		recibet = threading.Thread(target=self.reproduceVideo)
		# Lanza los hilos
		buffert.start()
		time.sleep(2)
		recibet.start()

	def menuPress(self, button):
		"""
			Función que determina las acciones de los botones del menu
			Args:
				  self -> la misma clase
				  button -> botón pulsado

		"""
		# Mostramos el perfil
		# Cerramos la sesión
		if button == "Cerrar Sesión":
			self.app.stop()
			sc = StartClient("316x260")
			sc.start()

		# Cerramos la aplicación
		elif button == "Cerrar":
			self.app.stop()

		# Cambiamos el nombre de usuario
		elif button == "Cambiar Nombre":
			nick = self.app.textBox("Conexión", "Introduce el nick del usuario a buscar")
			if not nick:
				pass

			else:
				self.user = nick
				texto = p.registrar(self.user, self.ip, self.puerto, self.pwd, self.version)
				# Si hay algun error
				if texto[0] == 'N':
					self.app.errorBox("err", "Error de Aplicación")
					# Cambiamos los atributos
				else:
					self.app.setLabel("nombre", "Bienvenido " + self.user)
					atr = "Usuario: " + self.user + "\nDirección IP: " + self.ip + "\nPuerto: " + self.puerto + "\nVersión: " + self.version
					self.app.setLabel("atr", atr)


		# Cambiamos a pantalla completa
		elif button == "Pantalla Completa":
			self.app.hideWidgetType(1, "nombre")
			self.app.hideWidgetType(1, "atr")
			self.app.hideWidgetType(17, "g1")
			self.app.setImageSize("video", 900, 300)

		# Cambiamos a pantalla normal
		elif button == "Pantalla Normal":
			self.app.exitFullscreen()
			self.app.showWidgetType(1, "nombre")
			self.app.showWidgetType(1, "atr")
			self.app.showWidgetType(17, "g1")
			self.app.setImageSize("video", 400, 400)



class RegisterClient(object):
	"""
		Clase que controla la interfaz del registro de usuarios
		Funciones:
				init -> inicia la clase con un tamaño de ventana
				start -> inicia la aplicación
				buttonsCallback -> controla las acciones de cada botón
								   (aceptar, cancelar y registrarse)
	"""

	def __init__(self, window_size):
		"""
			Función que inicia la Clase
			Args:
				  self -> la misma clase
				  window_size -> tamaño que queremos para la ventana

			Returns : la clase incializada
		"""
		# Creamos una variable que contenga el GUI principal
		self.app = gui("VideoIsComing", window_size)
		self.app.setGuiPadding(20,20)
		self.app.setBg("light green")
		self.app.setLabelFont(13, "Times")
		self.app.setButtonFont(12, "Times")

		# Añadimos las entradas
		self.app.addFlashLabel("title", "Bienvenido a VideoIsComing")
		self.app.addLabelEntry("     Usuario:  ")
		self.app.addLabelSecretEntry("Contraseña: ")
		self.app.addLabelSecretEntry("     Repítela: ")
		self.app.addLabelEntry("Dirección IP:")
		self.app.addLabelEntry("      Puerto:    ")
		self.app.setFocus("     Usuario:  ")

		# Añadimos los botones
		self.app.addButtons(["Registrarse", "Cancelar"], self.buttonsCallback)



	def start(self):
		"""
			Función que inicia la aplicación
		"""
		self.app.go()


	# Función que gestiona los callbacks de los botones
	def buttonsCallback(self, button):
		"""
			Función que asocia acciones a los botones
			Args: self -> clase
				  button -> tipo de botón que hemos pulsado (cancelar, registrar)
		"""
		# Salimos de la app
		if button == "Cancelar":
			self.app.stop()

		# Nos registramos en el servidor
		elif button == "Registrarse":
			user = self.app.getEntry("     Usuario:  ")
			pwd = self.app.getEntry("Contraseña: ")
			pwd2 = self.app.getEntry("     Repítela: ")
			ip = self.app.getEntry("Dirección IP:")
			puerto = self.app.getEntry("      Puerto:    ")
			version = "V0"

			# Si no hay texto sale un popup
			if not user or not pwd or not pwd2 or not ip or not puerto:
				self.app.warningBox("sintexto", "Por favor, introduce todos los campos")

			# Si las contraseñas no coinciden
			elif pwd != pwd2:
				self.app.warningBox("password", "Las contraseñas no coinciden")
				self.app.clearEntry("Contraseña:")
				self.app.clearEntry(" Repítela: ")

			# Nos registramos
			else:
				texto = p.registrar(user, ip, puerto, pwd, version)

				# SI hay algun error
				if texto[0] == 'N':
					self.app.warningBox("err", "Ha habido un error, por favor, vuelve a intentarlo")
					self.app.clearAllEntries()
				# Cerramos la pestaña actual e iniciamos la del video
				else:
					self.app.stop()
					vc = VideoClient("900x600", user, pwd, ip, puerto, version)
					vc.start()


class StartClient(object):
	"""
		Clase que controla la interfaz del inicio de sesión
		Funciones:
				init -> inicia la clase con un tamaño de ventana
				start -> inicia la aplicación
				buttonsCallback -> controla las acciones de cada botón
								   (aceptar, cancelar y registrarse)
	"""

	def __init__(self, window_size):
		"""
			Función que inicia la Clase
			Args:
				  self -> la misma clase
				  window_size -> tamaño que queremos para la ventana

			Returns : la clase incializada
		"""
		# Creamos una variable que contenga el GUI principal
		self.app = gui("VideoIsComing", window_size)
		self.app.setGuiPadding(20,20)
		self.app.setBg("light green")

		# Añadimos un titulo
		self.app.addFlashLabel("title", "Bienvenido a VideoIsComing")
		self.app.setLabelFont(13, "Times")
		self.app.setButtonFont(12, "Times")
		#self.app.setLabelBg("title", "light yellow")

		# Añadimos las entradas de usuario y contraseña y los botones
		self.app.addLabelEntry("    Usuario:  ")
		self.app.addLabelSecretEntry("Contraseña:")
		self.app.setFocus("    Usuario:  ")
		self.app.addButtons(["Entrar", "Cancelar"], self.buttonsCallback)

		# Añadimos un botón para registrarnos
		self.app.addLabel("registra", "¿No tienes cuenta?")
		self.app.addButtons(["Regístrate"], self.buttonsCallback)


	def start(self):
		"""
			Función que inicia la aplicación
		"""
		self.app.go()


	# Función que gestiona los callbacks de los botones
	def buttonsCallback(self, button):
		"""
			Función que asocia acciones a los botones
			Args: self -> clase
				  button -> tipo de botón que hemos pulsado (aceptar, cancelar, registrar)
		"""

		# Salimos de la app
		if button == "Cancelar":
			self.app.stop()

		# Inicia Sesión
		elif button == "Entrar":
			user = self.app.getEntry("    Usuario:  ")
			pwd = self.app.getEntry("Contraseña:")

			# Si no hay texto sale un popup
			if not user or not pwd:
				self.app.warningBox("sintexto", "Por favor, introduce tu usuario y contraseña")
			# Sino lo busca en la base de datos
			else:
				texto = p.info_decode(user)

				# Si el usuario no existe sale un popup para registrarse
				if texto[0] == 'N':
					self.app.warningBox("reg", user + " no existe, por favor, regístrate")
					self.app.clearAllEntries()

				# Sino accede al video
				else:
					ip = texto[0]
					puerto = texto[1]
					version = texto[2]
					texto = p.registrar(user, ip, puerto, pwd, version)

					# Si hay algun error
					if texto[0] == 'N':
						self.app.errorBox("err", "Ha introducido mal su contraseña")
						self.app.clearEntry("Contraseña:")
					# Cerramos la pestaña del usuario y abrimos la del video
					else:
						self.app.stop()
						vc = VideoClient("900x600", user, pwd, ip, puerto, version)
						vc.start()

		# Cerramos la pestaña actual y abrimos la de registrarse
		elif button == "Regístrate":
			self.app.stop()
			rc = RegisterClient("326x260")
			rc.start()


if __name__ == '__main__':

	sc = StartClient("316x260")
	sc.start()
