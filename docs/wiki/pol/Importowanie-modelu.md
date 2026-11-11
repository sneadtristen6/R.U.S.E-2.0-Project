# Importowanie modelu

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.9.6 lub nowszego, moda i modelu 3D (.3ds, .glb lub .gltf) ·
> **Czas:** kilka minut

Daj nowej jednostce własny model 3D, z Blendera lub dowolnego innego narzędzia 3D. Tak powstał
[mod M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods): pierwszy model wprowadzony do R.U.S.E. z innego programu 3D,
widziany w grze.

Model może też trafić na nowy budynek, w miejsce części jego wyglądu (zobacz
[[Budynki i menu budowy|Budynki-i-menu-budowy]]), albo na twoją mapę jako własna skała, obiekt, krzew lub drzewo
(zobacz [[Rozmieszczanie budynków i drzew|Rozmieszczanie-budynków-i-drzew]]). Oba: Studio 0.9.8.8, widziane w grze.

## 1. Zdobądź model

Plik **.3ds** z jego obrazami (.tga lub .png) albo **.glb** lub **.gltf** (obrazy są w środku: PNG, JPG lub WebP).
Model, którego importer nie umie przeczytać (skompresowane siatki, obrazy KTX2), mówi o tym i jak to naprawić
w Blenderze.

- **Z Blendera:** File > Export > glTF 2.0, format **glTF Binary (.glb)**.
- **Ze strony z darmowymi modelami:** wiele czołgów jest w .3ds z folderem obrazów .tga. Zostaw folder taki, jaki
  przyszedł: Studio znajduje obrazy obok .3ds lub w folderze wyżej, nawet pod skróconymi nazwami, których używają pliki
  .3ds (`MAIN_DEF.TGA` zamiast `Main_Defuse.tga`).
- Sprawdź licencję modelu, zanim udostępnisz mod, i podziękuj jego autorowi w README swojego moda.

**Co pomaga:** części nazwane od tego, czym są. Studio obraca część z *turret* w nazwie (albo *tourelle*, *tower*) razem
z wieżą, a część z *barrel*, *gun* lub *cannon* też razem z nią. Część osadzona na wieży również obraca się z nią.
Wszystko inne porusza się z kadłubem. Działo powinno być skierowane prosto przed siebie.

Przykład Abramsa: **„Tank Abrams” autorstwa ags**, za darmo na
[downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/) (plik .3ds i jego obrazy .tga,
części nazwane Main_Body, Main_Turre, Main_Barre...).

## 2. Zrób jednostkę

W zakładce **Jednostki** kliknij u góry **Nowa jednostka (import modelu)**, potem wybierz jednostkę, od której zaczynasz
(dla czołgu czołg: Shermana dla Abramsa). Nadaj jej nazwę i kliknij **Utwórz**: strona nowej jednostki otwiera się przy
**Importuj model…**. Model nowej jednostki będzie się obracał i jeździł jak ta jednostka. Strona jednostki z gry ma to samo
wejście: **Nowa jednostka z tej…** pod **Własny model**. (Studio 0.9.6 nie ma jeszcze żadnego z tych przycisków: otwórz
jednostkę i wybierz **Nowa jednostka…** na jej stronie.)

## 3. Import

Na stronie nowej jednostki, pod **Własny model**:

1. Ustaw **Rozmiar**: jej długość w stosunku do skopiowanej jednostki. **1** to ta sama długość; M1 Abrams w stosunku do
   Shermana to **1.36** (ich prawdziwe długości).
2. Kliknij **Importuj model…** i wybierz plik .3ds lub .glb.

Studio dopasowuje go do jednostki: przodem do przodu (tam, gdzie celuje jego działo), na jej długość, w miejscu, w
którym stoi skopiowana jednostka, z wieżą obracającą się tam, gdzie jest na twoim modelu, stojący na ziemi. Jego obrazy
stają się jego własnymi teksturami. Strona pokazuje go w 3D, razem z tym, które części obracają się z wieżą. Jeśli jakiś
obraz nie został znaleziony, strona mówi który: połóż obrazy obok modelu i zaimportuj go znowu.

Zostaje zapisany w twoim modzie jako `files/models/<the unit's name>.glb`. **Użyj modelu kopiowanej jednostki** znowu go
usuwa.

**Jego rozmiar później:** suwak pod polem rozmiaru idzie od **Malutki** do **Ogromny** (od 0.05 do 20), z zaznaczonymi
**Rozmiar z gry** (1) oraz, dla jednostki z innej epoki, **Jak w rzeczywistości**; kliknij **Zmień rozmiar**, a model
zostanie dopasowany od nowa z jego własnego pliku. Przy kilku nowych samolotach (lub jednostkach lądowych) jedno kliknięcie
zmienia rozmiar wszystkich. Gra czyta model przy wczytywaniu, więc nowy rozmiar widać od następnego budowania.

