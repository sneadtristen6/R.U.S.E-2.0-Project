# Když se něco pokazí

Najděte, co vidíte, a postupujte podle opravy.

## Nejdřív zkuste Řešení potíží

**Řešení potíží** najednou zkontroluje, co může zastavit test nebo **Hrát**: zda je hra nalezena, zda běží Steam, zda
nezůstala běžet R.U.S.E. z kopie s mody, disk a jeho volné místo, zbylé kopie, soubory jen pro čtení a zda aplikace
může zapisovat tam, kam jdou kopie. Každý problém, který umí opravit, má tlačítko; u ostatních je napsáno, co dělat.

- V RUSE Studiu: vedle **Vyzkoušet ve hře** a v **Nastavení > Nápověda**. V RUSE Launcheru: ve spodní liště a v každé
  zprávě o problému (Studio 0.8.0, Launcher 0.3.0).
- **Kopírovat zprávu** dá text, který vložíte do [[hlášení chyby|Nahlášení-chyby]] (vaše uživatelské jméno ve Windows je
  vynecháno).

## Samotná hra se zdá změněná (jiným správcem modů nebo ruční úpravou)

**Nastavení > Čistá záloha hry** uchovává čistou kopii souborů hry, kontroluje je proti ní a vrací, co se změnilo.
Soubory, které nepatří hře, se přesunou stranou, nikdy se nesmažou. Nebo **Ověřit ve Steamu** nechá Steam hru opravit.
To je jediné místo, kde aplikace zapisují do složky vaší hry, a jen když o to požádáte.

## Červený pruh pod záhlavím Studia

To je **kontrola modu**. Studio čte každý soubor vašeho modu tak, jak ho bude číst sestavení hry, když mod vyberete,
a znovu před **Vyzkoušet ve hře**. Každý problém je popsaný srozumitelně (co je špatně, na které mapě, co dělat),
s tlačítkem, které ho opraví, kde to jde: doplní chybějící hodnotu, vyjme tu jednu položku nebo nastavení, které jsou
špatně, nebo soubor odloží. Soubor, jak byl, se uchová vedle něj. **Podrobnosti** ukáže vlastní slova sestavení, což se
hodí, když žádáte o pomoc.

- **Odložit** (vedle poškozeného souboru mapy) ho přejmenuje na `<name>.broken.toml` vedle originálu: nic se neztratí,
  mod funguje bez něj a ta mapa začne načisto.
