# Quand quelque chose ne va pas

Trouvez ce que vous voyez, et suivez la solution.

## Essayez d'abord Dépannage

**Dépannage** vérifie en une fois ce qui peut empêcher un test ou **Jouer** : le jeu trouvé, Steam lancé, R.U.S.E. resté
ouvert depuis une copie moddée, le disque et son espace libre, des copies restées en trop, des fichiers en lecture seule,
et si l'application peut écrire là où vont les copies. Chaque problème qu'il peut corriger a un bouton ; les autres disent
quoi faire.

- Dans RUSE Studio : à côté de **Tester en jeu**, et dans **Réglages > Aide**. Dans RUSE Launcher : la barre du bas, et
  sur chaque message de problème (Studio 0.8.0, Launcher 0.3.0).
- **Copier le rapport** donne un texte à coller dans un [[rapport de bug|Signaler-un-bug]] (votre nom d'utilisateur Windows
  en est retiré).

## Le jeu lui-même semble changé (par un autre gestionnaire de mods ou une modification à la main)

**Réglages > Sauvegarde propre du jeu** garde une copie propre des fichiers du jeu, les vérifie par rapport à elle, et
remet ce qui a changé. Les fichiers qui ne sont pas ceux du jeu sont mis de côté, jamais supprimés. Ou **Vérifier avec
Steam** laisse Steam réparer le jeu. C'est le seul endroit où les applications écrivent dans le dossier de votre jeu, et
seulement quand vous le demandez.

## Une barre rouge sous l'en-tête du Studio

C'est la **vérification du mod**. Le Studio lit chaque fichier de votre mod comme le fera la construction du jeu, quand
vous choisissez le mod et de nouveau avant **Tester en jeu**. Chaque problème est dit avec des mots simples (ce qui ne va
pas, sur quelle carte, quoi faire), avec un bouton qui le corrige quand c'est possible : remplir une valeur manquante,
retirer le seul élément ou réglage qui ne va pas, ou mettre le fichier de côté. Le fichier tel qu'il était est gardé à
côté. **Détails** montre les propres mots de la construction, pratique pour demander de l'aide.

