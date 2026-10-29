**RUSE Studio, wersja zapoznawcza dla modderów.** Przeglądaj jednostki gry w dowolnym z jej dziesięciu języków,
zmieniaj je we własnym modzie i testuj go w grze. Twoja instalacja Steam nigdy nie jest zmieniana.

**0.9.8.9:** pobieranie na większej liczbie PC, i bezpieczniejsze wczytywanie obrazów.

- **Poprawione, zgłoszone przez gracza:** na PC, którego Windows nie ma certyfikatu, którym sprawdzane są pobrania z GitHuba, i nie może go pobrać, pobieranie się nie udawało („unable to get issuer certificate”). Pobrania Studio (jego aktualizacje, łatki gry, modele jednostek epok i tekstury online Map Paint) próbują teraz także z listą certyfikatów Firefoksa, którą Studio ma ze sobą.
- **Bezpieczniejsze obrazy:** biblioteka, którą Studio wczytuje obrazy (Pillow), ma teraz wersję 13.0.0, z poprawkami chroniącymi przed specjalnie spreparowanymi plikami obrazów, które mogły zawiesić aplikację, wyczerpać jej pamięć lub gorzej.
- **Staranniejszy kod:** 12 ostrzeżeń kontroli kodu GitHuba dla tego projektu zostało załatwionych. Gdy Studio pokazuje swoje strony w twojej przeglądarce, otwierają one tylko jego własne pliki, sprawdzane w sposób, który ta kontrola rozpoznaje; pobieranie wymaga TLS 1.2 lub nowszego, jak już wcześniej; a odczyt błędów dróg z nieudanego testu pozostaje szybki przy każdym komunikacie. Poza tym w działaniu Studia nic się nie zmienia.

**0.9.8.8:** ekran startowy i tablica budynków, własne budynki, RUSE Decoy do dźwięków i animacji, każda zasada gry w jednej zakładce, oraz R.U.S.E. 2.0 w złocie.

