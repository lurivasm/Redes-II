import tcp as t
import udp as u


def registrar(nick, ip_address, port, password, protocol):
    """
     Función que registra un usuario en el servidor

     Args : nick -> nombre del usuario
             ip_address -> dirección ip del usuario
             password -> contraseña del usuario
             protocol -> protocolo del servidor utilizado

     Returns : mensaje a imprimir
    """

    # Enviamos el mensaje y decodificamos la respuesta
    mensaje = "REGISTER " + nick + " " + ip_address + " " + port + " " + password + " " + protocol
    recv = t.enviarTCP(mensaje)
    respuesta = recv.decode().split(" ")

    # Si la respuesta es OK devolvemos un mensaje completo
    if respuesta[0] == "OK":
        res = "Usuario: " + respuesta[2] + "\nts: " + respuesta[3]
        return res
    # Sino devolvemos el mensaje de error
    else:
        return recv.decode()


def info(name):
    """
      Función que devuelve la ip y puerto de un usuario a través de su nick

      Args : name -> nombre del usuario
      Returns : ip y puerto del usuario
    """
    # Enviamos el mensaje y decodificamos la respuesta
    mensaje = "QUERY " + name
    recv = t.enviarTCP(mensaje)
    respuesta = recv.decode().split(" ")

    # Si la respuesta es OK devolvemos el mensaje completo
    if respuesta[0] == "OK":
        prot = respuesta[5].split("#")
        res = "Usuario: " + respuesta[2] + "\nDirección IP: " + respuesta[3] + "\nPuerto: " + respuesta[4] + "\nProtocolos: "
        for i in range(0,len(prot)):
            res = res + prot[i] + " "
        return res
    # Sino devolvemos un mensaje de error
    else:
        return recv.decode()

def info_decode(name):
    """
        Función que devuelve la ip, puerto y protocolo por separado
        Args: name -> nombre del usuario
        Returns: NOK -> en caso de que no exista el usuario
                 ip -> direccion ip del usuario
                 puerto -> puerto del usuario
                 protocolo -> versiones que soporta
    """
    texto = info(name)

    # En caso de que el texto sea NOK
    if texto[0] == 'N':
        return texto
    # Sino devuelve la Ip, el puerto y un array de versiones
    else:
        texto = texto.split()
        ip = texto[4]
        puerto = texto[6]
        versiones = texto[8:]

        version = versiones[0]
        for i in range(1, len(versiones)):
            version = version + "#" + versiones[i]

        return ip, puerto, version

def usuarios():
    """
      Función que devuelve la lista de usuarios
      Args : void
      Returns : lista de usuarios a imprimir
    """
    # Enviamos el mensaje y decodificamos la respuesta
    mensaje = "LIST_USERS"
    recv = t.enviarTCP(mensaje,True)

    # Si la respuesta es OK devolvemos la lista de usuarios
    if recv.decode()[0] == "O":
        # La dividimos por '#'
        respuesta = recv.decode().split("#")
        pr = respuesta[0].split(" ")
        res = pr[3] + " " + pr[4] + " " + pr[5] + " " + pr[6] + "\n"
        for i in range(1,len(respuesta)-1):
            res = res + respuesta[i] + "\n"
        return res
    # Sino devolvemos un mensaje de error
    else:
        return recv.decode()


def usuarios_decode():
    """
      Función que devuelve la lista de usuarios por tuplas
      Args : void
      Returns : lista de usuarios a imprimir por tuplas
    """
    # Enviamos el mensaje y decodificamos la respuesta
    mensaje = "LIST_USERS"
    recv = t.enviarTCP(mensaje,True)
    # Si la respuesta es OK devolvemos la lista de usuarios
    if recv.decode()[0] == "O":
        # La dividimos por '#'
        respuesta = recv.decode().split("#")
        pr = respuesta[0].split(" ")
        res0 = [pr[3], pr[4], pr[5]]
        res = [pr.split()[:3] for pr in respuesta[1:-1]]
        res = [res0] + res
        res = [["Usuario", "Dirección IP", "Puerto"]] + res
        return res
    # Sino devolvemos un mensaje de error
    else:
        return recv.decode()


def salir():
    """
      Función que sale del programa
      Args : void
      Returns : mensaje a imprimir para salir
    """
    # Enviamos el mensaje y devolvemos la respuesta
    mensaje = "QUIT"
    recv = t.enviarTCP(mensaje)
    return recv




def llamar(nick, ip, puerto):
    """
      Función que establece la llamada
      Args : nick -> nick del usuario que llama
             ip -> ip de usuario a llamar
             puerto -> puerto TCP del usuario a llamar
      Returns : respuesta de la conexión de control
    """
    # Enviamos el mensaje a la conexión de control del otrp usuario
    recv = t.enviarTCP("CALLING " + nick + " " + str(u.UDP_PORT),False, ip, puerto)
    mensaje = recv.decode().split(" ")
    # Si acepta la llamada, devolvemos su nick y su puerto UDP
    if mensaje[0] == "CALL_ACCEPTED":
        return mensaje[1], mensaje[2]
        # Si deniega la llamada enviamos False y DENIED
    elif mensaje[0] == "CALL_DENIED":
        return False, "DENIED"
    # Si está ocupado, enviamos False y BUSY
    else:
        return False, "BUSY"
