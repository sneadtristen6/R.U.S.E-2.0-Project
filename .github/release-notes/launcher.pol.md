**RUSE Launcher 0.4, dla graczy.** Znajduje R.U.S.E. przez Steam, a **Graj** buduje zmodowaną kopię gry z twoimi
modami i ją uruchamia. Twoja instalacja Steam nigdy nie jest zmieniana.

**0.4.8.14:** Mody z własnym skryptem rozgrywki znowu się budują.

- **Naprawione: Graj zatrzymywało się przy niektórych zestawach modów** z komunikatem „RUSE Guard's scripts can't be added: .xyz says ... bytes but holds ...”: kilka modów ma własny skrypt rozgrywki, którego nagłówek żąda więcej miejsca, niż skrypt potrzebuje (wśród nich 1 VS 7 AI, 1 VS 15 AI, Operation Overlord i Sand Box). Gra uruchamia te skrypty bez problemu, ale Launcher je odrzucał, więc nie dało się zbudować żadnego zestawu z jednym z tych modów. Teraz czyta je tak jak gra.

**0.4.8.13:** Raporty o awariach gry mówią, co doprowadziło do awarii.

- **Raporty Bug Watch o awariach gry mówią więcej:** jeśli zaznaczyłeś Bug Watch, a gra ulegnie awarii, raport mówi teraz także, co gra próbowała odczytać lub zapisać, oraz do 16 miejsc w grze, które doprowadziły do awarii, odczytanych z własnego raportu o awarii gry na twoim PC, który nadal nigdy go nie opuszcza. Raport, który mówił tylko, gdzie gra się zatrzymała, nie mógł pokazać dlaczego; teraz możemy prześledzić awarie takie jak ta, którą gracz przysłał nam w tym tygodniu, i je naprawić.
- **Umowa, wersja 3:** wymienia teraz te dwie nowe rzeczy wśród tego, co zawiera raport o awarii gry; nic innego się w niej nie zmieniło. Ponieważ się zmieniła, obie aplikacje pokażą ci ją jeszcze raz przy otwarciu.

**0.4.8.12:** Graj znowu buduje zmodowane gry.

- **Naprawione: Graj zatrzymywało się przy każdym zestawie modów** z komunikatem „No such file or directory: ...fairplay_watch.bin”: instalatorom wersji 0.4.8.10 i 0.4.8.11 brakowało trzech plików RUSE Guard, więc nie dało się zbudować żadnej zmodowanej gry. Wróciły, a aplikacji, której brakuje któregoś z jej plików, nie da się już wydać.

**0.4.8.11:** logowanie przez Steam kończy się w aplikacjach; w Linux programy pomocnicze budowania startują tak jak w Windows.

- **Naprawione: logowanie przez Steam.** Po zalogowaniu na stronie Steam Launcher i Studio dalej czekały i nigdy nie pytały naszego serwera, czy już skończyłeś: okno zatrzymywało własne sprawdzanie przed pierwszym razem. Teraz sprawdza co kilka sekund i loguje cię, gdy tylko Steam to potwierdzi. Wypróbowane w podglądzie: sprawdzanie działa, a okno pokazuje, że jesteś zalogowany.
- **Programy pomocnicze startują od nowa w każdym systemie:** programy, między które budowanie dzieli pracę (importowane modele, naprawa mapy, ruch, woda), startują teraz od nowa także w Linux, tak jak zawsze w Windows. W Linux startowały jako kopie działającej aplikacji, co czasem mogło zawiesić budowanie i sprawiało, że jeden z naszych testów tam nie przechodził. W Windows i w Proton na Steam Decku nic się nie zmienia.

**0.4.8.10:** mody ponad 4 GB, listy budowy w grupach, szybsze budowanie dużych modów, perski i każda strona w 11 językach, poprawki ze zgłoszeń testerów; oraz RUSE Guard, nasz anty-cheat do prawdziwych gier wieloosobowych, z kodem gry; Bug Watch, raporty o awariach i użyciu, które możesz włączyć; logowanie przez Steam; i umowa przy pierwszym uruchomieniu.

