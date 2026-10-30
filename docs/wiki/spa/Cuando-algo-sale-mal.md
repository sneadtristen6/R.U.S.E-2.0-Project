# Cuando algo sale mal

Busca lo que ves y sigue el arreglo.

## Prueba primero Solucionar problemas

**Solucionar problemas** comprueba de una vez lo que puede impedir una prueba o **Jugar**: si se encuentra el juego,
si Steam está abierto, si R.U.S.E. sigue abierto desde una copia con mods, la unidad y su espacio libre, copias
sobrantes, archivos de solo lectura, y si la aplicación puede escribir donde van las copias. Cada problema que puede
arreglar tiene un botón; los demás dicen qué hacer.

- En RUSE Studio: junto a **Probar en el juego**, y en **Ajustes > Ayuda**. En RUSE Launcher: la barra de abajo, y en
  cada mensaje de problema (Studio 0.8.0, Launcher 0.3.0).
- **Copiar informe** da un texto para pegar en un [[informe de error|Informar-de-un-error]] (tu nombre de usuario de Windows
  queda fuera).

## El propio juego parece cambiado (por otro gestor de mods o por un cambio a mano)

**Ajustes > Copia de seguridad limpia del juego** guarda una copia limpia de los archivos del juego, los comprueba con
ella y devuelve lo que cambió. Los archivos que no son del juego se apartan, nunca se borran. O **Verificar con Steam**
deja que Steam repare el juego. Es el único sitio en el que las aplicaciones escriben en la carpeta de tu juego, y
solo cuando lo pides.

## Una barra roja bajo la cabecera del Studio

Es la **comprobación del mod**. El Studio lee cada archivo de tu mod como lo hará la construcción del juego, cuando
eliges el mod y otra vez antes de **Probar en el juego**. Cada problema se dice con palabras sencillas (qué va mal, en
qué mapa, qué hacer), con un botón que lo arregla donde se puede: rellenar un valor que falta, quitar el elemento o el
ajuste concreto que está mal, o apartar el archivo. El archivo tal como estaba se guarda a su lado. **Detalles** muestra
las palabras de la propia construcción, útiles para pedir ayuda.

- **Apartar** (junto a un archivo de mapa roto) le cambia el nombre a `<name>.broken.toml` junto al original: no se
  pierde nada, el mod funciona sin él y ese mapa empieza limpio.
