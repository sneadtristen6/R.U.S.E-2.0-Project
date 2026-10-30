# Exportar y compartir

> **Para:** modders · **Necesitas:** RUSE Studio y un mod terminado · **Tiempo:** 5 minutos

## 1. Exportar

1. Abre el menú **Mod** y elige **Exportar mod…**.
2. Rellena la **versión** (tres números, como `1.0.0`), tu nombre y una línea sobre lo que hace el mod.
3. Elige dónde guardarlo. El Studio construye el mod una vez sobre tu juego, para anotar la versión del juego con la que
   se hizo y su **huella** (un código corto que es el mismo para todos los que tienen los mismos mods), y luego guarda
   un solo archivo: `<your-mod>-<version>.rusemod`.

Ese archivo es todo lo que necesita un jugador: lo añade en RUSE Launcher ([[Instalar y jugar|Instalar-y-jugar]]).

**Mods de mapas grandes:** un mapa cambiado por todas partes puede hacer que la construcción tarde minutos en calcularse
(por dónde pueden ir las unidades en el terreno que abriste, por ejemplo). Esa espera la haces una vez. La exportación
pone en el archivo lo que calculó la construcción, así que la primera construcción de un jugador es más corta. Solo
contiene nuestros propios números, nunca un archivo del juego, y está bloqueado con el propio archivo del juego para
ese mapa: solo se abre en un PC que tiene el juego. Por ahora solo el movimiento; aún no visto en el juego.

Cuando termina la exportación, el Studio abre **Comparte tu mod** con el tamaño del archivo, su suma de comprobación
SHA-256 y su entrada para la lista, listos para copiar. Puedes volver a abrirlo cuando quieras desde el menú **Mod**
(**Compartir tu mod…**).

## 2. Compartir: añádelo a los mods compatibles

¿Has hecho un mod? Añádelo a la lista y pasa a ser colaborador. La pestaña **Mods compatibles** de RUSE Launcher muestra
los mods de la lista de [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), y los jugadores los
instalan con un clic (a los jugadores nuevos se les ofrecen la primera vez que inician el launcher):

1. Sube el `.rusemod` (lo más fácil es una GitHub Release: la de tu propio repositorio, o la de la lista).
2. Abre una pull request en [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods) que añada la entrada
   de tu mod a `index.toml`: pega la entrada que muestra Comparte tu mod y pon el enlace del archivo en `download`. El
   tamaño y el SHA-256 deben ser los que mostró la exportación: el launcher rechaza una descarga que no coincide, así
   que nadie puede cambiar tu archivo por otro.
3. O publícalo en [Discussions > Mods & maps](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) con una
   captura de pantalla y lo que cambia (arrastra el `.rusemod` a la publicación), y se añade a la lista por ti.

Un truco o una herramienta de prueba (unidades gratis, construcción instantánea...) recibe la etiqueta `"cheat"`: el
launcher lo muestra en su propio grupo, «Trucos y herramientas de prueba (opcional)», y nunca lo marca ni lo descarga
salvo que lo haga el jugador. Una versión nueva es un archivo nuevo con un número de versión nuevo: un archivo
publicado nunca cambia.

El formato exacto de la entrada:
[MOD_FORMAT.md, sección 15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/docs/MOD_FORMAT.md#15-the-mod-index-supported-mods).

## Editar un mod instalado

En el menú Mod del Studio, **Editar un mod instalado…** lista cada mod que tiene el Launcher (con un cuadro de
búsqueda). El tuyo abre su proyecto. El de otra persona se convierte en una copia tuya con un nombre propio (no puede
llevar el nombre del original): tus cambios van en ella, y una actualización del original nunca los borra. Un mod de
RUSE Mod Manager (`.rmod`) se convierte en su copia, así que sus cambios de valores pasan a ser cambios del Studio que
puedes modificar.

## Qué puede contener un mod

Solo datos: números, textos, mapas, modelos, texturas. Las dos aplicaciones rechazan los programas (`.exe`, `.dll`,
scripts que se ejecutan en un PC). Una excepción: los propios scripts de misión del juego, tal como los guarda el
Studio. Se ejecutan dentro del juego y pueden hacer todo lo que él puede, así que instálalos solo de autores en los que confíes ([SECURITY.md](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/SECURITY.md)).

## Buenas prácticas

- Conserva la carpeta de tu mod: el `.rusemod` es para los jugadores, la carpeta es lo que edita el Studio.
- Di en tu publicación qué otros mods necesita el tuyo o con cuáles choca.
- Da crédito a las personas en cuyo trabajo te basas.

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Export-and-Share]]
