**RUSE Launcher 0.4, pro hráče.** Najde R.U.S.E. přes Steam a **Hrát** sestaví upravenou kopii hry s vašimi módy a
spustí ji. Vaše instalace Steamu se nikdy nemění.

**0.4.8.9:** módy se instalují na více PC, a bezpečnější čtení obrázků.

- **Opraveno, nahlášeno hráčem:** na některých PC se nenainstaloval žádný mód: „tento PC nedůvěřuje bezpečnostnímu certifikátu webu (unable to get issuer certificate)“. Windows na těchto PC nemá certifikát, kterým se ověřuje stahování z GitHubu, a nedokáže ho získat. Launcher teď zkouší i seznam certifikátů Firefoxu, který nese s sebou. Do té doby se mód stažený v prohlížeči ze seznamu módů nainstaluje přes **Přidat soubor módu…**.
- **Bezpečnější obrázky:** knihovna, kterou Launcher čte obrázky (Pillow), je teď ve verzi 13.0.0, s opravami proti schválně upraveným souborům obrázků, které mohly aplikaci shodit, vyčerpat její paměť nebo hůř.
- **Pečlivější kód:** 12 varování kontroly kódu GitHubu k tomuto projektu je vyřešeno. Když Launcher ukazuje své stránky ve vašem prohlížeči, otevírají jen jeho vlastní soubory, ověřené způsobem, který ta kontrola rozpozná, a stahování vyžaduje TLS 1.2 nebo novější, jako už dřív. Na tom, jak Launcher funguje, se nic nemění.

**0.4.8.8:** spouští mody vytvořené ve Studiu 0.9.8.8 a vaše upravená hra říká R.U.S.E. 2.0 ve zlaté.

- **Mody ze Studia 0.9.8.8 hrají:** vlastní budovy (druhá a třetí národa potřebují malou záplatu hry, jednou staženou a použitou jen na vaši upravenou kopii, nikdy na hru ve vaší složce Steamu), vlastní vzhled nových budov a předměty, zvuky a animace změněné v RUSE Decoy, hodnoty počítačových hráčů a pravidla hry, a uzavřené přechody po starých mostech.
- **R.U.S.E. 2.0 ve zlaté:** vaše upravená hra začne bitevní scénou se startujícím motorem a její hlavní nabídka, malý název každé nabídky, obrysy nabídek a načítací obrazovky říkají R.U.S.E. 2.0 ve zlaté. Udělá se na vašem PC ze souborů vaší vlastní hry napoprvé (jednou pár minut, pak se uchová). Nastavení má zaškrtávací pole pro zachování názvu hry.
- **Opraveno: tmavé a světlé skvrny na mapách vytvořených ve Studiu** (prázdné, zvětšené, reliéfní a sektorové mapy): taková mapa je osvětlená správně, jakmile se sestaví touto verzí (její terén se poprvé udělá znovu).
- **Opraveno, nahlášeno hráčem:** na stránce Podporované módy „Nová sada módů…“ nic nedělala. Teď otevře novou sadu. Zatím nevyzkoušeno v aplikaci samotné.
- **Písmo hry:** Launcher je psaný písmem nabídek hry, vzatým z vaší hry při každém spuštění.
- **Stále chybové, hrajte na vlastní uvážení:** mapy vytvořené s texturami Map Paint a prázdné mapy (Prázdný terén, Prázdný oceán).

**0.4.8.7:** spouští mody vytvořené ve Studiu 0.9.8.7.

- **Mody ze Studia 0.9.8.7 hrají:** objekty přesunuté nebo umístěné mřížkou, obdélníkem a podél cest, větší prázdné mapy s jejich sektory a změny ekonomiky jen Jaderného režimu.
- **Řádky sestavení ve vašem jazyce**, ve všech deseti.
- **Uchované výsledky sestavení zůstanou platné i po aktualizaci.**
- **Stále chybové, hrajte na vlastní uvážení:** mapy vytvořené s texturami Map Paint a prázdné mapy (Prázdný terén, Prázdný oceán).

**0.4.8.6:** spouští mody vytvořené ve Studiu 0.9.8.6.

