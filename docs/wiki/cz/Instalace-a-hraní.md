# Instalace a hraní

> **Pro:** hráče · **Potřebujete:** R.U.S.E. na Steamu, nainstalovanou · **Trvá:** 5 minut

**Ve zkratce:** stáhněte **RUSE-Launcher-Setup** ze stránky vydání, spusťte ho, otevřete **RUSE Launcher**, klikněte na
**Podporované módy**, zaškrtněte mod a stiskněte **Nainstalovat**, vložte ho do sady módů a pak **Hrát**. Každý krok
níže přesně říká, kam kliknout.

Ke hraní modů potřebujete jen **RUSE Launcher**. **RUSE Studio** je na jejich tvorbu (viz konec této stránky).

## Krok 1: Stáhněte Launcher

1. Otevřete stránku [vydání launcheru](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher).
2. Nejnovější je nahoře, označené **Latest** (například *RUSE Launcher 0.4.8.9*).
3. Sjeďte pod ním dolů k **Assets** a klikněte na **RUSE-Launcher-Setup-0.4.8.9.exe** (číslo verze se mění; vezměte
   `.exe`, který začíná na `RUSE-Launcher-Setup`). Prohlížeč ho stáhne.

Ostatní soubory tam (`RUSE-Launcher-notes.json`, *Source code*) nepotřebujete.

## Krok 2: Nainstalujte ho

1. Otevřete stažený soubor (obvykle ve složce **Stažené soubory**).
2. **„Systém Windows ochránil váš počítač“?** Klikněte na **Další informace**, pak na **Přesto spustit**. Aplikace je
   pro kontrolu pověsti ve Windows nová; její kód je veřejný tady na GitHubu.
3. Proklikejte se instalátorem. Nechte zaškrtnuté **Uchovat čistou kopii souborů hry**: aplikace nikdy nemění složku
   vaší hry, ale jiní správci modů a ruční úpravy ano, a každá hra s mody se sestavuje z těchto souborů. Kopie se
   vytvoří při prvním spuštění aplikace (několik minut, zhruba tolik místa na disku jako hra).
4. Spusťte **RUSE Launcher** (nabídka Start nebo zástupce na ploše). Při prvním spuštění **Vyberte jazyk**: kterýkoli
   z jedenácti, deset jazyků hry a perštinu (فارسی); tlačítko jazyka nahoře ho kdykoli změní. R.U.S.E. najde sám přes
   Steam. Pokud řekne, že nemůže: **Nastavení > Složka hry > Vybrat složku…** a vyberte složku, ve které je `RUSE.exe`
   (obvykle `C:\Program Files (x86)\Steam\steamapps\common\R.U.S.E`).

> [!IMPORTANT]
> **R.U.S.E. 2.0 funguje jen s kopií hry, kterou vlastníte na Steamu.** Než se spustí hra s mody, Launcher a Studio
> zkontrolují složku hry: záznam Steamu o R.U.S.E. nainstalovaném právě tam, vlastní soubor Steamu v ní a žádné
> soubory, které nechají hru běžet bez Steamu. Pokud to nedokážou ověřit, okno řekne proč a co dělat (**Hrát** zůstane
> vypnuté, dokud se to nevyřeší): viz [[Když se něco pokazí|Když-se-něco-pokazí]].

## Krok 3: Získejte mody

**Z našeho seznamu (nejsnazší):** klikněte na **Podporované módy**, zaškrtněte mody, které chcete, a stiskněte
**Nainstalovat**. Každý soubor se stáhne a ověří proti seznamu, než přijde do vaší knihovny.

**Ze souboru, který někdo sdílel:** klikněte na **Přidat soubor módu…** a vyberte soubor, nebo ho přetáhněte do okna.
Launcher bere:
- `.rusemod`: vytvořený v RUSE Studiu;
- `.rmod`: vytvořený pro RUSE Mod Manager od LittleGroove;
- `.zip`: zabalenou složku modu.

Nejdřív soubor zkontroluje: soubor, který není mod nebo který obsahuje program, odmítne a uvede důvod.

**Starý mod, který přichází jako vlastní soubory hry** (balíky `.dat`, které jste měli zkopírovat do složky hry):
klikněte na **Převést starý mod…**, vyberte jeho složku, dejte mu název a klikněte na **Převést a přidat do knihovny**.
Složky vaší hry se to nedotkne.

## Krok 4: Vyberte, co hrát

1. **Sada módů** jsou mody, které hrajete spolu, v daném pořadí. Klikněte na **Nová sada módů…**, přidejte mody
   a seřaďte je (když dva mody mění stejnou věc, vyhraje ten níž).
