# Gdy coś pójdzie nie tak

Znajdź to, co widzisz, i zastosuj poprawkę.

## Najpierw spróbuj Rozwiązywania problemów

**Rozwiązywanie problemów** sprawdza za jednym razem to, co może zatrzymać test lub **Graj**: czy gra jest znaleziona, czy
Steam działa, czy R.U.S.E. nie zostało uruchomione ze zmodowanej kopii, dysk i jego wolne miejsce, pozostawione kopie,
pliki tylko do odczytu oraz czy aplikacja może zapisywać tam, gdzie trafiają kopie. Każdy problem, który umie naprawić,
ma przycisk; przy reszcie jest napisane, co zrobić.

- W RUSE Studio: obok **Testuj w grze** i w **Ustawienia > Pomoc**. W RUSE Launcher: na dolnym pasku i w każdym
  komunikacie o problemie (Studio 0.8.0, Launcher 0.3.0).
- **Kopiuj raport** daje tekst do wklejenia w [[zgłoszenie błędu|Zgłaszanie-błędu]] (twoja nazwa użytkownika Windows jest
  pominięta).

## Sama gra wygląda na zmienioną (przez inny menedżer modów lub ręczną zmianę)

**Ustawienia > Czysta kopia zapasowa gry** przechowuje czystą kopię plików gry, porównuje z nią pliki i przywraca to, co
się zmieniło. Pliki, które nie należą do gry, są odkładane na bok, nigdy usuwane. Albo **Zweryfikuj w Steam** pozwala
Steamowi naprawić grę. To jedyne miejsce, w którym aplikacje zapisują coś w folderze twojej gry, i tylko wtedy, gdy o to
poprosisz.

## Czerwony pasek pod nagłówkiem Studio

To **kontrola moda**. Studio czyta każdy plik twojego moda tak, jak zrobi to budowanie gry, gdy wybierzesz mod, i znowu
przed **Testuj w grze**. Każdy problem jest opisany prostymi słowami (co jest nie tak, na której mapie, co zrobić),
z przyciskiem, który go naprawia, tam gdzie się da: uzupełnia brakującą wartość, usuwa ten jeden zły element lub
ustawienie albo odkłada plik na bok. Plik w dawnej postaci zostaje zachowany obok. **Szczegóły** pokazuje słowa samego
budowania, przydatne, gdy prosisz o pomoc.

- **Odłóż** (obok zepsutego pliku mapy) zmienia jego nazwę na `<name>.broken.toml` obok oryginału: nic nie przepada,
  mod działa bez niego, a ta mapa zaczyna od nowa, czysta.