- **Ekran startowy:** kontynuuj swój mod, zacznij nowy albo go pomiń (także zawsze). Kroki nowego moda: jego nazwa, czy każda nacja zachowuje swoje jednostki, czy zaczyna pusta, badania (te z gry, żadne albo własne), tablica budynków, potem to, co mod zmieni. Widziane w grze.
- **Tablica budynków:** budynki każdej nacji jako rzędy jednostek, które oferują ich menu budowy, w kolejności gry. Wstaw jednostkę (własną nacji, kopię jednostki innej nacji, jednostkę epoki), przeciągnij ją wzdłuż rzędu albo do innego budynku, usuń ją albo każ ją badać od jednostki, pod którą stoi. Strona każdej jednostki mówi, gdzie jest budowana. Widziane w grze.
- **Dodaj budynek…:** kopia budynku z gry, która robi te same jednostki, albo budynek z własnymi jednostkami i własną zakładką na pasku budowy, do trzech na nację. Drugi i trzeci potrzebują małej łatki gry na więcej budynków: Studio pobiera ją raz i nakłada tylko na twoją zmodowaną kopię, nigdy na grę w twoim folderze Steam. Widziane w grze.
- **Własny wygląd budynku:** na stronie nowego budynku zaimportuj model 3D w miejsce jednej części wyglądu, który kopiuje (głównego budynku fabryki lub sztabu albo wybranej części), i daj mu własny obraz w menu budowy. Widziane w grze.
- **Importuj model… w zakładce Mapy:** model 3D (.glb, .gltf lub .3ds) staje się jedną z własnych skał, obiektów, roślin lub drzew twojej mapy, stawianą jak te z gry, z rozmiarem i podziękowaniem dla autora (modele innych: tylko CC0 lub CC-BY). Jednostki przewracają go jak te z gry; z zaznaczonym **Lity** omijają go. Widziane w grze.
- **RUSE Decoy, projektant dźwięku i animacji,** w miejsce zakładki Muzyka. Każdy dźwięk gry według rodzaju (broń z bliska i z daleka, trafienia, silniki, otoczenie, interfejs, karty podstępu, głosy jednostek, radio, kwestie misji z tym, co mówi każda, muzyka): odtwórz go, daj mu własną głośność (od 0 do 200%) albo go zastąp. Animacje: inny klip w miejsce klipu, klip wolniejszy lub szybszy, kość powiększona lub obrócona, albo motion capture na żołnierzach, z biblioteki 3205 darmowych ruchów (baza motion capture CMU i 100STYLE, z podziękowaniami), każdy pobierany, gdy go wybierzesz. Strona jednostki otwiera RUSE Decoy na jej własnych dźwiękach i animacjach. Widziane w grze. Jego komunikaty o błędach są na razie tylko po angielsku.
- **Ustawienia SI i graczy:** zakładki Ekonomia i SI są jedną zakładką. Ustawienia graczy: pieniądze i dochód, składy zaopatrzenia, produkcja i karty podstępu, jak wcześniej. Gracze komputerowi: każda z ich 47 wartości w zestawie domyślnym, na każdym poziomie trudności i przy każdej osobowości (wartość, której gra nie podaje w zestawie, pokazuje 0, które gra liczy). **Zasady gry:** 172 kolejne wartości gry w 16 grupach (bitwa i kapitulacja, populacja, ruch i drogi, ogień i cele, obrażenia, lasy i osłona, samoloty, karty podstępu w działaniu, stawianie budynków, rozgrywki rankingowe online, zarysy i efekty na ekranie, kolory graczy i sektorów z wybieraniem koloru, i inne), każda nazwana i wyjaśniona. Jeszcze nie testowane w grze.
- **Wszystkie wartości i pliki:** zakładki Wszystkie wartości i Pliki są jedną zakładką, z przełącznikiem u góry; otwiera się na części używanej ostatnio.
- **Poprawione:** Wszystkie wartości pokazywały liczby koloru w złej kolejności (gra trzyma niebieski pierwszy), więc kolor gracza 1, niebieski, wyglądał na pomarańczowy, a wpisanie czerwonego zmieniało niebieski. Kolory są teraz pokazywane i wpisywane od czerwonego; plik moda zachowuje kolejność gry, jak wcześniej.
- **Poprawione: ciemne i jasne plamy na mapach zrobionych przez Studio** (pustych, powiększonych, z rzeźbą terenu i z sektorami): nachylenie gruntu było źle zapisywane, więc trawa i pola były nierówno oświetlone. Mapa jest dobrze oświetlona, gdy zostanie zbudowana tą wersją (jej grunt jest robiony od nowa za pierwszym razem). Widziane w grze.
- **Usuwanie starych przejść (od DomesticNukes):** w drogach zakładki Mapy, przy włączonym **Usuń mosty z mapy**, **Zamknij przejścia po dawnych mostach** zamyka też grunt, gdzie każdy dawny most stał nad wodą, i przecina połączenia drogowe przez niego: nic już tam nie przechodzi; reszta sieci dróg zostaje. Jeszcze nie testowane w grze.
- **R.U.S.E. 2.0 w złocie:** zmodowana gra, którą buduje Testuj w grze, otwiera się sceną bitwy z uruchamianym silnikiem, a jej menu główne, mały tytuł każdego menu, obramowania menu i ekrany ładowania mówią R.U.S.E. 2.0 w złocie. Powstaje na twoim PC z plików twojej własnej gry za pierwszym razem (raz kilka minut, potem zachowane). Ustawienia mają pole, by zachować tytuł gry. Widziane w grze.
- **Litery gry:** Studio jest pisane czcionką menu gry, braną z twojej gry przy każdym starcie (czcionka nie jest dołączona do Studio).
- **Poprawione, zgłoszone przez moddera:** model zaimportowany na nową jednostkę zrobioną z Panthera lądował daleko od jednostki; na jednostkach zrobionych z 85 innych (155 mm GPF, SU-85, Carro Veloce, StuG III, M7 Priest...) siedział obok wieży. Studio czyta teraz dobrze, gdzie obracają się ich wieże. Model zaimportowany wcześniej zachowuje stare miejsce: użyj znów Importuj model… na tej jednostce. Jeszcze nie testowane w grze.
- **Poprawione, zgłoszone przez gracza:** model z obrazami JPG lub WebP (większość pobranych .glb) był odrzucany; teraz się importuje. Model, którego import wciąż nie umie odczytać (skompresowane siatki, obrazy KTX2), mówi to i jak to naprawić w Blenderze. Jeszcze nie testowane w grze.
- **Poprawione, zgłoszone przez gracza:** czołg z gry otwarty w Blenderze i zaimportowany z powrotem miał nieruchomą wieżę. Otwórz w Blenderze nazywa teraz kość każdej części tak jak gra, a import obraca część na kości wieży razem z wieżą. Model wyeksportowany wcześniej zachowuje stare nazwy: otwórz go znów w Blenderze. Jeszcze nie testowane w grze.
- **Nazwij swoją amunicję:** skopiowana amunicja nazywa się w grze tak, jak ją nazwiesz, a strona każdej amunicji ma **Jej nazwa w grze**: nowa nazwa lub rodzaj, we wszystkich językach naraz, potem jeden język osobno. Jeszcze nie testowane w grze.
- **Własne typy flag:** pod flagami jednostki **Utwórz lub zmień typy flag…** tworzy nazwany typ: zaznacz flagi gry, które włącza i wyłącza. Daj go dowolnej jednostce; zabierz go, a jej flagi wrócą do poprzednich. Zmień typ, a zmieni się każda jednostka, która go ma. Gra działa tylko na swoich flagach, więc typ łączy to, co one już robią. Jeszcze nie testowane w grze.
- **Prędkość pocisku dobrze wyjaśniona:** przewodnik liczb mówił, że prędkość pocisku, opór, przełącznik „bez fizyki” i czas przed wylotem to tylko wygląd. Decydują one, kiedy nastąpi trafienie: wolniejszy pocisk trafia później, a w ruchomy cel celuje się z wyprzedzeniem o czas lotu (z działania gry; jeszcze nie sprawdzone w teście).
- **Każdy błąd w dziesięciu językach:** 35 błędów Studio, które przyszły z importem modeli i tablicą budynków.
- **Podziękowania:** README mówi, co silnik LittleGroove'a wciąż robi w naszym, co jest nasze, i że nasz czytnik tekstur też używa kodeka ProLution.
- **Wciąż z błędami, używasz na własną odpowiedzialność:** tekstury Map Paint i obie puste mapy (Pusty teren i Pusty ocean).

