# Musique et sons

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.9.8.8 ou plus récent, un mod ; pour un son à vous, un
> fichier son (WAV, MP3, OGG ou FLAC), pour des mouvements à vous, un fichier de capture de mouvement (.bvh) ·
> **Durée :** quelques minutes pour chacun

Tout se fait ici dans le Studio, dans l'onglet **RUSE Decoy**, le concepteur de sons et d'animations (il a pris la place
de l'onglet Musique dans Studio 0.9.8.8). Aucun autre programme à installer.

## Chaque son du jeu

**RUSE Decoy** liste chaque son du jeu, par type, à gauche : les armes de près et au loin, les impacts et les
destructions, les moteurs et les pas, l'environnement, les ambiances des cartes, l'interface, les cartes ruse, les voix
des unités, le QG et le renseignement, les échanges radio, les dialogues des missions (avec ce que dit chaque réplique),
la musique et les jingles. La case de recherche trouve un son par son nom ou par les paroles qu'on y entend.

Pour chaque son :

- **Écouter** le fait entendre.
- **Volume :** faites-le glisser. 100 % est celui du jeu, jusqu'à 200 %.
- **Remplacer…** ouvre l'éditeur ci-dessous, pour mettre un son à vous à sa place.

Les changements sont enregistrés dans votre mod et passent dans le jeu quand vous le testez ou l'exportez.

## Remplacer un son ou un morceau

1. Déposez un fichier son sur l'éditeur, ou choisissez-en un. Le vôtre peut avoir n'importe quelle durée : le Studio le
   met au format du jeu.
2. Coupez-le avec les deux poignées, **Fondu d'entrée** et **Fondu de sortie**, réglez le **Volume**, et écoutez-le.
3. **Utiliser** l'enregistre dans votre mod. Plus tard, **Modifier…** le rouvre et **Retirer** remet le son du jeu.

## Ajouter un morceau

Sous **Musique et jingles**, les morceaux sont listés selon l'endroit où ils sont joués : le menu principal, le
générique, les trois listes où puisent les batailles, la fin d'une partie, les objectifs de mission, et les chapitres de
campagne et Opérations qui les désignent. Les trois listes de bataille : une calme pendant que les joueurs se
développent, une de combat dès que les tirs touchent, et la musique des ruses quand une carte ruse est jouée.

Sous chaque liste de bataille, **Ajouter un morceau…** : donnez-lui un nom, déposez un fichier son, coupez-le, puis
**Utiliser**. Il rejoint les morceaux que le jeu joue dans cette liste, marqué Nouveau.

## Animations

Sous **Animations** : comment les unités bougent, de la course, du tir et du rechargement jusqu'à la mort et aux
servants d'un canon au travail. Chacune dit comment le jeu l'appelle et combien d'unités la jouent. **Voir et changer…**
la montre en 3D sur une unité qui la joue (faites glisser pour la tourner, la molette zoome ; la vue 3D a besoin
d'internet une fois) :

- **Vitesse :** 100 % est celle du jeu, 200 % deux fois plus vite, 50 % deux fois moins vite.
- **Utiliser à la place :** une autre animation du même corps à sa place (des fusiliers pourraient courir comme quand
  ils fuient, par exemple).
- **Un os**, avec **Taille** et **Tourner autour de** / **Rotation** : une partie du corps agrandie, ou tournée, tout au
  long de l'animation (ce qui y est attaché grandit avec elle).
- **Revenir à celle du jeu** retire tous les changements qui lui ont été faits.

## Capture de mouvement

Mettez le mouvement d'une vraie personne sur une animation, sous **Capture de mouvement** : choisissez un mouvement dans
la bibliothèque de mouvements (3 205 mouvements gratuits de la base de capture de mouvement CMU et de 100STYLE, chacun
téléchargé quand vous le choisissez), ou **Choisir un fichier de capture…** à vous (.bvh, de Mixamo, Blender ou
n'importe quel programme de capture de mouvement).

1. Choisissez la partie à utiliser : **À partir de** (en secondes) et **Durée**. Pour une marche ou une course, un pas
   entier de chaque pied ; pour une mort, commencez juste avant la chute.
2. **Garder sur place** garde les marches et les courses là où le jeu déplace l'unité ; **La faire boucler** lisse la
   dernière pose vers la première, pour une animation que le jeu joue encore et encore.
3. **Crédit (qui a fait le mouvement) :** rempli pour les mouvements de la bibliothèque ; pour tout autre fichier,
   écrivez qui l'a fait et sa licence. Il suit votre mod partout.
4. **Regarder**, puis **Utiliser**. Les changements de vitesse et d'os s'appliquent toujours par-dessus ; **Revenir à
   celle du jeu** la retire.

## Les sons et animations d'une unité

La page d'une unité a une section **Sons et animations** : ses propres répliques et sons de moteur, et ses animations.
**Changer ses sons dans RUSE Decoy** ouvre RUSE Decoy sur ceux de cette unité. Une unité dit les répliques de sa nation
et de son type, donc une réplique changée là s'entend chez toutes les unités qui la partagent. Ses tirs et ses impacts
sont sous les types armes et impacts.

## Le son d'ambiance d'une carte

Dans l'onglet **Cartes**, **Son d'ambiance…** montre celui de la carte : ce dont il part, et ses trois couches, chacune
s'écoute et se remplace dans le même éditeur. Une carte peut aussi partir de l'ambiance qu'une autre carte joue.

## Ce qui a été vu en jeu

Vu en jeu : les sons et animations de RUSE Decoy (Studio 0.9.8.8), le morceau du menu principal, les morceaux des listes
de bataille 1 et 2, de nouveaux morceaux qui y sont ajoutés, et les répliques d'une unité. Pas encore essayé : le son
d'ambiance d'une carte, et la liste de la musique des ruses (connue par le fonctionnement du jeu). Les messages d'erreur
de RUSE Decoy ne sont qu'en anglais pour l'instant.

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Music-and-Sounds]]
