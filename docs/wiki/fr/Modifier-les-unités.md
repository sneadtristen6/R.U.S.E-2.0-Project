# Modifier les unités

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio et un mod · **Durée :** autant que vous voulez

## Trouver une unité

L'onglet **Unités** liste chaque unité et chaque bâtiment. Réduisez la liste avec :

- la zone **Rechercher** (les noms de code ou les noms que voient les joueurs, dans n'importe laquelle des dix langues du
  jeu : le bouton de langue en haut). Chaque mot que vous tapez doit correspondre ; des **#étiquettes** réduisent la
  liste (`#us`, `#germany`, `#air`, `#armor`, `#new` pour les nouvelles unités de votre mod ; tapez `#` pour les voir
  toutes), et vos recherches récentes sont gardées ;
- les puces **Type** et **Nation** ;
- le menu des **types** : à quoi sert l'unité, comme QG, argent, usines, forts et leurres pour les bâtiments, ou l'usine
  qui construit une unité.

## Changer une valeur

1. Cliquez sur l'unité. Ses valeurs sont listées par section (prix, blindage, vitesse, armes...).
2. Tapez une nouvelle valeur. Elle est enregistrée dans votre mod tout de suite ; la valeur du jeu s'affiche à côté.
3. **Annuler** à côté d'une valeur remet la valeur du jeu.

## Les drapeaux : ce qu'est une unité et ce qu'elle peut faire

Les drapeaux sont des interrupteurs marche/arrêt, numérotés de 0 à 104, qui disent au jeu ce qu'est une unité (un avion,
un camion, de l'infanterie, un bâtiment...) et ce qu'elle peut faire (entrer dans les bois, voir tout autour, ne tirer
que sur ordre...). Sur la page d'une unité, ils s'affichent comme des puces, chacune avec son nom : survolez-en une pour
voir exactement ce qu'elle fait, comment s'en servir et à quel point nous en sommes sûrs. La croix en retire un ;
**Ajouter un drapeau…** en ajoute un, triés par ce à quoi servent les drapeaux.

**Guide des drapeaux : tous expliqués** (sous les drapeaux) ouvre la liste entière, avec une zone de recherche. Pour
chaque drapeau, il dit :

