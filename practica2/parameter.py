"""
    Librería parameter.py
    Contiene las funciones que capturan los parámetros de entrada, y realiza las
    acciones que correspondan

    Lucía Rivas Molina <lucia.rivasmolina@estudiante.uam.es>
    Daniel Santo-Tomás López <daniel.santo-tomas@estudiante.uam.es>
"""


import requests
import sys
import argparse
import json
import os
import encriptar as e
from Crypto.PublicKey import RSA


def define_parametros():
    """
        Función que define los posibles parámetros de entrada

        Returns: Un objeto de tipo ArgumentParser

    """
    parser = argparse.ArgumentParser(description='%(prog)s SecureBox')

    parser.add_argument('--create_id', help='Crea un nuevo id', nargs=2,
                                       metavar=('Nombre', 'Email'))

    parser.add_argument('--search_id', help='Busca el id argumento', metavar='Nombre/Email')
    parser.add_argument('--delete_id', help='Borra la identidad del id argumento',
                                       metavar='ID')

    parser.add_argument('--upload', help='Envia un fichero al id especificado en --dest_id',
                                    metavar='fichero')

    parser.add_argument('--source_id', help='ID del emisor del fichero',
                                       metavar='ID_emisor')

    parser.add_argument('--dest_id', help='ID del receptor del fichero',
                                     metavar='ID_receptor')

    parser.add_argument('--list_files',action='store_true',help='Lista todos los ficheros del usuario')

    parser.add_argument('--download', help='Recupera un fichero con id ID_fichero',
                                      metavar='ID_fichero')

    parser.add_argument('--delete_file', help='Borra el fichero ID_fichero del sistema',
                                         metavar='Id_fichero')

    parser.add_argument('--encrypt', help='Cifra un fichero descifrado por --dest_id',
                                     metavar='fichero')

    parser.add_argument('--sign', help='Firma un fichero', metavar='fichero')
    parser.add_argument('--enc_sign', help='Cifra y firma un fichero', metavar='fichero')

    return parser


