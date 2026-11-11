# Úprava jednotek

> **Pro:** moddery · **Potřebujete:** RUSE Studio a mod · **Trvá:** jak dlouho chcete

## Najděte jednotku

Záložka **Jednotky** uvádí každou jednotku a budovu. Zúžit seznam můžete pomocí:

- pole **hledání** (kódové názvy nebo názvy, které vidí hráči, v kterémkoli z deseti jazyků hry: tlačítko jazyka nahoře).
  Každé napsané slovo musí sedět; **#štítky** seznam zúží (`#us`, `#germany`, `#air`, `#armor`, `#new` pro nové
  jednotky vašeho modu; napište `#` a uvidíte je všechny) a vaše nedávná hledání se uchovávají;
- štítků **druhu** a **národa**;
- nabídky **typu**: k čemu slouží, například velitelství, peníze, továrny, pevnosti a makety u budov, nebo továrna,
  která jednotku vyrábí.

## Změňte hodnotu

1. Klikněte na jednotku. Její hodnoty jsou uvedené po oddílech (cena, pancéřování, rychlost, zbraně...).
2. Napište novou hodnotu. Hned se uloží do vašeho modu; hodnota ze hry se ukazuje vedle ní.
3. **Zpět** vedle hodnoty vrátí hodnotu ze hry.

## Příznaky: co jednotka je a co umí

Příznaky jsou přepínače zapnuto/vypnuto, očíslované 0 až 104, které hře říkají, co jednotka je (letadlo, náklaďák,
pěchota, budova...) a co umí (vjet do lesa, vidět všude kolem, střílet jen na rozkaz...). Na stránce jednotky se
zobrazují jako štítky, každý se svým názvem: najeďte na jeden myší a uvidíte přesně, co dělá, jak ho použít a jak moc
si tím jsme jistí. Křížek jeden odebere; **Přidat příznak…** jeden přidá, seřazené podle toho, k čemu příznaky slouží.

**Průvodce flagy: všechny vysvětlené** (pod příznaky) otevře celý seznam s polem hledání. U každého příznaku říká:

- **co to je a co dělá** ve hře;
- **jak ho použít**;
- **jak moc si jsme jistí:** *vyzkoušeno ve hře*, *z jednotek hry* (co mají společného jednotky hry, které ho mají),
  *očekávané, zatím nevyzkoušené*, *hra ho nastavuje sama* (zapíná a vypíná je za běhu: v seznamu jednotky nic
  nedělají), nebo *nepoužívaný*.

**Studio kontroluje příznaky každé jednotky** pokaždé, když je změníte, a znovu před spuštěním hry:

- **Známé pády zastaví sestavení**, takže hra se s nimi nikdy nespustí. Stránka jednotky řekne proč a nabídne opravu
  (**Odebrat 62**, **Přidat 100**):
  - 62 (náklaďák) nebo 63 (stavební náklaďák) na čemkoli, co není náklaďák: hra spadne na začátku zápasu;
  - 99 (průzkumné letadlo) na letadle se zbraněmi, bez 100 (stíhačka): hra spadne, když letadlo pošlete útočit.
    Použijte pole **Role** (Průzkumný si ponechá své útoky) nebo přidejte 100;
  - 59 (výsadkový transport) na čemkoli kromě letadla, nebo na letadle bez jednotky k vysazení.
- **Co nejspíš jednotku rozbije, je varování**, ne zastavení: 2 (letadlo) na pozemní jednotce, 4 (budova) nebo 49 na
  jednotce, 6 nebo 76 na jednotce, která se má pohybovat (stojí na místě), 42 (pěchota) na vozidle, nebo odebrání 43
  (tým ji započítává) či 22 (hráč jí může dávat rozkazy).

Užitečné, vyzkoušené ve hře: odeberte **11, 21 a 55** najednou a vozidlo může vjet do lesa; **1** dá jakékoli jednotce
nepřímou palbu; **71** vidí všude kolem; **77** střílí jen na rozkaz.

**Vlastní typy flagů** (Studio 0.9.8.8): **Vytvořit nebo změnit typy flagů…** pod příznaky jednotky vytvoří
pojmenovanou sadu příznaků hry, každý přepnutý na **Zap.** nebo **Vyp.**, s řádkem o tom, k čemu slouží. **Dát typ
flagů…** u jakékoli jednotky tyto příznaky naráz zapne a vypne; jeho odebráním se příznaky jednotky vrátí, jak byly.
Změňte typ a změní se i každá jednotka, která ho má. Hra jedná jen podle svých vlastních příznaků, takže typ kombinuje,
co už dělají. Zatím nevyzkoušeno ve hře.

