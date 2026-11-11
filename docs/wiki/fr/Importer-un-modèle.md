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

Le Studio l'ajuste à l'unité : tourné vers l'avant (là où pointe son canon), à sa longueur, placé là où se tient l'unité
copiée, sa tourelle tournant là où elle est sur votre modèle, posé sur le sol. Ses images deviennent ses propres
textures. La page le montre en 3D, avec les pièces qui tournent avec la tourelle. Si une image n'a pas été trouvée, elle
dit laquelle : mettez les images à côté du modèle et importez de nouveau.

Il est enregistré dans votre mod sous `files/models/<the unit's name>.glb`. **Utiliser le modèle de l'unité copiée** le
retire de nouveau.

**Sa taille plus tard :** le curseur sous la case de taille va de **Minuscule** à **Énorme** (0.05 à 20), avec **Taille du
jeu** (1) et, pour une unité d'époque, **Taille réelle** marqués ; cliquez sur **Redimensionner** et le modèle est de
nouveau ajusté depuis son propre fichier. Avec plusieurs nouveaux avions (ou unités terrestres), un clic les
redimensionne tous. Le jeu lit un modèle quand il se charge, donc une nouvelle taille se voit à partir de la construction
suivante.

**Où il se place :** un nouveau modèle est posé au milieu de l'unité qu'il copie, donc la plupart des modèles n'ont
besoin de rien ici. Si le vôtre n'est pas bien placé, ouvrez la partie **Le déplacer** sous la taille (elle reste
ouverte sur un modèle que vous avez déplacé). Elle demande trois nombres, **Avant**, **Droite** et **Haut**, en unités
du jeu (la page dit quelle longueur fait l'unité copiée, dans ces unités). Un moins va dans l'autre sens, et 0, 0, 0 le
remet là où il a été ajusté. Cliquez sur **Déplacer** et le modèle est de nouveau ajusté depuis son propre fichier,
déplacé d'autant ; sa tourelle et ses hélices le suivent, donc elles tournent toujours au bon endroit. Dans la vue 3D,
l'anneau bleu est l'endroit où se tient l'unité copiée, et la marque sur l'anneau est l'avant. Une nouvelle taille garde
le déplacement. Un modèle lié aux os de l'unité (un soldat, les servants d'un canon) reste là où sont ses os : celui-là,
déplacez-le dans Blender. Un modèle importé avant le Studio 0.9.8.17 garde son ancienne place (sa tourelle sur la
tourelle de l'unité copiée), même redimensionné, jusqu'à ce que vous l'importiez de nouveau ou le déplaciez ; les
modèles des unités d'époque gardent la leur.

**Les avions :** un avion ouvert dans Blender depuis le Studio puis ramené reste tourné vers l'avant et garde ses
hélices là où votre modèle les a, autant qu'il en a, quelles que soient celles de l'avion qu'il copie : des pales au
sol, des disques qui tournent en vol. Vu en jeu. Un modèle venu d'ailleurs garde ses hélices telles qu'elles sont
dessinées, immobiles : l'importateur ne sait pas encore dire lesquelles de ses pièces sont des hélices. Dans la vue 3D,
les disques d'un avion apparaissent transparents, comme le jeu dessine une hélice qui tourne.

**Soldats, servants et plus d'avions :** les soldats, les servants d'un canon et les avions auxquels le Studio ne savait
pas ajuster de modèle avant (le P-47, par exemple) prennent eux aussi un modèle à eux, s'il est lié aux os de l'unité :
par exemple un des modèles du jeu ouvert dans Blender depuis le Studio et modifié là. Il va sur ces os tel quel, sans
rien déplacer ni redimensionner, et les autres hommes d'une escouade qui ont les mêmes os le portent aussi. Vu en jeu
avec une escouade de fusiliers, les servants d'un canon et le P-47.

**Vos joueurs :** un mod avec un modèle importé par le Studio 0.9.8.17 ou plus récent demande le Launcher 0.4.8.17 ou
plus récent : un Launcher plus ancien donne au modèle le squelette de l'unité copiée, donc sa tourelle tourne autour du
mauvais point. La 0.4.8.17 est une mise à jour obligatoire, donc le Launcher l'installe tout seul.

## Votre propre soldat, pas à pas

Pour une escouade (fusiliers, parachutistes, toute infanterie), le Studio fait la partie Blender avec vous :

1. **Créez l'escouade** comme à l'étape 2 plus haut, à partir d'une escouade (les fusiliers américains, par exemple).
2. **Ouvrez son soldat dans Blender.** Sur la page de la nouvelle escouade, sous **Son propre modèle**, cliquez sur **Changer dans Blender**. Blender s'ouvre avec le soldat et ses os, chacun là où le jeu le place. Pas encore Blender ? **Obtenir Blender (gratuit)** l'installe ; **Choisir Blender…** montre au Studio où il est.
3. **Modifiez-le, ou posez votre propre modèle sur ses os.** Pour le modifier, éditez-le là. Pour un modèle à vous : importez-le avec **File > Import** dans la même scène et placez-le sur le soldat ; cliquez sur votre modèle, **Maj+clic** sur les os, puis **Ctrl+P > With Automatic Weights**. Supprimez le soldat du jeu si vous ne le gardez pas.
4. **Envoyez-le.** Cliquez sur **Envoyer au R.U.S.E. Studio** en haut de Blender.
5. **Ramenez-le.** Dans le Studio, cliquez sur **Ramener le modèle**. Chaque soldat de l'escouade porte votre modèle : le fusilier, le soldat au bazooka et les petites figurines vues de loin. **Tester en jeu** le montre.

Bon à savoir :
- Vos fichiers Blender restent dans le dossier de votre mod : `Documents\RUSE 2.0\Mods\<votre mod>\blender\<nom de l'unité>\`. Ils ne sont pas emballés dans votre mod quand vous le partagez. Le prochain **Changer dans Blender** repart de ce que vous avez envoyé en dernier.
- Si des points de votre modèle n'ont pas d'os (les poids automatiques de Blender en oublient quelques-uns), la page dit combien : ils ne bougent qu'avec les hanches du soldat. Peignez-les sur un os dans **Weight Paint**, puis renvoyez.
- Une escouade avec un **Uniforme personnalisé** : votre modèle prend la place de l'uniforme (sa peinture reste dans votre mod), et **Utiliser le modèle de l'unité copiée** rend l'uniforme.
- Vous avez déjà un .glb fait sur les os du soldat du jeu ? **Importer un modèle…** le prend tel quel.
- Le modèle que porte votre escouade est gardé dans le dossier de votre mod sous `files\models\<nom de l'unité>.glb`, une fois en place.

## Ses animations, changées dans Blender

**Changer dans Blender** ouvre le soldat avec toutes les animations que joue l'escouade (debout, marche, course, tir, mort…), chacune nommée d'après ce qu'il y fait, suivie du nom du jeu : `Course, en visant (fusilier_course_vise)`.

1. **Choisissez-en une.** En bas de Blender, l'Action Editor les liste : choisissez celle à changer. **Espace** la joue.
2. **Posez les os.** Cliquez sur un os, appuyez sur **Ctrl+Tab** pour le Pose Mode, **R** pour le tourner (**G** le déplace), puis **I** pour garder la pose à cette image. Faites-le à chaque image que vous changez : Blender passe tout seul d'une pose gardée à la suivante.
3. **Envoyez-la.** Cliquez sur **Envoyer au R.U.S.E. Studio** : toutes les animations partent, changées ou non.
4. **Ramenez-la.** Cliquez sur **Ramener le modèle**. Le Studio dit lesquelles sont revenues changées : elles sont désormais propres à cette escouade, et RUSE Decoy les montre sous **Cette unité seulement**. Toutes les autres escouades, et chaque animation que vous n'avez pas touchée, restent celles du jeu.

Bon à savoir :
- Le jeu joue les animations à 30 images par seconde, et Blender les ouvre ainsi. Une animation s'ouvre avec la durée que lui donne le jeu ; allongez-la ou raccourcissez-la dans Blender et elle revient ainsi.
- Une animation faite dans Blender (la copie d'une autre, renommée) revient aussi, mais aucune action ne la joue encore : le Studio le dit. Une animation renommée compte comme nouvelle, et celle qu'elle était se joue comme avant.
- Les os sur lesquels aucun point du soldat ne repose (le point de la bouche du canon, la main de la seconde arme) peuvent être animés, mais les poids automatiques de Blender les laissent de côté.
- Vérifié avec Blender 4.5 et les tests du Studio ; pas encore essayé en jeu.

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
- Essayé en jeu avec les propres modèles du jeu (le Sherman, deux avions, une escouade de fusiliers, les servants d'un
  canon) : pas encore avec un modèle venu d'ailleurs, un autre char à tourelle, une tourelle qui fait un tour complet,
  ou un avion qui copie une unité sans hélices.

En ligne de commande : `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. Avec `--move`, il est ajusté comme le Studio
l'ajuste : `--move 50 0 -10` le déplace de 50 vers l'avant et de 10 vers le bas depuis là où il est ajusté (avant,
droite, haut), et `--move 0 0 0` l'y laisse. Sans `--move`, la commande l'ajuste toujours à l'ancienne, sa tourelle sur
la tourelle de l'unité copiée.

**Suivant :** [[Exporter et partager|Exporter-et-partager]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Import-a-Model]]
