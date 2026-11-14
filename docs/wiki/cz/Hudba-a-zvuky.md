# Hudba a zvuky

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.9.8.8 nebo novější, mod; pro vlastní zvuk zvukový soubor (WAV,
> MP3, OGG nebo FLAC), pro vlastní pohyby soubor motion capture (.bvh) · **Zabere:** pár minut na každou věc

Všechno se tu dělá ve Studiu, v záložce **RUSE Decoy**, návrháři zvuku a animací (ve Studiu 0.9.8.8 nahradil záložku
Hudba). Žádný další program k instalaci.

## Každý zvuk ve hře

**RUSE Decoy** uvádí vlevo každý zvuk, který hra má, podle druhu: zbraně zblízka a zdálky, zásahy a ničení, motory
a kroky, okolí, pozadí map, rozhraní, karty lstí, hlasy jednotek, velitelství a zpravodajství, rádiový hovor, repliky
misí (s tím, co která říká), hudbu a znělky. Pole hledání najde zvuk podle názvu nebo podle slov, která v něm zazní.

U každého zvuku:

- **Přehrát** ho pustí.
- **Hlasitost:** táhněte ji. 100 % je hlasitost ze hry, až do 200 %.
- **Nahradit…** otevře editor níže, abyste na jeho místo dali vlastní zvuk.

Změny se ukládají do vašeho modu a do hry se dostanou, když ho vyzkoušíte nebo exportujete.

## Nahrazení zvuku nebo skladby

1. Přetáhněte na editor zvukový soubor, nebo ho vyberte. Ten váš může mít jakoukoli délku: Studio ho převede do
   formátu hry.
2. Ořízněte ho dvěma úchyty, **Zesílení na začátku** a **Zeslabení na konci**, nastavte **Hlasitost** a poslechněte si
   ho.
3. **Použít** ho uloží do vašeho modu. Později ho **Změnit…** znovu otevře a **Odebrat** vrátí zvuk ze hry.

## Přidání skladby

Pod **Hudba a znělky** jsou skladby uvedené podle toho, kde hrají: hlavní nabídka, titulky, tři seznamy, ze kterých se
hraje v bitvách, konec zápasu, cíle misí a kapitoly kampaně a Operace, které je uvádějí. Tři seznamy bitev: klidný,
zatímco hráči budují, bojový, jakmile dopadnou první střely, a hudba lstí, když se zahraje karta lsti.

Pod každým seznamem bitev je **Přidat skladbu…**: dejte jí název, přetáhněte zvukový soubor, ořízněte ho, pak
**Použít**. Přidá se ke skladbám, které hra z toho seznamu hraje, s označením Nová.

## Animace

Pod **Animace**: jak se jednotky pohybují, od běhu, střelby a nabíjení po umírání a obsluhu děla při práci. U každé je
uvedeno, jak ji nazývá hra a kolik jednotek ji hraje. **Prohlédnout a změnit…** ji ukáže ve 3D na jednotce, která ji
hraje (tažením ji otočíte, kolečko přibližuje; 3D pohled jednou potřebuje internet):

- **Rychlost:** 100 % je rychlost ze hry, 200 % dvakrát rychleji, 50 % poloviční rychlostí.
- **Použít místo:** jiná animace stejného těla na jejím místě (střelci by například mohli běhat tak, jak utíkají).
- **Kost**, s **Velikost** a **Otočit kolem** / **Otočení**: jedna část těla zvětšená nebo otočená po celou animaci
  (co je k ní připojené, roste s ní).
- **Zpět na původní** vezme zpět každou její změnu.

Jakou animaci jednotka hraje pro každou činnost, změna jen pro jednu jednotku, kopie pro jednotky, které vybereš, a
animace nové jednotky v Blenderu: [[Animace jednotek|Animace-jednotek]].

## Motion capture

Dejte na animaci pohyb skutečného člověka, pod **Motion capture**: vyberte pohyb z knihovny pohybů (3 205 volných
pohybů z databáze motion capture CMU a 100STYLE, každý se stáhne, když ho vyberete), nebo **Vybrat soubor motion
capture…** s vlastním (.bvh, z Mixama, Blenderu nebo jakéhokoli programu pro motion capture).

1. Vyberte, kterou jeho část použít: **Od** (v sekundách) a **Jak dlouho**. U chůze nebo běhu jeden celý krok každou
   nohou; u smrti začněte těsně před pádem.
2. **Držet na místě** nechá chůzi a běh tam, kde jednotku posouvá hra; **Opakovat dokola** plynule převede poslední
   pózu do první, pro animaci, kterou hra hraje znovu a znovu.
3. **Autoři (kdo pohyb nahrál):** u pohybů z knihovny je vyplněno; u jakéhokoli jiného souboru napište, kdo ho udělal,
   a jeho licenci. Jde všude, kam jde váš mod.
4. **Podívat se**, pak **Použít**. Změny rychlosti a kostí dál platí navrch; **Zpět na původní** ho odebere.

## Zvuky a animace jednotky

Stránka jednotky má řádek **Zvuky a animace** ve **Vzhled a pohyb**: její vlastní repliky a zvuky motoru a její
animace. **Změnit v RUSE Decoy** otevře RUSE Decoy na zvucích té jednotky (stránka budovy má vlastní rámeček **Zvuky a
animace**). Jednotka mluví replikami svého národa a druhu, takže replika
změněná tam zazní u každé jednotky, která ji sdílí. Její zbraně a zásahy jsou pod druhy zbraní a zásahů.

## Zvuk na pozadí mapy

V záložce **Mapy** ukáže **Zvuk na pozadí…** zvuk mapy: z čeho vychází a jeho tři vrstvy, každou si poslechnete a
nahradíte ve stejném editoru. Mapa může také vycházet ze zvuku na pozadí, který hraje jiná mapa.

## Co už bylo vyzkoušeno ve hře

Viděno ve hře: zvuky a animace RUSE Decoy (Studio 0.9.8.8), skladba hlavní nabídky, skladby seznamů bitev 1 a 2, nové
skladby do nich přidané a repliky jednotky. Zatím nevyzkoušeno: zvuk na pozadí mapy a seznam hudby lstí (známo z toho,
jak hra funguje). Chybové zprávy RUSE Decoy jsou zatím jen anglicky.

---

[[Polní příručka|Polní-příručka]] · [[English|Music-and-Sounds]]
