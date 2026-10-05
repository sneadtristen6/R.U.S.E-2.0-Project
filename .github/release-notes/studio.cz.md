**RUSE Studio, ukázková verze pro moddery.** Procházejte jednotky hry v kterémkoli z jejích deseti jazyků, měňte je ve
vlastním módu a vyzkoušejte ho ve hře. Vaše instalace Steamu se nikdy nemění.

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
