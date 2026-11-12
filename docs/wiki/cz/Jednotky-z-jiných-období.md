# Jednotky z jiných období

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.9.8.2 nebo novější a mod · **Trvá:** minutu nebo dvě na jednotku

366 jednotek od 1. světové války po dnešek stojí v záložce **Jednotky** vedle těch ze hry: tanky a letadla
z 1. světové války, 2. světové války+, studené války a současnosti, všechny v jedné hře. Každá je volný 3D model jiného
autora (CC BY), už napasovaný do hry, s výsostnými znaky svého národa, a s uvedením autora. Žádná z nich není ve vašem
modu, dokud ji nepřidáte.

## Získejte jednotky jedné éry

1. V záložce **Jednotky** vyberte nad druhy éru: **1. světová válka**, **2. světová válka+**, **Studená válka** nebo
   **Současnost** (**Vanilla** jsou vlastní jednotky hry, seznam jako vždy).
2. Poprvé Studio řekne, kolik jednotek éra má a jak je velká, s tlačítkem **Stáhnout jednotky 1. světová válka** (nebo
   té éry). Stáhne je z GitHubu projektu, zkontroluje každý soubor, než se použije, a zobrazí je v seznamu.

   | Éra | Jednotky | Stažení |
   |---|---|---|
   | 1. světová válka | 61 | 232 MB |
   | 2. světová válka+ | 32 | 198 MB |
   | Studená válka | 149 | 996 MB |
   | Současnost | 124 | 709 MB |

3. Stažená éra se sama aktualizuje, když vyjdou novější jednotky: Studio to oznámí a stáhne je.

Jednotky éry se filtrují jako ty ze hry: druh (pozemní nebo letecké), národ (i Čína), typ a pole hledání.

## Přidejte jednu do svého modu

1. Klikněte na jednotku. Její stránka ukazuje obrázek jejího modelu a jeho autora: **Model:** autor, licence a odkaz
   na místo, kde ho sdílel.
2. Vyplňte formulář:
   - **Název nové jednotky** (zobrazí se ve všech jazycích).
   - **Vycházet z**: jednotka hry, jejíž hodnoty převezme (rychlost, pancéřování, zbraně, jak se hraje). Navržená je
     první; vybrat jde kterákoli jednotka jejího druhu.
   - **Cena** (v každém datu bitvy).
   - **Velikost**: 1 je stejně dlouhá jako výchozí jednotka. Návrh je její skutečná velikost (její skutečná šířka,
     u letadla rozpětí křídel, v měřítku hry); cokoli od 0.05 do 20. Táhněte posuvníkem, nebo klikněte na jeden z jeho
     pojmenovaných bodů: **Drobný**, **Velikost ze hry** (1: stejně dlouhá jako výchozí jednotka, tak velká, jak hra
     ten druh jednotky kreslí), **Skutečná velikost** a **Obrovský**. Moderní letadla ve skutečné velikosti jsou mnohem
     větší než letadla 2. světové války ve hře (J-16 je stejně dlouhý jako Lancaster).
   - **Nabídka výroby**: národ a továrna, kde se kupuje.
   - **Zkoumá se z**: jednotka, ze které se zkoumá, nebo **Žádná: k mání od začátku**, s poli **Cena výzkumu**
     a **Doba výzkumu** (dobu zadejte v sekundách nebo minutách: výběr vedle ní).
3. Klikněte na **Přidat do modu**. Teď je to nová jednotka vašeho modu: **Otevřít její stránku** a změňte kteroukoli
   její hodnotu, její model nebo její kartu, jako u každé jednotky. **Odebrat z modu** ji zase smaže.

## Pozdější změna velikosti

Na stránce jednotky má **Vlastní model** stejný posuvník: vyberte velikost a klikněte na **Změnit velikost** (model se
napasuje znovu ze svého vlastního souboru, nic nevybíráte). **Všechna letadla mého modu** (nebo pozemní jednotky)
udělá všechny najednou: **Velikost ze hry**, **Skutečná velikost**, **Menší** (o pětinu) nebo **Větší** (o čtvrtinu).
Hra čte model jednotky při načítání, takže velikost se během hraní změnit nemůže: nová velikost se ukáže od dalšího
sestavení (Vyzkoušet ve hře).

