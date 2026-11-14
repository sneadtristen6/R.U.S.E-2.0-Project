# Animace jednotek

> **Potřebuješ:** RUSE Studio 0.9.8.20 nebo novější a mod; Blender (zdarma), abys mohl měnit animace nové jednotky v
> Blenderu · **Zabere:** 10 minut čtení

To, jak se jednotka hýbe (stojí, jde, běží, míří, střílí, umírá), jsou její **animace**. Tahle stránka říká, k čemu
slouží animace hry, kterou jednotka hraje pro každou svou činnost, každý způsob, jak jednu změnit (pro jednu jednotku,
pro všechny, pro jednotky, které vybereš, nebo v Blenderu), a jak se vrátit k té ze hry.

## Co je animace

- Animace hýbe kostmi modelu v čase: krok běhu, puška zvednutá k rameni, pád (viz [[Modely a kosti|Modely-a-kosti]]).
- Každá věc, kterou jednotka ve hře dělá (**činnost**: stojí na místě, jde, běží, střílí...), hraje animaci. Voják hraje
  dvě najednou, jednu pro každou polovinu těla.
- Mnoho jednotek sdílí animace hry: každý americký střelec běhá stejně. Změna animace je proto, pokud nevybereš jinak,
  změna pro všechny jednotky, které ji hrají.
- Tanky otáčejí věží a koly bez animací: pro ně tu není co měnit.

## Animace hry a k čemu která je

**RUSE Decoy** (jeho karta nahoře ve Studiu) vypisuje každou animaci hry vlevo, pod **Animace**, podle druhu:

| Druh | Co v něm je |
|---|---|
| **Pěchota** | Střelci, bazuky, výsadkáři a řidiči: stání, chůze, běh, míření, střelba, přebíjení, útěk, zásah a smrt (horní i dolní část těla má vlastní) |
| **Obsluhy děl** | Muži u děla: v klidu, při posunu, přípravě, střelbě a přebíjení |
| **Vozidla a děla** | Děla při rozložení a složení, v klidu a při střelbě a další pohyblivé části |
| **Postavy velitelství** | Důstojníci u stolu velitelství ve scénách mise (nehraje je žádná jednotka) |
| **Zvířata a kulisy** | Krávy, koně, kozy, slepice, racci a větrníky na mapách |

Každá říká, jak jí říká hra a kolik jednotek ji hraje. Na stránce jednotky se činnosti jmenují podle toho, co jednotka
dělá, seskupené takhle:

| Skupina | Její činnosti (některé) |
|---|---|
| Na místě | Stojí na místě, Přikrčí se, Rozhlíží se |
| Pohyb | Jde, Jde pozpátku, Běží, Běží doprava, Běží pozpátku, Prchá |
| Míření a střelba | Míří vestoje, Míří za chůze, Střílí, Hází granát, Přebíjí |
| Těžká zbraň | Míří těžkou zbraní, Střílí z těžké zbraně, Zvedá těžkou zbraň, Spouští těžkou zbraň |
| Zásahy | Je zasažen, Je zasažen zezadu, Je zasažen výbuchem |
| Smrt | Umírá zastřelen, Umírá ve výbuchu, Leží padlý |
| Seskok padákem | Vyskakuje, Padá, Snáší se na padáku, Přistává |
| Činnosti osádky | Čeká, Jde vpřed s dělem, Jde k dělu, Rozkládá dělo, Střílí (člen osádky), Nabíjí dělo |

## Její animace: kterou hraje každá činnost

Jednotka s vlastními animacemi (model s vlastními kostmi: kůň, kůň s jezdcem, jakékoli stvoření) má na své stránce
tabulku: **Vzhled a pohyb**, řádek **Zvuky a animace**, **Více**, pak **Její animace**.

- **Stojí na místě**, **Jde** a **Běží** jsou první: to je minimum, které model potřebuje. Nemá-li některá nic
  vlastního, stránka to řekne, a co hraje místo ní.
