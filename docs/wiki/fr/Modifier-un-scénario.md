# Modifier un scénario

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.9.8.4 et un mod · **Durée :** quelques minutes

Un **scénario**, c'est ce avec quoi une carte commence : les zones de capture, le point de départ de chaque camp, et les
unités et bâtiments déjà sur le terrain. Une carte en a plusieurs : un pour chaque façon dont le jeu la fait jouer.

## Les trois façons du jeu de jouer une carte

Ce sont les boutons du menu principal de R.U.S.E. :

| Bouton | Ce que c'est |
|---|---|
| **BATAILLES** | Une partie libre contre l'ordinateur sur une carte, avec les joueurs que vous choisissez (d'autres jeux appellent ça une escarmouche). |
| **OPERATION** | Une courte mission avec des objectifs fixés, sur une situation toute prête. |
| **CAMPAGNE** | L'histoire, chapitre après chapitre. |

Le Studio nomme chaque scénario d'après le bouton qui le fait jouer, et une ligne dorée sous le menu des scénarios dit
exactement où : par exemple **Dans le jeu : Batailles › Le jour J (6 joueurs)**.

## Choisir le scénario

Au début de la barre de l'écran de la carte, choisissez **Scénario** (à côté de **Carte**). Les éléments propres à la
carte (terrain, bâtiments, arbres, routes) s'affichent estompés et ne peuvent pas être saisis par erreur ; revenez à
**Carte** pour les changer. Puis choisissez le scénario dans le menu en haut. Les points de départ s'affichent comme des
piliers à la couleur de chaque camp, les apparitions comme des losanges blancs, les zones comme des surfaces ombrées.

## Déplacer un point de départ ou une apparition

1. Du côté **Scénario**, cliquez sur **Déplacer**.
2. Cliquez sur le pilier ou le losange, puis cliquez là où il doit aller.
3. Pour le remettre là où le jeu l'avait, cliquez de nouveau dessus et choisissez **Remettre**.

## Ajouter des unités : une seule ou toute une formation

1. Du côté **Scénario**, cliquez sur **Ajouter une unité**.
2. Choisissez le genre (Bâtiments, Terrestre, Infanterie, Aérien), puis le type, puis l'unité dans la liste (groupée par
   nation).
3. Choisissez **Pour qui ?** Pour une Opération ou un chapitre de campagne, la liste donne les camps propres à ce
   scénario, tirés de sa mission : **Joueur** (vous : le camp 0 dans la campagne) et les camps de l'**Ordinateur**, chacun
   avec son pays, plus **Neutre**. Le nombre entre parenthèses est ce qui est enregistré. Une carte de **BATAILLES** ne
   prend que des unités neutres (le jeu la lance sans liste d'équipes, donc les unités d'un joueur n'y apparaîtraient
   jamais).
4. **Combien :** 1, 2, 4, 6, 8 ou 10.
5. Pour plus d'une, choisissez une **formation** : ligne, colonne, coin, carré ou cercle. Elle est tournée vers le haut de
   l'écran : tournez la vue pour la viser. **Espacement** règle les mètres entre les unités.
6. Des anneaux sur la carte montrent où chaque unité se tiendra. Cliquez pour les placer.

Une unité que vous avez ajoutée peut être déplacée comme n'importe quelle apparition, ou retirée avec **Retirer**.

## Plus de joueurs sur une carte (jusqu'à 8)

Chaque joueur commence sur un **point de départ** de son équipe, un par joueur : dans un 3v3, les équipes 1 et 2 ont
chacune les places 1 à 3. Un 4v4 demande la place 4 dans les deux.

1. Choisissez le scénario que le jeu fait jouer en ligne (sa ligne dorée dit **Batailles**), puis dans la barre cliquez
   sur **Scénario**.
2. **Joueurs** (à droite) montre le nombre de joueurs de la carte, celui du jeu marqué *(jeu)*. Choisissez le nouveau
   nombre, 8 au plus. La ligne en dessous nomme chaque point de départ qui manque encore, par ex. *équipe 1, place 4*.
3. Cliquez sur **Ajouter un départ de QG**, choisissez l'**équipe**, puis cliquez sur un terrain dégagé là où ce joueur
   commence, loin des autres. Il prend la place suivante de l'équipe, et sa caméra et son intro à un coéquipier.
4. Quand la ligne dit **Chaque joueur a un point de départ**, cliquez sur **Tester en jeu** et ouvrez **BATAILLES** : la
   carte est listée avec son nouveau nombre, par ex. *(8) Cotentin (4v4)*.

Un point de départ que vous avez ajouté se déplace avec **Déplacer**, ou s'en va avec **Retirer**. Plus de 8 : non, le
salon du jeu a 8 places (essayé le 2026-10-02).

> [!NOTE]
> Nouveau, pas encore vérifié en jeu : dites-nous dans les [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions)
> comment se passe une partie à 8 joueurs.

