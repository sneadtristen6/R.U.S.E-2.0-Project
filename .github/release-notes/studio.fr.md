**RUSE Studio, un aperçu pour les moddeurs.** Parcourez les unités du jeu dans n'importe laquelle de ses dix langues,
modifiez-les dans un mod à vous et testez-le en jeu. Votre installation Steam n'est jamais modifiée.

**0.9.8.2:** les unités d'autres époques arrivent : leurs modèles, à leur vraie taille, derrière une recherche.

- **Des unités d'autres époques :** les époques WWI, WWII+, Guerre froide et Moderne de l'onglet Unités ont désormais
  leurs unités : 366, chacune sur le modèle gratuit d'un autre auteur (CC0 ou CC BY), crédité. Chaque époque se
  télécharge dans le Studio quand vous la choisissez, depuis notre GitHub (chaque fichier vérifié : WWI 232 Mo, WWII+
  198 Mo, Guerre froide 996 Mo, Moderne 709 Mo), et se met à jour d'elle-même à mesure que d'autres sont terminées.
  - **À leur vraie taille :** la vraie largeur de chaque unité (pour un avion, son envergure) à l'échelle du jeu ;
    modifiable de 0,2 à 5 fois.
  - **Recherchées comme les unités du jeu :** depuis n'importe quelle unité du bâtiment de sa nation, y compris les
    unités d'époque du mod, pour faire une chaîne (un T-80, puis un T-90M), avec un prix et une durée de recherche.
    Les unités WWI et WWII+ s'achètent directement ; celles de la Guerre froide et Modernes partent d'une recherche
    depuis une unité adaptée.
  - **Leurs propres cartes** dans le menu de construction et à la sélection.
  - Vu en jeu : elles se chargent tout de suite, les onglets de recherche et une chaîne, un Land Rover avec son
    propre modèle, les tailles. Pas encore essayé : les canons tractés (pas encore de canon du jeu auquel les
    ajuster).
- **Importer un modèle… :** un modèle qui commence par une figurine d'équipage a maintenant son propre modèle (les
  jeeps copiées sur le Kübelwagen montraient celui du Kübelwagen) ; les modèles peints en spéculaire-brillance
  gardent leur peinture ; les couleurs données en nombres ne sont plus noires ; les gros modèles s'importent plus
  vite.
- **Une unité recherchée depuis l'unité d'une autre armée** laissait le jeu sur un écran de chargement sans fin :
  **Nouvelle unité…** retire ce lien désormais, et la construction du mod refuse une unité recherchée depuis une
  unité absente ou d'une autre nation, en disant pourquoi et comment corriger.
