# Import modelu

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.9.6 nebo novější, mod a 3D model (.3ds, .glb nebo .gltf) ·
> **Trvá:** pár minut

Dejte nové jednotce vlastní 3D model, z Blenderu nebo z jakéhokoli jiného 3D nástroje. Tak vznikl
[mod M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods): první model přenesený do R.U.S.E. z jiného 3D programu,
viděný ve hře.

Model může jít také na novou budovu, místo jednoho dílu jejího vzhledu (viz
[[Budovy a nabídky stavby|Budovy-a-nabídky-stavby]]), nebo na vaši mapu jako vlastní kámen, předmět, keř nebo strom
(viz [[Umisťování budov a stromů|Umisťování-budov-a-stromů]]). Obojí: Studio 0.9.8.8, viděno ve hře.

## 1. Opatřete si model

Soubor **.3ds** s jeho obrázky (.tga nebo .png), nebo **.glb** či **.gltf** (obrázky jsou uvnitř: PNG, JPG nebo WebP).
Model, který import neumí přečíst (komprimované sítě, obrázky KTX2), to řekne, i jak to opravit v Blenderu.

- **Z Blenderu:** File > Export > glTF 2.0, formát **glTF Binary (.glb)**.
- **Ze stránky s volnými modely:** mnoho tanků přichází jako .3ds se složkou obrázků .tga. Nechte složku tak, jak
  přišla: Studio najde obrázky vedle .3ds nebo ve složce nad ním, i pod zkrácenými názvy, které soubory .3ds používají
  (`MAIN_DEF.TGA` pro `Main_Defuse.tga`).
- Než mod budete sdílet, zkontrolujte licenci modelu a uveďte jeho autora v README svého modu.

**Co pomáhá:** díly pojmenované podle toho, čím jsou. Studio otáčí díl, který má v názvu *turret* (nebo *tourelle*,
*tower*), s věží, a díl s *barrel*, *gun* nebo *cannon* s ní také. Díl, který sedí na věži, se s ní otáčí taky.
Všechno ostatní se pohybuje s korbou. Kanón by měl mířit rovně dopředu.

Příklad s Abramsem: **"Tank Abrams" od ags**, zdarma na
[downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/) (.3ds a jeho obrázky .tga,
díly pojmenované Main_Body, Main_Turre, Main_Barre...).

## 2. Vytvořte jednotku

V záložce **Jednotky** klikněte nahoře na **Nová jednotka (import modelu)**, pak vyberte jednotku, ze které začnete
(pro tank tank: pro Abrams Sherman). Dejte jí název a klikněte na **Vytvořit**: stránka nové jednotky se otevře na
**Importovat model…**. Model nové jednotky se bude otáčet a jezdit jako model této jednotky. Stránka jednotky hry má
stejnou cestu: **Nová jednotka z této…** pod **Vlastní model**. (Studio 0.9.6 zatím nemá ani jedno tlačítko: otevřete
jednotku a na její stránce zvolte **Nová jednotka…**.)

## 3. Import

Na stránce nové jednotky, pod **Vlastní model**:

1. Nastavte **Velikost**: její délka vůči kopírované jednotce. **1** je stejně dlouhá; M1 Abrams vůči Shermanu je
   **1.36** (jejich skutečné délky).
2. Klikněte na **Importovat model…** a vyberte .3ds nebo .glb.

Studio ho napasuje na jednotku: natočený dopředu (tam, kam míří jeho kanón), jeho délku, umístěný tam, kde stojí
kopírovaná jednotka, s věží, která se otáčí tam, kde je na vašem modelu, stojící na zemi. Jeho obrázky se stanou jeho
vlastními texturami. Stránka ho ukáže ve 3D, i to, které díly se otáčejí s věží. Pokud se nějaký obrázek nenašel,
řekne který: dejte obrázky vedle modelu a importujte znovu.

Uloží se do vašeho modu jako `files/models/<the unit's name>.glb`. **Použít model kopírované jednotky** ho zase vyjme.

**Jeho velikost později:** posuvník pod polem velikosti jde od **Drobný** po **Obrovský** (0.05 až 20), s vyznačenou
**Velikost ze hry** (1) a u jednotky z jiné éry i **Skutečná velikost**; klikněte na **Změnit velikost** a model se
napasuje znovu ze svého vlastního souboru. S několika novými letadly (nebo pozemními jednotkami) změní jedno kliknutí
velikost všem. Hra čte model při načítání, takže nová velikost se ukáže od dalšího sestavení.

