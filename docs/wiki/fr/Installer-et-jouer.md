# Installer et jouer

> **Pour :** les joueurs · **Il vous faut :** R.U.S.E. sur Steam, installé · **Durée :** 5 minutes

**En bref :** téléchargez **RUSE-Launcher-Setup** depuis la page des versions, lancez-le, ouvrez **RUSE Launcher**,
cliquez sur **Mods compatibles**, cochez un mod et appuyez sur **Installer**, mettez-le dans un ensemble de mods, puis
**Jouer**. Chaque étape ci-dessous dit exactement où cliquer.

Vous n'avez besoin que de **RUSE Launcher** pour jouer avec des mods. **RUSE Studio** sert à les créer (voir la fin de
cette page).

## Étape 1 : télécharger le Launcher

1. Ouvrez la page des [versions du Launcher](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher).
2. La plus récente est en haut, marquée **Latest** (par exemple *RUSE Launcher 0.4.8.9*).
3. Descendez jusqu'à **Assets** en dessous et cliquez sur **RUSE-Launcher-Setup-0.4.8.9.exe** (le numéro de version
   change ; prenez le `.exe` qui commence par `RUSE-Launcher-Setup`). Votre navigateur le télécharge.

Les autres fichiers (`RUSE-Launcher-notes.json`, *Source code*) ne sont pas nécessaires.

## Étape 2 : l'installer

1. Ouvrez le fichier que vous avez téléchargé (en général dans votre dossier **Téléchargements**).
2. **« Windows a protégé votre ordinateur » ?** Cliquez sur **Informations complémentaires**, puis sur **Exécuter quand
   même**. L'application est nouvelle pour la vérification de réputation de Windows ; son code est public sur ce GitHub.
3. Avancez dans l'installateur. Laissez **Garder une copie propre des fichiers de mon jeu** coché : les applications ne
   changent jamais le dossier de votre jeu, mais d'autres gestionnaires de mods et des modifications à la main peuvent le
   faire, et chaque jeu moddé est construit à partir de ces fichiers. La copie est faite au premier démarrage de
   l'application (quelques minutes, et à peu près autant de place sur le disque que le jeu).
4. Lancez **RUSE Launcher** (menu Démarrer, ou le raccourci du bureau). La première fois, **Choisissez votre langue** :
   l'une des onze, les dix du jeu et le persan (فارسی) ; le bouton de langue en haut la change à tout moment. Il trouve
   R.U.S.E. tout seul via Steam. S'il dit qu'il n'y arrive pas : **Réglages > Dossier du jeu > Choisir le dossier…** et
   choisissez le dossier qui contient `RUSE.exe` (en général `C:\Program Files (x86)\Steam\steamapps\common\R.U.S.E`).

> [!IMPORTANT]
> **R.U.S.E. 2.0 ne marche qu'avec une copie du jeu que vous possédez sur Steam.** Avant qu'un jeu moddé démarre, le
> Launcher et le Studio vérifient le dossier du jeu : l'inscription chez Steam de R.U.S.E. installé là, le propre
> fichier de Steam qui s'y trouve, et aucun fichier qui fasse tourner le jeu sans Steam. S'ils ne peuvent pas le
> confirmer, une fenêtre dit pourquoi et quoi faire (Jouer reste désactivé jusque-là) : voir
> [[Quand quelque chose ne va pas|Quand-quelque-chose-ne-va-pas]].

## Étape 3 : obtenir des mods

**Depuis notre liste (le plus simple) :** cliquez sur **Mods compatibles**, cochez les mods que vous voulez et appuyez sur
**Installer**. Chaque fichier est téléchargé et vérifié par rapport à la liste avant d'entrer dans votre bibliothèque.

**Depuis un fichier que quelqu'un a partagé :** cliquez sur **Ajouter un fichier de mod…** et choisissez le fichier, ou
faites-le glisser sur la fenêtre. Le Launcher accepte :
- `.rusemod` : fait avec RUSE Studio ;
- `.rmod` : fait pour le RUSE Mod Manager de LittleGroove ;
- `.zip` : un dossier de mod zippé.

Il vérifie d'abord le fichier : un fichier qui n'est pas un mod, ou qui contient un programme, est refusé avec la raison.

**Un ancien mod qui se présente sous forme de fichiers du jeu** (des archives `.dat` qu'on vous disait de copier dans le
dossier du jeu) : cliquez sur **Convertir un ancien mod…**, choisissez son dossier, donnez-lui un nom et cliquez sur
**Convertir et ajouter à la bibliothèque**. Le dossier de votre jeu n'est pas touché.

