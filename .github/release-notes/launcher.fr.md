**RUSE Launcher 0.4, pour les joueurs.** Il trouve R.U.S.E. via Steam, et **Jouer** construit une copie moddée du jeu
avec vos mods et la lance. Votre installation Steam n'est jamais modifiée.

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
