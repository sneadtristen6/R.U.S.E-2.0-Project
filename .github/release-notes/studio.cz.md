**RUSE Studio, ukázková verze pro moddery.** Procházejte jednotky hry v kterémkoli z jejích deseti jazyků, měňte je ve
vlastním módu a vyzkoušejte ho ve hře. Vaše instalace Steamu se nikdy nemění.

**0.9.8.1:** Nástroje LittleGroove přicházejí do Studia, s hudbou a zvuky, národem proměněným v jiný a jednotkami z jiných období.

- **Nástroje LittleGroove, převzaté** z jeho RUSE-Mod-Manageru:
  - **Karta Ekonomika:** počáteční peníze a příjem, zásobovací sklady a karty lsti, se kterými začíná každá strana.
    Ověřeno ve hře: počáteční peníze a počáteční karty.
  - **Karta AI:** jak hrají počítačoví hráči, které jednotky upřednostňují, karty lsti; a skripty map a misí hry,
    zobrazené jako Python, jen ke čtení. Ověřeno ve hře.
  - **Rámeček Vylepšení** na stránce jednotky: jednotka, jejímž je vylepšením, její vlastní vylepšení, cena a doba
    výzkumu.
  - **Karta Všechny hodnoty:** libovolný objekt nebo hodnota hry, změněné v modu: přidat nebo odebrat hodnotu,
    vytvořit nebo smazat objekt, dát textové hodnotě vlastní slova.
  - **Karta Soubory:** libovolný soubor z balíků hry, k prohlédnutí a uložení. Nahraďte jeden svým souborem nebo přidejte
    nový: váš mod si ponechá jen změny, každou ověřenou podle jejího druhu.
  - **Mise:** změnit skripty mise; zjistit, zda je v menu, zda se načte každý soubor, který potřebuje, a její texty;
    posunout ji v jejím menu nahoru nebo dolů.
  - **Mapy:** názvy měst a kopců, pojmenované body a zóny, název a natočení objektu na mapě. **Poznámky** k jednotce,
    hodnotě nebo počítačovému hráči.
- **Karta Hudba:** každá skladba podle místa, kde hraje, každá nahrazená v malém editoru ve Studiu (střih, prolínání,
  hlasitost); nové skladby přidané do bitevních seznamů; hlášky jednotky na její stránce; zvuk pozadí mapy. Ověřeno ve
  hře: skladby, nové skladby a hlášky.
- **Udělat z jednoho národa jiný.** Nová karta **Národy** dá jednomu ze sedmi národů hry nový název (v lobby a pro
  jeho armádu) a novou vlajku z jakéhokoli obrázku: třeba Čínu místo Itálie. Jeho jednotky a to, co říkají, se mění
  jako dosud, na kartě Jednotky a na stránce každé jednotky. Ověřeno ve hře: nový název v lobby, nová vlajka v
  zápase.
- **Jednotky z jiných období:** karta Jednotky nabízí vedle jednotek hry WWI, WWII+, Studenou válku a Současnost.
  Přidejte jednu do svého modu a stane se novou jednotkou s vlastním modelem a uvedeným autorem; nic se nepřidá,
  dokud ji nevyberete.
- **Nová mapa: od nuly…** je na kartě Mapy, dokud není otevřená žádná mapa.
- **Terén Prázdného terénu se kreslí jako vlastní.** Nová mapa začatá od nuly má terén vytvořený z vašich tahů terénu,
  ne posunutý terén mapy ze hry: kulaté břehy zblízka i shora, žádné promáčkliny na vrcholcích kopců a budovy i tanky
  stojí přesně na něm. Ověřeno ve hře na testovacích mapách.
- **Prázdný oceán zůstává, s varováním** na svém tlačítku: oddělené ostrovy zatím nejsou připravené na velké
  bitvy (níže).

Ve hře zatím nevyzkoušeno: rámeček Vylepšení, Všechny hodnoty, Soubory, nástroje misí, doplňky map, zvuky pozadí
a jednotky z jiných období.

**Proč zatím nejsou námořní mapy.** Zkoušeli jsme mapy z ostrovů pro velké bitvy s loďmi a v cestě stojí samotná hra:

- Pozemní jednotka poslaná na ostrov, kam se nemůže dostat, způsobí pád hry.
- Spojení ostrovů pruhem souše pádu zabrání, ale počítač po něm pak jen posílá svou pěchotu.
- Bez silnice mezi ostrovy nejde nikde postavit žádnou budovu.
- Se zbraněmi ze hry si lodě a pozemní jednotky skoro neublíží.

Samotná data mapy pád neopraví: je třeba změnit soubory samotné hry, a tak námořní mapy čekají na postoj studia Eugen.

**0.9.8:** nová mapa může začít prázdná, jako rovná souš nebo otevřené moře, a každá mapa může mít vlastní obrázky v
nabídkách hry.

- **Začněte mapu prázdnou.** **Duplikovat mapu** má novou volbu, **Začít z**: **Prázdný terén** (rovná souš, na které
  není nic kromě startovních bodů) nebo **Prázdný oceán** (moře přes celou mapu). Ověřeno ve hře.
- **Obrázky v nabídce pro každou mapu.** Vyberte PNG pro obrázek mapy a její 3D mapu v nabídkách, nebo se vraťte k těm
  ze hry; bílé startovní body se kreslí tam, kde začínají hráči mapy. **Udělat v Blenderu…** otevře vlastní 3D model
  mapy, abyste je udělali, a **Přenést zpět** je dá do vašeho módu. Ověřeno ve hře.