- **Naprawione, zgłoszone przez gracza: mody ponad 4 GB.** Zestaw modów, którego zmodowana gra przekraczała 4 GB, przestawał się budować po Graj („'I' format requires 0 <= number <= 4294967295”). Paczki mają teraz pełną długość, a paczka ponad 4 GB jest zapisywana w szerszym układzie, który gra potrafi odczytać dzięki małej łatce gry: pobieranej raz i nakładanej tylko na twoją zmodowaną kopię, nigdy na grę w twoim folderze Steam. Powyżej 32 GB albo przy jednym pliku ponad 4 GB budowanie mówi to wprost. Przetestowane w grze: kopie ponad 4 GB oraz z 200, 283 i wszystkimi 366 jednostkami z innych epok.
- **Wiele własnych modeli:** gra znajduje tekstury zastępcze paczki przez indeks, a budowanie, które dodawało je dla importowanych modeli, zapisywało go źle: przy wielu jednostkach z innych epok gra zawieszała się albo padała podczas wczytywania. Teraz jest zapisywany tak, jak gra go czyta, dla każdego moda, który je dodaje. Przetestowane w grze ze wszystkimi 366 jednostkami z innych epok.
- **Listy budowy w grupach:** mod z wieloma jednostkami dostaje listę budowy każdego budynku w grupach, linie samej gry: najwyżej 6 jednostek w grupie i 10 grup w budynku, żeby cała lista mieściła się na ekranie i każdą jednostkę dało się zbudować. Mod zrobiony wcześniej, który przekracza te limity, i tak się zbuduje, z ostrzeżeniem. Przetestowane w grze z 297 jednostkami z innych epok w grupach.
- **Szybsze budowanie:** modele z twoich modów są przechowywane między budowaniami, a nowe powstają równolegle na rdzeniach twojego PC. Mod z 366 jednostkami z innych epok budował się około 18 minut na PC z 8 rdzeniami; teraz około 5 za pierwszym razem i około 3 potem, z tymi samymi plikami gry, bajt w bajt.
- **Zgłoszenia testerów:** mod jednostek i zmiany mapy zrobione pod jedną nazwą budują się razem (zatrzymywały Graj); mapa z usuniętymi własnymi mostami buduje się z nowymi mostami; importowane części wieży i działa holowane budują się tak, jak robi je Studio 0.9.8.10. Mosty i części wieży jeszcze nie wypróbowane w grze.
- **Twoje pliki:** Usuń wysyła moda z biblioteki do Kosza, Pokaż w folderze otwiera moda tam, gdzie jest, a Ustawienia pokazują, gdzie trzymane są twoje pliki. Widziane w podglądzie; jeszcze nie wypróbowane w oknie aplikacji.
- **Perski i 11 języków:** perski jest 11. językiem aplikacji, pisanym od prawej do lewej; README, wiki, te notatki i ekrany instalatora są we wszystkich 11.
- **Obowiązkowe aktualizacje:** aktualizacja, którą oznaczymy jako obowiązkową, instaluje się sama, z oknem, którego nikt nie może zamknąć (aplikacje od tej wersji potrafią odczytać to oznaczenie).
- **Tylko posiadane kopie:** zanim Graj zbuduje zmodowaną kopię, aplikacje sprawdzają, czy folder gry to kopia, którą posiadasz, na podstawie tego, co zostawił tam Steam, w Windows, w Proton na Steam Decku i w Linux. Jeśli twojej nie da się potwierdzić (kopia pudełkowa sprzed czasów R.U.S.E. na Steamie), okno pozwala otworzyć zgłoszenie, a my wysyłamy ci kod odblokowania dla tego PC.
- **Discord:** aplikacje i strony używają nowego zaproszenia, które nie wygasa.
- **Umowa przy pierwszym uruchomieniu:** gdy Studio lub Launcher otwiera się po raz pierwszy, mówi, co robi RUSE Guard, i prosi o jego zaakceptowanie (to konieczne, by grać online z aplikacjami), czy włączyć Bug Watch (opcjonalnie), oraz o nazwę użytkownika, którą nasi programiści widzą przy twoich raportach: dodawane są # i cztery cyfry, by była niepowtarzalna, jak Nick#4821. Jedna nazwa działa w obu aplikacjach. Umowa pokazuje się znów, gdy się zmieni. Widziane w obu aplikacjach. We wszystkich 11 językach.
- **RUSE Guard:** nasz anty-cheat, według projektu DomesticNukes. Działa tylko w grach wieloosobowych i kooperacyjnych, nigdy w grze jednoosobowej, w potyczce z komputerem ani w kampanii. Twoja zmodowana gra dostaje **kod gry** do wysłania osobom, z którymi grasz: ten sam kod oznacza tę samą grę, tę samą wersję, te same mody i wersje modów, więc gra nie może się rozjechać. Mod zmieniający skrypty gry ma odznakę **Uruchamia skrypty**, a Graj czeka, aż zaznaczysz, że ufasz jego autorowi; kod (cheat) lub narzędzie testowe ma odznakę **Kod** i czyni kopię tylko offline: sama opuszcza gry wieloosobowe i kooperacyjne. W prawdziwej grze RUSE Guard porównuje nazwy uruchomionych programów z listą znanych narzędzi do oszukiwania (tylko nazwy; nic więcej nie jest odczytywane), a to, co zbierze, trafia pod twoją nazwę użytkownika, nigdy pod twoje konto Steam. Przetestowane w grach wieloosobowych z prawdziwym przeciwnikiem; dowody docierają na nasz serwer.
- **Bug Watch (opcjonalnie):** gdy go zaznaczysz, Studio i Launcher liczą, czego używasz i kiedy coś idzie nie tak, awarie aplikacji i gry, z tym, które mody były włączone, i raz dziennie wysyłają to naszym programistom z twoją nazwą użytkownika. Bez prawdziwych nazwisk, bez konta Steam, bez plików. Wyłączony, dopóki go nie zaznaczysz; odznacz go kiedy chcesz, a to, co było przechowywane, zostanie usunięte. Widziane w obu aplikacjach.
- **Logowanie przez Steam:** logowanie na własnej stronie Steam w twojej przeglądarce potwierdza, że posiadasz R.U.S.E., do gry online, RUSE Guard i pobierania zawartości. Nigdy nie widzimy twojego hasła, a twój identyfikator Steam nigdy nie jest zapisywany: tylko przepustka przechowywana na twoim komputerze przez 30 dni. Jest w Ustawieniach, **Logowanie przez Steam**; Launcher pyta raz. Nic tego jeszcze nie wymaga. Jeszcze nie wypróbowane w aplikacji.

