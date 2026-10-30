# Úprava scénáře

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.9.8.4 a mod · **Trvá:** pár minut

**Scénář** je to, s čím mapa začíná: zóny k obsazení, startovní bod každé strany a jednotky a budovy, které už stojí
na bojišti. Jedna mapa jich má několik: jeden pro každý způsob, jak ji hra hraje.

## Tři způsoby, jak hra hraje mapu

Toto jsou tlačítka hlavní nabídky R.U.S.E.:

| Tlačítko | Co to je |
|---|---|
| **BITVY** | Volná hra proti počítači na jedné mapě, s hráči, které si vyberete (jiné hry tomu říkají šarvátka). |
| **OPERACE** | Krátká mise s danými cíli, na předem připraveném rozestavení. |
| **KAMPAŇ** | Příběh, kapitola po kapitole. |

Studio pojmenuje každý scénář podle tlačítka, které ho hraje, a zlatý řádek pod nabídkou scénářů přesně říká kde:
například **Ve hře: Bitvy › Den D (6 hráčů)**.

## Výběr scénáře

Na začátku lišty obrazovky mapy vyberte **Scénář** (vedle **Mapa**). Vlastní věci mapy (terén, budovy, stromy,
silnice) se zobrazí vybledle a nedají se omylem chytit; chcete-li je změnit, přepněte zpět na **Mapa**. Pak vyberte
scénář z nabídky nahoře. Startovní body se zobrazují jako sloupy v barvě každé strany, místa příchodu jako bílé
kosočtverce, zóny jako vystínované plochy.

## Přesunutí startovního bodu nebo místa příchodu

1. Na straně **Scénář** klikněte na **Přesunout**.
2. Klikněte na sloup nebo kosočtverec, pak klikněte tam, kam patří.
3. Chcete-li ho vrátit tam, kde ho měla hra, klikněte na něj znovu a zvolte **Vrátit**.

## Přidání jednotek: jedné nebo celé formace

1. Na straně **Scénář** klikněte na **Přidat jednotku**.
2. Vyberte druh (Budovy, Pozemní, Pěchota, Letectvo), pak typ, pak jednotku v seznamu (seskupené podle národů).
3. Vyberte **Komu?** U operace nebo kapitoly kampaně jsou v seznamu vlastní tábory toho scénáře, z jeho mise:
   **Hráč** (vy: tábor 0 v kampani) a tábory hráče **Počítač**, každý se svou zemí, plus **Neutrální**. Číslo
   v závorce je to, co se uloží. Mapa **BITVY** bere jen neutrální jednotky (hra ji spouští bez seznamu týmů, takže
   jednotky hráče by se tam nikdy neobjevily).
4. **Kolik:** 1, 2, 4, 6, 8 nebo 10.
5. Pro víc než jednu vyberte **formaci**: řada, kolona, klín, čtverec nebo kruh. Míří k hornímu okraji obrazovky:
   otočte pohled, abyste ji namířili. **Rozestup** nastavuje metry mezi jednotkami.
6. Kroužky na mapě ukazují, kde bude každá jednotka stát. Kliknutím je umístíte.

Přidanou jednotku můžete přesunout jako jakékoli místo příchodu, nebo ji vyjmout tlačítkem **Odebrat**.

## Víc hráčů na mapě (až 8)

Každý hráč začíná na **startovním bodě** svého týmu, jeden na hráče: ve hře 3v3 mají týmy 1 a 2 každý místa
1 až 3. Hra 4v4 potřebuje místo 4 v obou.

1. Vyberte scénář, který hra hraje online (jeho zlatý řádek říká **Bitvy**), pak na liště klikněte na **Scénář**.
2. **Hráči** (vpravo) ukazuje počet hráčů mapy, ten ze hry je označený *(hra)*. Vyberte nový počet, nejvýš 8.
   Řádek pod tím jmenuje každý startovní bod, který ještě chybí, např. *tým 1, místo 4*.
3. Klikněte na **Přidat start velitelství**, vyberte **tým**, pak klikněte na volný terén, kde ten hráč začíná, dál
   od ostatních. Dostane další místo týmu a kameru a úvod od spoluhráče.
4. Když řádek říká **Každý hráč má startovní bod.**, klikněte na **Vyzkoušet ve hře** a otevřete **BITVY**: mapa je
   v seznamu s novým počtem, např. *(8) Cotentin (4v4)*.

Přidaný startovní bod přesunete pomocí **Přesunout**, nebo ho odstraníte pomocí **Odebrat**. Víc než 8: ne, lobby hry
má 8 míst (vyzkoušeno 2026-10-02).

> [!NOTE]
> Nové, zatím neověřené ve hře: napište nám do [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions),
> jak probíhá hra 8 hráčů.