## Vytvořte novou jednotku

Nová jednotka začíná jako kopie jednotky hry, s vlastním názvem, takže ji můžete měnit, aniž byste sahali na
originál. Záložka Jednotky má nahoře dvě tlačítka: **Upravit jednotku** (seznam, pak hodnoty jednotky a Blender)
a **Nová jednotka (import modelu)**. U **Nová jednotka** vyberte jednotku, ze které začnete, dejte jí název a klikněte
na **Vytvořit**; pak ji měňte jako kteroukoli jinou. Nebo vyberte jednotku a na její stránce zvolte **Nová jednotka…**.

## Změňte, jak jednotka vypadá

Stránka jednotky ukazuje její **3D model**: tažením ho otočíte, kolečkem myši přiblížíte.

Pod ním **Vzhled a pohyb** shromažďuje vše o tom, jak jednotka vypadá a jak se pohybuje, řádek pro každou věc, v
pořadí, v jakém pracujete: **Model**, **Jeho vojáci** (družstvo, jehož střelci a voják s těžkou zbraní mají různé
modely), **Animace**, **Zvuky** a **Jezdí v**. Každý řádek říká, co jednotka teď má, a má jedno tlačítko pro obvyklou
věc; **Více** ukáže přímo tam zbytek možností řádku. Vše, co změníte, se hned uloží do vašeho modu: nic k ukládání,
žádná složka k vybírání. Přemalování, vlastní kopie modelu, uniforma družstva a vlastní model jsou na řádku **Model**;
animace a zvuky se mění v RUSE Decoy z jejich řádků (**Změnit v RUSE Decoy**): animace jen pro tuto jednotku, nebo pro
všechny jednotky, které ji hrají, zvuk pro všechny jednotky, které ho hrají.

- **Přebarvení v Blenderu:** klikněte na **Otevřít v Blenderu** (Blender je zdarma; pokud ho Studio nenajde, stránka
  nabídne **Získat Blender (zdarma)** a **Vybrat Blender…**, kterým mu ukážete, kde je `blender.exe`). Jednotka se
  otevře se svými obrázky, připravená k malování na model. Malujte, pak klikněte na **Přenést zpět**: vaše
  malba přejde do vašeho modu. Viděno ve hře, zblízka i zdálky.
- **Její karta v nabídce stavby:** otáčejte a přibližujte 3D model, dokud uvnitř čárkovaného rámečku nevypadá správně,
  pak **Použít tento pohled jako kartu**. **Karta ze hry** ji vrátí. Viděno ve hře. Nová jednotka má vlastní kartu:
  jednotka, kterou kopíruje, si ponechá svůj obrázek.
- **Vlastní kopie modelu:** jednotka kreslená modelem ze hry sdílí svou malbu se všemi jednotkami kreslenými stejným
  modelem. **Dát mu vlastní kopii modelu** (na její stránce) vytvoří stejný model s vlastními texturami: pak **Otevřít
  v Blenderu** přebarví jen tuto jednotku. Funguje pro nové jednotky i pro ty ze hry.
- **Uniforma družstva:** vojáci jednoho národa ve hře nosí všichni jeden obrázek (ti z USA: jejich GI, Rangers
  a výsadkáři a osádky jejich děl a vozidel), proto se **Výchozí uniforma** tady nepřebarvuje. Zvolte
  **Vlastní uniforma** a dejte družstvu vlastní, pak ji namalujte v Blenderu. Viděno ve hře.
- **Jezdí v:** náklaďák, ve který se družstvo nebo dělo na silnicích promění: ten ze hry, náklaďák jiného národa nebo
  kopie náklaďáku, kterou jste vytvořili a přebarvili. Viděno ve hře.
- **Vlastní model (nové jednotky):** **Importovat model…** přinese 3D model z Blenderu nebo jakéhokoli 3D nástroje.
  Viz [[Import modelu|Import-modelu]]. Jednotka hry si ponechá svůj model: její stránka má **Nová jednotka
  z této…**, kterou vytvoříte novou jednotku, na kterou model přijde.
- **Nová jednotka od začátku do konce:** **Nová jednotka (import modelu)** nahoře na záložce Jednotky, vyberte výchozí
  jednotku (tank pro tank, družstvo pro vojáky nebo pro koně s jezdcem), pojmenujte ji a klikněte na **Vytvořit**. Pak
  projděte **Vzhled a pohyb** shora dolů: její model, její vojáky, její animace, její zvuky, její nákladní auto. Dejte
  jí kartu, nastavte cenu a hodnoty a pak **Vyzkoušet ve hře**. Velký mod s mnoha novými jednotkami jsou stejné kroky
  pro každou: každá jednotka má to vše ve vašem modu pod svým vlastním názvem.
