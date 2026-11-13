**RUSE Studio, ukázková verze pro moddery.** Procházejte jednotky hry v kterémkoli z jejích deseti jazyků, měňte je ve
vlastním módu a vyzkoušejte ho ve hře. Vaše instalace Steamu se nikdy nemění.

**0.9.8.20:** Ochrany tam, kde některé sady módů zastavovaly hru; vylepšení vyráběné v jiné budově si nechá svou jednotku; editor sad říká proč; Bug Watch říká, proč selhalo sestavení nebo Hrát; vlastní voják družstva, změněný v Blenderu (Studio); družstvo voják po vojákovi, animace pro jedinou jednotku, modely s vlastními animacemi a Jízdní družstvo (Studio).

- **Ochrany tam, kde módy zastavovaly hru:** s R.U.S.E. Field Manual a Balance Overhaul Mod dohromady se hra zastavila, jakmile byla postavena tanková základna (hlášení o pádech od hráčů). Každá hra s módy má teď ochranu na třech místech, kde ji zastavovaly vlastní skripty hry: karty výzkumu v seznamu budovy pro jednotku, která je v jiné budově, mise, která spouští počítačového hráče strany, za kterou hraje člověk, a mise, která mění jednotky poté, co jedna z nich padla. Ochrana nic nedělá, kromě míst, kde by se hra zastavila. Vyzkoušeno ve hře s tankovou základnou; dvě ochrany misí byly vyzkoušeny mimo hru.
- **Vylepšení vyráběné v jiné budově si nechá svou jednotku:** se stejnými dvěma módy výzkum T-34 v tankové základně vzal T-26 z kasáren, protože hra jednotku odebere, jakmile je vyzkoumáno jakékoli její vylepšení, ať se vyrábí kdekoli. Sestavení teď z takového vylepšení udělá samostatný výzkum a řekne to ve varování. Vyzkoušeno ve hře za SSSR a Itálii. Mění to některé sady s Balance Overhaul Mod a sady s Field Manual před Balanced Realism Mod; varování jmenuje každou jednotku.
- **Kódy hry:** sada, kterou sestavení takto změní, dostane nový kód hry: tuto verzi potřebuje každý hráč zápasu s ní. Každá jiná sada si nechá svůj kód. Po aktualizaci příští **Hrát** nebo **Vyzkoušet ve hře** sestaví hru znovu samo.
- **Editor sad v Launcheru říká proč:** když nemůže vytvořit nebo uložit sadu (není zaškrtnutý žádný mód, nebo mód už není v knihovně), řekne to teď přímo v editoru, pod jeho tlačítky. Dřív zpráva šla na stránku sady, schovanou za editorem, a zdálo se, že se nic neděje. **Vytvořit** a **Uložit** čekají, dokud není zaškrtnutý mód. Vyzkoušeno v náhledu obrazovky, zatím ne v nainstalovaném Launcheru.
- **Vlastní mise (Studio):** mise nové mapy, která vytváří jednotky národa, jejž kopírovaná mise nenačítá, teď dostane balíky tohoto národa, takže ty jednotky mají své modely (hra se zastavila, když se taková jednotka vytvořila). Kontrola misí také odmítne událost, která předá počítači stranu, za kterou hraje člověk. Ověřeno přečtením skutečného sestavení; ve hře zatím nevyzkoušeno.
- **Vlastní voják pro družstvo (Studio):** stránka družstva má **Vlastní model** s tlačítkem **Změnit v Blenderu**: voják družstva se otevře v Blenderu na svých kostech a Blender dostane tlačítko **Poslat do R.U.S.E. Studia**. **Přenést model** ho vezme zpět na kosti vojáka ze hry a **Vlastní uniforma** k tomu není potřeba. **Importovat model…** teď funguje i u jednotky s volbou **Vlastní uniforma**: vyjme kopii a **Použít model kopírované jednotky** ji jedním kliknutím vrátí. Body, které Blender nechá bez kosti, se řídí kořenovou kostí a stránka řekne, kolik jich je. Vyzkoušeno ve hře na dvou amerických družstvech udělaných takto (jedno s větší hlavou, druhé s novou sítí s váhami z Blenderu); zbytek byl ověřen mimo hru.
- **Družstvo voják po vojákovi (Studio):** stránka družstva teď začíná jeho kartou družstva a řádkem pro každého vojáka, místo rámečku **Vlastní model**. **Změnit družstvo v Blenderu** otevře všechny jeho vojáky vedle sebe, každého s vlastní kopií jeho obrázků; po **Poslat do R.U.S.E. Studia** v Blenderu dá **Přenést moje změny** každému vojákovi jen to, co se udělalo s ním. Na svém řádku má voják **Importovat model…** a jakmile má vlastní model, **Zpět na vzhled ze hry**. Zdálky mají malé figurky družstva vzhled, jaký má většina jeho vojáků. Vyzkoušeno ve hře s družstvem, ve kterém byl načerveno natřený jen voják s bazukou.
- **Víc nebo méně vojáků (Studio):** **Přidat vojáka** přidá kopii vojáka z družstva, vojáka z jiného družstva nebo soubor modelu; **Odebrat** jednoho odebere; **+1 voják** a **−1 voják** hned přidají nebo uberou střelce, bez Blenderu. Družstvo má 2 až 8 vojáků a voják může mít vlastní vzhled, který nemá nikdo jiný. Hra to dostane přes malou záplatu hry: stáhne se jednou a použije se jen na vaši upravenou kopii, nikdy na hru ve vaší složce Steam; každé jiné družstvo zůstane, jak ho má hra. Vyzkoušeno ve hře s družstvy o 3 a 7 vojácích udělanými těmito tlačítky a s jediným střelcem natřeným načerveno; voják z jiného družstva nebo ze souboru modelu a družstva o 2 nebo 8 vojácích zatím ne.
- **Animace pro jedinou jednotku (Studio):** stránka jednotky teď má **Vzhled a pohyb**: její model, její vojáky, její zvuky a animace a to, v čem jezdí, řádek po řádku. **Změnit v RUSE Decoy** na řádku **Zvuky a animace** otevře RUSE Decoy na této jednotce a změna jedné z jejích animací může platit pro **Jen tato jednotka**, která pak hraje vlastní kopii, nebo pro všechny jednotky, které ji hrají. **Zpět na tu, kterou hrají všechny jednotky** vlastní kopii jednotky odebere. **Motion capture** jde na jedinou jednotku stejně. Vyzkoušeno ve hře s družstvem, které tančilo na místě, zatímco každé jiné družstvo stálo jako dřív; rychlost, náhrada nebo kost změněné pro jedinou jednotku zatím ne.
- **Animace změněné v Blenderu (Studio):** pro novou jednotku udělanou ve vašem modu otevře **Změnit jeho animace v Blenderu** v RUSE Decoy Blender s jednotkou a každou animací, kterou hraje, každou pojmenovanou podle toho, co v ní dělá. Změňte jednu, klikněte na **Poslat do R.U.S.E. Studia** a pak na **Přenést moje změny**: změněné se stanou vlastními této jednotky a každá jiná jednotka si nechá ty ze hry. Odeslání, které jste nikdy nepřenesli, se odloží a **Přenést odložené odeslání** ho převezme. Vyzkoušeno ve hře s družstvem, které stojí a běhá se zdviženou paží, a s Jízdním družstvem, jehož koně drží hlavu vysoko.
- **Modely s vlastními kostmi a animacemi (Studio):** **Importovat model…** teď vezme i .glb na vlastních kostech s jeho animacemi: koně s jezdcem nebo jakýkoli tvor. **Její animace** ukazuje, kterou animaci jednotka hraje pro každou věc, kterou dělá; vyberte jinou, nebo ji nechte na **Nejbližší**. **Na dlouhých přesunech** může družstvo jít samo a hrát jednu z nich, místo aby jelo ve svém autě. **Jeho dvě poloviny** vybere kost, kde se model dělí na horní a dolní polovinu, které hra animuje zároveň (jezdec míří, zatímco jeho kůň běží), a **Bude to ve hře fungovat?** řekne, co by na modelu mohlo hru zastavit nebo vypadat špatně. V družstvu dostanou střelci i voják s těžkou zbraní každý vlastní model, na vlastním řádku. Vyzkoušeno ve hře s Jízdním družstvem udělaným takto: střelci a voják s bazukou na koních střílejí, na dlouhých přesunech jedou sami a každý kůň padá se svým jezdcem; jiná animace vybraná ručně nebo jiné dělení zatím ne.
- **Jízdní družstvo (Studio):** střelci a voják s těžkou zbraní, každý na vlastním koni, teď na kartě **Jednotky** mezi jednotkami z jiných období (**2. světová válka+**, USA), vypnuté, dokud ho nepřidáte. **Přidat do modu** vyrobí jeho koně a jezdce ve vašem PC z vaší vlastní kopie hry (nic se nestahuje), přidá ho jako novou jednotku vašeho modu a zapíše sneadtristen6 do poděkování vašeho modu; **Odebrat z modu** zase vše odebere. Dělá se stejně jako Jízdní družstvo vyzkoušené výše; přidané z karty **Jednotky** zatím nebylo ve hře vyzkoušeno.
- **Vlastní lesk po Blenderu (Studio):** model poslaný do Blenderu přes **Změnit v Blenderu** a přenesený zpět přes **Přenést model** si nechá vlastní vrstvu lesku a barvy strany; dřív se vracel s obyčejnou, jakou dostane model ze souboru. Když ji nejde zachovat, stránka řekne, u kterých částí. Ve hře zatím nevyzkoušeno.
- **Kde je váš model (Studio):** řádek **Model** (na stránce družstva **Další možnosti**) řekne, kde váš mod drží vlastní model jednotky ve vašem PC, s tlačítkem **Ukázat ve složce**.
- **Karta Národy (Studio):** **Začít nový mod** se teď ptá jen na název a otevře Studio s novým modem; průvodce kroky je zatím vypnutý. Co měl jen on, je na kartě **Národy**: **Ponechat jednotky** nebo **Začít prázdný** pro každý národ a **Bez výzkumu** nebo **Ponechat výzkum ze hry** pro celý mod.
- **Jednotka bez obrázku karty (Studio a Launcher):** jednotka zobrazená v nabídce stavby bez obrázku karty se teď při sestavení hry odmítne, i s tím, co změnit. V testu se hra s takovou jednotkou zastavila hned při spuštění (kopie nákladního auta velitelství zobrazená v nabídce stavby).
- **Export vynechá složky vašeho PC (Studio):** exportovaný mod už nenese složky vašeho PC, které Studio zapisovalo do záznamů jeho modelů (často s vaším uživatelským jménem ve Windows): odejde jen samotný název souboru. Co jste napsali sami (README, popisy, poděkování), odejde, jak jste to napsali, a export vás upozorní, pokud to jmenuje vaši domovskou složku. Poděkování jednotek z jiných období, i Jízdního družstva, teď odcházejí s modem.
- **Menší věci (Studio):** každá továrna se jmenuje jako její budova; v perštině se názvy ze hry ukazují anglicky, nikdy jako interní názvy.
- **Hráči, aktualizujte Launcher:** mod, jehož družstva mají vlastní vojáky nebo jehož jednotky mají vlastní animace, potřebuje Launcher 0.4.8.20 nebo novější: starší jim je dát nedokáže.
- **Bug Watch říká proč, pokud jste ho zaškrtli:** která kontrola odmítla sestavení nebo našla chybu (pevný název z našeho kódu), kam až došlo **Hrát** nebo **Vyzkoušet ve hře**, které módy z našeho seznamu byly zapnuté a kolik vašich vlastních (spočítaných podle druhu, nikdy nejmenovaných), Hrát odmítnutá před spuštěním a aktualizace nabídnuté, nainstalované nebo neúspěšné. Nikdy zobrazená slova, cestu ani to, co obsahují vaše módy. To vše je v dohodě, kterou jste přijali (verze 3), takže se vám znovu nezobrazí.
- **Beze změny:** RUSE Guard, hra bez módů, kampaň a potyčky.

**0.9.8.19:** RUSE Guard: hra sestavená s cheatovým módem teď hraje hry více hráčů a kooperaci s hráči, kteří mají stejné sestavení. Zatím není plně podporováno a může mít chyby: ve hře více hráčů to používáte na vlastní uvážení.

