# Import modelu

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.9.6 nebo novější, mod a 3D model (.3ds, .glb nebo .gltf) ·
> **Trvá:** pár minut

Dejte nové jednotce vlastní 3D model, z Blenderu nebo z jakéhokoli jiného 3D nástroje. Tak vznikl
[mod M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods): první model přenesený do R.U.S.E. z jiného 3D programu,
viděný ve hře.

Model může jít také na novou budovu, místo jednoho dílu jejího vzhledu (viz
[[Budovy a nabídky stavby|Budovy-a-nabídky-stavby]]), nebo na vaši mapu jako vlastní kámen, předmět, keř nebo strom
(viz [[Umisťování budov a stromů|Umisťování-budov-a-stromů]]). Obojí: Studio 0.9.8.8, viděno ve hře.

Na stránce jednotky je to vše ve **Vzhled a pohyb**: **Importovat model…** je tlačítko řádku **Model** a ostatní možnosti modelu (velikost, **Posunout**, **Změnit v Blenderu**) jsou pod **Více** toho řádku. **Jeho vojáci** je samostatný řádek a co dělají animace modelu, je pod **Více** řádku **Zvuky a animace**.

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
stejnou cestu: **Nová jednotka z této…** na řádku **Model** v části **Vzhled a pohyb**. (Studio 0.9.6 zatím nemá ani jedno tlačítko: otevřete
jednotku a na její stránce zvolte **Nová jednotka…**.)

## 3. Import

Na stránce nové jednotky, na řádku **Model** v části **Vzhled a pohyb**:

1. Klikněte na **Více** a nastavte **Velikost**: její délka vůči kopírované jednotce. **1** je stejně dlouhá; M1 Abrams vůči Shermanu je
   **1.36** (jejich skutečné délky).
2. Klikněte na **Importovat model…** (tlačítko řádku) a vyberte .3ds nebo .glb.

Studio ho napasuje na jednotku: natočený dopředu (tam, kam míří jeho kanón), jeho délku, umístěný tam, kde stojí
kopírovaná jednotka, s věží, která se otáčí tam, kde je na vašem modelu, stojící na zemi. Jeho obrázky se stanou jeho
vlastními texturami. Stránka ho ukáže ve 3D, i to, které díly se otáčejí s věží. Pokud se nějaký obrázek nenašel,
řekne který: dejte obrázky vedle modelu a importujte znovu.

Uloží se do vašeho modu jako `files/models/<the unit's name>.glb`. **Použít model kopírované jednotky** ho zase vyjme.

**Kde je ve vašem počítači:** **Více** na řádku **Model** začíná právě tím: celou cestou, `Documents\RUSE 2.0\Mods\<váš mod>\files\models\<název jednotky>.glb`, a **Ukázat ve složce**, které tu složku otevře. Dokud jednotka nemá vlastní model, řekne, kde soubor bude. Jednotka s vlastní kopií modelu (**Dát mu vlastní kopii modelu** nebo **Vlastní uniforma** družstva) je ve stejné složce jako `<název jednotky>.copy.toml` a její barvy ve složce se stejným názvem.

**Jeho velikost později:** posuvník pod polem velikosti jde od **Drobný** po **Obrovský** (0.05 až 20), s vyznačenou
**Velikost ze hry** (1) a u jednotky z jiné éry i **Skutečná velikost**; klikněte na **Změnit velikost** a model se
napasuje znovu ze svého vlastního souboru. S několika novými letadly (nebo pozemními jednotkami) změní jedno kliknutí
velikost všem. Hra čte model při načítání, takže nová velikost se ukáže od dalšího sestavení.

**Kde sedí:** nový model se umístí doprostřed jednotky, kterou kopíruje, takže většina modelů tu nic nepotřebuje.
Pokud ten váš nesedí správně, použijte **Posunout** pod velikostí, v **Více** řádku Model.
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
ostatní muži družstva kreslení stejným modelem ho nosí také. Viděno ve hře se střeleckým družstvem, obsluhou děla a P-47.
Voják s těžkou zbraní, kterého hra kreslí vlastním modelem (muž s bazukou v americkém střeleckém družstvu), si ho
nechá, dokud mu nedáš model v **Jeho vojáci** (níže).

**Vaši hráči:** mod s modelem importovaným Studiem 0.9.8.17 nebo novějším potřebuje Launcher 0.4.8.17 nebo novější:
starší dá modelu kostru kopírované jednotky, takže se jeho věž otáčí kolem špatného bodu. 0.4.8.17 je povinná
aktualizace, takže ji Launcher nainstaluje sám.

