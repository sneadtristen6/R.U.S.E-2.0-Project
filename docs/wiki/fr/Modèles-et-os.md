# Modèles et os

> **Il vous faut :** RUSE Studio 0.9.8.20 ou plus récent, un mod avec une nouvelle unité, et Blender (gratuit) pour
> changer des os · **Durée :** 10 minutes de lecture

Les soldats, les chevaux et toute créature bougent dans R.U.S.E. parce que leur modèle 3D a des **os**. Cette page dit
ce que sont les os, comment le jeu s'en sert, et ce que veut dire chaque encadré sur les os de la page d'une unité, et
quoi en faire. Un char tourne sa tourelle et ses roues sans animation : cette page parle donc surtout de soldats, de
chevaux et de créatures.

## Ce que sont les os

- Un **modèle** est une coque faite de points, avec des images peintes dessus.
- À l'intérieur, comme un squelette, il y a des **os** : un bras, un avant-bras, une main, la tête, chaque jambe d'un
  cheval. Chaque os pend à un autre (la main à l'avant-bras, l'avant-bras au bras), jusqu'au premier os.
- Chaque point de la coque suit un os, ou quelques-uns : les points d'une manche suivent le bras. La part avec
  laquelle un point suit chaque os est son **poids**.
- Une **animation** fait bouger les os, image après image, et la coque les suit. C'est ainsi qu'un soldat marche, vise
  et tombe.
- Dans Blender, les os d'un modèle sont un seul objet, appelé **armature**.

## Comment le jeu s'en sert

- Le jeu bouge les os d'un modèle **selon leur place dans sa liste d'os**, pas selon leurs noms. Une animation faite
  pour un modèle ne va donc qu'à un modèle qui a les mêmes os, dans le même ordre.
- Certains os ont un rôle : un tir part d'un os à la bouche de l'arme, le haut du corps se tourne vers sa cible à un
  os de la colonne, une arme est montrée et cachée sur un os, une tourelle ou une roue tourne sur un os. La page de
  l'unité nomme chacun de ceux qui manquent à votre modèle (voir **Est-ce que cela marchera en jeu ?** plus bas).
- Un soldat joue **deux animations à la fois** : une sur la moitié haute de son corps (viser, tirer) et une sur la
  moitié basse (marcher, courir). Un cheval et son cavalier aussi : voir **Ses deux moitiés** plus bas.
- On n'a pas vu le jeu animer un modèle de plus de 64 os.

## Deux sortes de modèles

| | Sur les os du soldat du jeu | Avec ses propres os |
|---|---|---|
| **Ce que c'est** | Un soldat changé dans Blender, ou un modèle à vous posé sur les os d'un soldat | Un cheval, un cheval et son cavalier, toute créature, fait dans Blender sur des os à vous |
| **Comment le faire** | **Ouvrir dans Blender** sur la carte de l'escouade : chaque soldat s'ouvre avec ses os (voir [[Ouvrir dans Blender|Ouvrir-dans-Blender]]) | Dans Blender, puis **Importer un modèle…** sur la carte de l'escouade (voir [[Importer un modèle|Importer-un-modèle]]) |
| **Ses animations** | Celles du jeu, comme le soldat | Les siennes, venues de son fichier |
| **Ses deux moitiés** | Celles du jeu : rien à choisir | C'est vous qui les choisissez (le Studio propose l'os) |
| **Sa taille et sa place** | Comme vous l'avez fait dans Blender, sur ses os | Comme dans son fichier |

La page dit de laquelle il s'agit. Sur un modèle posé sur les os du soldat du jeu : « Votre modèle est sur les os du
soldat du jeu : il garde les deux moitiés du jeu, rien à choisir. » Sur un modèle avec ses propres os : « Il a ses
propres os : » et combien. L'**Escouade à cheval générique** (onglet **Unités**, **39-45+**) est une escouade avec ses
propres os : voir [[Unités des autres époques|Unités-des-autres-époques]].

## Où la page les montre

Sur la page d'une nouvelle unité, tout ce qui touche aux os est dans **Apparence et mouvements** :