- **Retirer une unité dont d'autres sont recherchées :** choisissez dans **Réglages > Recherche** d'être averti
  d'abord (par défaut), de refuser, ou de les relier à nouveau à son propre parent ; une unité qui pointe vers une
  unité disparue le montre sur sa page et dans la vérification. Les durées de recherche se tapent en secondes ou en
  minutes (que le jeu les compte en secondes n'est pas encore essayé en jeu).
- **Linux et Steam Deck (via Proton) :** le Studio s'ouvre dans votre navigateur web quand sa propre fenêtre ne le
  peut pas. Pas encore essayé sur Linux : dites-nous ce qu'il en est.

**0.9.8.1:** Les outils de LittleGroove arrivent dans le Studio, avec la musique et les sons, et une nation changée en une autre.

- **Les outils de LittleGroove, repris** de son RUSE-Mod-Manager :
  - **Onglet Économie :** argent de départ et revenus, dépôts de ravitaillement, et les cartes de ruse de départ de
    chaque camp. Vu en jeu : l'argent de départ et les cartes de départ.
  - **Onglet IA :** la façon de jouer des joueurs ordinateur, les unités qu'ils préfèrent et les cartes de ruse ; et les
    scripts de cartes et de missions du jeu, montrés en Python, en lecture seule. Vu en jeu.
  - **Encadré Amélioration** sur la page d'une unité : l'unité qu'elle améliore, ses propres améliorations, le prix et
    la durée de sa recherche.
  - **Onglet Toutes les valeurs :** n'importe quel objet ou valeur du jeu, changé dans un mod : ajouter ou
    retirer une valeur, créer ou supprimer un objet, donner à une valeur de texte ses propres mots.
  - **Onglet Fichiers :** n'importe quel fichier des packs du jeu, visible et enregistrable. Remplacez-en un par un fichier à
    vous ou ajoutez-en un : votre mod ne garde que les changements, chacun vérifié selon son type.
  - **Missions :** changer les scripts d'une mission ; voir si elle est dans les menus, si chaque fichier dont elle a
    besoin se charge, et ses textes ; la monter ou la descendre dans son menu.
  - **Cartes :** noms de villes et de collines, points et zones nommés, nom et orientation d'un objet de la carte.
    **Notes** sur une unité, une valeur ou un joueur ordinateur.
- **Onglet Musique :** chaque morceau selon l'endroit où il joue, chacun remplacé dans un petit éditeur du Studio
  (couper, fondu, volume) ; de nouveaux morceaux ajoutés aux listes de bataille ; les répliques d'une unité sur sa
  page ; le son d'ambiance d'une carte. Vu en jeu : les morceaux, les nouveaux morceaux et les répliques.
- **Faire d'une nation une autre.** Le nouvel onglet **Nations** donne à l'une des sept nations du jeu un nouveau
  nom (dans le salon, et pour son armée) et un nouveau drapeau à partir de n'importe quelle image : la Chine à la
  place de l'Italie, par exemple. Ses unités et ce qu'elles disent se changent comme avant, dans l'onglet Unités et
  sur la page de chaque unité. Vu en jeu : le nouveau nom dans le salon, le nouveau drapeau dans une partie.
- **Des unités d'autres époques :** l'onglet Unités propose les époques WWI, WWII+, Guerre froide et Moderne à côté
  des unités du jeu. Elles n'ont pas encore d'unités : elles arriveront dans une prochaine mise à jour.
- **Nouvelle carte : partir de zéro…** est dans l'onglet Cartes avant qu'une carte soit ouverte.
- **Le sol de Terrain vierge est dessiné pour lui-même.** Une nouvelle carte partie de zéro a un sol fait à partir de
  vos traits de terrain, et non plus le sol de la carte du jeu déplacé : des rivages arrondis de près comme de haut,
  plus de creux au sommet des collines, et les bâtiments et les chars posés exactement dessus. Vu en jeu sur des
  cartes de test.
- **Océan vierge reste, avec un avertissement** sur son bouton : des îles séparées ne sont pas prêtes pour de
  vraies batailles (ci-dessous).

Pas encore essayé en jeu : l'encadré Amélioration, Toutes les valeurs, Fichiers, les outils des missions, les ajouts
aux cartes et les sons d'ambiance.

**Pourquoi il n'y a pas encore de cartes navales.** Nous avons essayé des cartes d'îles pour de vraies batailles avec
des navires, et c'est le jeu lui-même qui bloque :

- Une unité terrestre envoyée vers une île qu'elle ne peut pas atteindre fait planter le jeu.
- Relier les îles par une bande de terre évite le plantage, mais l'ordinateur y envoie alors simplement son infanterie.
- Sans route entre les îles, aucun bâtiment ne peut être placé nulle part.
- Avec les armes du jeu, navires et unités terrestres ne peuvent presque pas se blesser.

Les données de carte seules ne peuvent pas corriger le plantage, donc les cartes navales attendent.

**0.9.8:** une nouvelle carte peut partir de zéro, en terre plate ou en pleine mer, et chaque carte peut avoir ses
propres images dans les menus du jeu.

- **Partir d'une carte vierge.** **Dupliquer la carte** a un nouveau choix, **Partir de** : **Terrain vierge** (une
  terre plate sans rien dessus, sauf les points de départ) ou **Océan vierge** (la mer sur toute la carte). Vérifié en
  jeu.
- **Des images de menu pour chaque carte.** Choisissez un PNG pour l'image de la carte et sa carte 3D dans les menus,
  ou revenez à celles du jeu ; les points de départ blancs sont dessinés là où partent les joueurs de la carte.
  **Créer dans Blender…** ouvre le modèle 3D de la carte elle-même pour les faire, et **Récupérer** les place dans
  votre mod. Vérifié en jeu.