- **Nahlásil hráč:** dva přátele se stejným balíkem módů to vyhazovalo z každé hry více hráčů, protože jeden mód v balíku (Infinite Supply Depot) je označen jako cheat. RUSE Guard bral každou hru sestavenou s cheatem nebo testovacím nástrojem jako hru jen pro offline: každou hru více hráčů i kooperaci po pár sekundách opustila a nikdy se nedívala, kdo další hraje.
- **Co jsme změnili:** sekundu po začátku hry více hráčů nebo kooperace teď taková hra sdělí hrám ostatních hráčů, o jaké sestavení jde: krátký kód vytvořený z verze hry a módů, nic o vás. Asi po sedmi sekundách rozhodne. Mají-li všichni hráči stejné sestavení (stejnou verzi hry, stejné módy ve stejném pořadí, stejné verze módů), napíše to na obrazovku a hra pokračuje. Má-li někdo jiné sestavení nebo žádné módy, hru opustí jako dřív.
- **Kód hry i pro tyto sady:** v Launcheru teď sada módů s cheatovým módem dostane kód hry jako každá jiná. Stejný kód znamená stejné sestavení: porovnejte si kódy, než začnete hrát.
- **Tuto verzi potřebuje každý hráč:** hra každého hráče musí být sestavena Launcherem 0.4.8.19 nebo Studiem 0.9.8.19, případně novějšími. Po aktualizaci ji příští **Hrát** nebo **Vyzkoušet ve hře** sestaví znovu samo.
- **Zatím není plně podporováno:** vyzkoušeli jsme to ve hře s jedním hráčem, který sám hostoval hru více hráčů proti počítači, a mimo hru na 20 simulovaných hrách až se čtyřmi hráči. Ve dvou ve skutečné hře to zatím nikdo nehrál, takže to může mít chyby: ve hře více hráčů to používáte na vlastní uvážení. Vyzkoušejte to a napište nám na Discord nebo GitHub, co se stalo: jakou zprávu RUSE Guard jste viděli a jestli hra pokračovala.
- **Beze změny:** hra sestavená bez cheatů, bitva proti počítači a kampaň.

**0.9.8.18:** Oprava v pozadí: kontrola upravené kopie vypisuje, co najde, ve stejném pořadí na každém systému.

- **V pozadí:** kontrola upravené kopie (které soubory hry se po jejím sestavení změnily) teď vypisuje, co najde, ve stejném pořadí ve Windows i v Linuxu. Co najde, se nemění.

**0.9.8.17:** Importované modely stojí tam, kde jednotka, s věžemi a vrtulemi na svých místech; munice může mít vlastní třídu zbraně.

- **Povinná aktualizace:** starší verze už nelze používat. Aplikace ji po otevření sama nainstaluje a **Vyzkoušet ve hře** počká, dokud nebude nainstalovaná.
- **Importované modely stojí tam, kde stojí jednotka** (hlášení moddera: modely se kreslily před svým kruhem výběru): **Importovat model…** teď posadí nový model doprostřed jednotky, kterou kopíruje, a dá mu vlastní kostru, takže se jeho věž otáčí tam, kde je věž na vašem modelu. Takto se usazuje každý nový import. Model importovaný dřív si nechá své staré místo, dokud ho znovu neimportujete nebo neposunete (níže), a jednotky z jiných období si nechají svá. Vyzkoušeno ve hře se Shermanem ze hry, otevřeným v Blenderu a přeneseným zpět, na jiných jednotkách; zatím ne s modelem odjinud, s jiným tankem s věží ani s věží, která se otočí dokola.
- **Posunout:** když model pořád nesedí správně, otevřete **Posunout** pod jeho velikostí na stránce jednotky (sbalené, dokud to nepotřebujete; u posunutého modelu zůstává otevřené). **Vpřed**, **Vpravo** a **Nahoru** ho posunou od místa, kam byl usazen, v jednotkách hry (stránka říká, jak dlouhá je v nich kopírovaná jednotka); mínus jde opačně a 0, 0, 0 ho vrátí. Jeho věž a vrtule jdou s ním, takže se dál otáčejí na správném místě, a nová velikost posun zachová. V 3D náhledu ukazuje modrý kruh, kde jednotka stojí, a značka na něm je předek. Model svázaný s kostmi jednotky zůstává tam, kde jsou jeho kosti: ten posuňte v Blenderu. Z příkazové řádky: `ruse import-model ... --move F R U`. Vyzkoušeno ve hře s tanky posunutými vpřed, vzad, vpravo a nahoru.
- **Letadla si nechají vlastní vrtule:** letadlo otevřené v Blenderu ze Studia a přenesené zpět přes **Importovat model…** si nechá vrtule tam, kde je má váš model, tolik, kolik jich má, ať mělo kopírované letadlo cokoli: listy na zemi, točící se disky ve vzduchu. V 3D náhledu jsou disky letadla teď průhledné, tak jak hra kreslí točící se vrtuli. Vyzkoušeno ve hře: model třímotorového bombardéru na kopii jednomotorové stíhačky a naopak. Model letadla odjinud si nechá vrtule tak, jak je kreslí, nehybné: importér zatím nepozná, které jeho části jsou vrtule.
- **Model může dostat každá jednotka:** vojáci, obsluha děla a letadla, ke kterým Studio dosud neumělo model usadit (třeba P-47), teď také dostanou vlastní, svázaný s kostmi samotné jednotky (třeba model ze hry otevřený v Blenderu ze Studia a tam změněný). Ponechá si ty kosti a použije se tak, jak je, a ostatní muži čety se stejnými kostmi ho nosí také. Vyzkoušeno ve hře: četa střelců, obsluha děla a P-47; zatím ne model odjinud.
- **Hrajte je s Launcherem z této aktualizace:** mod s modelem importovaným touto verzí potřebuje Launcher z této aktualizace nebo novější, pro vás i vaše hráče: starší Launcher dá modelu kostru kopírované jednotky, takže se jeho věž otáčí kolem špatného bodu. Mody s modely importovanými dřív se hrají jako dosud.
- **Nová třída zbraně** (na stránce munice): rámeček **Třída zbraně** určuje, jakou část poškození munice způsobí každému druhu cíle. **Nová třída zbraně…** otevře po jednom čísle pro každý: budovy a opevnění, letadla, výsadkáři při seskoku, pěchota, lehká vozidla, pancéřování 1 až 5 a stavební nákladní auta. 1 je plné poškození, 2 dvojnásobné, 0,5 poloviční a 0 znamená, že tento cíl vůbec nemůže napadnout. **Uložit třídu** dá munici vlastní kopii tabulky poškození ze hry, takže poškození žádné jiné munice se nezmění; jako každá změna munice platí pro každou jednotku, která touto municí střílí (pro jedinou jednotku munici nejdřív zkopírujte). **Zpět na třídu ze hry** kopii odebere a smazání zkopírované munice vezme její třídu s sebou. Vyzkoušeno ve hře: čety střelců, jejichž munice dostala čísla proti tankům, střílely po tancích z pušek a poškozovaly je. Viděno v náhledu; v okně aplikace se na tlačítko zatím neklikalo.

**0.9.8.16:** Řešení potíží zachová kopie hry, které jste si udělali sami.

- **Opraveno: „Odstranit je“ v Řešení potíží mazalo kopie, které jste udělali vy:** stejná oprava jako v Launcheru (jeden kód pro obě aplikace). Kopie hry postavená ručně ve složce kopií, testovací kopie nebo referenční kopie se počítala jako zbytek a byla smazána nadobro. Každá taková kopie teď nese malou poznámku „ponechat“ a kopie s poznámkou nikdy není zbytek: odstraňují se jen zbytky samotných aplikací (napůl postavené kopie a ty, které starší verze dělaly pro každou sadu modů). Kopie postavená před touto verzí poznámku ještě nemá: postavte ji jednou znovu touto verzí, nebo do té doby na „Odstranit je“ nesahejte.

**0.9.8.15:** I Původní hra má zlatý název R.U.S.E. 2.0.

- **Ve Studiu samotném se nic nemění:** tato aktualizace je Launcheru (i Původní hra má zlatý název R.U.S.E. 2.0). Zaškrtávací pole zlatého názvu v Nastavení Studia je totéž nastavení jako v Launcheru, takže zrušení zaškrtnutí zde také spouští Původní hru přes Steam.

**0.9.8.14:** Módy s vlastním skriptem zápasu se znovu sestavují.

- **Opraveno: Vyzkoušet ve hře se zastavilo u některých módů** s hláškou „RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...“: několik módů přináší vlastní skript zápasu, jehož hlavička žádá víc místa, než skript potřebuje (mezi nimi 1 VS 7 AI, 1 VS 15 AI, Operation Overlord a Sand Box). Hra tyto skripty spouští bez potíží, ale Studio je odmítalo, takže nešlo sestavit nic s některým z těchto módů. Teď je čte stejně jako hra.

**0.9.8.13:** Hlášení o pádech hry říkají, co k pádu vedlo.

- **Hlášení Bug Watch o pádech hry říkají víc:** pokud jste zaškrtli Bug Watch a hra spadne, hlášení teď také říká, co se hra pokoušela číst nebo zapisovat, a až 16 míst ve hře, která k pádu vedla, přečtených z vlastního hlášení hry o pádu na vašem PC, které ho stále nikdy neopouští. Hlášení, které říkalo jen, kde se hra zastavila, nemohlo ukázat proč; teď můžeme dohledat pády jako ten, který nám tento týden poslal jeden hráč, a opravit je.
- **Smlouva, verze 3:** nyní mezi tím, co obsahuje hlášení o pádu hry, uvádí i tyto dvě nové věci; nic jiného se v ní nezměnilo. Protože se změnila, obě aplikace vám ji při otevření ukážou ještě jednou.

**0.9.8.12:** Vyzkoušet ve hře znovu sestavuje upravené hry.

- **Opraveno: Vyzkoušet ve hře se zastavilo u každého módu** s hláškou „No such file or directory: ...fairplay_watch.bin“: instalátorům verzí 0.9.8.10 a 0.9.8.11 chyběly tři soubory RUSE Guard, takže nešlo sestavit žádnou upravenou hru. Jsou zpět a aplikaci, které chybí některý z jejích souborů, už nelze vydat.

**0.9.8.11:** přihlášení přes Steam se v aplikacích dokončí; v Linuxu se pomocné programy sestavení spouštějí stejně jako ve Windows.

- **Opraveno: přihlášení přes Steam.** Po přihlášení na stránce Steamu Launcher a Studio dál čekaly a nikdy se našeho serveru nezeptaly, jestli jste hotovi: okno zastavilo vlastní kontroly ještě před první. Teď kontroluje každých pár sekund a přihlásí vás, jakmile to Steam potvrdí. Vyzkoušeno v náhledu: kontrola proběhne a okno ukáže, že jste přihlášeni.
- **Pomocné programy se spouštějí znovu na každém systému:** programy, mezi které sestavení dělí práci (importované modely, opravy mapy, pohyb, voda, terén pohledu na mapu), se teď i v Linuxu spouštějí znovu, jak to vždy bylo ve Windows. V Linuxu se spouštěly jako kopie běžící aplikace, což mohlo občas sestavení zaseknout a jedna z našich kontrol tam neprošla. Ve Windows ani v Protonu na Steam Decku se nic nemění.

**0.9.8.10:** módy nad 4 GB, seznamy stavby ve skupinách, rychlejší sestavení velkých módů, vaše soubory v Documents\RUSE 2.0, perština a každá stránka v 11 jazycích, opravy z hlášení testerů; a RUSE Guard, náš anticheat pro skutečné hry více hráčů; Bug Watch, hlášení o pádech a používání, která si můžete zapnout; přihlášení přes Steam; a dohoda při prvním spuštění.

