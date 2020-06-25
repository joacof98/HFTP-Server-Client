# Laboratorio 2: Aplicacion servidor (Protocolo HFTP)
### Integrantes: Fracchia Joaquin, Germán John




# Estructura general del servidor

En el archivo *server.py* se encuentra la implementación del servidor, mediante la clase Server. En función main se crea una instancia de la clase y el servidor se va a mantener escuchando a una dirección y puerto. Se van a estar aceptando peticiones constantemente y manejandolas con una instancia de Connection, hasta que termine la conexión y el server notifique esa acción.

En el archivo *connection.py* se encuentra la implementacion del manejador de conexiones del cliente. Constantemente se va a estar recibiendo información del cliente conectado y por cada comando, verifica todos los errores posibles y si no existe ninguno, ejecuta el comando indexando una lista de comandos, pasando parámetros de ser necesario. Cuando el cliente finalize la sesión, se notifica al servidor este cambio.

# Diseño
## Server
La instancia del servidor puede iniciarse con los parametros por default, o agregarse opciones para determinar directorio, dirección y puerto. Las propiedades de la instancia son el socket para servidor y el directorio. Con el socket se pone al servidor a escuchar al puerto y direccion especificadas.
Cuando se llama al método *serve*, un bucle constante acepta peticiones con **accept** y crea la instancia de Connection, pasandole el socket resultante de haber aceptado la sesión y empieza a ejecutar *handle*. En caso de que el objeto de conexión lo dicte (con su propiedad connected) el servidor muestra **connection ended** para notificar el fin de sesion.

## Conexión

### *Propiedades*
En las propiedades de clase por una parte tenemos el **socket de la conexión**, **directorio** a usar para los comandos y el **estado de la conexión**.
Por otro lado, tenemos todos los distintos **mensajes de error** que puede enviar el servidor referentes a sumar robustez. Estan creados en base al archivo *constants.py*, ya incluido.
Y por último, un **diccionario** con todos los comandos posibles, para poder indexarlo y acceder a la función correspondiente de cada uno.

Para enviar mensajes al cliente utilizamos el método *send* que también es usado por la implementación del cliente que vino en el *kickstarter*. Se encarga de agregar siempre el terminador de linea y codificar el mensaje al enviarlo.

### *Recibiendo datos del cliente*
En el método **handle**, recibimos mediante el socket lo que envie el cliente y lo decodificamos a ASCII (tipo de datos para el intercambio de mensajes).
También nos encargamos de manejar errores como por ejemplo, uno interno que pueda tener el servidor en ese momento.
En otro caso, lo que hacemos es obtener los **n-1** comandos a ejecutar usando el método *split*. El último comando lo guardamos, no lo vamos a ejecutar ya que queremos que se concatene con lo que vaya llegando en el proximo recv. Esto se da porque se podria estar mandando un comando incompleto y queremos esperar hasta el fin de linea para ejecutarlo.
Luego, iteramos todos los n-1 comandos listos, y por cada uno checkeamos los errores, y si está libre de ellos se ejecuta, en caso contrario seguimos al próximo.

### *Manejo de errores*
Luego, llamamos al metodo *checkErrors* pasandole el comando en cuestión. Éste se encarga de enviar mensajes de error si el comando presenta distintos errores, ya sea de cantidad argumentos, no existe archivo, comando inválido, etc. devolviendo un **booleano**. Lo que nos facilitó esta parte fue crear un arreglo para el comando, donde cada elemento es un argumento, lo que permite obtener la cantidad que tenemos, tipo de un sólo argumento específico, etc.
Los métodos *checkSlice, checkMetadata* están aislados, pero son una extension del anterior. Uno se encarga de manejar sólo el comando **get_slice** debido a los muchos errores que puede generar como por ejemplo si existe archivo, si no pasamos numeros enteros positivos o si el offset supera el tamaño del archivo. Metadata solo se encarga de ver que exista el archivo.

### *Ejecución de comandos*
Luego de haber asegurado que todos los parámetros están bien, podemos ejecutar con seguridad los comandos.
Para *get_file_listing* usamos la libreria *os* (como tambien la usamos en otros comandos que la requieren), que nos permite ver si existe el directorio a listar de la instancia, y decidir crear uno nuevo en caso de que no exista. Luego manda el mensaje Ok, y para cada archivo enviamos el nombre.
En *quit* simplemente avisamos que recibimos el comando, cambiamos el estado de conexión (que el server va a obtener, y que tambien no permite que sigamos recibiendo data) y cerramos el socket.
En *get_metadata* también usamos *os* para obtener el archivo del directorio y su tamaño, y finalmente enviamos confirmación y el numero entero para el tamaño.
Y para el último *get_slice*, obtenemos por separado cada argumento,  abrimos el archivo para leer (soportando cualquier tipo) y nos paramos donde indique offset. A partir de ahi leemos hasta size, codificamos a base64. Al final decodificamos a ASCII para poder enviar los datos, y enviamos el Ok junto con la cadena o fragmento del archivo.

# Dificultades
La primer dificultad fue pensar como implementar la detección para cada comando, pero luego de la recomendación de un profe (ejecutarlos indexando un diccionario) optamos que era la más viable.

Otra fue en lo referido a la robustez. Considerar cada caso de pasaje de argumentos fue dificil, y costaba identificar cuándo era necesario manejar parámetros de sobra o no. Gracias a crear un arreglo donde cada elemento fuera un argumento, pudimos abarcar mejor el problema.

La dificultad que más tiempo nos consumió fue el hecho de que la conexión pueda manejar múltiples comandos. Intentamos muchas veces hacer *split* y simplemente mandar un comando a ejecutar y otros a esperar, pero entraban conflictos con otros tests y tuvimos que redefinir algunos manejos de errores. La complicación fue entender que teníamos que ir ejecutando los n-1 comandos y esperar al último. Antes de poder llegar a esa implementación probamos una forma más ineficiente (esperar a que llegue todo antes de dividir y ejecutar) que generaba conflictos, pero anduvo.
Finalmente pudimos cambiar nuevamente a la idea original, y logramos implementarla.


# Preguntas

1. ¿Qué estrategias existen para poder implementar este mismo servidor pero con capacidad de atender múltiples clientes simultáneamente? Investigue y responda brevemente qué cambios serían necesario en el diseño del código.

2. Pruebe ejecutar el servidor en una máquina del laboratorio, mientras utiliza el cliente desde otra, hacia la ip de la máquina servidor. ¿Qué diferencia hay si se corre el servidor desde la IP “localhost”, “127.0.0.1” o la ip “0.0.0.0”?

1) Una forma de implementar el mismo servidor pero con capacidad de atender multiples clientes simultàneamente, es usando Multi-threaded. Agregando el modulo _thread en el server, y creando una clase de hilo principal que vaya creando hilos nuevos cada vez que se conecta un cliente. Tambien agregarle cuantas cantidad de peticiones que puede realizar en cola con socket.listen() 

2) No pudimos probar de ejecutar el servidor en una maquina del laboratorio, mientras utiliza el cliente desde otra. 