**Kde sedí:** nový model se umístí doprostřed jednotky, kterou kopíruje, takže většina modelů tu nic nepotřebuje.
Pokud ten váš nesedí správně, otevřete **Posunout** pod velikostí (u modelu, který jste posunuli, zůstane otevřené).
Má tři čísla, **Vpřed**, **Vpravo** a **Nahoru**, v jednotkách hry (stránka uvádí, jak dlouhá je kopírovaná jednotka
v těchto jednotkách). Mínus posouvá opačným směrem a 0, 0, 0 ho vrátí tam, kam byl napasován. Klikněte na
**Posunout** a model se napasuje znovu ze svého vlastního souboru, posunutý o tolik; jeho věž a vrtule jdou s ním,
takže se pořád otáčejí na správném místě. Ve 3D pohledu je modrý kruh místo, kde stojí kopírovaná jednotka, a značka
na kruhu je předek. Nová velikost posun zachová. Model napojený na vlastní kosti jednotky (voják, obsluha děla) zůstane
tam, kde jsou jeho kosti: ten posuňte v Blenderu. Model importovaný Studiem starším než 0.9.8.17 si nechá své staré
místo (věž na věži kopírované jednotky), i po změně velikosti, dokud ho znovu neimportujete nebo neposunete; modely
jednotek z jiné éry si nechají svá místa.

**Letadla:** letadlo otevřené v Blenderu ze Studia a přenesené zpět je natočené dopředu a ponechá si vrtule tam, kde
je má váš model, a tolik, kolik jich má, ať už mělo kopírované letadlo jakékoli: listy na zemi, roztočené kotouče ve
vzduchu. Viděno ve hře. Model odjinud si nechá vrtule tak, jak jsou v něm nakreslené, nehybné: import zatím nepozná,
které jeho díly jsou vrtule. Ve 3D pohledu jsou kotouče letadla průhledné, tak jak hra kreslí roztočenou vrtuli.

**Vojáci, obsluhy a další letadla:** vojáci, obsluha děla a letadla, na která Studio dřív model napasovat neumělo
(například P-47), dostanou vlastní model také, pokud je napojený na vlastní kosti jednotky: třeba jeden z modelů hry
otevřený v Blenderu ze Studia a tam upravený. Na ty kosti jde tak, jak je, nic se neposouvá ani nemění velikost, a
ostatní muži družstva se stejnými kostmi ho nosí také. Viděno ve hře se střeleckým družstvem, obsluhou děla a P-47.

**Vaši hráči:** mod s modelem importovaným Studiem 0.9.8.17 nebo novějším potřebuje Launcher 0.4.8.17 nebo novější:
starší dá modelu kostru kopírované jednotky, takže se jeho věž otáčí kolem špatného bodu. 0.4.8.17 je povinná
aktualizace, takže ji Launcher nainstaluje sám.

## 4. Jeho karta, pak test

Otáčejte 3D pohledem, dokud nový model v čárkovaném rámečku nevypadá správně, a klikněte na **Použít tento pohled jako
kartu** (viz [[Úprava jednotek|Úprava-jednotek]]). Pak **Vyzkoušet ve hře**: jednotka je v bitvě u své továrny.

## Změna v Blenderu

`files/models/<the unit's name>.glb` se v Blenderu otevře jako jakýkoli .glb. Ponechte oba názvy objektů (`chassis` pro
korbu, `tourelle_01` pro věž) a exportujte ho přes stejný soubor (glTF Binary): další sestavení ho použije.

**Otevřít v Blenderu** na stránce jednotky pojmenuje kost každého dílu tak, jak to dělá hra, takže tank ze hry otevřený
v Blenderu a importovaný zpět si ponechá otáčivou věž (Studio 0.9.8.8; model exportovaný dřív si nechá stará jména:
otevřete ho v Blenderu znovu).

**Model, který seděl na špatném místě** (Studio 0.9.8.7 a starší, na nových jednotkách vytvořených z Panthera a 85
dalších jednotek, jejichž věže Studio četlo špatně): použijte na té jednotce znovu **Importovat model…** a bude sedět
na věži.

## Zatím v začátcích

- Pásy a kola se zatím neotáčejí: pohybují se s korbou.
- Záblesk kanónu a vrak jsou z kopírované jednotky.
- Obrázky jsou nejvýš 1024 na šířku, jako vlastní obrázky jednotek hry.
- Vyzkoušeno ve hře s vlastními modely hry (Sherman, dvě letadla, střelecké družstvo, obsluha děla): zatím ne
  s modelem odjinud, jiným tankem s věží, věží, která se otočí dokola, ani s letadlem, které kopíruje jednotku bez
  vrtulí.

Z příkazového řádku: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. S `--move` se napasuje tak, jak ho napasuje
Studio: `--move 50 0 -10` ho posune o 50 dopředu a o 10 dolů od místa, kam je napasovaný (vpřed, vpravo, nahoru),
a `--move 0 0 0` ho tam nechá. Bez `--move` ho příkaz pořád napasuje postaru, s věží na věži kopírované jednotky.

**Další:** [[Export a sdílení|Export-a-sdílení]]

---

[[Polní příručka|Polní-příručka]] · [[English|Import-a-Model]]