- **ce qu'il est et ce qu'il fait** dans le jeu ;
- **Comment s'en servir** ;
- **Degré de certitude :** *essayé en jeu*, *d'après les unités du jeu* (ce que les unités du jeu qui l'ont ont en
  commun), *attendu, pas encore essayé*, *le jeu le pose lui-même* (il les active et les désactive pendant qu'il tourne :
  dans la liste d'une unité, ils ne font rien), ou *inutilisé*.

**Le Studio vérifie les drapeaux de chaque unité** chaque fois que vous les changez, et de nouveau avant que le jeu
démarre :

- **Les plantages connus arrêtent la construction**, pour que le jeu ne soit jamais lancé avec eux. La page de l'unité
  dit pourquoi et propose la correction (**Retirer 62**, **Ajouter 100**) :
  - 62 (camion) ou 63 (camion de construction) sur tout ce qui n'est pas un camion : le jeu plante au début de la
    partie ;
  - 99 (avion de reconnaissance) sur un avion avec des armes, sans 100 (chasseur) : le jeu plante quand l'avion est
    envoyé attaquer. Utilisez la case **Rôle** (Reconnaissance garde ses attaques) ou ajoutez 100 ;
  - 59 (transport de parachutistes) sur autre chose qu'un avion, ou sur un avion sans unité à larguer.
- **Ce qui devrait abîmer une unité est un avertissement**, pas un arrêt : 2 (avion) sur une unité terrestre, 4
  (bâtiment) ou 49 sur une unité, 6 ou 76 sur une unité qui devrait bouger (elle reste immobile), 42 (infanterie) sur un
  véhicule, ou retirer 43 (son équipe la compte) ou 22 (le joueur peut lui donner des ordres).

Des drapeaux utiles, essayés en jeu : retirez **11, 21 et 55** ensemble pour laisser un véhicule entrer dans les bois ;
**1** donne un tir indirect à n'importe quelle unité ; **71** voit tout autour ; **77** ne tire que sur ordre.

**Des types de drapeaux à vous** (Studio 0.9.8.8) : **Créer ou changer des types de drapeaux…** sous les drapeaux d'une
unité crée un ensemble nommé de drapeaux du jeu, chacun mis sur **Activé** ou **Désactivé**, avec une ligne sur ce à
quoi il sert. **Donner un type de drapeaux…** sur n'importe quelle unité active et désactive ces drapeaux d'un coup ; le
retirer remet les drapeaux de l'unité comme ils étaient. Changez un type et chaque unité qui l'a change aussi. Le jeu
n'agit que sur ses propres drapeaux, donc un type combine ce qu'ils font déjà. Pas encore essayé en jeu.

## Créer une nouvelle unité

Une nouvelle unité commence comme une copie d'une unité du jeu, avec son propre nom, pour que vous puissiez la changer
sans toucher l'originale. L'onglet Unités a deux boutons en haut : **Modifier une unité** (la liste, puis les valeurs de
l'unité et Blender) et **Nouvelle unité (importer un modèle)**. Avec **Nouvelle unité**, choisissez l'unité de départ,
donnez-lui un nom, et cliquez sur **Créer** ; puis changez-la comme n'importe quelle autre. Ou choisissez l'unité et
prenez **Nouvelle unité…** sur sa page.

## Changer l'apparence d'une unité

La page de l'unité montre son **Modèle 3D** : faites glisser pour le tourner, utilisez la molette pour zoomer.

- **Repeindre dans Blender :** cliquez sur **Ouvrir dans Blender** (Blender est gratuit ; si le Studio ne le trouve pas,
  la page propose **Obtenir Blender (gratuit)** et **Choisir Blender…** pour lui montrer où est `blender.exe`). L'unité
  s'ouvre avec ses images, prête à être peinte sur le modèle. Peignez, puis cliquez sur **Récupérer** : votre
  peinture va dans votre mod. Vu en jeu, de près et de loin.
- **Sa carte dans le menu de construction :** tournez et zoomez le modèle 3D jusqu'à ce qu'il rende bien dans le cadre
  en pointillés, puis **Utiliser cette vue comme carte**. **Carte du jeu** la reprend. Vu en jeu. Sur une nouvelle unité,
  la carte est la sienne : l'unité qu'elle copie garde son image.
- **Sa propre copie du modèle :** une unité dessinée avec le modèle du jeu partage sa peinture avec chaque unité dessinée
  avec lui. **Lui donner sa propre copie du modèle** (sur sa page) fait le même modèle avec ses propres textures : alors
  **Ouvrir dans Blender** ne peint que cette unité. Marche pour les nouvelles unités et celles du jeu.
- **L'uniforme d'une escouade :** les soldats du jeu d'une même nation portent tous une seule image (ceux des US : ses
  GI, Rangers et parachutistes, et les équipages de ses canons et véhicules), donc l'**Uniforme par défaut** n'est pas
  repeint ici. Choisissez **Uniforme personnalisé** pour donner à l'escouade le sien, puis peignez-le dans Blender. Vu en
  jeu.
- **Se déplace en :** le camion en lequel une escouade ou un canon se change sur les routes : celui du jeu, celui d'une
  autre nation, ou une copie d'un camion que vous avez faite et repeinte. Vu en jeu.
- **Un modèle à elle (nouvelles unités) :** **Importer un modèle…** fait entrer un modèle 3D venu de Blender ou de
  n'importe quel outil 3D. Voir [[Importer un modèle|Importer-un-modèle]]. Une unité du jeu garde son modèle : sa page a
  **Nouvelle unité à partir de celle-ci…** pour créer la nouvelle unité sur laquelle le modèle va.

## Blindage

**Blindage** sur la page d'une unité choisit un des niveaux de blindage du jeu (les chars ont de 1 à 5, le chiffre sur le
bouclier). L'unité se bat avec lui, et sa carte et son menu de construction l'affichent. Changer un nombre à l'intérieur
de la partie blindage elle-même faisait se battre une unité avec une valeur pendant que sa carte en affichait une autre,
donc cette partie ne peut plus être changée directement. Vu en jeu.

