**RUSE Studio, wersja zapoznawcza dla modderów.** Przeglądaj jednostki gry w dowolnym z jej dziesięciu języków,
zmieniaj je we własnym modzie i testuj go w grze. Twoja instalacja Steam nigdy nie jest zmieniana.

**0.9.8.1:** Narzędzia LittleGroove'a trafiają do Studia, a z nimi muzyka i dźwięki, nacja zmieniona w inną i jednostki z innych epok.

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
- **Jednostki z innych epok:** karta Jednostki oferuje WWI, WWII+, Zimną wojnę i Współczesność obok jednostek gry.
  Dodaj jedną do swojego moda, a stanie się nową jednostką z własnym modelem i podpisanym autorem; nic nie jest
  dodawane, dopóki jej nie wybierzesz.
- **Nowa mapa: od zera…** jest w karcie Mapy, zanim otworzysz jakąkolwiek mapę.
- **Grunt Pustego terenu jest rysowany jako własny.** Nowa mapa zaczęta od zera ma grunt zrobiony z twoich pociągnięć
  terenu, a nie przesunięty grunt mapy z gry: okrągłe brzegi z bliska i z góry, bez wgnieceń na szczytach wzgórz, a
  budynki i czołgi stoją dokładnie na nim. Sprawdzone w grze na mapach testowych.
- **Pusty ocean zostaje, z ostrzeżeniem** na swoim przycisku: osobne wyspy nie są gotowe do pełnych bitew
  (niżej).

Jeszcze nie sprawdzone w grze: pole Ulepszenie, Wszystkie wartości, Pliki, narzędzia misji, dodatki do map,
dźwięki tła i jednostki z innych epok.

**Dlaczego nie ma jeszcze map morskich.** Wypróbowaliśmy mapy z wyspami do pełnych bitew z okrętami i przeszkadza
sama gra:

- Jednostka lądowa wysłana na wyspę, do której nie może dotrzeć, powoduje awarię gry.
- Połączenie wysp pasem lądu zapobiega awarii, ale wtedy komputer po prostu wysyła nim swoją piechotę.
- Bez drogi między wyspami nigdzie nie da się postawić budynku.
- Z bronią z gry okręty i jednostki lądowe ledwo mogą sobie nawzajem zaszkodzić.

Same dane mapy nie naprawią awarii: potrzebne są zmiany w plikach samej gry, więc mapy morskie czekają na stanowisko
studia Eugen w tej sprawie.

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