- Un problema en `mod.toml` o en los cambios de unidades no tiene Apartar: abre el archivo y arregla la línea que nombra
  la barra, o pregunta en
  [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

> [!NOTE]
> Caso conocido: RUSE Studio 0.7.0 y anteriores guardaban los trazos de **Agua** sin su nivel de agua ("the water brush
> needs level"). La 0.7.1 lo arregla; **Apartar** limpia un archivo antiguo.

## La aplicación tarda mucho en abrirse

- **El primer arranque tras instalar**, con «Conservar una copia limpia de los archivos de mi juego» marcada, hace esa
  copia (toda la carpeta del juego, unos 5,3 GB): Ajustes muestra cuánto le falta, y mientras tanto se puede usar la
  aplicación.
- **El índice del juego de RUSE Studio** se crea una vez por cada versión del juego, y otra vez cuando una actualización
  del Studio lo cambia (un minuto aprox.; el Studio pregunta antes). Mientras tanto se pueden usar la pestaña Mapas y
  Ajustes, y la línea de abajo dice cuándo está listo.
- Cualquier otra cosa: abre **Solucionar problemas** y **Copiar informe**. El informe lista cuánto tardó cada paso de
  los últimos arranques de la aplicación, en segundos: pégalo en un [[informe de error|Informar-de-un-error]]. Las mismas
  líneas se guardan en
  `%LOCALAPPDATA%\RUSE Mod Platform\logs\studio-start.log` (las del Launcher: `launcher-start.log`).

## «Windows protegió su PC»

Las aplicaciones son nuevas para la comprobación de reputación de Windows. Haz clic en **Más información** y luego en
**Ejecutar de todas formas**.

## "certificate verify failed: unable to get local issuer certificate" (o "unable to get issuer certificate")

No se descarga ningún mod, o no se descarga la actualización. Windows aún no había obtenido el certificado con el que
se comprueba GitHub; desde el Launcher 0.4.8.4 y el Studio 0.9.8.4, las aplicaciones se lo piden a Windows y lo
intentan otra vez. Desde el Launcher 0.4.8.9 y el Studio 0.9.8.9 también lo intentan con la lista de certificados que
usa Firefox, que llevan consigo, para un PC cuyo Windows no puede obtenerlo (con sus actualizaciones de certificados
desactivadas o bloqueadas: "unable to get issuer certificate", o «el PC no confía en el certificado de seguridad del
sitio»). Con una aplicación más antigua, la actualización tampoco se puede descargar: consigue el instalador en las
[versiones](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases) con tu navegador y ejecútalo (se instala
sobre el antiguo, como hace la actualización). Un mod siempre se puede descargar con tu navegador desde las
[versiones](https://github.com/sneadtristen6/Ruse-Mods/releases) de la lista de mods y añadirse con **Añadir un archivo de mod…** en el Launcher. Si una
aplicación nueva sigue diciéndolo: puede deberse a un antivirus que analiza las conexiones seguras (HTTPS), a una red
de un centro de estudios o de trabajo, o a una fecha equivocada en el PC; cuéntanoslo en
[Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## "[WinError 5] Access is denied" al probar o al jugar

Windows se negó a quitar una copia del juego que hizo la aplicación (en `RUSE-Instances`). También: «Una copia con mods
antigua en `...\RUSE-Instances\<name>.old` no se puede quitar», en cada segundo **Probar en el juego** o **Jugar**.

- **Actualiza primero** (las aplicaciones lo ofrecen al abrirse): desde RUSE Studio 0.7.6 y el Launcher 0.2.11, una
  copia que Windows no quiere borrar nunca detiene una prueba: se mueve a `RUSE-Instances\.trash` y se quita de ahí en
  cuanto nada la retiene.
- **¿R.U.S.E. sigue abierto desde una prueba anterior?** La aplicación lo dice, con el nombre del programa: cierra el
  juego (busca `RUSE.exe` en la pestaña Detalles del Administrador de tareas) y vuelve a intentarlo. **Solucionar
  problemas** encuentra un juego que sigue abierto desde una copia y las copias sobrantes, y los quita por ti.
- **Con una versión más antigua:** borra la carpeta que nombra el mensaje (`...\RUSE-Instances\<name>.partial` o `.old`;
  Windows pregunta por los archivos de solo lectura: di que sí; solo se va la copia, nunca el juego) y vuelve a
  intentarlo. Si Windows se niega, reinicia Windows primero.
- ¿Sigue ahí? [[Infórmalo|Informar-de-un-error]] con el mensaje completo.

## La aplicación no encuentra R.U.S.E.

**Ajustes > Carpeta del juego > Elegir carpeta...** y elige la carpeta que contiene `RUSE.exe` (en Steam:
`steamapps\common\R.U.S.E`).

## «No hemos podido confirmar esta copia de R.U.S.E.»

R.U.S.E. 2.0 funciona solo con una copia del juego que tengas. Hasta que la carpeta del juego esté confirmada,
**Jugar** y **Probar en el juego** siguen desactivados, y este cuadro dice por qué: Steam no tiene registro de R.U.S.E.
instalado en esa carpeta; el propio archivo de Steam que hay en ella (`steam_api64.dll`) falta, ha cambiado o no es de
Valve; o la carpeta tiene archivos que hacen funcionar el juego sin Steam (los nombra).

- **Lo tienes en Steam:** haz clic en **Comprobar mis archivos en Steam** (Steam vuelve a poner cualquiera de sus
  archivos que falte o haya cambiado), quita los archivos que nombre el cuadro y luego haz clic en **Comprobar de
  nuevo**. Una carpeta del juego que elegiste a mano debe ser la que instaló Steam.
- **Lo tienes de otra forma** (una copia en caja de antes de que R.U.S.E. estuviera en Steam), **o crees que la
  comprobación se equivocó:** el cuadro muestra **Tu código** (hecho a partir de este PC y de la carpeta del juego).
  Haz clic en **Copiar**, luego en **Abrir un ticket en Discord** o **Abrir un ticket en GitHub**, y pégalo. Te
  enviamos un código de desbloqueo: pégalo bajo **Código de desbloqueo** y haz clic en **Desbloquear**. Confirma esa
  copia en ese PC.

La comprobación es la misma en Windows, Linux y Steam Deck. Este proyecto nunca ayuda a nadie a jugar a R.U.S.E. sin
tenerlo: no se reparten archivos del juego ni se ejecuta sin Steam.

## «En un formato de mod más antiguo» o «lo guardó un RUSE Studio más nuevo»

- **Un formato de mod más antiguo:** el mod se hizo con un Studio más antiguo. **Actualizar este mod** reescribe sus
  archivos como los lee este Studio, conservando lo que significan; antes, un zip de todo el mod va a la carpeta
  `mod-backups` del Studio.
- **Un RUSE Studio más nuevo:** actualiza el Studio antes de cambiar ese mod: uno más antiguo podría perder lo que no
  conoce.

## Al cerrar el Studio pregunta «¿Cerrar RUSE Studio?»

Aún no está todo guardado, y el cuadro dice qué (un cuadro con texto escrito pero sin confirmar, un cambio que todavía
se está guardando, Probar en el juego aún construyendo...). **No** mantiene abierto el Studio; **Sí** lo cierra y eso
se pierde.

## El juego empieza, pero sin mis cambios

1. ¿Se inició con **Jugar** (launcher) o con **Probar en el juego** (Studio)? Desde Steam, el juego empieza sin mods.
2. Los cambios de un mapa solo se ven en ese mapa: en el menú principal haz clic en **BATALLAS** y elígelo (el mensaje
   del Studio después de Probar en el juego dice qué botón y qué mapa).
3. ¿Está el mod en el conjunto, y hay un mod más abajo en el orden que cambia lo mismo?

## El juego se cierra

Anota lo que hiciste justo antes (qué mapa, qué orden, qué había en pantalla), haz una captura de pantalla e
[[infórmalo|Informar-de-un-error]]. Los informes de cierres en mapas editados son la forma en que las herramientas de mapas se
volvieron sólidas.

## Otra cosa

[[Hacer una pregunta|Hacer-una-pregunta]].

---

[[Manual de campaña|Manual-de-campaña]] · [[English|When-Something-Goes-Wrong]]