## Prázdná mapa: umístěte velitelství každého hráče

Mapa začatá jako **Prázdný terén** nebo **Prázdný oceán** (**Duplikovat mapu** v záložce Mapy) nemá nic
z kopírované mapy, ani její velitelství. **Velitelství každého hráče** (na straně Scénář) uvádí každé velitelství,
které mapa potřebuje: klikněte na **Umístit**, pak na zem, kam patří. **Vyzkoušet ve hře** čeká, dokud každý hráč
nemá velitelství.

**Velikost mapy** (Studio 0.9.8.7) udělá novou prázdnou mapu větší nebo menší, pruh po pruhu: stiskněte **+** u
strany, abyste podél ní přidali pruh terénu, nebo **−**, abyste jeden ubrali, pak **Použít tuto velikost**. Zatím
nevyzkoušeno ve hře.

> [!WARNING]
> Obě prázdné mapy jsou stále plné chyb: používejte je na vlastní uvážení a dejte nám vědět, na co narazíte.

## Sektory

**Sektory** (na straně Scénář) mění sektory scénáře, zóny, na kterých se hrají karty lsti. Prázdná mapa začíná bez
nich: uděláte si je.
- **Tvary:** tažením rohového bodu posunete hranici (sektory, které ji sdílejí, se posunou spolu). Dvojklikem na
  hranici přidáte bod; kliknutím pravým tlačítkem na bod ho odeberete. **Nový sektor:** táhněte obdélník na zemi.
  **Žádný sektor:** táhněte obdélník tam, kde žádný sektor být nemá. **Smazat sektor** dá všechnu jeho zem sektorům
  kolem.
- **Malovat:** vyberte sektor, pak tažením po zemi ho malujte; „Žádný sektor“ vyjme zem ze všech sektorů.
- **Začít bez sektorů** nebo **Začít od sektorů mapy**; **Zpět** vrátí poslední změnu.
- **Vytvořit sektory** rozřeže celou mapu na sektory zhruba tak široké, jak říká **Sektory zhruba po** (vlastní mapy hry
  mají sektory 1 až 3 km napříč), s klikatými hranicemi; **Jiné rozložení** je rozřeže jinak. Pak tažením rohů nebo
  malováním upravte jejich tvar.

Viděno ve hře: namalované sektory na prázdné mapě, nový sektor nakreslený na mapě Den D a samostatně rozsvícený
kartou lsti, zem bez sektoru (mezera na mapovém stole, kterou žádná karta lsti nerozsvítí). Tenké čáry, které Studio
prořízne, aby sektor zůstal v jednom kuse, zatím nebyly ve hře vyzkoušené.

## Zásobovací sklady na této mapě

Vyberte zásobovací sklad a dejte mu víc náklaďáků (víc náklaďáků, víc peněz v něm), nebo použijte **Všechny sklady
tady**: vynásobte náklaďáky každého skladu (**krát jejich náklaďáky**) nebo jim všem dejte stejný počet (**náklaďáků
každý**), pak **Použít**. **Zpět na ty ze hry** to vrátí. Chcete-li změnit všechny mapy najednou, použijte **Sklady na
mapách** v **Nastavení počítače a hráčů** ([[Ekonomika, AI a další|Ekonomika-AI-a-další]]). Sklady s více než 1 000
náklaďáky potřebují Launcher 0.4.8.4 nebo novější.

## Vlastní mise

Nová operace nebo kapitola kampaně může hrát vlastní misi, s cíli, událostmi a pohyby kamery:
[[Tvorba mise|Tvorba-mise]].

## Podívejte se na své jednotky ve hře

1. Klikněte na **Vyzkoušet ve hře** (nahoře ve Studiu). Studio sestaví váš mod do kopie hry s mody
   (`RUSE-Instances\Modded game` na disku s vaší hrou, nebo do složky, kterou jste zvolili v Nastavení: jedna pro celé PC, i pro Launcher) a spustí z ní R.U.S.E. Zpráva dole
   říká, co otevřít, například **BITVY > Den D**.
2. V hlavní nabídce hry klikněte na to tlačítko (**BITVY** pro bitvu), pak vyberte mapu (**Den D**).
3. Nastavte hru jako obvykle a spusťte ji. Vaše jednotky se objeví tam, kam jste je umístili.

> [!NOTE]
> Spuštění R.U.S.E. ze Steamu spustí hru bez vašeho modu. Použijte **Vyzkoušet ve hře** (nebo **Hrát** v launcheru).

> [!NOTE]
> Který startovní bod patří kterému hráči z lobby v bitvě, se ještě testuje. Napište nám, na co jste přišli, do
> [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Další:** [[Export a sdílení|Export-a-sdílení]]

---

[[Polní příručka|Polní-příručka]] · [[English|Edit-a-Scenario]]
