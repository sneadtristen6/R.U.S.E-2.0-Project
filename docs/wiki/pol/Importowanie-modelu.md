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

Studio dopasowuje go do jednostki: przodem do przodu (tam, gdzie celuje jego działo), na jej długość, z pierścieniem wieży
na wieży skopiowanej jednostki, stojący na ziemi. Jego obrazy stają się jego własnymi teksturami. Strona pokazuje go
w 3D, razem z tym, które części obracają się z wieżą. Jeśli jakiś obraz nie został znaleziony, strona mówi który: połóż
obrazy obok modelu i zaimportuj go znowu.

Zostaje zapisany w twoim modzie jako `files/models/<the unit's name>.glb`. **Użyj modelu kopiowanej jednostki** znowu go
usuwa.

**Jego rozmiar później:** suwak pod polem rozmiaru idzie od **Malutki** do **Ogromny** (od 0.05 do 20), z zaznaczonymi
**Rozmiar z gry** (1) oraz, dla jednostki z innej epoki, **Jak w rzeczywistości**; kliknij **Zmień rozmiar**, a model
zostanie dopasowany od nowa z jego własnego pliku. Przy kilku nowych samolotach (lub jednostkach lądowych) jedno kliknięcie
zmienia rozmiar wszystkich. Gra czyta model przy wczytywaniu, więc nowy rozmiar widać od następnego budowania.

**Samoloty:** samolot otwarty w Blenderze ze Studio i przeniesiony z powrotem zachowuje obracające się śmigła i jest
zwrócony do przodu. Widziane w grze.

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

Z wiersza poleceń to samo: `ruse import-model "Tank Abrams.3ds" --like coc_shermanm4_tir --unit
Descriptor_Unit_R2_M1_Abrams --size 1.36 --mod <your mod folder>`.

**Dalej:** [[Eksport i udostępnianie|Eksport-i-udostępnianie]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Import-a-Model]]
