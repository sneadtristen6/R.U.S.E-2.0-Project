**RUSE Studio, wersja zapoznawcza dla modderów.** Przeglądaj jednostki gry w dowolnym z jej dziesięciu języków,
zmieniaj je we własnym modzie i testuj go w grze. Twoja instalacja Steam nigdy nie jest zmieniana.

**0.9.8.10:** RUSE Guard, nasz anty-cheat do prawdziwych gier wieloosobowych; Bug Watch, raporty o awariach i użyciu, które możesz włączyć; logowanie przez Steam; i umowa przy pierwszym uruchomieniu.

- **Umowa przy pierwszym uruchomieniu:** gdy Studio lub Launcher otwiera się po raz pierwszy, mówi, co robi RUSE Guard, i prosi o jego zaakceptowanie (to konieczne, by grać online z aplikacjami), czy włączyć Bug Watch (opcjonalnie), oraz o nazwę użytkownika, którą nasi programiści widzą przy twoich raportach: dodawane są # i cztery cyfry, by była niepowtarzalna, jak Nick#4821. Jedna nazwa działa w obu aplikacjach. Umowa pokazuje się znów, gdy się zmieni. Widziane w obu aplikacjach. Jej tekst jest na razie po angielsku; pozostałe języki nadchodzą.
- **RUSE Guard:** nasz anty-cheat, według projektu DomesticNukes. Działa tylko w grach wieloosobowych i kooperacyjnych, nigdy w grze jednoosobowej, w potyczce z komputerem, w kampanii ani gdy robisz mody. Zmodowana kopia zbudowana z kodem (cheatem) lub narzędziem testowym służy tylko do gry offline: sama opuszcza gry wieloosobowe i kooperacyjne. W prawdziwej grze porównuje nazwy uruchomionych programów z listą znanych narzędzi do oszukiwania (tylko nazwy; nic więcej nie jest odczytywane), a to, co zbierze z gry, trafia pod twoją nazwę użytkownika, nigdy pod twoje konto Steam. Testuj w grze buduje z nim swoje kopie. Przetestowane w grach wieloosobowych z prawdziwym przeciwnikiem; dowody docierają na nasz serwer.
- **Bug Watch (opcjonalnie):** gdy go zaznaczysz, Studio i Launcher liczą, czego używasz i kiedy coś idzie nie tak, awarie aplikacji i gry, z tym, które mody były włączone, i raz dziennie wysyłają to naszym programistom z twoją nazwą użytkownika. Bez prawdziwych nazwisk, bez konta Steam, bez plików. Wyłączony, dopóki go nie zaznaczysz; odznacz go kiedy chcesz, a to, co było przechowywane, zostanie usunięte. Widziane w obu aplikacjach.
- **Logowanie przez Steam:** logowanie na własnej stronie Steam w twojej przeglądarce potwierdza, że posiadasz R.U.S.E., do gry online, RUSE Guard i pobierania zawartości. Nigdy nie widzimy twojego hasła, a twój identyfikator Steam nigdy nie jest zapisywany: tylko przepustka przechowywana na twoim komputerze przez 30 dni. Studio pyta raz; Ustawienia Launchera otwierają to w każdej chwili. Nic tego jeszcze nie wymaga. Jeszcze nie wypróbowane w aplikacjach.

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

**0.9.6:** nowa jednostka może mieć własny model 3D, z dowolnego programu 3D, a **Testuj w grze** startuje od razu, gdy
nic się nie zmieniło. I pierwszy raz:

- **Pierwszy model z innego programu 3D w R.U.S.E.:** M1 Abrams, zrobiony jako nowa jednostka USA obok Shermana. Kupuje
  się go w Armor Base z własną kartą, jest budowany i obraca wieżę jak czołgi z gry. Widziane w grze.

| Wcześniej | Teraz |
|---|---|
| Nowa jednostka miała model jednostki, którą kopiuje. | **Importuj model…** na stronie nowej jednostki: wybierz **.3ds** (z obrazami obok niego albo w folderze wyżej) lub **.glb** (z Blendera i większości narzędzi 3D). Studio dopasowuje go do jednostki, którą kopiuje: jego długość (razy **Rozmiar**: 1 to tak samo długi, Abrams względem Shermana to 1,36), jego wieżę na wieży tej jednostki, żeby gra obracała ją tak samo, jego obrazy jako jego własne tekstury. Strona pokazuje go w 3D; **Użyj modelu kopiowanej jednostki** znowu go usuwa. Trafia do twojego moda jako `files/models/<the unit's name>.glb`, który otwiera się w Blenderze. **Widziane w grze.** Wczesna wersja: gąsienice i koła jeszcze się nie obracają, błysk działa pokazuje się tam, gdzie jest wylot lufy kopiowanej jednostki, a wrak jest wrakiem kopiowanej jednostki. |
| Nowa jednostka z własną kartą powodowała awarię gry, gdy była budowana (0.9.5). | Jej karta jest tam, gdzie gra czyta ją także na mapie. **Widziane w grze.** |
| Mapy zrobionej przez **Duplikuj mapę** nie dało się usunąć w Studio. | **Usuń mapę**, pod Duplikuj mapę na nowej mapie: pyta raz, potem jej folder trafia do Kosza, skąd możesz go odzyskać. Map samej gry nie da się usunąć. |
| Studio mówiło, że Blender nie jest zainstalowany, jeśli był rozpakowany, a nie zainstalowany. | Znajduje Blendera wszędzie, gdzie go rozpakowałeś (główny folder dysku lub jeden niżej, Pobrane, Pulpit, Dokumenty). |
| Przemalowania wychodziły z niektórymi kolorami trochę nie takimi (czerwono-niebieska łata mogła zrobić się fioletowa). | Każda łata 4 x 4 zachowuje własne kolory. Przemalowane jednostki i pomalowany teren wychodzą z nieco innymi danymi obrazu niż w 0.9.5 (ten sam wygląd), więc odcisk i kod dołączenia takiego moda się zmieniają: wszyscy gracze powinni zaktualizować przed wspólną grą. |
| **Testuj w grze** za każdym razem budowało od nowa całą zmodowaną kopię, nawet gdy nic się nie zmieniło. | Nic się nie zmieniło od ostatniego budowania: gra startuje od razu, bez budowania (testowy mod: z 21-29 s do mniej niż 0,1 s). Budowanie używa ponownie niezmienionych plików ostatniej kopii zamiast kopiować je jeszcze raz. |
| Każde budowanie wczytywało dane jednostek gry od nowa. | Są zachowywane między budowaniami: duży testowy mod zajmował za każdym razem 213 s; teraz pierwsze budowanie trwa mniej więcej tyle samo, a kolejne 68 s. Gra nie kopiuje już wszystkich swoich danych przed budowaniem. |
| Usunięcie większości dużej mapy wyczerpywało pamięć Studio, a usunięcie całej mapy było odrzucane jako zbyt duże. | Usuwanie jest przeliczane w kilka sekund, jedno po drugim; **Wyczyść całą mapę** w panelu Usuń (Cofnij to wycofuje). Usunięta sceneria jest zapisywana zwięźle. Nowe: jeszcze nie widziane w grze na dużą skalę. |
| Teren spłaszczony pod drogą zostawiał drogę w dalekim widoku na starej wysokości. | Model drogi idzie za nowym terenem. Nowe: jeszcze nie widziane w grze. |
| Spłaszczone koryto rzeki zachowywało z bliska obrazy skał i wąwozu. | Jest wypełniane od obu brzegów, a jego niska osłona usuwana. Nowe: jeszcze nie widziane w grze tak, jak robi to budowanie. |
| Gdy budował się indeks gry (około minuty), Studio mogło tylko czekać. | Mapy i Ustawienia pozostają dostępne; wiersz na dole mówi, kiedy jest gotowy. |
| Powolny start nie zostawiał żadnej wskazówki. | Kroki każdego startu są mierzone w czasie; **Kopiuj raport** w Rozwiązywaniu problemów wymienia ostatnie pięć. |
| Strona okna mogła sięgnąć do większej części aplikacji niż jej własne wywołania. | Dostaje tylko własne wywołania aplikacji. |

