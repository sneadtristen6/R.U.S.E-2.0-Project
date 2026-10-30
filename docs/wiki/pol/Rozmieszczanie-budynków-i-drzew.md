# Rozmieszczanie budynków i drzew

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.7.2 i moda (Siatka, Prostokąt, Ścieżka, Zaznacz i Ponów: 0.9.8.7;
> własne modele: 0.9.8.8) · **Sprawdzone w grze:** postawione budynki widać przy każdym przybliżeniu, do 8× ich
> rozmiaru, a jednostki je omijają. Jeszcze nie sprawdzone w grze: to, co postawiono Siatką, Prostokątem i Ścieżką,
> oraz przesunięte obiekty

## Stawianie

1. Na pasku kliknij **Budynki** albo **Obiekty i drzewa**, a potem jego zakładkę **Obiekty** lub **Drzewa**.
2. Wybierz typ z obrazków (wpisz coś w polu wyszukiwania, by je zawęzić). Każdy obrazek jest rysowany z własnego
   modelu gry, a liczba w jego rogu mówi, ile ma ich już mapa. Lista zawiera własne typy tej mapy: gra przyjmuje
   tylko typ, którego mapa już używa.
3. Wybierz, jak stawia kliknięcie:
   - **Jeden**: jeden obiekt tam, gdzie klikniesz;
   - **Obszar**: przeciągnij, by rozsiać obiekty w kole (**Odstęp** trzyma je z dala od siebie, **Obszar** ustala
     koło);
   - **Linia**: kliknij początek, potem koniec, by postawić rząd (żywopłot, ulicę, szpaler drzew), obrócony wzdłuż
     niego;
   - **Siatka**: rzędy obiektów: kliknij, gdzie pierwszy rząd się zaczyna i gdzie się kończy, potem odsuń rzędy
     i kliknij (**Między rzędami** ustala odstęp);
   - **Prostokąt**: przeciągnij prostokąt na terenie i puść: wypełnia się wybranym obiektem w rzędach;
   - **Ścieżka**: klikaj wzdłuż trasy, potem kliknij dwukrotnie, naciśnij **Enter** albo **Zakończ**: obiekty idą
     gładką krzywą przez twoje kliknięcia (żywopłot, szpaler drzew); z szerokością powstaje ich pas. **Esc** porzuca
     niedokończoną siatkę, linię lub ścieżkę.
4. **Frontem do dróg:** blisko drogi obiekt staje obok niej i obraca się do niej frontem, a rząd biegnie wzdłuż niej;
   siatka lub prostokąt zostawia drogi wolne. Suwak obrotu nadal go obraca (spróbuj 180°, jeśli dom pokazuje tył).
5. **Obrót** i **Rozmiar** (do 10×) to suwaki po prawej. Drzewa same trochę różnią się rozmiarem i obrotem, więc las
   nie wygląda jak odbity stemplem.

Przed kliknięciem typ widać półprzezroczyście pod kursorem, obrócony i w takim rozmiarze, w jakim stanie. Postawione
obiekty pokazują się jako ich własne modele, każdy z małą złotą kropką u stóp, która oznacza go z daleka.

## Zaznaczanie, przesuwanie, obracanie, usuwanie

**Zaznacz** (na panelach **Budynki** oraz **Obiekty i drzewa**) wybiera to, co stoi na mapie: to, co postawił twój mod,
albo własne obiekty mapy. Kliknij jeden, **Shift+kliknięcie**, by dodać, albo przeciągnij prostokąt wokół kilku. Potem
przeciągnij jeden z zaznaczonych, by je przesunąć, użyj **Obrót** i **Rozmiar** albo **Usuń**. **Przywróć jak na mapie**
cofa twoje zmiany własnych obiektów mapy; **Esc** odznacza wszystko.

## Własne modele

**Importuj model…** (w **Obiekty i drzewa**) robi z modelu 3D (.glb, .gltf lub .3ds) własną skałę, obiekt, krzew lub
drzewo twojego moda mapy. Stawia się go jak własne obiekty gry, na każdej mapie moda, z mniejszymi wersjami zrobionymi
dla niego na średnie i dalekie odległości. Daj mu **Rozmiar** i **Pochodzenie**: model zrobiony przez kogoś innego może
trafić do moda tylko na licencji CC0 lub CC-BY, z podaniem autora. Zaznaczone **Twardy: jednostki go omijają**; bez
zaznaczenia jednostki przejeżdżają przez niego i go przewracają, jak własne małe obiekty gry. **Twój model…** zmienia go
później. Widziane w grze.

## Lite budynki

**Lity** (domyślnie włączony) sprawia, że jednostki omijają postawiony budynek, zamiast przez niego przechodzić.
Wyłącz go dla budynku, który ma być tylko do oglądania.

## Ukrywanie się w nich

Postawione budynki same nie ukrywają jednostek: otwórz **Osłona**, wybierz **Miasto** i kliknij zrobione miasto.

## Cofanie i ponawianie

**Cofnij** (albo **Ctrl+Z**) zabiera ostatni obiekt albo cały obszar, linię, siatkę, prostokąt lub ścieżkę, a także
ostatnie przesunięcie, obrót, zmianę rozmiaru lub usunięcie. **Ponów** (albo **Ctrl+Y**, **Ctrl+Shift+Z**) przywraca
to. Każde narzędzie mapy ma oba.

## Usuwanie drzew i obiektów samej mapy

1. Na pasku kliknij **Usuń** (Studio 0.8.1).
2. Wybierz, co zabiera: **drzewa**, **obiekty**, **budynki** (w dowolnym połączeniu). Każde koło zachowuje to, co
   było wybrane, gdy je namalowano.
3. Przeciągnij po mapie: czerwone koła oznaczają to, co zniknie, a to, co obejmują, jest zabarwione na czerwono.
   **Rozmiar** ustala koła; panel narzędzi liczy, co zabiorą, gdy mod zostanie zbudowany.

Tam, gdzie znikają drzewa, teren otwiera się dla wszystkich jednostek i traci osłonę lasu (sprawdzone w grze: czołgi
wjeżdżają do wyczyszczonego lasu, piechota nie jest tam ukryta). Usunięte budynki też otwierają swój teren dla
jednostek. **Cofnij** (**Ctrl+Z**) zabiera ostatnie przeciągnięcie, **Zacznij od nowa** usuwa wszystkie koła z mapy.

**Dalej:** [[Edycja scenariusza|Edycja-scenariusza]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Place-Buildings-and-Trees]]