**0.9.8.7:** Ponów i zaznaczaj to, co postawione, stawianie siatką / prostokątem / ścieżką, większe puste mapy, i każda wartość wyjaśniona.

- **Poprawione, zgłoszone przez moddera:** w nowej jednostce zrobionej z jednej z 17 jednostek gry (Królewski Tygrys, działa atomowe, V2...) pole zmiany modelu nigdy się nie pojawiało. Studio znajduje teraz te modele, a jeśli któregoś nie znajdzie, pole to mówi, zamiast znikać.
- **Zakładka SI wyjaśniona:** każda wartość graczy komputerowych mówi, co robi, w prostych jednostkach, i która liczy się w bitwie dla każdego poziomu trudności i profilu; tryby, poziomy, profile i jednostki wybierane po nazwie.
- **Każda wartość wyjaśniona, wszędzie:** Wszystkie wartości, zakładka Jednostki, pędzle zakładki Mapy (rozmiar w metrach, siła według tego, co robi) i zakładka Muzyka (kiedy gra każda lista bitewna).
- **Zakładka Ekonomia, Normalny i Nuklearny osobno:** tam, gdzie oba tryby się różnią, każdy ma własne pola. Zmiana tylko trybu Nuklearnego nie była jeszcze testowana w grze.
- **Ponów i zaznacz:** Ponów w każdym narzędziu mapy (Ctrl+Y lub Ctrl+Shift+Z, i przycisk); w panelach Budynki oraz Obiekty i drzewa zaznacz to, co postawione (klik, Shift+klik lub ramka), przeciągnij, obróć, zmień rozmiar lub usuń, także obiekty samej mapy.
- **Siatka, Prostokąt i Ścieżka:** rzędy obiektów w siatce lub prostokącie, budynki frontem do dróg, oraz żywopłoty, szpalery i pasy drzew wzdłuż ścieżki, z osłoną.
- **Większe puste mapy:** okno Rozmiar mapy nowej pustej mapy dodaje lub zabiera pasy terenu z każdej strony, a Utwórz sektory wypełnia ją sektorami.
- **Menu i wygoda:** wiersze liczb zamiast suwaków, wyszukiwanie z #tagami i ostatnimi wyszukiwaniami, wyskakujące karty, i klawisze do zmiany (Zamień, Weź, Anuluj).
- **Bezpieczniej:** zamknięcie z niezapisaną pracą najpierw pyta; mapa z nowym odciętym terenem jest odrzucana przed Testem w grze; mod zrobiony starszym Studio jest aktualizowany po kopii zapasowej (Zaktualizuj ten mod); zachowane wyniki budowania pozostają dobre po aktualizacji Studio.
- **Każdy komunikat w dziesięciu językach:** błędy Studio i wiersze budowania.
- **Nowa jednostka** pomija dwie jednostki bez modelu do startu (działo SOLO 57 mm i spadochroniarzy SOLO).
- Jeszcze nie testowane w grze: to, co postawione Siatką, Prostokątem i Ścieżką, przesunięte obiekty i większa mapa zrobiona w Studio.
- **Wciąż z błędami, używasz na własną odpowiedzialność:** tekstury Map Paint i obie puste mapy (Pusty teren i Pusty ocean).

**0.9.8.6:** każda flaga i każda liczba jednostek wyjaśnione, narzędzia mapy pokazują, co zrobiły, a puste mapy rysują się poprawnie.

