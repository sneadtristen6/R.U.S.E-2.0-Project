# Bâtiments et menus de construction

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.9.8.8 ou plus récent et un mod · **Durée :** quelques
> minutes

Les bâtiments de chaque nation, ce que proposent leurs menus de construction et dans quel ordre, et des bâtiments à
vous. Vu en jeu.

## Le tableau des bâtiments

Ouvrez l'onglet **Nations** : sous chaque nation, **Bâtiments et unités** montre ses bâtiments en lignes, chacune une
rangée des unités que propose son menu de construction, dans l'ordre du jeu. À côté du nom de chaque nation, **Garder ses unités** remet toutes ses unités dans ses menus de construction, comme dans le jeu, et **La vider** les retire toutes, pour que vous remplissiez vous-même ses bâtiments. **Recherche**, au-dessus des nations : **Aucune recherche** rend chaque unité de chaque nation constructible dès le départ ; **Garder les recherches du jeu** rend leur recherche aux unités du jeu. Les deux demandent d'abord.

- **+** ajoute une unité à un bâtiment : une unité de la nation elle-même, une copie de celle d'une autre nation, ou une
  [[unité d'époque|Unités-des-autres-époques]]. Une copie va dans votre mod, nommée comme le jeu la nomme.
- **Faites glisser** une unité le long de sa ligne pour changer sa place dans le menu, ou sur un autre bâtiment pour la
  construire là.
- **×** retire une unité du menu de construction. Elle est cachée, pas supprimée : l'unité est toujours dans les
  fichiers du jeu.
- **Recherche…** puis **Placer sous celle-ci** sur l'unité après laquelle elle vient : elle se recherche depuis
  celle-là (dans n'importe quel bâtiment de la nation). **Constructible dès le départ** n'a besoin d'aucune recherche.
  **Coût de recherche** et **Temps de recherche (s)** sont à côté.

Chaque ligne dit combien d'unités elle a. Un bâtiment laissé sans rien à construire montre dans le jeu la liste de
bâtiments du QG quand on le choisit. Plus de 10 unités dans un bâtiment, un avion dans un bâtiment terrestre, ou un
véhicule à l'aérodrome : pas encore essayé en jeu.

La page d'une unité dans l'onglet **Unités** dit où elle est construite (« Construite dans BASE DE BLINDES : place 2 sur
6 »), et **Voir dans les bâtiments** ouvre sa ligne.

## Groupes

En jeu, la liste de construction d'un bâtiment montre chaque groupe sur une ligne : une unité et ses améliorations
(le Panzer IV et le Panther). Le tableau montre les groupes de chaque bâtiment, chacun avec son compte (**4 sur 6**),
et combien de groupes a le bâtiment (**7 groupes sur 10**).

- Une nouvelle unité va dans le groupe de son type dans son bâtiment, ou dans un groupe à elle quand le bâtiment n'en a
  aucun de ce type. **+** sur un groupe, ou un dépôt dessus, l'y met ; **Nouveau groupe** en commence un.
- Un groupe a au plus 6 (ses unités et cartes de recherche), et un bâtiment au plus 10 groupes, pour que sa liste
  tienne à l'écran. Un de plus est refusé : retirez une unité, ou mettez-la dans un bâtiment à elle (**Ajouter un bâtiment…**).
- Une unité sans type de carte dans le jeu (un camion, le lanceur de V2) : choisissez son groupe.

Pas encore essayé en jeu.

## Ajouter un bâtiment

**Ajouter un bâtiment…** sous le tableau d'une nation : choisissez le bâtiment du jeu qu'il copie (**Copie de**),
donnez-lui un **Nom**, puis soit :

- **Produit les mêmes unités que le bâtiment copié**, soit
- **Produit ses propres unités** : une ligne et un onglet à lui dans la barre de construction du jeu, remplis avec
  **+**. Jusqu'à trois par nation.

Le deuxième et le troisième bâtiment avec leurs propres unités ont besoin d'un petit correctif du jeu pour plus de
bâtiments. Le Studio le télécharge une fois et ne le met que dans votre copie moddée du jeu, jamais dans le jeu de votre
dossier Steam.

## L'apparence propre d'un bâtiment

Sur la page d'un nouveau bâtiment, **Importer un modèle** met un modèle 3D à vous (.glb, .gltf ou .3ds) à la place
d'une pièce de l'apparence qu'il copie : le bâtiment principal d'une usine ou d'un QG, ou la pièce que vous choisissez.
Votre modèle est mis à la taille de cette pièce et se tient là où elle se tenait ; le reste de l'apparence reste. Les
bâtiments du jeu lui-même restent tels quels : créez d'abord un nouveau bâtiment à partir de l'un d'eux.

**Où votre mod le garde :** `files\buildings\<nom du bâtiment>\`. La boîte affiche le chemin complet sur votre PC (ou l'endroit où il sera, avant que le modèle soit en place), et **Afficher dans le dossier** ouvre ce dossier.

**Son image dans le menu de construction :** tournez et zoomez le modèle jusqu'à ce qu'il rende bien dans le cadre en
pointillés, puis utilisez cette vue. Voir [[Importer un modèle|Importer-un-modèle]] pour les modèles en général.

## Ce qui a été vu en jeu

Vu : les changements du tableau (unités ajoutées, déplacées, retirées, recherchées depuis une autre), un bâtiment
copié, un bâtiment avec ses propres unités et son onglet dans la barre de construction, un deuxième et un troisième avec
le correctif du jeu, et le propre modèle et l'image d'un bâtiment.

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Buildings-and-Build-Menus]]
