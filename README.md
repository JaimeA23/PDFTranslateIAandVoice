# PDFTranslateIAandVoice
Aplicación de prueba python, integra un sistema de traducción con IA, y con un sistema de voz.
(es un aplicativo de prueba no se debe usar para ningun entorno productivo)


El aplicativo tiene una interfaz ordinaria y cuenta con las funciones de:

 1-Cargar PDF
 2-Escoger idioma y traducir pdf
 3-cantidad de paginas a ver en el momento (1-5)
 4- sistema de sroll de paginas
 5 -lectura con voz del sistema del texto cargado en el momento
 6- sistema de play-pausa-stop para el audio reproducido

La voz depende del ssistema que se tenga instalado, por ejemplo si tu equipo es un windows con distibuccion en español, la voz no podra reproducir texto en caracteres distintos, como el japones o el chino.

Esta traduccion consume una "API" para poder traducir el texto, usando un promp predeterminado para obtener la traduccion como se necesita, en mi caso use llama 3.1 de 8B a nivel loccal, pero se puede adecuar para consumir otras  incluyendo servicios pagos como deepseek o chatgpt.
Tambien se puede adaptar una version sin IA que use los servicios de Google, para eso recomiendo ver mi otro repositorio.