## Řetězce výzkumu

Jednotku lze zkoumat z jakékoli jednotky v nabídce stavby jejího národa, i z jednotek jiných ér vašeho modu: přidejte
tank ze studené války, pak moderní, zkoumaný z něj. Jednotky z 1. světové války a 2. světové války+ se dají koupit
hned; jednotky ze studené války a současnosti začínají jako zkoumané z vhodné jednotky (formulář říká, kterou navrhuje,
a proč).

Když vyjmete jednotku, ze které se zkoumají jiné, o tom, co se stane, rozhoduje **Nastavení > Výzkum**:

- **Nejdřív mě varovat** (výchozí): Studio uvede jednotky zkoumané z ní, s tlačítkem **Přesto odebrat**.
- **Odmítnout**: jednotka zůstane a zpráva řekne, jak nejdřív změnit ty ostatní.
- **Znovu je propojit**: každá se místo toho zkoumá z nadřazené jednotky odebrané jednotky, za svou cenu a čas (nebo
  se dá koupit hned od začátku).

Jednotka, která zůstala zkoumaná z jednotky, jež už neexistuje, to řekne ve svém poli **Vylepšení a výzkum** a v liště
kontroly, a sestavení se na ní zastaví, dokud nevyberete jinou jednotku, nebo žádnou.

## Jízdní družstvo

**2. světová válka+** ukazuje také **Jízdní družstvo**, jehož autorem je sneadtristen6: střelci a voják s těžkou zbraní,
každý na vlastním koni. Nic z něj se nestahuje, takže tam je, ať už jsi jednotky 2. světové války+ stáhl, nebo ne.
Stejně jako jednotky z období není ve tvém modu, dokud ho nepřidáš.

1. Klikni na něj. Jeho stránka říká, kdo ho udělal a co přidání udělá.
2. Vyplň formulář jako u jednotky z období: jeho název, cenu, **Nabídka výroby**, **Skupina** a jednotku, ze které se
   **Zkoumá se z**. **Vycházet z** je vždy družstvo PĚCHOTA ze hry (američtí střelci): jeho koně a jezdci jsou udělaní pro
   vojáky tohoto družstva.
3. Klikni na **Přidat do modu**. Studio vyrobí jeho koně a jezdce v tvém PC z tvé vlastní kopie hry, vytvoří jednotku a
   pak dá koně jeho střelcům a vojákovi s těžkou zbraní. Každý krok se ukazuje pod tlačítkem, jak postupuje, s časem,
   který už uběhl. Když tvoje hra nemůže dát, co je potřeba, Studio řekne proč a nic se nepřidá.
4. Teď je to nová jednotka tvého modu: **Otevřít její stránku** a změň kteroukoli jeho hodnotu, jako u každé jednotky.
   **Odebrat z modu** ho zase odebere, i s oběma modely a jejich animacemi.

Jeho autor, sneadtristen6, je uveden v souboru `CREDITS-era-units.md` tvého modu, vedle autorů jednotek z období.

Viděno ve hře: tito jezdci na svých koních, udělaní přes **Importovat model…** na kopii družstva PĚCHOTA. Zatím
nevyzkoušeno ve hře: Jízdní družstvo přidané z tohoto seznamu.

## Autoři

Autor každé jednotky z jiné éry je uveden: na její stránce a v souboru `CREDITS-era-units.md` vašeho modu, který Studio
zapíše, když nějakou přidáte. Ten soubor nechte u svého modu: licence modelů to vyžaduje. Úplný seznam autorů je ve
[vydání jednotek ér](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/era-units).

## Co už bylo viděno ve hře

Viděno: načtou se hned, s vlastními kartami v nabídkách stavby; záložky výzkumu a řetěz vylepšení; jejich vlastní
modely; jejich velikosti. Zatím nevyzkoušeno: tažená
děla (import je zatím neumí napasovat, takže ukazují model výchozí jednotky) a zda hra počítá dobu výzkumu
v sekundách.

---

[[Polní příručka|Polní-příručka]] · [[English|Units-From-Other-Eras]]
