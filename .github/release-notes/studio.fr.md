**RUSE Studio, un aperçu pour les moddeurs.** Parcourez les unités du jeu dans n'importe laquelle de ses dix langues,
modifiez-les dans un mod à vous et testez-le en jeu. Votre installation Steam n'est jamais modifiée.

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