- **Mody ze Studia 0.9.8.6 hrají:** prázdné mapy se stíny na rovném terénu, umístěné věci tam, kde kopírovaná mapa měla moře, nakreslené, a podlaha kamery na novém terénu.
- **Známý pád odmítnut:** mod, jehož ozbrojené letadlo nese flag průzkumu bez flagu stíhačky, shazoval hru, když bylo letadlo posláno útočit; teď ho Launcher odmítne sestavit a řekne proč.
- **Stále chybové, hrajte na vlastní uvážení:** mapy vytvořené s texturami Map Paint a prázdné mapy (Prázdný terén, Prázdný oceán).

**0.4.8.5:** spouští módy vytvořené ve Studiu 0.9.8.5.

- **Módy ze Studia 0.9.8.5 fungují:** letadla v nové roli (bombardér s pumovnicí, průzkumník, který si nechá zbraně), průzkumná vozidla, zbraně, které zasahují letadla, a terén namalovaný z knihovny štětce Textura s detailem hry navrch. Starší Launcher některé z nich nesestaví.
- **Rychleji:** mapa namalovaná stejně dostane namalovaný terén z minulého sestavení zpět za pár sekund.
- **Stále chybové, hrajte na vlastní uvážení:** mapy vytvořené s texturami Map Paint a prázdné mapy (Prázdný terén, Prázdný oceán).

**0.4.8.4:** módy se stahují na každém PC a spouští módy vytvořené ve Studiu 0.9.8.4.

- **Módy se stahují na každém PC:** na některých PC se nestáhl žádný mód („certificate verify failed: unable to get local issuer certificate“). Teď Launcher požádá Windows o certifikát, jako prohlížeč, a zkusí to znovu; i u vlastních aktualizací. Zatím nevyzkoušeno na PC, které mělo ten problém.
- **Módy ze Studia 0.9.8.4 fungují:** vlastní mise, prázdné mapy s jejich velitelstvími a sektory, sklady s víc auty (starší Launcher sklady s víc než 1 000 auty odmítne), jednotky s vlastním vzhledem a uniformami, úpravy cizích módů pod vlastním jménem.
- **Stále chybové, hrajte na vlastní uvážení:** mapy vytvořené s texturami Map Paint a prázdné mapy (Prázdný terén, Prázdný oceán).

**0.4.8.3:** kopie s módy se ukládají tam, kam řeknete.

- **Kam se ukládají kopie s módy**, v Nastavení: vyberte složku, ve které se sestavuje kopie hry s módy, nebo se vraťte
  na doporučené místo, `RUSE-Instances` na disku hry (tam kopie sdílí soubory hry a je hotová za pár sekund; na jiném
  disku je to úplná kopie hry, pomalejší a větší). Čistá záloha hry jde vedle. Další Hrát sestaví na novém místě;
  starou složku lze smazat ručně. Studio používá stejnou složku.

**0.4.8.2:** otevře se ve vašem webovém prohlížeči, když jeho vlastní okno nemůže, a spouští mody ze Studia 0.9.8.2.

- **Linux a Steam Deck (přes Proton):** Launcher se otevře ve vašem webovém prohlížeči, když jeho vlastní okno
  nemůže. Na Linuxu zatím nevyzkoušeno: dejte nám vědět, jak to šlo.
- Mody ze Studia 0.9.8.2 fungují: jednotky z jiných období s vlastními modely, velikostmi, výzkumem a kartami.

**0.4.8.1:** převádí staré mody a spouští mody ze Studia 0.9.8.1.

- **Převést starý mod…**, nástroj Convert od LittleGroove: starší mod v podobě balíků hry, určený ke zkopírování do
  složky hry, se stane modem, který vaše knihovna spustí vedle ostatních. Se skutečným starým modem zatím nevyzkoušeno.
- **Dva mody mění stejný soubor hry:** Launcher to řekne před Hrát a **Použít verzi…** vybere který.
- Mody ze Studia 0.9.8.1 fungují: skladby a hlasy, národ proměněný v jiný.