def lee_parametros(parser):
    """
        Función que lee los parámetros introducidos y actúa en cosecuencia

        Args: parser -> Objeto del tipo ArgumentParser con la información de los posibles argumentos de entrada

    """
    args = parser.parse_args()
    token = 'FEcCDf2B670a53dA'


    if args.create_id:
        """
        Genera un par de claves RSA , almacenando la privada en el directorio, y despúes crea el usuario con
        la información suministrada y la clave pública generada
        """
        url = 'http://vega.ii.uam.es:8080/api/users/register'
        key = RSA.generate(2048)
        key_priv = key.exportKey()
        key_pub = key.publickey().exportKey().decode("utf-8")
        file = 'privado'
        with open(file, 'wb') as f:
            f.write(key_priv)


        argum = { 'nombre': args.create_id[0], 'email' : args.create_id[1], 'publicKey' : key_pub }


        r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})

        print("Generando par de claves RSA de 2048 bits...OK")
        url = 'http://vega.ii.uam.es:8080/api/users/search'
        argum = { 'data_search' : args.create_id[1]}
        r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})

        print("Identidad con ID#" + r.json()[0]['userID'] +  " creada correctamente")


    if args.search_id:
        """
        Busca el usuario según los datos dados, imprimiendo todos los que coinciden con lo pedido
        """
        url = 'http://vega.ii.uam.es:8080/api/users/search'
        argum = { 'data_search' : args.search_id}
        r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})

        print("Buscando usuario " + args.search_id + " en el servidor...OK")
        if(len(r.json()) == 0):
            print("Usuario no encontrado")
        else:
            print(str(len(r.json())) + " usuarios encontrados : ")
            for i in range(0,len(r.json())) :
                print("[" + str(i+1) + "] " + r.json()[i]['nombre'] + ", " + r.json()[i]['email'] + ", ID: " + r.json()[i]['userID'])


    elif args.delete_id:
        """
        Asumiendo que solo se elimina el usuario propio, borra el usuario cuyo id se le pasa, además
        del fichero con la clave privada
        """
        url = 'http://vega.ii.uam.es:8080/api/users/delete'
        argum = { 'userID': args.delete_id }
        os.remove("privado")

        r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})
        print("Solicitando borrado de la identidad " + args.delete_id +  "...OK")
        print("Identidad con ID#" + args.delete_id + " borrada correctamente")


    elif args.encrypt:
        """
        Encripta el archivo sin firmar, usando la clave pública del usuario pasado como argumemto(ID)
        """
        if args.dest_id:
            url = 'http://vega.ii.uam.es:8080/api/users/getPublicKey'
            argum = { 'userID': args.dest_id }
            r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})

            if r.status_code == 401:
                print("Id incorrecto")

            clave_publica = e.RSA.importKey(r.json()['publicKey'])
            e.cifrar(args.encrypt,clave_publica)
            print("Fichero cifrado, guardado como 'Encriptado'")
        else :
            print("Falta el ID del destinatario")


    elif args.sign :
        """
        Genera la firma del archivo pasado
        """
        e.firmar(args.sign)
        print("Fichero firmado, guardado como 'Firma'")


    elif args.enc_sign :
        """
        Firma y encripta el archivo, usando la clave pública del usuario pasado como argumento(ID)
        """
        if args.dest_id:
            url = 'http://vega.ii.uam.es:8080/api/users/getPublicKey'
            argum = { 'userID': args.dest_id }
            r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})

            if r.status_code == 401:
                print("Id incorrecto")

            clave_publica = e.RSA.importKey(r.json()['publicKey'])

            e.firmar(args.enc_sign)
            print("Fichero firmado, guardado como 'Firma'")

            e.cifrar('Firma',clave_publica)
            print("Fichero cifrado y firmado, guardado como 'Encriptado'")
        else :
            print("Falta el ID del destinatario")


    elif args.upload :
        """
        Sube un fichero cifrado y firmado para un destinatario indicado por dest_id
        """
        if args.dest_id:
            print("Solicitado envio de fichero a SecureBox")
            url = 'http://vega.ii.uam.es:8080/api/users/getPublicKey'
            argum = { 'userID': args.dest_id }
            r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})
            print(" Recuperando clave pública de ID "+ args.dest_id + "...")
            if r.status_code == 401:
                print("Id incorrecto")
                return

            clave_publica = e.RSA.importKey(r.json()['publicKey'])

            e.firmar(args.upload)
            print("Firmando fichero...OK")

            e.cifrar('Firma',clave_publica)
            print("Cifrando fichero...OK")

            url = 'http://vega.ii.uam.es:8080/api/files/upload'
            files = {'ufile': (args.upload, open('Encriptado', 'rb'))}

            r = requests.post(url, files=files, headers={'Authorization' : 'Bearer ' + token})
            print("Subiendo fichero a servidor...")

            if r.status_code == 401 :
                print("Cuota máxima de almacenamiento de ficheros superada (20)")
                return
            elif r.status_code == 403 :
                print("Se ha supera el tamaño máximo permitido en la subida de un fichero (50Kb)")
                return

            print("Subida realizada correctamente, ID del fichero: " + r.json()['file_id'])
            os.remove('Firma')

            os.remove('Encriptado')

        else:
            print("Falta el ID del destinatario")

    elif args.list_files:
        """
        Imprime la lista de ficheros de un usuario
        """
        url = 'http://vega.ii.uam.es:8080/api/files/list'
        r = requests.post(url, headers={'Authorization' : 'Bearer ' + token})


        len = int(r.json()['num_files'])

        if len == 0 :
            print("No hay ficheros")
        else:
            for i in range(0,len) :
                print("[" + str(i+1) + "] " + r.json()['files_list'][i]['fileName'] + " " + r.json()['files_list'][i]['fileID'])


    elif args.delete_file:
        """
        Borra un fichero
        """
        url = 'http://vega.ii.uam.es:8080/api/files/delete'
        argum = { 'file_id': args.delete_file }
        r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})

        if r.status_code == 401 :
            print("El fichero no existe")
            return
        print("Fichero con ID "+ args.delete_file + " borrado")


    elif args.download :
        """
        Descarga un fichero y lo desencripta. El emisor se indica con source_id
        """
        if args.source_id :
            url = 'http://vega.ii.uam.es:8080/api/files/download'
            argum = { 'file_id': args.download }
            r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})
            print("Descargando fichero de SecureBox...")
            if r.status_code == 401 :
                print("El fichero no existe")
                return
            print("Fichero descargado")
            with open('Descarga', 'wb') as d:
                d.write(r.content)

            url = 'http://vega.ii.uam.es:8080/api/users/getPublicKey'
            argum = { 'userID': args.source_id }
            r = requests.post(url, json=argum, headers={'Authorization' : 'Bearer ' + token})
            print(" Recuperando clave pública de ID "+ args.source_id + "...")

            if r.status_code == 401:
                print("Id incorrecto")
                return

            clave_publica = e.RSA.importKey(r.json()['publicKey'])
            val = e.desencriptar('Descarga', clave_publica)
            print("Descifrando fichero y comprobando firma")

            if val == False:
                print("Firma inválida")
                return

            os.remove('Descarga')
            os.rename('Desencriptado', 'Descarga')

            print("Fichero  descargado, guardado como 'Descarga' ")


        else:
            print("Falta el ID de origen")
    else:
        parser.print_help(sys.stderr)


    return