Do tego `ruse import-model <file> --like <model> --unit <name>` robi to samo z wiersza poleceń.

**0.9.5:** jednostki dostają własny wygląd. Zobacz dowolną jednostkę w 3D, przemaluj ją w Blenderze, daj jej własną kartę
w menu budowy. I nasze pierwsze razy, wszystkie widziane w grze:

- **Pierwsza jednostka przemalowana przez mod:** czerwony Sherman, z bliska i z daleka.
- **Pierwsza jednostka pomalowana w Blenderze** i przeniesiona z powrotem do gry.
- **Pierwsza karta menu budowy zrobiona w Studio,** pokazana we własnym menu Armor Base gry.
- **Pierwsza nowa jednostka z własnym modelem,** obok tych z gry: Tall Sherman, obok Shermana (zrobiony w testach;
  robienie własnych modeli w Studio jest następne).
- **Pierwsza własna misja** rozegrana do zwycięstwa: nowa Operacja z własnymi celami, jednostkami i uderzeniem artylerii
  (zrobiona w testach).

| Wcześniej | Teraz |
|---|---|
| Strona jednostki pokazywała tylko jej wartości. | **Model 3D** na stronie jednostki: obracaj go, przybliżaj, zobacz na nim farbę swojego moda. |
| Wygląd jednostki był taki jak w grze. | **Przemaluj w Blenderze:** **Otwórz w Blenderze** otwiera modele jednostki z ich obrazami; maluj na modelu, potem **Przenieś** zapisuje twoje malowanie i umieszcza je w twoim modzie. **Widziane w grze**, z bliska i z daleka. Blender jest darmowy: jeśli Studio go nie znajdzie, **Pobierz Blendera (za darmo)** i **Wybierz Blendera…** są tuż obok. |
| Obraz jednostki w menu budowy był taki jak w grze. | **Użyj tego widoku jako karty:** obracaj i przybliżaj model 3D, aż dobrze wygląda w przerywanej ramce; ten widok staje się kartą jednostki w menu budowy. **Widziane w grze.** |
| Nowa jednostka pokazywała tę samą kartę co jednostka, którą kopiuje, więc obie wyglądały w menu tak samo. | Karta nowej jednostki jest jej własna (`files/cards/<the unit's name>.png`): zrobienie jej karty nigdy nie zmienia karty oryginału. Jeszcze nie widziane w grze. |
| Paczka modeli jednostek, która urosła, była odrzucana przez grę, a każdego modelu z niej brakowało: awaria przy pierwszej fabryce. | Paczki modeli są zapisywane tak, jak gra je sprawdza, bez względu na rozmiar. **Widziane w grze:** drugi Sherman z własnym modelem. |
| Jednostki nacji dane innej armii nie miały modelu w rozdziałach kampanii i Operacjach: mod sprowadzający francuskie jednostki na mapie Holandii powodował awarię podczas wczytywania. | Ich modele wczytują się także tam. **Widziane w grze** (francuskie jednostki na Colditz). |
| **Duplikuj mapę** robiło tylko mapy BITWY. | Robi też nową **Operację** lub nowy **Rozdział kampanii** z wpisu dowolnej mapy. **Widziane w grze:** nowa Operacja. Wczesna wersja: nowy rozdział kampanii nie był jeszcze próbowany. |
| Spłaszczenie gór na krawędzi mapy zostawiało tam urwisko. | Krawędź mapy idzie za terenem. **Widziane w grze** (Blitz Twin, płaska aż do krawędzi). |
| Jednostki omijały miejsca, gdzie stały usunięte budynki miasta. | Teren otwiera się dla każdej jednostki tam, gdzie znikają budynki, tak jak przy drzewach. **Widziane w grze.** |
| Nie było sposobu, by malować teren mapy. | **Malowanie mapy (Map Paint):** maluj obraz terenu kolorem (koło kolorów, własne kolory mapy albo pipeta) albo własnym terenem mapy skopiowanym z innego miejsca. **Oczyść teren pod spodem** (domyślnie włączone) usuwa trawę, uprawy i kamienie spod farby, żeby było ją widać na każdej wysokości. Wczesna wersja: widziane w grze z wysoka. |

**0.9.4:** nowe mapy, wczesna wersja. **Duplikuj mapę** robi nową mapę z dowolnej mapy BITWY, a mapy otwierają się w
sekundę.

