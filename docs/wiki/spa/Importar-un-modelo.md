# Importar un modelo

> **Para:** modders · **Necesitas:** RUSE Studio 0.9.6 o posterior, un mod y un modelo 3D (.3ds, .glb o .gltf) ·
> **Tiempo:** unos minutos

Da a una unidad nueva un modelo 3D propio, de Blender o de cualquier otra herramienta 3D. Así se hizo el
[mod del M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods): el primer modelo traído a R.U.S.E. desde otro programa
3D, visto en el juego.

Un modelo también puede ir en un edificio nuevo, en lugar de una pieza de su aspecto (consulta
[[Edificios y menús de construcción|Edificios-y-menús-de-construcción]]), o en tu mapa como roca, objeto, arbusto o árbol propio
(consulta [[Colocar edificios y árboles|Colocar-edificios-y-árboles]]). Los dos: Studio 0.9.8.8, visto en el juego.

## 1. Consigue un modelo

Un **.3ds** con sus imágenes (.tga o .png), o un **.glb** o **.gltf** (con las imágenes dentro: PNG, JPG o WebP). Un
modelo que el importador no puede leer (mallas comprimidas, imágenes KTX2) lo dice, y cómo arreglarlo en Blender.

- **Desde Blender:** File > Export > glTF 2.0, formato **glTF Binary (.glb)**.
- **Desde un sitio de modelos gratuitos:** muchos tanques vienen como .3ds con una carpeta de imágenes .tga. Deja la
  carpeta tal como vino: el Studio encuentra las imágenes junto al .3ds o en la carpeta de encima, incluso con los
  nombres acortados que usan los archivos .3ds (`MAIN_DEF.TGA` por `Main_Defuse.tga`).
- Comprueba la licencia del modelo antes de compartir tu mod, y da crédito a su autor en el README de tu mod.

**Lo que ayuda:** piezas con nombres según lo que son. El Studio gira con la torreta una pieza que tenga *turret* en su
nombre (o *tourelle*, *tower*), y también una con *barrel*, *gun* o *cannon*. Una pieza que está sobre la torreta
también gira con ella. Todo lo demás se mueve con el casco. El cañón debe apuntar recto hacia delante.

El ejemplo del Abrams: **«Tank Abrams», de ags**, gratis en
[downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/) (un .3ds y sus imágenes .tga,
con piezas llamadas Main_Body, Main_Turre, Main_Barre...).

## 2. Crea la unidad

En la pestaña **Unidades**, haz clic en **Nueva unidad (importar un modelo)** arriba, y luego elige la unidad de la que
partir (para un tanque, un tanque: el Sherman para el Abrams). Dale un nombre y haz clic en **Crear**: la página de la
unidad nueva se abre en **Importar modelo…**. El modelo de la unidad nueva girará y avanzará como el de esta unidad. La
página de una unidad del juego tiene la misma entrada: **Nueva unidad a partir de esta…** bajo **Su propio modelo**.
(El Studio 0.9.6 aún no tiene ninguno de los dos botones: abre la unidad y elige **Nueva unidad…** en su página.)

## 3. Importa

En la página de la unidad nueva, bajo **Su propio modelo**:

1. Ajusta el **Tamaño**: su longitud respecto a la de la unidad copiada. **1** es igual de largo; un M1 Abrams respecto
   a un Sherman es **1.36** (sus longitudes reales).
2. Haz clic en **Importar modelo…** y elige el .3ds o el .glb.

El Studio lo ajusta a la unidad: mirando hacia delante (hacia donde apunta su cañón), su longitud, colocado donde está
la unidad copiada, con su torreta girando en el sitio que tiene en tu modelo, apoyado en el suelo. Sus imágenes pasan a
ser texturas propias. La página lo muestra en 3D, con las piezas que giran con la torreta. Si no se encontró una imagen,
dice cuál: pon las imágenes junto al modelo e impórtalo otra vez.

Se guarda en tu mod como `files/models/<the unit's name>.glb`. **Usar el modelo de la unidad copiada** lo quita otra
vez.

**Su tamaño más tarde:** el control deslizante bajo el cuadro del tamaño va de **Diminuto** a **Enorme** (de 0.05 a
20), con **Tamaño del juego** (1) y, en una unidad de época, **Tamaño real** marcados; haz clic en **Cambiar tamaño** y
el modelo se ajusta otra vez a partir de su propio archivo. Con varios aviones nuevos (o unidades terrestres), un clic
les cambia el tamaño a todos. El juego lee un modelo cuando carga, así que un tamaño nuevo se ve a partir de la
siguiente construcción.