- **Opraveno, nahlásil hráč: módy nad 4 GB.** Upravená hra, jejíž balíčky přesáhly 4 GB, se přestala sestavovat („'I' format requires 0 <= number <= 4294967295“). Balíčky teď nesou svou plnou délku a balíček nad 4 GB se zapisuje v širším uspořádání, které hra dokáže číst díky malé záplatě hry: stáhne se jednou a použije se jen na vaši upravenou kopii, nikdy na hru ve vaší složce Steam. Nad 32 GB nebo u jednoho souboru nad 4 GB to sestavení řekne jasně. Vyzkoušeno ve hře: kopie nad 4 GB a s 200, 283 a všemi 366 jednotkami z jiných období.
- **Mnoho vlastních modelů:** hra hledá náhradní textury balíčku přes index a sestavení, které je přidávalo pro importované modely, ho zapisovalo špatně: s mnoha jednotkami z jiných období se hra při načítání zasekla nebo spadla. Teď se zapisuje tak, jak ho hra čte, pro každý mód, který je přidává. Vyzkoušeno ve hře se všemi 366 jednotkami z jiných období.
- **Seznamy stavby ve skupinách:** s mnoha jednotkami seznam stavby budovy přetékal přes okraj obrazovky a k jednotkám dole se nedalo dostat. Každý seznam teď ukazuje jeden řádek na skupinu, vlastní linie hry (nová jednotka patří do skupiny svého druhu): nejvýš 6 jednotek ve skupině a 10 skupin v budově, aby celý seznam zůstal na obrazovce. Studio řekne proč, když je skupina plná, a ukazuje skupiny tam, kde jednotky přidáváte; mód udělaný dřív, který tyto limity překračuje, se přesto sestaví, s varováním. Vyzkoušeno ve hře s 297 jednotkami z jiných období ve skupinách.
- **Rychlejší sestavení:** modely, které importujete, se uchovávají mezi sestaveními a nové vznikají souběžně na jádrech vašeho PC. Mód s 366 jednotkami z jiných období se na PC s 8 jádry sestavoval asi 18 minut; teď asi 5 poprvé a asi 3 potom, se stejnými soubory hry, bajt po bajtu.
- **Importované modely (hlášení testerů):** část věže na kosti, kterou zkopírovaný vzhled nemá v seznamu (M109 zkopírovaný z M7 Priest), zastavila import; teď jde na vlastní seznam kopie. Část věže na modelu bez věže (P-40, M274 Mule) jede s korbou, tažené dělo zdálky ukazuje svůj vlastní model a tenká pásková textura dostane svou náhradní texturu. Tažená děla vyzkoušena ve hře; části věží zatím neprohlédnuty zblízka.
- **Mosty (hlášení testera):** jedna karta Mosty: nový most, vaše mosty (každý s Přejít a Smazat) a vlastní mosty mapy s jejich přechody, odebírané nebo vracené jedním tlačítkem. Nový most se počítá, když odebrání starých rozdělí mapu na dvě části, a tvarování terénu drží konce vlastních mostů mapy v jejich výšce. Mazání se hledá snáz (Malování a odstranění nebo klávesa X). Mód jednotek a změny mapy udělané pod jedním jménem se sestaví spolu a pohled na mapu zase ukazuje modely hry. Zatím nevyzkoušeno ve hře.
- **Vaše soubory v Documents\RUSE 2.0:** vaše módy, mapy, exporty a zálohy jdou do Documents\RUSE 2.0, kde je ukazuje Průzkumník souborů; co Studio drželo ve své staré složce, se tam jednou přesune a Studio to řekne. Smazat mód… ho pošle do Koše, Ukázat složku tohoto módu ji otevře a Nastavení ukazuje, kde co je. Viděno v náhledu; zatím nevyzkoušeno v oknech aplikací.
- **Perština a 11 jazyků:** perština je 11. jazyk aplikací, psaný zprava doleva; README, wiki, tyto poznámky a obrazovky instalace jsou ve všech 11.
- **Povinné aktualizace:** aktualizace, kterou označíme jako povinnou, se nainstaluje sama, s oknem, které nikdo nemůže zavřít (aplikace od této verze tu značku umí přečíst). Okno Co je nového drží svou výšku, když v něm posouváte.
- **Jen vlastní kopie:** než Hrát nebo Vyzkoušet ve hře sestaví upravenou kopii, aplikace zkontrolují, že složka hry je kopie, kterou vlastníte, podle toho, co tam nechal Steam, ve Windows, v Protonu na Steam Decku i v Linuxu. Když tu vaši nejde potvrdit (krabicová kopie z doby, než byl R.U.S.E. na Steamu), okno vám dovolí otevřít tiket a my vám pošleme odemykací kód pro ten PC.
- **Discord:** aplikace a stránky používají novou pozvánku, která nevyprší.
- **Dohoda při prvním spuštění:** když se Studio nebo Launcher otevře poprvé, řekne, co RUSE Guard dělá, a požádá vás o jeho přijetí (pro hraní online s aplikacemi je to nutné), zda zapnout Bug Watch (volitelné), a o uživatelské jméno, které naši vývojáři vidí u vašich hlášení: přidá se # a čtyři číslice, aby bylo jedinečné, třeba Nick#4821. Jedno jméno platí pro obě aplikace. Dohoda se ukáže znovu, když se změní. Viděno v obou aplikacích. Ve všech 11 jazycích.
- **RUSE Guard:** náš anticheat podle návrhu DomesticNukes. Pracuje jen v hrách více hráčů a kooperaci, nikdy v hře jednoho hráče, v bitvě proti počítači, v kampani ani když tvoříte módy. Módovaná kopie postavená s cheatem nebo testovacím nástrojem je jen pro hru offline: hry více hráčů a kooperaci sama opustí. Během skutečné hry porovnává názvy vašich běžících programů se seznamem známých cheatovacích nástrojů (jen názvy; nic jiného se nečte) a to, co ze hry sesbírá, se ukládá pod vaše uživatelské jméno, nikdy pod váš účet Steam. Vyzkoušet ve hře s ním staví své kopie. Vyzkoušeno ve hrách více hráčů proti skutečnému soupeři; důkazy dorazí na náš server.
- **Bug Watch (volitelné):** když ho zaškrtnete, Studio a Launcher počítají, co používáte a kdy se něco pokazí, pády aplikací i hry, s tím, které módy byly zapnuté, a jednou denně to posílají našim vývojářům s vaším uživatelským jménem. Žádná skutečná jména, žádný účet Steam, žádné soubory. Vypnuto, dokud ho nezaškrtnete; odškrtněte ho kdykoli a to, co bylo uchováno, se smaže. Viděno v obou aplikacích.
- **Přihlásit se přes Steam:** přihlášení na vlastní stránce Steamu ve vašem prohlížeči potvrdí, že R.U.S.E. vlastníte, pro hru online, RUSE Guard a stahování obsahu. Vaše heslo nikdy nevidíme a vaše Steam ID se nikdy neukládá: jen propustka uložená na vašem počítači na 30 dní. Studio se zeptá jednou; Nastavení Launcheru ji otevře kdykoli. Zatím ji nic nepotřebuje. V aplikacích zatím nevyzkoušeno.

**0.9.8.9:** stahování na více PC, a bezpečnější čtení obrázků.

- **Opraveno, nahlášeno hráčem:** na PC, jehož Windows nemá certifikát, kterým se ověřuje stahování z GitHubu, a nedokáže ho získat, stahování selhávalo („unable to get issuer certificate“). Stahování Studia (jeho aktualizace, záplaty hry, modely jednotek ér a online textury Map Paint) teď zkouší i seznam certifikátů Firefoxu, který Studio nese s sebou.
- **Bezpečnější obrázky:** knihovna, kterou Studio čte obrázky (Pillow), je teď ve verzi 13.0.0, s opravami proti schválně upraveným souborům obrázků, které mohly aplikaci shodit, vyčerpat její paměť nebo hůř.
- **Pečlivější kód:** 12 varování kontroly kódu GitHubu k tomuto projektu je vyřešeno. Když Studio ukazuje své stránky ve vašem prohlížeči, otevírají jen jeho vlastní soubory, ověřené způsobem, který ta kontrola rozpozná; stahování vyžaduje TLS 1.2 nebo novější, jako už dřív; a čtení chyb silnic z neúspěšného testu zůstává rychlé u jakékoli zprávy. Jinak se na tom, jak Studio funguje, nic nemění.

**0.9.8.8:** úvodní obrazovka a tabule budov, vlastní budovy, RUSE Decoy pro zvuky a animace, každé pravidlo hry v jedné záložce, a R.U.S.E. 2.0 ve zlaté.

- **Úvodní obrazovka:** pokračujte ve svém módu, začněte nový, nebo ji přeskočte (i natrvalo). Kroky nového módu: jeho název, zda si každý národ ponechá své jednotky, nebo začne prázdný, výzkum (ze hry, žádný, nebo vlastní), tabule budov, pak co mód změní. Viděno ve hře.
- **Tabule budov:** budovy každého národa jako řady jednotek, které nabízejí jejich nabídky stavby, v pořadí hry. Vložte jednotku (vlastní jednotku národa, kopii jednotky jiného národa, jednotku éry), přetáhněte ji po řadě nebo k jiné budově, vyjměte ji, nebo ji nechte zkoumat od jednotky, pod kterou patří. Stránka každé jednotky říká, kde se staví. Viděno ve hře.
- **Přidat budovu…:** kopie budovy ze hry, která dělá stejné jednotky, nebo budova s vlastními jednotkami a vlastní záložkou na liště stavby, až tři na národ. Druhá a třetí potřebují malou záplatu hry pro více budov: Studio ji jednou stáhne a použije jen na vaši upravenou kopii, nikdy na hru ve vaší složce Steamu. Viděno ve hře.
- **Vlastní vzhled budovy:** na stránce nové budovy importujte 3D model místo jednoho dílu vzhledu, který kopíruje (hlavní budovy továrny nebo velitelství, nebo dílu, který vyberete), a dejte jí vlastní obrázek v nabídce stavby. Viděno ve hře.
- **Importovat model… v záložce Mapy:** 3D model (.glb, .gltf nebo .3ds) se stane vlastním kamenem, předmětem, rostlinou nebo stromem vaší mapy, umisťovaným jako ty ze hry, s velikostí a uvedením autora (modely jiných: jen CC0 nebo CC-BY). Jednotky ho porazí jako ty ze hry; se zaškrtnutým **Pevné** ho objedou. Viděno ve hře.
- **RUSE Decoy, návrhář zvuku a animací,** místo záložky Hudba. Každý zvuk hry podle druhu (zbraně zblízka a zdálky, zásahy, motory, okolí, rozhraní, karty lstí, hlasy jednotek, rádio, repliky misí s tím, co která říká, hudba): přehrajte ho, dejte mu vlastní hlasitost (0 až 200 %) nebo ho nahraďte. Animace: jiný klip místo klipu, klip pomalejší nebo rychlejší, kost zvětšená nebo otočená, nebo motion capture na vojácích, z knihovny 3 205 volných pohybů (databáze motion capture CMU a 100STYLE, s uvedením autorů), každý stažený, když ho vyberete. Stránka jednotky otevře RUSE Decoy na jejích vlastních zvucích a animacích. Viděno ve hře. Jeho chybové zprávy jsou zatím jen anglicky.
- **Nastavení počítače a hráčů:** záložky Ekonomika a AI jsou jedna záložka. Nastavení hráčů: peníze a příjem, zásobovací sklady, výroba a karty lsti, jako dřív. Počítačoví hráči: každá z jejich 47 hodnot na výchozí sadě, každé obtížnosti a každé povaze (hodnota, kterou hra v sadě vynechá, ukazuje 0, se kterou hra počítá). **Pravidla hry:** dalších 172 hodnot hry v 16 skupinách (bitva a kapitulace, populace, pohyb a silnice, palba a cíle, poškození, lesy a kryt, letadla, karty lsti v akci, stavění budov, hodnocené hry online, obrysy a efekty na obrazovce, barvy hráčů a sektorů s výběrem barvy, a další), každá pojmenovaná a vysvětlená. Zatím nevyzkoušeno ve hře.
- **Všechny hodnoty a soubory:** záložky Všechny hodnoty a Soubory jsou jedna záložka, s přepínačem nahoře; otevře se na části použité naposledy.
- **Opraveno:** Všechny hodnoty ukazovaly čísla barvy ve špatném pořadí (hra drží modrou první), takže barva hráče 1, modrá, vypadala oranžově a zadání červené měnilo modrou. Barvy se teď ukazují a zadávají od červené; soubor módu drží pořadí hry, jako dřív.
- **Opraveno: tmavé a světlé skvrny na mapách, které udělalo Studio** (prázdné, zvětšené, reliéfní a sektorové mapy): sklon terénu se zapisoval špatně, takže tráva a pole byly osvětlené nerovnoměrně. Mapa je osvětlená správně, jakmile se sestaví touto verzí (její terén se poprvé udělá znovu). Viděno ve hře.
- **Odebrat staré přechody (od DomesticNukes):** v silnicích záložky Mapy, se zapnutým **Odebrat mosty mapy**, **Uzavřít přechody po starých mostech** uzavře i terén, kde každý starý most stál nad vodou, a přeruší silniční spojení přes něj: nic už tam nepřejde; zbytek silniční sítě zůstane. Zatím nevyzkoušeno ve hře.
- **R.U.S.E. 2.0 ve zlaté:** upravená hra, kterou sestaví Vyzkoušet ve hře, začne bitevní scénou se startujícím motorem a její hlavní nabídka, malý název každé nabídky, obrysy nabídek a načítací obrazovky říkají R.U.S.E. 2.0 ve zlaté. Udělá se na vašem PC ze souborů vaší vlastní hry napoprvé (jednou pár minut, pak se uchová). Nastavení má zaškrtávací pole pro zachování názvu hry. Viděno ve hře.
- **Písmo hry:** Studio je psané písmem nabídek hry, vzatým z vaší hry při každém spuštění (písmo se se Studiem nedodává).
- **Opraveno, nahlášeno modderem:** model importovaný na novou jednotku vytvořenou z Panthera přistál daleko od jednotky; na jednotkách z 85 dalších (155mm GPF, SU-85, Carro Veloce, StuG III, M7 Priest...) seděl mimo věž. Studio teď správně čte, kde se jejich věže otáčejí. Model importovaný dřív si nechá staré místo: použijte znovu Importovat model… na té jednotce. Zatím nevyzkoušeno ve hře.
- **Opraveno, nahlášeno hráčem:** model s obrázky JPG nebo WebP (většina stažených .glb) byl odmítnut; teď se importuje. Model, který import stále neumí přečíst (komprimované sítě, obrázky KTX2), to řekne, i jak to opravit v Blenderu. Zatím nevyzkoušeno ve hře.
- **Opraveno, nahlášeno hráčem:** tank ze hry otevřený v Blenderu a importovaný zpět měl věž nehybnou. Otevřít v Blenderu teď pojmenuje kost každého dílu jako hra a import otáčí díl na kosti věže s věží. Model exportovaný dřív si nechá stará jména: otevřete ho v Blenderu znovu. Zatím nevyzkoušeno ve hře.
- **Pojmenujte svou munici:** zkopírovaná munice se ve hře jmenuje tak, jak ji pojmenujete, a stránka každé munice má **Její jméno ve hře**: nové jméno nebo druh, ve všech jazycích naráz, pak jeden jazyk zvlášť. Zatím nevyzkoušeno ve hře.
- **Vlastní typy flagů:** pod flagy jednotky **Vytvořit nebo změnit typy flagů…** vytvoří pojmenovaný typ: zaškrtněte flagy hry, které zapíná a vypíná. Dejte ho jakékoli jednotce; odeberte ho a její flagy se vrátí, jak byly. Změňte typ a změní se každá jednotka, která ho má. Hra jedná jen podle svých vlastních flagů, takže typ kombinuje, co už dělají. Zatím nevyzkoušeno ve hře.
- **Rychlost střely správně vysvětlená:** průvodce čísly říkal, že rychlost střely, odpor, přepínač „bez fyziky“ a čas před výstřelem jsou jen vzhled. Rozhodují, kdy zásah dopadne: pomalejší střela zasáhne později a na pohyblivý cíl se míří s předstihem o dobu letu (z fungování hry; zatím neověřeno testem).
- **Každá chyba v deseti jazycích:** 35 chyb Studia, které přišly s importem modelů a tabulí budov.
- **Poděkování:** README říká, co engine od LittleGroove v našem stále dělá, co je naše, a že naše čtečka textur také používá kodek ProLution.
- **Stále chybové, používejte na vlastní uvážení:** textury Map Paint a obě prázdné mapy (Prázdný terén a Prázdný oceán).

