"""
    Librería encriptar.py
    Contiene las funciones para encriptar, firmar, comprobar firmas y desencriptar

    Lucía Rivas Molina <lucia.rivasmolina@estudiante.uam.es>
    Daniel Santo-Tomás López <daniel.santo-tomas@estudiante.uam.es>
"""
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Util.Padding import pad, unpad
from Crypto import Random
import os




def hash_code(fichero):
"""
    Función que genera el hash code de un fichero

    Args: fichero -> Fichero del que se quiere generar el hash code

    Returns: El hash code en SHA256 del fichero

"""
    hash_object = SHA256.new()
    with open(fichero, 'rb') as f:
         hash_object.update(f.read())

    return hash_object


def firmar(fichero):
    """
        Función que firma un fichero

        Args: fichero -> Fichero del que se quiere firmar

        Returns: No devuelve nada, pero queda guardado en el directorio el fichero
                 firmado, es decir, la firma concatenada con el fichero original

    """
    hash = hash_code(fichero)
    key = RSA.importKey(open('privado').read())
    signature = PKCS1_v1_5.new(key).sign(hash)
    with open('Firma','wb') as f:
        f.write(signature)
        f.write(open(fichero,'rb').read())

    return


def cifrar(firmado, key_dest):
"""
    Función que cifra un fichero, haciendo uso de la clave pública pasada como argumento

    Args: firmado -> Archivo a cifrar, puede ser un fichero firmado o sin firmar
          key_dest -> Clave pública del destinatario, necesaria para el cifrado

    Returns: Devuelve el nombre del fichero encriptado, el cual queda guardado en el directorio

"""
    key = os.urandom(32)                            # Generamos una clave simétrica de 256 bits
    resultado = 'Encriptado'
    cipher = PKCS1_OAEP.new(key_dest)               # Generamos el cifrador para la clave simétrica a raiz de la clave pública del destinatario
    key_hash = SHA256.new(key)                      # Obtenemos el hash de la clave simétrica
    key_encrypted = cipher.encrypt(key_hash.digest())   # Encriptamos el hash de la clave simétrica
    iv = Random.new().read(AES.block_size)          # Generamos el vector de inicialización
    aes = AES.new(key_hash.digest(), AES.MODE_CBC, iv)       # Creamos el cifrador AES

    with open(resultado,'wb') as f:
        f.write(iv)                                 # Escribimos primero el vector de inicialización
        f.write(key_encrypted)                      # Concatenamos con la clave simétrica encriptada
        with open(firmado, 'rb') as firma:
            buf = firma.read(1024)              # Vamos leyendo de 1024 en 1024 el fichero con el mensaje
            tam = len(buf)                      # y la firma , y lo encriptamos con AES para después
            while len(buf) != 0 :
                if (tam % 16) != 0 :
                    break
                f.write(aes.encrypt(buf))
                buf = firma.read(1024)
                tam += len(buf)

            if (tam % 16) != 0 :
                buf = pad(buf,16)
                f.write(aes.encrypt(buf))

    return resultado



def comprobar_firma(firma, mensaje, key_pub_emisor):
"""
    Función que verifica la firma de un fichero

    Args: firma -> firma del fichero
          mensaje -> mensaje original (el fichero como tal)
          key_pub_emisor -> clave pública del emisor del fichero

    Returns: True si la firma corresponde al mensaje, False en otro caso

"""
    ver = PKCS1_v1_5.new(key_pub_emisor)
    hash = SHA256.new()
    hash.update(mensaje)

    return ver.verify(hash, firma)


def desencriptar(f, key_pub_emisor):
"""
    Función que desencripta un fichero

    Args: f -> fichero encriptado, a desencriptar
          key_pub_emisor -> clave pública del emisor del fichero

    Returns: True si se ha desencriptado y la firma es correcta, en cuyo caso además se guarda
             el fichero desencriptado en el directorio, False en cualquier otro caso

"""
    key_private = RSA.importKey(open('privado').read())             # Obtenemos nuestra clave privada
    cipher = PKCS1_OAEP.new(key_private)                            # Creamos el cifrador para desencriptar

    with open(f, 'rb') as descarga:
        iv = descarga.read(16)                            # Leemos el vector de inicialización
        key_encrypted = descarga.read(256)                # Leemos la clave simétrica encriptada
        bloque_encriptado = descarga.read()               # Leemos el conjunto de firma +  mensaje encriptados
        key_hash = cipher.decrypt(key_encrypted)          # Desencriptamos el hash de la clave simétrica
        aes = AES.new(key_hash, AES.MODE_CBC, iv)         # Con esa clave i el iv, creamos otro cifrador

        bloque = aes.decrypt(bloque_encriptado)           # Desencriptamos el bloque de firma + mensaje

        bloque = unpad(bloque,16)                         # Deshacemos el posible pad que pueda tener el bloque
        firma = bloque[0:256]                             # Obtenemos la firma y el mensaje
        mensaje = bloque[256:]


    val = comprobar_firma(firma,mensaje,key_pub_emisor)   # Comprobamos la firma
    if val == True:                                       # Si es correcta, se guarda el fichero desencriptado
        with open('Desencriptado','wb') as d:
            d.write(mensaje)
        return val
    else :
        return val