| Encadré | Où | Ce qu'il vous dit |
|---|---|---|
| **Ses os et ses animations** | La ligne **Sons et animations**, **Plus** | Combien d'os a le modèle, et chaque animation avec sa durée et le nombre d'actions de l'unité qui la jouent (un modèle avec ses propres os) |
| **Ses deux moitiés** | La ligne **Sons et animations**, **Plus** | Où le modèle se partage entre sa moitié haute et sa moitié basse |
| **Ses animations** | La ligne **Sons et animations**, **Plus** | Quelle animation l'unité joue pour chaque chose qu'elle fait : voir [[Animations des unités|Animations-des-unités]] |
| **Est-ce que cela marchera en jeu ?** | La ligne **Modèle**, **Plus** ; sur la page d'une escouade, **Plus d'options** sous les soldats, puis **Le modèle de chaque soldat** | Ce qui, dans le modèle, pourrait arrêter le jeu ou avoir l'air faux, et comment le corriger |
| Points sans os | Au même endroit que **Est-ce que cela marchera en jeu ?** | Combien de points du modèle ne suivent aucun os |

## Ses deux moitiés

Le jeu joue deux animations à la fois sur un soldat : une sur sa **moitié haute** (viser, tirer) et une sur sa
**moitié basse** (marcher, courir). Un cavalier vise et tire pendant que son cheval court : le cavalier est la moitié
haute, le cheval la moitié basse.

- Un modèle sur les os du soldat du jeu garde les moitiés du jeu : la page dit « rien à choisir ».
- Un modèle avec ses propres os se partage à **un os** : cet os et tous les os en dessous forment la moitié haute,
  tous les autres la moitié basse.

Pour le choisir :

1. Sur la page de l'unité, dans **Apparence et mouvements**, cliquez sur **Plus** sur la ligne **Sons et animations**.
2. Sous **Ses deux moitiés**, la liste **La moitié haute commence à** montre d'abord ce que propose le Studio, marqué
   « (proposé) ». Le Studio propose le premier os du cavalier sur un cheval monté (**bip01** sur l'Escouade à cheval
   générique), sinon le premier os nommé spine (comme un soldat), sinon l'os où le squelette se divise pour la première
   fois.
3. La plupart des modèles vont bien avec cette proposition : laissez-la. Pour la changer, choisissez un autre os dans la
   liste. C'est enregistré tout de suite, et se voit dans le jeu après la prochaine construction (**Tester en jeu**).
4. Sous la liste, la page compte les os de chaque moitié, et **Quel os va où** liste chaque os du modèle, marqué
   moitié haute ou moitié basse.
5. Pour revenir à la proposition, choisissez de nouveau la première ligne de la liste.

Un autre partage que celui proposé n'a pas encore été essayé dans le jeu.

## Les poids : quel os suit chaque point

Quand vous posez un modèle à vous (ou un casque, un sac, une arme) sur les os d'un soldat, Blender doit savoir quel os
suit chacun de ses points. Voici les étapes de Blender lui-même.

**Votre modèle sur un soldat, chaque point suivant les os les plus proches :**

1. Sur la carte de l'escouade, cliquez sur **Ouvrir dans Blender** : Blender s'ouvre avec les soldats, chacun sur ses
   os.
2. Dans Blender, importez votre modèle avec **File > Import** et placez-le sur le soldat.
3. Cliquez sur votre modèle, puis **Maj+clic** sur les os du soldat : les os en dernier.
4. Appuyez sur **Ctrl+P** et choisissez **With Automatic Weights**. Blender calcule les poids pour vous.
5. Supprimez ce que vous ne gardez pas (la forme du soldat du jeu, si votre modèle prend sa place), mais gardez ses os.
6. Cliquez sur **Envoyer au R.U.S.E. Studio** en haut de la vue 3D de Blender, puis sur **Ramener mes changements** dans
   le Studio.

**Une pièce rigide qui ne suit qu'un os (un casque sur la tête) :**

1. Dans Blender, cliquez sur le casque, puis **Maj+clic** sur les os du soldat.
2. Appuyez sur **Ctrl+Tab** pour le Pose Mode, et cliquez sur l'os de la tête.
3. Appuyez sur **Ctrl+P** et choisissez **Bone**. Le casque bouge maintenant avec la tête, et lui seul le reçoit quand
   vous ramenez vos changements.

**Des points sans os.** Les poids automatiques de Blender oublient parfois quelques points. La page dit alors « {n}
point(s) de votre modèle n'ont pas d'os : ils ne bougent qu'avec les hanches du soldat. » Pour corriger :

1. **Ouvrir dans Blender** à nouveau.
2. Cliquez sur votre modèle, puis passez le mode de Blender (en haut à gauche de la vue 3D) de **Object Mode** à
   **Weight Paint**.