**0.9.8.7:** Znovu a výběr umístěného, umisťování mřížkou / obdélníkem / cestou, větší prázdné mapy, a každá hodnota vysvětlená.

- **Opraveno, nahlášeno modderem:** u nové jednotky vytvořené z jedné ze 17 jednotek hry (Královský tygr, atomová děla, V2...) se pole pro změnu modelu nikdy neobjevilo. Studio teď tyto modely najde, a když některý nenajde, pole to řekne místo toho, aby zmizelo.
- **Záložka AI vysvětlená:** každá hodnota počítačových hráčů říká, co dělá, v jednoduchých jednotkách, a která platí v bitvě pro každou obtížnost a profil; režimy, obtížnosti, profily a jednotky se vybírají podle jména.
- **Každá hodnota vysvětlená, všude:** Všechny hodnoty, záložka Jednotky, štětce záložky Mapy (velikost v metrech, síla podle toho, co dělá) a záložka Hudba (kdy hraje který bitevní seznam).
- **Záložka Ekonomika, Normální a Jaderný zvlášť:** kde se oba režimy liší, má každý svá pole. Změna jen Jaderného režimu ještě nebyla ve hře vyzkoušena.
- **Znovu a výběr:** Znovu v každém nástroji mapy (Ctrl+Y nebo Ctrl+Shift+Z a tlačítko); v panelech Budovy a Předměty a stromy vyberte umístěné (klik, Shift+klik nebo rámeček), přetáhněte, otočte, změňte velikost nebo smažte, i objekty samotné mapy.
- **Mřížka, Obdélník a Cesta:** řady objektů v mřížce nebo obdélníku, budovy čelem k silnicím, a živé ploty, stromořadí a pásy stromů podél cesty, s krytem.
- **Větší prázdné mapy:** okno Velikost mapy nové prázdné mapy přidá nebo ubere pruhy terénu na kterékoli straně a Vytvořit sektory ji vyplní sektory.
- **Nabídky a ovládání:** řádky čísel místo posuvníků, hledání s #štítky a nedávnými hledáními, vyskakovací karty, a klávesy k přeřazení (Prohodit, Vzít, Zrušit).
- **Bezpečněji:** zavření s neuloženou prací se nejdřív zeptá; mapa s nově odříznutým terénem se odmítne před Testem ve hře; mod ze staršího Studia se aktualizuje po záloze (Aktualizovat tento mod); uchované výsledky sestavení zůstanou platné i po aktualizaci Studia.
- **Každá zpráva v deseti jazycích:** chyby Studia a řádky sestavení.
- **Nová jednotka** vynechá dvě jednotky bez modelu, ze kterého začít (57mm dělo SOLO a výsadkáře SOLO).
- Zatím nevyzkoušeno ve hře: co se umístí Mřížkou, Obdélníkem a Cestou, přesunuté objekty a větší mapa vytvořená ve Studiu.
- **Stále chybové, používejte na vlastní uvážení:** textury Map Paint a obě prázdné mapy (Prázdný terén a Prázdný oceán).

**0.9.8.6:** každý flag a každé číslo jednotek vysvětlené, nástroje mapy ukazují, co udělaly, a prázdné mapy se kreslí správně.

- **Flagy jednotek vysvětlené:** každý flag na stránce jednotky ukazuje svůj název a po najetí myší je vidět, co dělá, jak ho použít a jak moc si jsme jistí. **Průvodce flagy: všechny vysvětlené** vypíše všech 105, s hledáním. Studio kontroluje flagy jednotky: známý pád hry (flagy nákladního auta na něčem, co není nákladní auto, ozbrojené letadlo s flagem průzkumu bez flagu stíhačky) ukáže svou opravu a Studio nespustí hru, dokud není opraven; flagy, které asi rozbijí jednotku, dají varování.
- **Každé číslo vysvětlené:** najeďte na název libovolného čísla jednotky nebo budovy a uvidíte, co znamená; vedle jeho hodnotu v jednoduchých jednotkách (metry, km/h, sekundy, stupně, $, %), posuvník, který ho zmenší nebo zvětší oproti hodnotě hry (jeho základní hodnotě, od -90 % do +300 %), a kde leží mezi jednotkami hry stejného druhu. Rychlosti jsou v km/h samotné hry.
- **Jak fungují zbraně a munice**, krok za krokem, v rámečku Zbraně.
- **Nástroje mapy ukazují, co udělaly:** Kryt, Odkrýt, Město, Les, Zablokovat a Otevřít označí terén, přes který šel každý tah, a řeknou, kolik m² se pro jednotky změnilo, nebo že se nic nezměnilo. Město pracuje ve skutečných metrech a nejdřív zakroužkuje budovy, které kliknutí pokryje.
- **Umisťování:** umístěné budovy, stromy a předměty ukazují své skutečné modely (s tečkou u paty); vybraný je vidět průhledně pod ukazatelem před kliknutím; seznam k umístění je mřížka obrázků. Stromy už nejsou černé a čísla sektorů se schovají, když je kamera blízko.
- **Prázdné mapy** (viděno ve hře na Prázdném terénu): stíny na rovném terénu; to, co umístíte tam, kde kopírovaná mapa měla moře, se nakreslí; podlaha kamery sleduje nový terén.
- **Stále chybové, používejte na vlastní uvážení:** textury Map Paint a obě prázdné mapy (Prázdný terén a Prázdný oceán).

**0.9.8.5:** letadla v jakékoli roli, zbraně, které zasahují letadla, a knihovna pro štětec Textura v Map Paint.

- **Role letadla** (hlášení hráče: stíhací bombardér, kterému se daly kobercové bomby bombardéru, doletěl k cíli a nic neshodil): nové pole Role na stránce letadla z něj udělá Stíhačku, Stíhací bombardér, Bombardér nebo Průzkumníka. S ní se mění jeho chování, to, jak ho používají počítačoví hráči, i jeho slova v nabídce stavby. Bomby bombardéru jdou do pumovnice (zkopírované z bombardéru hry), jediným způsobem, jak je nálet bombardéru shodí. Ověřeno ve hře: stíhací bombardér změněný na bombardér shazuje bomby; průzkumník, který si nechá zbraně (Stuka, ME109), dál útočí a vidí jako průzkumníci.
- **Průzkumná vozidla:** pole Role pozemního vozidla z něj udělá Průzkum: dohled průzkumných vozů (mnohem dál než tank), to, jak je používají počítačoví hráči, jejich slova v nabídce stavby, a může vjet do lesa (ověřeno ve hře s Panzerem IV).
- **Co zbraň zasahuje:** Zasahuje u každé zbraně vybere zem, letadla nebo obojí (druhá zbraň vedle, tak jako protiletadlová děla hry nesou na každé jednu). Ověřeno ve hře: tankové granáty střílející na letadla. Známé: zbraň letadla nastavená jen na zem zatím nezpůsobuje poškození.
- **Štětec Textura v Map Paint dostal knihovnu:** textury terénu ze hry (tráva, pole, písek, sníh, skály, cesty..., podle bojiště, s hledáním), čtverec terénu libovolné mapy, vlastní obrázky a obrázky zdarma z internetu (Poly Haven a ambientCG, CC0; letecké snímky USA, volné dílo), jeden obrázek stažený na kliknutí a uložený ve vašem módu i s uvedením autora. Posuvník Velikost, naposledy použité textury a **Detail hry zblízka**, který na malovaný terén položí vlastní obtisky hry pro texturu ze hry. Zatím neověřeno ve hře; stahování z internetu zatím nevyzkoušeno.
- **Objekty umístěné v otevřeném terénu**, daleko od měst, statků a lesů mapy, jsou teď v dosahu vykreslování hry a velké skupiny nových objektů jsou uspořádané jako objekty hry (zatím neověřeno ve hře).
- **Rychlejší přemalování:** namalovaný terén se uchovává od sestavení k sestavení, ať ho namalovala kterákoli kopie nebo mód: mapa namalovaná stejně ho dostane zpět za pár sekund, ne minut.
- **Stále chybové, používejte na vlastní uvážení:** textury Map Paint a obě prázdné mapy (Prázdný terén a Prázdný oceán).

**0.9.8.4:** vlastní mise, prázdné mapy k zastavění a mnohem víc k přizpůsobení.

- **Stále chybové, používejte na vlastní uvážení:** textury Map Paint a obě prázdné mapy (Prázdný terén a Prázdný oceán).
- **Vlastní mise:** nová Operace nebo nová kapitola kampaně dostane vlastní misi na straně Scénář obrazovky mapy: strany, cíle, události (Když → Udělej: přivést jednotky, pohyb, útok, držet zónu, dělostřelectvo, bombardování, výsadkáři, zprávy, peníze, vítězství, porážka) a pohyby kamery. Ověřeno ve hře: její pohyb kamery, cíle (zóna, zničená skupina, čas), opakované události, peníze, strana předaná počítači. Zatím nevyzkoušeno: výsadkáři, pohyb kamery spuštěný událostí.
- **Mapa | Scénář** na obrazovce mapy: věci druhé strany jsou vybledlé a nejde je omylem chytit.
- **Prázdné mapy:** ze zkopírované mapy už není nic vidět a velitelství každého hráče umístíte sami (sestavení čeká, až budou umístěna všechna). Prázdný terén funguje i pro Operace a kapitoly kampaně.
- **Vlastní sektory:** malujte je, táhněte jejich rohy, nakreslete nový jako obdélník, nechte zem bez sektoru, sektor smažte (ověřeno ve hře).
- **Zásobovací sklady:** karta Ekonomika dá každému skladu na každé mapě nebo na jedné mapě víc nákladních aut (krát, nebo počet na každý); žádný strop 1 000 aut.
- **Karta Národy:** skryjte najednou všechny jednotky národa, zase je ukažte nebo naplňte jeho nabídky jednotkami z epochy.
- **Upravit nainstalovaný mód:** otevřete libovolný mód z Launcheru; cizí se stane vaší kopií pod vlastním jménem. Módy RUSE Mod Manager (.rmod) se převedou, aby šly měnit jejich hodnoty.
- **Kontrola módu jednoduchými slovy**, s tlačítkem opravy u každého problému.
- **Vlastní vzhled jednotky:** vlastní kopie jejího modelu k přemalování; čety nosí výchozí uniformu nebo vlastní; vyberte nákladní auto, kterým jede četa nebo dělo. Pěchota je vidět ve 3D a otevře se v Blenderu.
- **Pancéřování** se vybírá z úrovní hry, takže karta ukazuje, s čím jednotka bojuje; **importovaná letadla** si nechají točící se vrtule a vracejí se natočená dopředu (obojí ověřeno ve hře).
- **Velikosti modelů na posuvníku** (Drobný, Velikost hry, Skutečná, Obří: 0,05 až 20), kdykoli změnitelné, všechna letadla najednou.
- **Víc ke změně:** vlastní hodnota obtížnosti nebo profilu AI pro hodnotu, kterou má jen Výchozí; čísla za posuvníky nástrojů mapy; hlasitější a delší úpravy hudby.
- **Opraveno:** jednotka ukázaná v nabídce, ale zkoumaná ze skryté, zastavila hru: kontrola ji jmenuje a sestavení ji odmítne. Tanky znovu střílejí přes smazaná města a jednotky už nepadají do děr po odstraněných mostech (ověřeno ve hře).
- **Stahování funguje na každém PC:** když Windows ještě nestáhl certifikát, kterým se ověřuje GitHub, Studio o něj Windows požádá, jako prohlížeč, a zkusí to znovu (zatím nevyzkoušeno na PC, které mělo ten problém).

