# Umisťování budov a stromů

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.7.2 a mod (Mřížka, Obdélník, Trasa, Výběr a Znovu: 0.9.8.7; vlastní
> modely: 0.9.8.8) · **Ověřeno ve hře:** umístěné budovy jsou vidět při každém přiblížení, až do 8× své velikosti, a
> jednotky je objíždějí. Zatím nevyzkoušeno ve hře: co se umístí nástroji Mřížka, Obdélník a Trasa, a přesunuté objekty

## Umístění

1. Na liště klikněte na **Budovy**, nebo na **Předměty a stromy** a pak na záložku **Předměty** nebo **Stromy**.
2. Vyberte typ z obrázků (psaním do pole hledání je zúžíte). Každý obrázek je vykreslený z vlastního modelu hry
   a číslo v jeho rohu říká, kolik jich mapa už má. Seznam obsahuje vlastní typy této mapy:
   hra přijme jen typ, který mapa už používá.
3. Zvolte, jak klik umisťuje:
   - **Jeden**: jeden objekt tam, kam kliknete;
   - **Plocha**: tažením rozmístíte objekty v kruhu (**Rozestup** je drží od sebe, **Plocha** určuje kruh);
   - **Řada**: klikněte na začátek, pak na konec, a vznikne řada (živý plot, ulice, stromořadí), natočená podél ní;
   - **Mřížka**: řady objektů: klikněte tam, kde první řada začíná a kde končí, pak pohybem ukazatele rozložte řady a
     klikněte (**Mezi řadami** určuje mezeru);
   - **Obdélník**: natáhněte obdélník na terénu a pusťte: vyplní se vybraným objektem v řadách;
   - **Trasa**: klikejte podél cesty, pak dvakrát klikněte, stiskněte **Enter** nebo **Hotovo**: objekty sledují
     hladkou křivku přes vaše kliknutí (živý plot, stromořadí); se šířkou z nich vznikne pás. **Esc** zahodí
     rozdělanou mřížku, řadu nebo trasu.
4. **Čelem k silnicím:** blízko silnice se objekt postaví vedle ní a otočí se k ní čelem a řada ji sleduje; mřížka nebo
   obdélník nechá silnice volné. Posuvník otočení ho i tak otočí (zkuste 180°, když dům ukazuje záda).
5. **Otočení** a **Velikost** (až 10×) jsou posuvníky vpravo. Stromy se samy trochu liší velikostí a natočením,
   aby les nevypadal jako razítko.

Než kliknete, typ se ukazuje průhledně pod ukazatelem, natočený a velký tak, jak bude stát. Umístěné objekty
se ukazují jako jejich vlastní modely, každý s malou zlatou tečkou u paty, která ho označuje zdálky.

## Výběr, přesun, otočení, smazání

**Výběr** (v panelech **Budovy** a **Předměty a stromy**) vybírá, co na mapě stojí, ať to umístil váš mod, nebo to
patří samotné mapě: klikněte na jeden objekt, **Shift+klik** přidá další, nebo táhněte rámeček kolem několika. Pak
tažením jednoho z vybraných je přesunete, nebo použijte **Otočení** a **Velikost**, nebo **Smazat**. **Vrátit jako na
mapě** vrátí vaše změny objektů samotné mapy; **Esc** výběr zruší.

## Vlastní modely

**Importovat model…** (v **Předměty a stromy**) udělá z 3D modelu (.glb, .gltf nebo .3ds) vlastní kámen, předmět,
keř nebo strom vašeho mapového modu. Umisťuje se jako ty ze hry, na každé mapě modu, a udělají se pro něj menší verze
pro střední a velkou vzdálenost. Dejte mu **Velikost** a **Původ**: model, který udělal někdo jiný, smí do modu jen pod
licencí CC0 nebo CC-BY, s uvedením autora. Zaškrtnuté **Pevný: jednotky ho objíždějí**; nezaškrtnuté: jednotky jím
projedou a porazí ho, jako malé předměty samotné hry. **Tvůj model…** ho později změní. Viděno ve hře.

## Pevné budovy

**Pevné** (ve výchozím stavu zapnuté) zařídí, že jednotky umístěnou budovu objedou, místo aby projely skrz. Vypněte
ho u budovy, která má být jen na pohled.

## Skrývání v nich

Umístěné budovy samy jednotky neskrývají: otevřete **Kryt**, vyberte **Město** a klikněte na město, které jste vytvořili.

## Zpět a Znovu

**Zpět** (nebo **Ctrl+Z**) vrátí poslední objekt, nebo celou plochu, řadu, mřížku, obdélník či trasu, a také poslední
přesun, otočení, změnu velikosti nebo smazání. **Znovu** (nebo **Ctrl+Y**, **Ctrl+Shift+Z**) to provede znovu. Každý
nástroj mapy má obojí.

## Odstranění vlastních stromů a předmětů mapy

1. Na liště klikněte na **Odstranit** (Studio 0.8.1).
2. Vyberte, co odebere: **stromy**, **předměty**, **budovy** (jakoukoli kombinaci). Každý kruh si ponechá to, co bylo
   vybráno, když jste ho malovali.
3. Táhněte přes mapu: červené kruhy označují, co zmizí, a co pokrývají, je zbarvené dočervena. **Velikost** určuje
   kruhy; panel počítá, co odeberou, až se mod sestaví.

Kde zmizí stromy, terén se otevře všem jednotkám a ztratí lesní kryt (ověřeno ve hře: tanky vjedou do vykáceného
lesa, pěchota tam není skrytá). Odstraněné budovy otevřou svůj terén jednotkám
také. **Zpět** (**Ctrl+Z**) vrátí poslední tažení, **Začít znovu** odstraní všechny kruhy na mapě.

**Další:** [[Úprava scénáře|Úprava-scénáře]]

---

[[Polní příručka|Polní-příručka]] · [[English|Place-Buildings-and-Trees]]