**0.4.8.9:** mody instalują się na większej liczbie PC, i bezpieczniejsze wczytywanie obrazów.

- **Poprawione, zgłoszone przez gracza:** na niektórych PC żaden mod się nie instalował: „ten PC nie ufa certyfikatowi bezpieczeństwa strony (unable to get issuer certificate)”. Windows na tych PC nie ma certyfikatu, którym sprawdzane są pobrania z GitHuba, i nie może go pobrać. Launcher próbuje teraz także z listą certyfikatów Firefoksa, którą ma ze sobą. Do tego czasu mod pobrany w przeglądarce z listy modów instaluje się przez **Dodaj plik moda…**.
- **Bezpieczniejsze obrazy:** biblioteka, którą Launcher wczytuje obrazy (Pillow), ma teraz wersję 13.0.0, z poprawkami chroniącymi przed specjalnie spreparowanymi plikami obrazów, które mogły zawiesić aplikację, wyczerpać jej pamięć lub gorzej.
- **Staranniejszy kod:** 12 ostrzeżeń kontroli kodu GitHuba dla tego projektu zostało załatwionych. Gdy Launcher pokazuje swoje strony w twojej przeglądarce, otwierają one tylko jego własne pliki, sprawdzane w sposób, który ta kontrola rozpoznaje, a pobieranie wymaga TLS 1.2 lub nowszego, jak już wcześniej. W działaniu Launchera nic się nie zmienia.

**0.4.8.8:** uruchamia mody zrobione w Studio 0.9.8.8, a twoja zmodowana gra mówi R.U.S.E. 2.0 w złocie.

- **Mody zrobione w Studio 0.9.8.8 działają:** własne budynki (drugi i trzeci nacji potrzebują małej łatki gry, pobieranej raz i nakładanej tylko na twoją zmodowaną kopię, nigdy na grę w twoim folderze Steam), własny wygląd nowych budynków i obiekty, dźwięki i animacje zmienione w RUSE Decoy, wartości graczy komputerowych i zasady gry, oraz zamknięte przejścia po dawnych mostach.
- **R.U.S.E. 2.0 w złocie:** twoja zmodowana gra otwiera się sceną bitwy z uruchamianym silnikiem, a jej menu główne, mały tytuł każdego menu, obramowania menu i ekrany ładowania mówią R.U.S.E. 2.0 w złocie. Powstaje na twoim PC z plików twojej własnej gry za pierwszym razem (raz kilka minut, potem zachowane). Ustawienia mają pole, by zachować tytuł gry.
- **Poprawione: ciemne i jasne plamy na mapach zrobionych w Studio** (pustych, powiększonych, z rzeźbą terenu i z sektorami): taka mapa jest dobrze oświetlona, gdy zostanie zbudowana tą wersją (jej grunt jest robiony od nowa za pierwszym razem).
- **Poprawione, zgłoszone przez gracza:** na stronie Obsługiwane mody „Nowy zestaw modów…” nic nie robił. Teraz otwiera nowy zestaw. Jeszcze nie testowane w samej aplikacji.
- **Litery gry:** Launcher jest pisany czcionką menu gry, braną z twojej gry przy każdym starcie.
- **Wciąż z błędami, grasz na własną odpowiedzialność:** mapy zrobione z teksturami Map Paint i puste mapy (Pusty teren, Pusty ocean).

