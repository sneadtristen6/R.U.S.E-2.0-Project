**RUSE Launcher 0.4, pour les joueurs.** Il trouve R.U.S.E. via Steam, et **Jouer** construit une copie moddée du jeu
avec vos mods et la lance. Votre installation Steam n'est jamais modifiée.

**0.4.8.20:** Des gardes là où certains ensembles de mods arrêtaient le jeu ; une amélioration faite dans un autre bâtiment garde son unité ; l'éditeur d'ensembles dit pourquoi ; Bug Watch dit pourquoi une construction ou un Jouer a échoué ; le propre soldat d'une escouade, changé dans Blender (Studio) ; les mods avec les nouvelles escouades et animations du Studio ; une unité sans image de carte refusée à la construction.

- **Des gardes là où des mods arrêtaient le jeu :** avec le R.U.S.E. Field Manual et le Balance Overhaul Mod ensemble, le jeu s'arrêtait dès que la base blindée était posée (rapports de plantage de joueurs). Chaque jeu moddé a maintenant une garde sur trois endroits où les scripts du jeu lui-même l'arrêtaient : des cartes de recherche dans la liste d'un bâtiment pour une unité qui est dans un autre bâtiment, une mission qui lance le joueur ordinateur d'un camp joué par une personne, et une mission qui change des unités après que l'une d'elles a été tuée. Une garde ne fait rien sauf là où le jeu se serait arrêté. Testé en jeu avec la base blindée ; les deux gardes des missions ont été testées hors du jeu.
- **Une amélioration faite dans un autre bâtiment garde son unité :** avec les deux mêmes mods, rechercher le T-34 dans la base blindée retirait le T-26 de la caserne, car le jeu retire une unité dès qu'une de ses améliorations est recherchée, où qu'elle soit fabriquée. La construction fait maintenant de cette amélioration une recherche à part et le dit dans un avertissement. Testé en jeu avec l'URSS et l'Italie. Cela change certains ensembles avec le Balance Overhaul Mod, et les ensembles avec le Field Manual avant le Balanced Realism Mod ; l'avertissement nomme chaque unité.
- **Codes de partie :** un ensemble que la construction change ainsi reçoit un nouveau code de partie : chaque joueur d'une partie avec lui a besoin de cette version. Tous les autres ensembles gardent leur code. Après la mise à jour, le prochain **Jouer** ou **Tester en jeu** reconstruit votre jeu tout seul.
- **L'éditeur d'ensembles du Launcher dit pourquoi :** quand il ne peut pas créer ou enregistrer un ensemble (aucun mod coché, ou un mod qui n'est plus dans votre bibliothèque), il le dit maintenant dans l'éditeur, sous ses boutons. Avant, le message allait sur la page de l'ensemble, cachée derrière l'éditeur, et rien ne semblait se passer. **Créer** et **Enregistrer** attendent qu'un mod soit coché. Essayé dans un aperçu de l'écran, pas encore dans le Launcher installé.
- **Vos propres missions (Studio) :** la mission d'une nouvelle carte qui crée des unités d'une nation que la mission copiée ne charge pas reçoit maintenant les packs de cette nation, et ces unités ont leurs modèles (le jeu s'arrêtait quand une telle unité était créée). La vérification des missions refuse aussi un événement qui donne à l'ordinateur un camp joué par une personne. Vérifié en relisant une vraie construction ; pas encore essayé en jeu.
- **Le propre soldat d'une escouade (Studio) :** la page d'une escouade reçoit **Son propre modèle** avec **Changer dans Blender** : le soldat de l'escouade s'ouvre dans Blender sur ses propres os, et Blender reçoit un bouton **Envoyer au R.U.S.E. Studio**. **Ramener le modèle** le reprend sur les os du soldat du jeu, sans **Uniforme personnalisé**. **Importer un modèle…** fonctionne aussi maintenant sur une unité qui a un **Uniforme personnalisé** : il retire la copie, et **Utiliser le modèle de l'unité copiée** la rend en un clic. Les points que Blender laisse sans os suivent l'os racine, et la page dit combien il y en a. Testé dans le jeu avec deux escouades américaines faites ainsi (l'une avec une tête plus grosse, l'autre avec un nouveau maillage pondéré dans Blender) ; le reste a été vérifié hors du jeu.
- **Les mods faits avec les nouvelles escouades et animations du Studio (Launcher) :** ce Launcher construit les escouades d'un mod avec leurs propres soldats, et ses unités avec leurs propres animations ; un tel mod en a besoin, car un Launcher plus ancien ne peut pas les leur donner. Un mod dont les escouades ont leurs propres soldats reçoit pour cela un petit correctif du jeu, téléchargé une fois et appliqué seulement à votre copie moddée, jamais au jeu dans votre dossier Steam. Pas encore essayé en jeu depuis le Launcher.
- **Une unité sans image de carte (Studio et Launcher) :** une unité montrée dans un menu de construction sans image de carte est maintenant refusée quand le jeu est construit, avec ce qu'il faut changer. Lors d'un test, le jeu s'arrêtait dès son démarrage avec une telle unité (une copie du camion QG montrée dans un menu de construction).
- **Bug Watch dit pourquoi, si vous l'avez coché :** quelle vérification a refusé une construction ou trouvé une erreur (un nom fixe de notre code), jusqu'où est allé un **Jouer** ou un **Tester en jeu**, quels mods de notre liste étaient actifs et combien des vôtres (comptés par type, jamais nommés), les Jouer refusés avant de commencer, et les mises à jour proposées, installées ou échouées. Jamais les mots affichés, un chemin, ni ce que contiennent vos propres mods. Tout cela figure dans l'accord que vous avez accepté (version 3) : il ne vous est donc pas montré de nouveau.
- **Sans changement :** RUSE Guard, un jeu sans mods, la campagne et l'escarmouche.

**0.4.8.19:** RUSE Guard : un jeu construit avec un mod de triche joue maintenant en multijoueur et en coop avec les joueurs qui ont la même construction. Pas encore entièrement pris en charge, et peut-être encore bogué : à utiliser en multijoueur à vos risques.

- **Signalé par un joueur :** deux amis avec le même pack de mods étaient exclus de chaque partie multijoueur, parce qu'un mod du pack (Infinite Supply Depot) porte le badge Triche. RUSE Guard traitait tout jeu construit avec une triche ou un outil de test comme hors ligne uniquement : il quittait chaque partie multijoueur et coopérative au bout de quelques secondes, sans jamais regarder qui d'autre jouait.
- **Ce que nous avons changé :** une seconde après le début d'une partie multijoueur ou coopérative, un tel jeu indique maintenant aux jeux des autres joueurs quelle construction il est : un code court tiré de la version du jeu et des mods, rien sur vous. Vers sept secondes, il décide. Si tous les joueurs ont la même construction (la même version du jeu, les mêmes mods dans le même ordre, les mêmes versions des mods), il l'affiche à l'écran et la partie continue. Si quelqu'un a une autre construction ou aucun mod, il quitte la partie comme avant.
- **Un code de partie pour ces ensembles :** dans le Launcher, un ensemble de mods avec un mod de triche reçoit maintenant un code de partie comme les autres. Le même code veut dire la même construction : comparez vos codes avant de jouer.
- **Chaque joueur a besoin de cette version :** le jeu de chaque joueur de la partie doit être construit par le Launcher 0.4.8.19 ou le Studio 0.9.8.19, ou plus récent. Après la mise à jour, le prochain **Jouer** ou **Tester en jeu** le reconstruit tout seul.
- **Pas encore entièrement pris en charge :** nous l'avons testé dans le jeu avec un seul joueur hébergeant une partie multijoueur contre l'ordinateur, et hors du jeu avec 20 parties simulées de quatre joueurs au plus. Personne n'y a encore joué à deux dans une vraie partie : il peut donc rester des bogues, et vous l'utilisez en multijoueur à vos risques. Essayez-le et dites-nous ce qui s'est passé sur Discord ou GitHub : quel message de RUSE Guard vous avez vu, et si la partie a continué.
- **Inchangé :** un jeu construit sans triche, l'escarmouche contre l'ordinateur et la campagne.

**0.4.8.18:** Une correction en coulisses : la vérification d'une copie moddée liste ce qu'elle trouve dans le même ordre sur tous les systèmes.

- **En coulisses :** la vérification d'une copie moddée (quels fichiers du jeu ont changé après sa construction) liste désormais ce qu'elle trouve dans le même ordre sous Windows et sous Linux. Ce qu'elle trouve ne change pas.

**0.4.8.17:** Les modèles importés se placent là où se tient l'unité, leurs tourelles et hélices à leur propre place ; une munition peut avoir sa propre classe d'arme.

- **Une mise à jour obligatoire :** les versions plus anciennes ne peuvent plus être utilisées. À son ouverture, l'application l'installe d'elle-même, et **Jouer** attend qu'elle soit installée.
- **Les mods avec des modèles importés de la nouvelle sorte :** le Studio ajuste maintenant le modèle importé d'une unité là où se tient l'unité, avec son propre squelette, donc sa tourelle tourne là où se trouve la tourelle du modèle, et les hélices d'un avion tournent là où le modèle les a, autant qu'il en a ; les soldats, l'équipage d'un canon et d'autres avions peuvent aussi prendre des modèles à eux. Jouez ces mods avec ce Launcher ou un plus récent : un plus ancien donne au modèle le squelette de l'unité copiée, donc sa tourelle tourne autour du mauvais point. Les mods faits avant se jouent comme avant. Testé en jeu sur des copies de test construites comme le Launcher construit ; pas encore joué par le Launcher lui-même.
- **La propre classe d'arme d'une munition :** un mod peut maintenant donner à une munition ses propres dégâts contre chaque type de cible (fait sur la page de munition du Studio). Rien n'a changé dans le Launcher pour cela : un tel mod se construit comme n'importe quel autre.

**0.4.8.16:** Dépannage garde les copies du jeu que vous avez faites vous-même.

- **Corrigé : « Les supprimer » dans Dépannage effaçait des copies faites par vous.** Une copie du jeu construite à la main dans le dossier des copies, une copie de test ou une copie de référence comptait comme un reste, et « Les supprimer » l'effaçait pour de bon, pas dans la Corbeille. Toute copie construite ailleurs que la copie moddée de l'application porte maintenant une petite note « à garder », et une copie qui en a une n'est jamais un reste : Dépannage ne supprime que les restes des applications elles-mêmes (copies à moitié construites, celles que d'anciennes versions faisaient par ensemble de mods). Constaté sur notre propre PC le 1er novembre, quand toutes les copies de test y sont parties. Une copie construite avant cette version n'a pas encore de note : reconstruisez-la une fois avec cette version, ou laissez « Les supprimer » tranquille d'ici là.

**0.4.8.15:** Le Jeu d'origine a aussi le titre R.U.S.E. 2.0 doré.

- **Le Jeu d'origine a aussi le titre R.U.S.E. 2.0 doré :** Jouer sur le Jeu d'origine construit maintenant la copie avec mods sans aucun mod et avec le titre doré, puis lance le jeu depuis elle, comme pour un ensemble de mods : la première fois elle se construit, ensuite le jeu démarre aussitôt, sauf si vous avez joué un ensemble de mods entre-temps. RUSE Guard surveille ses parties multijoueurs, comme pour chaque ensemble. Décochez le titre doré dans les Réglages et le Jeu d'origine se lance par Steam comme avant. Votre installation Steam n'est jamais modifiée.

**0.4.8.14:** Les mods qui ont leur propre script de partie se construisent de nouveau.

- **Corrigé : Jouer s'arrêtait pour certains ensembles de mods** avec « RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ... » : quelques mods apportent leur propre script de partie, dont l'en-tête demande plus de place que le script n'en a besoin (parmi eux 1 VS 7 AI, 1 VS 15 AI, Operation Overlord et Sand Box). Le jeu exécute ces scripts sans problème, mais le Launcher les refusait, si bien qu'aucun ensemble contenant l'un de ces mods ne pouvait être construit. Il les lit maintenant comme le jeu.

**0.4.8.13:** Les rapports de plantage du jeu disent ce qui a mené au plantage.

- **Les rapports de plantage du jeu de Bug Watch en disent plus :** si vous avez coché Bug Watch et que le jeu plante, le rapport indique maintenant aussi ce que le jeu essayait de lire ou d'écrire, et jusqu'à 16 endroits du jeu qui ont mené au plantage, lus dans le propre rapport de plantage du jeu sur votre PC, qui ne le quitte toujours jamais. Un rapport qui disait seulement où le jeu s'était arrêté ne pouvait pas montrer pourquoi ; nous pouvons maintenant remonter la piste de plantages comme celui qu'un joueur nous a envoyé cette semaine, et les corriger.
- **L'accord, version 3 :** il liste maintenant ces deux nouveautés parmi ce que contient un rapport de plantage du jeu, et rien d'autre n'y a changé. Comme il a changé, les deux applications vous le montrent encore une fois à leur ouverture.

**0.4.8.12:** Jouer construit de nouveau les jeux moddés.

- **Corrigé : Jouer s'arrêtait pour chaque ensemble de mods** avec « No such file or directory: ...fairplay_watch.bin » : les installateurs des versions 0.4.8.10 et 0.4.8.11 avaient oublié trois fichiers de RUSE Guard, si bien qu'aucun jeu moddé ne pouvait être construit. Ils sont de retour, et une application à laquelle il manque un de ses fichiers ne peut plus être publiée.

**0.4.8.11:** la connexion via Steam aboutit dans les applications ; sous Linux, les programmes d'aide d'une construction démarrent comme sous Windows.

- **Corrigé : la connexion via Steam.** Après votre connexion sur la page de Steam, le Launcher et le Studio attendaient sans jamais demander à notre serveur si c'était fait : la fenêtre arrêtait ses propres vérifications avant la première. Elle vérifie maintenant toutes les quelques secondes et vous connecte dès que Steam le confirme. Essayé dans l'aperçu : la vérification a lieu et la fenêtre vous montre connecté.
- **Les programmes d'aide démarrent à neuf sur tous les systèmes :** les programmes entre lesquels une construction répartit son travail (modèles importés, réparation de la carte, déplacements, eau) démarrent maintenant à neuf sous Linux aussi, comme ils l'ont toujours fait sous Windows. Sous Linux, ils démarraient comme des copies de l'application en cours, ce qui pouvait parfois bloquer une construction, et faisait échouer l'une de nos vérifications. Rien ne change sous Windows ni avec Proton sur le Steam Deck.

**0.4.8.10:** des mods de plus de 4 Go, des listes de construction en groupes, des constructions plus rapides pour les gros mods, le persan et chaque page en 11 langues, des corrections signalées par des testeurs ; et RUSE Guard, notre anti-triche pour les vraies parties multijoueur, avec un code de partie ; Bug Watch, des rapports de plantages et d'utilisation que vous pouvez activer ; la connexion via Steam ; et un accord au premier démarrage.

- **Corrigé, signalé par un joueur : les mods de plus de 4 Go.** Un ensemble de mods dont le jeu moddé dépassait 4 Go ne se construisait plus avec Jouer (« 'I' format requires 0 <= number <= 4294967295 »). Les paquets portent maintenant leur longueur complète, et un paquet de plus de 4 Go est écrit dans une disposition plus large qu'un petit correctif du jeu permet au jeu de lire : téléchargé une fois et appliqué seulement à votre copie moddée, jamais au jeu dans votre dossier Steam. Au-delà de 32 Go, ou pour un seul fichier de plus de 4 Go, la construction le dit clairement. Testé en jeu : des copies de plus de 4 Go, et avec 200, 283 et les 366 unités d'autres époques.
- **Beaucoup de modèles à vous :** le jeu trouve les textures de remplacement d'un paquet grâce à un index, et une construction qui en ajoutait pour des modèles importés l'écrivait mal : avec beaucoup d'unités d'autres époques, le jeu se figeait ou plantait au chargement. Il est maintenant écrit comme le jeu le lit, pour chaque mod qui en ajoute. Testé en jeu avec les 366 unités d'autres époques.
- **Listes de construction en groupes :** un mod avec beaucoup d'unités reçoit la liste de construction de chaque bâtiment en groupes, les lignées du jeu lui-même : 6 unités au plus par groupe et 10 groupes au plus par bâtiment, pour que toute la liste reste à l'écran et que chaque unité puisse être construite. Un mod fait avant qui dépasse ces limites se construit quand même, avec un avertissement. Testé en jeu avec 297 unités d'autres époques en groupes.
- **Constructions plus rapides :** les modèles de vos mods sont gardés d'une construction à l'autre, et les nouveaux sont faits côte à côte sur les cœurs de votre PC. Un mod avec 366 unités d'autres époques prenait environ 18 minutes à construire sur un PC à 8 cœurs ; maintenant environ 5 la première fois et environ 3 ensuite, avec les mêmes fichiers de jeu, octet pour octet.
- **Rapports de testeurs :** un mod d'unités et des changements de carte faits sous un même nom se construisent ensemble (ils arrêtaient Jouer) ; une carte dont les ponts propres sont retirés se construit avec les nouveaux ponts ; les pièces de tourelle et les canons tractés importés se construisent comme le Studio 0.9.8.10 les fait. Les ponts et les pièces de tourelle pas encore essayés en jeu.
- **Vos fichiers :** Retirer envoie un mod de la bibliothèque à la Corbeille, Afficher dans le dossier ouvre un mod là où il est, et les Réglages montrent où vos fichiers sont gardés. Vu dans un aperçu ; pas encore essayé dans la fenêtre de l'application.
- **Le persan et 11 langues :** le persan est la 11e langue des applications, écrit de droite à gauche ; le README, le wiki, ces notes et les écrans d'installation sont dans les 11.
- **Mises à jour obligatoires :** une mise à jour que nous marquons obligatoire s'installe d'elle-même, avec une fenêtre que personne ne peut fermer (les applications à partir de cette version savent lire la marque).
- **Copies possédées seulement :** avant que Jouer ne construise une copie moddée, les applications vérifient que le dossier du jeu est une copie que vous possédez, d'après ce que Steam y a laissé, sous Windows, sous Proton sur le Steam Deck et sous Linux. Si la vôtre ne peut pas être confirmée (une copie en boîte d'avant l'arrivée de R.U.S.E. sur Steam), une fenêtre vous permet d'ouvrir un ticket, et nous vous envoyons un code de déblocage pour ce PC.
- **Discord :** les applications et les pages utilisent une nouvelle invitation qui n'expire pas.
- **Un accord au premier démarrage :** la première fois que le Studio ou le Launcher s'ouvre, il explique ce que fait RUSE Guard et vous demande de l'accepter (c'est obligatoire pour jouer en ligne avec les applications), si vous voulez activer Bug Watch (facultatif), et un nom d'utilisateur que nos développeurs voient avec vos rapports : un # et quatre chiffres y sont ajoutés pour qu'il soit unique, comme Nick#4821. Un seul nom sert aux deux applications. L'accord s'affiche à nouveau quand il change. Vu dans les deux applications. Dans les 11 langues.
- **RUSE Guard :** notre anti-triche, d'après la conception de DomesticNukes. Il ne fonctionne qu'en parties multijoueur et coopératives, jamais en solo, en escarmouche contre l'ordinateur ni dans la campagne. Votre jeu moddé reçoit un **code de partie** à envoyer aux personnes avec qui vous jouez : le même code veut dire le même jeu, la même version, les mêmes mods et versions de mods, pour qu'une partie ne puisse pas se désynchroniser. Un mod qui change les scripts du jeu porte le badge **Exécute des scripts**, et Jouer attend que vous cochiez que vous faites confiance à son auteur ; une triche ou un outil de test porte **Triche** et rend la copie hors ligne uniquement : elle quitte d'elle-même les parties multijoueur et coopératives. Pendant une vraie partie, RUSE Guard compare les noms de vos programmes en cours d'exécution à une liste d'outils de triche connus (les noms seulement ; rien d'autre n'est lu), et ce qu'il recueille est classé sous votre nom d'utilisateur, jamais sous votre compte Steam. Testé en parties multijoueur contre un vrai adversaire ; les preuves arrivent sur notre serveur.
- **Bug Watch (facultatif) :** quand vous le cochez, le Studio et le Launcher comptent ce que vous utilisez et quand quelque chose va mal, les plantages des applications et ceux du jeu, avec les mods qui étaient actifs, et l'envoient une fois par jour à nos développeurs avec votre nom d'utilisateur. Pas de vrai nom, pas de compte Steam, pas de fichier. Désactivé tant que vous ne le cochez pas ; décochez-le quand vous voulez et ce qui était conservé est supprimé. Vu dans les deux applications.
- **Connexion via Steam :** une connexion sur la page de Steam dans votre navigateur confirme que vous possédez R.U.S.E., pour le jeu en ligne, RUSE Guard et les téléchargements de contenu. Nous ne voyons jamais votre mot de passe, et votre identifiant Steam n'est jamais enregistré : seulement un laissez-passer conservé sur votre PC pendant 30 jours. C'est dans les Réglages, **Connexion Steam** ; le Launcher le demande une fois. Rien n'en a encore besoin. Pas encore essayé dans l'application.

**0.4.8.9:** les mods s'installent sur plus de PC, et une lecture d'images plus sûre.

- **Corrigé, signalé par un joueur :** sur certains PC, aucun mod ne s'installait : « ce PC ne fait pas confiance au certificat de sécurité du site (unable to get issuer certificate) ». Windows sur ces PC n'a pas le certificat avec lequel les téléchargements de GitHub sont vérifiés et ne peut pas le récupérer. Le Launcher essaie maintenant aussi avec la liste de certificats de Firefox, qu'il emporte. D'ici là, un mod téléchargé dans votre navigateur depuis la liste des mods s'installe avec **Ajouter un fichier de mod…**.
- **Des images plus sûres :** la bibliothèque avec laquelle le Launcher lit les images (Pillow) passe en version 13.0.0, avec ses corrections contre des fichiers d'image piégés qui pouvaient faire planter l'application, épuiser sa mémoire, ou pire.
- **Un code plus strict :** les 12 avertissements de la vérification de code de GitHub sur ce projet sont traités. Quand le Launcher affiche ses pages dans votre navigateur, elles n'ouvrent que ses propres fichiers, vérifiés d'une façon que cette vérification reconnaît, et les téléchargements demandent TLS 1.2 ou plus récent, comme avant. Rien ne change dans le fonctionnement du Launcher.

**0.4.8.8:** il joue les mods faits avec Studio 0.9.8.8, et votre jeu moddé dit R.U.S.E. 2.0 en or.

- **Les mods faits avec Studio 0.9.8.8 se jouent :** des bâtiments à eux (le deuxième et le troisième d'une nation demandent un petit patch du jeu, téléchargé une fois et appliqué seulement à votre copie moddée, jamais au jeu de votre dossier Steam), l'apparence propre des nouveaux bâtiments et leurs objets, les sons et animations changés avec RUSE Decoy, les valeurs des joueurs ordinateur et les règles du jeu, et les passages des anciens ponts fermés.
- **R.U.S.E. 2.0 en or :** votre jeu moddé s'ouvre sur une scène de bataille avec un moteur qui démarre, et son menu principal, le petit titre de chaque menu, les contours des menus et les écrans de chargement disent R.U.S.E. 2.0 en or. Il est fait sur votre PC à partir des fichiers de votre propre jeu la première fois (quelques minutes une fois, puis gardé). Réglages a une case pour garder le titre du jeu.
- **Corrigé : des taches sombres et claires sur les cartes faites avec le Studio** (cartes vierges, agrandies, en relief et à secteurs) : une telle carte est bien éclairée une fois construite avec cette version (son sol est refait la première fois).
- **Corrigé, signalé par un joueur :** sur la page Mods compatibles, « Nouvel ensemble de mods… » ne faisait rien. Il ouvre le nouvel ensemble maintenant. Pas encore essayé dans l'application elle-même.
- **Les lettres du jeu :** le Launcher est écrit dans la police des menus du jeu, prise dans votre jeu à chaque démarrage.
- **Encore buggé, à jouer à vos risques :** les cartes faites avec les textures de Map Paint, et les cartes vierges (Terrain vierge, Océan vierge).

**0.4.8.7:** il joue les mods faits avec Studio 0.9.8.7.

- **Les mods faits avec Studio 0.9.8.7 se jouent :** objets déplacés ou placés en grille, en boîte et le long de chemins, cartes vierges plus grandes avec leurs secteurs, et changements d'économie du seul mode Nucléaire.
- **Les lignes de la construction dans votre langue**, dans les dix.
- **Les résultats de construction gardés restent bons après une mise à jour.**
- **Encore buggé, à jouer à vos risques :** les cartes faites avec les textures de Map Paint, et les cartes vierges (Terrain vierge, Océan vierge).

**0.4.8.6:** il joue les mods faits avec Studio 0.9.8.6.

- **Les mods faits avec Studio 0.9.8.6 se jouent :** des cartes vierges avec des ombres sur le sol plat, ce qui est placé là où la carte copiée avait la mer dessiné, et le plancher de la caméra sur le nouveau sol.
- **Un plantage connu refusé :** un mod dont un avion armé porte le drapeau de reconnaissance sans celui de chasseur plantait le jeu quand l'avion était envoyé attaquer ; le Launcher refuse maintenant de le construire et dit pourquoi.
- **Encore buggé, à jouer à vos risques :** les cartes faites avec les textures de Map Paint, et les cartes vierges (Terrain vierge, Océan vierge).

**0.4.8.5:** il joue les mods faits avec Studio 0.9.8.5.

- **Les mods faits avec Studio 0.9.8.5 se jouent :** des avions dans un nouveau rôle (un bombardier avec sa soute, un éclaireur qui garde ses armes), des véhicules de reconnaissance, des armes qui touchent les avions, et du sol peint depuis la bibliothèque du pinceau Texture avec le détail du jeu par-dessus. Un Launcher plus ancien ne peut pas construire certains d'entre eux.
- **Plus rapide :** une carte repeinte de la même façon reprend son sol peint de la construction précédente en quelques secondes.
- **Encore buggé, à jouer à vos risques :** les cartes faites avec les textures de Map Paint, et les cartes vierges (Terrain vierge, Océan vierge).

**0.4.8.4:** les mods se téléchargent sur tous les PC, et il joue les mods faits avec Studio 0.9.8.4.

- **Les mods se téléchargent sur tous les PC :** sur certains PC, aucun mod ne se téléchargeait (« certificate verify failed: unable to get local issuer certificate »). Désormais le Launcher demande le certificat à Windows, comme un navigateur, puis réessaie ; ses propres mises à jour aussi. Pas encore essayé sur un PC qui avait le problème.
- **Les mods faits avec Studio 0.9.8.4 se jouent :** leurs propres missions, des cartes vierges avec leurs QG et leurs secteurs, des dépôts avec plus de camions (un Launcher plus ancien refuse les dépôts au-delà de 1 000 camions), des unités avec leur propre look et leurs uniformes, des modifications des mods des autres sous leur propre nom.
- **Encore buggé, à jouer à vos risques :** les cartes faites avec les textures de Map Paint, et les cartes vierges (Terrain vierge, Océan vierge).

**0.4.8.3:** les copies avec les mods vont où vous le dites.

- **Où vont les copies avec les mods**, dans les Réglages : choisissez le dossier où la copie du jeu avec les mods est
  construite, ou revenez à l'emplacement recommandé, `RUSE-Instances` sur le disque du jeu (la copie y partage les
  fichiers du jeu et est prête en quelques secondes ; sur un autre disque, c'est une copie complète du jeu, plus lente
  et plus grosse). La sauvegarde propre du jeu va à côté. Le prochain Jouer construit au nouvel endroit ; l'ancien
  dossier peut être supprimé à la main. Le Studio utilise le même dossier.

**0.4.8.2:** il s'ouvre dans votre navigateur web quand sa propre fenêtre ne le peut pas, et lance les mods faits
avec le Studio 0.9.8.2.

- **Linux et Steam Deck (via Proton) :** le Launcher s'ouvre dans votre navigateur web quand sa propre fenêtre ne le
  peut pas. Pas encore essayé sur Linux : dites-nous ce qu'il en est.
- Les mods faits avec le Studio 0.9.8.2 se lancent : des unités d'autres époques avec leurs propres modèles, tailles,
  recherches et cartes.

**0.4.8.1:** il convertit les anciens mods et lance les mods faits avec le Studio 0.9.8.1.

- **Convertir un ancien mod…**, l'outil Convert de LittleGroove repris : un ancien mod livré sous forme de packs du jeu,
  à copier dans le dossier du jeu, devient un mod que votre bibliothèque lance avec les autres. Pas encore essayé avec
  un vrai ancien mod.
- **Deux mods qui changent le même fichier du jeu :** le Launcher le dit avant Jouer, et **Utiliser celle de…**
  choisit lequel.
- Les mods faits avec le Studio 0.9.8.1 se lancent : morceaux et voix, une nation changée en une autre.

**0.4.8:** il lance les mods faits avec Studio 0.9.8, dont les nouvelles cartes qui partent de zéro, et montre les
nouveautés dans votre langue.

| Avant | Maintenant |
|---|---|
| Une nouvelle carte montrait les images de menu de la carte copiée. | Ses propres images, telles que son auteur les a faites, avec les points de départ là où partent ses joueurs. |
| Une unité construite sur une mer asséchée pouvait faire planter le jeu. | Corrigé (vérifié en jeu). |
| Une vieille eau de rivière se dressait en murs le long du bord d'une carte, et des phares effacés brillaient encore sur la mer. | Corrigé (vérifié en jeu). |
| Un mod qui efface toute une carte pouvait épuiser la mémoire du PC pendant sa construction. | Il se construit. |
| Les nouveautés étaient en anglais seulement. | Elles sont dans la langue du Launcher. |

Connu : **les cartes navales ne sont pas finies.** Océan vierge se construit et se joue, mais les unités sous son eau
n'ont pas encore été essayées.

**0.4.7:** les très grands mods de carte se construisent maintenant en quelques minutes (avant, cela prenait très
longtemps), et il lance les mods faits avec Studio 0.9.7.

| Avant | Maintenant |
|---|---|
| **Jouer** pouvait prendre des heures pour construire un grand mod de carte. | Le plus extrême que nous ayons (la carte « Le jour J » avec sa mer asséchée) prenait environ quatre heures ; maintenant moins de 10 minutes, avec le même résultat. |
| La première construction d'un grand mod de carte calculait tout sur votre PC. | Un mod exporté avec Studio 0.9.7 emporte ce que sa construction a calculé pour les déplacements de la carte : votre première construction est plus courte. Chaque réponse est vérifiée, et les fichiers du jeu sortent identiques. |

Connu : **les cartes navales ne sont pas encore au point.** Une mer asséchée ou peinte se construit et se charge, mais
l'eau s'affiche toujours.

**0.4.6:** **Jouer** démarre tout de suite quand rien n'a changé, et il lance les mods faits avec Studio 0.9.6 : de
nouvelles unités avec leur propre modèle 3D.

| Avant | Maintenant |
|---|---|
| **Jouer** reconstruisait toute la copie moddée à chaque fois, même quand rien n'avait changé (un joueur : « 30 minutes d'attente à chaque fois »). | Rien n'a changé : le jeu démarre tout de suite. Un changement reconstruit, mais les fichiers inchangés de la dernière copie sont réutilisés, donc une copie sur un autre disque que le jeu ne recopie plus chaque pack. Jouer dit combien il a copié. |
| Chaque construction relisait de zéro les données des unités du jeu. | Gardées d'une construction à l'autre : un gros mod de test prenait 213 s à chaque fois ; maintenant, les constructions qui suivent la première prennent 68 s. |
| La nouvelle unité d'un mod avait le modèle de l'unité qu'elle copie. | Son propre modèle venu du mod (`files/models`) est dans le jeu. **Vu en jeu :** un M1 Abrams à côté du Sherman. |
| La nouvelle unité d'un mod avec sa propre carte faisait planter le jeu quand elle était construite. | Corrigé. **Vu en jeu.** |
| Les couleurs des unités repeintes sortaient un peu fausses par endroits. | Plus proches de l'image du mod. Un mod avec des unités repeintes ou du sol peint reçoit une nouvelle empreinte et un nouveau code pour rejoindre : tous ceux qui jouent ensemble doivent mettre à jour. |
| Un démarrage lent ne laissait aucun indice. | **Copier le rapport** liste les étapes des cinq derniers démarrages. |
| — | Lance les mods qui utilisent l'effacement de toute la carte, les routes sur un sol remodelé et le comblement des lits de rivière de Studio 0.9.6 (nouveau, pas encore vu en jeu à grande échelle). |

**0.4.5:** il lance les mods faits avec Studio 0.9.5 : des unités repeintes, leurs propres cartes, et des unités avec leur
propre modèle.

| Avant | Maintenant |
|---|---|
| Un mod ne pouvait pas changer l'apparence d'une unité. | Les unités repeintes et les cartes d'un mod s'affichent dans le jeu. **Vu en jeu :** un Sherman rouge, une carte faite dans le Studio. |
| Un mod dont les packs de modèles d'unités grossissaient était écarté par le jeu : un plantage à la première usine. | Construits comme le jeu les vérifie. **Vu en jeu :** un deuxième Sherman avec son propre modèle. |
| Un mod qui faisait apparaître les unités d'une autre nation dans un chapitre de campagne ou une Opération plantait au chargement (des unités françaises sur Holland). | Leurs modèles s'y chargent aussi. **Vu en jeu.** |
| Aplanir les montagnes au bord d'une carte y laissait une falaise. | Le bord suit le sol. **Vu en jeu.** |

**0.4.4:** il lance les mods avec de nouvelles cartes, faites avec Dupliquer la carte de Studio 0.9.4.

| Avant | Maintenant |
|---|---|
| Les nouvelles cartes d'un mod n'avaient pas été essayées en jeu. | **Vu en jeu :** la nouvelle carte d'un mod est listée dans BATAILLES et joue son propre sol, 101 à la fois. Encore à ses débuts : signalez ce que vous trouvez. |
| Les mises à jour ne venaient que sous forme de versions complètes. | De petites corrections peuvent arriver entre deux versions (0.4.4.1), proposées comme n'importe quelle mise à jour. |

**0.4.3:** il lance les mods faits avec Studio 0.9.3, et les construit environ trois fois plus vite.

| Avant | Maintenant |
|---|---|
| Les rochers et la plupart des autres objets placés par un mod disparaissaient dès que la caméra s'éloignait un peu. | Dessinés jusqu'au plus loin ; les objets propres à la carte ne changent pas. **Vu en jeu.** |
| La nouvelle route d'un mod à travers un bois était une bande claire vue de haut, ou disparaissait à moyenne et longue distance. | Peinte à travers les bois comme les routes de la carte. **Vu en jeu.** |
| Les routes d'un mod retiraient toujours les arbres de leur tracé. | Une route peut les garder (`keep_trees`) : elle passe sous les arbres, plus pâle et plus grise dans un bois. |
| **Jouer** prenait environ 5 minutes pour construire un mod avec de nouvelles routes sur M03_Italie. | Environ 1½ minute après la première fois sur une carte. |

**0.4.2:** il lance les mods faits avec Studio 0.9.2.

| Avant | Maintenant |
|---|---|
| Un mod avec une route sur l'eau sur les cartes d'Italie, d'Allemagne, de Hollande et d'autres était refusé : son pont « n'aurait pas de plancher ». | Construit : le pont reçoit le plancher propre à la carte. Pas encore vu en jeu sur ces cartes. |
| Un mod qui donnait des unités au joueur dans un chapitre de campagne (camp 0) était refusé, et les unités des camps de l'ordinateur recevaient l'avertissement « pourraient ne jamais apparaître ». | Construit ; seul un camp que la mission du chapitre n'a pas reçoit un avertissement. |
| Sur M03_Italie et d'autres cartes, la nouvelle route d'un mod en terrain dégagé cachait de loin le décor de la carte, et ses objets ne s'affichaient que de près. | La vue lointaine de la carte reste comme elle était, et les objets du mod s'affichent de loin. Pas encore vu en jeu. |

**0.4.1:** votre langue dès le premier démarrage, et un éditeur d'ensembles de mods qui trouve les mods par leur nom.

| Avant | Maintenant |
|---|---|
| Créer un ensemble de mods listait toute votre bibliothèque avec Créer tout en bas, et aucun moyen de trouver un mod par son nom. | Créer est en haut, avec les mods déjà dans l'ensemble juste en dessous ; plus bas, « Ajouter des mods de votre bibliothèque », avec une recherche qui réduit la liste à mesure que vous tapez. |
| La langue se trouvait dans les Réglages, donc les joueurs ne savaient pas que le Launcher parle leur langue. | Le premier démarrage demande : « Choisissez votre langue », chaque langue dans ses propres mots, celle de votre jeu dans Steam marquée (les joueurs qui mettent à jour le voient une fois). Ensuite, un bouton de langue en haut, toujours visible. |
| La liste des applications installées de Windows montrait la toute première version installée. | Elle montre la version que vous avez. |

**0.4.0:** il lance les mods avec de nouvelles routes, telles que Studio 0.9 les construit : elles ressemblent aux routes
de la carte, vues de haut comme au ras du sol (essayé en jeu sur la carte Le jour J).

![Une nouvelle route vue de près sur Le jour J](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Avant | Maintenant |
|---|---|
| Les nouvelles routes d'un mod disparaissaient de près. | Elles sont dessinées avec l'asphalte et les décalques de bord de la carte, peintes comme les routes de la carte, et les plantes sur leur tracé sont retirées. |
| Un mod avec beaucoup de cercles d'effacement mettait des minutes à se construire. | Bien plus rapide. |

**0.3.3:** il lance les mods faits avec Studio 0.8.3.

| Avant | Maintenant |
|---|---|
| Un mod avec une caméra d'ouverture tournée (Studio 0.8.3) était refusé. | Construit : la caméra est tournée comme le mod le dit. |
| La caméra d'ouverture d'un point de départ déplacé restait à l'ancien endroit. | La caméra se déplace avec lui ; un nouveau point de départ reçoit sa propre caméra. |
| Un mod avec un point de départ dans un bois était refusé. | Construit : un QG y fonctionne. |

**0.3.2:** une seule copie du jeu pour tout le PC, la version affichée, et une bibliothèque plus claire.

| Avant | Maintenant |
|---|---|
| Chaque ensemble de mods construisait sa propre copie du jeu. | Une seule copie moddée pour tout le PC, partagée avec le Studio. |
| La version n'était pas affichée, et Nouveautés était une liste. | La version est à côté du nom, et Nouveautés ouvre un tableau avant/après comme celui-ci. |
| Les cartes et les mods se ressemblaient dans la bibliothèque. | Une carte a un badge CARTE. |
| Peu d'infobulles. | Des infobulles sur les principales commandes. |
| Les mods avec de nouvelles routes sur Twilight of the Gods, Alpha, Ostfriesland et Robert n'avaient pas le modèle de route de la carte. | Ils l'ont aussi. |

**0.3.1:** les mods avec des unités d'une autre nation (un Tiger allemand pour les États-Unis, par exemple) fonctionnent,
même dans une partie où personne ne joue cette nation (essayé en jeu, 2026-10-02). Et un nouveau look : les bleus de
R.U.S.E. au lieu du noir et or, et un nouveau logo : un chasseur qui monte à travers les nuages. La barre latérale a deux
onglets, **Ensembles de mods** et **Bibliothèque de mods**, chacun sur toute la hauteur, donc toute votre bibliothèque
est accessible (la moitié était cachée derrière la barre de défilement), avec une recherche et un compteur.
L'installateur propose une **sauvegarde propre du jeu** à côté du raccourci sur le bureau, et dit pourquoi.

**0.3.0:** **Mods compatibles :** le Launcher affiche notre liste de mods
([sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods)) ; cochez ceux que vous voulez, et ils sont
téléchargés et vérifiés. Au premier lancement, vous choisissez vos mods ; les mods de triche sont mis à part et jamais
cochés pour vous. Un bouton **Dépannage** (dans la barre du bas, et sur chaque message de problème) vérifie en une fois
ce qui peut empêcher **Jouer** et corrige ce qu'il peut, avec un rapport à coller dans un rapport de bug. Une
**sauvegarde propre du jeu** dans les Réglages garde une copie propre des fichiers de votre jeu et remet en place tout ce
qu'un autre gestionnaire de mods a changé (ou laisse Steam le réparer). Les mods faits avec le nouveau Studio
fonctionnent comme prévu : les chars et l'infanterie franchissent les nouveaux ponts sur le tablier, l'infanterie suit
les nouvelles routes, les bois dégagés sont ouverts aux unités, les bâtiments placés reposent sur le sol à n'importe
quelle taille, et le couvert arrive là où il a été peint sur Le jour J et les autres cartes qui ne sont pas carrées.
Problème connu : les nouvelles routes ne sont pas encore dessinées de près (elles s'affichent de loin).

**0.2.11:** **Jouer** fonctionne à chaque fois : une copie moddée que Windows refuse de supprimer (un fichier qu'une
ancienne version a lié, un programme qui le tient encore) est mise de côté dans `RUSE-Instances\.trash` au lieu
d'arrêter le jeu, et un jeu qui tourne encore depuis la copie est nommé. Les mods avec de nouveaux ponts ne créent jamais
de sol que les unités ne peuvent pas atteindre (cela faisait planter le jeu).

**0.2.9:** **Jouer** fonctionne quand les fichiers de votre jeu sont en lecture seule : il échouait avec « [WinError 5]
Access is denied » dès qu'une copie moddée restait à moitié construite. Si le jeu tourne encore depuis la copie moddée,
on vous dit de le fermer au lieu de vous montrer une erreur de Windows. Les mods avec de nouvelles routes construisent
leurs routes peintes et leurs ponts.

**0.2.8:** un mod que vous ajoutez est vérifié tout de suite, de la façon dont la construction du jeu le lira : un
fichier de carte cassé, ou un dossier de carte nommé d'après le titre de la carte (maps/Blitz au lieu de
maps/SuperCrossRoads4), est signalé avec sa correction avant que Jouer ne s'arrête dessus.

**0.2.7:** **Aide** et **Signaler un problème** dans la barre du bas : le wiki (un manuel pour jouer avec des mods), et
un rapport de bug dans votre navigateur avec la version du Launcher déjà remplie. Un message de problème a son propre
lien **Signaler**. Le Launcher n'envoie rien : vous lisez le rapport et vous le publiez. Les mods dont le dossier de
carte porte le titre de la carte (maps/Blitz au lieu de maps/SuperCrossRoads4) reçoivent maintenant la correction.

**0.2.6:** un bouton **Réglages** (en haut à droite) : la langue, le dossier du jeu et les mises à jour au même endroit,
prêt pour la suite.

**0.2.5:** la recherche de mises à jour est plus solide : quand GitHub refuse l'unique vérification au démarrage (il en
permet 60 par heure par adresse internet, partagées par tout ce qui l'utilise), le Launcher lit à la place la liste des
versions publiées sur GitHub.

**0.2.4:** votre langue est gardée après les redémarrages, les mises à jour et les réinstallations.

**0.2.3:** l'encadré rouge se replie comme le jaune (un grand ensemble peut lister des dizaines de conflits).

**0.2.2: Mettre dans le meilleur ordre.** Quand des mods d'un ensemble changent les mêmes valeurs, l'encadré jaune a un
bouton **Mettre dans le meilleur ordre** : les mods qui changent le plus passent d'abord et les plus petits après, pour
que chacun garde le plus possible de ses changements. Il dit quels mods il sauve, et les mods peuvent toujours être
déplacés à la main.

**0.2.1: les mods qui ne vont pas ensemble ne peuvent pas être joués, et le Launcher dit pourquoi.** Quand deux mods
d'un ensemble remplacent le même fichier ou script, un encadré rouge nomme les mods et ce qu'ils changent tous les deux,
et Jouer reste désactivé jusqu'à ce que l'un d'eux soit retiré. Quand un mod placé après ne fait qu'écraser des valeurs
d'un mod précédent (la vitesse d'un navire, par exemple), un encadré jaune les liste et l'ensemble se joue quand même.

**Nouveau dans la 0.2 :**

- **Des ensembles de mods créés dans la fenêtre :** nouveau, modifier, renommer, dupliquer, supprimer, et mettre les
  mods dans l'ordre. Plus de fichiers à modifier à la main. Un guide en trois étapes sur le premier écran montre le
  chemin.
- **Ajouter un fichier de mod…** (ou déposez-le sur la fenêtre) : un `.rusemod` exporté par RUSE Studio, un dossier de
  mod dans un `.zip`, ou un **`.rmod` de RUSE Mod Manager**, utilisé tel quel (appliqué par le propre moteur de
  LittleGroove).
- **Partager un ordre de chargement** sous forme de texte, et **Importer un ordre de chargement…** d'un ami : le
  Launcher dit quels mods vous avez, lesquels manquent et lesquels sont dans une autre version, puis crée l'ensemble.
  C'est le même texte que RUSE Mod Manager copie et lit, donc les ordres de chargement passent dans les deux sens.
- **Il se met à jour tout seul :** à partir de cette version, quand un Launcher plus récent sort, une barre le dit ;
  **Mettre à jour** le télécharge, vérifie son SHA-256 et l'installe, et le Launcher redémarre de lui-même.

Vos ensembles de mods de la 0.1 sont gardés. Problèmes et idées : GitHub Issues.

![RUSE Launcher](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/launcher.jpg)
