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

- **Rozwiązywanie problemów** w Launcherze mówi też, gdy brakuje własnych plików aplikacji (Graj potrzebuje ich do zbudowania gry), zamiast mówić, że wszystko gotowe: zainstaluj aplikację ponownie ze strony [wydań](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases).

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

- **Odłóż** jest też proponowane dla uszkodzonego pliku grup menu budowy (`menu_groups.toml`) i plików animacji (`files/anim/units.toml`, `copies.toml`, `clips.toml`). Zanim klikniesz, wiersz mówi, bez czego obejdzie się budowanie (twoich grup na listach budowy albo własnych animacji twoich jednostek; ich pliki klipów zostają), a plik dostaje nazwę `<nazwa>.broken.toml`, nigdy nie jest usuwany.

## Aplikacja długo się otwiera

- **Pierwsze uruchomienie po instalacji** z zaznaczonym „Zachowaj czystą kopię plików gry” robi tę kopię (cały folder
  gry, około 5.3 GB): Ustawienia pokazują, ile już zrobiono, a z aplikacji można w tym czasie korzystać.
- **Indeks gry w RUSE Studio** jest budowany raz na wersję gry i znowu, gdy aktualizacja Studio go zmienia (około minuty;
  Studio najpierw pyta). W tym czasie można korzystać z zakładki Mapy i z Ustawień, a wiersz na dole mówi, kiedy indeks
  jest gotowy.
- Cokolwiek innego: otwórz **Rozwiązywanie problemów** i kliknij **Kopiuj raport**. Raport podaje, ile trwał każdy krok
  ostatnich uruchomień aplikacji, w sekundach: wklej go w [[zgłoszenie błędu|Zgłaszanie-błędu]]. Te same wiersze są zapisywane
  w `%LOCALAPPDATA%\RUSE Mod Platform\logs\studio-start.log` (Launchera: `launcher-start.log`).

- Zanim indeks gry zostanie zbudowany, karta **Nacje** w Studio to mówi, z przyciskiem **Zbuduj indeks**.

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
  czyta je to Studio, zachowując ich znaczenie; najpierw zip całego moda trafia do folderu `Backups` Studia.
- **Nowsze RUSE Studio:** zaktualizuj Studio, zanim zmienisz ten mod: starsze mogłoby pominąć to, czego nie zna.

## Zamykanie Studio pyta „Zamknąć RUSE Studio?”

Nie wszystko jest jeszcze zapisane, a okienko mówi co (pole z wpisanym, ale niezatwierdzonym tekstem, zmiana wciąż
zapisywana, Testuj w grze wciąż budujące...). **Nie** zostawia Studio otwarte; **Tak** zamyka je i to traci.

## Gra startuje, ale bez moich zmian

1. Czy została uruchomiona przez **Graj** (launcher) lub **Testuj w grze** (Studio)? Ze Steama gra startuje bez modów.
2. Zmiany mapy widać tylko na tej mapie: w menu głównym kliknij **BITWY** i wybierz ją (komunikat Studio po Testuj w grze
   mówi, który przycisk i którą mapę).
3. Czy mod jest w zestawie i czy mod niżej w kolejności nie zmienia tego samego?

## „nie dało się odczytać ani zapisać (błąd 448)” zaraz po instalacji lub aktualizacji

Redirection Guard systemu Windows zablokował folder gry: aplikację otworzył jej instalator lub aktualizacja, a do folderu prowadzi dowiązanie folderu (biblioteka Steam przeniesiona na inny dysk za pomocą dowiązania). Od Launchera 0.4.8.24 i Studia 0.9.8.24 instalator już go nie przekazuje. Jeśli nadal to widzisz, **Rozwiązywanie problemów** o tym mówi: kliknij **Otwórz aplikację ponownie** albo zamknij aplikację i uruchom ją z menu Start.

## Plik jest w użyciu (Usuń, Eksport)

**Usuń** czeka do 10 sekund na plik, który trzyma inny program (Blender, edytor), a potem go nazywa: zamknij ten program i kliknij **Usuń** jeszcze raz. **Eksport** kończy się, nawet gdy plik starszej kopii modu w bibliotece Launchera jest otwarty w innym programie: mówi, że mod nie został dodany do biblioteki, i nazywa plik do zamknięcia.

## Aktualizacja się nie instaluje

Aktualizacje są podpisane: instaluje się tylko taka, która ma nasz podpis i jest dokładnie podpisanym plikiem. Jeśli aplikacja mówi, że nowej wersji nie udało się potwierdzić, nie instaluj jej ręcznie, chyba że powiemy o tym na naszym Discordzie: poczekaj na następną aktualizację. Jeśli pobieranie nie uda się trzy razy, aplikacja sama przestaje próbować i wskazuje stronę wydania: pobierz tam instalator w przeglądarce i uruchom go (instaluje się na starej wersji, tak jak aktualizacja).

## Gra się wywraca

Gdy gra uruchomiona przyciskiem **Graj** albo **Testuj w grze** się zawiesi, aplikacja to mówi i podaje krótki **kod awarii**, z **Kopiuj kod**. Wyślij kod i zrzut ekranu do XUL na Discordzie (XUL6x3) albo na GitHubie ([[zgłoś to|Zgłaszanie-błędu]]), razem z tym, co robiłeś tuż przed (która mapa, który rozkaz, co było na ekranie). Z włączonym **Bug Watch** znana nam awaria jest też wyjaśniona: jednostka, którą gra właśnie tworzyła, i dlaczego. Zgłoszenia awarii na edytowanych mapach sprawiły, że narzędzia map są solidne.

- **Nowa mapa zawieszała grę przy wczytywaniu**, gdy folder gry miał pozostałe foldery rewizji (zgłoszenie GitHub 25). Studio 0.9.8.23 i Launcher 0.4.8.23 budują z najnowszego: zaktualizuj.

## Coś innego

[[Zadaj pytanie|Zadawanie-pytań]].

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|When-Something-Goes-Wrong]]
