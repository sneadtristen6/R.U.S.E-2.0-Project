# Trazar carreteras

> **Para:** modders · **Necesitas:** RUSE Studio 0.7.4 y un mod · **Probado en el juego:** las rutas de suministro
> siguen una carretera nueva, y queda pintada en el suelo

## Ver las carreteras del mapa

Marca **Carreteras** arriba del mapa: las propias carreteras del mapa se ven en dorado, sobre el terreno mientras le
das forma.

## Traza una carretera nueva

1. En la barra de abajo, haz clic en **Carreteras y puentes** (se abre su pestaña **Carreteras**). Las carreteras del
   mapa se ven en dorado, las nuevas tuyas en azul.
2. Elige una herramienta:

| Herramienta | Cómo |
|---|---|
| **Recta** | Haz clic donde empieza la carretera y luego donde termina. |
| **Curva** | Haz clic en el inicio, luego en la curva hacia la que se tira, y luego en el final. |
| **Libre** | Haz clic a lo largo del camino; haz doble clic, pulsa **Enter** o haz clic en **Terminar** para acabarla. |

3. Una cinta azul sigue al puntero, con la **longitud de la carretera** al lado (Libre también muestra el tramo desde
   tu último clic). Un extremo cerca de cualquier carretera **se engancha a ella** (un anillo muestra dónde), así que
   la carretera nueva se une a ella: los camiones de suministros pueden ir de una a otra. Las herramientas de
   Carreteras muestran cuántas carreteras nuevas tiene el mapa y su longitud total.
4. **Esc** descarta una carretera que estás trazando; **Deshacer** (o **Ctrl+Z**) quita la última, **Rehacer** (o
   **Ctrl+Y**) la vuelve a trazar.

Las carreteras nuevas se guardan en tu mod al momento (`maps/<map>/roads.toml`).

## Lo que hace una carretera nueva en el juego

- **Las rutas de suministro la usan** (probado: la ruta de un depósito de suministros tomó un atajo nuevo a campo
  abierto).
- **Queda pintada en el suelo** con el color de carretera propio del mapa, para que los jugadores la vean (probado en
  el juego). Se parece a las carreteras del propio mapa desde lo alto y a ras de suelo.
- **La infantería la sigue** para llegar antes a algún sitio (probado en el juego, Studio 0.8.0).
- **Sobre el agua lleva un puente**: el tipo propio del mapa (24 de los 32 mapas tienen uno), una sola pieza estirada
  de orilla a orilla como los propios puentes del juego, y las unidades pueden cruzarlo. Una carretera sobre uno de
  los puentes del propio mapa pone el puente nuevo en su lugar. En un mapa sin tipo de puente, la construcción lo dice
  y el agua sigue cerrada. (Probado en el juego: tanques, infantería y camiones de suministros cruzan por el tablero.)
- Las plantas y objetos de su camino se quitan; **Mantener los árboles en las carreteras nuevas** conserva los
  árboles y arbustos (una carretera bajo los árboles).

## Quitar las carreteras y los puentes del propio mapa

En las herramientas de **Carreteras**:

- **Quitar las carreteras del mapa:** las propias carreteras del mapa se van: la red que siguen los camiones de
  suministros (en su lugar van a campo traviesa) y las carreteras dibujadas en el suelo. Tus carreteras nuevas se
  quedan. Visto en el juego: las carreteras se van; los camiones de suministros a campo traviesa aún no se han probado.
- **Quitar los puentes del mapa:** los propios puentes del mapa se van, con los tableros sobre los que estaban las
  unidades. Las unidades siguen cruzando donde estaban, por el suelo de debajo, a menos que marques también la casilla
  siguiente. Tus puentes nuevos se quedan.
- **Cerrar los cruces de los puentes viejos** (con los puentes quitados; de DomesticNukes): el suelo donde cada puente
  viejo cruzaba el agua se cierra a las unidades, y los enlaces de carretera que lo atraviesan se cortan: nada cruza
  allí, camiones de suministros incluidos, y el resto de la red de carreteras se queda. Una carretera nueva tuya que
  cruce en el mismo sitio recibe allí su propio puente. Si cerrarlos dejara un trozo de terreno aislado del resto, el
  Studio lo dice antes de la construcción.

Aún sin probar en el juego: quitar los puentes y cerrar sus cruces.

## Coloca un puente propio

En la pestaña **Puentes**: elige un tipo, ajusta su longitud y su giro, y luego haz clic en el suelo donde va el centro
del puente. Los dos extremos deberían apoyarse en orilla seca. **Deshacer** y **Rehacer** también funcionan aquí.

**Verlo:** **Probar en el juego**, luego en el menú principal del juego **BATALLAS** y el mapa. Coloca un depósito de
suministros cerca de tu carretera y mira su ruta.

**Siguiente:** [[Colocar edificios y árboles|Colocar-edificios-y-árboles]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Draw-Roads]]