- Problem w `mod.toml` lub w zmianach jednostek nie ma Odłóż: otwórz plik i popraw wiersz, który wskazuje pasek, albo
  zapytaj w [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

> [!NOTE]
> Znany przypadek: RUSE Studio 0.7.0 i starsze zapisywały pociągnięcia pędzla **Woda** bez poziomu wody („the water brush
> needs level”). 0.7.1 to naprawia; **Odłóż** usuwa stary plik.

## Aplikacja długo się otwiera

- **Pierwsze uruchomienie po instalacji** z zaznaczonym „Zachowaj czystą kopię plików gry” robi tę kopię (cały folder
  gry, około 5.3 GB): Ustawienia pokazują, ile już zrobiono, a z aplikacji można w tym czasie korzystać.
- **Indeks gry w RUSE Studio** jest budowany raz na wersję gry i znowu, gdy aktualizacja Studio go zmienia (około minuty;
  Studio najpierw pyta). W tym czasie można korzystać z zakładki Mapy i z Ustawień, a wiersz na dole mówi, kiedy indeks
  jest gotowy.
- Cokolwiek innego: otwórz **Rozwiązywanie problemów** i kliknij **Kopiuj raport**. Raport podaje, ile trwał każdy krok
  ostatnich uruchomień aplikacji, w sekundach: wklej go w [[zgłoszenie błędu|Zgłaszanie-błędu]]. Te same wiersze są zapisywane
  w `%LOCALAPPDATA%\RUSE Mod Platform\logs\studio-start.log` (Launchera: `launcher-start.log`).

## „System Windows ochronił ten komputer”

Aplikacje są nowe dla sprawdzania reputacji Windows. Kliknij **Więcej informacji**, potem **Uruchom mimo to**.

## „certificate verify failed: unable to get local issuer certificate” (lub „unable to get issuer certificate”)

Żaden mod się nie pobiera albo nie pobiera się aktualizacja. Windows nie pobrał jeszcze certyfikatu, z którym sprawdzany
jest GitHub; od Launchera 0.4.8.4 i Studio 0.9.8.4 aplikacje proszą o niego Windows i próbują znowu. Od Launchera 0.4.8.9
i Studio 0.9.8.9 próbują też z listą certyfikatów, której używa Firefox, a którą mają ze sobą, dla PC, którego Windows nie
może go pobrać (aktualizacje certyfikatów są tam wyłączone lub zablokowane: „unable to get issuer certificate” albo „ten PC
nie ufa certyfikatowi bezpieczeństwa strony”). Ze starszą aplikacją aktualizacja też nie może się pobrać: pobierz
instalator z [wydań](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases) w przeglądarce i uruchom go (instaluje
się na starej wersji, tak jak aktualizacja). Mod zawsze można pobrać w przeglądarce z
[wydań](https://github.com/sneadtristen6/Ruse-Mods/releases) listy modów i dodać przez **Dodaj plik moda…** w Launcherze.
Jeśli nowa aplikacja wciąż to mówi: może to powodować antywirus, który skanuje bezpieczne połączenia (HTTPS), sieć szkolna
lub firmowa albo zła data na PC; napisz nam w [Discussions > Help](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## „[WinError 5] Odmowa dostępu” podczas testowania lub grania

Windows odmówił usunięcia kopii gry zrobionej przez aplikację (w `RUSE-Instances`). Także: „An old modded copy at
`...\RUSE-Instances\<name>.old` can't be removed”, przy co drugim **Testuj w grze** lub **Graj**.

- **Najpierw zaktualizuj** (aplikacje proponują to przy otwarciu): od RUSE Studio 0.7.6 i Launchera 0.2.11 kopia, której
  Windows nie chce usunąć, nigdy nie zatrzymuje testu: jest przenoszona do `RUSE-Instances\.trash` i usuwana stamtąd, gdy
  nic jej już nie trzyma.
- **R.U.S.E. wciąż działa z wcześniejszego testu?** Aplikacja o tym mówi, z nazwą programu: zamknij grę (sprawdź, czy na
  karcie Szczegóły w Menedżerze zadań jest `RUSE.exe`), potem spróbuj znowu. **Rozwiązywanie problemów** znajduje grę
  wciąż uruchomioną z kopii oraz pozostawione kopie i usuwa je za ciebie.
- **Ze starszą wersją:** usuń folder, który podaje komunikat (`...\RUSE-Instances\<name>.partial` lub `.old`; Windows
  pyta o pliki tylko do odczytu: odpowiedz tak; znika tylko kopia, nigdy gra), potem spróbuj znowu. Jeśli Windows
  odmawia, najpierw uruchom Windows ponownie.
- Wciąż to samo? [[Zgłoś to|Zgłaszanie-błędu]] z całym komunikatem.

## Aplikacja nie może znaleźć R.U.S.E.

**Ustawienia > Folder gry > Wybierz folder…** i wybierz folder, w którym jest `RUSE.exe` (na Steamie:
`steamapps\common\R.U.S.E`).

## „Nie udało się potwierdzić tej kopii R.U.S.E.”

R.U.S.E. 2.0 działa tylko z kopią gry, którą posiadasz. Dopóki folder gry nie zostanie potwierdzony, **Graj** i **Testuj
w grze** pozostają wyłączone, a to okienko mówi dlaczego: Steam nie ma zapisu o R.U.S.E. zainstalowanej w tym folderze;
własnego pliku Steama w nim (`steam_api64.dll`) brakuje, jest zmieniony albo nie pochodzi od Valve; albo folder ma
pliki, które pozwalają uruchomić grę bez Steama (okienko je wymienia).

- **Masz ją na Steamie:** kliknij **Sprawdź moje pliki w Steam** (Steam przywraca swoje pliki, których brakuje lub które
  zostały zmienione), usuń pliki, które wymienia okienko, potem kliknij **Sprawdź ponownie**. Folder gry wybrany ręcznie
  musi być tym, który zainstalował Steam.
- **Masz ją w inny sposób** (kopia pudełkowa sprzed pojawienia się R.U.S.E. na Steamie) **albo uważasz, że sprawdzenie
  się pomyliło:** okienko pokazuje **Twój kod** (zrobiony z tego PC i folderu gry). Kliknij **Kopiuj**, potem **Otwórz
  zgłoszenie na Discordzie** albo **Otwórz zgłoszenie na GitHubie** i wklej go. Wyślemy ci kod odblokowujący: wklej go
  pod **Kod odblokowujący** i kliknij **Odblokuj**. Potwierdza on tę kopię na tym PC.

Sprawdzenie jest takie samo na Windows, Linuksie i Steam Deck. Ten projekt nigdy nikomu nie pomaga grać w R.U.S.E. bez
posiadania gry: żadnego rozdawania plików gry, żadnego uruchamiania jej bez Steama.

## „W starszym formacie moda” albo „zapisany przez nowsze RUSE Studio”

- **Starszy format moda:** mod został zrobiony starszym Studio. **Zaktualizuj ten mod** przepisuje jego pliki tak, jak
  czyta je to Studio, zachowując ich znaczenie; najpierw zip całego moda trafia do folderu `mod-backups` Studia.
- **Nowsze RUSE Studio:** zaktualizuj Studio, zanim zmienisz ten mod: starsze mogłoby pominąć to, czego nie zna.

## Zamykanie Studio pyta „Zamknąć RUSE Studio?”

Nie wszystko jest jeszcze zapisane, a okienko mówi co (pole z wpisanym, ale niezatwierdzonym tekstem, zmiana wciąż
zapisywana, Testuj w grze wciąż budujące...). **Nie** zostawia Studio otwarte; **Tak** zamyka je i to traci.

## Gra startuje, ale bez moich zmian

1. Czy została uruchomiona przez **Graj** (launcher) lub **Testuj w grze** (Studio)? Ze Steama gra startuje bez modów.
2. Zmiany mapy widać tylko na tej mapie: w menu głównym kliknij **BITWY** i wybierz ją (komunikat Studio po Testuj w grze
   mówi, który przycisk i którą mapę).
3. Czy mod jest w zestawie i czy mod niżej w kolejności nie zmienia tego samego?

## Gra się wywraca

Zapisz, co robiłeś tuż przedtem (która mapa, jaki rozkaz, co było na ekranie), zrób zrzut ekranu i
[[zgłoś to|Zgłaszanie-błędu]]. To dzięki zgłoszeniom awarii na edytowanych mapach narzędzia map stały się solidne.

## Coś innego

[[Zadaj pytanie|Zadawanie-pytań]].

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|When-Something-Goes-Wrong]]