**0.9.8.3:** kopie s módy se ukládají tam, kam řeknete.

- **Kam se ukládají kopie s módy**, v Nastavení: vyberte složku, ve které se sestavuje kopie hry s módy, nebo se vraťte
  na doporučené místo, `RUSE-Instances` na disku hry (tam kopie sdílí soubory hry a je hotová za pár sekund; na jiném
  disku je to úplná kopie hry, pomalejší a větší). Čistá záloha hry jde vedle. Další Vyzkoušet ve hře sestaví na
  novém místě; starou složku lze smazat ručně. Launcher používá stejnou složku.

**0.9.8.2:** přicházejí jednotky z jiných období: jejich modely, ve skutečné velikosti, za výzkumem.

- **Jednotky z jiných období:** období WWI, WWII+, Studená válka a Současnost na kartě Jednotky teď mají své
  jednotky: 366, každá na bezplatném modelu jiného autora (CC0 nebo CC BY), uvedeného. Každé období se stáhne ve
  Studiu, když ho vyberete, z našeho GitHubu (každý soubor ověřený: WWI 232 MB, WWII+ 198 MB, Studená válka 996 MB,
  Současnost 709 MB), a samo se aktualizuje, jak přibývají další hotové.
  - **Ve skutečné velikosti:** skutečná šířka každé jednotky (u letadla rozpětí křídel) v měřítku hry; dá se změnit
    od 0,2 do 5 násobku.
  - **Zkoumané jako jednotky hry:** z kterékoli jednotky budovy svého národa, i z jednotek období v modu, takže
    funguje řetěz (T-80, pak T-90M), s cenou a dobou výzkumu. Jednotky WWI a WWII+ se dají koupit hned; ty ze Studené
    války a Současnosti začínají jako zkoumané z vhodné jednotky.
  - **Vlastní karty** v nabídce stavby a při výběru.
  - Ověřeno ve hře: načtou se hned, karty výzkumu a řetěz, Land Rover s vlastním modelem, velikosti. Zatím
    nevyzkoušeno: tažená děla (zatím není dělo ze hry, ke kterému je přizpůsobit).
- **Importovat model…:** model, který začíná figurkou osádky, teď dostane vlastní model (džípy zkopírované z
  Kübelwagenu ukazovaly Kübelwagen); modely malované metodou specular-glossiness si nechají barvu; barvy zadané čísly
  už nejsou černé; velké modely se importují rychleji.
- **Jednotka zkoumaná z jednotky jiné armády** nechávala hru na nekonečné obrazovce načítání: **Nová jednotka…** teď
  to propojení odstraní a sestavení odmítne jednotku zkoumanou z chybějící jednotky nebo z jednotky jiného národa a
  řekne proč a jak to opravit.
- **Odebrání jednotky, ze které se zkoumají jiné:** v **Nastavení > Výzkum** vyberte, zda nejdřív varovat (výchozí),
  odmítnout, nebo je znovu propojit s jejím vlastním předchůdcem; jednotka, která ukazuje na odebranou, to ukáže na
  své stránce a v kontrole. Doby výzkumu se zadávají v sekundách nebo minutách (že je hra počítá v sekundách, zatím
  není ve hře vyzkoušeno).
- **Linux a Steam Deck (přes Proton):** Studio se otevře ve vašem webovém prohlížeči, když jeho vlastní okno nemůže.
  Na Linuxu zatím nevyzkoušeno: dejte nám vědět, jak to šlo.

**0.9.8.1:** Nástroje LittleGroove přicházejí do Studia, s hudbou a zvuky a národem proměněným v jiný.

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
- **Jednotky z jiných období:** karta Jednotky nabízí vedle jednotek hry období WWI, WWII+, Studená válka a
  Současnost. Zatím v nich nejsou žádné jednotky: přijdou v některé z dalších aktualizací.
- **Nová mapa: od nuly…** je na kartě Mapy, dokud není otevřená žádná mapa.
- **Terén Prázdného terénu se kreslí jako vlastní.** Nová mapa začatá od nuly má terén vytvořený z vašich tahů terénu,
  ne posunutý terén mapy ze hry: kulaté břehy zblízka i shora, žádné promáčkliny na vrcholcích kopců a budovy i tanky
  stojí přesně na něm. Ověřeno ve hře na testovacích mapách.
- **Prázdný oceán zůstává, s varováním** na svém tlačítku: oddělené ostrovy zatím nejsou připravené na velké
  bitvy (níže).

Ve hře zatím nevyzkoušeno: rámeček Vylepšení, Všechny hodnoty, Soubory, nástroje misí, doplňky map
a zvuky pozadí.

**Proč zatím nejsou námořní mapy.** Zkoušeli jsme mapy z ostrovů pro velké bitvy s loďmi a v cestě stojí samotná hra:

- Pozemní jednotka poslaná na ostrov, kam se nemůže dostat, způsobí pád hry.
- Spojení ostrovů pruhem souše pádu zabrání, ale počítač po něm pak jen posílá svou pěchotu.
- Bez silnice mezi ostrovy nejde nikde postavit žádnou budovu.
- Se zbraněmi ze hry si lodě a pozemní jednotky skoro neublíží.

Samotná data mapy pád neopraví, a tak námořní mapy počkají.

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

**0.9.6:** nová jednotka může mít vlastní 3D model z jakéhokoli 3D nástroje a **Vyzkoušet ve hře** spustí hru hned,
když se nic nezměnilo. A jedno prvenství:

- **První model z jiného 3D programu v R.U.S.E.:** M1 Abrams, vytvořený jako nová jednotka USA vedle Shermana. Kupuje
  se na Armor Base s vlastní kartou, staví se a otáčí věží jako tanky hry. Viděno ve hře.

| Dřív | Teď |
|---|---|
| Nová jednotka měla model jednotky, kterou kopíruje. | **Importovat model…** na stránce nové jednotky: vyberte **.3ds** (jeho obrázky vedle něj nebo ve složce nad ním) nebo **.glb** (z Blenderu a většiny 3D nástrojů). Studio ho přizpůsobí jednotce, kterou kopíruje: její délku (krát **Velikost**: 1 je stejně dlouhý, Abrams oproti Shermanovi je 1,36), jeho věž na věž té jednotky, aby ji hra otáčela stejně, jeho obrázky jako vlastní textury. Stránka ho ukazuje ve 3D; **Použít model kopírované jednotky** ho zase odebere. Do vašeho módu jde jako `files/models/<the unit's name>.glb`, který se otevře v Blenderu. **Viděno ve hře.** Raná verze: pásy a kola se zatím neotáčejí, záblesk výstřelu je vidět tam, kde má ústí hlavně kopírovaná jednotka, a vrak je vrak kopírované jednotky. |
| Nová jednotka s vlastní kartou shodila hru, když byla postavena (0.9.5). | Její karta je i na mapě tam, kde ji hra čte. **Viděno ve hře.** |
| Mapu vytvořenou pomocí **Duplikovat mapu** nešlo ve Studiu smazat. | **Smazat mapu**, pod Duplikovat mapu na nové mapě: jednou se zeptá, pak její složka jde do Koše, odkud ji můžete vrátit. Vlastní mapy hry smazat nejde. |
| Studio hlásilo, že Blender není nainstalovaný, když byl rozbalený, a ne nainstalovaný. | Najde Blender, ať jste ho rozbalili kamkoli (nejvyšší složka disku nebo o jednu níž, Stažené soubory, Plocha, Dokumenty). |
| Přebarvení vycházela s některými barvami trochu jinak (červená a modrá skvrna mohla zfialovět). | Každý čtvereček 4 x 4 si drží vlastní barvy. Přebarvené jednotky a namalovaný terén vycházejí s mírně jinými daty obrázku než v 0.9.5 (stejný vzhled), takže se otisk a kód pro připojení takového módu změní: hráči by měli všichni aktualizovat, než budou hrát spolu. |
| **Vyzkoušet ve hře** pokaždé znovu sestavilo celou upravenou kopii, i když se nic nezměnilo. | Od posledního sestavení se nic nezměnilo: hra se spustí hned, bez sestavení (testovací mód: z 21-29 s na méně než 0,1 s). Sestavení použije nezměněné soubory poslední kopie, místo aby je znovu kopírovalo. |
| Každé sestavení četlo data jednotek hry znovu od začátku. | Uchovávají se mezi sestaveními: velký testovací mód trval pokaždé 213 s; teď první sestavení trvá zhruba stejně a další 68 s. Hra už před sestavením nekopíruje všechna svá data. |
| Odstranění většiny velké mapy vyčerpalo paměť Studia a odstranění celé mapy bylo odmítnuto jako příliš velké. | Odstranění se spočítá během sekund, jedno po druhém; **Vymazat celou mapu** v panelu Odstranit (Zpět ho vezme zpět). Smazaná scenérie se zapisuje úsporně. Nové: ve hře zatím neviděno ve velkém. |
| Terén srovnaný pod silnicí nechával silnici ve vzdáleném pohledu ve staré výšce. | Model silnice sleduje nový terén. Nové: ve hře zatím neviděno. |
| Srovnané koryto řeky si zblízka nechávalo obrázky skal a soutěsky. | Vyplní se od obou břehů a jeho nízký porost se odstraní. Nové: ve hře zatím neviděno, jak to udělá sestavení. |
| Zatímco se sestavoval index hry (asi minutu), Studio mohlo jen čekat. | Mapy a Nastavení zůstávají použitelné; řádek dole řekne, až bude hotový. |
| Pomalé spuštění nezanechalo žádnou stopu. | Kroky každého spuštění se měří; **Kopírovat zprávu** v Řešení potíží vypíše posledních pět. |
| Stránka v okně se mohla dostat k větší části aplikace, než jsou její vlastní volání. | Dostane jen vlastní volání aplikace. |

Také `ruse import-model <file> --like <model> --unit <name>` dělá totéž z příkazového řádku.

**0.9.5:** jednotky dostanou vlastní vzhled. Prohlédněte si jakoukoli jednotku ve 3D, přebarvěte ji v Blenderu, dejte
jí vlastní kartu v nabídce stavby. A naše prvenství, všechna viděná ve hře:

- **První jednotka přebarvená módem:** červený Sherman, zblízka i z dálky.
- **První jednotka namalovaná v Blenderu** a přenesená zpět do hry.
- **První karta nabídky stavby vytvořená ve Studiu,** ukázaná ve vlastní nabídce Armor Base hry.
- **První nová jednotka s vlastním modelem,** vedle těch ze hry: Tall Sherman, vedle Shermana (vytvořený při
  testování; vytváření vlastních modelů ve Studiu přijde příště).
- **První vlastní mise** dohraná do vítězství: nová Operace s vlastními cíli, jednotkami a dělostřeleckým úderem
  (vytvořená při testování).

