# Instalacja i gra

> **Dla:** graczy · **Potrzebujesz:** gry R.U.S.E. ze Steama, zainstalowanej · **Czas:** 5 minut

**W skrócie:** pobierz **RUSE-Launcher-Setup** ze strony wydań, uruchom go, otwórz **RUSE Launcher**, kliknij
**Obsługiwane mody**, zaznacz mod i naciśnij **Zainstaluj**, dodaj go do zestawu modów, potem **Graj**. Każdy krok poniżej
mówi dokładnie, gdzie kliknąć.

Do grania z modami potrzebujesz tylko **RUSE Launcher**. **RUSE Studio** służy do ich tworzenia (zobacz koniec tej
strony).

## Krok 1: Pobierz Launcher

1. Otwórz stronę [wydań launchera](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher).
2. Najnowsze jest na górze, oznaczone **Latest** (na przykład *RUSE Launcher 0.4.8.23*).
3. Przewiń w dół do **Assets** pod nim i kliknij **RUSE-Launcher-Setup-0.4.8.23.exe** (numer wersji się zmienia; weź plik
   `.exe`, który zaczyna się od `RUSE-Launcher-Setup`). Twoja przeglądarka go pobierze.

Pozostałe pliki (`RUSE-Launcher-notes.json`, *Source code*) nie są potrzebne.

## Krok 2: Zainstaluj go

1. Otwórz pobrany plik (zwykle w folderze **Pobrane**).
2. **„System Windows ochronił ten komputer”?** Kliknij **Więcej informacji**, potem **Uruchom mimo to**. Aplikacja jest
   nowa dla sprawdzania reputacji Windows; jej kod jest publiczny na tym GitHubie.
3. Przejdź przez instalator. Zostaw zaznaczone **Zachowaj czystą kopię plików gry**: aplikacje nigdy nie zmieniają
   folderu twojej gry, chyba że poprosisz je o przywrócenie go z tej kopii, ale inne menedżery modów i ręczne zmiany
   mogą to zrobić, a każda gra z modami jest budowana z tych plików. Kopia powstaje przy pierwszym uruchomieniu
   aplikacji (kilka minut, mniej więcej tyle miejsca na dysku, ile zajmuje gra).
4. Uruchom **RUSE Launcher** (menu Start albo skrót na pulpicie). Za pierwszym razem **Wybierz język**: dowolny
   z jedenastu, dziesięciu języków gry i perskiego (فارسی); przycisk języka u góry zmienia go w każdej chwili.
   Launcher sam znajduje R.U.S.E. przez Steam.
   Jeśli mówi, że nie może: **Ustawienia > Folder gry > Wybierz folder…** i wybierz folder, w którym jest `RUSE.exe`
   (zwykle `C:\Program Files (x86)\Steam\steamapps\common\R.U.S.E`).

> [!IMPORTANT]
> **R.U.S.E. 2.0 działa tylko z kopią gry, którą masz na Steamie.** Zanim zmodowana gra wystartuje, Launcher i Studio
> sprawdzają folder gry: zapis Steama o R.U.S.E. zainstalowanej w tym folderze, własny plik Steama w nim i brak plików,
> które pozwalają uruchomić grę bez Steama. Jeśli nie mogą tego potwierdzić, okienko mówi dlaczego i co zrobić (Graj
> pozostaje wyłączone do tego czasu): zobacz [[Gdy coś pójdzie nie tak|Gdy-coś-pójdzie-nie-tak]].

**Przy pierwszym uruchomieniu** aplikacja pokazuje nasze **warunki korzystania i informację o prywatności**: przeczytaj je i kliknij **Akceptuj i kontynuuj**. Możesz je przeczytać ponownie w każdej chwili w **Ustawienia > Warunki, autorzy i licencje**. Jeśli w Windows brakuje **Microsoft WebView2** (potrzebuje go okno aplikacji), jest proponowany, nigdy wymuszany: zaznaczone pole w instalatorze, pytanie Tak/Nie przy uruchomieniu aplikacji i karta w **Ustawieniach**.