- **Flagi jednostek wyjaśnione:** każda flaga na stronie jednostki pokazuje swoją nazwę, a po najechaniu widać, co robi, jak jej używać i jak bardzo jesteśmy pewni. **Przewodnik po flagach: wszystkie wyjaśnione** wymienia wszystkie 105, z wyszukiwaniem. Studio sprawdza flagi jednostki: znany crash (flagi ciężarówki na czymś, co nie jest ciężarówką, uzbrojony samolot z flagą zwiadu bez flagi myśliwca) pokazuje swoją poprawkę, a Studio nie uruchomi gry, dopóki nie zostanie poprawiony; flagi, które mogą zepsuć jednostkę, dają ostrzeżenie.
- **Każda liczba wyjaśniona:** najedź na nazwę dowolnej liczby jednostki lub budynku, by zobaczyć, co znaczy; obok jej wartość w prostych jednostkach (metry, km/h, sekundy, stopnie, $, %), suwak, który robi ją mniejszą lub większą od wartości z gry (jej wartości bazowej, od -90% do +300%), i gdzie wypada wśród jednostek gry tego rodzaju. Prędkości są w km/h samej gry.
- **Jak działają broń i amunicja**, krok po kroku, w ramce Broń.
- **Narzędzia mapy pokazują, co zrobiły:** Osłona, Odsłoń, Miasto, Las, Blokuj i Otwórz zaznaczają teren, po którym przeszło każde pociągnięcie, i mówią, ile m² zmieniło się dla jednostek, albo że nic się nie zmieniło. Miasto działa w prawdziwych metrach i najpierw otacza budynki, które obejmie kliknięcie.
- **Stawianie:** postawione budynki, drzewa i obiekty pokazują swoje prawdziwe modele (z kropką u stóp); wybrany widać półprzezroczyście pod kursorem przed kliknięciem; lista do stawiania to siatka obrazków. Drzewa nie są już czarne, a numery sektorów chowają się, gdy kamera jest blisko.
- **Puste mapy** (widziane w grze na Pustym terenie): cienie na płaskim terenie; to, co postawisz tam, gdzie kopiowana mapa miała morze, jest rysowane; podłoga kamery idzie za nowym terenem.
- **Wciąż z błędami, używasz na własną odpowiedzialność:** tekstury Map Paint i obie puste mapy (Pusty teren i Pusty ocean).

**0.9.8.5:** samoloty w dowolnej roli, broń trafiająca samoloty i biblioteka dla pędzla Tekstura w Map Paint.

- **Rola samolotu** (zgłoszenie gracza: myśliwiec-bombowiec, któremu dano bomby dywanowe bombowca, leciał do celu i niczego nie zrzucał): nowe pole Rola na stronie samolotu robi z niego Myśliwiec, Myśliwiec-bombowiec, Bombowiec lub Zwiadowcę. Razem z nią zmienia się jego zachowanie, to, jak używają go gracze komputerowi, i jego słowa w menu budowy. Bomby bombowca trafiają do komory bombowej (skopiowanej z bombowca z gry), bo tylko z niej zrzuca je nalot bombowca. Sprawdzone w grze: myśliwiec-bombowiec zmieniony w bombowiec zrzuca bomby; zwiadowca, który zachowuje broń (Stuka, ME109), nadal atakuje i ma zasięg widzenia zwiadowców.
- **Pojazdy rozpoznawcze:** pole Rola pojazdu naziemnego robi z niego Rozpoznanie: zasięg widzenia samochodów rozpoznawczych (dużo dalej niż czołgu), to, jak używają ich gracze komputerowi, ich słowa w menu budowy, i może wjeżdżać do lasów (sprawdzone w grze z Panzerem IV).
- **Co trafia broń:** Trafia przy każdej broni wybiera ziemię, samoloty albo jedno i drugie (druga broń obok, tak jak działa przeciwlotnicze w grze mają po jednej na każde). Sprawdzone w grze: pociski czołgowe strzelające do samolotów. Znane: broń samolotu ustawiona tylko na ziemię jeszcze nie zadaje obrażeń.
- **Pędzel Tekstura w Map Paint dostaje bibliotekę:** tekstury terenu z gry (trawa, pola, piasek, śnieg, skały, drogi..., według teatru działań, z wyszukiwaniem), kwadrat terenu dowolnej mapy, własne obrazy i darmowe obrazy z internetu (Poly Haven i ambientCG, CC0; zdjęcia lotnicze USA, domena publiczna), jeden obraz pobierany na kliknięcie i zapisany w twoim modzie z informacją o autorze. Suwak Rozmiar, ostatnio używane tekstury i **Detal gry z bliska**, który kładzie własne naklejki gry dla tekstury z gry na malowanym terenie. Jeszcze niesprawdzone w grze; pobieranie z internetu jeszcze niewypróbowane.
- **Obiekty postawione w otwartym terenie**, z dala od miast, gospodarstw i lasów mapy, są teraz w zasięgu rysowania gry, a duże grupy nowych obiektów są ułożone tak jak w grze (jeszcze niesprawdzone w grze).
- **Szybsze ponowne malowanie:** pomalowany teren jest zachowywany między budowaniami, niezależnie od tego, która kopia lub mod go pomalowały: mapa pomalowana tak samo odzyskuje go w kilka sekund, a nie minut.
- **Wciąż z błędami, używasz na własną odpowiedzialność:** tekstury Map Paint i obie puste mapy (Pusty teren i Pusty ocean).