| Dřív | Teď |
|---|---|
| Stránka jednotky ukazovala jen její hodnoty. | **3D model** na stránce jednotky: otáčejte ho, přibližte ho, uvidíte na něm barvy svého módu. |
| Vzhled jednotky byl ten ze hry. | **Přebarvit v Blenderu:** **Otevřít v Blenderu** otevře modely jednotky s jejich obrázky; malujte na model, pak **Přenést zpět** uloží vaše barvy a dá je do vašeho módu. **Viděno ve hře**, zblízka i z dálky. Blender je zdarma: když ho Studio nenajde, **Získat Blender (zdarma)** a **Vybrat Blender…** jsou hned tam. |
| Obrázek jednotky v nabídce stavby byl ten ze hry. | **Použít tento pohled jako kartu:** otáčejte a přibližujte 3D model, dokud v čárkovaném rámečku nevypadá dobře; ten pohled se stane kartou jednotky v nabídce stavby. **Viděno ve hře.** |
| Nová jednotka ukazovala stejnou kartu jako jednotka, kterou kopíruje, takže obě v nabídce vypadaly stejně. | Karta nové jednotky je její vlastní (`files/cards/<the unit's name>.png`): vytvoření její karty nikdy nezmění kartu originálu. Ve hře zatím neviděno. |
| Balík modelů jednotek, který narostl, hra zahodila a chyběl každý model v něm: pád u první továrny. | Balíky modelů se zapisují tak, jak je hra kontroluje, ať jsou jakkoli velké. **Viděno ve hře:** druhý Sherman s vlastním modelem. |
| Jednotky národa dané jiné armádě neměly v kapitolách kampaně a Operacích model: mód, který nechá objevit francouzské jednotky na mapě Holland, spadl při načítání. | Jejich modely se načtou i tam. **Viděno ve hře** (francouzské jednotky na mapě Colditz). |
| **Duplikovat mapu** vytvářelo jen mapy BITVY. | Vytvoří také novou **Operaci** nebo **Kapitolu kampaně** ze záznamu jakékoli mapy. **Viděno ve hře:** nová Operace. Raná verze: nová kapitola kampaně zatím nebyla vyzkoušena. |
| Srovnání hor na okraji mapy tam nechalo útes. | Okraj mapy sleduje terén. **Viděno ve hře** (Blitz Twin, rovný až k okraji). |
| Jednotky obcházely místa, kde stály smazané budovy města. | Kde mizí budovy, otevře se terén všem jednotkám, jako u stromů. **Viděno ve hře.** |
| Terén mapy nešlo malovat. | **Malování mapy:** malujte obrázek terénu barvou (barevné kolo, vlastní barvy mapy nebo kapátko) nebo vlastním terénem mapy zkopírovaným z jiného místa. **Vyčistit zem pod ní** (ve výchozím stavu zapnuto) odstraní trávu, plodiny a kameny pod malbou, aby byla vidět v každé výšce. Raná verze: ve hře viděno shora. |

**0.9.4:** nové mapy, raná verze. **Duplikovat mapu** vytvoří novou mapu z jakékoli mapy BITVY a mapy se otevřou za
vteřinu.

| Dřív | Teď |
|---|---|
| Změny map mohly měnit jen vlastní mapy hry. | **Duplikovat mapu** (záložka Mapy, pod názvem otevřené mapy) vytvoří **novou mapu**: úplnou kopii s vlastním názvem, uvedenou v nabídce BITVY vedle originálu, kterou pak měníte jako kteroukoli mapu. Okno řekne, co dělá a jak to funguje. **Viděno ve hře:** nová mapa se hraje na vlastním terénu a 101 nových map naráz bylo všech uvedeno a hrálo se. Raná verze: kopie jiných map než Blitz se sestaví, ale ve hře zatím nebyly vyzkoušeny, a srovnání hor na okraji mapy tam nechá útes. Prosím nahlaste, na co narazíte. |
| Mapa se pokaždé otevírala několik sekund (M03_Italie: 7,6 s). | Její data se uchovávají mezi návštěvami a spuštěními: 1,7 s podruhé. |
| „Mód“ a „Mapa“ byly dvě podobné nabídky. | **Mód jednotek** (s tankem) a **Změny map** (s mapou). |
| Strany a zóny se snadno pletly. | **Komu?** říká, že strana je ten, kdo ovládá jednotky (jedna země jich může mít několik), a popisek zóny po najetí myší říká, že je to oblast mapy, ne strana. |
| Aktualizace přicházely jen jako celé verze. | Malé opravy mohou přijít mezi verzemi (0.9.4.1), nabízené jako každá aktualizace. |

**0.9.3:** všechno, co umístíte, je vidět z dálky, nové silnice lesem vypadají jako vlastní silnice mapy, stromy, které
můžete na silnici ponechat, předměty a stromy pod svými názvy ve vašem jazyce a sestavení asi třikrát rychlejší.

| Dřív | Teď |
|---|---|
| Předměty, stromy a budovy k umístění byly vypsané pod francouzskými kódovými názvy: Caillou_10, ChampsPierres_02, Osier... | Pod názvy v jazyce Studia, ve všech deseti, s tím, jaký druh věci každá je: „Stony field 2“, „Champ de pierres 2“, „Steiniges Feld 2“. Mění se s tlačítkem jazyka. Kódový název a jeho složka jsou v popisku. |
| Kameny a většina dalších předmětů, které jste umístili, zmizely, jakmile kamera opustila blízkou vzdálenost, a objevovaly se a mizely, jak jste ji otáčeli. | Všechno, co mód umístí, se kreslí až do velké dálky, vlastní objekty mapy beze změny. **Viděno ve hře:** umístěné kameny jsou vidět v každé výšce. |
| Shora byla nová silnice lesem světlým pruhem a po první opravě zmizela ze středně dlouhé vzdálenosti. | Malovaná lesem tak, jak jsou malované vlastní silnice mapy, v každé výšce. **Viděno ve hře.** |
| Nová silnice vždy odstranila stromy ze své cesty, asi 6 m na každou stranu. | **Ponechat stromy na nových silnicích** v panelu Silnice: stromy a keře zůstanou nad silnicí a v lese je silnice vidět slabší a šedší. **Viděno ve hře.** |
| **Vyzkoušet ve hře** sestavovalo mód s novými silnicemi na M03_Italie asi 5 minut. | Asi 1½ minuty: jak vypadají silnice mapy, se změří jednou a uchová, a kopie vynechají pomalou kontrolu, kterou nepotřebují. |

**0.9.2:** opravy z testerovy mapy kampaně: mosty pro nové silnice na každé mapě, konce silnic, které se přichytí
k mostům (nebo vůbec ne), názvy, které hráč zná, jednotky pro hráče, scenérie viditelná z dálky a zóny scénáře jako
hranice na zemi.

| Dřív | Teď |
|---|---|
| Silnice přes vodu zastavila sestavení na 20 z 29 map s mosty (Itálie, Německo, Holandsko...): její most „by neměl podlahu“. | Dostane most a podlahu na každé mapě s mosty. Na těchto mapách ve hře zatím neviděno. |
| Každý bod silnice se přichytil k nejbližší silnici, na silnici i tam, kde jste umístili most. | Přichytí se jen dva konce silnice, nejdřív ke konci umístěného mostu. **Přichytit konce k silnicím a mostům** v panelu Silnice to vypne. |
| Budovy a jednotky pod kódovými názvy, jako „Descriptor_Building_VehiculeFactoryLeurre“. | Pod názvy, které jim dává hra (DECOY ARMOR BASE), s vlastním řádkem hry o tom, co každá dělá. |
| Jednotky nešlo dát hráči v kapitole kampaně: strana hráče (0) byla odmítnuta. | **Komu?** vypíše vlastní strany scénáře z jeho mise: „Hráč · USA (strana 0)“, „Počítač · Německo (strana 1)“... |
| Na M03_Italie a dalších mapách nová silnice v otevřeném terénu skrývala scenérii mapy z dálky a předměty, které jste umístili, byly vidět jen zblízka. | Pohled na mapu z dálky zůstává, jak byl, a umístěné předměty jsou vidět z dálky jako vlastní předměty mapy. Ve hře zatím neviděno. |
| Zóny scénáře byly barevné plochy vznášející se nad mapou a zakrývaly její terén i ikony. | Každá zóna je jasná čára podél své hranice na zemi s průhledným odstínem uvnitř, jako hranice ve Stellaris. **Výplň zón** nastaví vnitřek (0 %: jen hranice). |

**0.9.1:** přetáhněte cokoli na mapě, přehlednější ikony, kterým můžete nastavit velikost a které můžete skrýt, váš
jazyk od prvního spuštění a typ každé jednotky tak, jak ho jmenuje hra.

| Dřív | Teď |
|---|---|
| Startovní body, zásobovací sklady a jednotky, které se objeví, se přesouvaly jen nástrojem Přesunout, jedním kliknutím a pak dalším. | Chyťte kterýkoli z nich na mapě a přetáhněte ho, bez vybraného nástroje, tak jako se už otáčely úvodní kamery. Sklady a velitelství se při tažení dál přichytávají k silnicím. |
| Ikony na mapě byly panáčci a krabičky a každý bunkr vypadal stejně. | Ikona pro každý druh: voják, tank, nákladní auto pro zásobovací sklady, letadlo, děla, jasně označené velitelství, rozlišená Armor Base a letiště a každý bunkr vlastní (protitankový, kulometný, protiletadlový, dělostřelecký, pevnost, pozorovatelna). |
| Ikony byly shora objemné a jediný způsob, jak je skrýt, bylo skrýt celý scénář. | Ikony se zmenšují, jak se kamera vzdaluje, posuvník nastaví jejich velikost a panel Scénář ukáže nebo skryje každý druh (starty, kamery, sklady, budovy, jednotky, zóny, města). Uchová se na příště. |
| Studio začínalo s kódovými názvy a jazyk byl schovaný v Nastavení, takže hráči nevěděli, že mluví jejich jazykem. | První spuštění se zeptá: „Vyberte jazyk“, každý jazyk vlastními slovy, s označeným jazykem, na který je vaše hra nastavená ve Steamu. Pak tlačítko jazyka nahoře, vždy na očích. |
| Jednotky byly jen „Pozemní“ nebo „Letectvo“. | Pod Pozemní, Pěchota a Letectvo vlastní typy hry: Lehký, Střední a Těžký tank, Stíhač tanků, Obrněný průzkum, Stíhačka, Stíhací bombardér, Lehký, Střední a Těžký bombardér, Letecký průzkum... i na řádku každé jednotky, ve vašem jazyce. Hledání je najde („bombardér“, „průzkum“). |
| Seznam nainstalovaných aplikací ve Windows ukazoval vůbec první nainstalovanou verzi. | Ukazuje verzi, kterou máte. |

**0.9.0:** silnice vypadají správně. Silnice, kterou nakreslíte, teď vypadá jako vlastní silnice mapy, shora i těsně
u země. Dostat se sem stálo hodně času a hodně testů, víc než mosty. Vyzkoušeno ve hře na mapě Den D.