**0.4.8.7:** uruchamia mody zrobione w Studio 0.9.8.7.

- **Mody zrobione w Studio 0.9.8.7 działają:** obiekty przesunięte lub postawione w siatce, prostokącie i wzdłuż ścieżek, większe puste mapy z ich sektorami oraz zmiany ekonomii tylko trybu Nuklearnego.
- **Wiersze budowania w Twoim języku**, we wszystkich dziesięciu.
- **Zachowane wyniki budowania pozostają dobre po aktualizacji.**
- **Wciąż z błędami, grasz na własną odpowiedzialność:** mapy zrobione z teksturami Map Paint i puste mapy (Pusty teren, Pusty ocean).

**0.4.8.6:** uruchamia mody zrobione w Studio 0.9.8.6.

- **Mody zrobione w Studio 0.9.8.6 działają:** puste mapy z cieniami na płaskim terenie, to, co postawione tam, gdzie kopiowana mapa miała morze, narysowane, i podłoga kamery na nowym terenie.
- **Znany crash odrzucony:** mod, w którym uzbrojony samolot ma flagę zwiadu bez flagi myśliwca, wywracał grę, gdy samolot był wysyłany do ataku; teraz Launcher odmawia jego zbudowania i mówi dlaczego.
- **Wciąż z błędami, grasz na własną odpowiedzialność:** mapy zrobione z teksturami Map Paint i puste mapy (Pusty teren, Pusty ocean).

**0.4.8.5:** uruchamia mody zrobione w Studio 0.9.8.5.

- **Mody zrobione w Studio 0.9.8.5 działają:** samoloty w nowej roli (bombowiec z komorą bombową, zwiadowca, który zachowuje broń), pojazdy rozpoznawcze, broń trafiająca samoloty i teren malowany z biblioteki pędzla Tekstura z detalem gry na wierzchu. Starszy Launcher nie zbuduje niektórych z nich.
- **Szybciej:** mapa pomalowana tak samo odzyskuje pomalowany teren z poprzedniego budowania w kilka sekund.
- **Wciąż z błędami, grasz na własną odpowiedzialność:** mapy zrobione z teksturami Map Paint i puste mapy (Pusty teren, Pusty ocean).

**0.4.8.4:** mody pobierają się na każdym komputerze, a Launcher uruchamia mody zrobione w Studio 0.9.8.4.

- **Mody pobierają się na każdym komputerze:** na niektórych komputerach żaden mod się nie pobierał („certificate verify failed: unable to get local issuer certificate”). Teraz Launcher prosi Windows o certyfikat, tak jak przeglądarka, i próbuje ponownie; dotyczy to też jego własnych aktualizacji. Jeszcze nie wypróbowane na komputerze, który miał ten problem.
- **Mody zrobione w Studio 0.9.8.4 działają:** własne misje, puste mapy z ich sztabami i sektorami, składy z większą liczbą ciężarówek (starszy Launcher odrzuca składy powyżej 1000 ciężarówek), jednostki z własnym wyglądem i mundurami, edycje cudzych modów pod własną nazwą.
- **Wciąż z błędami, grasz na własną odpowiedzialność:** mapy zrobione z teksturami Map Paint i puste mapy (Pusty teren, Pusty ocean).

**0.4.8.3:** kopie z modami trafiają tam, gdzie wskażesz.

- **Gdzie trafiają kopie z modami**, w Ustawieniach: wybierz folder, w którym budowana jest kopia gry z modami, albo
  wróć do zalecanego miejsca, `RUSE-Instances` na dysku gry (tam kopia dzieli pliki z grą i jest gotowa w kilka sekund;
  na innym dysku jest pełną kopią gry, wolniejszą i większą). Czysta kopia zapasowa gry trafia obok. Następne Graj
  buduje w nowym miejscu; stary folder można usunąć ręcznie. Studio używa tego samego folderu.

**0.4.8.2:** otwiera się w twojej przeglądarce, gdy jego własne okno nie może, i uruchamia mody zrobione w Studiu
0.9.8.2.

- **Linux i Steam Deck (przez Protona):** Launcher otwiera się w twojej przeglądarce, gdy jego własne okno nie może.
  Jeszcze nie sprawdzone na Linuksie: daj nam znać, jak poszło.
