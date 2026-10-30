# Économie, IA et plus : les outils de LittleGroove

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.9.8.1 ou plus récent, et un mod · **Durée :** autant que vous voulez

Le RUSE-Mod-Manager de LittleGroove avait des outils que le Studio n'avait pas. Ils sont dans le Studio maintenant, chacun
dans votre propre mod : un changement y est enregistré tout de suite, et les fichiers du jeu ne sont jamais touchés.

## L'onglet Réglages de l'IA et des joueurs

Un onglet en trois parties : **Réglages des joueurs**, **Règles du jeu** et **Joueurs ordinateur**.

### Réglages des joueurs

L'argent de départ et les revenus, les dépôts de ravitaillement (l'argent par camion, les camions par convoi, le temps
entre deux convois), les limites de production, et les cartes de ruse avec lesquelles chaque camp commence. Un changement
vaut pour tous les modes de jeu ; là où le mode Nucléaire a sa propre valeur, il a sa propre case. Les dépôts de
ravitaillement et les bâtiments administratifs sont des bâtiments : leur prix, leur temps de construction et leur
résistance sont dans l'onglet **Unités**.
Vu en jeu : l'argent de départ et les cartes de ruse au début.

**Dépôts sur les cartes** (sous Dépôts de ravitaillement) : donnez plus de camions, donc plus d'argent, à chaque dépôt de
ravitaillement, sur **Toutes les cartes** ou **Une carte :** à vous de choisir. Multipliez les camions de chaque dépôt
(**fois leurs camions**) ou donnez-leur à tous le même nombre (**camions chacun**). La ligne au-dessus dit ce que contient
un dépôt avec vos valeurs. Un dépôt auquel vous avez donné ses propres camions dans l'onglet Cartes les garde. Jouez les
mods avec plus de 1 000 camions par dépôt avec le Launcher 0.4.8.4 ou plus récent. Vu en jeu (les dépôts de la carte Le jour J
avec 500 camions ; les autres cartes trois fois les leurs).

### Règles du jeu

Toutes les autres règles que le jeu garde pour tous les joueurs, par groupes : bataille et reddition, population,
déplacement et routes, tir et cibles, unités livrées à elles-mêmes, dégâts et clouage, bois et vue, avions, cartes de ruse
en action, le contrôleur de partie, la pose des bâtiments, le jeu classé en ligne, contours et flèches, effets à l'écran,
les couleurs des camps et des secteurs (un sélecteur de couleur chacune), et pour finir quelques valeurs dont l'usage
n'est pas encore connu. Chacune dit ce qu'elle fait et ce que le jeu a. Pas encore essayé en jeu.

### Joueurs ordinateur

Comment jouent les joueurs ordinateur. Un joueur ordinateur mélange trois jeux de valeurs : **Défaut**, sa difficulté et
son profil (tous deux choisis dans le salon du jeu) ; choisissez-en un pour voir et changer ses valeurs : quand il
commence à attaquer, quelle force il attend d'avoir, comment il défend, les unités qu'il préfère, et ses cartes de ruse.
Chaque valeur peut être changée dans chaque jeu : une valeur qu'un jeu ne liste pas compte pour 0 dans le jeu, et lui
donner un nombre l'ajoute à votre mod. En dessous, ce qui vaut pour tous les joueurs ordinateur (la valeur d'armée qui
le fait attaquer, ses leurres...).
Vu en jeu : une carte de ruse retirée du menu, une autre déplacée dedans, la durée d'une carte, et quand Facile commence
à attaquer. Le reste pas encore essayé en jeu.

**Scripts des cartes et des missions**, en dessous : les scripts que le jeu fait tourner sur ses cartes (les chapitres de
la campagne, les défis, les Opérations), affichés en Python pour être lus. **Copier** en copie un.

## La case Amélioration et recherche d'une unité

Sur la page d'une unité : l'unité dont elle est une amélioration (**Amélioration de**), ses propres améliorations, et
son prix et son temps de recherche. Choisissez une autre unité, ou **Aucune : une unité à part entière**. Voir
[[Modifier les unités|Modifier-les-unités]].

## L'onglet Toutes les valeurs et fichiers

Deux parties, choisies avec l'interrupteur en haut de la liste.

**Toutes les valeurs :** n'importe quel objet et n'importe quelle valeur du jeu, changés dans votre mod : ajoutez ou
retirez une valeur, créez ou supprimez un objet, donnez à une valeur de texte ses propres mots. Pas encore essayé en jeu.

**Fichiers :** n'importe quel fichier dans les archives du jeu : choisissez une archive, puis un fichier pour le voir tel
qu'il est (une image, un tableau de texte, un script de mission...). **Enregistrer une copie…** l'enregistre à part ;
**Le remplacer par un de mes fichiers…** met le vôtre dans votre mod ; **Ajouter un de mes fichiers à cette archive…** en
ajoute un nouveau. Votre mod ne garde que ce que vous changez, jamais une copie du fichier du jeu. Pas encore essayé en
jeu.

## Missions et cartes

Les scripts d'une mission peuvent être changés, et le Studio vérifie si elle est dans les menus, si chaque fichier dont
elle a besoin se charge, et ses textes ; elle peut être montée ou descendue dans son menu. Sur une carte : les noms des
villes et des collines, les points et zones nommés, et le nom et l'orientation d'un élément de la carte. Des **Notes**
peuvent être gardées sur une unité, une valeur ou un joueur ordinateur. Pas encore essayé en jeu.

## Dans le Launcher : Convertir un ancien mod

Un ancien mod qui se présente sous forme d'archives du jeu, fait pour être copié dans le dossier du jeu, devient un mod
que votre bibliothèque fait jouer à côté des autres : voir [[Installer et jouer|Installer-et-jouer]].

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Economy-AI-and-More]]
