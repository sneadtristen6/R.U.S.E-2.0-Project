# Dossiers et fichiers des mods

> **Référence** · Vous n'avez jamais besoin d'y toucher à la main : le Studio les écrit. Cette page sert quand quelque
> chose semble anormal, ou aux moddeurs qui modifient les fichiers directement.

## Où se trouvent les choses

| Quoi | Où |
|---|---|
| Les mods du Studio | `Documents\RUSE 2.0\Mods\<mod>` ; les modifs de cartes dans `Maps`, les fichiers exportés dans `Exports`, les sauvegardes dans `Backups`. Dans le Studio, **Réglages → Où sont vos fichiers** ouvre chacun d'eux, et **Afficher le dossier de ce mod** (menu du mod) ouvre celui que vous modifiez |
| Les mods installés par le Launcher | `%LOCALAPPDATA%\RUSE Mod Platform\library` |
| Les copies moddées du jeu | Le dossier que vous choisissez dans les Réglages (**Où vont les copies avec les mods**, dans l'une ou l'autre application) ; l'emplacement recommandé est `RUSE-Instances` sur le même disque que le jeu (par exemple `D:\RUSE-Instances`), où une copie partage les fichiers du jeu. Sur un autre disque, chaque copie est une copie complète du jeu : plus lente et plus grosse. La sauvegarde propre du jeu (`RUSE-Backup`) va à côté. |
| Le jeu lui-même | Jamais modifié |

Les anciens Studios les rangeaient dans `%LOCALAPPDATA%\RUSE Mod Platform` (`mods`, `maps`, `exports`, `mod-backups`) : le Studio les déplace vers Documents au premier démarrage, et le dit.

## L'intérieur d'un mod

```
my-mod/
  mod.toml                    the mod's name, id, version, author (required)
  src/studio.rndf             unit changes made in the Studio
  text/studio.baseunite.csv   names of new units
  files/replace/gen/...png    a unit's paint (from Blender) or a unit's card, under the game texture it changes
  files/cards/<unit>.png      a new unit's own card in the build menu, named after the new unit
  files/models/<unit>.glb     a new unit's own 3D model (Import model), named after the new unit
  maps/<map pack name>/       one folder per map the mod changes:
    terrain.toml                ground brushes (also water, cover and block brushes)
    scenery.toml                buildings, props and trees placed
    scenario.toml               starting points and spawns moved, units added
    cover.toml, movement.toml   cover and movement written by hand
    map.toml                    how many players; or, for a new map, the map it copies and its name
```

## Le nom du dossier d'une carte est le nom de l'archive de la carte, pas son titre

Les joueurs connaissent une carte par son titre (**Blitz**) ; les fichiers du jeu utilisent le nom de son archive
(**SuperCrossRoads4**). Le dossier d'une carte doit utiliser le nom de l'archive : `maps/SuperCrossRoads4/`, pas
`maps/Blitz/`. La paire de chaque carte est dans [[Noms des cartes|Noms-des-cartes]], et la liste des cartes du Studio montre
les deux : le titre d'abord, le nom de l'archive après le point.

## Une nouvelle carte

Un mod peut ajouter sa propre carte à BATAILLES : une copie d'une carte livrée avec le jeu ou un départ vierge, sous un
nom à elle, que les autres fichiers du mod remodèlent ensuite. Le nom de son dossier est le nom d'archive de la nouvelle
carte (lettres, chiffres et `_`), et son `map.toml` dit quelle carte elle copie et comment les menus l'appellent :

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from (its pack name: Blitz)

[name]
us = "Blitz Twin"              # English, used where a language is left out
fr = "Blitz jumeau"
```

`maps/BlitzTwin/terrain.toml` et les autres fichiers modifient ensuite la copie, et Blitz reste comme elle était.
N'importe quelle carte listée dans BATAILLES peut être copiée ; les cartes de la campagne et des Opérations, non. Deux
joueurs ont besoin du même mod pour y jouer ensemble, comme pour n'importe quel mod. Les nouvelles cartes se jouent en jeu
(2026-10-03), et **Dupliquer la carte** dans le Studio crée ce dossier pour vous.

## Erreurs courantes

| Erreur | Ce qui se passe | Correction |
|---|---|---|
| Le zip contient un dossier dans un dossier | Le Launcher regarde un dossier plus bas et le trouve. À deux niveaux ou plus, il dit qu'il n'a trouvé aucun mod. | Zippez le dossier qui contient `mod.toml`. |
| Un dossier de carte nommé d'après le titre de la carte | La construction dit que ce n'est pas un nom d'archive de carte. | Renommez-le avec le nom de l'archive. |
| Un fichier modifié à la main a une faute de frappe | La vérification du mod nomme le fichier et la ligne. | Corrigez-la, ou **Mettre de côté** dans le Studio. |
| Un `.exe`, un `.dll` ou un script de PC dans le mod | Refusé : les mods ne contiennent que des données (les propres scripts de mission du jeu, tels que le Studio les enregistre, sont la seule exception). | Retirez-le. |

Si un fichier ne peut pas être lu, le Studio n'écrit jamais par-dessus : votre travail n'est jamais perdu. **Mettre de
côté** le renomme `<name>.broken.toml` à côté de l'original.

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Mod-Folders-and-Files]]