| Wcześniej | Teraz |
|---|---|
| Zmiany map mogły zmieniać tylko mapy samej gry. | **Duplikuj mapę** (zakładka Mapy, pod nazwą otwartej mapy) robi **nową mapę**: pełną kopię z własną nazwą, na liście w BITWY obok oryginału, którą potem zmieniasz jak każdą mapę. Okno mówi, co robi i jak to działa. **Widziane w grze:** na nowej mapie gra się na jej własnym terenie, a 101 nowych map naraz było na liście i dało się na nich grać. Wczesna wersja: kopie map innych niż Blitz budują się, ale nie były jeszcze próbowane w grze, a spłaszczenie gór na krawędzi mapy zostawia tam urwisko. Zgłoś, proszę, co znajdziesz. |
| Mapa otwierała się za każdym razem kilka sekund (M03_Italie: 7,6 s). | Jej dane są zachowywane między otwarciami i uruchomieniami: 1,7 s za drugim razem. |
| „Mod” i „Mapa” były dwoma podobnymi menu. | **Mod jednostek** (z czołgiem) i **Zmiany map** (z mapą). |
| Strony i strefy łatwo było pomylić. | **Dla kogo?** mówi, że strona to ten, kto kontroluje jednostki (jeden kraj może mieć kilka stron), a podpowiedź strefy mówi, że to obszar mapy, a nie strona. |
| Aktualizacje przychodziły tylko jako całe wersje. | Małe poprawki mogą przychodzić między wersjami (0.9.4.1), oferowane jak każda aktualizacja. |

**0.9.3:** wszystko, co postawisz, widać z daleka, nowe drogi przez lasy wyglądają jak drogi samej mapy, drzewa, które
możesz zachować na drodze, obiekty i drzewa po nazwach w twoim języku i budowanie około trzy razy szybsze.

| Wcześniej | Teraz |
|---|---|
| Obiekty, drzewa i budynki do stawiania były wymienione po francuskich nazwach kodowych: Caillou_10, ChampsPierres_02, Osier... | Po nazwach w języku Studio, we wszystkich dziesięciu, z tym, jakim rodzajem rzeczy jest każda: „Stony field 2”, „Champ de pierres 2”, „Steiniges Feld 2”. Zmieniają się z przyciskiem języka. Nazwa kodowa i jej folder są w podpowiedzi. |
| Skały i większość innych postawionych obiektów znikały, gdy tylko kamera oddaliła się z bliska, i pojawiały się i znikały, gdy ją obracałeś. | Wszystko, co stawia mod, jest rysowane aż do dalekiej odległości, obiekty samej mapy bez zmian. **Widziane w grze:** postawione skały widać na każdej wysokości. |
| Z wysoka nowa droga przez las była jasnym pasem, a po pierwszej poprawce znikała ze średnio-dalekiej odległości. | Malowana przez lasy tak jak drogi samej mapy, na każdej wysokości. **Widziane w grze.** |
| Nowa droga zawsze usuwała drzewa ze swojej trasy, około 6 m z każdej strony. | **Zachowaj drzewa na nowych drogach** w panelu Drogi: drzewa i krzaki zostają nad drogą, a w lesie droga jest bledsza i bardziej szara. **Widziane w grze.** |
| **Testuj w grze** budowało mod z nowymi drogami na M03_Italie około 5 minut. | Około 1½ minuty: to, jak wyglądają drogi mapy, jest mierzone raz i zachowywane, a kopie pomijają powolne sprawdzenie, którego nie potrzebują. |

**0.9.2:** poprawki z mapy kampanii testera: mosty dla nowych dróg na każdej mapie, końce dróg przyciągane do mostów
(albo wcale), nazwy, które gracz zna, jednostki dla gracza, sceneria widoczna z daleka i strefy scenariusza jako granice
na ziemi.

| Wcześniej | Teraz |
|---|---|
| Droga nad wodą zatrzymywała budowanie na 20 z 29 map z mostami (Włochy, Niemcy, Holandia...): jej most „nie miałby podłogi”. | Dostaje most i podłogę na każdej mapie z mostami. Jeszcze nie widziane w grze na tych mapach. |
| Każdy punkt drogi przyciągał się do najbliższej drogi, na drogę nawet wtedy, gdy postawiłeś tam most. | Przyciągają się tylko dwa końce drogi, najpierw do końca postawionego mostu. **Przyciągaj końce do dróg i mostów** w panelu Drogi to wyłącza. |
| Budynki i jednostki po nazwach kodowych, jak „Descriptor_Building_VehiculeFactoryLeurre”. | Po nazwach, jakie daje im gra (DECOY ARMOR BASE), z własnym zdaniem gry o tym, co każdy robi. |
| Nie było sposobu, by dać jednostki graczowi w rozdziale kampanii: strona gracza (0) była odrzucana. | **Dla kogo?** wymienia własne strony scenariusza z jego misji: „Player · USA (side 0)”, „Computer · Germany (side 1)”... |
| Na M03_Italie i innych mapach nowa droga na otwartym terenie ukrywała z daleka scenerię mapy, a postawione obiekty były widoczne tylko z bliska. | Daleki widok mapy zostaje taki, jaki był, a postawione obiekty widać z daleka jak te z mapy. Jeszcze nie widziane w grze. |
| Strefy scenariusza były kolorowymi płachtami unoszącymi się nad mapą, zakrywającymi jej teren i ikony. | Każda strefa to wyraźna linia wzdłuż jej granicy na ziemi z półprzezroczystym odcieniem w środku, jak granice w Stellaris. **Wypełnienie stref** ustawia środek (0 %: same granice). |

**0.9.1:** przeciągnij cokolwiek na mapie, czytelniejsze ikony, które możesz powiększać i ukrywać, twój język od
pierwszego startu i typ każdej jednostki tak, jak nazywa go gra.