- **Jednotka, která nese svého jezdce (kůň, motocykl):** jeden model s jezdcem a tím, na čem jede, na jedné kostře, s
  vlastními animacemi (alespoň stání, chůze a běh), importovaný na kopírované družstvo: viz [[Import
  modelu|Import-modelu]], část o modelu s vlastními kostmi a animacemi. Horse Squad byl takto udělán ve Studiu a hrán
  ve hře (listopad 2026); nic jiného takto udělaného zatím ve hře vyzkoušeno nebylo.

## Pancéřování

**Pancéřování** na stránce jednotky vybírá jednu z úrovní pancéřování hry (tanky mají 1 až 5, číslo na štítu).
Jednotka s ním bojuje a ukazuje ho její karta i nabídka stavby. Změna čísla přímo uvnitř části pancéřování způsobila,
že jednotka bojovala s jednou hodnotou, zatímco její karta ukazovala jinou, takže tu část už přímo měnit nelze.
Viděno ve hře.

## Výzkum: čeho je vylepšením

Stránka jednotky má pole **Vylepšení a výzkum**: jednotka, jejímž je vylepšením (**Vylepšení jednotky**), její
vlastní vylepšení a její cena a doba výzkumu. Vyberte jinou jednotku ze stejné nabídky stavby, nebo **Žádná:
samostatná jednotka**, aby se dala koupit hned od začátku. Doby výzkumu lze zadat v sekundách nebo minutách (výběr
vedle nich).

Když vyjmete jednotku, ze které se zkoumají jiné, o tom, co se stane, rozhoduje **Nastavení > Výzkum**: **Nejdřív mě
varovat** (výchozí), **Odmítnout** nebo **Znovu je propojit** na její vlastní nadřazenou jednotku. Jednotka, která
zůstala zkoumaná z jednotky, jež už neexistuje, to řekne tady i v liště kontroly, a sestavení se na ní zastaví, dokud
nevyberete jinou.

Jednotka zobrazená ve své nabídce stavby musí být zkoumaná z jednotky, která je tam zobrazená také: ta, kterou můžete
postavit, je první, výzkum až po ní. Jednotka zobrazená v datu bitvy, ve kterém je jednotka, ze které se zkoumá,
skrytá, zastaví hru, když se ta nabídka stavby otevře (viděno ve hře), proto ji lišta kontroly jmenuje a sestavení se
na ní zastaví. Zobrazte tu druhou jednotku znovu, nebo vyberte jinou jednotku, ze které se bude zkoumat, nebo žádnou.
**Národy > Skrýt všechny jednotky** to udělá za vás: jednotka, která zůstane zkoumaná ze skryté, se dá koupit hned od
začátku.

## Jednotky z jiných období

366 jednotek od 1. světové války po dnešek, každá volný 3D model jiného autora, můžete přidat do svého modu jako nové
jednotky, v jejich skutečné velikosti a za výzkumem: viz [[Jednotky z jiných období|Jednotky-z-jiných-období]].

## Zbraně a munice

Pole **Zbraně** na stránce jednotky uvádí její zbraně (Zbraň 1 je hlavní kanón). **Jak fungují zbraně a munice**, pod
ním, má tyto kroky také.

1. **Každá zbraň střílí jednu munici.** Seznam vedle ní vybírá kterou: jakoukoli munici hry, seřazenou podle typu
   (AP, HE, protiletadlová, kulomety, bomby, rakety...), nebo kopii, kterou jste vytvořili. Záblesk u ústí hlavně
   a zvuk přicházejí s ní.
2. **Munice rozhoduje, co zbraň dělá:** její poškození, dostřel, kadenci a co může zasáhnout. **Otevřít munici**
   ukáže a umožní změnit její čísla.
3. **Změna munice změní každou jednotku, která ji střílí** (její stránka je uvádí). Jen pro jednu jednotku: na stránce
   munice klikněte na **Kopírovat tuto munici…**, změňte kopii, pak ji vyberte v seznamu zbraně. Posuvník **dostřelu**
   zbraně se ptá na totéž: jen tato jednotka, nebo každá jednotka s touto municí.
4. **Zasahuje** (pod zbraní) vybírá zem, letouny nebo obojí. Pole **Role** u letadla nastavuje, jak útočí (níže).
5. **Přidat nebo odebrat zbraň zatím nejde:** zbraně jsou svázané s animacemi modelu a tak daleko ještě nejsme.