![Nová silnice zblízka na mapě Den D: asfalt s přerušovanou středovou čarou a štěrkovými krajnicemi, které přecházejí do trávy](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Dřív | Teď |
|---|---|
| Nová silnice mizela, jak se k ní kamera snášela: shora byla vidět jen její malba. | Zblízka se kreslí vlastními asfaltovými obtisky mapy, kladenými podél ní tak, jak je klade mapa, s okrajovým obtiskem na každé straně: asfalt, přerušovaná středová čára, štěrkové krajnice. |
| Malba byla jednolitá barva, světlejší a širší než silnice mapy. | Malba se měří na vlastních silnicích mapy: jejich barva, jejich krajnice a to, jak přecházejí do terénu. Každá mapa dostane vlastní. |
| Tráva, keře a stromy statku prorůstaly novou silnicí. | Rostliny a předměty mapy na cestě silnice se odstraní (asi 6 m na každou stranu). Lesy si ponechají kryt a pohyb a budovy zůstanou. |
| Byly známé jen obtisky silnic mapy Den D. | Na pouštních mapách se používají jejich vlastní obtisky, kladené stejně (ve hře zatím neviděno). |
| Velké mazání (tisíce kruhů) se sestavovalo mnoho minut. | Mnohem rychleji: prohlížejí se jen kruhy blízko každé části mapy. |

![Tři nové silnice odbočující z hlavní silnice mapy Den D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-6-done-overview.jpg)

**0.8.3:** nástroje scénáře editoru mapy z RUSE-Mod-Manageru od LittleGroove: zásobovací sklady a velitelství se
přichytí k silnicím, ikona pro každou budovu a jednotku a úvodní kamera každého hráče ukázaná, přenášená a otáčená.
Ve hře zatím nevyzkoušeno.

| Dřív | Teď |
|---|---|
| Místo pro zásobovací sklad nešlo umístit. | **Místo pro zásobovací sklad** je první v Přidat jednotku → Budovy → Peníze. |
| Startovní bod šel přesně tam, kam jste klikli, na silnici i daleko od ní. | **Přichytit k silnicím** (ve výchozím stavu zapnuto) ho dá vedle nejbližší silnice, tak daleko od ní jako vlastní mapy hry (změřil to LittleGroove). Zrušte zaškrtnutí, chcete-li umístit doprostřed pole. |
| Místa příchodu byla pár ikon s písmeny pro zemi. | Ikona podle toho, co každé je (velitelství, zásobovací sklad, továrna, pevnost, návnada, voják, tank, protitankové, dělostřelectvo, prototyp, letadlo, věž), a výsostný znak země. |
| Nebylo vidět, kde se hráčův zápas otevře. | Každý startovní bod ukazuje svou úvodní kameru: přílet (tečkovaně), kde se zastaví, na co se dívá a část mapy, kterou ukazuje obrazovka. |
| Úvodní kamera přesunutého startovního bodu zůstala na starém místě. | Kamera se přesune s ním; nový startovní bod dostane vlastní kameru. |
| Úvodní kameru nešlo změnit. | S **Přesunout** přetáhněte kameru startu kolem jeho velitelství, aby se zápas otevřel z jiné strany; **Vrátit kameru** to vrátí. |
| Startovní bod v lese byl odmítnut. | Povoleno: velitelství tam funguje a zásobovací auta jezdí lesem. Odmítnuty jsou jen voda, útesy a zablokovaný terén. |

**0.8.2:** test zastavený chybou ve vašem módu řekne kterou a opraví ji, módy a mapy zvlášť, přehlednější barvy mapy
a místa příchodu a jedna kopie hry pro celé PC.

| Dřív | Teď |
|---|---|
| Test zastavený chybou ve vašem módu pohřbil důvod v logu a odkazoval na Řešení potíží, které mód opravit neumí. | Každá chyba je vypsaná nad logem s tlačítkem, které ji opraví: místo příchodu týmu na mapě BITVY změněné na neutrální nebo vyjmuté (i všechna naráz), silnice, která se s ničím nespojuje, vyjmutá. Řešení potíží se ukáže jen u jiných selhání. |
| Zprávu dole nešlo zavřít. | Každá zpráva má × k zavření. |
| Log testu nešlo zkopírovat. | **Kopírovat zprávu** zkopíruje log a zprávu, pro hlášení chyby nebo Discord. |
| Módy a mapy sdílely jednu nabídku. | Módy a mapy mají každé svou nabídku a Exportovat dá soubor rovnou do knihovny Launcheru. |
| Každé místo příchodu na mapě vypadalo stejně. | Každé místo příchodu je ikona budovy, tanku, vojáka nebo letadla v barvě své strany, se svou zemí. |
| Barvy mapy nebyly vysvětlené. | Legenda barev pro kryt, Kam jednotky mohou a Odstranit; kryt nástroje Město má vlastní barvu; posuvník průhlednosti pro každou vrstvu. |
| Kopce a stromy prostupovaly zónami scénáře. | Zóny se vznášejí nad terénem a posuvník **Výška zón** nastaví jak vysoko. |
| Každý test si držel vlastní kopii hry. | Jedna upravená kopie pro celé PC, sdílená s Launcherem. |
| Verze nebyla vidět a Co je nového byl seznam. | Verze je vedle názvu a Co je nového otevře tabulku dřív/teď, jako je tato. |
| Málo popisků. | Popisky u hlavních ovládacích prvků, psané pro hráče, kteří s módováním začínají. |
| Novým silnicím na mapách Twilight of the Gods, Alpha, Ostfriesland a Robert chyběl model silnic mapy. | Dostanou ho také. |
| Sestavení říkalo, že nové silnice jsou „kreslené zblízka“. | Říká, že jsou vidět z dálky; zblízka zatím vidět nejsou (pořád známý problém). |

**0.8.1:** jednotky z jakéhokoli národa, nový vzhled, kratší lišta nástrojů a nástroj Odstranit.
- **Jednotky z jiného národa fungují.** Nová jednotka může jít do nabídky stavby kteréhokoli národa, ať její model
  pochází z jakékoli armády: německý Tiger nebo Ju 87 pro USA, i japonská Zero nebo Chi-Ha. Postaví se, bojuje,
  ukazuje svůj obrázek na kartě a na značce a dá se vybrat na zemi i ve vzduchu, i v zápase, kde národ, ze kterého
  pochází, nikdo nehraje (vyzkoušeno ve hře, 2026-10-02). Sestavení nechá modely toho národa načíst v každém zápase;
  zápas zabere o něco víc paměti a doby načítání.
- **Nový vzhled:** modré barvy R.U.S.E. místo černé a zlaté a nové logo: stůl štábní místnosti.
- **Lišta nástrojů editoru mapy je kratší.** Nástroje, které patří k sobě, sdílejí jednu dlaždici se záložkou pro
  každý: Terén a voda, Kryt a pohyb, Silnice a mosty, Budovy, Předměty a stromy, pak Odstranit, Scénář a Kontrola.
  Dlaždice se otevře na záložce, kterou jste použili naposledy.
- **Nástroj Odstranit:** přetáhněte přes vlastní stromy a předměty mapy (i budovy, když je vyberete) a při sestavení
  módu zmizí. Červené kruhy se ukládají v módu, co pokrývají, je zabarvené červeně, a panel spočítá, co odstraní. Kde
  mizí stromy, terén se otevře všem jednotkám a ztratí lesní kryt. Pořádné odstranění vlastních budov, silnic, keřů a
  kamenů mapy přijde příště.
- **Instalátor nabízí čistou zálohu hry** vedle zástupce na ploše a říká proč: s ní může řešení potíží vrátit cokoli,
  co změnil jiný správce módů.

**0.8.0:** editor mapy dospívá: nové štětce a panely, mosty, které jednotky opravdu přejdou, lesy, které můžete
vykácet, a sestavení, které kontroluje pravidla hry, takže to, co vytvoříte, funguje napoprvé. K tomu řešení potíží a
čistá záloha hry.
- **Nové v editoru mapy:**
  - **Štětce Otevřít** (Pohyb): opak Zablokovat. Dejte jednotkám terén, ze kterého je mapa drží pryč (všem jednotkám,
    pěchotě nebo vozidlům). Otevření vody je povolené a s varováním: jednotky tam stojí na dně řeky.
  - **Štětec Les** (Kryt): stromy a kryt jedním tahem; Zpět vezme obojí.
  - **Panel Mosty:** vlastní druhy mostů mapy a most umístěný ručně v délce a natočení, které zvolíte; přechody nových
    silnic přes vodu kreslené zlatě.
  - **Zkontrolovat mapu:** vypíše, co by se pokazilo, než začnete testovat (odříznutý terén, silnice nebo mosty, které
    jednotky nemůžou použít, nespojené konce silnic, budovy na silnicích), a kliknutí na položku ukáže kde.
  - Vysušená nebo do sucha zvednutá koryta řek sestavení otevře jednotkám.
- **Vykácejte vlastní stromy a předměty mapy:** kruhy `[[erase]]` v souboru `scenery.toml` módu (zatím psané ručně;
  nástroj Odstranit ve Studiu je na cestě). Tanky vjedou do vykáceného lesa a pěchota tam už není skrytá.
- **Umístěné objekty stojí na zemi v jakékoli velikosti.** Budova zvětšená 10× se vznášela ve vzduchu; teď sedí na
  zemi jako vlastní budovy mapy.
- **Opraveno: kryt na mapách, které nejsou čtvercové** (Den D, Frontline, Djebel, Medjez, Handshake over the Elbe a
  mapy kampaně v Tunisku, Holandsku a Ardenách). Kryt tam namalovaný nebo odstraněný (štětce Kryt, Odkrýt, Město a Les,
  `cover.toml`) přistál až kilometr od místa, kde byl nakreslen, a zobrazení mapy ho ukazovalo na stejném špatném
  místě. Obojí je teď správně: pokud jste na jedné z těchto map malovali kryt, podívejte se na něj znovu v zobrazení
  mapy. Čtvercové mapy (Blitz a většina ostatních) byly vždy správně.
- **Mosty fungují ve hře.** Silnice, kterou nakreslíte přes vodu, dostane vlastní druh mostu mapy (i u holandských
  map) a tanky, pěchota a zásobovací auta ho přejdou po mostovce, pěchota ve výšce mostovky. Konce mostu se napojí na
  silnice, které už jednotky používají, a drží se stranou od budov mapy; most, který nejde napojit, zůstane uzavřený a
  poznámka sestavení řekne, na co silnice narazila a kde.
- **Sestavení kontroluje pravidla hry.** Každý soubor, který mód mění, byl porovnán s tím, co s ním dělá hra, a mód,
  který by se ve hře rozbil, se odmítne s poznámkou proč, dřív než se cokoli zapíše:
  - silnice: jednotky teď sledují nové silnice, nejen zásobovací auta, a nová silnice, která se nespojuje s žádnou
    jinou, se odmítne (silniční síť musí zůstat v jednom kuse);
  - umístěné budovy a bloky: jednotky jimi už neprojedou; nové budovy, mosty a stromy jsou vidět na každou
    vzdálenost;
  - terén: nová voda je pro jednotky uzavřená, mapa AI sleduje vaše lesy, bloky, mosty a vodu a tah, který nemůže
    změnit terén (nebo dosáhne na podlahu mostu), to řekne;
  - jednotky: špatná salva, ID, národ nebo seznam nabídky se odmítne, flagy jednotek se kontrolují a každý flag je
    vysvětlený ve výběru flagů (flagy 62 a 63, které shodí hru na jednotce, která není nákladní auto, jsou chyba);
    jednotka daná do továrny jiného národa se zatím odmítne (při stavbě shazovala hru; zprovoznit ji je další krok);
  - scénář: místa příchodu jsou ve výchozím stavu neutrální, místo příchodu jednotky, jejíž modely zápas nemusí
    načíst, se odmítne (shazovalo hru na začátku), start, kam nemůžou vozidla, se odmítne, přesunutý start si vezme
    svou kameru s sebou a místa hráčů se počítají po týmech.
- **Zpráva sestavení** ukazuje každé varování (některá se ztrácela) a nové sestavení nejdřív odstraní starou
  testovací kopii, aby se stará kopie nedala omylem spustit.
- **Čtvercový kryt:** `square = true` u malby v `cover.toml` nebo u tahu Kryt či Odkrýt v `terrain.toml` namaluje
  čtverec podél os mapy (zatím psané ručně; zobrazení mapy ho kreslí jako čtverec).
- **Řešení potíží** (vedle *Vyzkoušet ve hře* a v Nastavení > Nápověda): jedním během zkontroluje, co může zastavit
  test (nalezená hra, Steam, hra ponechaná běžet z upravené kopie, disk a jeho volné místo, zbylé kopie, soubory jen
  pro čtení, zda aplikace může zapisovat tam, kam jdou kopie), s tlačítkem pro každou opravu, kterou umí udělat, a
  zprávou k vložení do hlášení chyby, bez vašeho uživatelského jména ve Windows.
- **Čistá záloha hry** (Nastavení): uchovejte čistou kopii souborů vaší hry, porovnejte je s ní a vraťte cokoli, co
  změnil jiný správce módů nebo ruční úprava. Soubory, které nepatří hře, se odsunou stranou, nikdy se nesmažou. Nebo
  nechte hru opravit Steamem (*Ověřit ve Steamu*). Je to jediné místo, kde Studio kdy zapisuje do složky vaší hry, a
  jen když o to požádáte.
- **Sdílejte svůj mód:** vytvořili jste mód? Po exportu Studio ukáže jeho velikost a SHA-256 a jak ho přidat do
  seznamu módů na GitHubu a stát se přispěvatelem.
- **Známý problém: nové silnice se zatím nekreslí zblízka.** Jsou namalované na zemi a vidět z dálky a jednotky je
  používají, ale s kamerou u země nová silnice zmizí. Pracujeme na tom.

**0.7.6:** druhé Vyzkoušet ve hře funguje a mosty, ke kterým se jednotky vždy dostanou.
- **Opraveno:** každé druhé *Vyzkoušet ve hře* mohlo selhat s „An old modded copy ... can't be removed ... (Access is
  denied)“. Kopie, kterou Windows nechce smazat (soubor, který starší verze propojila s nahrazeným souborem hry,
  program, který ho ještě drží), už nezastaví test: odsune se stranou do `RUSE-Instances\.trash` a odstraní se, jakmile
  ji nic nedrží. Pokud R.U.S.E. ještě běží z testovací kopie, dozvíte se to i s názvem programu. Dvojí stisknutí
  *Vyzkoušet ve hře* spustí jeden test, ne dva.
- **Opraveno:** nový most silnice mohl shodit hru, když jednotky dostaly rozkaz na něj vjet: jeho mostovka
  nedosahovala na žádný terén, který jednotky používají. Každý konec mostu se teď napojí na terén podél silnice (až
  62 m nájezdu); most, který nejde napojit, zůstane pro jednotky uzavřený, s poznámkou, a sestavení nikdy nezapíše
  terén, kam se jednotky nedostanou.