| Wcześniej | Teraz |
|---|---|
| Punkty startowe, składy zaopatrzenia i sprowadzane jednostki przesuwało się tylko narzędziem Przesuń, jednym kliknięciem, a potem drugim. | Chwyć dowolne z nich na mapie i przeciągnij, bez wybranego narzędzia, tak jak już obracały się kamery otwarcia. Składy i sztaby nadal trzymają się dróg podczas przeciągania. |
| Ikony mapy były ludzikami i prostokątami, a każdy bunkier wyglądał tak samo. | Ikona dla każdego rodzaju: żołnierz, czołg, ciężarówka dla składów zaopatrzenia, samolot, działa, wyraźnie oznaczony sztab, baza pancerna i lotnisko odróżnione od siebie, a każdy bunkier z własną (przeciwpancerny, karabin maszynowy, przeciwlotniczy, artyleria, fort, punkt obserwacyjny). |
| Ikony były z wysoka nieporęczne, a jedynym sposobem, by je ukryć, było ukrycie całego scenariusza. | Ikony maleją, gdy kamera się oddala, suwak ustawia ich rozmiar, a panel Scenariusz pokazuje lub ukrywa każdy rodzaj (starty, kamery, składy, budynki, jednostki, strefy, miasta). Zachowane na następny raz. |
| Studio startowało z nazwami kodowymi, a język był w Ustawieniach, więc gracze nie wiedzieli, że mówi w ich języku. | Pierwszy start pyta: „Wybierz język”, każdy język we własnych słowach, z zaznaczonym tym, na który twoja gra jest ustawiona w Steam. Potem przycisk języka na górze, zawsze na widoku. |
| Jednostki były tylko „Lądowe” albo „Lotnictwo”. | Pod Lądowe, Piechota i Lotnictwo typy samej gry: Czołg lekki, średni i ciężki, Niszczyciel czołgów, Rozpoznanie pancerne, Myśliwiec, Myśliwiec-bombowiec, Bombowiec lekki, średni i ciężki, Rozpoznanie lotnicze... także w wierszu każdej jednostki, w twoim języku. Wyszukiwanie je znajduje („bombowiec”, „rozpoznanie”). |
| Lista zainstalowanych aplikacji Windows pokazywała pierwszą kiedykolwiek zainstalowaną wersję. | Pokazuje wersję, którą masz. |

**0.9.0:** drogi wyglądają dobrze. Droga, którą narysujesz, wygląda teraz jak drogi samej mapy, z wysoka i tuż przy
ziemi. Dojście do tego zajęło dużo czasu i dużo testów, dłużej niż mosty. Przetestowane w grze na D-Day.

![Nowa droga z bliska na D-Day: asfalt z przerywaną linią środkową i żwirowymi poboczami przechodzącymi w trawę](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-5-done-close.jpg)

| Wcześniej | Teraz |
|---|---|
| Nowa droga znikała, gdy kamera się do niej zbliżała: widać było tylko jej farbę, z wysoka. | Z bliska jest rysowana asfaltowymi naklejkami samej mapy, kładzionymi wzdłuż niej tak, jak kładzie je mapa, z naklejką krawędzi po obu stronach: asfalt, przerywana linia środkowa, żwirowe pobocza. |
| Farba była jednym płaskim kolorem, bledszym i szerszym niż drogi mapy. | Farba jest mierzona na własnych drogach mapy: ich kolor, pobocza i to, jak przechodzą w teren. Każda mapa dostaje własną. |
| Trawa, krzaki i drzewa gospodarstwa przerastały przez nową drogę. | Rośliny i obiekty mapy na trasie drogi są usuwane (około 6 m z każdej strony). Lasy zachowują osłonę i ruch, a budynki zostają. |
| Znane były tylko naklejki dróg z D-Day. | Na mapach pustynnych używane są ich własne naklejki, kładzione tak samo (jeszcze nie widziane w grze). |
| Duże usuwanie (tysiące okręgów) budowało się wiele minut. | Dużo szybciej: sprawdzane są tylko okręgi blisko każdej części mapy. |

![Trzy nowe drogi odchodzące od głównej drogi D-Day](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/roads-6-done-overview.jpg)

**0.8.3:** narzędzia scenariusza edytora mapy z RUSE-Mod-Managera LittleGroove'a: składy zaopatrzenia i sztaby trzymają
się dróg, ikona dla każdego budynku i jednostki, a kamera otwarcia każdego gracza pokazana, przenoszona i obracana.
Jeszcze nie wypróbowane w grze.

| Wcześniej | Teraz |
|---|---|
| Miejsca na skład zaopatrzenia nie dało się postawić. | **Miejsce na skład zaopatrzenia** jest pierwsze w Dodaj jednostkę → Budynki → Pieniądze. |
| Punkt startowy trafiał dokładnie tam, gdzie kliknąłeś, tak samo na drodze, jak daleko od niej. | **Przyciągaj do dróg** (domyślnie włączone) stawia go obok najbliższej drogi, tak daleko od niej, jak robią to mapy samej gry (zmierzył to LittleGroove). Odznacz, by postawić go na środku pola. |
| Miejsca pojawiania to było kilka ikon, z literami dla kraju. | Ikona tego, czym jest każde (sztab, skład zaopatrzenia, fabryka, fort, atrapa, żołnierz, czołg, przeciwpancerne, artyleria, prototyp, samolot, wieżyczka), i znak rozpoznawczy kraju. |
| Nie było widać, gdzie otwiera się mecz gracza. | Każdy punkt startowy pokazuje swoją kamerę otwarcia: przelot (kropkowany), gdzie się zatrzymuje, na co patrzy i część mapy, którą pokazuje ekran. |
| Kamera otwarcia przesuniętego punktu startowego zostawała w starym miejscu. | Kamera przesuwa się razem z nim; nowy punkt startowy dostaje własną kamerę. |
| Kamery otwarcia nie dało się zmienić. | Z **Przesuń** przeciągnij kamerę startu wokół jego sztabu, by otworzyć mecz z innej strony; **Przywróć kamerę** to cofa. |
| Punkt startowy w lesie był odrzucany. | Dozwolony: sztab tam działa, a ciężarówki zaopatrzenia jeżdżą przez lasy. Odrzucane są tylko woda, urwiska i zablokowany teren. |

**0.8.2:** test zatrzymany przez błąd w twoim modzie mówi ci, który to błąd, i go naprawia, mody i mapy osobno,
czytelniejsze kolory mapy i miejsca pojawiania, i jedna kopia gry na cały PC.