- **Mettre de côté** (à côté d'un fichier de carte cassé) le renomme `<name>.broken.toml` à côté de l'original : rien
  n'est perdu, le mod marche sans lui, et cette carte repart de zéro.
- Un problème dans `mod.toml` ou dans les modifications d'unités n'a pas de Mettre de côté : ouvrez le fichier et corrigez
  la ligne que nomme la barre, ou demandez dans
  [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

> [!NOTE]
> Cas connu : RUSE Studio 0.7.0 et les versions antérieures enregistraient les coups de pinceau **Eau** sans leur niveau
> d'eau (« the water brush needs level »). La 0.7.1 corrige ça ; **Mettre de côté** débarrasse d'un ancien fichier.

## L'application met longtemps à s'ouvrir

- **Le premier démarrage après l'installation**, avec « Garder une copie propre des fichiers de mon jeu » coché, fait
  cette copie (tout le dossier du jeu, environ 5.3 Go) : les Réglages montrent où elle en est, et l'application peut
  servir pendant ce temps.
- **L'index du jeu de RUSE Studio** est construit une fois par version du jeu, et de nouveau quand une mise à jour du
  Studio le change (environ une minute ; le Studio demande d'abord). Pendant ce temps, l'onglet Cartes et les Réglages
  peuvent servir, et la ligne en bas dit quand il est prêt.
- Autre chose : ouvrez **Dépannage** et **Copier le rapport**. Le rapport liste combien de temps chacun des derniers
  démarrages de l'application a pris à chaque étape, en secondes : collez-le dans un [[rapport de bug|Signaler-un-bug]].
  Les mêmes lignes sont gardées dans `%LOCALAPPDATA%\RUSE Mod Platform\logs\studio-start.log` (celles du Launcher :
  `launcher-start.log`).

## « Windows a protégé votre ordinateur »

Les applications sont nouvelles pour la vérification de réputation de Windows. Cliquez sur **Informations
complémentaires**, puis sur **Exécuter quand même**.

## « certificate verify failed: unable to get local issuer certificate » (ou « unable to get issuer certificate »)

Aucun mod ne se télécharge, ou la mise à jour non plus. Windows n'avait pas encore récupéré le certificat par rapport
auquel GitHub est vérifié ; depuis le Launcher 0.4.8.4 et le Studio 0.9.8.4, les applications le demandent à Windows et
réessaient. Depuis le Launcher 0.4.8.9 et le Studio 0.9.8.9, elles essaient aussi avec la liste de certificats
qu'utilise Firefox, qu'elles emportent, pour un PC dont Windows ne peut pas le récupérer (ses mises à jour de
certificats désactivées ou bloquées : « unable to get issuer certificate », ou « the PC doesn't trust the site's security
certificate »). Avec une application plus ancienne, la mise à jour ne peut pas se télécharger non plus : prenez
l'installateur sur la page des [versions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases) dans votre
navigateur et lancez-le (il s'installe par-dessus l'ancien, comme le fait la mise à jour). Un mod peut toujours être
téléchargé dans votre navigateur depuis les [versions](https://github.com/sneadtristen6/Ruse-Mods/releases) de la liste
des mods et ajouté avec **Ajouter un fichier de mod…** dans le Launcher. Si une application récente le dit encore : un
antivirus qui analyse les connexions sécurisées (HTTPS), un réseau d'école ou de travail, ou une mauvaise date sur le PC
peuvent en être la cause ; dites-le-nous dans
[Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## « [WinError 5] Accès refusé » en testant ou en jouant

Windows a refusé de supprimer une copie du jeu que l'application a faite (dans `RUSE-Instances`). Aussi : « An old
modded copy at `...\RUSE-Instances\<name>.old` can't be removed », à chaque deuxième **Tester en jeu** ou **Jouer**.

- **Mettez d'abord à jour** (les applications le proposent à leur ouverture) : depuis RUSE Studio 0.7.6 et le Launcher
  0.2.11, une copie que Windows refuse de supprimer n'arrête jamais un test : elle est déplacée dans
  `RUSE-Instances\.trash` et supprimée là une fois que plus rien ne la retient.
- **R.U.S.E. tourne encore depuis un test précédent ?** L'application le dit, avec le nom du programme : fermez le jeu
  (cherchez `RUSE.exe` dans l'onglet Détails du Gestionnaire des tâches), puis réessayez. **Dépannage** trouve un jeu qui
  tourne encore depuis une copie et les copies restées en trop, et les retire pour vous.
- **Avec une version plus ancienne :** supprimez le dossier que nomme le message (`...\RUSE-Instances\<name>.partial` ou
  `.old` ; Windows pose une question sur les fichiers en lecture seule : répondez oui ; seule la copie s'en va, jamais le
  jeu), puis réessayez. Si Windows refuse, redémarrez d'abord Windows.
- Toujours là ? [[Signalez-le|Signaler-un-bug]] avec le message entier.

## L'application ne trouve pas R.U.S.E.

**Réglages > Dossier du jeu > Choisir le dossier…** et choisissez le dossier qui contient `RUSE.exe` (sur Steam :
`steamapps\common\R.U.S.E`).

## « Nous n'avons pas pu confirmer cette copie de R.U.S.E. »

R.U.S.E. 2.0 ne marche qu'avec une copie du jeu que vous possédez. Tant que le dossier du jeu n'est pas confirmé,
**Jouer** et **Tester en jeu** restent désactivés, et cette fenêtre dit pourquoi : Steam n'a aucune trace de R.U.S.E.
installé dans ce dossier ; le propre fichier de Steam qui s'y trouve (`steam_api64.dll`) manque, a été changé ou n'est
pas celui de Valve ; ou le dossier a des fichiers qui font tourner le jeu sans Steam (elle les nomme).

- **Vous le possédez sur Steam :** cliquez sur **Vérifier mes fichiers dans Steam** (Steam remet ceux de ses fichiers
  qui manquent ou ont été changés), retirez les fichiers que la fenêtre nomme, puis cliquez sur **Vérifier à nouveau**.
  Un dossier du jeu que vous avez choisi à la main doit être celui que Steam a installé.
- **Vous le possédez autrement** (une copie en boîte d'avant l'arrivée de R.U.S.E. sur Steam), **ou vous pensez que la
  vérification s'est trompée :** la fenêtre affiche **Votre code** (fait à partir de ce PC et du dossier du jeu).
  Cliquez sur **Copier**, puis sur **Ouvrir un ticket sur Discord** ou **Ouvrir un ticket sur GitHub** et collez-le.
  Nous vous envoyons un code de déblocage : collez-le sous **Code de déblocage** et cliquez sur **Débloquer**. Il
  confirme cette copie sur ce PC.

La vérification est la même sous Windows, sous Linux et sur Steam Deck. Ce projet n'aide jamais personne à jouer à
R.U.S.E. sans le posséder : aucun fichier du jeu distribué, aucun lancement sans Steam.

## « Dans un format de mod plus ancien » ou « enregistré par un RUSE Studio plus récent »

- **Un format de mod plus ancien :** le mod a été fait avec un Studio plus ancien. **Mettre ce mod à jour** réécrit ses
  fichiers de la façon dont ce Studio les lit, en gardant ce qu'ils veulent dire ; un zip du mod entier va d'abord dans
  le dossier `Backups` du Studio.
- **Un RUSE Studio plus récent :** mettez le Studio à jour avant de changer ce mod : un plus ancien pourrait perdre ce
  qu'il ne connaît pas.

## Fermer le Studio demande « Fermer RUSE Studio ? »

Tout n'est pas encore enregistré, et la fenêtre dit quoi (une case avec du texte tapé mais pas validé, un changement
encore en cours d'enregistrement, Tester en jeu encore en construction...). **Non** garde le Studio ouvert ; **Oui** le
ferme et perd cela.

## Le jeu démarre, mais sans mes changements

1. A-t-il été lancé depuis **Jouer** (Launcher) ou **Tester en jeu** (Studio) ? Depuis Steam, le jeu démarre sans mods.
2. Les changements d'une carte ne se voient que sur cette carte : dans le menu principal, cliquez sur **BATAILLES** et
   choisissez-la (le message du Studio après Tester en jeu dit quel bouton et quelle carte).
3. Le mod est-il dans l'ensemble, et un mod plus bas dans l'ordre change-t-il la même chose ?

## Le jeu plante

Notez ce que vous avez fait juste avant (quelle carte, quel ordre, ce qu'il y avait à l'écran), faites une capture
d'écran, et [[signalez-le|Signaler-un-bug]]. Les rapports de plantage sur des cartes modifiées, c'est ce qui a rendu les
outils de carte solides.

## Autre chose

[[Poser une question|Poser-une-question]].

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|When-Something-Goes-Wrong]]