**0.9.8.4:** własne misje, puste mapy do zabudowania i dużo więcej do dostosowania.

- **Wciąż z błędami, używasz na własną odpowiedzialność:** tekstury Map Paint i obie puste mapy (Pusty teren i Pusty ocean).
- **Własne misje:** nowa Operacja lub nowy rozdział kampanii ma własną misję po stronie Scenariusz ekranu mapy: strony, cele, zdarzenia (Gdy → Zrób: sprowadź jednostki, ruch, atak, utrzymanie strefy, artyleria, bombardowanie, spadochroniarze, komunikaty, pieniądze, zwycięstwo, porażka) i ruchy kamery. Sprawdzone w grze: jej ruch kamery, cele (strefa, zniszczona grupa, czas), powtarzane zdarzenia, pieniądze, strona oddana komputerowi. Jeszcze nie testowane: spadochroniarze, ruch kamery uruchamiany przez zdarzenie.
- **Mapa | Scenariusz** na ekranie mapy: rzeczy z drugiej strony są przygaszone i nie da się ich chwycić przez przypadek.
- **Puste mapy:** nic ze skopiowanej mapy już się nie pokazuje, a sztab każdego gracza stawiasz sam (budowanie czeka, aż wszystkie będą postawione). Pusty teren działa też dla Operacji i rozdziałów kampanii.
- **Własne sektory:** maluj je, przeciągaj ich narożniki, narysuj nowy jako prostokąt, zostaw teren bez sektora, usuń sektor (sprawdzone w grze).
- **Składy zaopatrzenia:** karta Ekonomia daje każdemu składowi na każdej mapie albo na jednej mapie więcej ciężarówek (razy albo liczba na każdy); koniec z limitem 1000 ciężarówek.
- **Karta Narody:** ukryj naraz wszystkie jednostki narodu, pokaż je z powrotem albo wypełnij jego menu jednostkami z epoki.
- **Edytuj zainstalowany mod:** otwórz dowolny mod z Launchera; cudzy staje się twoją kopią pod własną nazwą. Mody RUSE Mod Manager (.rmod) są konwertowane, żeby można było zmieniać ich wartości.
- **Sprawdzanie moda prostymi słowami**, z przyciskiem naprawy przy każdym problemie.
- **Własny wygląd jednostki:** jej własna kopia modelu do przemalowania; oddziały noszą domyślny mundur albo własny; wybierz ciężarówkę, którą jedzie oddział lub działo. Piechota pokazuje się w 3D i otwiera się w Blenderze.
- **Pancerz** wybiera się spośród poziomów gry, więc karta pokazuje to, czym jednostka walczy; **importowane samoloty** zachowują kręcące się śmigła i wracają skierowane do przodu (oba sprawdzone w grze).
- **Rozmiary modeli na suwaku** (Malutki, Rozmiar gry, Rzeczywisty, Ogromny: od 0,05 do 20), do zmiany w każdej chwili, wszystkie samoloty naraz.
- **Więcej do zmiany:** własna wartość poziomu trudności lub profilu SI dla takiej, którą ma tylko Domyślny; liczby poza zakresem suwaków narzędzi mapy; głośniejsze i dłuższe edycje muzyki.
- **Naprawione:** jednostka pokazana w menu, ale badana z ukrytej, zatrzymywała grę: sprawdzanie ją wskazuje, a budowanie ją odrzuca. Czołgi znów strzelają nad usuniętymi miastami, a jednostki nie wpadają już w dziury w miejscach usuniętych mostów (sprawdzone w grze).
- **Pobieranie działa na każdym komputerze:** gdy Windows nie pobrał jeszcze certyfikatu, którym sprawdzany jest GitHub, Studio prosi o niego Windows, tak jak przeglądarka, i próbuje ponownie (jeszcze nie wypróbowane na komputerze z tym problemem).

**0.9.8.3:** kopie z modami trafiają tam, gdzie wskażesz.

- **Gdzie trafiają kopie z modami**, w Ustawieniach: wybierz folder, w którym budowana jest kopia gry z modami, albo
  wróć do zalecanego miejsca, `RUSE-Instances` na dysku gry (tam kopia dzieli pliki z grą i jest gotowa w kilka sekund;
  na innym dysku jest pełną kopią gry, wolniejszą i większą). Czysta kopia zapasowa gry trafia obok. Następne Testuj w
  grze buduje w nowym miejscu; stary folder można usunąć ręcznie. Launcher używa tego samego folderu.