- Mody zrobione w Studiu 0.9.8.2 działają: jednostki z innych epok z własnymi modelami, rozmiarami, badaniami i
  kartami.

**0.4.8.1:** konwertuje stare mody i uruchamia mody zrobione w Studiu 0.9.8.1.

- **Przekształć stary mod…**, narzędzie Convert LittleGroove'a: starszy mod w postaci paczek gry, do skopiowania do
  folderu gry, staje się modem, który twoja biblioteka uruchamia obok innych. Jeszcze nie sprawdzone na prawdziwym
  starym modzie.
- **Dwa mody zmieniające ten sam plik gry:** Launcher mówi o tym przed Graj, a **Użyj wersji…** wybiera który.
- Mody zrobione w Studiu 0.9.8.1 działają: utwory i głosy, nacja zmieniona w inną.

**0.4.8:** uruchamia mody zrobione w Studio 0.9.8, w tym nowe mapy zaczynające się od pustej, i pokazuje nowości w
twoim języku.

| Wcześniej | Teraz |
|---|---|
| Nowa mapa pokazywała obrazy w menu kopiowanej mapy. | Własne obrazy, takie, jakie zrobił jej autor, z punktami startowymi tam, gdzie zaczynają jej gracze. |
| Jednostka zbudowana na osuszonym morzu mogła zawiesić grę. | Naprawione (sprawdzone w grze). |
| Stara woda rzek stała jak ściany wzdłuż krawędzi mapy, a usunięte latarnie morskie wciąż świeciły nad morzem. | Naprawione (sprawdzone w grze). |
| Mod, który czyści całą mapę, mógł podczas budowania wyczerpać pamięć komputera. | Buduje się. |
| Nowości były tylko po angielsku. | Są w języku Launchera. |

Znane: **mapy morskie nie są skończone.** Pusty ocean buduje się i działa w grze, ale jednostki pod jego wodą nie
zostały jeszcze sprawdzone.

**0.4.7:** bardzo duże mody map budują się teraz w kilka minut (wcześniej trwało to bardzo długo), i uruchamia mody
zrobione w Studio 0.9.7.

| Wcześniej | Teraz |
|---|---|
| **Graj** mogło budować duży mod mapy godzinami. | Najbardziej ekstremalny, jaki mamy (mapa „D-Day” z osuszonym morzem), budował się około czterech godzin; teraz mniej niż 10 minut, z tym samym wynikiem. |
| Pierwsze budowanie dużego moda mapy wyliczało wszystko na twoim komputerze. | Mod wyeksportowany w Studio 0.9.7 zabiera ze sobą to, co jego budowanie wyliczyło dla ruchu na mapie: twoje pierwsze budowanie jest krótsze. Każda odpowiedź jest sprawdzana, a pliki gry wychodzą takie same. |

Znane: **mapy morskie nie są jeszcze dopracowane.** Osuszone lub pomalowane morze buduje się i wczytuje, ale woda wciąż
jest widoczna.

**0.4.6:** **Graj** uruchamia grę od razu, gdy nic się nie zmieniło, i uruchamia mody zrobione w Studio 0.9.6: nowe
jednostki z własnym modelem 3D.

| Wcześniej | Teraz |
|---|---|
| **Graj** za każdym razem budowało od nowa całą zmodowaną kopię, nawet gdy nic się nie zmieniło (gracz: „za każdym razem 30 minut czekania”). | Nic się nie zmieniło: gra startuje od razu. Zmiana przebudowuje kopię, ale niezmienione pliki ostatniej kopii są używane ponownie, więc kopia na innym dysku niż gra nie kopiuje już od nowa każdej paczki. Graj mówi, ile skopiowało. |
| Każde budowanie wczytywało dane jednostek gry od nowa. | Zachowane między budowaniami: duży testowy mod zajmował za każdym razem 213 s; teraz kolejne budowania po pierwszym zajmują 68 s. |
| Nowa jednostka moda miała model jednostki, którą kopiuje. | Jej własny model z moda (`files/models`) jest w grze. **Widziane w grze:** M1 Abrams obok Shermana. |
| Nowa jednostka moda z własną kartą powodowała awarię gry, gdy była budowana. | Naprawione. **Widziane w grze.** |
| Kolory przemalowanych jednostek wychodziły miejscami trochę nie takie. | Bliżej obrazu z moda. Mod z przemalowanymi jednostkami lub pomalowanym terenem dostaje nowy odcisk i kod dołączenia: wszyscy, którzy grają razem, powinni zaktualizować. |
| Powolny start nie zostawiał żadnej wskazówki. | **Kopiuj raport** wymienia kroki ostatnich pięciu startów. |
| — | Uruchamia mody z czyszczeniem całej mapy, drogami na przekształconym terenie i wypełnianiem koryt rzek ze Studio 0.9.6 (nowe, jeszcze nie widziane w grze na dużą skalę). |