## Une carte vierge : placer le QG de chaque joueur

Une carte commencée en **Terrain vierge** ou **Océan vierge** (avec **Dupliquer la carte** dans l'onglet Cartes) n'a rien
de la carte copiée, pas même ses QG. **Le QG de chaque joueur** (du côté Scénario) liste chaque QG dont la carte a
besoin : cliquez sur **Placer**, puis sur le terrain où il va. **Tester en jeu** attend que chaque joueur ait un QG.

**Taille de la carte** (Studio 0.9.8.7) agrandit ou rétrécit une nouvelle carte vierge, une bande à la fois : appuyez
sur **+** d'un côté pour ajouter une bande de terrain le long de ce côté, ou sur **−** pour en retirer une, puis sur
**Donner cette taille**. Pas encore essayé en jeu.

> [!WARNING]
> Les deux cartes vierges sont encore buggées : utilisez-les à vos risques, et dites-nous ce que vous trouvez.

## Secteurs

**Secteurs** (du côté Scénario) change les secteurs du scénario, les zones sur lesquelles les cartes de ruse sont jouées.
Une carte vierge commence sans aucun : c'est vous qui les faites.
- **Formes :** faites glisser un point d'angle pour déplacer une frontière (les secteurs qui la partagent bougent
  ensemble). Double-cliquez sur une frontière pour ajouter un point ; clic droit sur un point pour le retirer. **Nouveau
  secteur :** tracez un cadre sur le terrain. **Aucun secteur :** tracez un cadre là où aucun secteur ne doit être.
  **Supprimer le secteur** donne tout son terrain aux secteurs qui l'entourent.
- **Peindre :** choisissez un secteur, puis faites glisser sur le terrain pour le peindre ; « Aucun secteur » retire le
  terrain de tous les secteurs.
- **Partir de zéro secteur** ou **Partir des secteurs de la carte** ; **Annuler** reprend le dernier changement.
- **Créer les secteurs** découpe toute la carte en secteurs à peu près aussi larges que l'indique **Secteurs d'environ**
  (les cartes du jeu ont des secteurs de 1 à 3 km de large), avec des frontières sinueuses ; **Autre découpage** les
  découpe autrement. Puis faites glisser les angles ou peignez pour les remodeler.

Vu en jeu : des secteurs peints sur une carte vierge, un nouveau secteur tracé sur Le jour J et éclairé seul par une carte
de ruse, du terrain hors de tout secteur (un trou sur la table de la carte qu'aucune carte de ruse n'éclaire). Les fines
lignes que le Studio découpe pour qu'un secteur reste d'un seul tenant n'ont pas encore été essayées en jeu.

## Les dépôts de ravitaillement de cette carte

Choisissez un dépôt de ravitaillement pour lui donner plus de camions (plus de camions, plus d'argent dedans), ou
utilisez **Tous les dépôts ici** : multipliez les camions de chaque dépôt (**fois leurs camions**) ou donnez-leur à tous
le même nombre (**camions chacun**), puis **Appliquer**. **Revenir à ceux du jeu** l'annule. Pour changer toutes les
cartes d'un coup, utilisez **Dépôts sur les cartes** dans **Réglages de l'IA et des joueurs**
([[Économie, IA et plus|Économie-IA-et-plus]]). Les dépôts avec plus de 1 000 camions demandent le Launcher 0.4.8.4 ou
plus récent.

## Une mission à elle

Une nouvelle Opération ou un nouveau chapitre de campagne peut jouer sa propre mission, avec des objectifs, des
événements et des mouvements de caméra : [[Créer une mission|Créer-une-mission]].

## Voir vos unités en jeu

1. Cliquez sur **Tester en jeu** (en haut du Studio). Le Studio construit votre mod dans la copie moddée du jeu
   (`RUSE-Instances\Modded game` sur le disque de votre jeu, ou le dossier que vous avez choisi dans les Réglages : une
   pour tout le PC, celle du Launcher aussi) et lance R.U.S.E. depuis celle-ci. Le message en bas dit quoi ouvrir, par
   exemple **BATAILLES > Le jour J**.
2. Dans le menu principal du jeu, cliquez sur ce bouton (**BATAILLES** pour une bataille), puis choisissez la carte
   (**Le jour J**).
3. Préparez la partie comme d'habitude et lancez-la. Vos unités apparaissent là où vous les avez placées.

> [!NOTE]
> Lancer R.U.S.E. depuis Steam lance le jeu sans votre mod. Utilisez **Tester en jeu** (ou **Jouer** dans le Launcher).

> [!NOTE]
> Quel point de départ revient à chaque joueur du salon dans une bataille est encore en test. Dites-nous ce que vous
> trouvez dans les [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Suivant :** [[Exporter et partager|Exporter-et-partager]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Edit-a-Scenario]]