| Wcześniej | Teraz |
|---|---|
| Test zatrzymany przez błąd w twoim modzie chował powód w logu i odsyłał do Rozwiązywania problemów, które nie może naprawić moda. | Każdy błąd jest wymieniony nad logiem z przyciskiem, który go naprawia: miejsce pojawiania drużyny na mapie BITWY zmienione na neutralne albo usunięte (także wszystkie naraz), droga, która z niczym się nie łączy, usunięta. Rozwiązywanie problemów pokazuje się tylko przy innych niepowodzeniach. |
| Komunikatu na dole nie dało się zamknąć. | Każdy komunikat ma ×, by go zamknąć. |
| Logu testu nie dało się skopiować. | **Kopiuj raport** kopiuje log i komunikat, do zgłoszenia błędu albo na Discord. |
| Mody i mapy dzieliły jedno menu. | Mody i mapy mają każde swoje menu, a Eksportuj umieszcza plik prosto w bibliotece Launchera. |
| Każde miejsce pojawiania na mapie wyglądało tak samo. | Każde miejsce pojawiania to ikona budynku, czołgu, żołnierza lub samolotu w kolorze jego strony, z jego krajem. |
| Kolory mapy nie były wyjaśnione. | Legenda kolorów dla osłony, tego, gdzie idą jednostki, i usuwania; osłona narzędzia Miasto ma własny kolor; suwak przezroczystości dla każdej warstwy. |
| Wzgórza i drzewa przebijały się przez strefy scenariusza. | Strefy unoszą się nad terenem, a suwak **Wysokość stref** ustawia, jak wysoko. |
| Każdy test trzymał własną kopię gry. | Jedna zmodowana kopia na cały PC, wspólna z Launcherem. |
| Wersja nie była pokazywana, a Co nowego było listą. | Wersja jest obok nazwy, a Co nowego otwiera tabelę wcześniej/teraz taką jak ta. |
| Mało podpowiedzi. | Podpowiedzi przy głównych kontrolkach, pisane dla graczy, którzy dopiero zaczynają modować. |
| Nowe drogi na Twilight of the Gods, Alpha, Ostfriesland i Robert nie dostawały modelu dróg mapy. | Też go dostają. |
| Budowanie mówiło, że nowe drogi są „rysowane z bliska”. | Mówi, że widać je z daleka; z bliska jeszcze ich nie widać (wciąż znany problem). |

**0.8.1:** jednostki z dowolnej nacji, nowy wygląd, krótszy pasek narzędzi i narzędzie Usuń.
- **Jednostki z innej nacji działają.** Nowa jednostka może trafić do menu budowy dowolnej nacji, bez względu na to, z
  jakiej armii pochodzi jej model: niemiecki Tiger lub Ju 87 dla USA, japoński Zero lub Chi-Ha też. Jest budowana,
  walczy, pokazuje swój obraz na karcie i znaczniku i można ją zaznaczyć na ziemi i w powietrzu, nawet w meczu, w którym
  nikt nie gra nacją, z której pochodzi (przetestowane w grze, 2026-10-02). Budowanie sprawia, że modele tej nacji
  wczytują się w każdym meczu; mecz zajmuje trochę więcej pamięci i czasu wczytywania.
- **Nowy wygląd:** błękity R.U.S.E. zamiast czerni i złota, oraz nowe logo: stół sztabowy.
- **Pasek narzędzi edytora mapy jest krótszy.** Narzędzia, które idą w parze, dzielą jeden kafelek, z zakładką dla
  każdego: Teren i woda, Osłona i ruch, Drogi i mosty, Budynki, Obiekty i drzewa, potem Usuń, Scenariusz i Sprawdź.
  Kafelek otwiera się na zakładce używanej ostatnio.
- **Narzędzie Usuń:** przeciągnij po drzewach i obiektach samej mapy (także budynkach, jeśli je wybierzesz), a znikną,
  gdy mod zostanie zbudowany. Czerwone okręgi są zapisywane w modzie, to, co zakrywają, jest zabarwione na czerwono, a
  panel liczy, co zabiorą. Tam, gdzie znikają drzewa, teren otwiera się dla każdej jednostki i traci osłonę lasu.
  Porządne usuwanie budynków, dróg, krzewów i skał samej mapy jest następne.
- **Instalator proponuje czystą kopię zapasową gry** obok skrótu na pulpicie i mówi dlaczego: dzięki niej narzędzie
  rozwiązywania problemów może przywrócić wszystko, co zmienił inny menedżer modów.

**0.8.0:** edytor mapy dorasta: nowe pędzle i panele, mosty, przez które jednostki naprawdę przechodzą, lasy, które
możesz wyciąć, i budowanie, które sprawdza zasady gry, żeby to, co zrobisz, działało za pierwszym razem. Do tego
narzędzie rozwiązywania problemów i czysta kopia zapasowa gry.
- **Nowe w edytorze mapy:**
  - **Pędzle Otwórz** (Ruch): odwrotność Blokuj. Daj jednostkom teren, z którego mapa je trzyma z dala (wszystkie
    jednostki, piechotę albo pojazdy). Otwarcie wody jest dozwolone, z ostrzeżeniem: jednostki stoją tam na dnie rzeki.
  - **Pędzel Las** (Osłona): drzewa i osłona jednym pociągnięciem; Cofnij zabiera jedno i drugie.
  - **Panel Mosty:** rodzaje mostów samej mapy i most stawiany ręcznie o długości i obrocie, które wybierzesz; przejścia
    nowych dróg przez wodę rysowane na złoto.
  - **Sprawdź tę mapę:** wymienia, co poszłoby źle, zanim zaczniesz test (odcięty teren, drogi lub mosty, których
    jednostki nie mogą użyć, niepołączone końce dróg, budynki na drogach), a kliknięcie jednego pokazuje, gdzie.
  - Osuszone lub podniesione do sucha koryta rzek są otwierane dla jednostek przez budowanie.
- **Usuń drzewa i obiekty samej mapy:** okręgi `[[erase]]` w `scenery.toml` moda (na razie pisane ręcznie; narzędzie
  Usuń w Studio jest w drodze). Czołgi wjeżdżają do wyciętego lasu, a piechota nie jest już tam ukryta.
- **Postawione obiekty stoją na ziemi w każdym rozmiarze.** Budynek powiększony 10× unosił się w powietrzu; teraz stoi
  na ziemi jak te z mapy.
- **Poprawione: osłona na mapach, które nie są kwadratowe** (D-Day, Frontline, Djebel, Medjez, Handshake over the Elbe
  oraz mapy kampanii w Tunezji, Holandii i Ardenach). Osłona malowana lub usuwana tam (pędzle Osłona, Odsłoń, Miasto i
  Las, `cover.toml`) lądowała do kilometra od miejsca, gdzie ją narysowano, a widok mapy też pokazywał ją w tym złym
  miejscu. Teraz jedno i drugie jest dobrze: jeśli malowałeś osłonę na jednej z tych map, spójrz na nią jeszcze raz w
  widoku mapy. Mapy kwadratowe (Blitz i większość innych) zawsze były dobrze.