- Každá činnost má seznam animací modelu. Vyber jednu, nebo nech první řádek, **Nejbližší**: pak hraje nejbližší, kterou
  model má, a řádek řekne kterou. Nejbližší znamená, v tomto pořadí: animace pojmenovaná podle té činnosti (stand nebo
  idle, walk, run nebo gallop, fire, death...), jinak to, co hraje nejbližší činnost (chůze hraje běh, střelba míření
  nebo stání). Hra hraje to, co říká stránka: sestavení se řídí stejným pravidlem.
- **Všechny ostatní činnosti** vypíše zbytek, po skupinách.
- **Na dlouhých přesunech** je její poslední řádek. Na dlouhém přesunu po silnici hra posadí družstvo do jeho auta.
  Jednotka s vlastními animacemi může místo toho jet sama za sebe a hrát jednu z nich dokola (svůj běh, necháš-li první
  řádek), rychlostí svého auta. Vyber **Ve svém autě**, chceš-li si auto nechat.

Jednotka zkopírovaná z jednotky s vlastními animacemi hraje tytéž.

## Změna animace v RUSE Decoy

1. Na stránce jednotky ve **Vzhled a pohyb** klikni na **Změnit v RUSE Decoy** v řádku **Zvuky a animace**. RUSE Decoy
   se otevře na té jednotce: její zvuky, pak **Její animace** s každou animací, kterou hraje. (Nebo otevři kartu **RUSE
   Decoy** a vyber druh pod **Animace**.)
2. Klikni u animace na **Prohlédnout a změnit…**. Hraje se ve 3D na jednotce, která ji hraje: tažením ji otočíš,
   kolečko přibližuje. 3D pohled jednou potřebuje internet.
3. Otevřená ze stránky jednotky se první řádek ptá **Změnit pro**:
   - **Jen tato jednotka**: tato jednotka hraje vlastní kopii animace s tvými změnami; všechny ostatní ji hrají jako
     dřív. Je vybraná na začátku, pokud animace už není změněná pro všechny jednotky.
   - **Všechny jednotky, které ji hrají**: změna jde do samotné animace, pro všechny jednotky, které ji hrají (číslo
     říká kolik).
   - **Vaše kopie** a její název: ukáže se, když tato jednotka hraje tvoji kopii (níže); pak je vybraná na začátku ona.
4. Změň ji:
   - **Rychlost**: 100 % je rychlost hry, 200 % dvakrát rychleji, 50 % dvakrát pomaleji. Uloží se, když pustíš.
   - **Použít místo**: jiná animace stejného těla na jejím místě (střelci by mohli běhat tak, jak prchají).
   - **Kost**, s **Velikost**, **Otočit kolem** a **Otočení**: část těla větší nebo otočená po celou dobu animace.
   - **Motion capture**: pohyb skutečného člověka na jejím místě (viz [[Hudba a zvuky|Hudba-a-zvuky]]).
5. Klikni na **Hotovo**. Každá změna se hned uloží do tvého modu a do hry jde, když testuješ nebo exportuješ.

## Kopie animace pro jednotky, které vybereš

**Kopírovat tuto animaci…** udělá kopii, kterou hrají jen jednotky a vojáci, které zaškrtneš: vlastní běh pro tři tvoje
družstva, například, a jen pro vojáka s bazukou čtvrtého.

1. V okně animace klikni na **Kopírovat tuto animaci…**, dej kopii název (vidíš ho jen ty) a klikni na **Udělat kopii**.
   Začne taková, jaká je animace teď, a otevře se ve stejném okně.
2. Změň ji jako výše.
3. V **Kdo ji hraje** zaškrtni jednotky, které hrají kopii: nejdřív **Vaše jednotky**, pak **Jednotky hry**. U jednotky,
   kde ji hraje víc vojáků nebo dílů, zaškrtni jen některé. **Najít jednotku** hledá podle názvu nebo země.
4. Kopii nehraje nic, dokud nezaškrtneš jednotku: řádek pod jejím názvem do té doby píše „zatím ji nehraje žádná
   jednotka“.

