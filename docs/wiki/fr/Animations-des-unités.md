# Animations des unités

> **Il vous faut :** RUSE Studio 0.9.8.20 ou plus récent et un mod ; Blender (gratuit) pour changer les animations
> d'une nouvelle unité dans Blender · **Durée :** 10 minutes de lecture

La façon dont une unité bouge (rester debout, marcher, courir, viser, tirer, mourir), ce sont ses **animations**. Cette
page dit à quoi servent les animations du jeu, laquelle une unité joue pour chaque chose qu'elle fait, chaque façon
d'en changer une (pour une unité, pour toutes, pour les unités que vous choisissez, ou dans Blender), et comment
retrouver celle du jeu.

## Ce qu'est une animation

- Une animation fait bouger les os d'un modèle dans le temps : un pas de course, un fusil porté à l'épaule, une chute
  (voir [[Modèles et os|Modèles-et-os]]).
- Chaque chose qu'une unité fait dans le jeu (une **action** : reste immobile, marche, court, tire...) joue une
  animation. Un soldat en joue deux à la fois, une pour chaque moitié de son corps.
- Beaucoup d'unités partagent les animations du jeu : tous les fusiliers américains courent de la même façon. Un
  changement à une animation est donc, sauf si vous choisissez autrement, un changement pour toutes les unités qui la
  jouent.
- Les chars tournent leur tourelle et leurs roues sans animation : il n'y a rien à changer ici pour eux.

## Les animations du jeu et à quoi chacune sert

**RUSE Decoy** (son onglet en haut du Studio) liste chaque animation du jeu à gauche, sous **Animations**, par sorte :

| Sorte | Ce qu'il y a dedans |
|---|---|
| **Infanterie** | Fusiliers, bazookas, parachutistes et conducteurs : debout, marche, course, visée, tir, rechargement, fuite, touchés et morts (le haut et le bas du corps ont chacun les leurs) |
| **Servants des canons** | Les hommes autour d'un canon : au repos, en le déplaçant, en le préparant, au tir et au rechargement |
| **Véhicules et canons** | Canons en batterie et au déplacement, au repos et au tir, et autres pièces mobiles |
| **Personnages du QG** | Les officiers à la table du QG dans les scènes d'une mission (joués par aucune unité) |
| **Animaux et décor** | Vaches, chevaux, chèvres, poules, mouettes et éoliennes des cartes |

Chacune dit comment le jeu l'appelle et combien d'unités la jouent. Sur la page d'une unité, les actions sont nommées
d'après ce que fait l'unité, rangées ainsi :

| Groupe | Ses actions (quelques-unes) |
|---|---|
| À l'arrêt | Reste immobile, S'accroupit, Regarde autour |
| En mouvement | Marche, Marche à reculons, Court, Court vers la droite, Court à reculons, Fuit |
| Viser et tirer | Vise, debout ; Vise en marchant ; Tire ; Lance une grenade ; Recharge |
| L'arme lourde | Vise avec l'arme lourde, Tire avec l'arme lourde, Lève l'arme lourde, Baisse l'arme lourde |
| Être touché | Est touché, Est touché dans le dos, Est touché par une explosion |
| Mourir | Meurt, abattu ; Meurt dans une explosion ; Gît à terre |
| Parachutage | Saute, Tombe, Descend sous le parachute, Atterrit |
| Actions d'un équipage | Attend, Avance avec la pièce, Va à la pièce, Met la pièce en batterie, Tire (un servant), Recharge la pièce |

## Ses animations : laquelle joue chaque action

Une unité qui a ses propres animations (un modèle avec ses propres os : un cheval, un cheval et son cavalier, toute
créature) a un tableau sur sa page : **Apparence et mouvements**, la ligne **Sons et animations**, **Plus**, puis
**Ses animations**.

- **Reste immobile**, **Marche** et **Court** viennent en premier : le minimum pour un modèle. Si l'une n'a rien en
  propre, la page le dit, et ce qu'elle joue à la place.
