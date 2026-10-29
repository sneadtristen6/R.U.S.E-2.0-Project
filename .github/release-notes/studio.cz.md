**RUSE Studio, ukázková verze pro moddery.** Procházejte jednotky hry v kterémkoli z jejích deseti jazyků, měňte je ve
vlastním módu a vyzkoušejte ho ve hře. Vaše instalace Steamu se nikdy nemění.

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