## Krok 3: Zdobądź mody

**Z naszej listy (najłatwiej):** kliknij **Obsługiwane mody**, zaznacz mody, które chcesz, i naciśnij **Zainstaluj**.
Każdy plik jest pobierany i sprawdzany z listą, zanim trafi do twojej biblioteki.

**Z pliku, który ktoś udostępnił:** kliknij **Dodaj plik moda…** i wybierz plik albo przeciągnij go na okno. Launcher
przyjmuje:
- `.rusemod`: zrobione w RUSE Studio;
- `.rmod`: zrobione dla RUSE Mod Manager LittleGroove'a;
- `.zip`: spakowany folder moda.

Najpierw sprawdza plik: plik, który nie jest modem albo zawiera program, jest odrzucany z podaniem powodu.

**Stary mod w postaci własnych plików gry** (paczki `.dat`, które miałeś skopiować do folderu gry): kliknij
**Przekształć stary mod…**, wybierz jego folder, nadaj mu nazwę i kliknij **Przekształć i dodaj do biblioteki**. Folder
twojej gry nie jest ruszany.

Pobieranie, które przyjdzie ucięte albo straci połączenie, jest ponawiane raz, a jedno nieudane nie zatrzymuje reszty instalacji kilku modów.

## Krok 4: Wybierz, w co grać

1. **Zestaw modów** to mody, w które grasz razem, w określonej kolejności. Kliknij **Nowy zestaw modów…**, dodaj mody
   i ustaw ich kolejność (gdy dwa mody zmieniają to samo, wygrywa ten niżej).
2. Jeśli dwóch modów nie da się używać razem, Launcher mówi które i dlaczego, zanim zagrasz.

## Krok 5: Graj

Wybierz swój zestaw modów i naciśnij **Graj**. Za pierwszym razem Launcher buduje zmodowaną kopię gry (mniej więcej
minutę); potem tylko to, co się zmieniło. Następnie R.U.S.E. startuje z twoimi modami.

**R.U.S.E. 2.0 na złoto** jest wyłączone, dopóki tego nie włączysz: do tego czasu twoja gra zachowuje swój własny tytuł
i film z logo Eugen Systems. Aby to włączyć, zaznacz **Używaj złotego tytułu i filmu wprowadzającego R.U.S.E. 2.0** w
sekcji **Tytuł gry** w **Ustawieniach** (umowa, którą Launcher pokazuje przy pierwszym otwarciu, też ma na to pole). Gra
otwiera się wtedy na scenie bitwy, z modami lub bez, a jej menu główne, menu i ekrany wczytywania mają złoty tytuł.
Powstaje on na twoim PC z plików twojej własnej gry oraz obrazu i dźwięku dołączonych do aplikacji, za pierwszym razem
(kilka minut, raz).

**Oryginał** (bez modów) to też nasza kopia: **Graj** buduje zwykłą kopię gry z RUSE Guard w środku. Aby grać w R.U.S.E. bez naszych aplikacji, uruchom grę ze Steam.

> [!NOTE]
> Uruchomienie R.U.S.E. ze **Steama** uruchamia grę **bez** modów, jak zawsze. Aby grać z modami, uruchom ją przyciskiem
> **Graj** w Launcherze. Graj nigdy nie zmienia twojej instalacji Steam.

## Aktualizacje

Launcher sprawdza, czy jest nowa wersja, przy każdym uruchomieniu: kliknij **Zaktualizuj**, gdy ją zaproponuje. Jeśli
aktualizacja się nie uda z komunikatem „certificate verify failed”, pobierz najnowszy `RUSE-Launcher-Setup` z kroku 1
w przeglądarce i uruchom go: instaluje się na starym i zachowuje twoje mody.