- **Mosty działają w grze.** Droga narysowana nad wodą dostaje rodzaj mostu samej mapy (także map holenderskich), a
  czołgi, piechota i ciężarówki zaopatrzenia przechodzą przez niego po pomoście, piechota na wysokości pomostu. Końce
  mostu łączą się z drogami, których jednostki już używają, i trzymają się z dala od budynków mapy; most, którego nie da
  się połączyć, zostaje zamknięty, a notatka budowania mówi, na co trafiła droga i gdzie.
- **Budowanie sprawdza zasady gry.** Każdy plik, który zmienia mod, został sprawdzony względem tego, co robi z nim gra,
  a mod, który by się w grze zepsuł, jest odrzucany z notatką mówiącą dlaczego, zanim cokolwiek zostanie zapisane:
  - drogi: jednostki idą teraz nowymi drogami, nie tylko ciężarówki zaopatrzenia, a nowa droga, która nie łączy się z
    żadną inną drogą, jest odrzucana (sieć dróg musi zostać w jednym kawałku);
  - postawione budynki i blokady: jednostki nie mogą już przez nie przejeżdżać; nowe budynki, mosty i drzewa są widoczne
    z każdej odległości;
  - teren: nowa woda jest zamknięta dla jednostek, mapa SI idzie za twoimi lasami, blokadami, mostami i wodą, a
    pociągnięcie, które nie może zmienić terenu (albo sięga podłogi mostu), mówi o tym;
  - jednostki: zła salwa, ID, nacja lub lista menu są odrzucane, flagi jednostek są sprawdzane, a każda flaga jest
    wyjaśniona przy wyborze flag (flagi 62 i 63, które powodują awarię gry na jednostce, która nie jest ciężarówką, są
    błędem); jednostka umieszczona w fabryce innej nacji jest na razie odrzucana (powodowała awarię gry przy budowie;
    sprawienie, by działała, jest następne);
  - scenariusz: miejsca pojawiania są domyślnie neutralne, miejsce pojawiania jednostki, której modeli mecz może nie
    wczytać, jest odrzucane (powodowało awarię gry na starcie), start, do którego pojazdy nie mogą dojechać, jest
    odrzucany, przesunięty start zabiera ze sobą swoją kamerę, a miejsca graczy są liczone na drużynę.
- **Raport budowania** pokazuje każde ostrzeżenie (niektóre ginęły), a przebudowa najpierw zabiera starą kopię testową,
  więc starej kopii nie da się uruchomić przez pomyłkę.
- **Kwadratowa osłona:** `square = true` na malowaniu w `cover.toml` albo na pociągnięciu Osłona lub Odsłoń w
  `terrain.toml` maluje kwadrat wzdłuż osi mapy (na razie pisane ręcznie; widok mapy rysuje go jako kwadrat).
- **Rozwiązywanie problemów** (obok *Testuj w grze* i w Ustawienia > Pomoc): sprawdza za jednym razem, co może zatrzymać
  test (czy gra jest znaleziona, Steam, gra pozostawiona uruchomiona ze zmodowanej kopii, dysk i jego wolne miejsce,
  pozostałe kopie, pliki tylko do odczytu, czy aplikacja może zapisywać tam, gdzie trafiają kopie), z przyciskiem dla
  każdej poprawki, jaką może zrobić, i raportem do wklejenia w zgłoszeniu błędu, bez twojej nazwy użytkownika Windows.
- **Czysta kopia zapasowa gry** (Ustawienia): trzymaj czystą kopię plików swojej gry, sprawdzaj je względem niej i
  przywracaj wszystko, co zmienił inny menedżer modów lub ręczna edycja. Pliki, które nie należą do gry, są odsuwane na
  bok, nigdy usuwane. Albo pozwól Steam naprawić grę (*Zweryfikuj w Steam*). To jedyne miejsce, gdzie Studio
  kiedykolwiek zapisuje coś w folderze twojej gry, i tylko wtedy, gdy o to poprosisz.
- **Udostępnij swój mod:** zrobiłeś mod? Po eksporcie Studio pokazuje jego rozmiar i SHA-256 oraz jak dodać go do listy
  modów na GitHubie i zostać współtwórcą.
- **Znany problem: nowe drogi nie są jeszcze rysowane z bliska.** Są malowane na ziemi i widać je z daleka, a jednostki
  ich używają, ale z kamerą blisko ziemi nowa droga znika. Pracujemy nad tym.

**0.7.6:** drugi Test w grze działa, a jednostki zawsze mogą dotrzeć do mostów.
- **Poprawione:** co drugi *Testuj w grze* mógł się nie udać z „An old modded copy ... can't be removed ... (Access is
  denied)”. Kopia, której Windows nie chce usunąć (plik, który starsza wersja podlinkowała do zastąpionego pliku gry,
  program, który wciąż go trzyma), już nie zatrzymuje testu: jest odsuwana do `RUSE-Instances\.trash` i usuwana, gdy nic
  jej już nie trzyma. Jeśli R.U.S.E. wciąż działa z kopii testowej, dostajesz o tym informację z nazwą programu.
  Dwukrotne naciśnięcie *Testuj w grze* uruchamia jeden test, nie dwa.
- **Poprawione:** nowy most drogi mógł spowodować awarię gry, gdy jednostkom kazano na niego wjechać: jego pomost nie
  sięgał żadnego terenu, po którym poruszają się jednostki. Każdy koniec mostu łączy się teraz z terenem wzdłuż drogi (do
  62 m dojazdu); most, którego nie da się połączyć, zostaje zamknięty dla jednostek, z notatką, a budowanie nigdy nie
  zapisuje terenu, do którego jednostki nie mogą dotrzeć.

**0.7.4:** Testuj w grze działa, gdy pliki twojej gry są oznaczone jako tylko do odczytu.
- **Poprawione:** *Testuj w grze* za każdym razem kończyło się błędem „[WinError 5] Access is denied”, gdy pliki R.U.S.E.
  są oznaczone jako tylko do odczytu (instalacja z płyty, przywrócona kopia zapasowa): kopia testowa zachowywała to
  oznaczenie, więc kopii zostawionej w połowie zbudowanej nigdy nie dało się usunąć. Kopia testowa nigdy już nie
  zachowuje oznaczenia, a pozostałość po starszej wersji jest usuwana sama (pliki twojej gry kończą dokładnie takie,
  jakie były). Jeśli gra wciąż działa z kopii testowej, dostajesz informację, by ją zamknąć, zamiast błędu Windows.