2. Pokud dva mody nejdou hrát spolu, Launcher řekne které a proč, ještě než začnete hrát.

## Krok 5: Hrajte

Vyberte svou sadu módů a stiskněte **Hrát**. Poprvé Launcher sestaví kopii hry s mody (asi minutu); potom už jen to,
co se změnilo. Pak se spustí R.U.S.E. s vašimi mody.

Vaše hra s mody říká **R.U.S.E. 2.0 ve zlaté**: otevře se bitevní scénou a její hlavní nabídka, nabídky a načítací
obrazovky nesou zlatý název. Udělá se na vašem PC ze souborů vaší vlastní hry napoprvé (několik minut, jednou).
Chcete-li ponechat původní název hry, zrušte v **Nastavení** zaškrtnutí **Název hry**.

> [!NOTE]
> Spuštění R.U.S.E. ze **Steamu** spustí hru **bez** modů, jako vždy. Chcete-li hrát s mody, spusťte ji tlačítkem
> **Hrát** v Launcheru. Vaše instalace ze Steamu se nikdy nemění.

## Aktualizace

Launcher při každém spuštění hledá novou verzi: když ji nabídne, klikněte na **Aktualizovat**. Pokud aktualizace
selže s „certificate verify failed“, stáhněte v prohlížeči nejnovější `RUSE-Launcher-Setup` z kroku 1 a spusťte ho:
nainstaluje se přes starou verzi a vaše mody zachová.

**Povinné aktualizace:** aktualizaci označenou jako povinnou (důležitou, například bezpečnostní opravu) nelze přeskočit. Launcher zakryje okno a aktualizace se nainstaluje sama, pak se Launcher znovu otevře; dokud není nainstalovaná, **Hrát** zůstává vypnuté. Bez internetu to okno řekne: připojte se a stiskněte **Zkusit znovu**. Studio dělá totéž s **Vyzkoušet ve hře**.

## Problémy?

| Co vidíte | Co dělat |
|---|---|
| „Systém Windows ochránil váš počítač“ | **Další informace**, pak **Přesto spustit** (krok 2). |
| Launcher nemůže najít R.U.S.E. | **Nastavení > Složka hry > Vybrat složku…**, složka s `RUSE.exe`. |
| „certificate verify failed: unable to get local issuer certificate“ | Pořiďte si Launcher 0.4.8.4 nebo novější (krok 1); viz [[Když se něco pokazí|Když-se-něco-pokazí]]. |
| „unable to get issuer certificate“ nebo „this PC doesn't trust the site's security certificate“ při instalaci modů | Pořiďte si Launcher 0.4.8.9 nebo novější (krok 1), nebo stáhněte mod v prohlížeči a použijte **Přidat soubor módu…**; viz [[Když se něco pokazí|Když-se-něco-pokazí]]. |
| Hra se spustí bez mých modů | Spusťte ji tlačítkem **Hrát** v Launcheru, ne ze Steamu. |
| Přátelé se nemohou připojit k mé hře | Všichni potřebují stejné mody ve stejném pořadí: [[Hraní s přáteli|Hraní-s-přáteli]]. |
| Cokoli jiného | [[Když se něco pokazí|Když-se-něco-pokazí]], nebo se zeptejte v [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) či na [Discordu](https://discord.gg/h54t5baNsC). |

## Linux a Steam Deck (přes Proton)

Když vlastní okno aplikace nemůže zobrazit její stránky (pod Protonem zůstane modré, protože WebView2 od Microsoftu
se tam nespustí), aplikace se místo toho otevře ve vašem webovém prohlížeči a malé okénko to oznámí: nechte ho během
hraní otevřené a jeho zavřením aplikaci zavřete. Na Linuxu zatím nevyzkoušeno: dejte nám prosím vědět, jak to jde,
v [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## Tvorba modů: RUSE Studio

1. Otevřete stránku [vydání studia](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio). Studio
   je ukázková verze, proto jsou jeho vydání označená **Pre-release**: vezměte nejnovější.
2. Pod **Assets** klikněte na **RUSE-Studio-Setup-0.9.8.9.exe** (nejnovější verze) a spusťte ho jako v kroku 2.
3. Spusťte **RUSE Studio**, pak postupujte podle [[Váš první mod|Váš-první-mod]] (10 minut).

**Další:** [[Hraní s přáteli|Hraní-s-přáteli]]

---

[[Polní příručka|Polní-příručka]] · [[English|Install-and-Play]]