**0.9.8.2:** przychodzą jednostki z innych epok: ich modele, w prawdziwej wielkości, za badaniem.

- **Jednostki z innych epok:** epoki WWI, WWII+, Zimna wojna i Współczesność w karcie Jednostki mają teraz swoje
  jednostki: 366, każda na darmowym modelu innego autora (CC0 lub CC BY), podpisanym. Każda epoka pobiera się w
  Studiu, gdy ją wybierzesz, z naszego GitHuba (każdy plik sprawdzony: WWI 232 MB, WWII+ 198 MB, Zimna wojna 996 MB,
  Współczesność 709 MB), i aktualizuje się sama, gdy kolejne są gotowe.
  - **W prawdziwej wielkości:** prawdziwa szerokość każdej jednostki (u samolotu rozpiętość skrzydeł) w skali gry; do
    zmiany od 0,2 do 5 razy.
  - **Badane jak jednostki gry:** z dowolnej jednostki budynku jej nacji, także z jednostek epok moda, więc działa
    łańcuch (T-80, potem T-90M), z ceną i czasem badania. Jednostki WWI i WWII+ można kupić od razu; te z Zimnej
    wojny i Współczesności zaczynają jako badane z odpowiedniej jednostki.
  - **Własne karty** w menu budowy i przy zaznaczeniu.
  - Sprawdzone w grze: wczytują się od razu, karty badań i łańcuch, Land Rover z własnym modelem, rozmiary. Jeszcze
    nie sprawdzone: działa holowane (na razie nie ma działa z gry, do którego można je dopasować).
- **Importuj model…:** model zaczynający się od figury załogi dostaje teraz własny model (jeepy skopiowane z
  Kübelwagena pokazywały Kübelwagena); modele malowane metodą specular-glossiness zachowują malowanie; kolory podane
  liczbami nie są już czarne; duże modele importują się szybciej.
- **Jednostka badana z jednostki innej armii** zostawiała grę na niekończącym się ekranie wczytywania: **Nowa
  jednostka…** usuwa teraz to powiązanie, a budowanie odrzuca jednostkę badaną z brakującej jednostki lub z jednostki
  innej nacji, mówiąc dlaczego i jak to naprawić.
- **Usuwanie jednostki, z której badane są inne:** wybierz w **Ustawienia > Badania**, czy najpierw ostrzec
  (domyślnie), odmówić, czy połączyć je ponownie z jej własnym poprzednikiem; jednostka wskazująca na usuniętą
  pokazuje to na swojej stronie i w sprawdzaniu. Czasy badań wpisuje się w sekundach lub minutach (że gra liczy je w
  sekundach, nie sprawdzono jeszcze w grze).
- **Linux i Steam Deck (przez Protona):** Studio otwiera się w twojej przeglądarce, gdy jego własne okno nie może.
  Jeszcze nie sprawdzone na Linuksie: daj nam znać, jak poszło.

**0.9.8.1:** Narzędzia LittleGroove'a trafiają do Studia, a z nimi muzyka i dźwięki oraz nacja zmieniona w inną.

- **Narzędzia LittleGroove'a, przeniesione** z jego RUSE-Mod-Managera:
  - **Karta Ekonomia:** pieniądze na start i dochód, składy zaopatrzenia oraz karty podstępu, z którymi startuje każda
    strona. Sprawdzone w grze: pieniądze na start i karty na start.
  - **Karta SI:** jak grają gracze komputerowi, jakie jednostki wolą i karty podstępu; a także skrypty map i misji gry,
    pokazane jako Python, tylko do odczytu. Sprawdzone w grze.
  - **Pole Ulepszenie** na stronie jednostki: jednostka, której jest ulepszeniem, jej własne ulepszenia, cena i czas
    badania.
  - **Karta Wszystkie wartości:** dowolny obiekt lub wartość gry, zmienione w modzie: dodać lub usunąć
    wartość, utworzyć lub usunąć obiekt, nadać wartości tekstowej własne słowa.
  - **Karta Pliki:** dowolny plik z paczek gry, do obejrzenia i zapisania. Zamień jeden na własny plik albo dodaj nowy:
    twój mod zachowuje tylko zmiany, każda sprawdzona według rodzaju.
  - **Misje:** zmienić skrypty misji; sprawdzić, czy jest w menu, czy ładuje się każdy potrzebny plik, i jej teksty;
    przesunąć ją w górę lub w dół w jej menu.
  - **Mapy:** nazwy miast i wzgórz, nazwane punkty i strefy, nazwa i obrót obiektu na mapie. **Notatki** o jednostce,
    wartości lub graczu komputerowym.