- **Droga pokazuje swoją długość** podczas rysowania, obok kursora (w stylu Cities: Skylines); narzędzia Drogi pokazują
  łączną długość twoich nowych dróg.
- **Nowe drogi są malowane na ziemi** w kolorze dróg samej mapy (potwierdzone w grze), a **droga nad wodą dostaje
  most**: rodzaj mostu samej mapy, jeden kawałek rozciągnięty od brzegu do brzegu, tak jak mosty samej gry, żeby
  jednostki mogły przejść. Droga nad jednym z mostów samej mapy dostaje w jego miejsce nowy most. (Mosty są nowe:
  jeszcze nie sprawdzone w grze.)

**0.7.3:** ułóż widok mapy po swojemu. Panel mapy (lewy górny róg) i narzędzia (na dole) przesuwasz w dowolne miejsce
za ich uchwyt (⠿) i zwijasz strzałką obok niego: panel mapy do samego tytułu, narzędzia do samego paska. Dwuklik uchwytu
przywraca ten panel na miejsce. Twój układ jest zachowywany.

**0.7.2:** drogi i czytelniejsze testy.
- **Rysuj drogi** w stylu Cities: Skylines (rodzaj Drogi na pasku): **Prosta**, **Łuk** i **Dowolna**. Koniec blisko
  drogi przyciąga się do niej i się z nią łączy. Nowe drogi rysują się jako niebieskie wstęgi, a **trasy zaopatrzenia
  ich używają** (potwierdzone w grze). Nie są jeszcze malowane na ziemi.
- Pole **Drogi** pokazuje własne drogi mapy na złoto.
- Słowa samej gry: scenariusz jest nazwany tak jak przycisk menu głównego, który go uruchamia (**Bitwy**, Operacja,
  Kampania, czytane z tekstu twojej gry w twoim języku), a złota linia pod menu scenariusza mówi, gdzie się w niego gra,
  np. *W grze: Bitwy › D-Day (6 graczy)*.
- **Testuj w grze** mówi, gdzie zbudowało i dokładnie co otworzyć, by zobaczyć twoje zmiany (np. *BITWY > D-Day*).
- Środkowy przycisk myszy obraca widok także w trybie rozglądania się (wcześniej tam przybliżał).

**0.7.1:** kilka jednostek naraz, sprawdzanie moda i pomoc pod ręką.
- **Dodaj jednostkę** stawia 1, 2, 4, 6, 8 lub 10 naraz, w **linii, kolumnie, klinie, czworoboku lub kręgu** zwróconych
  ku górze ekranu, z suwakiem odstępu i pierścieniami pokazującymi, gdzie stanie każda.
- **Sprawdzanie moda**: każdy plik twojego moda jest czytany tak, jak czyta go budowanie gry, gdy wybierasz mod i przed
  **Testuj w grze**. Czerwony pasek wymienia każdy problem; uszkodzony plik mapy można **odłożyć** (zmienić mu nazwę,
  nigdy nie zgubić), a folderowi mapy nazwanemu tytułem mapy (maps/Blitz) można jednym kliknięciem **zmienić nazwę** na
  nazwę jego paczki (maps/SuperCrossRoads4).
- Poprawione: pociągnięcia **Woda** były zapisywane bez swojego poziomu, więc budowanie gry odrzucało mod. Każdy plik,
  który zapisuje Studio, jest teraz odczytywany z powrotem, zanim zostanie zapisany.
- Listę map można **zwinąć** («), żeby mieć więcej miejsca.
- **Ustawienia > Pomoc i społeczność**: wiki (nowy podręcznik), Discussions i **Zgłoś problem**, który otwiera
  zgłoszenie błędu z już wpisaną twoją wersją. Błąd na dole ma własny link **Zgłoś**. Aplikacja niczego nie wysyła:
  czytasz zgłoszenie i sam je publikujesz.

**0.7.0:** nowy wygląd i narzędzia ruchu. Narzędzia mapy przeniosły się na pasek u dołu, jak w Cities: Skylines, w
stylu HUD samego R.U.S.E.: wybierz rodzaj (Teren, Woda, Osłona, Ruch, Budynki, Obiekty, Drzewa, Scenariusz), a jego
narzędzia otworzą się nad nim; kliknij go znowu albo naciśnij Esc, żeby tylko się rozejrzeć. Wybory scenariusza są
teraz kafelkami, a nie listami rozwijanymi. **Ruch:** pole **Gdzie idą jednostki** pokazuje to na mapie (czerwony:
żadna jednostka; żółty: tylko piechota), a trzy nowe pędzle zamykają teren: **Blokuj** (każda jednostka), **Blokuj
piechotę** i **Blokuj pojazdy**. Postawione budynki zatrzymują jednostki (pole **Lity**, domyślnie włączone).
Potwierdzone w grze: jednostki planują trasę wokół zablokowanego dołu i przechodzą między postawionymi wieżami.

**0.6.9:** budynki, obiekty i drzewa, które postawisz, są teraz widoczne w grze przy każdym przybliżeniu (potwierdzone na
Blitz, do 8× ich rozmiaru): każda grupa trafia do nowego bloku owiniętego wokół najbliższej wioski lub gospodarstwa,
które mapa rysuje z daleka. Sprawdzone na wszystkich 32 mapach: nic innego się nie przesuwa. Jednostki nadal przechodzą
przez postawione budynki; zrobienie ich litymi jest następne.

**0.6.8:** twórz miasta i lasy, w których jednostki mogą się ukryć. Widok mapy pokazuje, gdzie jednostki się ukrywają
(pole **Osłona**, na zielono), a trzy nowe pędzle to malują: **Osłona**, **Odsłoń** i **Miasto** (kliknij miasto:
osłona otacza każdy jego budynek, także postawione). Potwierdzone w grze: piechota na malowanej osłonie jest ukryta.

**0.6.7:** postawione obiekty mogą mieć do 10× swojego rozmiaru (suwak Rozmiar narzędzia Postaw; [ i ] zmieniają o 0,1
do 3×, potem o 0,5).

**0.6.6:** amunicja jest też posortowana według typu: pociski przeciwpancerne, pociski odłamkowo-burzące,
przeciwlotnicza, karabiny maszynowe, broń piechoty, przeciwpancerna broń piechoty, bomby i rakiety (lista Typ nad
amunicją). Mody mogą też malować osłonę (gdzie jednostki się ukrywają, jak w lesie) i zablokowany teren na mapie
(`maps/<map>/cover.toml`); narzędzie Studio do tego jest następne.

