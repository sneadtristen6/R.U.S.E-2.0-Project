# Instalar y jugar

> **Para:** jugadores · **Necesitas:** R.U.S.E. de Steam, instalado · **Tiempo:** 5 minutos

**La versión corta:** descarga **RUSE-Launcher-Setup** de la página de versiones, ejecútalo, abre **RUSE Launcher**,
haz clic en **Mods compatibles**, marca un mod y pulsa **Instalar**, ponlo en un conjunto de mods y luego **Jugar**.
Cada paso de abajo dice exactamente dónde hacer clic.

Solo necesitas **RUSE Launcher** para jugar con mods. **RUSE Studio** sirve para crearlos (consulta el final de esta
página).

## Paso 1: Descarga el Launcher

1. Abre la página de [versiones del launcher](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher).
2. La más reciente está arriba, marcada **Latest** (por ejemplo *RUSE Launcher 0.4.8.9*).
3. Baja hasta **Assets**, debajo de ella, y haz clic en **RUSE-Launcher-Setup-0.4.8.9.exe** (el número de versión
   cambia; coge el `.exe` que empieza por `RUSE-Launcher-Setup`). Tu navegador lo descarga.

Los demás archivos de ahí (`RUSE-Launcher-notes.json`, *Source code*) no hacen falta.

## Paso 2: Instálalo

1. Abre el archivo que descargaste (normalmente en tu carpeta **Descargas**).
2. **¿«Windows protegió su PC»?** Haz clic en **Más información** y luego en **Ejecutar de todas formas**. La aplicación
   es nueva para la comprobación de reputación de Windows; su código es público en este GitHub.
3. Avanza por el instalador. Deja marcada **Conservar una copia limpia de los archivos de mi juego**: las aplicaciones
   nunca cambian la carpeta de tu juego, pero otros gestores de mods y los cambios a mano sí pueden, y cada juego con
   mods se construye a partir de esos archivos. La copia se hace la primera vez que arranca la aplicación (unos
   minutos, y más o menos tanto espacio en disco como el juego).
4. Inicia **RUSE Launcher** (menú Inicio, o el acceso directo del escritorio). La primera vez, **Elige tu idioma**:
   cualquiera de once, los diez del juego y el persa (فارسی); el botón de idioma de arriba lo cambia cuando quieras.
   Encuentra R.U.S.E. por sí solo a través de Steam.
   Si dice que no puede: **Ajustes > Carpeta del juego > Elegir carpeta…** y elige la carpeta que contiene `RUSE.exe`
   (normalmente `C:\Program Files (x86)\Steam\steamapps\common\R.U.S.E`).

> [!IMPORTANT]
> **R.U.S.E. 2.0 funciona solo con una copia del juego que tengas en Steam.** Antes de que empiece un juego con mods, el
> Launcher y el Studio comprueban la carpeta del juego: el registro de Steam de R.U.S.E. instalado ahí, el propio
> archivo de Steam que hay en ella, y que no haya archivos que hagan funcionar el juego sin Steam. Si no pueden
> confirmarlo, un cuadro dice por qué y qué hacer (Jugar sigue desactivado hasta entonces): consulta
> [[Cuando algo sale mal|Cuando-algo-sale-mal]].

## Paso 3: Consigue mods

**De nuestra lista (lo más fácil):** haz clic en **Mods compatibles**, marca los mods que quieras y pulsa **Instalar**.
Cada archivo se descarga y se comprueba con la lista antes de entrar en tu biblioteca.

**De un archivo que alguien compartió:** haz clic en **Añadir un archivo de mod…** y elige el archivo, o arrástralo a
la ventana. El Launcher admite:
- `.rusemod`: hecho con RUSE Studio;
- `.rmod`: hecho para el RUSE Mod Manager de LittleGroove;
- `.zip`: una carpeta de mod comprimida.

Primero comprueba el archivo: un archivo que no es un mod, o que contiene un programa, se rechaza indicando el motivo.

**Un mod antiguo que viene como archivos propios del juego** (paquetes `.dat` que te dijeron que copiaras en la carpeta
del juego): haz clic en **Convertir un mod antiguo…**, elige su carpeta, dale un nombre y haz clic en **Convertir y
añadir a la biblioteca**. La carpeta de tu juego no se toca.

## Paso 4: Elige a qué jugar

