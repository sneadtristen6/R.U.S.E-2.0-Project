**RUSE Studio, un aperçu pour les moddeurs.** Parcourez les unités du jeu dans n'importe laquelle de ses dix langues,
modifiez-les dans un mod à vous et testez-le en jeu. Votre installation Steam n'est jamais modifiée.

**0.9.8.9:** des téléchargements sur plus de PC, et une lecture d'images plus sûre.

- **Corrigé, signalé par un joueur :** sur un PC dont Windows n'a pas le certificat avec lequel les téléchargements de GitHub sont vérifiés et ne peut pas le récupérer, les téléchargements échouaient (« unable to get issuer certificate »). Les téléchargements du Studio (ses mises à jour, les patchs du jeu, les modèles des unités d'époque et les textures en ligne de Map Paint) essaient maintenant aussi avec la liste de certificats de Firefox, qu'il emporte.
- **Des images plus sûres :** la bibliothèque avec laquelle le Studio lit les images (Pillow) passe en version 13.0.0, avec ses corrections contre des fichiers d'image piégés qui pouvaient faire planter l'application, épuiser sa mémoire, ou pire.
- **Un code plus strict :** les 12 avertissements de la vérification de code de GitHub sur ce projet sont traités. Quand le Studio affiche ses pages dans votre navigateur, elles n'ouvrent que ses propres fichiers, vérifiés d'une façon que cette vérification reconnaît ; les téléchargements demandent TLS 1.2 ou plus récent, comme avant ; et la lecture des erreurs de routes d'un test échoué reste rapide sur n'importe quel message. Rien d'autre ne change dans le fonctionnement du Studio.

**0.9.8.8:** un écran de départ et un tableau des bâtiments, des bâtiments à vous, RUSE Decoy pour les sons et les animations, chaque règle du jeu dans un onglet, et R.U.S.E. 2.0 en or.