**0.6.5:** scenariusze można edytować na mapie. **Przesuń** punkt startowy lub miejsce pojawiania (kliknij go, potem
miejsce, gdzie ma trafić; Przywróć to cofa). **Dodaj jednostkę** sprowadza jednostkę lub budynek, gdy scenariusz się
zaczyna: wybierz jej rodzaj (budynki, lądowe, piechota, lotnictwo), potem typ (dla budynków: sztab, pieniądze, fabryki,
forty i obrona, atrapy; dla jednostek: fabryka, która je buduje), potem jednostkę (według nacji) i jej stronę.
Zapisywane w `maps/<map>/scenario.toml` moda. Lista jednostek ma ten sam filtr Typ.

**0.6.4:** lista map ma filtr typu: wszystkie mapy albo tylko mapy potyczek, Operacje, kampania, demo lub mapy testowe
(z menu samej gry; mapa może należeć do kilku). Jest zapamiętywany.

**0.6.3:** zakładka **Ustawienia** (obok Jednostki i Mapy): język, klawisze widoku mapy, folder gry i aktualizacje w
jednym miejscu, gotowe na więcej.

**0.6.2:** wyszukiwanie aktualizacji jest solidniejsze: gdy GitHub odrzuci to jedno sprawdzenie przy starcie (pozwala
na 60 na godzinę na adres internetowy, wspólny dla wszystkiego, co z niego korzysta), Studio czyta zamiast tego listę
wydań GitHuba. Mody mogą też sprowadzać jednostki i budynki w scenariuszu (`[[spawn]]` w `maps/<map>/scenario.toml`).

**0.6.1:**

- **Twój język i klawisze są zachowywane** po ponownym uruchomieniu, aktualizacjach i ponownej instalacji (ginęły przy
  każdym starcie).
- **Scenariusze pogrupowane tak, jak używa ich gra:** Potyczka, Operacje, Kampania, Demo, Test i te, których nie wczytuje
  żadne menu, każdy nazwany tak, jak nazywają go menu gry („10. UTAH BEACH”, „Anzio”).
- **Mody mogą przesuwać punkty startowe i miejsca pojawiania** (`maps/<map>/scenario.toml`); sprawdzone w grze: sztab
  startuje tam, gdzie umieszcza go mod.

**Nowe w 0.6:**

- **Teren, który działa w grze:** teren, który podnosisz, obniżasz lub spłaszczasz, przyjmuje teraz rozkazy ruchu,
  kamera zostaje nad nim, a drzewa i budynki na nim stoją. Przepis DomesticNukes i jego Claude'a: najpierw przesuwa się
  teren rozgrywki, rysowany teren idzie za nim, a ukryte limity wysokości gry są poszerzone. Sprawdzone na wszystkich 32
  mapach.
- **Scenariusze na mapie:** wiersz „Scenariusz” wybiera jeden ze scenariuszy mapy (potyczki, wyzwania, rozdziały
  kampanii) i pokazuje jego strefy, punkty startowe (słupy w kolorze każdego sojuszu), miejsca pojawiania (białe romby)
  i nazwy miast. Wskaż jedno, by zobaczyć, co to jest. Pierwszy krok w stronę robienia map.

**0.5.2:**

- **Pędzle Woda i Osusz** (Woda pod klawiszem 0): zalej teren poniżej danego poziomu, by zrobić jezioro, albo osusz
  jezioro lub rzekę. Od DomesticNukes i jego Claude'a, sprawdzone w grze na Blitz.
- **Własne klawisze:** „Zmień klawisze…” pod wierszem pomocy widoku mapy: kliknij akcję, naciśnij klawisz. Domyślne
  przywraca je.

**0.5.1:**

- **Działo zachowuje własny błysk i dźwięk:** gdy broń strzela amunicją innej jednostki, bierze teraz też błysk wylotu
  lufy i dźwięk wystrzału tej jednostki (działo Shermana na strzelcu strzela jak Sherman). Broń pokazuje, który z nich
  odtwarza.
- **Pędzel Poziomuj** (klawisz 7): maluje teren płasko na wysokości, gdzie zaczynasz przeciągać.
- **WASD porusza się z kamerą**: W to zawsze przód na ekranie, jakkolwiek widok jest obrócony.
- Indeks gry jest budowany ponownie raz, przy pierwszym otwarciu 0.5.1 (około pół minuty).

**Nowe w 0.5:**

- **Nowe jednostki:** skopiuj jednostkę z jej strony, nazwij ją, ustal jej cenę i umieść ją w menu budowy.
- **Amunicja i flagi:** rodzaj Amunicja z każdą amunicją. Broń może strzelać amunicją innej broni (pokazana jest nacja,
  z której pochodzi) albo własną jej kopią. Listy flag (czym jednostka jest i co robi) można edytować, jak w edytorze
  jednostek RUSE Mod Managera.
- **Mapy:** każda mapa pokazuje swoją nazwę z gry, w twoim języku, obok nazwy kodowej. Budynki, obiekty i drzewa są
  rysowane **prawdziwymi modelami 3D i teksturami gry**, dzięki DomesticNukes i jego Claude'owi.
- **Pędzle terenu:** podnieś, obniż, wygładź i zrób rampę z terenu, zapisane w modzie. **Zacznij od nowa** czyści mapę.
- **Narzędzie Postaw:** jedno kliknięcie stawia budynek, obiekt lub drzewo. Pomaluj obszar albo kliknij dwa razy, by
  zrobić linię (żywopłot, ulicę). Cofnij zabiera cały obszar lub linię. Sceneria jest na razie tylko dla wyglądu:
  jednostki przez nią przejeżdżają.
- **Klawisze:** WASD / strzałki przesuwają widok, Q/E go obracają, R/F przybliżają. Najedź na dowolny przycisk, by
  zobaczyć podpowiedź.
- **Eksportuj .rusemod:** jeden plik, który instaluje Launcher.
- **Aktualizuje się samo:** od tej wersji pasek mówi, kiedy wyszło nowsze Studio; **Zaktualizuj** je instaluje.

Jest nowe i ledwie testowane poza PC dewelopera, więc zgłaszaj, proszę, wszystko, co dziwne, w GitHub Issues.

![Mapy w RUSE Studio: Centre of Gravity w 3D](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-maps.jpg)

![RUSE Studio w trybie podglądu, z przykładowymi jednostkami](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/studio-unit.jpg)