**Gdzie stoi:** nowy model jest stawiany na środku jednostki, którą kopiuje, więc większości modeli nic tu nie trzeba.
Jeśli twój stoi nie tak, jak trzeba, otwórz sekcję **Przesuń** pod rozmiarem (zostaje otwarta przy modelu już
przesuniętym). Są w niej trzy liczby, **Do przodu**, **W prawo** i **W górę**, w jednostkach gry (strona mówi, jaką
długość ma skopiowana jednostka w tych jednostkach). Minus to przeciwny kierunek, a 0, 0, 0 przywraca go tam, gdzie
został dopasowany. Kliknij przycisk **Przesuń**, a model zostanie dopasowany od nowa z jego własnego pliku, przesunięty
o tyle; jego wieża i śmigła idą razem z nim, więc dalej obracają się we właściwym miejscu. W widoku 3D niebieski
pierścień to miejsce, w którym stoi skopiowana jednostka, a znak na pierścieniu to przód. Nowy rozmiar zachowuje
przesunięcie. Model związany z kośćmi jednostki (żołnierz, obsługa działa) zostaje tam, gdzie są jego kości: taki
przesuń w Blenderze. Model zaimportowany przed Studio 0.9.8.17 zachowuje swoje stare miejsce (wieżę na wieży skopiowanej
jednostki), nawet po zmianie rozmiaru, dopóki nie zaimportujesz go ponownie albo go nie przesuniesz; modele jednostek z
innej epoki zachowują swoje.

**Samoloty:** samolot otwarty w Blenderze ze Studio i przeniesiony z powrotem jest zwrócony do przodu i ma śmigła tam,
gdzie ma je twój model, tyle, ile ich ma, bez względu na to, jakie miał samolot, który kopiuje: łopaty na ziemi,
wirujące tarcze w powietrzu. Widziane w grze. Model z dowolnego innego źródła zachowuje śmigła tak, jak je narysowano,
nieruchome: importer nie umie jeszcze rozpoznać, które jego części są śmigłami. W widoku 3D tarcze samolotu są
półprzezroczyste, tak jak gra rysuje obracające się śmigło.

**Żołnierze, obsługa dział i więcej samolotów:** żołnierze, obsługa działa i samoloty, do których Studio wcześniej nie
umiało dopasować modelu (na przykład P-47), też mogą dostać własny model, jeśli jest związany z kośćmi jednostki: na
przykład jeden z modeli gry otwarty w Blenderze ze Studio i tam zmieniony. Trafia na te kości taki, jaki jest, nic nie
jest przesuwane ani skalowane, a pozostali ludzie z oddziału z tymi samymi kośćmi też go noszą. Widziane w grze z
oddziałem strzelców, obsługą działa i P-47.

**Twoi gracze:** mod z modelem zaimportowanym przez Studio 0.9.8.17 lub nowsze potrzebuje Launchera 0.4.8.17 lub
nowszego: starszy Launcher daje modelowi szkielet skopiowanej jednostki, więc jego wieża obraca się wokół złego punktu.
Wersja 0.4.8.17 to wymagana aktualizacja, więc Launcher instaluje ją sam.

## Własny żołnierz krok po kroku

Przy oddziale (strzelcy, spadochroniarze, dowolna piechota) Studio robi z tobą część w Blenderze:

1. **Utwórz oddział** jak w kroku 2 powyżej, zaczynając od oddziału (np. amerykańskich strzelców).
2. **Otwórz jego żołnierza w Blenderze.** Na stronie nowego oddziału, w części **Własny model**, kliknij **Zmień w Blenderze**. Blender otworzy się z żołnierzem i jego kośćmi, każdą tam, gdzie ma ją gra. Nie masz Blendera? **Pobierz Blendera (za darmo)** go instaluje; **Wybierz Blendera…** pokazuje Studiu, gdzie jest.
3. **Zmień go albo załóż własny model na jego kości.** Żeby go zmienić, edytuj go tam. Własny model: wczytaj go przez **File > Import** do tej samej sceny i połóż na żołnierzu; kliknij swój model, **Shift+klik** na kości, potem **Ctrl+P > With Automatic Weights**. Usuń żołnierza z gry, jeśli go nie zostawiasz.
4. **Wyślij go.** Kliknij **Wyślij do R.U.S.E. Studio** u góry Blendera.
5. **Przenieś go z powrotem.** W Studiu kliknij **Przenieś model**. Każdy żołnierz oddziału nosi twój model: strzelec, żołnierz z bazooką i małe figurki widoczne z daleka. **Testuj w grze** go pokaże.