## Recherche : de quoi elle est une amélioration

La page d'une unité a une case **Amélioration et recherche** : l'unité dont elle est une amélioration (**Amélioration
de**), ses propres améliorations, et son prix et son temps de recherche. Choisissez une autre unité du même menu de
construction, ou **Aucune : une unité à part entière** pour qu'elle soit achetable dès le début. Les temps de recherche
peuvent se taper en secondes ou en minutes (le sélecteur à côté).

Quand vous retirez une unité depuis laquelle d'autres sont recherchées, **Réglages > Recherche** décide de ce qui se
passe : **M'avertir d'abord** (par défaut), **Refuser**, ou **Les relier à nouveau** à son propre parent. Une unité
restée recherchée depuis une unité disparue le dit ici et dans la barre de vérification, et la construction s'arrête
dessus jusqu'à ce que vous en choisissiez une autre.

Une unité affichée dans son menu de construction doit être recherchée depuis une unité qui y est affichée aussi : celle
que vous pouvez construire vient d'abord, la recherche après. Une unité affichée à une date de bataille où l'unité depuis
laquelle elle est recherchée est cachée arrête le jeu quand ce menu de construction s'ouvre (vu en jeu), donc la barre de
vérification la nomme et la construction s'arrête dessus. Affichez de nouveau l'autre unité, ou choisissez une autre
unité depuis laquelle la rechercher, ou aucune. **Nations > Tout masquer** le fait pour vous : une unité restée recherchée
depuis une unité cachée devient achetable dès le début.

## Unités des autres époques

366 unités de la Première Guerre mondiale à aujourd'hui, chacune un modèle 3D gratuit d'un autre créateur, peuvent être
ajoutées à votre mod comme nouvelles unités, à leur taille réelle et derrière une recherche : voir
[[Unités des autres époques|Unités-des-autres-époques]].

## Armes et munitions

La case **Armes** sur la page d'une unité liste ses armes (l'Arme 1 est le canon principal). **Comment marchent les armes
et les munitions**, en dessous, reprend aussi ces étapes.

1. **Chaque arme tire une munition.** La liste à côté choisit laquelle : n'importe quelle munition du jeu, triée par
   type (AP, HE, antiaérienne, mitrailleuses, bombes, roquettes...), ou une copie que vous avez faite. Sa lueur de bouche
   et son son viennent avec elle.
2. **La munition décide de ce que fait l'arme :** ses dégâts, sa portée, sa cadence de tir et ce qu'elle peut toucher.
   **Ouvrir la munition** pour voir et changer ses nombres.
3. **Changer une munition change chaque unité qui la tire** (sa page les liste). Pour une seule unité : sur la page de
   la munition, cliquez sur **Copier cette munition…**, changez la copie, puis choisissez la copie dans la liste de
   l'arme. Le curseur **Portée** d'une arme demande la même chose : cette unité seulement, ou chaque unité avec cette
   munition.
4. **Touche** (sous une arme) choisit le sol, les avions ou les deux. La case **Rôle** d'un avion règle sa façon
   d'attaquer (plus bas).
5. **Ajouter ou retirer une arme n'est pas encore possible :** les armes sont liées aux animations du modèle, et nous
   n'en sommes pas encore là.