- **Un écran de départ :** reprendre votre mod, en commencer un nouveau, ou le passer (même toujours). Les étapes d'un nouveau mod : son nom, chaque nation garde ses unités ou part vide, la recherche (celle du jeu, aucune ou la vôtre), le tableau des bâtiments, puis ce que le mod changera. Vu en jeu.
- **Le tableau des bâtiments :** les bâtiments de chaque nation en rangées des unités que leurs menus de construction offrent, dans l'ordre du jeu. Mettez-y une unité (de la nation, la copie d'une unité d'une autre nation, une unité d'époque), glissez-la le long d'une rangée ou vers un autre bâtiment, retirez-la, ou faites-la rechercher depuis l'unité sous laquelle elle va. La page de chaque unité dit où elle est construite. Vu en jeu.
- **Ajouter un bâtiment… :** une copie d'un bâtiment du jeu qui fait les mêmes unités, ou un bâtiment avec ses propres unités et son propre onglet dans la barre de construction, jusqu'à trois par nation. Le deuxième et le troisième demandent un petit patch du jeu pour plus de bâtiments : le Studio le télécharge une fois et ne l'applique qu'à votre copie moddée, jamais au jeu de votre dossier Steam. Vu en jeu.
- **L'apparence propre d'un bâtiment :** sur la page d'un nouveau bâtiment, importez un modèle 3D à la place d'une pièce de l'apparence qu'il copie (le bâtiment principal d'une usine ou d'un QG, ou la pièce choisie), et donnez-lui sa propre image dans le menu de construction. Vu en jeu.
- **Importer un modèle… dans l'onglet Cartes :** un modèle 3D (.glb, .gltf ou .3ds) devient un rocher, un objet, une plante ou un arbre de votre carte, placé comme ceux du jeu, avec une taille et le crédit de son auteur (modèles d'autrui : CC0 ou CC-BY seulement). Les unités le renversent comme ceux du jeu ; avec **Solide** coché, elles le contournent. Vu en jeu.
- **RUSE Decoy, le concepteur de sons et d'animations,** à la place de l'onglet Musique. Chaque son du jeu par type (armes proches et lointaines, impacts, moteurs, ambiances, interface, cartes ruse, voix des unités, radio, répliques des missions avec ce que dit chacune, musique) : écoutez-le, donnez-lui son propre volume (0 à 200 %) ou remplacez-le. Animations : un autre clip à la place d'un clip, un clip plus lent ou plus rapide, un os agrandi ou tourné, ou de la capture de mouvement sur les soldats, depuis une bibliothèque de 3 205 mouvements libres (la base de capture de mouvement CMU et 100STYLE, crédités), chacun téléchargé quand vous le choisissez. La page d'une unité ouvre RUSE Decoy sur ses propres sons et animations. Vu en jeu. Ses messages d'erreur sont en anglais seulement pour l'instant.
- **Réglages de l'IA et des joueurs :** les onglets Économie et IA ne font plus qu'un. Réglages des joueurs : argent et revenu, dépôts de ravitaillement, production et cartes ruse, comme avant. Joueurs ordinateur : chacune de leurs 47 valeurs sur le jeu par défaut, chaque difficulté et chaque personnalité (une valeur que le jeu omet dans un jeu de valeurs montre le 0 que le jeu compte). **Règles du jeu :** 172 autres valeurs du jeu en 16 groupes (bataille et reddition, population, déplacement et routes, tir et cibles, dégâts, bois et couvert, avions, cartes de ruse en action, placement des bâtiments, parties classées en ligne, contours et effets à l'écran, couleurs des joueurs et des secteurs avec un sélecteur de couleur, et d'autres), chacune nommée et expliquée. Pas encore essayé en jeu.
- **Toutes les valeurs et fichiers :** les onglets Toutes les valeurs et Fichiers ne font plus qu'un, avec un interrupteur en haut ; il s'ouvre sur la partie utilisée en dernier.
- **Corrigé :** Toutes les valeurs montrait les nombres d'une couleur dans le mauvais ordre (le jeu garde le bleu en premier) : la couleur de joueur 1, bleue, paraissait orange, et taper le rouge changeait le bleu. Les couleurs se montrent et se saisissent maintenant rouge en premier ; un fichier de mod garde l'ordre du jeu, comme avant.
- **Corrigé : des taches sombres et claires sur les cartes faites par le Studio** (cartes vierges, agrandies, en relief et à secteurs) : l'inclinaison du sol était mal écrite, donc l'herbe et les champs étaient éclairés inégalement. Une carte est bien éclairée une fois construite avec cette version (son sol est refait la première fois). Vu en jeu.
- **Retirer les anciens passages (de DomesticNukes) :** dans les routes de l'onglet Cartes, avec **Retirer les ponts de la carte** activé, **Fermer les passages des anciens ponts** ferme aussi le sol où chaque ancien pont franchissait l'eau et coupe les liens de route qui le traversent : plus rien ne traverse là ; le reste du réseau routier reste. Pas encore essayé en jeu.
- **R.U.S.E. 2.0 en or :** le jeu moddé que construit Tester en jeu s'ouvre sur une scène de bataille avec un moteur qui démarre, et son menu principal, le petit titre de chaque menu, les contours des menus et les écrans de chargement disent R.U.S.E. 2.0 en or. Il est fait sur votre PC à partir des fichiers de votre propre jeu la première fois (quelques minutes une fois, puis gardé). Réglages a une case pour garder le titre du jeu. Vu en jeu.
- **Les lettres du jeu :** le Studio est écrit dans la police des menus du jeu, prise dans votre jeu à chaque démarrage (la police n'est pas fournie avec le Studio).
- **Corrigé, signalé par un moddeur :** un modèle importé sur une nouvelle unité faite à partir du Panther se posait loin de l'unité ; sur des unités faites à partir de 85 autres (le GPF de 155 mm, le SU-85, le Carro Veloce, le StuG III, le M7 Priest...), il était décalé de la tourelle. Le Studio lit maintenant bien où leurs tourelles tournent. Un modèle importé avant garde son ancienne place : utilisez de nouveau Importer un modèle… sur cette unité. Pas encore essayé en jeu.
- **Corrigé, signalé par un joueur :** un modèle aux images JPG ou WebP (la plupart des .glb téléchargés) était refusé ; il s'importe maintenant. Un modèle que l'import ne sait toujours pas lire (maillages compressés, images KTX2) le dit, et comment le corriger dans Blender. Pas encore essayé en jeu.
- **Corrigé, signalé par un joueur :** un char du jeu, ouvert dans Blender et réimporté, gardait sa tourelle fixe. Ouvrir dans Blender nomme maintenant l'os de chaque pièce comme le jeu, et l'import fait tourner une pièce sur l'os de la tourelle avec la tourelle. Un modèle exporté avant garde ses anciens noms : rouvrez-le dans Blender. Pas encore essayé en jeu.
- **Nommez vos munitions :** une munition copiée porte en jeu le nom que vous lui donnez, et la page de chaque munition a **Son nom en jeu** : un nouveau nom ou type, dans toutes les langues à la fois, puis une langue seule. Pas encore essayé en jeu.
- **Des types de drapeaux à vous :** sous les drapeaux d'une unité, **Créer ou changer des types de drapeaux…** crée un type nommé : cochez les drapeaux du jeu qu'il active et désactive. Donnez-le à n'importe quelle unité ; retirez-le et ses drapeaux redeviennent comme avant. Changez un type et chaque unité qui l'a change aussi. Le jeu n'agit que sur ses propres drapeaux : un type combine ce qu'ils font déjà. Pas encore essayé en jeu.
- **La vitesse des tirs bien expliquée :** le guide des nombres disait que la vitesse d'un tir, sa traînée, l'interrupteur « sans physique » et le temps avant le départ n'étaient que de l'apparence. Ils décident quand le coup arrive : un tir plus lent touche plus tard, et une cible en mouvement est visée en avance du temps de vol (d'après le fonctionnement du jeu ; pas encore essayé en test).
- **Chaque erreur en dix langues :** les 35 erreurs du Studio venues avec l'import de modèles et le tableau des bâtiments.
- **Crédits :** le README dit ce que le moteur de LittleGroove fait encore dans le nôtre, ce qui est à nous, et que notre lecteur de textures utilise aussi le codec de ProLution.
- **Encore buggé, à utiliser à vos risques :** les textures de Map Paint, et les deux cartes vierges (Terrain vierge et Océan vierge).

**0.9.8.7:** Rétablir et sélectionner ce qui est placé, placement en Grille / Boîte / Chemin, des cartes vierges plus grandes, et chaque valeur expliquée.

- **Corrigé, signalé par un moddeur :** sur une nouvelle unité faite à partir de 17 des unités du jeu (le Tigre royal, les canons atomiques, le V2...), la case pour changer son modèle n'apparaissait jamais. Le Studio trouve ces modèles maintenant, et s'il n'en trouve pas un, la case le dit au lieu de disparaître.
- **L'onglet IA expliqué :** chaque valeur des joueurs de l'ordinateur dit ce qu'elle fait, en unités simples, et laquelle l'emporte en bataille pour chaque difficulté et profil ; modes, difficultés, profils et unités choisis par leur nom.
- **Chaque valeur expliquée, partout :** Toutes les valeurs, l'onglet Unités, les pinceaux de l'onglet Cartes (taille en mètres, force selon ce qu'elle fait) et l'onglet Musique (quand chaque liste de bataille joue).
- **L'onglet Économie, Normal et Nucléaire à part :** là où les deux modes diffèrent, chacun a ses propres cases. Un changement du seul mode Nucléaire n'a pas encore été essayé en jeu.
- **Rétablir et sélectionner :** Rétablir dans chaque outil de carte (Ctrl+Y ou Ctrl+Maj+Z, et un bouton) ; dans les plateaux Bâtiments et Objets & arbres, sélectionnez ce qui est placé (clic, Maj+clic ou un cadre), faites-le glisser, tournez-le, redimensionnez-le ou supprimez-le, ceux de la carte aussi.
- **Grille, Boîte et Chemin :** placez des rangées d'objets en grille ou en boîte, des bâtiments face aux routes, et des haies, alignements et bandes d'arbres le long d'un chemin, avec couvert.
- **Des cartes vierges plus grandes :** la fenêtre Taille de la carte d'une nouvelle carte vierge ajoute ou retire des bandes de terrain de chaque côté, et Faire les secteurs la remplit de secteurs.
- **Menus et confort :** des lignes de nombres au lieu de curseurs, une recherche avec #étiquettes et vos recherches récentes, des fiches qui s'ouvrent, et des touches à réassigner (Échanger, La prendre, Annuler).
- **Plus sûr :** fermer le Studio avec du travail non enregistré demande d'abord ; une carte avec un nouveau terrain coupé est refusée avant Tester en jeu ; un mod fait avec un ancien Studio est mis à jour après une sauvegarde (Mettre à jour ce mod) ; les résultats de construction gardés restent bons après une mise à jour du Studio.
- **Chaque message dans les dix langues :** les erreurs du Studio et les lignes de la construction.
- **Nouvelle unité** laisse de côté les deux unités sans modèle de départ (le canon SOLO de 57 mm et les parachutistes SOLO).
- Pas encore essayé en jeu : ce qui est placé avec Grille, Boîte et Chemin, les objets déplacés, et une plus grande carte faite dans le Studio.
- **Encore buggé, à utiliser à vos risques :** les textures de Map Paint, et les deux cartes vierges (Terrain vierge et Océan vierge).

**0.9.8.6:** chaque drapeau et chaque nombre des unités expliqués, les outils de carte montrent ce qu'ils ont fait, et les cartes vierges bien dessinées.

- **Les drapeaux des unités expliqués :** chaque drapeau sur la page d'une unité montre son nom, et en le survolant on voit ce qu'il fait, comment s'en servir et à quel point nous en sommes sûrs. **Guide des drapeaux : tous expliqués** liste les 105, avec une recherche. Le Studio vérifie les drapeaux d'une unité : un plantage connu (les drapeaux d'un camion sur autre chose qu'un camion, un avion armé avec le drapeau de reconnaissance sans celui de chasseur) montre sa correction, et le Studio ne lance pas le jeu tant qu'il n'est pas corrigé ; les drapeaux qui devraient casser une unité donnent un avertissement.
- **Chaque nombre expliqué :** survolez le nom de n'importe quel nombre d'une unité ou d'un bâtiment pour voir ce qu'il veut dire ; à côté, sa valeur en unités simples (mètres, km/h, secondes, degrés, $, %), un curseur pour le rendre plus petit ou plus grand que la valeur du jeu (sa valeur de base, de -90 % à +300 %), et où il se place parmi les unités du jeu de son genre. Les vitesses sont dans les km/h du jeu.
- **Comment marchent les armes et les munitions**, pas à pas, dans le cadre Armes.
- **Les outils de carte montrent ce qu'ils ont fait :** Couvert, Découvrir, Ville, Forêt, Bloquer et Ouvrir marquent le sol que chaque trait a parcouru et disent combien de m² ont changé pour les unités, ou que rien n'a changé. Ville marche en vrais mètres et entoure d'abord les bâtiments qu'un clic couvrira.
- **Placer :** les bâtiments, arbres et objets placés montrent leurs vrais modèles (avec un point à leur pied) ; celui choisi apparaît en transparence sous le pointeur avant le clic ; la liste à placer est une grille d'images. Les arbres ne sont plus noirs, et les numéros de secteur se cachent quand la caméra est proche.
- **Cartes vierges** (vu en jeu sur un Terrain vierge) : des ombres sur le sol plat ; ce que vous placez là où la carte copiée avait la mer est dessiné ; le plancher de la caméra suit le nouveau sol.
- **Encore buggé, à utiliser à vos risques :** les textures de Map Paint, et les deux cartes vierges (Terrain vierge et Océan vierge).

**0.9.8.5:** des avions dans n'importe quel rôle, des armes qui touchent les avions, et une bibliothèque pour le pinceau Texture de Map Paint.

- **Le rôle d'un avion** (signalé par un joueur : un chasseur-bombardier à qui l'on donnait les bombes en tapis d'un bombardier volait jusqu'à sa cible et ne larguait rien) : une nouvelle case Rôle sur la page d'un avion en fait un Chasseur, un Chasseur-bombardier, un Bombardier ou un Éclaireur. Son comportement, la façon dont les joueurs de l'ordinateur l'utilisent et ses mots dans le menu de construction changent avec. Les bombes d'un bombardier vont dans une soute (copiée sur celle d'un bombardier du jeu), la seule façon dont le passage d'un bombardier les largue. Vu en jeu : un chasseur-bombardier devenu bombardier largue ses bombes ; un éclaireur qui garde ses armes (un Stuka, un ME109) attaque toujours et a la vue des éclaireurs.
- **Véhicules de reconnaissance :** la case Rôle d'un véhicule terrestre en fait un véhicule de Reconnaissance : la vue des voitures de reconnaissance (bien plus loin que celle d'un char), la façon dont les joueurs de l'ordinateur les utilisent, leurs mots dans le menu de construction, et il peut entrer dans les bois (vu en jeu avec un Panzer IV).
- **Ce qu'une arme touche :** le Touche de chaque arme choisit le sol, les avions, ou les deux (une seconde arme à côté, comme les canons antiaériens du jeu en portent une pour chacun). Vu en jeu : des obus de char tirés sur des avions. Connu : une arme d'avion réglée pour toucher le sol seul ne fait encore aucun dégât.
- **Le pinceau Texture de Map Paint a une bibliothèque :** les textures de sol du jeu (herbe, champs, sable, neige, roche, routes..., par théâtre, avec une recherche), un carré du sol de n'importe quelle carte, vos propres images, et des images gratuites en ligne (Poly Haven et ambientCG, CC0 ; photos aériennes des États-Unis, domaine public), une image téléchargée par clic et gardée dans votre mod avec son crédit. Un curseur Taille, les textures utilisées récemment, et **Détail du jeu de près**, qui pose les décalques du jeu d'une texture du jeu sur le sol que vous peignez. Pas encore vu en jeu ; les téléchargements en ligne pas encore essayés.
- **Les objets placés en terrain dégagé**, loin des villes, des fermes et des bois de la carte, sont maintenant à la portée de l'affichage du jeu, et les grands groupes de nouveaux objets sont rangés comme ceux du jeu (pas encore vu en jeu).
- **Repeindre plus vite :** le sol peint est gardé d'une construction à l'autre, quelle que soit la copie ou le mod qui l'a peint : une carte repeinte de la même façon le reprend en quelques secondes, pas en minutes.
- **Encore buggé, à utiliser à vos risques :** les textures de Map Paint, et les deux cartes vierges (Terrain vierge et Océan vierge).

**0.9.8.4:** vos propres missions, des cartes vierges à construire, et bien plus à personnaliser.

- **Encore buggé, à utiliser à vos risques :** les textures de Map Paint, et les deux cartes vierges (Terrain vierge et Océan vierge).
- **Vos propres missions :** une nouvelle Opération ou un nouveau chapitre de campagne a sa propre mission, côté Scénario de l'écran de carte : camps, objectifs, événements (Quand → Faire : faire venir des unités, déplacer, attaquer, tenir une zone, artillerie, bombardement, parachutistes, messages, argent, victoire, défaite) et mouvements de caméra. Vu en jeu : son mouvement de caméra, les objectifs (une zone, un groupe détruit, un temps), les événements répétés, l'argent, un camp confié à l'ordinateur. Pas encore essayé : les parachutistes, un mouvement de caméra lancé par un événement.
- **Carte | Scénario** sur l'écran de carte : ce qui est de l'autre côté est estompé et ne peut pas être pris par erreur.
- **Cartes vierges :** plus rien de la carte copiée ne s'affiche, et vous placez le QG de chaque joueur (la construction attend qu'ils soient tous placés). Terrain vierge marche aussi pour les Opérations et les chapitres de campagne.
- **Vos propres secteurs :** peignez-les, tirez leurs coins, tracez-en un nouveau en boîte, laissez du terrain sans secteur, supprimez-en un (vu en jeu).
- **Dépôts de ravitaillement :** l'onglet Économie donne plus de camions à chaque dépôt de chaque carte, ou d'une carte (fois, ou un nombre chacun) ; plus de plafond à 1 000 camions.
- **Onglet Nations :** cachez d'un coup toutes les unités d'une nation, montrez-les de nouveau, ou remplissez ses menus avec les unités d'une époque.
- **Modifier un mod installé :** ouvrez n'importe quel mod du Launcher ; celui de quelqu'un d'autre devient une copie à vous sous son propre nom. Les mods RUSE Mod Manager (.rmod) sont convertis pour que leurs valeurs puissent être changées.
- **La vérification du mod en mots simples**, avec un bouton pour corriger chaque problème.
- **Le look propre d'une unité :** sa propre copie de son modèle à repeindre ; les escouades portent l'uniforme par défaut ou un uniforme personnalisé ; choisissez le camion dans lequel une escouade ou un canon roule. L'infanterie s'affiche en 3D et s'ouvre dans Blender.
- **Le blindage** se choisit parmi les niveaux du jeu, pour que la carte montre ce avec quoi l'unité se bat ; **les avions importés** gardent leurs hélices qui tournent et reviennent tournés vers l'avant (les deux vus en jeu).
- **Tailles des modèles sur un curseur** (Minuscule, Taille du jeu, Taille réelle, Énorme : 0,05 à 20), à changer quand vous voulez, tous les avions d'un coup.
- **Plus à changer :** une valeur propre à une difficulté ou un profil d'IA pour une valeur que seul Défaut liste ; des nombres au-delà des curseurs des outils de carte ; des retouches de musique plus fortes et plus longues.
- **Corrigé :** une unité montrée dans un menu mais recherchée depuis une unité cachée arrêtait le jeu : la vérification la nomme et la construction la refuse. Les chars tirent de nouveau à travers les villes effacées, et les unités ne tombent plus dans les trous laissés là où les ponts ont été retirés (vu en jeu).
- **Les téléchargements marchent sur tous les PC :** quand Windows n'a pas encore récupéré le certificat qui sert à vérifier GitHub, le Studio le lui demande, comme un navigateur, puis réessaie (pas encore essayé sur un PC qui avait le problème).

**0.9.8.3:** les copies avec les mods vont où vous le dites.

- **Où vont les copies avec les mods**, dans les Réglages : choisissez le dossier où la copie du jeu avec les mods est
  construite, ou revenez à l'emplacement recommandé, `RUSE-Instances` sur le disque du jeu (la copie y partage les
  fichiers du jeu et est prête en quelques secondes ; sur un autre disque, c'est une copie complète du jeu, plus lente
  et plus grosse). La sauvegarde propre du jeu va à côté. Le prochain Tester en jeu construit au nouvel endroit ;
  l'ancien dossier peut être supprimé à la main. Le Launcher utilise le même dossier.

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