**0.4.8:** spouští módy udělané ve Studiu 0.9.8, mezi nimi nové mapy, které začínají prázdné, a ukazuje novinky ve
vašem jazyce.

| Dřív | Teď |
|---|---|
| Nová mapa ukazovala obrázky v nabídce kopírované mapy. | Vlastní obrázky, jak je udělal její autor, se startovními body tam, kde začínají její hráči. |
| Jednotka postavená na vysušeném moři mohla shodit hru. | Opraveno (ověřeno ve hře). |
| Stará říční voda stála jako zdi podél okraje mapy a smazané majáky dál svítily nad mořem. | Opraveno (ověřeno ve hře). |
| Mód, který smaže celou mapu, mohl při sestavování vyčerpat paměť počítače. | Sestaví se. |
| Novinky byly jen anglicky. | Jsou v jazyce Launcheru. |

Známé: **námořní mapy nejsou hotové.** Prázdný oceán se sestaví a hraje, ale jednotky pod jeho vodou zatím nebyly
vyzkoušeny.

**0.4.7:** velmi velké módy map se teď sestaví za několik minut (dřív to trvalo velmi dlouho) a spouští módy vytvořené
ve Studiu 0.9.7.

| Dřív | Teď |
|---|---|
| **Hrát** mohlo sestavovat velký mód mapy hodiny. | Ten nejextrémnější, který máme (mapa „Den D“ s vysušeným mořem), se sestavoval asi čtyři hodiny; teď za méně než 10 minut, se stejným výsledkem. |
| První sestavení velkého módu mapy počítalo všechno na vašem počítači. | Mód exportovaný ve Studiu 0.9.7 si nese to, co jeho sestavení spočítalo pro pohyb na mapě: vaše první sestavení je kratší. Každá odpověď se kontroluje a soubory hry vyjdou stejné. |

Známé: **námořní mapy ještě nejsou vyřešené.** Vysušené nebo namalované moře se sestaví a načte, ale voda je stále vidět.

**0.4.6:** **Hrát** spustí hru hned, když se nic nezměnilo, a hraje módy vytvořené ve Studiu 0.9.6: nové jednotky
s vlastním 3D modelem.

| Dřív | Teď |
|---|---|
| **Hrát** pokaždé znovu sestavilo celou upravenou kopii, i když se nic nezměnilo (hráč: „pokaždé čekám 30 minut“). | Nic se nezměnilo: hra se spustí hned. Změna kopii znovu sestaví, ale nezměněné soubory poslední kopie se použijí znovu, takže kopie na jiném disku, než je hra, už znovu nekopíruje každý balík. Hrát řekne, kolik zkopírovalo. |
| Každé sestavení četlo data jednotek hry znovu od začátku. | Uchovávají se mezi sestaveními: velký testovací mód trval pokaždé 213 s; teď další sestavení po prvním trvají 68 s. |
| Nová jednotka módu měla model jednotky, kterou kopíruje. | Její vlastní model z módu (`files/models`) je ve hře. **Viděno ve hře:** M1 Abrams vedle Shermana. |
| Nová jednotka módu s vlastní kartou shodila hru, když byla postavena. | Opraveno. **Viděno ve hře.** |
| Barvy přebarvených jednotek místy vycházely trochu jinak. | Blíž obrázku z módu. Mód s přebarvenými jednotkami nebo namalovaným terénem dostane nový otisk a kód pro připojení: všichni, kdo hrají spolu, by měli aktualizovat. |
| Pomalé spuštění nezanechalo žádnou stopu. | **Kopírovat zprávu** vypíše kroky posledních pěti spuštění. |
| — | Hraje módy s vymazáním celé mapy, silnicemi na přetvořeném terénu a vyplněním koryt řek ze Studia 0.9.6 (nové, ve hře zatím neviděno ve velkém). |

**0.4.5:** hraje módy vytvořené ve Studiu 0.9.5: přebarvené jednotky, jejich vlastní karty a jednotky s vlastními modely.

