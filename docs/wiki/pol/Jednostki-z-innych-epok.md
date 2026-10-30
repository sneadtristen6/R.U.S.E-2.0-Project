# Jednostki z innych epok

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.9.8.2 lub nowszego i moda · **Czas:** minuta lub dwie na jednostkę

366 jednostek od I wojny światowej po dziś czeka obok jednostek z gry w zakładce **Jednostki**: czołgi i samoloty z I
wojny światowej, II wojny światowej+, zimnej wojny i współczesności, wszystkie w jednej grze. Każda to darmowy model 3D
innego autora (CC BY), już dopasowany do gry, z oznaczeniami swojej nacji i z podziękowaniem dla autora. Żadnej z nich nie
ma w twoim modzie, dopóki jej nie dodasz.

## Pobierz jednostki epoki

1. W zakładce **Jednostki** wybierz epokę nad rodzajami: **I wojna światowa**, **II wojna światowa+**, **Zimna wojna**
   lub **Współczesność** (**Vanilla** to własne jednostki gry, lista jak zawsze).
2. Za pierwszym razem Studio mówi, ile jednostek ma epoka i ile zajmuje, z przyciskiem **Pobierz jednostki z I wojny
   światowej** (lub z danej epoki). Pobiera je z GitHuba projektu, sprawdza każdy plik przed użyciem i pokazuje je na
   liście.

   | Epoka | Jednostki | Pobieranie |
   |---|---|---|
   | I wojna światowa | 61 | 232 MB |
   | II wojna światowa+ | 32 | 198 MB |
   | Zimna wojna | 149 | 996 MB |
   | Współczesność | 124 | 709 MB |

3. Pobrana epoka sama się aktualizuje, gdy pojawią się nowsze jednostki: Studio o tym mówi i je ściąga.

Jednostki epoki filtruje się tak jak te z gry: rodzaj (lądowe lub powietrzne), nacja (także Chiny), typ i pole
wyszukiwania.

## Dodaj jedną do swojego moda

1. Kliknij jednostkę. Jej strona pokazuje obraz jej modelu i jego twórcę: **Model autorstwa** twórcy, licencję i link do
   miejsca, gdzie go udostępnił.
2. Wypełnij formularz:
   - **Nazwa nowej jednostki** (pokazywana w każdym języku).
   - **Na bazie**: jednostka z gry, której wartościami nowa jednostka zaczyna (prędkość, pancerz, broń, sposób gry).
     Proponowana jest pierwsza; można wybrać dowolną jednostkę jej rodzaju.
   - **Cena** (dla każdej daty bitwy).
   - **Rozmiar**: 1 to ta sama długość co jednostka bazowa. Propozycja to jej prawdziwy rozmiar (jej prawdziwa
     szerokość, rozpiętość skrzydeł samolotu, w skali gry); dowolna wartość od 0.05 do 20. Przeciągnij suwak albo kliknij
     jeden z jego nazwanych punktów: **Malutki**, **Rozmiar z gry** (1: tak długa jak jednostka bazowa, tak duża, jak gra
     rysuje ten rodzaj jednostek), **Jak w rzeczywistości** i **Ogromny**. Współczesne samoloty w rzeczywistym rozmiarze
     są dużo większe niż samoloty z II wojny światowej w grze (J-16 jest tak długi jak Lancaster).
   - **Menu budowy**: nacja i fabryka, w której się ją kupuje.
   - **Badana z**: jednostka, z której jest badana, albo **Żadna: do kupienia od początku**, z polami **Cena badania**
     i **Czas badania** (wpisz czas w sekundach lub minutach: wybór obok).
3. Kliknij **Dodaj do moda**. Jest teraz nową jednostką twojego moda: **Otwórz jej stronę**, by zmienić dowolną z jej
   wartości, jej model lub jej kartę, jak przy każdej jednostce. **Usuń z mojego moda** znowu ją usuwa.

## Zmień jej rozmiar później

Na stronie jednostki **Własny model** ma ten sam suwak: wybierz rozmiar i kliknij **Zmień rozmiar** (model zostaje
dopasowany od nowa z jego własnego pliku, nie trzeba nic wybierać). **Wszystkie samoloty mojego moda** (lub jednostki
lądowe) robi to dla wszystkich naraz: **Rozmiar z gry**, **Jak w rzeczywistości**, **Mniejsze** (o jedną piątą) lub
**Większe** (o jedną czwartą). Gra czyta model jednostki przy wczytywaniu, więc rozmiar nie może się zmienić w trakcie gry:
nowy rozmiar widać od następnego budowania (Testuj w grze).

## Łańcuchy badań

Jednostkę można badać z dowolnej jednostki z menu budowy jej nacji, także z jednostek epok twojego moda: dodaj czołg
z zimnej wojny, potem współczesny, badany z niego. Jednostki z I wojny światowej i II wojny światowej+ można kupić od razu;
te z zimnej wojny i współczesne zaczynają jako badane z odpowiedniej jednostki (formularz mówi, którą proponuje
i dlaczego).

Gdy usuwasz jednostkę, z której badane są inne, **Ustawienia > Badania** decyduje, co się stanie:

- **Najpierw mnie ostrzeż** (domyślnie): Studio wymienia jednostki z niej badane, z przyciskiem **Usuń mimo to**.
- **Odmów**: jednostka zostaje, a komunikat mówi, jak najpierw zmienić pozostałe.
- **Połącz je ponownie**: każda jest zamiast tego badana z rodzica usuniętej jednostki, za własną cenę i we własnym
  czasie (albo staje się dostępna do kupienia od początku).

Jednostka, która została badana z jednostki, której już nie ma, mówi to w swoim polu **Ulepszenie i badania** i na pasku
kontroli, a budowanie zatrzymuje się na niej, dopóki nie wybierzesz innej jednostki albo żadnej.

## Podziękowania

Twórca każdej jednostki z epoki jest wymieniony: na jej stronie i w pliku `CREDITS-era-units.md` twojego moda, który
Studio zapisuje, gdy ją dodajesz. Trzymaj ten plik razem z modem: wymaga tego licencja modeli. Pełna lista twórców jest
w [wydaniu jednostek epok](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases/tag/era-units).

## Co było widziane w grze

Widziane: wczytują się od razu, z własnymi kartami w menu budowy; zakładki badań i łańcuch ulepszeń; ich własne modele;
ich rozmiary. Jeszcze nie testowane: działa holowane (importer nie umie ich jeszcze dopasować, więc pokazują model
jednostki bazowej) oraz to, czy gra liczy czas badania w sekundach.

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Units-From-Other-Eras]]
