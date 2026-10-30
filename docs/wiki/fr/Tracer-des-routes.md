# Tracer des routes

> **Pour :** les moddeurs · **Il vous faut :** RUSE Studio 0.7.4 et un mod · **Prouvé en jeu :** les trajets de
> ravitaillement suivent une nouvelle route, et elle est peinte sur le sol

## Voir les routes de la carte

Cochez **Routes** en haut de la carte : les routes de la carte elle-même s'affichent en doré, sur le sol pendant que
vous le modelez.

## Tracer une nouvelle route

1. Dans la barre en bas, cliquez sur **Routes et ponts** (son onglet **Routes** s'ouvre). Les routes de la carte
   s'affichent en doré, vos nouvelles routes en bleu.
2. Choisissez un outil :

| Outil | Comment |
|---|---|
| **Droite** | Cliquez là où la route commence, puis là où elle finit. |
| **Courbe** | Cliquez sur le début, puis sur le virage vers lequel elle est tirée, puis sur la fin. |
| **Libre** | Cliquez le long du chemin ; double-cliquez, appuyez sur **Enter** ou cliquez sur **Terminer** pour la finir. |

3. Un ruban bleu suit le pointeur, avec la **longueur de la route** à côté (Libre montre aussi la partie depuis votre
   dernier clic). Une extrémité près d'une route **s'y accroche** (un anneau montre où), donc la nouvelle route la
   rejoint : les camions de ravitaillement peuvent rouler de l'une à l'autre. Les outils Routes montrent combien de
   nouvelles routes la carte a, et leur longueur totale.
4. **Esc** abandonne une route en cours de tracé ; **Annuler** (ou **Ctrl+Z**) reprend la dernière, **Rétablir** (ou
   **Ctrl+Y**) la retrace.

Les nouvelles routes sont enregistrées dans votre mod tout de suite (`maps/<map>/roads.toml`).

## Ce que fait une nouvelle route en jeu

- **Les trajets de ravitaillement l'empruntent** (prouvé : le trajet d'un dépôt de ravitaillement a pris un nouveau
  raccourci à travers les champs).
- **Elle est peinte sur le sol** dans la couleur des routes de la carte, pour que les joueurs la voient (prouvé en
  jeu). Elle ressemble aux routes de la carte vue de haut comme tout près du sol.
- **L'infanterie la suit** pour arriver plus vite quelque part (prouvé en jeu, Studio 0.8.0).
- **Au-dessus de l'eau, elle reçoit un pont** : le type de pont de la carte (24 des 32 cartes en ont un), d'une seule
  pièce étirée d'une rive à l'autre comme les ponts du jeu, et les unités peuvent le traverser. Une route sur l'un des
  ponts de la carte reçoit le nouveau pont à sa place. Sur une carte sans type de pont, la construction le dit et l'eau
  reste fermée. (Prouvé en jeu : les chars, l'infanterie et les camions de ravitaillement traversent sur le tablier.)
- Les plantes et les objets sur son chemin sont retirés ; **Garder les arbres sur les nouvelles routes** garde les
  arbres et les buissons (une route sous les arbres).

## Retirer les routes et les ponts de la carte

Dans les outils **Routes** :

- **Retirer les routes de la carte :** les routes de la carte elle-même disparaissent : le réseau que suivent les
  camions de ravitaillement (ils roulent alors à travers champs), et les routes dessinées sur le sol. Vos nouvelles
  routes restent. Vu en jeu : les routes disparaissent ; les camions de ravitaillement qui roulent à travers champs ne
  sont pas encore essayés.
- **Retirer les ponts de la carte :** les ponts de la carte elle-même disparaissent, avec les tabliers sur lesquels se
  tenaient les unités. Les unités traversent toujours là où ils se trouvaient, sur le sol en dessous, sauf si vous
  cochez aussi la case suivante. Vos nouveaux ponts restent.
- **Fermer les passages des anciens ponts** (avec les ponts retirés ; de DomesticNukes) : le terrain où chaque ancien
  pont passait au-dessus de l'eau est fermé aux unités, et les liaisons routières qui le traversent sont coupées : rien
  ne passe là, camions de ravitaillement compris, et le reste du réseau routier reste. Une nouvelle route à vous qui
  traverse au même endroit y reçoit son propre pont. Si les fermer coupait un morceau de terrain du reste, le Studio le
  dit avant la construction.

Pas encore essayé en jeu : retirer les ponts et fermer leurs passages.

## Placer un pont à vous

Dans l'onglet **Ponts** : choisissez un type, réglez sa longueur et sa rotation, puis cliquez sur le sol où va le
milieu du pont. Les deux extrémités doivent reposer sur une rive sèche. **Annuler** et **Rétablir** marchent ici aussi.

**Le voir :** **Tester en jeu**, puis dans le menu principal du jeu **BATAILLES** et la carte. Placez un dépôt de
ravitaillement près de votre route et regardez son trajet.

**Suite :** [[Placer bâtiments et arbres|Placer-bâtiments-et-arbres]]

---

[[Manuel de terrain|Manuel-de-terrain]] · [[English|Draw-Roads]]
