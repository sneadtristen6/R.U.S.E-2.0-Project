**RUSE Launcher 0.4, pro hráče.** Najde R.U.S.E. přes Steam a **Hrát** sestaví upravenou kopii hry s vašimi módy a
spustí ji. Vaše instalace Steamu se nikdy nemění.

**0.4.8.9:** módy se instalují na více PC, a bezpečnější čtení obrázků.

- **Opraveno, nahlášeno hráčem:** na některých PC se nenainstaloval žádný mód: „tento PC nedůvěřuje bezpečnostnímu certifikátu webu (unable to get issuer certificate)“. Windows na těchto PC nemá certifikát, kterým se ověřuje stahování z GitHubu, a nedokáže ho získat. Launcher teď zkouší i seznam certifikátů Firefoxu, který nese s sebou. Do té doby se mód stažený v prohlížeči ze seznamu módů nainstaluje přes **Přidat soubor módu…**.
- **Bezpečnější obrázky:** knihovna, kterou Launcher čte obrázky (Pillow), je teď ve verzi 13.0.0, s opravami proti schválně upraveným souborům obrázků, které mohly aplikaci shodit, vyčerpat její paměť nebo hůř.

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