- **Karta Muzyka:** każdy utwór według miejsca, w którym gra, każdy zamieniany w małym edytorze w Studiu (cięcie,
  wyciszanie, głośność); nowe utwory dodane do list bitewnych; kwestie jednostki na jej stronie; dźwięk tła mapy.
  Sprawdzone w grze: utwory, nowe utwory i kwestie.
- **Zrób z jednej nacji inną.** Nowa karta **Nacje** daje jednej z siedmiu nacji gry nową nazwę (w lobby i dla jej
  armii) oraz nową flagę z dowolnego obrazu: na przykład Chiny w miejsce Włoch. Jej jednostki i to, co mówią,
  zmienia się jak dotąd, w karcie Jednostki i na stronie każdej jednostki. Sprawdzone w grze: nowa nazwa w lobby,
  nowa flaga w meczu.
- **Jednostki z innych epok:** karta Jednostki oferuje epoki WWI, WWII+, Zimna wojna i Współczesność obok jednostek
  gry. Nie mają jeszcze jednostek: przyjdą w jednej z kolejnych aktualizacji.
- **Nowa mapa: od zera…** jest w karcie Mapy, zanim otworzysz jakąkolwiek mapę.
- **Grunt Pustego terenu jest rysowany jako własny.** Nowa mapa zaczęta od zera ma grunt zrobiony z twoich pociągnięć
  terenu, a nie przesunięty grunt mapy z gry: okrągłe brzegi z bliska i z góry, bez wgnieceń na szczytach wzgórz, a
  budynki i czołgi stoją dokładnie na nim. Sprawdzone w grze na mapach testowych.
- **Pusty ocean zostaje, z ostrzeżeniem** na swoim przycisku: osobne wyspy nie są gotowe do pełnych bitew
  (niżej).

Jeszcze nie sprawdzone w grze: pole Ulepszenie, Wszystkie wartości, Pliki, narzędzia misji, dodatki do map
i dźwięki tła.

**Dlaczego nie ma jeszcze map morskich.** Wypróbowaliśmy mapy z wyspami do pełnych bitew z okrętami i przeszkadza
sama gra:

- Jednostka lądowa wysłana na wyspę, do której nie może dotrzeć, powoduje awarię gry.
- Połączenie wysp pasem lądu zapobiega awarii, ale wtedy komputer po prostu wysyła nim swoją piechotę.
- Bez drogi między wyspami nigdzie nie da się postawić budynku.
- Z bronią z gry okręty i jednostki lądowe ledwo mogą sobie nawzajem zaszkodzić.

Same dane mapy nie naprawią awarii, więc mapy morskie czekają.

**0.9.8:** nowa mapa może zacząć się pusta, jako płaski ląd albo otwarte morze, a każda mapa może mieć własne obrazy w
menu gry.

- **Zacznij mapę od pustej.** **Duplikuj mapę** ma nowy wybór, **Zacznij od**: **Pusty teren** (płaski ląd, na którym
  nie ma nic poza punktami startowymi) albo **Pusty ocean** (morze na całej mapie). Sprawdzone w grze.
- **Obrazy w menu dla każdej mapy.** Wybierz plik PNG na obraz mapy i jej mapę 3D w menu albo wróć do tych z gry;
  białe punkty startowe są rysowane tam, gdzie zaczynają gracze mapy. **Zrób w Blenderze…** otwiera własny model 3D
  mapy, żeby je zrobić, a **Przenieś** umieszcza je w twoim modzie. Sprawdzone w grze.

