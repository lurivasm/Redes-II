/**
* demonizar.h
* Librería que contiene las funciones que demonizan el servidor
*
* Lucía Rivas Molina <lucia.rivasmolina@estudiante.uam.es>
* Daniel Santo-Tomás López <daniel.santo-tomas@estudiante.uam.es>
*/
#define  _GNU_SOURCE
#ifndef DEMONIO_H
#define DEMONIO_H

#include <stdio.h>
#include <syslog.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>

/**
 * Macro OK
 * Devolver OK en las funciones
 */
#define OK 0
/**
 * Macro ERROR
 * Devolver ERROR en las funciones
 */
#define ERROR -1


/**
 * Funcion : demonizar
 * Demoniza un proceso dado
 * INPUT : tipo_servicio -> el tipo de servicio a demonizar
 * OUTPUT : OK/ERROR
 */
int demonizar(char* tipo_servicio);

#endif