Každá kopie je vlevo v RUSE Decoy pod **Vaše kopie**: otevři ji tam, nebo **Smazat kopii**. Vlastní kopie jednotky
(**Jen tato jednotka**) nebo animace změněná v Blenderu má pro tu jednotku přednost před kopií: seznam to píše vedle.

## Změna animací nové jednotky v Blenderu

Pro novou jednotku vytvořenou v tvém modu (jednotka hry nejdřív potřebuje novou jednotku vytvořenou z ní):

1. Na stránce jednotky klikni na **Změnit v RUSE Decoy**. Nad jejími animacemi klikni na **Změnit jeho animace v
   Blenderu**. Blender se otevře s jednotkou a každou animací, kterou hraje, každá pojmenovaná podle toho, co v ní dělá,
   a za tím jméno, které jí dává hra.
2. Dole v Blenderu je vypíše Action Editor: vyber jednu. **Mezerník** ji přehraje.
3. Klikni na kost, stiskni **Ctrl+Tab** pro Pose Mode, **R** pro otočení (**G** ji posune), pak **I**, aby se póza
   v tomto snímku uložila. Udělej to v každém snímku, který měníš: Blender jde sám od jedné uložené pózy k další.
4. Klikni na **Poslat do R.U.S.E. Studia** nahoře v 3D pohledu Blenderu: odejde každá animace, změněná nebo ne.
5. V RUSE Decoy klikni na **Přenést moje změny**. Řekne, které se vrátily změněné: ty jsou teď vlastní této jednotky.
   Všechny ostatní jednotky a každá animace, na kterou jsi nesáhl, zůstávají jako dřív.

Kosti jen nastavuj do póz: nepřejmenovávej je, nemaž je a nepřesouvej je v Edit Mode. Jinak Studio nic nepřevezme a
řekne, které kosti.

Model s vlastními kostmi (kůň, jakékoli stvoření) posílá vlastní animace pod jejich vlastními jmény. Ta, kterou změníš,
zaujme své místo: každá činnost, která ji hrála, ji hraje změněnou.

## Návrat k animaci hry

| Co odebrat | Klikni na | Kde |
|---|---|---|
| Změnu pro všechny jednotky | **Zpět na původní** | Řádek animace v RUSE Decoy nebo její okno |
| Vlastní kopii této jednotky (**Jen tato jednotka**) | **Zpět na tu, kterou hrají všechny jednotky** | Řádek animace v seznamu jednotky nebo její okno |
| Změny kopie (název a zaškrtnutí zůstanou) | **Zpět na animaci hry** | Okno kopie |
| Kopii, celou | **Smazat kopii** | **Vaše kopie** |
| Změnu udělanou v Blenderu | Vrať ji zpět v Blenderu, dokud je ten Blender ještě otevřený, pak **Přenést moje změny**: vrátí se i v tvém modu | Blender, pak RUSE Decoy |

Tlačítka výše neodebírají změnu udělanou v Blenderu.

## Co ti může říct Přenést moje změny

