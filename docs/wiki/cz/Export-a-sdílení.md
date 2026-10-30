# Export a sdílení

> **Pro:** moddery · **Potřebujete:** RUSE Studio a hotový mod · **Trvá:** 5 minut

## 1. Export

1. Otevřete nabídku **módu** a vyberte **Exportovat mód…**.
2. Vyplňte **verzi** (tři čísla, například `1.0.0`), své jméno a řádek o tom, co mod dělá.
3. Vyberte, kam uložit. Studio jednou sestaví mod na vaší hře, aby zaznamenalo build hry, na kterém vznikl, a jeho
   **otisk** (krátký kód, který je stejný pro každého se stejnými mody), pak uloží jeden soubor:
   `<your-mod>-<version>.rusemod`.

Ten soubor je vše, co hráč potřebuje: přidá ho v RUSE Launcheru ([[Instalace a hraní|Instalace-a-hraní]]).

**Mody s velkými mapami:** u mapy změněné po celé ploše může sestavení počítat celé minuty (například kam mohou
jednotky jet na terénu, který jste otevřeli). Na to čekáte jen jednou. Export vloží do souboru to, co sestavení
spočítalo, takže první sestavení u hráče je kratší. Obsahuje jen naše vlastní čísla, nikdy soubor hry, a je zamčené
vlastním souborem hry pro tu mapu: otevře se jen na PC, které hru má. Zatím jen pohyb; ve hře zatím neviděno.

Když je export hotový, Studio otevře **Sdílejte svůj mód** s velikostí souboru, jeho kontrolním součtem SHA-256 a jeho
záznamem pro seznam, připraveným ke zkopírování. Kdykoli ho můžete znovu otevřít z nabídky **módu** (**Sdílet svůj
mód…**).

## 2. Sdílení: přidejte ho mezi podporované mody

Udělali jste mod? Přidejte ho do seznamu a staňte se přispěvatelem. Záložka **Podporované módy** v RUSE Launcheru
ukazuje mody ze seznamu na [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods) a hráči je instalují
jedním kliknutím (noví hráči je dostanou nabídnuté při prvním spuštění launcheru):

1. Nahrajte `.rusemod` (nejsnazší je GitHub Release: ve vašem vlastním repozitáři nebo v repozitáři seznamu).
2. Otevřete pull request do [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), který přidá záznam
   vašeho modu do `index.toml`: vložte záznam, který ukazuje Sdílejte svůj mód, a do `download` dejte odkaz na soubor.
   Velikost a SHA-256 musí být ty, které ukázal export: launcher odmítne stažení, které nesouhlasí, takže nikdo nemůže
   váš soubor vyměnit za jiný.
3. Nebo ho zveřejněte v [Discussions > Mods & maps](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions)
   se snímkem obrazovky a tím, co mění (přetáhněte `.rusemod` do příspěvku), a do seznamu ho přidáme za vás.

Cheat nebo testovací nástroj (jednotky zdarma, okamžitá stavba...) dostane štítek `"cheat"`: launcher ho ukáže ve
vlastní skupině „Cheaty a testovací nástroje (volitelné)“ a nikdy ho nezaškrtne ani nestáhne, pokud to neudělá hráč.
Nová verze je nový soubor s novým číslem verze: zveřejněný soubor se nikdy nemění.

Přesný formát záznamu:
[MOD_FORMAT.md, oddíl 15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/docs/MOD_FORMAT.md#15-the-mod-index-supported-mods).

## Úprava nainstalovaného modu

V nabídce módu ve Studiu **Upravit nainstalovaný mód…** uvádí každý mod, který Launcher má (s polem hledání). Váš
vlastní otevře svůj projekt. Mod někoho jiného se stane vaší vlastní kopií s vlastním názvem (nemůže převzít název
originálu): vaše změny jdou do ní a aktualizace originálu je nikdy nesmaže. Mod z RUSE Mod Manageru (`.rmod`) se
převede ve své kopii, takže jeho změny hodnot se stanou změnami Studia, které můžete dál měnit.

## Co mod může obsahovat

Jen data: čísla, texty, mapy, modely, textury. Programy (`.exe`, `.dll`, skripty, které běží na PC) obě aplikace
odmítnou. Jedna výjimka: vlastní skripty misí hry, tak jak je ukládá Studio. Běží uvnitř hry a mohou dělat cokoli, co
umí ona, proto je instalujte jen od autorů, kterým věříte ([SECURITY.md](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/SECURITY.md)).

## Dobrá praxe

- Ponechte si složku svého modu: `.rusemod` je pro hráče, složka je to, co upravuje Studio.
- Napište do příspěvku, jaké jiné mody váš mod potřebuje nebo s jakými se tluče.
- Uveďte lidi, na jejichž práci stavíte.

---

[[Polní příručka|Polní-příručka]] · [[English|Export-and-Share]]