Dobrze wiedzieć:
- Twoje pliki Blendera zostają w folderze twojego moda: `Documents\RUSE 2.0\Mods\<twój mod>\blender\<nazwa jednostki>\`. Nie trafiają do moda, gdy go udostępniasz. Następne **Zmień w Blenderze** zaczyna od tego, co wysłałeś ostatnio.
- Jeśli niektóre punkty modelu nie mają kości (automatyczne wagi Blendera kilka pomijają), strona powie ile: ruszają się tylko z biodrami żołnierza. Pomaluj je na kość w **Weight Paint** i wyślij ponownie.
- Oddział z **Własny mundur**: twój model zajmuje miejsce munduru (jego malowanie zostaje w modzie), a **Użyj modelu kopiowanej jednostki** przywraca mundur.
- Masz już .glb zrobiony na kościach żołnierza z gry? **Importuj model…** weźmie go tak, jak jest.
- Model, który nosi twój oddział, jest trzymany w folderze moda jako `files\models\<nazwa jednostki>.glb`, gdy już jest w środku.

## Jej animacje: którą odtwarza każda czynność

Model na własnych kościach (koń, koń z jeźdźcem, dowolne stworzenie) przynosi ze sobą swoje animacje. Na stronie
jednostki **Jej animacje** pokazują, co jednostka odtwarza przy każdej czynności w grze:

- **Stoi w miejscu**, **Idzie** i **Biegnie** są pierwsze: to minimum, którego potrzebuje model. Jeśli któraś nie ma
  nic własnego, strona to mówi i pokazuje, co odtwarza zamiast tego.
- Każda czynność to lista animacji modelu. Wybierz jedną albo zostaw **Najbliższą**: wtedy odtwarza najbardziej
  podobną, jaką ma model, a lista mówi którą. Najbliższa to po kolei: animacja nazwana tak jak czynność (stand lub
  idle, walk, run lub gallop, fire, death...), a jeśli jej nie ma, to co odtwarza najbliższa czynność (chód odtwarza
  bieg, bieg chód, potem stanie; strzał celowanie, potem stanie; każda śmierć zwykłą śmierć). Budowanie stosuje tę samą
  zasadę: to, co mówi strona, odtwarza gra.
- Animacja, której nazwa zaczyna się od t_ lub b_ (hr_t_fire, hr_b_run), działa tylko na górnej albo dolnej połowie
  ciała: jeźdźca u góry, jego konia na dole.
- **Wszystkie inne czynności** otwierają resztę, według rodzaju: w miejscu, w ruchu, celowanie i strzelanie, ciężka
  broń, trafienia, śmierć.
- **Na długich trasach** gra wsadza oddział do ciężarówki. Jednostka z własnymi animacjami idzie zamiast tego sama,
  odtwarzając wybraną tam animację (swój bieg, jeśli zostawisz Najbliższą), tak szybko jak jej ciężarówka. Wybierz
  **W swojej ciężarówce**, aby zostawić ciężarówkę.

**Kopia zachowuje animacje:** jednostka skopiowana z takiej, która ma własne animacje, odtwarza te same. Aby zmienić
którąś tylko dla niej, użyj RUSE Decoy.

Jeszcze nie sprawdzone w grze w wykonaniu Studia; Horse Squad zrobiony w ten sam sposób ręcznie działał w grze
(listopad 2026).

## 4. Jego karta, potem test

Obracaj widok 3D, aż nowy model będzie dobrze wyglądał w przerywanej ramce, i kliknij **Użyj tego widoku jako karty**
(zobacz [[Edycja jednostek|Edycja-jednostek]]). Potem **Testuj w grze**: jednostka czeka w swojej fabryce w bitwie.

## Zmień go w Blenderze

`files/models/<the unit's name>.glb` otwiera się w Blenderze jak każdy plik .glb. Zachowaj dwie nazwy obiektów (`chassis`
dla kadłuba, `tourelle_01` dla wieży) i wyeksportuj go na ten sam plik (glTF Binary): następne budowanie go użyje.

**Otwórz w Blenderze** na stronie jednostki nazywa kość każdej części tak jak gra, więc jeden z własnych czołgów gry
otwarty w Blenderze i zaimportowany z powrotem zachowuje obracającą się wieżę (Studio 0.9.8.8; model wyeksportowany
wcześniej ma stare nazwy: otwórz go w Blenderze jeszcze raz).

**Model, który stał w złym miejscu** (Studio 0.9.8.7 i wcześniejsze, na nowych jednostkach zrobionych z Panthera i 85
innych jednostek, których wieże Studio źle odczytywało): użyj znowu **Importuj model…** na tej jednostce, a model
stanie na wieży.

## Wczesna wersja

- Gąsienice i koła jeszcze się nie obracają: poruszają się z kadłubem.
- Błysk działa i wrak są ze skopiowanej jednostki.
- Obrazy mają najwyżej 1024 piksele szerokości, jak własne obrazy jednostek gry.
- Wypróbowane w grze z własnymi modelami gry (Sherman, dwa samoloty, oddział strzelców, obsługa działa): jeszcze nie z
  modelem z innego źródła, innym czołgiem z wieżą, wieżą obracającą się dookoła ani samolotem kopiującym jednostkę bez
  śmigieł.

Z wiersza poleceń: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. Z `--move` jest dopasowywany tak, jak dopasowuje go
Studio: `--move 50 0 -10` przesuwa go o 50 do przodu i o 10 w dół od miejsca dopasowania (do przodu, w prawo, w górę), a
`--move 0 0 0` zostawia go tam. Bez `--move` polecenie dalej dopasowuje go po staremu, z wieżą na wieży skopiowanej
jednostki.

**Dalej:** [[Eksport i udostępnianie|Eksport-i-udostępnianie]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Import-a-Model]]