## Vlastní voják krok za krokem

U družstva (střelci, výsadkáři, jakákoli pěchota) udělá Studio část v Blenderu s tebou:

1. **Vytvoř družstvo** jako v kroku 2 výše, z nějakého družstva (třeba amerických střelců).
2. **Otevři jeho vojáka v Blenderu.** Na stránce nového družstva v části **Vlastní model** klikni na **Změnit v Blenderu**. Blender se otevře s vojákem a jeho kostmi, každou tam, kde ji má hra. Nemáš Blender? **Získat Blender (zdarma)** ho nainstaluje; **Vybrat Blender…** ukáže Studiu, kde je.
3. **Změň ho, nebo nasaď vlastní model na jeho kosti.** Chceš-li ho změnit, uprav ho tam. Pro vlastní model: načti ho přes **File > Import** do téže scény a polož ho na vojáka; klikni na svůj model, **Shift+klik** na kosti, pak **Ctrl+P > With Automatic Weights**. Vojáka ze hry smaž, pokud si ho nenecháš.
4. **Pošli ho.** Klikni nahoře v Blenderu na **Poslat do R.U.S.E. Studia**.
5. **Přenes ho zpět.** Ve Studiu klikni na **Přenést model**. Tvůj model nosí střelci družstva. Družstvo, jehož vojáka s těžkou zbraní hra kreslí vlastním modelem (třeba muže s bazukou v americkém střeleckém družstvu), si ho nechá tak, jak ho má kopírované družstvo, dokud mu nedáš vlastní: řádek **Jeho vojáci** ukazuje každého z nich a jeho **Importovat model…** je jen pro něj. **Vyzkoušet ve hře** ho ukáže.

