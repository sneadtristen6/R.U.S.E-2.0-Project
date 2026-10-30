# Exporter et partager

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio et un mod terminé · **Durée :** 5 minutes

## 1. Exporter

1. Ouvrez le menu **Mod** et choisissez **Exporter le mod…**.
2. Remplissez la **version** (trois nombres, comme `1.0.0`), votre nom et une ligne sur ce que fait le mod.
3. Choisissez où enregistrer. Le Studio construit le mod une fois sur votre jeu, pour noter la version du jeu sur
   laquelle il a été fait et son **empreinte** (un code court qui est le même pour tous ceux qui ont les mêmes mods), puis
   enregistre un seul fichier : `<your-mod>-<version>.rusemod`.

Ce fichier est tout ce dont un joueur a besoin : il l'ajoute dans RUSE Launcher ([[Installer et jouer|Installer-et-jouer]]).

**Les gros mods de carte :** une carte changée de partout peut demander des minutes de calcul à la construction (par
exemple où les unités peuvent aller sur un terrain que vous avez ouvert). Vous n'attendez ça qu'une fois. L'export met ce
que la construction a calculé dans le fichier, pour que la première construction d'un joueur soit plus courte. Il ne
contient que nos propres nombres, jamais un fichier du jeu, et il est verrouillé avec le fichier du jeu pour cette carte :
il ne s'ouvre que sur un PC qui a le jeu. Seulement les déplacements pour l'instant ; pas encore vu en jeu.

Quand l'export est fini, le Studio ouvre **Partagez votre mod** avec la taille du fichier, sa somme de contrôle SHA-256 et
son entrée pour la liste, prêtes à copier. Vous pouvez la rouvrir à tout moment depuis le menu **Mod** (**Partagez votre
mod…**).

## 2. Partager : l'ajouter aux mods compatibles

Vous avez fait un mod ? Ajoutez-le à la liste et devenez contributeur. L'onglet **Mods compatibles** de RUSE Launcher
montre les mods de la liste de [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), et les joueurs les
installent en un clic (les nouveaux joueurs se les voient proposer au premier lancement du Launcher) :

1. Mettez en ligne le `.rusemod` (une Release GitHub est le plus simple : celle de votre propre dépôt, ou celle de la
   liste).
2. Ouvrez une pull request sur [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods) qui ajoute l'entrée
   de votre mod à `index.toml` : collez l'entrée que montre Partagez votre mod et mettez le lien du fichier dans
   `download`. La taille et le SHA-256 doivent être ceux que l'export a montrés : le Launcher refuse un téléchargement qui
   ne correspond pas, donc personne ne peut échanger votre fichier contre un autre.
3. Ou publiez-le dans [Discussions > Mods & maps](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) avec
   une capture d'écran et ce qu'il change (faites glisser le `.rusemod` dans le message), et il est ajouté à la liste pour
   vous.

Une triche ou un outil de test (unités gratuites, construction instantanée...) reçoit l'étiquette `"cheat"` : le Launcher
le montre dans son propre groupe, « Triches et outils de test (facultatif) », et ne le coche ni ne le télécharge jamais
sauf si le joueur le fait. Une nouvelle version est un nouveau fichier avec un nouveau numéro de version : un fichier
publié ne change jamais.

Le format exact de l'entrée :
[MOD_FORMAT.md, section 15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/docs/MOD_FORMAT.md#15-the-mod-index-supported-mods).

## Modifier un mod installé

Dans le menu Mod du Studio, **Modifier un mod installé…** liste chaque mod qu'a le Launcher (avec une zone de
recherche). Le vôtre ouvre son projet. Celui de quelqu'un d'autre devient une copie à vous avec son propre nom (elle ne
peut pas prendre le nom de l'original) : vos changements vont dedans, et une mise à jour de l'original ne les efface
jamais. Un mod de RUSE Mod Manager (`.rmod`) est converti dans sa copie, donc ses changements de valeurs deviennent des
changements du Studio que vous pouvez modifier.

## Ce qu'un mod peut contenir

Des données seulement : nombres, textes, cartes, modèles, textures. Les programmes (`.exe`, `.dll`, scripts qui tournent
sur un PC) sont refusés par les deux applications. Une exception : les propres scripts de mission du jeu, tels que le
Studio les enregistre. Ils tournent dans le jeu et peuvent faire tout ce qu'il peut faire, donc n'installez ceux-là que
d'auteurs en qui vous avez confiance ([SECURITY.md](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/SECURITY.md)).

## Bonnes pratiques

- Gardez le dossier de votre mod : le `.rusemod` est pour les joueurs, le dossier est ce que le Studio modifie.
- Dites dans votre message de quels autres mods le vôtre a besoin ou avec lesquels il entre en conflit.
- Citez les personnes sur le travail desquelles vous vous appuyez.

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Export-and-Share]]