## Étape 4 : choisir à quoi jouer

1. Un **ensemble de mods**, ce sont les mods auxquels vous jouez ensemble, dans un ordre. Cliquez sur **Nouvel ensemble
   de mods…**, ajoutez les mods et mettez-les dans l'ordre (quand deux mods changent la même chose, celui du bas gagne).
2. Si deux mods ne peuvent pas être joués ensemble, le Launcher dit lesquels et pourquoi, avant que vous jouiez.

## Étape 5 : jouer

Choisissez votre ensemble de mods et appuyez sur **Jouer**. La première fois, le Launcher construit une copie moddée du
jeu (une minute environ) ; ensuite, seulement ce qui a changé. Puis R.U.S.E. démarre, avec vos mods.

Votre jeu moddé affiche **R.U.S.E. 2.0 en or** : il s'ouvre sur une scène de bataille, et son menu principal, ses
menus et ses écrans de chargement portent le titre doré. Il est fait sur votre PC à partir des fichiers de votre propre
jeu la première fois (quelques minutes, une fois). Pour garder le titre du jeu, décochez **Le titre du jeu** dans les
**Réglages**.

> [!NOTE]
> Lancer R.U.S.E. depuis **Steam** lance le jeu **sans** mods, comme toujours. Pour jouer avec des mods, lancez-le avec
> **Jouer** dans le Launcher. Votre installation Steam n'est jamais modifiée.

## Mises à jour

Le Launcher cherche une nouvelle version à chaque démarrage : cliquez sur **Mettre à jour** quand il en propose une. Si la
mise à jour échoue avec « certificate verify failed », téléchargez le dernier `RUSE-Launcher-Setup` de l'étape 1 dans
votre navigateur et lancez-le : il s'installe par-dessus l'ancien et garde vos mods.

## Des problèmes ?

| Ce que vous voyez | Que faire |
|---|---|
| « Windows a protégé votre ordinateur » | **Informations complémentaires**, puis **Exécuter quand même** (étape 2). |
| Le Launcher ne trouve pas R.U.S.E. | **Réglages > Dossier du jeu > Choisir le dossier…**, le dossier avec `RUSE.exe`. |
| « certificate verify failed: unable to get local issuer certificate » | Prenez le Launcher 0.4.8.4 ou plus récent (étape 1) ; voir [[Quand quelque chose ne va pas|Quand-quelque-chose-ne-va-pas]]. |
| « unable to get issuer certificate » ou « this PC doesn't trust the site's security certificate » en installant des mods | Prenez le Launcher 0.4.8.9 ou plus récent (étape 1), ou téléchargez le mod dans votre navigateur et utilisez **Ajouter un fichier de mod…** ; voir [[Quand quelque chose ne va pas|Quand-quelque-chose-ne-va-pas]]. |
| Le jeu démarre sans mes mods | Lancez-le avec **Jouer** dans le Launcher, pas depuis Steam. |
| Mes amis ne peuvent pas rejoindre ma partie | Tout le monde a besoin des mêmes mods dans le même ordre : [[Jouer entre amis|Jouer-entre-amis]]. |
| Autre chose | [[Quand quelque chose ne va pas|Quand-quelque-chose-ne-va-pas]], ou demandez dans les [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) ou sur le [Discord](https://discord.gg/h54t5baNsC). |

## Linux et Steam Deck (avec Proton)

Quand la propre fenêtre d'une application ne peut pas afficher ses pages (sous Proton elle reste bleue, parce que
WebView2 de Microsoft n'y démarre pas), l'application s'ouvre dans votre navigateur web à la place, et une petite fenêtre
le dit : gardez-la ouverte pendant que vous jouez, et fermez-la pour fermer l'application. Pas encore essayé sous Linux :
dites-nous comment ça se passe dans les
[Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## Créer des mods : RUSE Studio

1. Ouvrez la page des [versions du Studio](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio). Le
   Studio est un aperçu, donc ses versions sont marquées **Pre-release** : prenez la plus récente.
2. Sous **Assets**, cliquez sur **RUSE-Studio-Setup-0.9.8.9.exe** (la version la plus récente), lancez-le comme à
   l'étape 2.
3. Lancez **RUSE Studio**, puis suivez [[Votre premier mod|Votre-premier-mod]] (10 minutes).

**Suivant :** [[Jouer entre amis|Jouer-entre-amis]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Install-and-Play]]