- Chaque action a une liste des animations du modèle. Choisissez-en une, ou laissez-la sur la première ligne, **La plus
  proche** : elle joue alors la plus proche que le modèle a, et la ligne dit laquelle. La plus proche, c'est, dans cet
  ordre : une animation nommée pour cette action (stand ou idle, walk, run ou gallop, fire, death...), sinon ce que joue
  l'action la plus proche (une marche joue la course, un tir la visée ou l'immobile). Le jeu joue ce que dit la page : la
  construction suit la même règle.
- **Toutes les autres actions** liste le reste, par groupe.
- **Sur les longs trajets** est sa dernière ligne. Sur un long trajet par la route, le jeu met une escouade dans son
  camion. Une unité qui a ses propres animations peut y aller comme elle-même, en jouant l'une d'elles en boucle (sa
  course, si la première ligne est laissée), à la vitesse de son camion. Choisissez **Dans son camion** pour garder le
  camion.

Une unité copiée d'une autre qui a ses propres animations joue les mêmes.

## Changer une animation dans RUSE Decoy

1. Sur la page de l'unité, dans **Apparence et mouvements**, cliquez sur **Changer dans RUSE Decoy** sur la ligne
   **Sons et animations**. RUSE Decoy s'ouvre sur cette unité : ses sons, puis **Ses animations** avec chaque animation
   qu'elle joue. (Ou ouvrez l'onglet **RUSE Decoy** et choisissez une sorte sous **Animations**.)
2. Cliquez sur **Voir et changer…** sur une animation. Elle se joue en 3D sur une unité qui la joue : faites glisser
   pour la tourner, la molette zoome. La vue 3D a besoin d'internet une fois.
3. Ouverte depuis la page d'une unité, la première ligne demande **Modifier pour** :
   - **Cette unité seulement** : cette unité joue sa propre copie de l'animation, avec vos changements ; toutes les
     autres la jouent comme avant. C'est le choix de départ, sauf si l'animation est déjà changée pour toutes les unités.
   - **Toutes les unités qui la jouent** : le changement va à l'animation elle-même, pour toutes les unités qui la
     jouent (le nombre dit combien).
   - **Votre copie** et son nom : montré quand cette unité joue une copie à vous (plus bas) ; c'est alors le choix de
     départ.
4. Changez-la :
   - **Vitesse** : 100 % est celle du jeu, 200 % deux fois plus vite, 50 % deux fois moins vite. Enregistré quand vous
     relâchez.
   - **Utiliser à la place** : une autre animation du même corps à sa place (des fusiliers pourraient courir comme
     quand ils fuient).
   - **Un os**, avec **Taille**, **Tourner autour de** et **Rotation** : une partie du corps plus grande, ou tournée,
     tout au long de l'animation.
   - **Capture de mouvement** : le mouvement d'une vraie personne à sa place (voir [[Musique et sons|Musique-et-sons]]).
5. Cliquez sur **Terminé**. Chaque changement est enregistré dans votre mod tout de suite, et va dans le jeu quand
   vous testez ou exportez.

## Une copie d'une animation, pour les unités que vous choisissez

**Copier cette animation…** fait une copie que seules les unités et les soldats que vous cochez jouent : une course à
vous pour trois de vos escouades, par exemple, et seulement le soldat au bazooka d'une quatrième.

1. Dans la fenêtre de l'animation, cliquez sur **Copier cette animation…**, donnez un nom à la copie (vous seul le
   voyez), et cliquez sur **Faire la copie**. Elle part de l'animation telle qu'elle est maintenant, et s'ouvre dans la
   même fenêtre.
2. Changez-la comme plus haut.
3. Sous **Qui la joue**, cochez les unités qui jouent la copie : **Vos unités** d'abord, puis **Les unités du jeu**.
   Sous une unité dont plusieurs soldats ou pièces la jouent, cochez-en seulement quelques-uns. **Trouver une unité**
   cherche par nom ou par pays.