| Píše | Co dělat |
|---|---|
| „Změněné v Blenderu, nyní vlastní této jednotky: ...“ | Nic: povedlo se. **Vyzkoušet ve hře** to ukáže. |
| „Každá animace se vrátila taková, jaká odešla.“ | Nic se nezměnilo. Uložil jsi každou pózu klávesou **I**? |
| „Vytvořené v Blenderu, zatím je nehraje žádná akce: ...“ | Nová animace se nepřevezme. Ulož ji v Blenderu (**File > Save**), chceš-li si ji nechat. |
| „Neodeslané zpět (smazané nebo přejmenované v Blenderu), takže hrají jako dřív: ...“ | Vrať jí v Blenderu jméno, chceš-li svou změnu dovnitř. |
| „Tyto hrají jen na jedné polovině těla ...“ | Kosti, kterými jsi hýbal, jsou v druhé polovině: hýbej kostmi poloviny, která ji hraje. |
| „Kosti vytvořené v Blenderu, které kostra této jednotky nemá ...“ | Novou kost nejde přehrát; zbytek dorazil. |
| „Editor NLA v Blenderu hraje tyto s vlastním časováním ...“ | Hra je hraje tak, jak je ukazuje Action Editor. |
| „Scéna Blenderu běžela na ... snímků za sekundu a hra běží na 30 ...“ | Nastav Blender na 30 snímků za sekundu, abys viděl rychlost hry. |
| „Scéna Blenderu má zapnuté Time Stretching ...“ | Nastav Old a New na stejné číslo, abys viděl rychlost hry. |
| „Žádná činnost této jednotky tyto animace nehraje ...“ | Vyber ji pro činnost v **Její animace** na stránce jednotky. |
| „Změněné ve Studiu od chvíle, kdy odešly do Blenderu, a z Blenderu poslané zpět beze změny, takže zůstává změna ze Studia ...“ | Nic: tvoje změna v RUSE Decoy zůstává. |
| „Změněné také ve Studiu od chvíle, kdy odešly do Blenderu: změna z Blenderu nahrazuje změnu ze Studia ...“ | Nic, pokud chceš změnu z Blenderu; jinak udělej svou změnu v RUSE Decoy znovu. |
| „Od posledního přenesení tvých změn nepřišlo z Blenderu nic nového.“ | Nejdřív klikni v Blenderu na **Poslat do R.U.S.E. Studia**. |

## Co se může pokazit

- **Ve hře se nic nemění:** změna pro **Jen tato jednotka** je vidět jen na té jednotce a kopie jen na jednotkách
  zaškrtnutých pro ni. Změna udělaná v Blenderu má pro tu jednotku přednost před pozdější změnou stejné animace přes
  **Jen tato jednotka** nebo kopii (pravidlo Studia; ve hře zatím nevyzkoušeno).
- **„Vlastní animace dostane jen nová jednotka vytvořená v tomto modu“**: je to jednotka hry. Nejdřív z ní udělej novou
  jednotku (**Nová jednotka z této…** na její stránce).
- **Na stránce chybí Její animace:** tabulka je jen u jednotky s vlastními animacemi (model s vlastními kostmi).
  Všechny ostatní jednotky hrají animace hry: měň je v RUSE Decoy.
- **Odeslání, které jsi nikdy nepřenesl:** nové otevření Blenderu ho odloží. RUSE Decoy ho ukáže s **Přenést odložené
  odeslání** a **Přesunout do Koše** (viz [[Otevřít v Blenderu|Otevřít-v-Blenderu]]).

## Co bylo vyzkoušeno ve hře

- Změny animací v RUSE Decoy pro všechny jednotky, které je hrají (Studio 0.9.8.8).
- **Jen tato jednotka**: družstvo tančící na místě, zatímco všechna ostatní družstva stála jako dřív (listopad 2026).
- **Kopírovat tuto animaci…**: kopie, kterou hraje jedno družstvo a jeden voják jiného (listopad 2026).
- **Změnit jeho animace v Blenderu**: družstvo stojící a běžící se zdviženou paží a Univerzální jízdní družstva, jejichž
  koně drží hlavu nahoře (listopad 2026).
- Vlastní animace Univerzálního jízdního družstva vybrané přes **Nejbližší** a jízda sama za sebe na dlouhých přesunech
  (listopad 2026).
- Ve hře zatím nevyzkoušeno: rychlost, náhrada nebo kost změněná jen pro jednu jednotku, a jiná animace vybraná ručně
  v **Její animace**.

Pořád nevíš? Zeptej se na [Discordu](https://discord.gg/h54t5baNsC), nebo se podívej na
[[Když se něco pokazí|Když-se-něco-pokazí]].

**Další:** [[Otevřít v Blenderu|Otevřít-v-Blenderu]] · [[Modely a kosti|Modely-a-kosti]]

---

[[Polní příručka|Polní-příručka]] · [[English|Unit-Animations]]
