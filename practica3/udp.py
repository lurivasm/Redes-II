import socket
import cv2
import numpy
from sortedcontainers import SortedList
from PIL import Image, ImageTk
import tcp as t
import peticiones as p

UDP_PORT = 9000

class conexionUDP(object):
		"""
			Clase que controla la conexión UDP de video
			Funciones:
					init -> inicia la clase
					enviarVideo -> envia datos por el socket
					recibirVideoBuffer -> recibe video y lo almacena en el buffer circular

		"""

		def __init__(self, ip,dest,ip_dest, puerto_dest):
			"""
				Función que inicia la Clase
				Args:
					 self -> la misma clase
					 ip -> ip del usuario
					 dest -> nick del destinatario de la  conexión
					 ip_dest -> ip del destinatario
					 puerto_dest -> puerto UDP del destinatario

				Returns : la clase incializada
			"""
			self.ip = ip
			self.dest = dest
			self.puerto = UDP_PORT
			self.ip_dest = ip_dest
			self.puerto_dest = puerto_dest
			self.pausa = False
			self.llamada = False
			#Crea el buffer circular
			self.buffer = SortedList(key=lambda x: x['indice'])

			# Crea lo sockets de envío y recepción
			self.sock_rcv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.sock_rcv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.sock_rcv.settimeout(10)
			self.sock_rcv.bind((self.ip, self.puerto))

			self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			self.sock_send.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


		def enviarVideo(self, frame):
			"""
				Función que envia datos por el socket de envio
				Args:
					 self -> la misma clase
					 frame -> datos a enviar
			"""
			self.sock_send.sendto(frame, (self.ip_dest, int(self.puerto_dest)))

		def recibirVideoBuffer(self,vc):
			"""
				Función que recibe video y lo almacena en el buffer
				Args:
					self -> la misma clase
					vc -> interfaz gráfica de la aplicación

			"""
			while 1:
				#Recibe datos. Si pasa el timeout sin estar en llamada, sale del hilo. Sino, mensaje de error y sale
				try:
					data, addr = self.sock_rcv.recvfrom(65535)
				except socket.timeout as e:
					if self.llamada == False:
						break
					else:
						vc.app.warningBox("Timeout","Conexion perdida")
						res = p.info_decode(vc.UDPcon.dest)
						t.enviarTCP("CALL_END " + vc.user,False,res[0],int(res[1]))
						vc.app.hideButton("Colgar")
						vc.app.hideButton("Pausa")
						vc.app.hideSubWindow("El otro")
						vc.UDPcon = None
				#Si ha recibido datos, decodifica la cabecera y parsea la imagen
				if data:
					request = data.split(b"#")
					indice = request[0]
					ts = request[1]
					res = request[2]
					fps = request[3]

					imagen = b'#'.join(request[4:])
					imagen = numpy.fromstring(imagen,dtype='uint8')
					imagen = cv2.imdecode(imagen,1)
					cv2_im = cv2.cvtColor(imagen,cv2.COLOR_BGR2RGB)
					img_tk =ImageTk.PhotoImage(Image.fromarray(cv2_im))

					#Genera un diccionario y lo mete en el buffer
					dict = {'indice':indice, 'ts':ts, 'res':res, 'fps':fps, 'imagen':img_tk}
					self.buffer.add(dict)