| Dřív | Teď |
|---|---|
| Mód nemohl změnit vzhled jednotky. | Přebarvené jednotky a karty z módu jsou vidět ve hře. **Viděno ve hře:** červený Sherman, karta vytvořená ve Studiu. |
| Mód, jehož balíky modelů jednotek narostly, hra zahodila: pád u první továrny. | Sestavené tak, jak je hra kontroluje. **Viděno ve hře:** druhý Sherman s vlastním modelem. |
| Mód, který v kapitole kampaně nebo Operaci nechá objevit jednotky jiného národa, spadl při načítání (francouzské jednotky na mapě Holland). | Jejich modely se načtou i tam. **Viděno ve hře.** |
| Srovnání hor na okraji mapy tam nechalo útes. | Okraj sleduje terén. **Viděno ve hře.** |

**0.4.4:** hraje módy s novými mapami, vytvořenými pomocí Duplikovat mapu ve Studiu 0.9.4.

| Dřív | Teď |
|---|---|
| Nové mapy z módu nebyly ve hře vyzkoušené. | **Viděno ve hře:** nová mapa z módu je v nabídce BITVY a hraje se na vlastním terénu, 101 naráz. Raná verze: nahlaste, na co narazíte. |
| Aktualizace přicházely jen jako celé verze. | Malé opravy mohou přijít mezi verzemi (0.4.4.1), nabízené jako každá aktualizace. |

**0.4.3:** hraje módy vytvořené ve Studiu 0.9.3 a sestavuje je asi třikrát rychleji.

| Dřív | Teď |
|---|---|
| Kameny a většina dalších předmětů umístěných módem zmizely, jakmile kamera opustila blízkou vzdálenost. | Kreslí se až do velké dálky; vlastní objekty mapy beze změny. **Viděno ve hře.** |
| Nová silnice módu lesem byla shora světlým pruhem, nebo ze středně dlouhé vzdálenosti zmizela. | Malovaná lesem tak, jak jsou malované vlastní silnice mapy. **Viděno ve hře.** |
| Silnice módu vždy odstranily stromy ze své cesty. | Silnice je může ponechat (`keep_trees`): vede pod stromy, v lese slabší a šedší. |
| **Hrát** sestavovalo mód s novými silnicemi na M03_Italie asi 5 minut. | Asi 1½ minuty, když už se na mapě jednou sestavovalo. |

**0.4.2:** hraje módy vytvořené ve Studiu 0.9.2.

| Dřív | Teď |
|---|---|
| Mód se silnicí přes vodu na mapách Itálie, Německa, Holandska a dalších byl odmítnut: jeho most „by neměl podlahu“. | Sestaví se: most dostane vlastní podlahu mapy. Na těchto mapách ve hře zatím neviděno. |
| Mód, který dává jednotky hráči v kapitole kampaně (strana 0), byl odmítnut a jednotky pro strany počítače dostaly varování „se možná nikdy neobjeví“. | Sestaví se; varování dostane jen strana, kterou mise kapitoly nemá. |
| Na M03_Italie a dalších mapách nová silnice módu v otevřeném terénu skrývala scenérii mapy z dálky a předměty módu byly vidět jen zblízka. | Pohled na mapu z dálky zůstává, jak byl, a předměty módu jsou vidět z dálky. Ve hře zatím neviděno. |

**0.4.1:** váš jazyk od prvního spuštění a editor sad módů, který najde módy podle názvu.

| Dřív | Teď |
|---|---|
| Vytváření sady módů vypsalo celou vaši knihovnu s Vytvořit dole a mód se nedal najít podle názvu. | Vytvořit je nahoře, hned pod ním módy, které už v sadě jsou; níž „Přidat módy z knihovny“ s hledáním, které zužuje seznam, jak píšete. |
| Jazyk byl schovaný v Nastavení, takže hráči nevěděli, že Launcher mluví jejich jazykem. | První spuštění se zeptá: „Vyberte jazyk“, každý jazyk vlastními slovy, s označeným jazykem, na který je vaše hra nastavená ve Steamu (hráči, kteří aktualizují, to uvidí jednou). Pak tlačítko jazyka nahoře, vždy na očích. |
| Seznam nainstalovaných aplikací ve Windows ukazoval vůbec první nainstalovanou verzi. | Ukazuje verzi, kterou máte. |