**0.4.5:** uruchamia mody zrobione w Studio 0.9.5: przemalowane jednostki, ich własne karty i jednostki z własnymi
modelami.

| Wcześniej | Teraz |
|---|---|
| Mod nie mógł zmienić wyglądu jednostki. | Przemalowane jednostki i karty z moda pokazują się w grze. **Widziane w grze:** czerwony Sherman, karta zrobiona w Studio. |
| Mod, którego paczki modeli jednostek urosły, był odrzucany przez grę: awaria przy pierwszej fabryce. | Budowane tak, jak gra je sprawdza. **Widziane w grze:** drugi Sherman z własnym modelem. |
| Mod sprowadzający jednostki innej nacji w rozdziale kampanii lub Operacji powodował awarię podczas wczytywania (francuskie jednostki na mapie Holandii). | Ich modele wczytują się także tam. **Widziane w grze.** |
| Spłaszczenie gór na krawędzi mapy zostawiało tam urwisko. | Krawędź idzie za terenem. **Widziane w grze.** |

**0.4.4:** uruchamia mody z nowymi mapami, zrobionymi przez Duplikuj mapę w Studio 0.9.4.

| Wcześniej | Teraz |
|---|---|
| Nowe mapy z moda nie były jeszcze próbowane w grze. | **Widziane w grze:** nowa mapa moda jest na liście w BITWY i gra się na jej własnym terenie, 101 naraz. Wczesna wersja: zgłoś, co znajdziesz. |
| Aktualizacje przychodziły tylko jako całe wersje. | Małe poprawki mogą przychodzić między wersjami (0.4.4.1), oferowane jak każda aktualizacja. |

**0.4.3:** uruchamia mody zrobione w Studio 0.9.3 i buduje je około trzy razy szybciej.

| Wcześniej | Teraz |
|---|---|
| Skały i większość innych obiektów postawionych przez mod znikały, gdy tylko kamera oddaliła się z bliska. | Rysowane aż do dalekiej odległości; obiekty samej mapy bez zmian. **Widziane w grze.** |
| Nowa droga moda przez las była z wysoka jasnym pasem albo znikała ze średnio-dalekiej odległości. | Malowana przez lasy tak, jak drogi samej mapy. **Widziane w grze.** |
| Drogi moda zawsze usuwały drzewa ze swojej trasy. | Droga może je zachować (`keep_trees`): biegnie pod drzewami, bledsza i bardziej szara w lesie. |
| **Graj** budowało mod z nowymi drogami na M03_Italie około 5 minut. | Około 1½ minuty po pierwszym razie na danej mapie. |

**0.4.2:** uruchamia mody zrobione w Studio 0.9.2.

| Wcześniej | Teraz |
|---|---|
| Mod z drogą nad wodą na mapach Włoch, Niemiec, Holandii i innych był odrzucany: jego most „nie miałby podłogi”. | Budowany: most dostaje podłogę samej mapy. Jeszcze nie widziane w grze na tych mapach. |
| Mod dający jednostki graczowi w rozdziale kampanii (strona 0) był odrzucany, a jednostki dla stron komputera dostawały ostrzeżenie „mogą się nigdy nie pojawić”. | Budowany; ostrzeżenie dostaje tylko strona, której misja rozdziału nie ma. |
| Na M03_Italie i innych mapach nowa droga moda na otwartym terenie ukrywała z daleka scenerię mapy, a obiekty moda były widoczne tylko z bliska. | Daleki widok mapy zostaje taki, jaki był, a obiekty moda widać z daleka. Jeszcze nie widziane w grze. |

**0.4.1:** twój język od pierwszego startu i edytor zestawów modów, który znajduje mody po nazwie.

| Wcześniej | Teraz |
|---|---|
| Tworzenie zestawu modów pokazywało całą twoją bibliotekę z Utwórz na dole i bez sposobu, by znaleźć mod po nazwie. | Utwórz jest na górze, z modami, które już są w zestawie, zaraz pod nim; poniżej „Dodaj mody z biblioteki” z wyszukiwaniem, które zawęża listę w trakcie pisania. |
| Język był w Ustawieniach, więc gracze nie wiedzieli, że Launcher mówi w ich języku. | Pierwszy start pyta: „Wybierz język”, każdy język we własnych słowach, z zaznaczonym tym, na który twoja gra jest ustawiona w Steam (gracze po aktualizacji widzą to raz). Potem przycisk języka na górze, zawsze na widoku. |
| Lista zainstalowanych aplikacji Windows pokazywała pierwszą kiedykolwiek zainstalowaną wersję. | Pokazuje wersję, którą masz. |