Dobré vědět:
- Tvoje soubory z Blenderu zůstávají ve složce tvého modu: `Documents\RUSE 2.0\Mods\<tvůj mod>\blender\<název jednotky>\`. Při sdílení modu se do něj nebalí. Další **Změnit v Blenderu** začne tím, co jsi poslal naposledy.
- Pod **Změnit v Blenderu** stránka řekne, kde ty soubory jsou, ještě před prvním kliknutím, a její **Ukázat ve složce** tu složku otevře, jakmile v ní Blender otevře vojáka.
- Pokud některé body tvého modelu nemají kost (automatické váhy Blenderu pár vynechají), stránka řekne kolik: hýbou se jen s boky vojáka. Namaluj je na kost v Blenderu ve **Weight Paint** a pošli znovu.
- Družstvo s **Vlastní uniforma**: tvůj model zaujme místo uniformy (její barvy zůstanou v modu) a **Použít model kopírované jednotky** uniformu vrátí.
- Máš už .glb udělaný na kostech vojáka ze hry? **Importovat model…** ho vezme tak, jak je.
- Model, který tvé družstvo nosí, je ve složce modu jako `files\models\<název jednotky>.glb`, jakmile je uvnitř; vlastní model vojáka s těžkou zbraní jako `files\models\<název jednotky>@bazooka.glb`.
- **Jeho vojáci** řekne, kde je model každého z nich uložený (nebo bude), a **Ukázat ve složce** na řádku **Model** tu složku otevře.
- **Jeho vojáci** také říká, které další figury družstva se kreslí kterým modelem: padlý voják a figura viděná zdálky (v americkém střeleckém družstvu se kreslí modelem muže s bazukou).

## Její animace: kterou hraje každá činnost

Model na vlastních kostech (kůň, kůň s jezdcem, jakýkoli tvor) si s sebou přináší své animace. Na stránce jednotky
ukazují **Její animace**, co jednotka hraje pro každou činnost ve hře:

- **Stojí na místě**, **Jde** a **Běží** jsou první: to nejmenší, co model potřebuje. Když některá nemá nic
  vlastního, stránka to řekne a ukáže, co hraje místo toho.
- Každá činnost je seznam animací modelu. Vyberte jednu, nebo nechte **Nejbližší**: pak hraje tu nejpodobnější,
  kterou model má, a seznam řekne kterou. Nejbližší znamená popořadě: animaci pojmenovanou podle té činnosti (stand
  nebo idle, walk, run nebo gallop, fire, death...), jinak to, co hraje nejbližší činnost (chůze běh, běh chůzi, pak
  stání; výstřel míření, pak stání; každá smrt obyčejnou smrt). Sestavení se řídí stejným pravidlem: co řekne stránka,
  to hra hraje.
- Animace, jejíž jméno začíná t_ nebo b_ (hr_t_fire, hr_b_run), hraje jen na horní nebo dolní polovině těla:
  jezdcova nahoře, jeho koně dole.
- **Všechny ostatní činnosti** vypíše zbytek, podle druhu: na místě, pohyb, míření a střelba, těžká zbraň, zásahy,
  smrt.
- **Na dlouhých přesunech** hra posadí četu do jejího auta. Jednotka s vlastními animacemi jde místo toho sama a hraje
  animaci tam vybranou (svůj běh, když necháte Nejbližší), stejně rychle jako její auto. Vyberte **Ve svém autě**,
  chcete-li auto ponechat.

**Kopie si nechává animace:** jednotka zkopírovaná z jednotky s vlastními animacemi hraje tytéž. Chcete-li některou
změnit jen pro ni, klikněte na **Změnit v RUSE Decoy** na jejím řádku **Zvuky a animace** a pak na **Jen tato jednotka**.

Horse Squad udělaný takto ve Studiu ve hře fungoval (listopad 2026).
## Model s vlastními kostmi a animacemi

Kůň, kůň s jezdcem, jakýkoli tvor: model na vlastních kostech jde na družstvo i se svými animacemi.

1. **Udělej ho v Blenderu**: tvůj model na armatuře s vlastními kostmi (pojmenovanými, jak chceš) a akci pro každou animaci. Pojmenuj akce podle toho, co ukazují: aspoň **stand** (nebo **idle**), **walk** a **run**; známé jsou i **death**, **fire**, **reload**, **hit**, **crouch**, **aim**, **look**, **flee** a **grenade**.
2. **Exportuj ho**: **File > Export > glTF 2.0**, formát **glTF Binary (.glb)**, se zaškrtnutým **Animation**.
3. **Vytvoř družstvo** jako v kroku 2 výše. Na jeho stránce klikni na **Importovat model…** na řádku **Model** v části **Vzhled a pohyb** a vyber svůj .glb. Studio pozná, že jeho kosti nejsou vojákovy, a vezme ho s vlastními kostmi a všemi animacemi. Stránka ukáže, kolik má kostí, každou animaci s její délkou a kolik akcí družstva ji hraje.
4. **Vyzkoušet ve hře** ho ukáže.

Dobré vědět:
- Každá akce družstva hraje animaci pojmenovanou pro ni. Akce, pro kterou žádná animace pojmenovaná není, zatím žádnou nemá: stránka řekne kolik.
- Změnil jsi ho v Blenderu? Importuj ho znovu: každá akce si nechá svou animaci, dokud je animace toho jména v souboru.
- Tvůj mod uchová model i každou animaci: `files\models\<název jednotky>.glb` a každou animaci jako `files\anim\own\<název jednotky>\<její název>.baf`.
- **Použít model kopírované jednotky** model zase odebere, i s jeho animacemi.
- Družstvo s vojákem s těžkou zbraní: dej mu vlastního koně s jezdcem v **Jeho vojáci**, udělaného na stejných kostech jako model střelců, a bude hrát jejich animace. Na jiných kostech hraje to, co v kopírovaném družstvu, a stránka tě varuje: to může hru zastavit. Odebrání modelu střelců odebere i jeho.
- Horse Squad udělaný takto ve Studiu ve hře fungoval (listopad 2026); nic jiného takto udělaného zatím ve hře vyzkoušeno nebylo.

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
- Nová jednotka zkopírovaná z taženého děla, FCM F1, Pumy, polopásového vozidla, Bren Carrieru, letadla pro výsadkáře,
  některých bunkrů a několika dalších dostane také model odjinud, nejen model napojený na její kosti, a kreslí se tak
  jako ta jednotka. Ve hře zatím nevyzkoušeno.

Z příkazového řádku: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. S `--move` se napasuje tak, jak ho napasuje
Studio: `--move 50 0 -10` ho posune o 50 dopředu a o 10 dolů od místa, kam je napasovaný (vpřed, vpravo, nahoru),
a `--move 0 0 0` ho tam nechá. Bez `--move` ho příkaz pořád napasuje postaru, s věží na věži kopírované jednotky.

**Další:** [[Export a sdílení|Export-a-sdílení]]

---

[[Polní příručka|Polní-příručka]] · [[English|Import-a-Model]]
