# Ekonomika, AI a další: nástroje od LittleGroove

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.9.8.1 nebo novější a mod · **Trvá:** jak dlouho chcete

RUSE-Mod-Manager od LittleGroove měl nástroje, které Studio nemělo. Teď jsou ve Studiu, každý ve vašem vlastním modu:
změna se tam uloží hned a soubory hry se nikdy nemění.

## Záložka Nastavení počítače a hráčů

Jedna záložka ve třech částech: **Nastavení hráčů**, **Pravidla hry** a **Počítačoví hráči**.

### Nastavení hráčů

Počáteční peníze a příjem, zásobovací sklady (peníze za náklaďák, náklaďáky v konvoji, čas mezi konvoji), limity
výroby a karty lsti, se kterými každá strana začíná. Změna platí pro všechny herní režimy; kde má jaderný režim vlastní
hodnotu, dostane i vlastní pole. Zásobovací sklady a administrativní budovy jsou budovy: jejich cena, doba stavby
a odolnost jsou v záložce **Jednotky**.
Viděno ve hře: počáteční peníze a karty lsti na začátku.

**Sklady na mapách** (v části Zásobovací sklady): dejte každému zásobovacímu skladu víc náklaďáků, tedy víc peněz, na
**Všechny mapy** nebo **Jedna mapa:**, jak si vyberete. Vynásobte náklaďáky každého skladu (**krát jejich náklaďáky**)
nebo jim všem dejte stejný počet (**náklaďáků každý**). Řádek nad tím říká, co sklad s vašimi hodnotami obsahuje. Sklad,
kterému jste v záložce Mapy dali vlastní náklaďáky, si je ponechá. Mody s více než 1 000 náklaďáky na sklad hrajte
s Launcherem 0.4.8.4 nebo novějším. Viděno ve hře (sklady na mapě Den D s 500 náklaďáky; ostatní mapy s trojnásobkem
svých).

### Pravidla hry

Každé další pravidlo, které hra drží pro všechny hráče, ve skupinách: bitva a kapitulace, populace, pohyb a silnice,
palba a cíle, jednotky samy od sebe, poškození a přitlačení k zemi, lesy a výhled, letadla, karty lsti v akci, ovladač,
stavění budov, hodnocené hry online, obrysy a šipky, efekty na obrazovce, barvy stran a sektorů (každá s výběrem barvy)
a nakonec pár hodnot, jejichž použití zatím není známé. U každého je napsáno, co dělá a jakou hodnotu má hra. Zatím
nevyzkoušeno ve hře.

### Počítačoví hráči

Jak počítačoví hráči hrají. Počítačový hráč kombinuje tři sady hodnot: **Výchozí**, svou obtížnost a svůj profil (obojí
se vybírá v lobby hry); vyberte jednu, abyste viděli a měnili její hodnoty: kdy začne útočit, jak silný chce být, než
zaútočí, jak se brání, jaké jednotky upřednostňuje a jeho karty lsti. Každou hodnotu lze změnit v každé sadě: hodnota, kterou
sada neuvádí, se ve hře počítá jako 0, a když jí dáte číslo, přidá se do vašeho modu. Pod nimi je to, co platí pro
všechny počítačové hráče (hodnota armády, při které zaútočí, jeho makety...).
Viděno ve hře: karta lsti vyjmutá z nabídky, jiná v ní přesunutá, jak dlouho karta trvá a kdy začne útočit obtížnost
Snadná. Zbytek zatím nevyzkoušen ve hře.

**Skripty map a misí**, pod tím: skripty, které hra spouští na svých mapách (kapitoly kampaně, výzvy, operace),
zobrazené jako Python ke čtení. **Kopírovat** jeden zkopíruje.

## Pole Vylepšení a výzkum na stránce jednotky

Na stránce jednotky: jednotka, jejímž je vylepšením (**Vylepšení jednotky**), její vlastní vylepšení a její cena a doba
výzkumu. Vyberte jinou jednotku, nebo **Žádná: samostatná jednotka**. Viz [[Úprava jednotek|Úprava-jednotek]].

## Záložka Všechny hodnoty a soubory

Dvě části, mezi kterými přepínáte přepínačem nahoře nad seznamem.

**Všechny hodnoty:** jakýkoli objekt a hodnota hry, změněné ve vašem modu: přidejte nebo vyjměte hodnotu, vytvořte nebo
smažte objekt, dejte textové hodnotě vlastní slova. Zatím nevyzkoušeno ve hře.

**Soubory:** jakýkoli soubor uvnitř balíků hry: vyberte balík, pak soubor, a uvidíte ho takový, jaký je (obrázek,
textová tabulka, skript mise...). **Uložit kopii…** ho uloží ven; **Nahradit vlastním souborem…** vloží do vašeho modu
váš soubor; **Přidat vlastní soubor do tohoto balíku…** přidá nový. Váš mod si drží jen to, co změníte, nikdy kopii
souboru hry. Zatím nevyzkoušeno ve hře.

## Mise a mapy

Skripty mise lze měnit a Studio kontroluje, zda je mise v nabídkách, zda se načte každý soubor, který potřebuje, a její
texty; v její nabídce ji lze posunout nahoru nebo dolů. Na mapě: názvy měst a kopců, pojmenované body a zóny a název
a natočení prvku mapy. **Poznámky** si můžete vést u jednotky, hodnoty nebo počítačového hráče. Zatím nevyzkoušeno ve
hře.

## V Launcheru: Převést starý mod

Starší mod, který přichází jako vlastní balíky hry, určené ke zkopírování do složky hry, se stane modem, který vaše
knihovna hraje vedle ostatních: viz [[Instalace a hraní|Instalace-a-hraní]].

---

[[Polní příručka|Polní-příručka]] · [[English|Economy-AI-and-More]]