- Problém v `mod.toml` nebo v úpravách jednotek nemá Odložit: otevřete soubor a opravte řádek, který pruh jmenuje, nebo
  se zeptejte v [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

> [!NOTE]
> Známý případ: RUSE Studio 0.7.0 a starší ukládalo tahy **Voda** bez jejich hladiny vody („the water brush
> needs level“). 0.7.1 to opravuje; **Odložit** starý soubor odstraní.

## Aplikace se otevírá dlouho

- **První spuštění po instalaci** se zaškrtnutým „Uchovat čistou kopii souborů hry“ tu kopii vytváří (celou složku
  hry, asi 5,3 GB): Nastavení ukazuje, jak daleko je, a aplikaci mezitím můžete používat.
- **Index hry v RUSE Studiu** se sestavuje jednou pro každou verzi hry a znovu, když ho změní aktualizace Studia (asi
  minutu; Studio se nejdřív zeptá). Mezitím lze používat záložku Mapy a Nastavení a řádek dole řekne, kdy je hotový.
- Cokoli jiného: otevřete **Řešení potíží** a **Kopírovat zprávu**. Zpráva uvádí, jak dlouho trval každý krok
  posledních spuštění aplikace, v sekundách: vložte ji do [[hlášení chyby|Nahlášení-chyby]]. Stejné řádky se ukládají
  do `%LOCALAPPDATA%\RUSE Mod Platform\logs\studio-start.log` (ty Launcheru: `launcher-start.log`).

## „Systém Windows ochránil váš počítač“

Aplikace jsou pro kontrolu pověsti ve Windows nové. Klikněte na **Další informace**, pak na **Přesto spustit**.

## „certificate verify failed: unable to get local issuer certificate“ (nebo „unable to get issuer certificate“)

Nestáhne se žádný mod, nebo se nestáhne aktualizace. Windows ještě nezískaly certifikát, proti kterému se GitHub
ověřuje; od Launcheru 0.4.8.4 a Studia 0.9.8.4 o něj aplikace Windows požádají a zkusí to znovu. Od Launcheru 0.4.8.9
a Studia 0.9.8.9 to zkoušejí také se seznamem certifikátů, který používá Firefox a který nesou s sebou, pro PC, jehož
Windows ho získat nedokážou (aktualizace certifikátů vypnuté nebo zablokované: „unable to get issuer certificate“,
nebo „the PC doesn't trust the site's security certificate“). Se starší aplikací se nestáhne ani aktualizace: stáhněte
instalátor ve svém prohlížeči z [vydání](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases) a spusťte ho
(nainstaluje se přes starý, stejně jako aktualizace). Mod lze vždy stáhnout v prohlížeči z
[vydání](https://github.com/sneadtristen6/Ruse-Mods/releases) seznamu modů a přidat v Launcheru přes **Přidat soubor módu…**. Pokud to
nová aplikace pořád hlásí: může to způsobovat antivirus, který kontroluje zabezpečená (HTTPS) spojení, školní nebo
pracovní síť nebo špatné datum v PC; napište nám do [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## „[WinError 5] Access is denied“ při testování nebo hraní

Windows odmítly odstranit kopii hry, kterou aplikace udělala (v `RUSE-Instances`). Také: „An old modded copy at
`...\RUSE-Instances\<name>.old` can't be removed“, při každém druhém **Vyzkoušet ve hře** nebo **Hrát**.

- **Nejdřív aktualizujte** (aplikace to nabídnou při otevření): od RUSE Studia 0.7.6 a Launcheru 0.2.11 kopie, kterou
  Windows nechtějí smazat, nikdy nezastaví test: přesune se do `RUSE-Instances\.trash` a odstraní se tam, jakmile ji
  nic nedrží.
- **Běží R.U.S.E. ještě z dřívějšího testu?** Aplikace to řekne, s názvem programu: zavřete hru (hledejte `RUSE.exe`
  na kartě Podrobnosti ve Správci úloh), pak to zkuste znovu. **Řešení potíží** najde hru, která pořád běží z kopie,
  a zbylé kopie, a odstraní je za vás.
- **Se starší verzí:** smažte složku, kterou zpráva jmenuje (`...\RUSE-Instances\<name>.partial` nebo `.old`;
  Windows se zeptají na soubory jen pro čtení: odpovězte ano; zmizí jen kopie, nikdy hra), pak to zkuste znovu. Pokud
  Windows odmítnou, nejdřív Windows restartujte.
- Pořád tam? [[Nahlaste to|Nahlášení-chyby]] s celou zprávou.

## Aplikace nemůže najít R.U.S.E.

**Nastavení > Složka hry > Vybrat složku…** a vyberte složku, ve které je `RUSE.exe` (na Steamu:
`steamapps\common\R.U.S.E`).

## „Tuto kopii R.U.S.E. se nepodařilo ověřit.“

R.U.S.E. 2.0 funguje jen s kopií hry, kterou vlastníte. Dokud složka hry není ověřená, **Hrát** a **Vyzkoušet ve
hře** zůstanou vypnuté a toto okno řekne proč: Steam nemá záznam o R.U.S.E. nainstalovaném v té složce; vlastní soubor
Steamu v ní (`steam_api64.dll`) chybí, je změněný nebo není od Valve; nebo složka obsahuje soubory, které nechají hru
běžet bez Steamu (okno je jmenuje).

- **Vlastníte ji na Steamu:** klikněte na **Zkontrolovat mé soubory ve Steamu** (Steam vrátí kterékoli své soubory,
  které chybí nebo jsou změněné), odstraňte soubory, které okno jmenuje, a pak klikněte na **Zkontrolovat znovu**.
  Složka hry, kterou jste vybrali ručně, musí být ta, do které hru nainstaloval Steam.
- **Vlastníte ji jinak** (krabicová kopie z doby, kdy R.U.S.E. ještě nebyl na Steamu), **nebo si myslíte, že se
  kontrola spletla:** okno ukazuje **Váš kód** (vytvořený z tohoto PC a složky hry). Klikněte na **Kopírovat**, pak na
  **Otevřít tiket na Discordu** nebo **Otevřít tiket na GitHubu** a kód tam vložte. Pošleme vám odemykací kód: vložte
  ho pod **Odemykací kód** a klikněte na **Odemknout**. Tím se ta kopie ověří na tom PC.

Kontrola je stejná na Windows, Linuxu i Steam Decku. Tento projekt nikdy nikomu nepomáhá hrát R.U.S.E., aniž by ho
vlastnil: žádné rozdávání souborů hry, žádné spouštění bez Steamu.

## „Ve starším formátu modu“ nebo „uloženo novějším RUSE Studiem“

- **Starší formát modu:** mod byl vytvořen starším Studiem. **Aktualizovat tento mod** přepíše jeho soubory tak, jak je
  čte toto Studio, a zachová, co znamenají; zip celého modu se předtím uloží do složky Studia `mod-backups`.
- **Novější RUSE Studio:** než ten mod změníte, aktualizujte Studio: starší by mohlo zahodit, co nezná.

## Zavření Studia se ptá „Zavřít RUSE Studio?“

Ještě není všechno uložené a okno řekne co (pole s napsaným, ale nepotvrzeným textem, změna, která se ještě ukládá,
Vyzkoušet ve hře, které se ještě sestavuje...). **Ne** nechá Studio otevřené; **Ano** ho zavře a tohle se ztratí.

## Hra se spustí, ale bez mých změn

1. Spustili jste ji přes **Hrát** (launcher) nebo **Vyzkoušet ve hře** (Studio)? Ze Steamu se hra spustí bez modů.
2. Změny mapy se ukážou jen na té mapě: v hlavní nabídce klikněte na **BITVY** a vyberte ji (zpráva Studia po
   Vyzkoušet ve hře říká, které tlačítko a mapu).
3. Je mod v sadě a nemění stejnou věc mod, který je v pořadí níž?

## Hra spadne

Zapište si, co jste dělali těsně předtím (jaká mapa, jaký rozkaz, co bylo na obrazovce), udělejte snímek obrazovky
a [[nahlaste to|Nahlášení-chyby]]. Díky hlášením pádů na upravených mapách jsou nástroje pro mapy spolehlivé.

## Něco jiného

[[Položení otázky|Položení-otázky]].

---

[[Polní příručka|Polní-příručka]] · [[English|When-Something-Goes-Wrong]]
