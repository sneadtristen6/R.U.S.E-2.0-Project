# Tu primer mod

> **Para:** modders nuevos · **Necesitas:** R.U.S.E. en Steam · **Lleva:** 10 minutos

Un recorrido completo: instala el Studio, crea un mod que hace que el M4 Sherman cueste 1 $, y míralo en el juego.

## 1. Instala RUSE Studio

1. Descarga el instalador desde las [versiones del Studio](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio)
   y ejecútalo («Windows protegió su PC»: **Más información**, **Ejecutar de todas formas**).
2. El primer arranque lee los archivos del juego en un índice: un minuto o dos, una vez por cada actualización del
   juego.

## 2. Crea un mod

El Studio se abre en **¿Qué quieres hacer?**: **Seguir con un mod**, **Empezar un mod nuevo** o **Saltar** (marca
**Saltar siempre esta pantalla** para ir directo a las pestañas a partir de entonces; Ajustes la vuelve a mostrar).

1. Haz clic en **Empezar un mod nuevo**. Sus pasos se muestran en una barra arriba, con **Atrás** y **Siguiente**:
   - **Nombre:** escribe un nombre, por ejemplo `cheap-sherman` (el nombre que ven los jugadores en el Launcher).
   - **Naciones:** para cada nación, **Conservar sus unidades** (sus menús de construcción como en el juego) o
     **Empezarla vacía**. **Cambiar** da a una nación un nombre y una bandera nuevos ([[Convertir una nación en otra|Convertir-una-nación-en-otra]]).
   - **Investigación:** **Conservar la investigación del juego**, **Sin investigación** (cada unidad se puede construir
     desde el principio) o **Personalizada**.
   - **Edificios:** los edificios de cada nación y lo que construyen ([[Edificios y menús de construcción|Edificios-y-menús-de-construcción]]).
   - **Qué más:** marca lo que quieres cambiar después (valores de las unidades, ajustes de la IA y de los jugadores,
     música y sonidos, cualquier otro valor); cada cosa se abre como su propia pestaña. Para este recorrido, marca
     **Valores de las unidades**.
2. Conserva las unidades y la investigación del juego, y pulsa **Siguiente** hasta que se abra la pestaña Unidades.

¿Ya estás en el Studio? El menú **Mod** de la cabecera también tiene **Nuevo mod…**: escribe un nombre y haz clic en
**Crear**.

A partir de ahora, todo lo que cambies se guarda en este mod, nunca en el juego.

## 3. Cambia el Sherman

1. Abre la pestaña **Unidades** y escribe `sherman` en el cuadro de búsqueda.
2. Haz clic en **M4 Sherman**.
3. Busca su precio y escribe `1`. Se guarda al momento, y el valor anterior se muestra al lado. **Deshacer** lo
   devuelve a como estaba.

## 4. Pruébalo

1. Haz clic en **Probar en el juego** (cabecera). El Studio comprueba el mod, construye la copia con mods (una para todo el PC, `RUSE-Instances\Modded game` en la unidad del juego, o la carpeta que elegiste en Ajustes) e inicia R.U.S.E.
2. En el menú principal del juego, haz clic en **BATALLAS** (una partida libre contra el ordenador), elige cualquier
   mapa, juega con USA y abre la fábrica de tanques: el Sherman cuesta 1 $.

> [!TIP]
> Si en su lugar aparece una barra roja bajo la cabecera, la comprobación del mod ha encontrado un error en un archivo
> de tu mod. Consulta [[Cuando algo sale mal|Cuando-algo-sale-mal]].

## Adónde ir después

- Más sobre unidades: [[Editar unidades|Editar-unidades]]
- Mapas: [[Dar forma al terreno|Dar-forma-al-terreno]]
- Compártelo: [[Exportar y compartir|Exportar-y-compartir]]

---

[[Manual de campaña|Manual-de-campaña]] · [[English|Your-First-Mod]]
