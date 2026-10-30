# Modeler le terrain

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.7.2 et un mod · **Prouvé en jeu :** les unités roulent
> sur le terrain modifié et y reçoivent des ordres

## Ouvrir la carte

1. Onglet **Cartes**, choisissez la carte à gauche (le bouton **«** replie la liste pour plus de place).
2. Regardez autour : faites glisser pour tourner, glissez avec le bouton droit pour vous déplacer, la molette pour
   zoomer (touches : [[Touches de la vue carte|Touches-de-la-vue-carte]]).
3. Dans la barre en bas, cliquez sur **Terrain et eau**. Ses outils s'ouvrent au-dessus de la barre, l'onglet
   **Terrain** d'abord.

## Les outils

| Outil | Pour faire | Comment |
|---|---|---|
| **Colline** | une colline ronde | un clic |
| **Surélever** / **Abaisser** | monter ou creuser, petit à petit | glisser |
| **Cratère** | un cratère avec un rebord | un clic |
| **Plateau** | une colline au sommet plat | un clic |
| **Aplanir** | ramener les bosses vers une même hauteur | glisser |
| **Niveler** | peindre le terrain à plat, à la hauteur où vous commencez | glisser |
| **Adoucir** | adoucir les arêtes vives | glisser |
| **Rampe** | une pente régulière, par exemple jusqu'à un plateau | cliquez là où elle commence, puis là où elle finit |

**Taille** et **Force** sont les curseurs à droite (touches **[ ]** et **- =**).

## L'eau

Cliquez sur l'onglet **Eau** (dans **Terrain et eau**) :

- **Eau** inonde le terrain sous un niveau : la hauteur où vous commencez à glisser, plus la Force. Faites-la glisser
  le long d'une vallée pour une rivière, ou dans un creux pour un lac.
- **Assécher** ramène l'eau au niveau de base de la carte : les rivières et les lacs à cet endroit s'assèchent.

## Peindre le sol avec une texture (Studio 0.9.8.5)

**Encore bogué, à utiliser à vos risques.** Dans la barre en bas, cliquez sur **Peinture de carte**, puis sur
**Texture**. Choisissez d'où vient la texture, cliquez sur l'une d'elles, et faites glisser sur le sol :

- **Textures du jeu :** les textures de sol des cartes du jeu (herbe, champs, sable, neige, roche, routes...), par
  groupe, avec une recherche. Elles sont lues dans votre jeu ; rien d'elles ne va dans votre mod.
- **D'une carte :** choisissez une carte, cliquez sur un endroit : un carré de 320 m de son sol devient votre texture.
- **Vos images :** **Ajouter une image…** garde une image à vous dans votre mod (`files/ground`).
- **En ligne (gratuit) :** des textures Poly Haven et ambientCG (CC0) et des photos aériennes des États-Unis (domaine
  public). Un clic télécharge cette seule image dans votre mod, avec son crédit. Pas encore essayé.
- **Cette carte :** copie le sol de cette carte depuis un endroit que vous choisissez.

**Taille** la pose plus grande ou plus petite (d'un quart à 16 fois). Avec une texture du jeu, **Détail du jeu de
près** pose aussi les décalques du jeu de cette texture par-dessus ce que vous peignez. Pas encore vu en jeu.

## Annuler et tout effacer

**Annuler** (ou **Ctrl+Z**) reprend le dernier trait ; **Tout effacer** reprend tous les traits de cette carte.

## Le voir en jeu

**Tester en jeu**, puis dans le menu principal du jeu cliquez sur **BATAILLES** et choisissez cette carte. Le message
en bas du Studio dit laquelle.

> [!TIP]
> Les falaises abruptes ont l'air dentelées : le sol du jeu est un maillage de triangles, et une arête vive tombe entre
> eux. Les formes larges et douces rendent le mieux.

**Suite :** [[Couvert et déplacement|Couvert-et-déplacement]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Shape-the-Ground]]