**Wymagane aktualizacje:** aktualizacji oznaczonej jako wymagana (ważnej, na przykład poprawki bezpieczeństwa) nie da się pominąć. Okno zasłania Launcher, a aktualizacja instaluje się sama, po czym Launcher uruchamia się ponownie; dopóki nie zostanie zainstalowana, **Graj** pozostaje wyłączone. Bez internetu okno o tym informuje: połącz się i naciśnij **Spróbuj ponownie**. Studio robi to samo z **Testuj w grze**.

Aktualizacja instaluje się tylko wtedy, gdy ma nasz podpis. Jeśli Launcher lub Studio mówi, że nowej wersji nie udało
się potwierdzić, nie instaluj jej ręcznie, chyba że powiemy tak na naszym Discordzie; poczekaj na następną aktualizację.

**Sprawdzanie aktualizacji** czeka, aż zaakceptujesz warunki. Jeśli pobieranie nie uda się trzy razy, aplikacja sama przestaje próbować i wskazuje stronę wydania: pobierz tam Setup (krok 1) i uruchom go.

**Odinstalowanie** pyta, czy usunąć też ustawienia i dane aplikacji (odpowiedź zaczyna się na Nie). Dopóki druga aplikacja jest zainstalowana, o nic nie pyta i niczego nie usuwa.

## Problemy?

| Co widzisz | Co zrobić |
|---|---|
| „System Windows ochronił ten komputer” | **Więcej informacji**, potem **Uruchom mimo to** (krok 2). |
| Launcher nie może znaleźć R.U.S.E. | **Ustawienia > Folder gry > Wybierz folder…**, folder z `RUSE.exe`. |
| „certificate verify failed: unable to get local issuer certificate” | Zdobądź Launcher 0.4.8.4 lub nowszy (krok 1); zobacz [[Gdy coś pójdzie nie tak|Gdy-coś-pójdzie-nie-tak]]. |
| „unable to get issuer certificate” albo „ten PC nie ufa certyfikatowi bezpieczeństwa strony” przy instalowaniu modów | Zdobądź Launcher 0.4.8.9 lub nowszy (krok 1) albo pobierz mod w przeglądarce i użyj **Dodaj plik moda…**; zobacz [[Gdy coś pójdzie nie tak|Gdy-coś-pójdzie-nie-tak]]. |
| Gra startuje bez moich modów | Uruchom ją przyciskiem **Graj** w Launcherze, nie ze Steama. |
| Znajomi nie mogą dołączyć do mojej gry | Wszyscy potrzebują tych samych modów w tej samej kolejności: [[Gra ze znajomymi|Gra-ze-znajomymi]]. |
| Coś innego | [[Gdy coś pójdzie nie tak|Gdy-coś-pójdzie-nie-tak]] albo zapytaj w [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) lub na [Discordzie](https://discord.gg/h54t5baNsC). |

## Linux i Steam Deck (przez Proton)

Gdy własne okno aplikacji nie może pokazać jej stron (pod Protonem zostaje niebieskie, bo WebView2 Microsoftu tam nie
startuje), aplikacja otwiera się zamiast tego w twojej przeglądarce, a małe okienko o tym mówi: trzymaj je otwarte podczas
gry i zamknij je, by zamknąć aplikację. Jeszcze nie testowane na Linuksie: napisz nam, jak poszło, w
[Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

## Tworzenie modów: RUSE Studio

1. Otwórz stronę [wydań Studio](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=studio). Studio jest
   wersją zapoznawczą, więc jego wydania są oznaczone **Pre-release**: weź najnowsze.
2. W **Assets** kliknij **RUSE-Studio-Setup-0.9.8.23.exe** (najnowsza wersja) i uruchom go jak w kroku 2.
3. Uruchom **RUSE Studio**, potem postępuj według [[Twój pierwszy mod|Twój-pierwszy-mod]] (10 minut).

**Dalej:** [[Gra ze znajomymi|Gra-ze-znajomymi]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Install-and-Play]]
