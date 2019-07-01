/**
* demonizar.c
* Librería que contiene las funciones que demonizan el servidor
*
* Lucía Rivas Molina <lucia.rivasmolina@estudiante.uam.es>
* Daniel Santo-Tomás López <daniel.santo-tomas@estudiante.uam.es>
*/
#include "demonio.h"

/**
 * Funcion : demonizar
 * Demoniza un proceso dado
 * INPUT : tipo_servicio -> el tipo de servicio a demonizar
 * OUTPUT : OK/ERROR
 */
int demonizar(char* tipo_servicio){
  pid_t pid;

  /*Creamos un hijo*/
  pid = fork();
  /*En caso de error*/
  if (pid < 0) return ERROR;
  /*Terminamos el proceso padre*/
  if (pid > 0) return OK;

  /* Creamos otro hijo*/
  pid = fork();
  /*En caso de error*/
  if (pid < 0) return ERROR;
  /*Terminamos el proceso hijo anterior*/
  if (pid > 0) return OK;

  /*Cambiamos la máscara*/
  umask(0);
  setlogmask (LOG_UPTO (LOG_INFO));
  openlog (tipo_servicio, LOG_CONS | LOG_PID | LOG_NDELAY, LOG_LOCAL3);
  syslog (LOG_ERR, "Inicializando nuevo servidor.");

  /*Cambiamos el id del hijo*/
  if (setsid() < 0) {
    syslog (LOG_ERR, "Error creando nuevo id del proceso hijo.");
    return ERROR;
  }
  printf("%d\n",getpid());
  /*Cambiamos el directorio a la raíz*/
  if ((chdir("/")) < 0) {
    syslog (LOG_ERR, "Error cambiando el directorio a \"/\"");
    return ERROR;
  }

 syslog (LOG_INFO, "Cerramos los descriptores de fichero");
 close(STDIN_FILENO); close(STDOUT_FILENO); close(STDERR_FILENO);
 return OK;
}