4. Rien ne joue une copie tant que vous ne cochez pas une unité : la ligne sous son nom dit « aucune unité ne la joue
   encore » jusque-là.

Chaque copie est à gauche de RUSE Decoy sous **Vos copies** : ouvrez-en une là, ou **Supprimer la copie**. La propre
copie d'une unité (**Cette unité seulement**) ou une animation changée dans Blender passe avant une copie pour cette
unité : la liste le dit à côté.

## Changer les animations d'une nouvelle unité dans Blender

Pour une nouvelle unité créée dans votre mod (une unité du jeu demande d'abord une nouvelle unité faite à partir
d'elle) :

1. Sur la page de l'unité, cliquez sur **Changer dans RUSE Decoy**. Au-dessus de ses animations, cliquez sur **Changer
   ses animations dans Blender**. Blender s'ouvre avec l'unité et chaque animation qu'elle joue, chacune nommée d'après
   ce qu'elle y fait, avec après le nom que lui donne le jeu.
2. En bas de Blender, l'Action Editor les liste : choisissez-en une. **Espace** la joue.
3. Cliquez sur un os, appuyez sur **Ctrl+Tab** pour le Pose Mode, **R** pour le tourner (**G** le déplace), puis **I**
   pour garder la pose à cette image. Faites-le à chaque image que vous changez : Blender va tout seul d'une pose gardée
   à la suivante.
4. Cliquez sur **Envoyer au R.U.S.E. Studio** en haut de la vue 3D de Blender : chaque animation part, changée ou non.
5. Dans RUSE Decoy, cliquez sur **Ramener mes changements**. Il dit lesquelles sont revenues changées : elles sont
   maintenant propres à cette unité. Toutes les autres unités, et chaque animation que vous n'avez pas touchée, restent
   comme avant.

Ne faites que poser les os : ne les renommez pas, ne les supprimez pas, ne les déplacez pas en Edit Mode. Sinon le
Studio ne prend rien, et dit quels os.

Un modèle avec ses propres os (un cheval, toute créature) envoie ses propres animations, sous leurs propres noms. Celle
que vous changez prend sa place : chaque action qui la jouait la joue changée.

## Retrouver l'animation du jeu

| Pour retirer | Cliquez sur | Où |
|---|---|---|
| Un changement pour toutes les unités | **Revenir à celle du jeu** | La ligne de l'animation dans RUSE Decoy, ou sa fenêtre |
| La propre copie de cette unité (**Cette unité seulement**) | **Revenir à ce que jouent toutes les unités** | La ligne de l'animation dans la liste de l'unité, ou sa fenêtre |
| Les changements d'une copie (son nom et ses coches restent) | **Revenir à l'animation du jeu** | La fenêtre de la copie |
| Une copie, en entier | **Supprimer la copie** | **Vos copies** |
| Un changement fait dans Blender | Annulez-le dans Blender tant que ce Blender est encore ouvert, puis **Ramener mes changements** : il est aussi annulé dans votre mod | Blender, puis RUSE Decoy |

Les boutons ci-dessus ne retirent pas un changement fait dans Blender.

## Ce que Ramener mes changements peut vous dire

| Il dit | Que faire |
|---|---|
| « Changées dans Blender, propres à cette unité désormais : ... » | Rien : ça a marché. **Tester en jeu** le montre. |
| « Chaque animation est revenue telle qu'elle était partie. » | Rien n'a été changé. Avez-vous gardé chaque pose avec **I** ? |
| « Faites dans Blender, jouées par aucune action pour l'instant : ... » | Une nouvelle animation n'est pas prise. Enregistrez-la dans Blender (**File > Save**) pour la garder. |
| « Non renvoyées (supprimées ou renommées dans Blender), elles se jouent donc comme avant : ... » | Redonnez-lui son nom dans Blender si vous voulez votre changement. |
| « Celles-ci se jouent sur une seule moitié du corps ... ils pourraient donc ne pas se voir dans le jeu » | Les os que vous avez bougés sont dans l'autre moitié : bougez ceux de la moitié qui la joue. |
| « Os faits dans Blender, que le squelette de cette unité n'a pas ... » | Un nouvel os ne peut pas être joué ; le reste est arrivé. |
| « L'éditeur NLA de Blender joue celles-ci avec un minutage à lui ... » | Le jeu les joue telles que l'Action Editor les montre. |
| « La scène de Blender tournait à ... images par seconde et le jeu tourne à 30 ... » | Mettez Blender à 30 images par seconde pour voir la vitesse du jeu. |
| « La scène de Blender a le Time Stretching activé ... » | Mettez Old et New au même nombre pour voir la vitesse du jeu. |
| « Aucune action de cette unité ne joue celles-ci ... » | Choisissez-en une pour une action sous **Ses animations**, sur la page de l'unité. |
| « Changées dans le Studio depuis leur départ vers Blender, et renvoyées par Blender sans changement : le changement du Studio reste donc ... » | Rien : votre changement fait dans RUSE Decoy est gardé. |
| « Changées aussi dans le Studio depuis leur départ vers Blender : le changement de Blender remplace celui du Studio ... » | Rien, si c'est le changement de Blender que vous voulez ; sinon, refaites votre changement dans RUSE Decoy. |
| « Rien de nouveau n'est venu de Blender depuis le dernier retour de vos changements. » | Cliquez d'abord sur **Envoyer au R.U.S.E. Studio** dans Blender. |

## Ce qui peut mal tourner

- **Rien ne change dans le jeu :** un changement pour **Cette unité seulement** ne se joue que sur cette unité, et une
  copie que sur les unités cochées pour elle. Un changement fait dans Blender passe avant un changement fait ensuite à la
  même animation avec **Cette unité seulement** ou une copie, pour cette unité (la règle du Studio ; pas encore essayé
  dans le jeu).
- **« Seule une nouvelle unité créée dans ce mod a ses propres animations »** : l'unité est une de celles du jeu.
  Faites d'abord une nouvelle unité à partir d'elle (**Nouvelle unité à partir de celle-ci…** sur sa page).
- **Ses animations manque sur la page :** le tableau n'existe que pour une unité qui a ses propres animations (un modèle
  avec ses propres os). Toutes les autres unités jouent celles du jeu : changez-les dans RUSE Decoy.
