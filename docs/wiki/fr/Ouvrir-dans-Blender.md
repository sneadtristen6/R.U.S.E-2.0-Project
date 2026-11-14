# Ouvrir dans Blender

> **Il vous faut :** RUSE Studio 0.9.8.20 ou plus récent, un mod, et Blender (gratuit) · **Durée :** 5 minutes de
> lecture

**Ouvrir dans Blender** emmène une unité dans Blender, le logiciel 3D gratuit, pour changer sa forme, ses os ou sa
peinture ; **Ramener mes changements** met ce que vous y avez fait dans votre mod. C'est un seul bouton pour toute
l'unité : **Ce qui va dans Blender**, à côté, dit ce qui part, et tout ce que vous décochez reste tel quel. Cette page
le parcourt pas à pas.

Les animations ne se changent pas avec ce bouton : elles se changent dans RUSE Decoy (voir
[[Animations des unités|Animations-des-unités]]). Les propres animations d'un modèle partent avec lui dans Blender et
reviennent avec lui.

## Où est le bouton

| L'unité | Où | Ce qui revient |
|---|---|---|
| Une escouade que vous avez faite (une nouvelle unité de votre mod) | Le grand **Ouvrir dans Blender** sur sa carte, en haut de sa page | Ses soldats, chacun de son côté ; leur peinture |
| Toute autre unité que vous avez faite (un char, un avion) | **Apparence et mouvements**, la ligne **Modèle**, **Plus** : l'encadré **Changer dans Blender** | Tout son modèle (ses os aussi, quand ce sont les siens), sa peinture |
| Une des unités du jeu (pas une escouade) | Le même encadré | Sa peinture seulement : peignez dessus, le reste reste celui du jeu |
| Une des escouades du jeu | Sa carte dit de faire d'abord une nouvelle unité à partir d'elle : **Nouvelle unité à partir de celle-ci…** | Son **Uniforme personnalisé** seulement, peint depuis sa ligne **Uniforme** (**Ouvrir dans Blender**, puis **Ramener**) |

Pas de Blender sur ce PC ? La page montre **Obtenir Blender (gratuit)**, qui ouvre la page de téléchargement de
Blender, et **Choisir Blender…**, pour montrer au Studio où est `blender.exe` si vous l'avez déjà.

## Ce qui va dans Blender

Cliquez sur **Ce qui va dans Blender ▾** à côté du bouton. Tout est coché au départ. Décochez une partie pour la garder
telle quelle : **Ramener mes changements** la laisse alors comme elle était, quoi que Blender lui ait fait.

| Vous voyez | Cela veut dire |
|---|---|
| **Ses soldats**, puis chaque soldat (« Fusilier 1 », « Soldat au bazooka 5 »...) | Les soldats cochés s'ouvrent côte à côte dans un seul Blender. Changez celui que vous voulez : seul celui que vous changez change. |
| **Quel modèle :** **Le modèle des fusiliers** ou **Le modèle du soldat à l'arme lourde** | Une escouade avec ses propres os (l'Escouade à cheval générique) : un modèle à la fois, avec ses os et ses animations. |
| **Son modèle** | La forme de l'unité (une unité qui n'est pas une escouade). |
| **Ses os** | Ses os (seulement un modèle avec ses propres os). Décoché, les os de votre mod sont remis comme ils étaient. |
| **Sa peinture** | Ses images. Décoché, les images de votre mod sont remises comme elles étaient. |

Bon à savoir :

- **Sa peinture seule** (son modèle, ou chaque soldat, décoché) : Blender s'ouvre avec les images à peindre, et seule
  la peinture revient. C'est ainsi que l'**Uniforme personnalisé** d'une escouade se peint, pour tous les soldats à la
  fois. Une escouade qui porte l'uniforme par défaut ne peut pas : « Choisissez d'abord Uniforme personnalisé »
  (l'uniforme par défaut est aussi porté par d'autres escouades et équipages). Choisissez d'abord **Uniforme
  personnalisé** sur sa ligne **Uniforme**, dans **Apparence et mouvements**.
- **Ses os** décoché, mais un os a été ajouté, retiré ou renommé dans Blender : les os ne peuvent pas être gardés, ils
  reviennent donc tels que Blender les a envoyés, et le Studio le dit.
- Une escouade de soldats du jeu n'a pas **Ses os** : ses soldats reviennent sur les os du soldat du jeu, quoi que
  Blender leur ait fait.
- Rien de coché : le Studio dit « Cochez d'abord ce qui va dans Blender : le modèle, ses os ou sa peinture. »

## L'aller-retour, pas à pas

1. **Ouvrez-le.** Cliquez sur **Ouvrir dans Blender**. Blender s'ouvre (cela prend quelques secondes), avec ce que vous
   avez coché.
2. **Changez-le.** Peignez, changez la forme, posez un modèle à vous sur les os d'un soldat (voir
   [[Modèles et os|Modèles-et-os]], « Les poids »). Les quelques choses à savoir sont écrites en haut de la vue 3D de
   Blender.