1. Un **conjunto de mods** son los mods con los que juegas juntos, en orden. Haz clic en **Nuevo conjunto de mods…**,
   añade los mods y ponlos en orden (cuando dos mods cambian lo mismo, gana el de más abajo).
2. Si dos mods no se pueden jugar juntos, el Launcher dice cuáles y por qué, antes de que juegues.

## Paso 5: Juega

Elige tu conjunto de mods y pulsa **Jugar**. La primera vez, el Launcher construye una copia con mods del juego (un
minuto o así); después, solo lo que cambió. Luego R.U.S.E. se inicia, con tus mods.

Tu juego con mods dice **R.U.S.E. 2.0 en oro**: se abre con una escena de batalla, y su menú principal, sus menús y sus
pantallas de carga llevan el título dorado. Se hace en tu PC con los archivos de tu propio juego la primera vez (unos
minutos, una sola vez). Para conservar el título del propio juego, desmarca **El título del juego** en **Ajustes**.

> [!NOTE]
> Iniciar R.U.S.E. desde **Steam** inicia el juego **sin** mods, como siempre. Para jugar con mods, inícialo con
> **Jugar** en el Launcher. Tu instalación de Steam nunca se modifica.

## Actualizaciones

El Launcher busca una versión nueva cada vez que arranca: haz clic en **Actualizar ahora** cuando te ofrezca una. Si la
actualización falla con "certificate verify failed", descarga el `RUSE-Launcher-Setup` más reciente del Paso 1 en tu
navegador y ejecútalo: se instala sobre el antiguo y conserva tus mods.

**Actualizaciones obligatorias:** una actualización marcada como obligatoria (una importante, como una corrección de seguridad) no se puede omitir. Un cuadro cubre el Launcher y la actualización se instala sola; luego el Launcher se vuelve a abrir. Hasta que esté instalada, **Jugar** sigue desactivado. Sin Internet, el cuadro lo dice: conéctate y pulsa **Reintentar**. El Studio hace lo mismo, con **Probar en el juego**.

## ¿Problemas?

| Lo que ves | Qué hacer |
|---|---|
| «Windows protegió su PC» | **Más información** y luego **Ejecutar de todas formas** (Paso 2). |
| El Launcher no encuentra R.U.S.E. | **Ajustes > Carpeta del juego > Elegir carpeta…**, la carpeta con `RUSE.exe`. |
| "certificate verify failed: unable to get local issuer certificate" | Consigue el Launcher 0.4.8.4 o más reciente (Paso 1); consulta [[Cuando algo sale mal|Cuando-algo-sale-mal]]. |
| "unable to get issuer certificate" o «este PC no confía en el certificado de seguridad del sitio» al instalar mods | Consigue el Launcher 0.4.8.9 o más reciente (Paso 1), o descarga el mod en tu navegador y usa **Añadir un archivo de mod…**; consulta [[Cuando algo sale mal|Cuando-algo-sale-mal]]. |
| El juego empieza sin mis mods | Inícialo con **Jugar** en el Launcher, no desde Steam. |
| Mis amigos no pueden unirse a mi partida | Todos necesitan los mismos mods en el mismo orden: [[Jugar con amigos|Jugar-con-amigos]]. |
| Cualquier otra cosa | [[Cuando algo sale mal|Cuando-algo-sale-mal]], o pregunta en [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) o en el [Discord](https://discord.gg/h54t5baNsC). |

## Linux y Steam Deck (con Proton)

Cuando la ventana propia de una aplicación no puede mostrar sus páginas (con Proton se queda azul, porque WebView2 de
Microsoft no arranca ahí), la aplicación se abre en tu navegador web, y un pequeño cuadro lo indica: deja el cuadro
abierto mientras juegas, y ciérralo para cerrar la aplicación. Aún no probado en Linux: cuéntanos cómo va en
[Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## Crear mods: RUSE Studio

1. Abre la página de [versiones del studio](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio). El
   Studio es una versión preliminar, así que sus versiones están marcadas **Pre-release**: coge la más reciente.
2. En **Assets**, haz clic en **RUSE-Studio-Setup-0.9.8.9.exe** (la versión más reciente) y ejecútalo como en el Paso 2.
3. Inicia **RUSE Studio** y luego sigue [[Tu primer mod|Tu-primer-mod]] (10 minutos).

**Siguiente:** [[Jugar con amigos|Jugar-con-amigos]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Install-and-Play]]