3. Dans les propriétés du modèle (le triangle vert), **Vertex Groups** a un groupe par os : choisissez l'os que ces
   points doivent suivre.
4. Peignez sur les points.
5. **Envoyer au R.U.S.E. Studio**, puis **Ramener mes changements**.

## Est-ce que cela marchera en jeu ?

Le Studio vérifie un modèle sur des os par rapport aux animations qu'il joue et aux pièces et tirs de l'unité qu'il
copie. La construction du mod vérifie encore, avec tous vos changements. Un problème ne vous bloque jamais : il dit ce
qui se passera, et comment le corriger.

**Où :** la page d'une nouvelle unité, **Apparence et mouvements**, la ligne **Modèle**, **Plus**. Sur la page d'une
escouade : **Plus d'options**, sous les soldats, puis **Le modèle de chaque soldat**.

Quand tout va bien, il dit : « Rien trouvé qui arrêterait le jeu : chaque animation qu'il joue a ses os, et chaque os
dont ses pièces et ses tirs ont besoin est là. » (avec le nombre d'os).

### Ce que veut dire chaque réponse

Chaque problème dit trois choses : ce qui ne va pas, ce que le jeu en fait, et comment le corriger. La ligne du milieu
est l'une de celles-ci :

| La page dit | Ce que cela veut dire | Que faire |
|---|---|---|
| Cela peut arrêter le jeu : c'est arrivé lors d'un test. | Le jeu s'est arrêté ainsi lors d'un de nos tests. | Corrigez avant de tester. |
| Cela peut arrêter le jeu (pas encore essayé en jeu). | On s'attend à ce que le jeu s'arrête. | Corrigez avant de tester. |
| Le jeu la joue, mais le résultat sera faux (pas encore essayé en jeu). | Ce ne seraient pas les bons os qui bougeraient. | Corrigez, ou testez et regardez. |
| L'unité combat toujours, mais ses tirs ne se verront pas : c'est arrivé lors d'un test. | Elle fait des dégâts, mais aucun tir ne se voit. | Ajoutez l'os que la page nomme. |
| Pas encore essayé en jeu : le jeu risque de ne pas l'animer. | Plus d'os que le jeu n'a été vu en animer. | Fusionnez ou supprimez des os. |
| Cela marche quand même, mais ce n'est peut-être pas ce que vous voulez. | Une remarque sur ses deux moitiés. | Vérifiez **Ses deux moitiés**. |

### Chaque problème et sa correction

**Des animations qui ne vont pas aux os du modèle.** La page dit combien d'animations, pour combien d'actions, et
pourquoi elles ne vont pas : « Elles bougent {a} os et votre modèle en a {b}. » (ou « n'en a que {b} »), ou autant d'os
« avec d'autres noms », ou « dans un autre ordre ». Ces animations ont été faites pour d'autres os.

- Si l'unité joue les animations du jeu sur votre modèle : donnez à ces actions des animations propres à votre modèle.
  **Importer un modèle…** apporte chaque animation du fichier de votre modèle, et vous choisissez celle que joue chaque
  action sous **Ses animations** ([[Animations des unités|Animations-des-unités]]).
- Si ce sont les animations de votre modèle, faites pour un autre modèle : refaites-les dans Blender sur les os de ce
  modèle, puis importez le modèle à nouveau.

**Un os dont l'unité a besoin.** Par exemple : « Fusiliers : les tirs partent d'un os nommé Fx_Tir_01, et votre modèle
n'en a pas. » (ou : le haut du corps s'y tourne vers la cible, une arme y est montrée et cachée, une pièce y est tenue,
une tourelle ou une roue y tourne, le corps y repose, un canon tracté s'y accroche). Pour ajouter l'os dans Blender :

1. Ouvrez le modèle dans Blender : **Ouvrir dans Blender** avec **Ses os** coché (voir
   [[Ouvrir dans Blender|Ouvrir-dans-Blender]]), ou votre propre fichier Blender.
2. Cliquez sur les os (l'armature) et appuyez sur **Tab** pour l'Edit Mode.
3. Appuyez sur **Maj+A** : un nouvel os apparaît là où se trouve le curseur 3D de Blender.
4. Appuyez sur **F2** et tapez exactement le nom que dit la page (par exemple `Fx_Tir_01`). Si votre modèle a cet os
   sous un autre nom, renommez plutôt celui-là.
5. Dans les propriétés de l'os (l'icône d'os), sous **Relations**, mettez dans **Parent** l'os avec lequel la pièce
   bouge : pour un tir, l'os avec lequel l'arme bouge.
6. Appuyez sur **G** et déplacez le nouvel os là où la pièce doit être : pour un tir, au bout du canon de l'arme.
7. Appuyez de nouveau sur **Tab**, cliquez sur **Envoyer au R.U.S.E. Studio**, puis sur **Ramener mes changements** (ou
   exportez votre propre fichier et cliquez sur **En importer un autre…**). **Est-ce que cela marchera en jeu ?**
   vérifie de nouveau le modèle.

**Trop d'os.** « Votre modèle a {n} os. On n'a pas vu le jeu animer un modèle de plus de 64 os. » Dans Blender,
fusionnez ou supprimez des os jusqu'à en avoir 64 ou moins, puis ramenez le modèle.

**Le partage.** « Le partage à {bone}, le premier os de votre modèle, met tous les os dans la moitié haute : les
animations de la moitié basse (marcher, courir) ne bougent rien. » : choisissez un os plus bas sous **Ses deux
moitiés**, là où commence le haut du corps. « L'os choisi pour le partage, {bone}, n'est plus dans votre modèle : il se
partage donc à {used}. » : choisissez de nouveau l'os.

**Le deuxième modèle d'une escouade sur d'autres os.** « Son modèle a ses propres os, qui ne sont pas ceux du modèle de
vos fusiliers : il joue donc ce qu'il jouait dans l'unité copiée, fait sur les os du soldat du jeu, ce qui peut arrêter
le jeu. » Le modèle d'un soldat à l'arme lourde doit être sur les mêmes os que celui des fusiliers pour jouer leurs
animations : faites le sien à partir du modèle des fusiliers dans Blender, puis importez-le sur sa ligne. Retirer le
modèle des fusiliers retire aussi le sien.

## Faire un modèle avec ses propres os dans Blender

1. **Ses os :** votre modèle sur une armature avec des os à vous, nommés comme vous voulez, et ses poids
   (**Ctrl+P > With Automatic Weights**, plus haut).
2. **Ses animations :** une action par animation (dans Blender, **Dope Sheet > Action Editor**). Nommez chacune pour ce
   qu'elle montre : **stand** (ou **idle**), **walk** et **run** (ou **gallop**) au moins ; **fire**, **aim**,
   **reload**, **hit**, **death**, **crouch**, **look**, **flee** et **grenade** sont connus aussi. Un nom comme
   **t_fire** (ou **hr_t_fire**) ne se joue que sur la moitié haute, et **b_run** (ou **hr_b_run**) que sur la moitié
   basse : ceux d'un cavalier et de son cheval.
3. **Exportez-le :** **File > Export > glTF 2.0**, format **glTF Binary (.glb)**, avec **Animation** coché.
4. **Importez-le** sur une nouvelle escouade : voir [[Importer un modèle|Importer-un-modèle]].
5. **Vérifiez sa page :** **Ses os et ses animations** (chaque animation est arrivée, et combien d'actions jouent
   chacune), **Ses deux moitiés**, **Ses animations**, **Est-ce que cela marchera en jeu ?**
6. **Tester en jeu.**

Vous l'avez changé ensuite dans Blender ? Importez-le de nouveau : chaque action garde son animation tant qu'une
animation de ce nom est encore dans le fichier.

## Ce qui a été essayé dans le jeu

- L'Escouade à cheval générique, faite ainsi (des fusiliers et un soldat au bazooka à cheval, un modèle avec ses
  propres os) : ils tirent, voyagent comme eux-mêmes sur les longs trajets, et chaque cheval tombe avec son cavalier
  (novembre 2026).
- Un soldat d'escouade changé dans Blender sur les os du soldat du jeu, avec des points pondérés là-bas (novembre 2026).
- Pas encore essayé dans le jeu : un autre partage que celui proposé, et chaque problème que la page marque « pas encore
  essayé en jeu ».

Toujours bloqué ? Demandez sur le [Discord](https://discord.gg/h54t5baNsC), ou voyez
[[Quand quelque chose ne va pas|Quand-quelque-chose-ne-va-pas]].

**Suivant :** [[Animations des unités|Animations-des-unités]] · [[Ouvrir dans Blender|Ouvrir-dans-Blender]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Models-and-Bones]]