**Dónde queda:** un modelo nuevo se pone en el centro de la unidad que copia, así que a la mayoría de los modelos no les
hace falta nada aquí. Si el tuyo no queda bien colocado, abre la sección **Moverlo** bajo el tamaño (se queda abierta en
un modelo que hayas movido). Pide tres números, **Adelante**, **Derecha** y **Arriba**, en unidades del juego (la página
dice cuánto mide la unidad copiada en esas unidades). Un menos va al otro lado, y 0, 0, 0 lo devuelve a donde se ajustó.
Haz clic en **Mover** y el modelo se ajusta otra vez a partir de su propio archivo, movido esa distancia; su torreta y
sus hélices van con él, así que siguen girando en el sitio correcto. En la vista 3D, el anillo azul es donde está la
unidad copiada, y la marca del anillo es el frente. Un tamaño nuevo conserva el movimiento. Un modelo ligado a los
huesos de la unidad (un soldado, la dotación de un cañón) se queda donde están sus huesos: ese, muévelo en Blender. Un
modelo importado antes del Studio 0.9.8.17 conserva su sitio de antes (su torreta sobre la torreta de la unidad
copiada), aunque le cambies el tamaño, hasta que lo importes otra vez o lo muevas; los modelos de las unidades de época
conservan el suyo.

**Los aviones:** un avión abierto en Blender desde el Studio y traído de vuelta mira hacia delante y conserva sus
hélices donde las tiene tu modelo, tantas como tenga, sin importar las que tuviera el avión que copia: palas en el
suelo, discos girando en el aire. Visto en el juego. Un modelo de cualquier otro sitio conserva sus hélices tal como
están dibujadas, quietas: el importador aún no sabe distinguir cuáles de sus piezas son hélices. En la vista 3D, los
discos de un avión se ven transparentes, como el juego dibuja una hélice que gira.

**Soldados, dotaciones y más aviones:** los soldados, la dotación de un cañón y los aviones a los que el Studio antes no
podía ajustar un modelo (el P-47, por ejemplo) también admiten un modelo propio, si está ligado a los huesos de la
unidad: uno de los modelos del juego abierto en Blender desde el Studio y cambiado allí, por ejemplo. Va sobre esos
huesos tal cual, sin mover ni escalar nada, y los demás hombres de un pelotón con los mismos huesos también lo llevan.
Visto en el juego con un pelotón de fusileros, la dotación de un cañón y el P-47.

**Tus jugadores:** un mod con un modelo importado con el Studio 0.9.8.17 o posterior necesita el Launcher 0.4.8.17 o más
reciente: un Launcher más antiguo le da al modelo el esqueleto de la unidad copiada, así que su torreta gira alrededor
del punto equivocado. La 0.4.8.17 es una actualización obligatoria, así que el Launcher la instala solo.

## 4. Su tarjeta, y luego la prueba

Gira la vista 3D hasta que el nuevo modelo se vea bien dentro del marco discontinuo y haz clic en **Usar esta vista
como tarjeta** (consulta [[Editar unidades|Editar-unidades]]). Luego **Probar en el juego**: la unidad está en su fábrica en
una batalla.

## Cambiarlo en Blender

`files/models/<the unit's name>.glb` se abre en Blender como cualquier .glb. Conserva los dos nombres de objeto
(`chassis` para el casco, `tourelle_01` para la torreta) y expórtalo sobre el mismo archivo (glTF Binary): la siguiente
construcción lo usa.

**Abrir en Blender**, en la página de una unidad, nombra el hueso de cada pieza como lo hace el juego, así que uno de
los tanques del propio juego abierto en Blender e importado de vuelta conserva su torreta girando (Studio 0.9.8.8; un
modelo exportado antes conserva sus nombres viejos: ábrelo otra vez en Blender).

**Un modelo que quedaba en el sitio equivocado** (Studio 0.9.8.7 y anteriores, en unidades nuevas hechas a partir del
Panther y de otras 85 unidades cuyas torretas el Studio leía mal): usa otra vez **Importar modelo…** en esa unidad, y
queda sobre la torreta.

## En fase temprana

- Las orugas y las ruedas aún no giran: se mueven con el casco.
- El fogonazo del cañón y los restos son los de la unidad copiada.
- Las imágenes se hacen de 1024 de ancho como máximo, como las imágenes de las unidades del propio juego.
- Probado en el juego con los propios modelos del juego (el Sherman, dos aviones, un pelotón de fusileros, la dotación
  de un cañón): aún no con un modelo de otro sitio, otro tanque con torreta, una torreta que da la vuelta completa ni un
  avión que copie una unidad sin hélices.

Desde la línea de comandos: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. Con `--move`, se ajusta como lo ajusta el Studio:
`--move 50 0 -10` lo mueve 50 hacia delante y 10 hacia abajo desde donde está ajustado (adelante, derecha, arriba), y
`--move 0 0 0` lo deja ahí. Sin `--move`, el comando aún lo ajusta a la manera antigua, con su torreta sobre la torreta
de la unidad copiada.

**Siguiente:** [[Exportar y compartir|Exportar-y-compartir]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Import-a-Model]]
