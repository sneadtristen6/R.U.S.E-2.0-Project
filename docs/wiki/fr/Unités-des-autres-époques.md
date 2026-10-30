# Unités des autres époques

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.9.8.2 ou plus récent, et un mod · **Durée :** une minute ou deux par unité

366 unités de la Première Guerre mondiale à aujourd'hui se trouvent à côté de celles du jeu dans l'onglet **Unités** :
des chars et des avions de 14-18, de 39-45+, de la Guerre froide et modernes, tous dans un même jeu. Chacune est un modèle
3D gratuit d'un autre créateur (CC BY), déjà ajusté au jeu, avec les marques de sa nation, et crédité. Aucune n'est dans
votre mod tant que vous ne l'ajoutez pas.

## Obtenir les unités d'une époque

1. Dans l'onglet **Unités**, choisissez une époque au-dessus des types : **14-18**, **39-45+**, **Guerre froide** ou
   **Moderne** (**Vanilla**, ce sont les unités du jeu, la liste de toujours).
2. La première fois, le Studio dit combien d'unités l'époque a et quelle est sa taille, avec **Télécharger les unités
   14-18** (ou celles de cette époque). Il les télécharge depuis le GitHub du projet, vérifie chaque fichier avant qu'il
   serve, et les liste.

   | Époque | Unités | Téléchargement |
   |---|---|---|
   | 14-18 | 61 | 232 Mo |
   | 39-45+ | 32 | 198 Mo |
   | Guerre froide | 149 | 996 Mo |
   | Moderne | 124 | 709 Mo |

3. Une époque téléchargée se met à jour toute seule quand des unités plus récentes sont mises en ligne : le Studio le dit
   et les récupère.

Les unités de l'époque se filtrent comme celles du jeu : type (terrestre ou aérien), nation (la Chine aussi), type
d'unité, et la zone de recherche.

## En ajouter une à votre mod

1. Cliquez sur une unité. Sa page montre l'image de son modèle et son créateur : **Modèle par** le créateur, la licence,
   et un lien vers l'endroit où il l'a partagé.
2. Remplissez le formulaire :
   - **Nom de la nouvelle unité** (affiché dans toutes les langues).
   - **Partir de** : l'unité du jeu dont elle prend les valeurs au départ (vitesse, blindage, armes, façon de jouer).
     Celle qui est suggérée est la première ; n'importe quelle unité de son type peut être choisie.
   - **Prix** (à chaque date de bataille).
   - **Taille** : 1, c'est aussi long que l'unité de départ. La suggestion est sa taille réelle (sa largeur réelle,
     l'envergure d'un avion, à l'échelle du jeu) ; n'importe quoi de 0.05 à 20. Faites glisser le curseur, ou cliquez sur
     un de ses points nommés : **Minuscule**, **Taille du jeu** (1 : aussi long que l'unité de départ, la taille à
     laquelle le jeu dessine ce type d'unité), **Taille réelle** et **Énorme**. Les avions modernes à leur taille réelle
     sont bien plus grands que les avions de 39-45 du jeu (un J-16 est aussi long qu'un Lancaster).
   - **Menu de production** : la nation et l'usine où elle s'achète.
   - **Recherchée depuis** : l'unité depuis laquelle elle est recherchée, ou **Aucune : achetable dès le début**, avec
     son **Prix de recherche** et son **Temps de recherche** (tapez le temps en secondes ou en minutes : le sélecteur à
     côté).
3. Cliquez sur **Ajouter à mon mod**. C'est maintenant une nouvelle unité de votre mod : **Ouvrir sa page** pour changer
   n'importe laquelle de ses valeurs, son modèle ou sa carte, comme pour n'importe quelle unité. **La retirer de mon mod**
   la supprime de nouveau.

## Changer sa taille plus tard

Sur la page de l'unité, **Son propre modèle** a le même curseur : choisissez une taille et cliquez sur **Redimensionner**
(le modèle est de nouveau ajusté depuis son propre fichier, rien à choisir). **Tous les avions de mon mod** (ou les
unités terrestres) les fait tous d'un coup : **Taille du jeu**, **Taille réelle**, **Plus petits** (d'un cinquième) ou
**Plus grands** (d'un quart). Le jeu lit le modèle d'une unité quand il se charge, donc une taille ne peut pas changer
pendant que vous jouez : la nouvelle taille se voit à partir de la construction suivante (Tester en jeu).

## Les chaînes de recherche

Une unité peut être recherchée depuis n'importe quelle unité du menu de construction de sa nation, y compris les propres
unités d'époque de votre mod : ajoutez un char de la Guerre froide, puis un char moderne recherché depuis lui. Les unités
de 14-18 et de 39-45+ peuvent être achetées tout de suite ; celles de la Guerre froide et modernes commencent recherchées
depuis une unité qui convient (le formulaire dit laquelle il suggère, et pourquoi).

Quand vous retirez une unité depuis laquelle d'autres sont recherchées, **Réglages > Recherche** décide de ce qui se
passe :

- **M'avertir d'abord** (par défaut) : le Studio liste les unités recherchées depuis elle, avec **La retirer quand
  même**.
- **Refuser** : l'unité reste, et le message dit comment changer les autres d'abord.
- **Les relier à nouveau** : chacune est recherchée depuis le propre parent de l'unité retirée à la place, à son propre
  prix et en son propre temps (ou devient achetable dès le début).

Une unité restée recherchée depuis une unité disparue le dit dans sa case **Amélioration et recherche** et dans la barre
de vérification, et la construction s'arrête dessus jusqu'à ce que vous choisissiez une autre unité, ou aucune.

## Crédits

Le créateur de chaque unité d'époque est crédité : sur sa page, et dans le `CREDITS-era-units.md` de votre mod, que le
Studio écrit quand vous en ajoutez une. Gardez ce fichier avec votre mod : la licence des modèles le demande. La liste
complète des créateurs est sur la
[version des unités d'époque](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/era-units).

## Ce qui a été vu en jeu

Vu : elles se chargent tout de suite, avec leurs propres cartes dans les menus de construction ; les onglets de recherche
et une chaîne d'améliorations ; leurs propres modèles ; leurs tailles. Pas encore essayé : les canons
tractés (l'importateur ne sait pas encore les ajuster, donc ils montrent le modèle de l'unité de départ), et si le jeu
compte le temps de recherche en secondes.

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Units-From-Other-Eras]]