**Její jméno ve hře** (na stránce munice, Studio 0.9.8.8): jak munici nazývá hra, její **Název** (Medium cal.,
MG 42) a její **Druh** (AP shell). Napište nová slova a uložte: všechny jazyky je ukazují, dokud jeden nezměníte zvlášť
přes **Změnit text…**; **Slova hry** ta vaše odebere. Zkopírovaná munice se jmenuje tak, jak ji pojmenujete. Zatím
nevyzkoušeno ve hře.

**Třída zbraně** (na stránce munice, Studio 0.9.8.17): jakou část poškození munice způsobí každému druhu cíle.
**Nová třída zbraně…** otevře jedno číslo pro každý druh: budovy a opevnění, letadla, výsadkáři při seskoku,
pěchota, lehká vozidla (transportéry), pancéřování 1 až 5 a stavební nákladní auta. 1 je plné poškození, 2 dvojnásobné,
0,5 poloviční a 0 znamená, že tento cíl vůbec nemůže napadnout. **Uložit třídu** dá munici vlastní kopii tabulky
poškození hry, takže se poškození žádné jiné munice nezmění, ale dostane ji každá jednotka, která touto municí střílí
(jen pro jednu jednotku nejdřív použijte **Kopírovat tuto munici…**). Tlačítko se pak jmenuje
**Změnit tuto třídu zbraně…**; **Zpět na třídu ze hry** kopii odebere a smazání zkopírované munice vezme její třídu
s sebou. Viděno ve hře: pěší družstva, jejichž munice dostala čísla proti tankům, střílela na tanky z pušek
a poškodila je. Samotné tlačítko zatím ve Studiu nikdo nestiskl.

**Rychlost střely:** rychlost střely munice a její odpor rozhodují, kdy zásah dopadne: pomalejší střela zasáhne
později a na pohyblivý cíl se míří s předstihem o dobu letu (známo z toho, jak hra funguje; zatím neověřeno testem).

## Změna role letadla (Studio 0.9.8.5)

Stránka letadla má pole **Role**: **Stíhačka**, **Stíhací bombardér**, **Bombardér** nebo **Průzkumný**. S ní se mění
to, jak letí a útočí, jak ho používají počítačoví hráči a slova v jeho nabídce stavby.

- **Bombardér:** bombardér shazuje bomby na přímém náletu, a jen z pumovnice. Nejdřív vyberte bomby pro jednu z jeho
  zbraní (Zbraně, níže), pak z něj udělejte Bombardér: jeho bomby přijdou do pumovnice zkopírované z bombardéru hry
  a tam je můžete měnit. Tohle je oprava pro stíhací bombardér, kterému byly dány kobercové bomby a nic neshodil.
  Viděno ve hře.
- **Průzkumný:** letadlo s kulomety dál může útočit (pole říká **Průzkumný, se zachovanými útoky**) a dostane výhled
  průzkumníků. Viděno ve hře se Stukou a ME109.
- Výsadkové letadlo si svou roli ponechá. **Zpět** vedle pole vrátí roli ze hry, s bombami tam, kde byly.

## Udělejte z vozidla průzkumné (Studio 0.9.8.5)

Pole **Role** pozemního vozidla: **Průzkum** mu dá výhled průzkumných vozů (mnohem dál než tank), to, jak je používají
počítačoví hráči, slova jejich nabídky stavby a může vjet do lesa. Zůstane stejně odolné a ozbrojené, jako je.
Viděno ve hře s Panzerem IV.

## Co zbraň zasahuje (Studio 0.9.8.5)

Pod každou zbraní **Zasahuje** vybírá **Pozemní cíle**, **Letouny** nebo **Pozemní cíle i letouny**. Letouny: zbraň
střílí kopii své munice, která zasahuje letadla (a zemi nic neudělá). Obojí: ponechá si svou munici a dostane vedle ní
druhou zbraň na letadla, tak jako protiletadlová děla hry nesou jednu pro každé. Tank střílející na letadla je viděn ve
hře; kanón letadla nastavený jen na zem zatím nezpůsobuje žádné poškození.

## Vyzkoušejte to

**Vyzkoušet ve hře** sestaví mod a spustí R.U.S.E. Hledejte jednotku tam, kde se staví (její továrna), v bitvě (hlavní nabídka: **BITVY**, pak mapa).

**Další:** [[Export a sdílení|Export-a-sdílení]]

---

[[Polní příručka|Polní-příručka]] · [[English|Edit-Units]]