| Avant | Maintenant |
|---|---|
| Une nouvelle carte partait d'une copie complète d'une carte du jeu. | **Dupliquer la carte** peut la faire partir de zéro : Terrain vierge ou Océan vierge. |
| Une nouvelle carte montrait les images de menu de la carte copiée. | **Images du menu…** lui donne les siennes : un PNG à vous ou une image faite dans Blender, avec les points de départ là où partent ses joueurs. |
| Les dépôts, unités, bâtiments et noms de la carte restaient. | **Retirer** en retire un, ou tous les dépôts ou tous les noms d'un coup (vérifié en jeu). |
| Les routes et les ponts de la carte restaient. | Le dock Routes les retire (les tracés des routes disparus : vérifié en jeu). |
| Les secteurs laissaient de côté la mer et les bords de la carte. | **Secteurs sur toute la carte** : toute la carte peut être prise (vérifié en jeu). |
| L'eau d'une carte venait seulement de ses rivières et de sa mer. | **Eau sur toute la carte** : une fine couche, comme la mer peinte d'une carte navale (vérifié en jeu ; les unités dessous pas encore essayées). |
| L'éditeur de carte prenait les apparitions une par une, sous des noms de code. | Tracez un cadre pour les sélectionner comme dans le jeu ; les icônes de la carte montrent ce qui est sélectionné, et combien. |
| Les panneaux de l'éditeur de carte avaient une seule taille. | Chaque panneau flottant se redimensionne, de 40 % à 125 %. |
| Les nouveautés étaient en anglais seulement. | Elles sont dans la langue du Studio. |
| Envoyer un mod à la liste des mods voulait dire écrire son entrée à la main. | **Publier sur la liste des mods** ouvre le formulaire de la liste, déjà rempli, avec une copie .zip prête à y glisser ; chaque export indique qu'il a été fait avec RUSE Studio. |
| Importer un modèle perdait l'ombrage et les parties transparentes du modèle. | Il les garde, et dit ce qu'il a gardé (pas encore vu en jeu). |
| Une unité construite sur une mer asséchée pouvait faire planter le jeu ; une vieille eau de rivière se dressait en murs le long du bord d'une carte ; des phares effacés brillaient encore sur la mer. | Corrigé, chaque point vérifié en jeu. |

Connu : **les cartes navales ne sont pas finies.** Océan vierge se construit et se joue, mais les unités sous son eau
n'ont pas encore été essayées.

**0.9.7:** les très grands mods de carte se construisent maintenant en quelques minutes. Avant, leur construction
prenait très longtemps, et c'est pour cela que cette mise à jour était nécessaire. Et **Exporter le mod…** emporte ce
que la construction a calculé : la première construction d'un tel mod chez un joueur est plus courte.

- **Le mod de carte le plus extrême que nous ayons** (la carte « Le jour J » avec sa mer asséchée : 154 coups
  d'aplanissement, 135 coups de peinture, 33 385 bâtiments effacés) prenait environ quatre heures à construire.
  Maintenant il se construit en **moins de 10 minutes**, sans rien garder d'une construction précédente, et les
  fichiers du jeu sortent identiques. Cela nous a pris environ 15 heures ; où cela bloquait et pourquoi :
  [Comment nous en sommes arrivés là](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here) (en
  anglais). Nous continuons à le rendre plus rapide.

| Avant | Maintenant |
|---|---|
| Une carte remodelée sur des kilomètres pouvait prendre des heures à construire, épuiser la mémoire du PC, ou être refusée comme trop grande pour les déplacements de la carte. | Son sol est remodelé en quelques secondes, ses lits de rivière réparés et son sol peint sur tous les cœurs du PC, et ses déplacements calculés sur deux cœurs de plus pendant la peinture. Chaque étape donne les mêmes fichiers qu'avant. |
| Une mer asséchée restait fermée aux unités. | Un large lit asséché reçoit des zones de déplacement aussi grandes que la place le permet. **Pas encore essayé en jeu :** des unités sur la mer ouverte. |
| Une reconstruction après un petit changement recalculait toute une grande carte. | Ce qui a été fait est gardé : une peinture inchangée prend une demi-seconde, des déplacements inchangés viennent du cache de construction, et un nouveau coup ne repeint que les tuiles qu'il touche. |
| La première construction d'un grand mod de carte chez un joueur recalculait tout. | **Exporter le mod…** met dans le mod ce que la construction a calculé pour les déplacements de la carte (`maps/<map>/solved.bin`). C'est verrouillé avec le fichier du jeu pour cette carte et cela ne contient aucun fichier du jeu. La construction du joueur le prend, vérifie chaque réponse et donne les mêmes fichiers. La peinture du sol et les lits de rivière sont toujours faits sur chaque PC. |
| Importer un modèle n'apparaissait que sur la page d'une nouvelle unité : difficile à trouver. | L'onglet Unités commence par deux boutons : **Modifier une unité** et **Nouvelle unité (importer un modèle)**. Choisissez l'unité de départ, nommez-la, Créer : sa page s'ouvre sur Importer un modèle. La page d'une unité du jeu a **Nouvelle unité à partir de celle-ci…**. |
| Le drapeau navire (76) disait qu'une unité qui l'a se déplace sur l'eau. | Il dit que l'unité ne se déplace pas du tout, comme un bâtiment (pas encore testé en jeu). |

Connu : **les cartes navales ne sont pas encore au point.** Une mer asséchée ou peinte se construit et se charge, mais
l'eau s'affiche toujours.