**Son nom en jeu** (sur la page d'une munition, Studio 0.9.8.8) : ce que le jeu appelle la munition, son **Nom**
(Calibre moyen, MG 42) et son **Type** (Obus perforant). Tapez de nouveaux mots et enregistrez : toutes les langues les
affichent jusqu'à ce que vous en changiez une à part avec **Changer le texte…** ; **Mots du jeu** retire les vôtres.
Une munition copiée porte le nom que vous lui donnez. Pas encore essayé en jeu.

**Classe d'arme** (sur la page d'une munition, Studio 0.9.8.17) : la part de ses dégâts que la munition inflige à
chaque type de cible. **Nouvelle classe d'arme…** ouvre un nombre pour chacun : bâtiments et fortifications, avions,
parachutistes en descente, infanterie, véhicules légers (transports), blindage 1 à 5, et camions de construction.
1 = dégâts complets, 2 = le double, 0,5 = la moitié, et 0 signifie qu'elle ne peut pas du tout attaquer cette cible.
**Enregistrer la classe** donne à la munition sa propre copie de la table des dégâts du jeu : les dégâts des autres
munitions ne bougent pas, mais chaque unité qui tire cette munition la reçoit (pour une seule unité, utilisez d'abord
**Copier cette munition…**). Le bouton devient alors **Modifier cette classe d'arme…** ;
**Revenir à la classe du jeu** retire la copie, et supprimer une munition copiée emporte sa classe avec elle. Vu en
jeu : des escouades de fusiliers dont la munition avait reçu des nombres contre les chars ont tiré sur des chars avec
leurs fusils et les ont endommagés. Le bouton lui-même n'a pas encore été cliqué dans le Studio.

**Vitesse du tir :** la vitesse du projectile d'une munition et sa traînée décident du moment où le coup arrive : un tir
plus lent touche plus tard, et une cible en mouvement est visée en avance, du temps de vol (connu par le fonctionnement
du jeu ; pas encore essayé dans un test).

## Changer le rôle d'un avion (Studio 0.9.8.5)

La page d'un avion a une case **Rôle** : **Chasseur**, **Chasseur-bombardier**, **Bombardier** ou **Reconnaissance**. Sa
façon de voler et d'attaquer, la façon dont les joueurs ordinateur l'utilisent et ses mots dans le menu de construction
changent avec.

- **Bombardier :** un bombardier lâche ses bombes sur une passe en ligne droite, et seulement depuis une soute à bombes.
  Choisissez d'abord des bombes pour une de ses armes (Armes, plus bas), puis faites-en un Bombardier : ses bombes vont
  dans une soute à bombes copiée sur celle d'un bombardier du jeu, et vous pouvez les y changer. C'est la correction pour
  un chasseur-bombardier à qui on avait donné des bombes de tapis et qui ne lâchait rien. Vu en jeu.
- **Reconnaissance :** un avion avec des armes reste capable d'attaquer (la case dit **Reconnaissance, en
  gardant ses attaques**) et reçoit la vue des éclaireurs. Vu en jeu avec un Stuka et un ME109.
- Un avion de parachutistes garde son rôle. **Annuler** à côté de la case rend le rôle du jeu, ses bombes là où elles
  étaient.

## Faire d'un véhicule un véhicule de reconnaissance (Studio 0.9.8.5)

La case **Rôle** d'un véhicule terrestre : **Reconnaissance** lui donne la vue des voitures de reconnaissance (bien plus
loin que celle d'un char), la façon dont les joueurs ordinateur les utilisent, leurs mots dans le menu de construction,
et il peut entrer dans les bois. Il reste aussi solide et armé qu'il l'est. Vu en jeu avec un Panzer IV.

## Ce que touche une arme (Studio 0.9.8.5)

Sous chaque arme, **Touche** choisit **Le sol**, **Les avions**, ou **Le sol et les avions**. Les avions : l'arme tire une
copie de sa munition qui touche les avions (et ne fait rien au sol). Les deux : elle garde sa munition et reçoit une
deuxième arme à côté pour les avions, comme les canons antiaériens du jeu en portent une pour chacun. Un char qui tire
sur des avions est vu en jeu ; un canon d'avion réglé pour ne toucher que le sol ne fait pas encore de dégâts.

## Le tester

**Tester en jeu** construit le mod et lance R.U.S.E. Cherchez l'unité là où elle est construite (son usine) dans une
bataille (menu principal : **BATAILLES**, puis une carte).

**Suivant :** [[Exporter et partager|Exporter-et-partager]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Edit-Units]]