**0.4.0:** uruchamia mody z nowymi drogami tak, jak buduje je Studio 0.9: wyglądają jak drogi samej mapy, z wysoka
i tuż przy ziemi (przetestowane w grze na D-Day).

![Nowa droga z bliska na D-Day](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Wcześniej | Teraz |
|---|---|
| Nowe drogi moda znikały z bliska. | Są rysowane asfaltem i naklejkami krawędzi samej mapy, malowane tak jak drogi mapy, a rośliny z ich trasy są usuwane. |
| Mod z wieloma okręgami usuwania budował się minutami. | Dużo szybciej. |

**0.3.3:** uruchamia mody zrobione w Studio 0.8.3.

| Wcześniej | Teraz |
|---|---|
| Mod z obróconą kamerą otwarcia (Studio 0.8.3) był odrzucany. | Budowany: kamera jest obrócona tak, jak mówi mod. |
| Kamera otwarcia przesuniętego punktu startowego zostawała w starym miejscu. | Kamera przesuwa się razem z nim; nowy punkt startowy dostaje własną kamerę. |
| Mod z punktem startowym w lesie był odrzucany. | Budowany: sztab tam działa. |

**0.3.2:** jedna kopia gry na cały PC, widoczna wersja i czytelniejsza biblioteka.

| Wcześniej | Teraz |
|---|---|
| Każdy zestaw modów budował własną kopię gry. | Jedna zmodowana kopia na cały PC, wspólna ze Studio. |
| Wersja nie była pokazywana, a Co nowego było listą. | Wersja jest obok nazwy, a Co nowego otwiera tabelę wcześniej/teraz taką jak ta. |
| Mapy i mody wyglądały w bibliotece tak samo. | Mapa ma plakietkę MAPA. |
| Mało podpowiedzi. | Podpowiedzi przy głównych kontrolkach. |
| Mody z nowymi drogami na Twilight of the Gods, Alpha, Ostfriesland i Robert nie dostawały modelu dróg mapy. | Też go dostają. |

**0.3.1:** mody z jednostkami z innej nacji (na przykład niemiecki Tiger dla USA) działają, nawet w meczu, w którym nikt
nie gra tą nacją (przetestowane w grze, 2026-10-02). I nowy wygląd: błękity R.U.S.E. zamiast czerni i złota, oraz nowe
logo: myśliwiec wznoszący się przez chmury. Pasek boczny ma dwie zakładki, **Zestawy modów** i **Biblioteka modów**,
każdą na całą wysokość, więc cała twoja biblioteka jest w zasięgu (połowa była schowana za paskiem przewijania), z
wyszukiwaniem i licznikiem. Instalator proponuje **czystą kopię zapasową gry** obok skrótu na pulpicie i mówi dlaczego.

**0.3.0:** **Obsługiwane mody:** Launcher pokazuje naszą listę modów
([sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods)); zaznacz te, które chcesz, a zostaną pobrane i
sprawdzone. Przy pierwszym uruchomieniu wybierasz swoje mody; mody z cheatami są trzymane osobno i nigdy nie są
zaznaczane za ciebie. Przycisk **Rozwiązywanie problemów** (dolny pasek i każdy komunikat o problemie) sprawdza za
jednym razem, co może zatrzymać **Graj**, i naprawia, co może, z raportem do wklejenia w zgłoszeniu błędu. **Czysta
kopia zapasowa gry** w Ustawieniach trzyma czystą kopię plików twojej gry i przywraca wszystko, co zmienił inny menedżer
modów (albo pozwala Steam to naprawić). Mody zrobione nowym Studio działają tak, jak je zrobiono: czołgi i piechota
przechodzą przez nowe mosty po pomoście, piechota idzie nowymi drogami, wycięte lasy są otwarte dla jednostek,
postawione budynki stoją na ziemi w każdym rozmiarze, a osłona trafia tam, gdzie ją namalowano, na D-Day i innych
mapach, które nie są kwadratowe. Znany problem: nowe drogi nie są jeszcze rysowane z bliska (widać je z daleka).

**0.2.11:** **Graj** działa za każdym razem: zmodowana kopia, której Windows nie chce usunąć (plik podlinkowany przez
starszą wersję, program, który wciąż go trzyma), jest odsuwana do `RUSE-Instances\.trash` zamiast zatrzymywać grę, a
gra wciąż uruchomiona z tej kopii jest podawana z nazwy. Mody z nowymi mostami nigdy nie tworzą terenu, do którego
jednostki nie mogą dotrzeć (to powodowało awarię gry).

**0.2.9:** **Graj** działa, gdy pliki twojej gry są oznaczone jako tylko do odczytu: kończyło się błędem „[WinError 5]
Access is denied”, gdy zmodowana kopia została w połowie zbudowana. Jeśli gra wciąż działa ze zmodowanej kopii,
dostajesz informację, by ją zamknąć, zamiast błędu Windows. Mody z nowymi drogami budują swoje malowane drogi i mosty.

**0.2.8:** dodany mod jest sprawdzany od razu, tak jak przeczyta go budowanie gry: uszkodzony plik mapy albo folder mapy
nazwany tytułem mapy (maps/Blitz zamiast maps/SuperCrossRoads4) jest wskazywany razem z poprawką, zanim Graj by się na
nim zatrzymało.

**0.2.7:** **Pomoc** i **Zgłoś problem** na dolnym pasku: wiki (podręcznik do grania w mody) i zgłoszenie błędu w twojej
przeglądarce z już wpisaną wersją Launchera. Komunikat o problemie ma własny link **Zgłoś**. Launcher niczego nie
wysyła: czytasz zgłoszenie i sam je publikujesz. Mody, których folder mapy jest nazwany tytułem mapy (maps/Blitz
zamiast maps/SuperCrossRoads4), dostają teraz podpowiedź, jak to naprawić.

**0.2.6:** przycisk **Ustawienia** (prawy górny róg): język, folder gry i aktualizacje w jednym miejscu, gotowe na
więcej.

**0.2.5:** wyszukiwanie aktualizacji jest solidniejsze: gdy GitHub odrzuci to jedno sprawdzenie przy starcie (pozwala
na 60 na godzinę na adres internetowy, wspólny dla wszystkiego, co z niego korzysta), Launcher czyta zamiast tego listę
wydań GitHuba.

**0.2.4:** twój język zostaje zachowany po ponownym uruchomieniu, aktualizacjach i ponownej instalacji.

**0.2.3:** czerwona ramka zwija się jak żółta (duży zestaw może wymieniać dziesiątki konfliktów).

**0.2.2: Ustaw w najlepszej kolejności.** Gdy mody w zestawie zmieniają te same wartości, żółta ramka ma przycisk
**Ustaw w najlepszej kolejności**: mody, które zmieniają więcej, idą pierwsze, a mniejsze po nich, więc każdy zachowuje
tyle swoich zmian, ile może. Mówi, które mody ratuje, a mody nadal można przesuwać ręcznie.

**0.2.1: mody, które do siebie nie pasują, nie mogą być uruchomione, a Launcher mówi dlaczego.** Gdy dwa mody w
zestawie zastępują ten sam plik lub skrypt, czerwona ramka wymienia te mody i to, co oba zmieniają, a Graj pozostaje
wyłączone, dopóki jeden nie zostanie usunięty. Gdy późniejszy mod tylko nadpisuje wartości wcześniejszego (na przykład
prędkość okrętu), żółta ramka je wymienia, a zestaw nadal działa.

**Nowe w 0.2:**

- **Zestawy modów tworzone w oknie:** nowy, edycja, zmiana nazwy, powielenie, usunięcie i ustawienie modów w kolejności.
  Koniec z ręczną edycją plików. Przewodnik w trzech krokach na pierwszym ekranie pokazuje drogę.
- **Dodaj plik moda…** (albo upuść go na okno): `.rusemod` wyeksportowany przez RUSE Studio, folder moda w `.zip` albo
  **`.rmod` z RUSE Mod Managera**, używany taki, jaki jest (stosowany przez własny silnik LittleGroove'a).
- **Udostępnij kolejność ładowania** jako tekst i **Importuj kolejność ładowania…** od znajomego: Launcher mówi, które
  mody masz, których brakuje, a które są w innej wersji, a potem tworzy zestaw. To ten sam tekst, który kopiuje i czyta
  RUSE Mod Manager, więc kolejności ładowania działają w obie strony.
- **Aktualizuje się sam:** od tej wersji, gdy wyjdzie nowszy Launcher, pasek o tym mówi; **Zaktualizuj** pobiera go,
  sprawdza jego SHA-256 i instaluje, a Launcher sam uruchamia się ponownie.

Twoje zestawy modów z 0.1 zostają zachowane. Problemy i pomysły: GitHub Issues.

![RUSE Launcher](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/launcher.jpg)