| Wcześniej | Teraz |
|---|---|
| Nowa mapa zaczynała się jako pełna kopia mapy z gry. | **Duplikuj mapę** może zacząć ją od pustej: Pusty teren albo Pusty ocean. |
| Nowa mapa pokazywała obrazy w menu kopiowanej mapy. | **Obrazy w menu…** daje jej własne: twój plik PNG albo obraz zrobiony w Blenderze, z punktami startowymi tam, gdzie zaczynają jej gracze. |
| Składy, jednostki, budynki i nazwy mapy zostawały. | **Usuń** usuwa jeden element albo wszystkie składy lub wszystkie nazwy naraz (sprawdzone w grze). |
| Drogi i mosty mapy zostawały. | Panel Drogi je usuwa (linie dróg znikają: sprawdzone w grze). |
| Sektory pomijały morze i krawędzie mapy. | **Sektory na całej mapie**: można zająć całą mapę (sprawdzone w grze). |
| Woda na mapie pochodziła tylko z jej rzek i morza. | **Woda na całej mapie**: cienka warstwa, jak namalowane morze na mapie morskiej (sprawdzone w grze; jednostki pod nią jeszcze nie sprawdzone). |
| Edytor mapy wybierał miejsca pojawiania pojedynczo, po nazwach kodowych. | Przeciągnij ramkę, żeby zaznaczyć je jak w grze; własne ikony mapy pokazują, co jest zaznaczone i ile. |
| Panele edytora mapy miały jeden rozmiar. | Każdy pływający panel zmienia rozmiar, od 40% do 125%. |
| Nowości były tylko po angielsku. | Są w języku Studia. |
| Wysłanie moda na listę modów oznaczało ręczne pisanie jego wpisu. | **Opublikuj na liście modów** otwiera formularz listy, już wypełniony, z kopią .zip gotową do przeciągnięcia; każdy eksport mówi, że zrobiono go w RUSE Studio. |
| Importuj model gubił własne cieniowanie i przezroczyste części modelu. | Zachowuje je i mówi, co zachował (jeszcze nie sprawdzone w grze). |
| Jednostka zbudowana na osuszonym morzu mogła zawiesić grę; stara woda rzek stała jak ściany wzdłuż krawędzi mapy; usunięte latarnie morskie wciąż świeciły nad morzem. | Naprawione, każde sprawdzone w grze. |

Znane: **mapy morskie nie są skończone.** Pusty ocean buduje się i działa w grze, ale jednostki pod jego wodą nie
zostały jeszcze sprawdzone.

**0.9.7:** bardzo duże mody map budują się teraz w kilka minut. Wcześniej ich budowanie trwało bardzo długo i dlatego
ta aktualizacja była potrzebna. A **Eksportuj mod…** zabiera ze sobą to, co wyliczyło budowanie, więc pierwsze
budowanie takiego moda u gracza jest krótsze.

- **Najbardziej ekstremalny mod mapy, jaki mamy** (mapa „D-Day” z osuszonym morzem: 154 pociągnięcia wyrównania,
  135 pociągnięć malowania, 33 385 usuniętych budynków) budował się około czterech godzin. Teraz buduje się w **mniej
  niż 10 minut**, bez zachowywania czegokolwiek z wcześniejszego budowania, a pliki gry wychodzą takie same. Zajęło nam
  to około 15 godzin; gdzie się zacinało i dlaczego: [Jak tu doszliśmy](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here)
  (po angielsku). Wciąż pracujemy nad tym, by było szybciej.

| Wcześniej | Teraz |
|---|---|
| Mapa przekształcona na przestrzeni kilometrów mogła budować się godzinami, wyczerpać pamięć komputera albo zostać odrzucona jako zbyt duża dla ruchu na mapie. | Jej teren jest przekształcany w kilka sekund, koryta rzek naprawiane, a teren malowany na wszystkich rdzeniach komputera, zaś ruch wyliczany na dwóch kolejnych, gdy teren jest malowany. Każdy krok daje te same pliki co wcześniej. |
| Osuszone morze pozostawało zamknięte dla jednostek. | Szerokie suche dno dostaje strefy ruchu tak duże, na ile pozwala miejsce. **Jeszcze niesprawdzone w grze:** jednostki na otwartym morzu. |
| Przebudowa po małej zmianie wyliczała dużą mapę od nowa. | To, co zrobiono, zostaje: niezmienione malowanie zajmuje pół sekundy, niezmieniony ruch pochodzi z pamięci podręcznej budowania, a nowe pociągnięcie przemalowuje tylko kafelki, do których sięga. |
| Pierwsze budowanie dużego moda mapy u gracza wyliczało wszystko od nowa. | **Eksportuj mod…** zapisuje w modzie to, co budowanie wyliczyło dla ruchu na mapie (`maps/<map>/solved.bin`). Jest to powiązane z plikiem gry dla tej mapy i nie zawiera żadnych plików gry. Budowanie gracza to wykorzystuje, sprawdza każdą odpowiedź i daje te same pliki. Malowanie terenu i koryta rzek wciąż powstają na każdym komputerze. |
| Importuj model pojawiał się tylko na stronie nowej jednostki: trudno go było znaleźć. | Karta Jednostki zaczyna się od dwóch przycisków: **Zmień jednostkę** i **Nowa jednostka (import modelu)**. Wybierz jednostkę wyjściową, nazwij ją, Utwórz: jej strona otwiera się przy Importuj model. Strona jednostki z gry ma **Nowa jednostka z tej…**. |
| Flaga okrętu (76) mówiła, że jednostka z nią porusza się po wodzie. | Mówi, że jednostka w ogóle się nie porusza, jak budynek (jeszcze niesprawdzone w grze). |

Znane: **mapy morskie nie są jeszcze dopracowane.** Osuszone lub pomalowane morze buduje się i wczytuje, ale woda wciąż
jest widoczna.