**0.4.0:** hraje módy s novými silnicemi tak, jak je sestavuje Studio 0.9: vypadají jako vlastní silnice mapy, shora
i těsně u země (vyzkoušeno ve hře na mapě Den D).

![Nová silnice zblízka na mapě Den D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Dřív | Teď |
|---|---|
| Nové silnice módu zblízka mizely. | Kreslí se vlastním asfaltem a okrajovými obtisky mapy, malované tak, jak jsou malované silnice mapy, a rostliny na jejich cestě se odstraní. |
| Mód s mnoha mazacími kruhy se sestavoval minuty. | Mnohem rychleji. |

**0.3.3:** hraje módy vytvořené ve Studiu 0.8.3.

| Dřív | Teď |
|---|---|
| Mód s natočenou úvodní kamerou (Studio 0.8.3) byl odmítnut. | Sestaví se: kamera je natočená tak, jak říká mód. |
| Úvodní kamera přesunutého startovního bodu zůstala na starém místě. | Kamera se přesune s ním; nový startovní bod dostane vlastní kameru. |
| Mód se startovním bodem v lese byl odmítnut. | Sestaví se: velitelství tam funguje. |

**0.3.2:** jedna kopie hry pro celé PC, zobrazená verze a přehlednější knihovna.

| Dřív | Teď |
|---|---|
| Každá sada módů sestavovala vlastní kopii hry. | Jedna upravená kopie pro celé PC, sdílená se Studiem. |
| Verze nebyla vidět a Co je nového byl seznam. | Verze je vedle názvu a Co je nového otevře tabulku dřív/teď, jako je tato. |
| Mapy a módy vypadaly v knihovně stejně. | Mapa má štítek MAPA. |
| Málo popisků. | Popisky u hlavních ovládacích prvků. |
| Módům s novými silnicemi na mapách Twilight of the Gods, Alpha, Ostfriesland a Robert chyběl model silnic mapy. | Dostanou ho také. |

**0.3.1:** módy s jednotkami z jiného národa (třeba německý Tiger pro USA) fungují, i v zápase, kde ten národ nikdo
nehraje (vyzkoušeno ve hře, 2026-10-02). A nový vzhled: modré barvy R.U.S.E. místo černé a zlaté a nové logo: stíhačka
stoupající mraky. Boční panel má dvě záložky, **Sady módů** a **Knihovna módů**, každou na celou výšku, takže se
dostanete k celé knihovně (polovina byla schovaná za posuvníkem), s hledáním a počtem. Instalátor nabízí
**čistou zálohu hry** vedle zástupce na ploše a říká proč.

**0.3.0:** **Podporované módy:** Launcher ukazuje náš seznam módů
([sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods)); zaškrtněte ty, které chcete, a stáhnou se a
zkontrolují. Při prvním spuštění si módy vyberete; cheatovací módy jsou oddělené a nikdy se nezaškrtnou za vás.
Tlačítko **Řešení potíží** (na spodní liště a u každé zprávy o problému) jedním během zkontroluje, co může zastavit
**Hrát**, a opraví, co může, se zprávou k vložení do hlášení chyby. **Čistá záloha hry** v Nastavení uchová čistou
kopii souborů vaší hry a vrátí cokoli, co změnil jiný správce módů (nebo nechte hru opravit Steamem). Módy vytvořené
v novém Studiu fungují tak, jak byly vytvořeny: tanky a pěchota přejíždějí nové mosty po mostovce, pěchota sleduje nové
silnice, vykácené lesy jsou pro jednotky otevřené, umístěné budovy stojí na zemi v jakékoli velikosti a kryt leží tam,
kde byl namalován, na mapě Den D a dalších mapách, které nejsou čtvercové. Známý problém: nové silnice se zatím
nekreslí zblízka (jsou vidět z dálky).

**0.2.11:** **Hrát** funguje pokaždé: upravená kopie, kterou Windows nechce smazat (soubor, který propojila starší
verze, program, který ho ještě drží), se odsune stranou do `RUSE-Instances\.trash`, místo aby zastavila hru, a hra,
která z kopie ještě běží, se jmenuje. Módy s novými mosty už nikdy nevytvoří terén, kam se jednotky nedostanou (to
shazovalo hru).

**0.2.9:** **Hrát** funguje, když jsou soubory vaší hry označené jen pro čtení: selhávalo s „[WinError 5] Access is
denied“, jakmile zůstala upravená kopie napůl sestavená. Pokud hra z upravené kopie ještě běží, dozvíte se, že ji máte
zavřít, místo chyby Windows. Módy s novými silnicemi sestaví své namalované silnice a mosty.

**0.2.8:** mód, který přidáte, se hned zkontroluje tak, jak ho přečte sestavení hry: poškozený soubor mapy nebo složka
mapy pojmenovaná podle titulu mapy (maps/Blitz místo maps/SuperCrossRoads4) se jmenuje i s opravou dřív, než by se na
tom Hrát zastavilo.

**0.2.7:** **Nápověda** a **Nahlásit problém** na spodní liště: wiki (příručka pro hraní módů) a hlášení chyby ve
vašem prohlížeči s vyplněnou verzí Launcheru. Zpráva o problému má vlastní odkaz **Nahlásit**. Launcher nic neodesílá:
hlášení si přečtete a zveřejníte sami. Módy, jejichž složka mapy je pojmenovaná podle titulu mapy (maps/Blitz místo
maps/SuperCrossRoads4), se teď dozví, jak to opravit.

**0.2.6:** tlačítko **Nastavení** (vpravo nahoře): jazyk, složka hry a aktualizace na jednom místě, připravené na
další.

**0.2.5:** hledání aktualizací je spolehlivější: když GitHub odmítne jedinou kontrolu při spuštění (povoluje 60 za
hodinu na internetovou adresu, sdílených vším, co ji používá), Launcher místo toho přečte seznam vydání na GitHubu.

**0.2.4:** váš jazyk se zachová přes restarty, aktualizace a přeinstalace.

**0.2.3:** červený rámeček se sbaluje jako žlutý (velká sada může vypsat desítky střetů).

**0.2.2: Seřadit v nejlepším pořadí.** Když módy v sadě mění stejné hodnoty, má žlutý rámeček tlačítko **Seřadit
v nejlepším pořadí**: módy, které mění víc, jdou první a menší po nich, aby si každý ponechal co nejvíc svých změn.
Řekne, které módy tím zachrání, a módy se dají dál přesouvat ručně.

**0.2.1: módy, které k sobě nepasují, nejde hrát, a Launcher řekne proč.** Když dva módy v sadě nahrazují stejný
soubor nebo skript, červený rámeček jmenuje módy a co oba mění, a Hrát zůstane vypnuté, dokud se jeden nevyjme. Když
pozdější mód jen přepisuje hodnoty dřívějšího (třeba rychlost lodi), žlutý rámeček je vypíše a sada se dá dál hrát.

**Nové v 0.2:**

- **Sady módů vytvořené v okně:** nová, upravit, přejmenovat, duplikovat, smazat a seřadit módy. Žádné další soubory
  k ruční úpravě. Průvodce ve třech krocích na první obrazovce ukáže cestu.
- **Přidat soubor módu…** (nebo ho pusťte na okno): `.rusemod` exportovaný z RUSE Studio, složka módu v `.zip`, nebo
  **RUSE Mod Manager `.rmod`**, použitý tak, jak je (aplikovaný vlastním enginem LittleGroove).
- **Sdílet pořadí načítání** jako text a **Importovat pořadí načítání…** od přítele: Launcher řekne, které módy máte,
  které chybí a které jsou v jiné verzi, a pak vytvoří sadu. Je to stejný text, který kopíruje a čte RUSE Mod Manager,
  takže pořadí načítání jdou oběma směry.
- **Aktualizuje se sám:** od této verze, když vyjde novější Launcher, lišta to oznámí; **Aktualizovat** ho stáhne,
  zkontroluje jeho SHA-256 a nainstaluje, a Launcher se sám znovu spustí.

Vaše sady módů z 0.1 zůstanou zachované. Problémy a nápady: GitHub Issues.

![RUSE Launcher](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/launcher.jpg)