| Dřív | Teď |
|---|---|
| Nová mapa začínala jako úplná kopie mapy ze hry. | **Duplikovat mapu** ji může nechat začít prázdnou: Prázdný terén nebo Prázdný oceán. |
| Nová mapa ukazovala obrázky v nabídce kopírované mapy. | **Obrázky v nabídce…** jí dají vlastní: vaše PNG nebo obrázek udělaný v Blenderu, se startovními body tam, kde začínají její hráči. |
| Sklady, jednotky, budovy a názvy mapy zůstávaly. | **Odebrat** odebere jeden, nebo všechny sklady či všechny názvy naráz (ověřeno ve hře). |
| Silnice a mosty mapy zůstávaly. | Panel Silnice je odebere (čáry silnic zmizely: ověřeno ve hře). |
| Sektory vynechávaly moře a okraje mapy. | **Sektory přes celou mapu**: lze obsadit celou mapu (ověřeno ve hře). |
| Voda na mapě byla jen v jejích řekách a moři. | **Voda přes celou mapu**: tenká vrstva jako namalované moře námořní mapy (ověřeno ve hře; jednotky pod ní zatím nevyzkoušeny). |
| Editor mapy vybíral místa příchodu po jednom, podle kódových jmen. | Táhněte rámeček a vyberte je jako ve hře; vlastní ikony mapy ukazují, co je vybráno a kolik. |
| Panely editoru mapy měly jednu velikost. | Každý plovoucí panel mění velikost, od 40 % do 125 %. |
| Novinky byly jen anglicky. | Jsou v jazyce Studia. |
| Poslat mód do seznamu módů znamenalo psát jeho záznam ručně. | **Zveřejnit v seznamu módů** otevře formulář seznamu, už vyplněný, s kopií .zip připravenou k přetažení; každý export uvádí, že byl udělán v RUSE Studio. |
| Importovat model ztrácel vlastní stínování a průhledné části modelu. | Zachová je a řekne, co zachoval (ve hře zatím nevyzkoušeno). |
| Jednotka postavená na vysušeném moři mohla shodit hru; stará říční voda stála jako zdi podél okraje mapy; smazané majáky dál svítily nad mořem. | Opraveno, vše ověřeno ve hře. |

Známé: **námořní mapy nejsou hotové.** Prázdný oceán se sestaví a hraje, ale jednotky pod jeho vodou zatím nebyly
vyzkoušeny.

**0.9.7:** velmi velké módy map se teď sestaví za několik minut. Dřív jejich sestavení trvalo velmi dlouho, a proto
byla tato aktualizace potřeba. A **Exportovat mód…** si s sebou nese to, co sestavení spočítalo, takže první sestavení
takového módu u hráče je kratší.

- **Nejextrémnější mód mapy, který máme** (mapa „Den D“ s vysušeným mořem: 154 tahů srovnání, 135 tahů barvy,
  33 385 smazaných budov) se sestavoval asi čtyři hodiny. Teď se sestaví za **méně než 10 minut**, bez ponechání
  čehokoli z dřívějšího sestavení, a soubory hry vyjdou stejné. Trvalo nám to zhruba 15 hodin; kde se to zasekávalo a
  proč: [Jak jsme se sem dostali](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here) (anglicky).
  Dál pracujeme na tom, aby to bylo rychlejší.

| Dřív | Teď |
|---|---|
| Mapa přetvořená přes kilometry se mohla sestavovat hodiny, vyčerpat paměť počítače, nebo být odmítnuta jako příliš velká pro pohyb na mapě. | Její terén se přetvoří za několik sekund, koryta řek se opraví a terén se maluje na všech jádrech počítače, a pohyb se počítá na dalších dvou, zatímco se terén maluje. Každý krok dá stejné soubory jako dřív. |
| Vysušené moře zůstávalo pro jednotky uzavřené. | Široké suché dno dostane zóny pohybu tak velké, jak dovolí místo. **Zatím nevyzkoušeno ve hře:** jednotky na otevřeném moři. |
| Nové sestavení po malé změně počítalo velkou mapu znovu celou. | Co bylo uděláno, zůstává: nezměněná barva zabere půl sekundy, nezměněný pohyb přijde z mezipaměti sestavení a nový tah přemaluje jen dlaždice, na které dosáhne. |
| První sestavení velkého módu mapy u hráče počítalo všechno znovu. | **Exportovat mód…** uloží do módu, co sestavení spočítalo pro pohyb na mapě (`maps/<map>/solved.bin`). Je to svázané se souborem hry pro tu mapu a neobsahuje žádné soubory hry. Sestavení hráče to převezme, zkontroluje každou odpověď a dá stejné soubory. Malování terénu a koryta řek se stále dělají na každém počítači. |
| Importovat model se ukazoval jen na stránce nové jednotky: těžko se hledal. | Karta Jednotky začíná dvěma tlačítky: **Upravit jednotku** a **Nová jednotka (import modelu)**. Vyberte výchozí jednotku, pojmenujte ji, Vytvořit: její stránka se otevře u Importovat model. Stránka jednotky ze hry má **Nová jednotka z této…**. |
| Příznak lodi (76) říkal, že jednotka s ním se pohybuje po vodě. | Říká, že se jednotka vůbec nepohybuje, jako budova (zatím nevyzkoušeno ve hře). |

Známé: **námořní mapy ještě nejsou vyřešené.** Vysušené nebo namalované moře se sestaví a načte, ale voda je stále vidět.