**0.7.4:** Vyzkoušet ve hře funguje, když jsou soubory vaší hry označené jen pro čtení.
- **Opraveno:** *Vyzkoušet ve hře* pokaždé selhalo s „[WinError 5] Access is denied“, když byly soubory R.U.S.E.
  označené jen pro čtení (instalace z disku, obnovená záloha): testovací kopie si označení ponechala, takže kopii
  ponechanou napůl sestavenou nešlo nikdy odstranit. Testovací kopie si teď označení nikdy neponechá a zbytek ze starší
  verze se odstraní sám (soubory vaší hry skončí přesně tak, jak byly). Pokud hra z testovací kopie ještě běží,
  dozvíte se, že ji máte zavřít, místo chyby Windows.
- **Silnice ukazuje svou délku**, zatímco ji kreslíte, vedle ukazatele (jako v Cities: Skylines); nástroje Silnice
  ukazují součet vašich nových silnic.
- **Nové silnice jsou namalované na zemi** vlastní barvou silnic mapy (ověřeno ve hře) a **silnice přes vodu dostane
  most**: vlastní druh mapy, jeden kus natažený od břehu ke břehu jako vlastní mosty hry, aby jednotky mohly přejít.
  Silnice přes jeden z vlastních mostů mapy dostane nový most na jeho místo. (Mosty jsou nové: ve hře zatím
  nezkontrolované.)

**0.7.3:** uspořádejte si zobrazení mapy po svém. Panel mapy (vlevo nahoře) a nástroje (dole) se přesunou kamkoli za
svůj úchyt (⠿) a sbalí se šipkou vedle něj: panel mapy až na svůj nadpis, nástroje až na svou lištu. Dvojklikem na
úchyt vrátíte ten panel na místo. Vaše rozložení se uchová.

**0.7.2:** silnice a přehlednější testy.
- **Kreslete silnice**, ve stylu Cities: Skylines (druh Silnice na liště): **Rovná**, **Oblouk** a **Volná**. Konec
  blízko silnice se k ní přichytí a napojí se na ni. Nové silnice se kreslí jako modré pásky a **zásobovací trasy je
  používají** (ověřeno ve hře). Na zemi zatím namalované nejsou.
- Pole **Silnice** ukazuje vlastní silnice mapy zlatě.
- Vlastní slova hry: scénář je pojmenovaný podle tlačítka hlavní nabídky, které ho hraje (**Bitvy**, Operace, Kampaň,
  přečtené z textů vaší hry ve vašem jazyce), a zlatý řádek pod nabídkou scénáře říká, kde se hraje, např. *Ve hře:
  Bitvy › Den D (6 hráčů)*.
- **Vyzkoušet ve hře** řekne, kde sestavilo, a přesně co otevřít, abyste uviděli své změny (např. *BITVY > Den D*).
- Prostřední tlačítko myši otáčí pohled i v režimu rozhlížení (dřív tam přibližovalo).

**0.7.1:** několik jednotek naráz, kontrola módu a nápověda po ruce.
- **Přidat jednotku** umístí 1, 2, 4, 6, 8 nebo 10 naráz, v **řadě, koloně, klínu, obdélníku nebo kruhu** čelem
  k horní straně obrazovky, s posuvníkem rozestupu a kroužky, které ukazují, kde každá bude stát.
- **Kontrola módu**: každý soubor vašeho módu se přečte tak, jak ho čte sestavení hry, když mód vyberete a před
  **Vyzkoušet ve hře**. Červená lišta jmenuje každý problém; poškozený soubor mapy jde **odložit** (přejmenovat, nikdy
  se neztratí) a složku mapy pojmenovanou podle titulu mapy (maps/Blitz) jde jedním kliknutím **přejmenovat** na název
  jejího balíku (maps/SuperCrossRoads4).
- Opraveno: tahy **Voda** se ukládaly bez své hladiny, takže sestavení hry mód odmítlo. Každý soubor, který Studio
  zapíše, se teď před uložením přečte zpět.
- Seznam map se **sbalí** («) pro víc místa.
- **Nastavení > Nápověda a komunita**: wiki (nová příručka), Discussions a **Nahlásit problém**, které otevře hlášení
  chyby s vyplněnou verzí. Chyba dole má vlastní odkaz **Nahlásit**. Aplikace nic neodesílá: hlášení si přečtete a
  zveřejníte sami.

**0.7.0:** nový vzhled a nástroje pohybu. Nástroje mapy se přesunuly na lištu podél spodního okraje, jako v Cities:
Skylines, ve vlastním stylu HUD R.U.S.E.: vyberte druh (Terén, Voda, Kryt, Pohyb, Budovy, Objekty, Stromy, Scénář) a
jeho nástroje se otevřou nad ním; klikněte na něj znovu nebo stiskněte Esc a jen se rozhlížejte. Výběry scénáře jsou
teď dlaždice, ne rozbalovací seznamy. **Pohyb:** pole **Kam jednotky mohou** to ukáže na mapě (červená: žádná jednotka;
žlutá: jen pěchota) a tři nové štětce terén uzavřou: **Zablokovat** (každé jednotce), **Zablokovat pěchotě** a
**Zablokovat vozidlům**. Budovy, které umístíte, zastaví jednotky (pole **Pevné**, ve výchozím stavu zapnuto). Ověřeno
ve hře: jednotky naplánují cestu kolem zablokované jámy a projdou mezi umístěnými věžemi.

**0.6.9:** budovy, předměty a stromy, které umístíte, jsou teď ve hře vidět při každém přiblížení (ověřeno na mapě
Blitz, až do 8× jejich velikosti): každá skupina jde do nového bloku obaleného kolem nejbližší vesnice nebo statku,
které mapa kreslí z dálky. Zkontrolováno na všech 32 mapách: nic jiného se nepohne. Jednotky umístěnými budovami pořád
procházejí; udělat je pevnými je další krok.

**0.6.8:** vytvořte města a lesy, ve kterých se jednotky mohou schovat. Zobrazení mapy ukazuje, kde se jednotky
schovávají (pole **Kryt**, zeleně), a tři nové štětce to malují: **Kryt**, **Odkrýt** a **Město** (klikněte na město:
kryt se položí kolem každé jeho budovy, i umístěných). Ověřeno ve hře: pěchota na namalovaném krytu je skrytá.

**0.6.7:** umístěné objekty jdou až do 10× své velikosti (posuvník Velikost nástroje Umístit; [ a ] krokují po 0,1 až
do 3×, pak po 0,5).

**0.6.6:** munice je řazená i podle typu: průbojné granáty, tříštivo-trhavé granáty, protiletadlové, kulomety, pěchotní
zbraně, pěchotní protitankové zbraně, pumy a rakety (seznam Typ nad municí). Módy také mohou na mapě malovat kryt (kde
se jednotky schovávají, jako v lese) a zablokovaný terén (`maps/<map>/cover.toml`); nástroj Studia na to přijde
příště.

**0.6.5:** scénáře se dají upravovat na mapě. **Přesunout** startovní bod nebo místo příchodu (klikněte na něj, pak
tam, kam má jít; Vrátit to vezme zpět). **Přidat jednotku** nechá objevit jednotku nebo budovu, když scénář začne:
vyberte její druh (budovy, pozemní, pěchota, letectvo), pak její typ (u budov: velitelství, peníze, továrny, pevnosti a
obrana, falešné návnady; u jednotek: továrna, která je staví), pak jednotku (podle národa) a její stranu. Uloženo
v `maps/<map>/scenario.toml` módu. Seznam jednotek má stejný filtr Typ.

**0.6.4:** seznam map má filtr typu: všechny mapy, nebo jen mapy pro šarvátky, Operace, kampaň, demo nebo testovací
mapy (z vlastních nabídek hry; mapa může patřit k několika). Pamatuje si to.

**0.6.3:** záložka **Nastavení** (vedle Jednotky a Mapy): jazyk, klávesy zobrazení mapy, složka hry a aktualizace na
jednom místě, připravené na další.

**0.6.2:** hledání aktualizací je spolehlivější: když GitHub odmítne jedinou kontrolu při spuštění (povoluje 60 za
hodinu na internetovou adresu, sdílených vším, co ji používá), Studio místo toho přečte seznam vydání na GitHubu. Módy
také mohou ve scénáři nechat objevit jednotky a budovy (`[[spawn]]` v `maps/<map>/scenario.toml`).

**0.6.1:**

- **Váš jazyk a klávesy se zachovají** přes restarty, aktualizace a přeinstalace (ztrácely se při každém spuštění).
- **Scénáře seskupené tak, jak je používá hra:** Šarvátka, Operace, Kampaň, Demo, Test a ty, které nenačítá žádná
  nabídka, každý pojmenovaný tak, jak ho pojmenovávají nabídky hry („10. UTAH BEACH“, „Anzio“).
- **Módy mohou přesouvat startovní body a místa příchodu** (`maps/<map>/scenario.toml`); zkontrolováno ve hře:
  velitelství začne tam, kam ho mód dá.

**Nové v 0.6:**

- **Terén, který funguje ve hře:** terén, který zvýšíte, snížíte nebo zarovnáte, teď přijímá rozkazy k pohybu, kamera
  zůstává nad ním a stromy a budovy na něm stojí. Recept od DomesticNukes a jeho Claude: herní terén se pohne první,
  kreslený terén ho následuje a skryté výškové limity hry se rozšíří. Zkontrolováno na všech 32 mapách.
- **Scénáře na mapě:** řádek „Scénář“ vybere jeden ze scénářů mapy (šarvátka, výzvy, kapitoly kampaně) a ukáže jeho
  zóny, startovní body (sloupy v barvě každé aliance), místa příchodu (bílé kosočtverce) a názvy měst. Najeďte na
  jeden a uvidíte, co to je. První krok k vytváření map.

**0.5.2:**

- **Štětce Voda a Vysušit** (Voda na klávese 0): zaplavte terén pod hladinou do jezera, nebo vysušte jezero či řeku.
  Od DomesticNukes a jeho Claude, zkontrolováno ve hře na mapě Blitz.
- **Vlastní klávesy:** „Změnit klávesy…“ pod řádkem nápovědy zobrazení mapy: klikněte na akci, stiskněte klávesu.
  Výchozí je vrátí.

**0.5.1:**

- **Zbraň si ponechá vlastní záblesk a zvuk:** když zbraň střílí munici jiné jednotky, teď si od té jednotky vezme i
  záblesk z hlavně a zvuk výstřelu (dělo Shermana na střelci střílí jako Sherman). Zbraň ukazuje, který přehrává.
- **Štětec Srovnat** (klávesa 7): maluje terén rovně ve výšce, kde začnete táhnout.
- **WASD se pohybuje s kamerou**: W je na obrazovce vždy dopředu, ať je pohled otočený jakkoli.
- Index hry se znovu sestaví jednou, při prvním otevření 0.5.1 (asi půl minuty).

**Nové v 0.5:**

- **Nové jednotky:** zkopírujte jednotku z její stránky, pojmenujte ji, dejte jí cenu a dejte ji do nabídky stavby.
- **Munice a flagy:** druh Munice s veškerou municí. Zbraň může střílet munici jiné zbraně (ukazuje se národ, ze
  kterého pochází) nebo její vlastní kopii. Seznamy flagů (co jednotka je a dělá) se dají upravovat, jako v editoru
  jednotek RUSE Mod Manageru.
- **Mapy:** každá mapa ukazuje svůj název ve hře, ve vašem jazyce, vedle svého kódového názvu. Budovy, předměty a
  stromy se kreslí **skutečnými 3D modely a texturami hry**, díky DomesticNukes a jeho Claude.
- **Štětce terénu:** zvyšujte, snižujte, vyhlazujte terén a dělejte z něj rampy, uloženo v módu. **Začít znovu**
  vyčistí mapu.
- **Nástroj Umístit:** jedno kliknutí umístí budovu, předmět nebo strom. Namalujte oblast, nebo klikněte dvakrát pro
  řadu (živý plot, ulice). Zpět vezme zpět celou oblast nebo řadu. Scenérie je zatím jen na pohled: jednotky jí
  projíždějí.
- **Klávesy:** WASD / šipky posouvají pohled, Q/E ho otáčejí, R/F přibližují. Najeďte na jakékoli tlačítko a uvidíte
  popisek.
- **Exportovat .rusemod:** jeden soubor, který Launcher nainstaluje.
- **Aktualizuje se samo:** od této verze lišta oznámí, když vyjde novější Studio; **Aktualizovat** ho nainstaluje.

Je nové a mimo vývojářovo PC bylo sotva vyzkoušené, tak prosím nahlaste cokoli divného na GitHub Issues.

![Mapy v RUSE Studio: Centre of Gravity ve 3D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-maps.jpg)

![RUSE Studio v režimu náhledu, s ukázkovými jednotkami](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-unit.jpg)