- **Un envoi que vous n'avez jamais ramené :** rouvrir Blender le met de côté. RUSE Decoy le montre avec **Ramener
  l'envoi mis de côté** et **Le mettre à la Corbeille** (voir [[Ouvrir dans Blender|Ouvrir-dans-Blender]]).

## Ce qui a été essayé dans le jeu

- Les changements d'animation de RUSE Decoy pour toutes les unités qui les jouent (Studio 0.9.8.8).
- **Cette unité seulement** : une escouade qui danse sur place pendant que toutes les autres restaient comme avant
  (novembre 2026).
- **Copier cette animation…** : une copie jouée par une escouade et par un soldat d'une autre (novembre 2026).
- **Changer ses animations dans Blender** : une escouade debout et courant un bras levé, et des Escouades à cheval
  génériques dont les chevaux tiennent la tête haute (novembre 2026).
- Les propres animations de l'Escouade à cheval générique, choisies par **La plus proche**, et le voyage comme
  elle-même sur les longs trajets (novembre 2026).
- Pas encore essayé dans le jeu : une vitesse, un remplacement ou un os changés pour une seule unité, et une autre
  animation choisie à la main sous **Ses animations**.

Toujours bloqué ? Demandez sur le [Discord](https://discord.gg/h54t5baNsC), ou voyez
[[Quand quelque chose ne va pas|Quand-quelque-chose-ne-va-pas]].

**Suivant :** [[Ouvrir dans Blender|Ouvrir-dans-Blender]] · [[Modèles et os|Modèles-et-os]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Unit-Animations]]
