# Importowanie modelu

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.9.6 lub nowszego, moda i modelu 3D (.3ds, .glb lub .gltf) ·
> **Czas:** kilka minut

Daj nowej jednostce własny model 3D, z Blendera lub dowolnego innego narzędzia 3D. Tak powstał
[mod M1 Abrams](https://github.com/sneadtristen6/Ruse-Mods): pierwszy model wprowadzony do R.U.S.E. z innego programu 3D,
widziany w grze.

Model może też trafić na nowy budynek, w miejsce części jego wyglądu (zobacz
[[Budynki i menu budowy|Budynki-i-menu-budowy]]), albo na twoją mapę jako własna skała, obiekt, krzew lub drzewo
(zobacz [[Rozmieszczanie budynków i drzew|Rozmieszczanie-budynków-i-drzew]]). Oba: Studio 0.9.8.8, widziane w grze.

Na stronie jednostki wszystko to jest w **Wygląd i ruch**: **Importuj model…** to przycisk wiersza **Model**, a pozostałe opcje modelu (rozmiar, **Przesuń**) są pod **Więcej** tego wiersza. To, co robią animacje modelu, jest pod **Więcej** wiersza **Dźwięki i animacje**. Strona oddziału zaczyna się natomiast od jego żołnierzy, na karcie oddziału: zobacz [[Zmiana oddziału|Zmiana-oddziału]].

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
wejście: **Nowa jednostka z tej…** w wierszu **Model** sekcji **Wygląd i ruch**. (Studio 0.9.6 nie ma jeszcze żadnego z tych przycisków: otwórz
jednostkę i wybierz **Nowa jednostka…** na jej stronie.)

## 3. Import

Na stronie nowej jednostki, w wierszu **Model** sekcji **Wygląd i ruch**:

1. Kliknij **Więcej** i ustaw **Rozmiar**: jej długość w stosunku do skopiowanej jednostki. **1** to ta sama długość; M1 Abrams w stosunku do
   Shermana to **1.36** (ich prawdziwe długości).
2. Kliknij **Importuj model…** (przycisk wiersza) i wybierz plik .3ds lub .glb.

Studio dopasowuje go do jednostki: przodem do przodu (tam, gdzie celuje jego działo), na jej długość, w miejscu, w
którym stoi skopiowana jednostka, z wieżą obracającą się tam, gdzie jest na twoim modelu, stojący na ziemi. Jego obrazy
stają się jego własnymi teksturami. Strona pokazuje go w 3D, razem z tym, które części obracają się z wieżą. Jeśli jakiś
obraz nie został znaleziony, strona mówi który: połóż obrazy obok modelu i zaimportuj go znowu.

Zostaje zapisany w twoim modzie jako `files/models/<the unit's name>.glb`. **Użyj modelu kopiowanej jednostki** znowu go
usuwa.

**Gdzie jest na twoim komputerze:** **Więcej** w wierszu **Model** zaczyna się od tego (strona oddziału mówi to w **Więcej opcji**, pod jego żołnierzami): pełna ścieżka, `Documents\RUSE 2.0\Mods\<twój mod>\files\models\<nazwa jednostki>.glb`, i **Pokaż w folderze**, który otwiera ten folder. Dopóki jednostka nie ma własnego modelu, mówi, gdzie będzie plik. Jednostka z własną kopią modelu (**Daj mu własną kopię modelu** albo **Własny mundur** oddziału) jest trzymana w tym samym folderze, jako `<nazwa jednostki>.copy.toml`, a jej malowanie w folderze o tej samej nazwie.

**Jego rozmiar później:** suwak pod polem rozmiaru idzie od **Malutki** do **Ogromny** (od 0.05 do 20), z zaznaczonymi
**Rozmiar z gry** (1) oraz, dla jednostki z innej epoki, **Jak w rzeczywistości**; kliknij **Zmień rozmiar**, a model
zostanie dopasowany od nowa z jego własnego pliku. Przy kilku nowych samolotach (lub jednostkach lądowych) jedno kliknięcie
zmienia rozmiar wszystkich. Gra czyta model przy wczytywaniu, więc nowy rozmiar widać od następnego budowania.

**Gdzie stoi:** nowy model jest stawiany na środku jednostki, którą kopiuje, więc większości modeli nic tu nie trzeba.
Jeśli twój stoi nie tak, jak trzeba, użyj **Przesuń** pod rozmiarem, w **Więcej** wiersza
Model. Są w niej trzy liczby, **Do przodu**, **W prawo** i **W górę**, w jednostkach gry (strona mówi, jaką
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
jest przesuwane ani skalowane, a pozostali ludzie z oddziału rysowani tym samym modelem też go noszą. Widziane w grze z
oddziałem strzelców, obsługą działa i P-47. Żołnierz z ciężką bronią, którego gra rysuje własnym modelem (żołnierz z
bazooką w amerykańskim oddziale strzelców), zachowuje go, dopóki nie dasz mu modelu w jego własnym wierszu na stronie oddziału (niżej).

**Twoi gracze:** mod z modelem zaimportowanym przez Studio 0.9.8.17 lub nowsze potrzebuje Launchera 0.4.8.17 lub
nowszego: starszy Launcher daje modelowi szkielet skopiowanej jednostki, więc jego wieża obraca się wokół złego punktu.
Wersja 0.4.8.17 to wymagana aktualizacja, więc Launcher instaluje ją sam.

## Własny żołnierz krok po kroku

Przy oddziale (strzelcy, spadochroniarze, dowolna piechota) Studio robi z tobą część w Blenderze. Strona oddziału zaczyna
się od karty oddziału i wiersza dla każdego z jego żołnierzy; [[Zmiana oddziału|Zmiana-oddziału]] przechodzi przez nie.

1. **Utwórz oddział** jak w kroku 2 powyżej, zaczynając od oddziału (na przykład amerykańskiego oddziału strzelców).
2. **Otwórz oddział w Blenderze.** Na karcie oddziału kliknij **Zmień oddział w Blenderze**. Blender otworzy się ze wszystkimi żołnierzami oddziału obok siebie, każdy na swoich kościach, każdy z własną kopią swoich obrazków. Nie masz jeszcze Blendera? **Pobierz Blendera (za darmo)** go instaluje; **Wybierz Blendera…** pokazuje Studiu, gdzie jest.
3. **Zmień żołnierza albo załóż własny model na jego kości.** Żeby go zmienić, edytuj go tam. Własny model: wczytaj go przez **File > Import** do tej samej sceny i połóż na żołnierzu; kliknij swój model, **Shift+klik** na jego kości, potem **Ctrl+P > With Automatic Weights**. Usuń żołnierza z gry, jeśli go nie zostawiasz.
4. **Wyślij.** Kliknij **Wyślij do R.U.S.E. Studio** u góry Blendera.
5. **Przenieś z powrotem.** Na karcie oddziału kliknij **Przenieś moje zmiany**. Każdy żołnierz dostaje tylko to, co zrobiono z nim, a ten, którego nie ruszałeś, zostaje taki, jaki był: karta mówi, kto się zmienił, a kto nie. **Testuj w grze** to pokaże.

Dobrze wiedzieć:
- Czterej strzelcy amerykańskiego oddziału strzelców to w Blenderze jedna figura: gra daje im jeden model, więc to, co z nim zrobisz, noszą wszyscy czterej. Żołnierz z bazooką to osobna figura.
- Twoje pliki Blendera zostają w folderze moda: `Documents\RUSE 2.0\Mods\<twój mod>\blender\<nazwa jednostki>\squad\`. Nie są pakowane do moda, gdy go udostępniasz. **Więcej opcji**, pod żołnierzami, mówi, gdzie są, a jego **Pokaż w folderze** otwiera folder, w którym leżą.
- Zamknąłeś Blendera, zanim przeniosłeś zmiany? Mały przycisk **Przenieś moje zmiany** pod dużym bierze to, co wysłałeś ostatnio.
- Jeśli niektóre punkty modelu nie mają kości (automatyczne wagi Blendera kilka pomijają), strona powie ile: ruszają się tylko z biodrami żołnierza. Pomaluj je na kość w **Weight Paint** i wyślij ponownie.
- Oddział z **Własny mundur**: twój model zajmuje miejsce munduru (jego malowanie zostaje w modzie); gdy każdy żołnierz wróci do wyglądu z gry (**Wróć do wyglądu z gry** w jego wierszu), mundur wraca.
- Masz już .glb zrobiony na kościach żołnierza z gry? **Importuj model…** w wierszu tego żołnierza bierze go tak, jak jest.
- Twój mod trzyma model każdego żołnierza w `files\models\`: strzelców jako `<nazwa jednostki>.glb`, żołnierza z ciężką bronią jako `<nazwa jednostki>@bazooka.glb`. **Więcej opcji** mówi, gdzie jest każdy z nich (albo gdzie będzie), i które inne figury oddziału są nim rysowane: poległy żołnierz i figura widziana z daleka (w amerykańskim oddziale strzelców rysowana modelem żołnierza z bazooką).
- Cały oddział w jednym Blenderze, każdy żołnierz przeniesiony osobno: to nowość, jeszcze niewypróbowana w grze.

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
- **Wszystkie inne czynności** wymieniają resztę, według rodzaju: w miejscu, w ruchu, celowanie i strzelanie, ciężka
  broń, trafienia, śmierć.
- **Na długich trasach** gra wsadza oddział do ciężarówki. Jednostka z własnymi animacjami idzie zamiast tego sama,
  odtwarzając wybraną tam animację (swój bieg, jeśli zostawisz Najbliższą), tak szybko jak jej ciężarówka. Wybierz
  **W swojej ciężarówce**, aby zostawić ciężarówkę.

**Kopia zachowuje animacje:** jednostka skopiowana z takiej, która ma własne animacje, odtwarza te same. Aby zmienić
którąś tylko dla niej, kliknij **Zmień w RUSE Decoy** w jej wierszu **Dźwięki i animacje**, potem **Tylko ta jednostka**.

Uniwersalny oddział konny zrobiony tak w Studiu działał w grze (listopad 2026).
## Model z własnymi kośćmi i animacjami

Koń, koń z jeźdźcem, dowolne stworzenie: model na własnych kościach trafia do oddziału razem ze swoimi animacjami.

1. **Zrób go w Blenderze**: twój model na armaturze z własnymi kośćmi (nazwanymi, jak chcesz) i akcja dla każdej animacji. Nazwij akcje tak, jak to, co pokazują: co najmniej **stand** (lub **idle**), **walk** i **run**; rozpoznawane są też **death**, **fire**, **reload**, **hit**, **crouch**, **aim**, **look**, **flee** i **grenade**.
2. **Wyeksportuj go**: **File > Export > glTF 2.0**, format **glTF Binary (.glb)**, z zaznaczonym **Animation**.
3. **Utwórz oddział** jak w kroku 2 powyżej. Na jego stronie kliknij **Importuj model…** w wierszu strzelców, pod **Każdy żołnierz**, i wybierz swój .glb. Studio widzi, że jego kości nie są kośćmi żołnierza, i bierze go z własnymi kośćmi i wszystkimi animacjami. Strona pokazuje, ile ma kości, każdą animację z jej długością i ile czynności oddziału ją gra.
4. **Testuj w grze** go pokaże.

Dobrze wiedzieć:
- Każda czynność oddziału gra animację nazwaną dla niej. Czynność, dla której żadna animacja nie jest nazwana, nie ma jeszcze żadnej: strona mówi, ile ich jest.
- Zmieniony w Blenderze? Zaimportuj go ponownie: każda czynność zachowa swoją animację, dopóki animacja o tej nazwie jest w pliku.
- Twój mod przechowuje model i każdą animację: `files\models\<nazwa jednostki>.glb`, a każdą animację jako `files\anim\own\<nazwa jednostki>\<jej nazwa>.baf`.
- **Wróć do wyglądu z gry** w tym wierszu znowu usuwa model, razem z jego animacjami.
- Oddział z żołnierzem z ciężką bronią: daj mu własnego konia z jeźdźcem przez **Importuj model…** w jego wierszu, zrobionego na tych samych kościach co model strzelców, a będzie odgrywał ich animacje. Na innych kościach odgrywa to, co w kopiowanym oddziale, a strona ostrzega: to może zatrzymać grę. Usunięcie modelu strzelców usuwa też jego.
- Uniwersalny oddział konny zrobiony tak w Studiu działał w grze (listopad 2026); nic innego zrobionego w ten sposób nie było jeszcze próbowane w grze.

## Jego animacje, zmienione w Blenderze

Animacje zmienia się w RUSE Decoy. Na stronie jednostki w wierszu **Dźwięki i animacje** kliknij **Zmień w RUSE Decoy**, potem **Zmień jego animacje w Blenderze** pod jej animacjami. Blender otworzy się z jednostką i wszystkimi animacjami, które odtwarza (stanie, marsz, bieg, strzał, śmierć…), każdą nazwaną od tego, co w niej robi, a za tym nazwa z gry: `Bieg, celując (fusilier_course_vise)`.

1. **Wybierz jedną.** Na dole Blendera Action Editor je wymienia: wybierz tę do zmiany. **Spacja** ją odtwarza.
2. **Ustaw kości.** Kliknij kość, naciśnij **Ctrl+Tab** dla Pose Mode, **R** aby ją obrócić (**G** przesuwa), potem **I** aby zachować pozę w tej klatce. Zrób to w każdej klatce, którą zmieniasz: Blender sam przechodzi od jednej zachowanej pozy do następnej.
3. **Wyślij ją.** Kliknij **Wyślij do R.U.S.E. Studio**: idą wszystkie animacje, zmienione czy nie.
4. **Przywróć ją.** W RUSE Decoy kliknij **Przenieś moje zmiany**. Powie, które wróciły zmienione: są teraz własne tej jednostki, a RUSE Decoy pokazuje je pod **Tylko ta jednostka**. Każda inna jednostka i każda animacja, której nie ruszałeś, zostaje z gry.

Warto wiedzieć:
- Gra odtwarza animacje z prędkością 30 klatek na sekundę i Blender tak je otwiera. Animacja otwiera się tak długa, jak odtwarza ją gra; wydłuż ją lub skróć w Blenderze, a wróci taka.
- Animacja zrobiona w Blenderze (kopia innej, przemianowana) też wraca, ale żadna akcja jeszcze jej nie odtwarza: Studio to mówi. Przemianowana liczy się jako nowa, a ta, którą była, gra jak wcześniej.
- Kości, na których nie opiera się żaden punkt żołnierza (punkt wylotu lufy, dłoń drugiej broni), można animować, ale automatyczne wagi Blendera je pomijają.
- Własne animacje dostaje tylko nowa jednostka zrobiona w twoim modzie: z jednostki z gry najpierw zrób nową jednostkę.
- Model na własnych kościach (koń, dowolne stworzenie) wysyła własne animacje pod ich własnymi nazwami. Ta, którą zmienisz, zajmuje jej miejsce: każda akcja, która ją odtwarzała, odtwarza ją zmienioną, a wiersz **Dźwięki i animacje** jednostki wymienia ją z innymi.
- Sprawdzone z Blenderem 4.5 i własnymi testami Studia; w grze jeszcze niewypróbowane.

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
- Nowa jednostka skopiowana z jednej z tych: działo holowane, FCM F1, Puma, transporter półgąsienicowy, Bren Carrier,
  samolot dla spadochroniarzy, niektóre bunkry i kilka innych, też przyjmuje model z innego źródła, nie tylko związany z
  jej kośćmi, i jest rysowany tak jak ta jednostka. Jeszcze niewypróbowane w grze.

Z wiersza poleceń: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`. Z `--move` jest dopasowywany tak, jak dopasowuje go
Studio: `--move 50 0 -10` przesuwa go o 50 do przodu i o 10 w dół od miejsca dopasowania (do przodu, w prawo, w górę), a
`--move 0 0 0` zostawia go tam. Bez `--move` polecenie dalej dopasowuje go po staremu, z wieżą na wieży skopiowanej
jednostki.

**Dalej:** [[Eksport i udostępnianie|Eksport-i-udostępnianie]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Import-a-Model]]
