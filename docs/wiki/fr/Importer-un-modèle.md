# Importer un modèle

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.9.6 ou plus récent, un mod, et un modèle 3D (.3ds, .glb
> ou .gltf) · **Durée :** quelques minutes

Donnez à une nouvelle unité son propre modèle 3D, venu de Blender ou de n'importe quel autre outil 3D. C'est ainsi que le
[mod M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods) a été fait : le premier modèle amené dans R.U.S.E. depuis un
autre programme 3D, vu en jeu.

Un modèle peut aussi aller sur un nouveau bâtiment, à la place d'une pièce de son apparence (voir
[[Bâtiments et menus de construction|Bâtiments-et-menus-de-construction]]), ou sur votre carte comme rocher, objet, buisson ou
arbre à vous (voir [[Placer bâtiments et arbres|Placer-bâtiments-et-arbres]]). Les deux : Studio 0.9.8.8, vus en jeu.

## 1. Se procurer un modèle

Un **.3ds** avec ses images (.tga ou .png), ou un **.glb** ou **.gltf** (images à l'intérieur : PNG, JPG ou WebP). Un
modèle que l'importateur ne sait pas lire (maillages compressés, images KTX2) le dit, et dit comment le corriger dans
Blender.

- **Depuis Blender :** File > Export > glTF 2.0, format **glTF Binary (.glb)**.
- **Depuis un site de modèles gratuits :** beaucoup de chars viennent en .3ds avec un dossier d'images .tga. Gardez le
  dossier tel qu'il est venu : le Studio trouve les images à côté du .3ds ou dans le dossier au-dessus, même sous les noms
  raccourcis qu'utilisent les fichiers .3ds (`MAIN_DEF.TGA` pour `Main_Defuse.tga`).
- Vérifiez la licence du modèle avant de partager votre mod, et citez son auteur dans le README de votre mod.

**Ce qui aide :** des pièces nommées d'après ce qu'elles sont. Le Studio fait tourner avec la tourelle une pièce qui a
*turret* dans son nom (ou *tourelle*, *tower*), et aussi une pièce avec *barrel*, *gun* ou *cannon*. Une pièce posée sur
la tourelle tourne aussi avec elle. Tout le reste bouge avec la caisse. Le canon doit pointer droit devant.

L'exemple de l'Abrams : **« Tank Abrams » par ags**, gratuit sur
[downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/) (un .3ds et ses images .tga,
pièces nommées Main_Body, Main_Turre, Main_Barre...).

## 2. Créer l'unité

Dans l'onglet **Unités**, cliquez sur **Nouvelle unité (importer un modèle)** en haut, puis choisissez l'unité de départ
(pour un char, un char : le Sherman pour l'Abrams). Donnez-lui un nom et cliquez sur **Créer** : la page de la nouvelle
unité s'ouvre sur **Importer un modèle…**. Le modèle de la nouvelle unité tournera et roulera comme celui de cette unité.
La page d'une unité du jeu a le même accès : **Nouvelle unité à partir de celle-ci…** sous **Son propre modèle**.
(Le Studio 0.9.6 n'a encore aucun de ces deux boutons : ouvrez l'unité et choisissez **Nouvelle unité…** sur sa page.)

## 3. Importer

Sur la page de la nouvelle unité, sous **Son propre modèle** :

1. Réglez **Taille** : sa longueur par rapport à celle de l'unité copiée. **1** veut dire aussi long ; un M1 Abrams par
   rapport à un Sherman, c'est **1.36** (leurs longueurs réelles).
2. Cliquez sur **Importer un modèle…** et choisissez le .3ds ou le .glb.

Le Studio l'ajuste à l'unité : tourné vers l'avant (là où pointe son canon), à sa longueur, l'anneau de sa tourelle sur
la tourelle de l'unité copiée, posé sur le sol. Ses images deviennent ses propres textures. La page le montre en 3D, avec
les pièces qui tournent avec la tourelle. Si une image n'a pas été trouvée, elle dit laquelle : mettez les images à côté
du modèle et importez de nouveau.

Il est enregistré dans votre mod sous `files/models/<the unit's name>.glb`. **Utiliser le modèle de l'unité copiée** le
retire de nouveau.

**Sa taille plus tard :** le curseur sous la case de taille va de **Minuscule** à **Énorme** (0.05 à 20), avec **Taille du
jeu** (1) et, pour une unité d'époque, **Taille réelle** marqués ; cliquez sur **Redimensionner** et le modèle est de
nouveau ajusté depuis son propre fichier. Avec plusieurs nouveaux avions (ou unités terrestres), un clic les
redimensionne tous. Le jeu lit un modèle quand il se charge, donc une nouvelle taille se voit à partir de la construction
suivante.

**Les avions :** un avion ouvert dans Blender depuis le Studio puis ramené garde ses hélices qui tournent et reste tourné
vers l'avant. Vu en jeu.

## 4. Sa carte, puis le test

Tournez la vue 3D jusqu'à ce que le nouveau modèle rende bien dans le cadre en pointillés et cliquez sur **Utiliser cette
vue comme carte** (voir [[Modifier les unités|Modifier-les-unités]]). Puis **Tester en jeu** : l'unité est à son usine dans une
bataille.

## Le changer dans Blender

`files/models/<the unit's name>.glb` s'ouvre dans Blender comme n'importe quel .glb. Gardez les deux noms d'objets
(`chassis` pour la caisse, `tourelle_01` pour la tourelle) et exportez-le par-dessus le même fichier (glTF Binary) : la
construction suivante l'utilise.

**Ouvrir dans Blender**, sur la page d'une unité, nomme l'os de chaque pièce comme le fait le jeu, donc un des chars du
jeu ouvert dans Blender puis réimporté garde sa tourelle qui tourne (Studio 0.9.8.8 ; un modèle exporté avant garde ses
anciens noms : rouvrez-le dans Blender).

**Un modèle qui se plaçait au mauvais endroit** (Studio 0.9.8.7 et avant, sur les nouvelles unités faites à partir du
Panther et de 85 autres unités dont le Studio lisait mal la tourelle) : utilisez de nouveau **Importer un modèle…** sur
cette unité, et il se pose sur la tourelle.

## Encore au début

- Les chenilles et les roues ne tournent pas encore : elles bougent avec la caisse.
- La lueur du canon et l'épave sont celles de l'unité copiée.
- Les images font au plus 1024 de large, comme les propres images d'unités du jeu.

En ligne de commande, la même chose : `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`.

**Suivant :** [[Exporter et partager|Exporter-et-partager]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Import-a-Model]]
