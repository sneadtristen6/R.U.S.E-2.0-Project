# Muzyka i dźwięki

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.9.8.8 lub nowszego, moda; do własnego dźwięku pliku dźwiękowego (WAV,
> MP3, OGG lub FLAC), do własnych ruchów pliku motion capture (.bvh) · **Zajmuje:** kilka minut na każdą rzecz

Wszystko tutaj robi się w Studio, w zakładce **RUSE Decoy**, projektancie dźwięków i animacji (zajął miejsce zakładki
Muzyka w Studio 0.9.8.8). Nie trzeba instalować żadnego innego programu.

## Każdy dźwięk w grze

**RUSE Decoy** wymienia po lewej każdy dźwięk, jaki ma gra, według rodzaju: broń z bliska i z daleka, trafienia
i zniszczenia, silniki i kroki, otoczenie, tła map, interfejs, karty podstępu, głosy jednostek, dowództwo i wywiad,
rozmowy radiowe, dialogi misji (z tym, co mówi każda kwestia), muzykę i sygnały. Pole wyszukiwania znajduje dźwięk po
jego nazwie albo po słowach, które w nim padają.

Dla każdego dźwięku:

- **Odtwórz** pozwala go posłuchać.
- **Głośność:** przeciągnij ją. 100% to głośność z gry, do 200%.
- **Zastąp…** otwiera edytor opisany niżej, by wstawić w jego miejsce własny dźwięk.

Zmiany są zapisywane w twoim modzie i trafiają do gry, gdy go testujesz lub eksportujesz.

## Zastąp dźwięk lub utwór

1. Upuść plik dźwiękowy na edytor albo wybierz jakiś. Twój może mieć dowolną długość: Studio zamienia go na format gry.
2. Przytnij go dwoma uchwytami, ustaw **Narastanie** i **Wyciszenie** oraz **Głośność**, i posłuchaj.
3. **Użyj tego** zapisuje go w twoim modzie. Później **Zmień…** otwiera go ponownie, a **Usuń** przywraca dźwięk z gry.

## Dodaj utwór

W **Muzyka i sygnały** utwory są wymienione według miejsca, gdzie grają: menu główne, napisy końcowe, trzy listy,
z których grają bitwy, koniec meczu, cele misji oraz rozdziały kampanii i Operacje, które je wskazują. Trzy listy
bitewne: spokojna, gdy gracze się rozbudowują, bojowa, gdy padają strzały, i muzyka podstępu, gdy zagrywana jest karta
podstępu.

Pod każdą listą bitewną **Dodaj utwór…**: nadaj mu nazwę, upuść plik dźwiękowy, przytnij go, potem **Użyj tego**.
Dołącza do utworów, które gra odtwarza z tej listy, oznaczony jako Nowy.

## Animacje

W **Animacje**: jak poruszają się jednostki, od biegania, strzelania i przeładowywania po umieranie i obsługę działa przy
pracy. Każda mówi, jak nazywa ją gra i ile jednostek ją odtwarza. **Obejrzyj i zmień…** pokazuje ją w 3D na jednostce,
która ją odtwarza (przeciągnij, by obrócić, kółko przybliża; widok 3D raz potrzebuje internetu):

- **Tempo:** 100% to tempo z gry, 200% dwa razy szybciej, 50% dwa razy wolniej.
- **Użyj zamiast:** inna animacja tego samego ciała w jej miejsce (strzelcy mogliby na przykład biegać tak, jak
  uciekają).
- **Kość**, z **Rozmiar** oraz **Obrót wokół** / **Obrót**: jedna część ciała powiększona lub obrócona przez całą
  animację (to, co jest do niej przyczepione, rośnie razem z nią).
- **Wróć do wersji z gry** usuwa wszystkie jej zmiany.

## Motion capture

Nałóż ruch prawdziwej osoby na animację, w **Motion capture**: wybierz ruch z biblioteki ruchów (3205 darmowych ruchów
z bazy motion capture CMU i 100STYLE, każdy pobierany, gdy go wybierzesz) albo **Wybierz plik motion capture…** własny
(.bvh, z Mixamo, Blendera lub dowolnego programu do motion capture).

1. Wybierz część, której użyć: **Od** (w sekundach) i **Jak długo**. Dla chodu lub biegu jeden cały krok każdą nogą;
   dla śmierci zacznij tuż przed upadkiem.
2. **Trzymaj w miejscu** trzyma chód i bieg tam, dokąd gra przesuwa jednostkę; **Zapętl** wygładza przejście od
   ostatniej pozy do pierwszej, dla animacji, którą gra odtwarza w kółko.
3. **Autorzy (kto nagrał ruch):** wypełnione dla ruchów z biblioteki; dla każdego innego pliku wpisz, kto go zrobił,
   i jego licencję. Idzie wszędzie tam, gdzie twój mod.
4. **Obejrzyj**, potem **Użyj**. Zmiany tempa i kości nadal działają na wierzchu; **Wróć do wersji z gry** to usuwa.

## Dźwięki i animacje jednostki

Strona jednostki ma sekcję **Dźwięki i animacje**: jej własne kwestie głosowe i dźwięki silnika oraz jej animacje.
**Zmień jej dźwięki w RUSE Decoy** otwiera RUSE Decoy na dźwiękach tej jednostki. Jednostka mówi kwestie swojej nacji
i swojego rodzaju, więc kwestię zmienioną tam słychać u każdej jednostki, która ją dzieli. Jej działa i trafienia są
w rodzajach broni i trafień.

## Dźwięk tła mapy

W zakładce **Mapy** **Dźwięk tła…** pokazuje dźwięk tła mapy: od czego się zaczyna i jego trzy warstwy, każdej można
posłuchać i zastąpić ją w tym samym edytorze. Mapa może też zaczynać od tła, które gra inna mapa.

## Co widziano w grze

Widziane w grze: dźwięki i animacje RUSE Decoy (Studio 0.9.8.8), utwór menu głównego, utwory list bitewnych 1 i 2,
nowe utwory do nich dodane oraz kwestie głosowe jednostki. Jeszcze nie wypróbowane: dźwięk tła mapy i lista muzyki
podstępu (wiadomo o niej z tego, jak działa gra). Komunikaty błędów RUSE Decoy są na razie tylko po angielsku.

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Music-and-Sounds]]
