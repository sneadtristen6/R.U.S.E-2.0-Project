# Placer bâtiments et arbres

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.7.2 et un mod (Grille, Cadre, Tracé, Sélection et
> Rétablir : 0.9.8.7 ; modèles à vous : 0.9.8.8) · **Prouvé en jeu :** les bâtiments placés s'affichent à tous les
> niveaux de zoom, jusqu'à 8× leur taille, et les unités les contournent. Pas encore essayé en jeu : ce qui est placé
> avec Grille, Cadre et Tracé, et les objets déplacés

## Placer

1. Dans la barre, cliquez sur **Bâtiments**, ou sur **Objets et arbres** puis son onglet **Objets** ou **Arbres**.
2. Choisissez un type parmi les images (tapez dans la zone de recherche pour réduire la liste). Chaque image est
   dessinée d'après le modèle du jeu lui-même, et le nombre dans son coin dit combien la carte en a déjà. La liste
   contient les types propres à cette carte : le jeu ne prend qu'un type qu'une carte utilise déjà.
3. Choisissez comment un clic place :
   - **Un** : un objet là où vous cliquez ;
   - **Zone** : faites glisser pour disperser des objets dans un cercle (**Écart** les tient espacés, **Zone** règle le
     cercle) ;
   - **Ligne** : cliquez sur le début, puis sur la fin, pour une rangée (une haie, une rue, une ligne d'arbres),
     orientée dans son sens ;
   - **Grille** : des rangées d'objets : cliquez où commence la première rangée et où elle finit, puis écartez les
     rangées et cliquez (**Entre rangées** règle l'écart) ;
   - **Cadre** : tracez un cadre sur le sol et relâchez : il se remplit de l'objet choisi, en rangées ;
   - **Tracé** : cliquez le long du trajet, puis double-cliquez, appuyez sur **Enter** ou sur **Terminer** : les objets
     suivent une courbe douce passant par vos clics (une haie, une ligne d'arbres) ; avec une largeur, une bande
     d'objets. **Esc** abandonne une grille, une ligne ou un tracé commencé.
4. **Face aux routes :** près d'une route, un objet se met à côté d'elle et se tourne vers elle, et une rangée la
   suit ; une grille ou un cadre laisse les routes dégagées. Le curseur de rotation le tourne toujours (essayez 180° si
   une maison montre son dos).
5. **Rotation** et **Taille** (jusqu'à 10×) sont les curseurs à droite. Les arbres varient un peu en taille et en
   rotation d'eux-mêmes, pour qu'un bois n'ait pas l'air tamponné.

Avant que vous cliquiez, le type s'affiche en transparence sous le pointeur, tourné et à la taille qu'il aura. Les
objets placés s'affichent avec leurs propres modèles, chacun avec un petit point doré à son pied qui le signale de loin.

## Sélectionner, déplacer, tourner, supprimer

**Sélection** (dans les volets **Bâtiments** et **Objets et arbres**) choisit ce qui se trouve sur la carte, ce que
votre mod a placé ou ce qui appartient à la carte : cliquez sur un objet, **Shift+clic** pour en ajouter, ou tracez un
cadre autour de plusieurs. Puis faites glisser l'un des objets choisis pour les déplacer, utilisez **Rotation** et
**Taille**, ou **Supprimer**. **Remettre comme sur la carte** annule vos changements sur ceux de la carte ; **Esc** ne
choisit plus rien.

## Des modèles à vous

**Importer un modèle…** (dans **Objets et arbres**) fait d'un modèle 3D (.glb, .gltf ou .3ds) l'un des rochers,
objets, buissons ou arbres propres à votre mod de carte. Il se place comme ceux du jeu, sur chaque carte du mod, avec
des versions plus légères faites pour lui pour les distances moyennes et lointaines. Donnez-lui une **Taille**, et une
**Provenance** : un modèle fait par quelqu'un d'autre ne peut aller dans un mod que sous CC0 ou CC-BY, avec son auteur.
Coché, **Solide : les unités le contournent** ; décoché, les unités le traversent et le renversent, comme les petits
objets du jeu. **Votre modèle…** le change plus tard. Vu en jeu.

## Bâtiments solides

**Solide** (activé par défaut) fait contourner un bâtiment placé par les unités au lieu de le traverser. Désactivez-le
pour un bâtiment qui ne doit être que regardé.

## S'y cacher

Les bâtiments placés ne cachent pas les unités par eux-mêmes : ouvrez **Couvert**, choisissez **Ville** et cliquez sur
la ville que vous avez faite.

## Annuler et Rétablir

**Annuler** (ou **Ctrl+Z**) reprend le dernier objet, ou toute la zone, la ligne, la grille, le cadre ou le tracé, et
le dernier déplacement, rotation, changement de taille ou suppression. **Rétablir** (ou **Ctrl+Y**, **Ctrl+Shift+Z**)
le remet. Chaque outil de carte a les deux.

## Effacer les arbres et les objets de la carte

1. Dans la barre, cliquez sur **Effacer** (Studio 0.8.1).
2. Choisissez ce qu'il retire : **arbres**, **objets**, **bâtiments** (n'importe quel mélange). Chaque cercle garde ce
   qui était choisi quand vous l'avez peint.
3. Faites glisser sur la carte : des cercles rouges marquent ce qui part, et ce qu'ils couvrent est teinté de rouge.
   **Taille** règle les cercles ; le panneau des outils compte ce qu'ils retireront quand le mod sera construit.

Là où les arbres partent, le terrain s'ouvre à toutes les unités et perd son couvert de forêt (prouvé en jeu : les
chars entrent dans un bois dégagé, l'infanterie qui s'y trouve n'est pas cachée). Les bâtiments effacés ouvrent aussi
leur terrain aux unités. **Annuler** (**Ctrl+Z**) reprend le dernier glisser, **Tout effacer** retire tous les cercles
de la carte.

**Suite :** [[Modifier un scénario|Modifier-un-scénario]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Place-Buildings-and-Trees]]