3. **Envoyez-le.** Cliquez sur **Envoyer au R.U.S.E. Studio** en haut à gauche de la vue 3D de Blender.
4. **Ramenez-le.** Dans le Studio, le bouton dit maintenant **Ramener mes changements** : cliquez dessus. La page dit ce
   qui est arrivé : qui a changé et qui non sur une escouade, le fichier du modèle sur toute autre unité, et ce qui,
   décoché, a été gardé.
5. **Tester en jeu** le montre.

Vous pouvez garder Blender ouvert et refaire un tour : changer, envoyer, ramener.

## Ramener mes changements

- **Blender encore ouvert ?** **Ramener mes changements** lui demande d'abord d'envoyer, et l'attend (jusqu'à une
  minute).
- **Vous fermez Blender ?** Cliquez sur **Envoyer au R.U.S.E. Studio** avant : ce que vous n'avez pas envoyé reste dans
  Blender, et le Studio ne le voit jamais.
- **Vous l'avez fermé après l'envoi ?** Le bouton dit **Ramener mes changements** jusqu'à ce que vous cliquiez dessus,
  et il prend ce que vous avez envoyé en dernier. Sur la carte d'une escouade, un envoi fait après votre dernier retour
  (ou après **Ajouter un soldat**) apparaît comme un petit **Ramener mes changements** sous le grand bouton, une fois
  Blender fermé : il prend ce que vous avez envoyé en dernier.
- **Rien d'envoyé encore :** « Rien n'est encore revenu de Blender : dans Blender, cliquez sur Envoyer au R.U.S.E.
  Studio en haut, puis sur Ramener mes changements ici. »
- Un seul Blender à la fois pour une unité : tant que Blender l'a, le bouton du Studio dit **Ramener mes changements**.

## Un envoi mis de côté

Un **envoi**, c'est ce que Blender a envoyé avec **Envoyer au R.U.S.E. Studio**. Si vous rouvrez Blender avant d'avoir
ramené le dernier envoi :

- **Une escouade :** cet envoi est mis de côté dans le dossier Blender de votre mod, dans un dossier nommé
  `sent-not-brought-` suivi de la date et l'heure, et le nouveau Blender part de ce que votre mod a. Rien n'est perdu,
  mais la carte ne le dit pas encore, et elle n'a pas de bouton pour le ramener : les fichiers sont dans
  `Documents\RUSE 2.0\Mods\<votre mod>\blender\<le nom de l'unité>\squad\`.
- **Toute autre unité, son modèle coché :** rien n'est mis de côté : le prochain **Ouvrir dans Blender** part de ce que
  vous avez envoyé en dernier.
- **Les animations de RUSE Decoy :** chaque envoi mis de côté est listé au-dessus des animations de l'unité (« Envoyé
  depuis Blender, jamais ramené, mis de côté le ... »), avec **Ramener l'envoi mis de côté** pour le prendre, ou **Le
  mettre à la Corbeille**.

## Où sont vos fichiers Blender

Dans le dossier de votre mod, `Documents\RUSE 2.0\Mods\<votre mod>\blender\<le nom de l'unité>\` : ceux de l'escouade
dans `squad`, ceux de RUSE Decoy dans `animations`. Ils ne sont pas mis dans votre mod quand vous l'exportez. Sur la
page d'une escouade, **Plus d'options** dit où ils sont, avec **Afficher dans le dossier**.

## Ce qui peut mal tourner

| Ce qui se passe | Pourquoi, et que faire |
|---|---|
| Blender s'ouvre vide | Regardez la fenêtre de Blender pour une erreur (**Window > Toggle System Console**), et dites-le-nous sur le Discord. |
| Un soldat que je n'ai pas touché apparaît comme changé | Tout ce qui diffère compte comme changé, un objet renommé aussi. Son apparence reste comme elle était. |
| « Sur aucun soldat, donc pas envoyé : ... » | Quelque chose que vous avez amené dans Blender n'est ni sur les os d'un soldat ni dans sa collection : posez-le sur lui, puis renvoyez. |
| Un point de mon modèle ne bouge qu'avec les hanches | Il n'a pas d'os : voir [[Modèles et os|Modèles-et-os]], « Des points sans os ». |
| Des pièces ont perdu leur brillance ou leur couleur de camp | La page les nomme : un matériau renommé ou nouveau dans Blender revient simple. Gardez les noms de matériaux avec lesquels Blender s'est ouvert. |
| La nouvelle forme de mon unité du jeu n'est pas revenue | Sur une des unités du jeu, seule la peinture revient. Faites une nouvelle unité à partir d'elle pour changer sa forme. |

## Ce qui a été essayé dans le jeu

- La peinture venue de Blender sur une unité, vue de près et de loin.
- Une escouade ouverte dans Blender, un soldat changé et ramené à lui seul (novembre 2026).
- Pas encore essayé dans le jeu : tout le modèle d'un char passé par Blender, et ce que **Ce qui va dans Blender** garde
  (essayé avec Blender et le Studio, hors du jeu).

Toujours bloqué ? Demandez sur le [Discord](https://discord.gg/h54t5baNsC), ou voyez
[[Quand quelque chose ne va pas|Quand-quelque-chose-ne-va-pas]].

**Suivant :** [[Changer une escouade|Changer-une-escouade]] · [[Modèles et os|Modèles-et-os]] ·
[[Animations des unités|Animations-des-unités]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Open-in-Blender]]
