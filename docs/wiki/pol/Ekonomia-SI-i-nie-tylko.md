# Ekonomia, SI i nie tylko: narzędzia LittleGroove'a

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.9.8.1 lub nowszego i moda · **Czas:** tyle, ile chcesz

RUSE-Mod-Manager LittleGroove'a miał narzędzia, których Studio nie miało. Teraz są w Studio, każde w twoim własnym modzie:
zmiana jest tam zapisywana od razu, a pliki gry nigdy nie są ruszane.

## Zakładka Ustawienia SI i graczy

Jedna zakładka w trzech częściach: **Ustawienia graczy**, **Zasady gry** i **Gracze komputerowi**.

### Ustawienia graczy

Pieniądze na start i dochód, składy zaopatrzenia (pieniądze na ciężarówkę, ciężarówki w konwoju, czas między konwojami),
limity produkcji i karty podstępu, z którymi zaczyna każda strona. Zmiana liczy się w każdym trybie gry; tam, gdzie tryb
nuklearny ma własną wartość, dostaje ona własne pole. Składy zaopatrzenia i budynki administracyjne są budynkami: ich cena,
czas budowy i wytrzymałość są w zakładce **Jednostki**.
Widziane w grze: pieniądze na start i karty podstępu na początku.

**Składy na mapach** (w części Magazyny zaopatrzenia): daj każdemu składowi zaopatrzenia więcej ciężarówek, a więc więcej
pieniędzy, na **Wszystkie mapy** albo **Jedna mapa:** wybierasz sam. Pomnóż ciężarówki każdego składu (**razy ich
ciężarówki**) albo daj wszystkim tę samą liczbę (**ciężarówek każdy**). Wiersz nad tym mówi, ile skład mieści przy twoich
wartościach. Skład, któremu dałeś własne ciężarówki w zakładce Mapy, zachowuje je. W mody z więcej niż 1000 ciężarówek na
skład graj z Launcherem 0.4.8.4 lub nowszym. Widziane w grze (składy D-Day z 500 ciężarówkami; na innych mapach trzy razy
więcej, niż miały).

### Zasady gry

Każda inna zasada, którą gra trzyma dla wszystkich graczy, w grupach: bitwa i kapitulacja, populacja, ruch i drogi,
ogień i cele, jednostki działające same, obrażenia i przyszpilenie, lasy i widzenie, samoloty, karty podstępu w działaniu,
kontroler gry, stawianie budynków, rozgrywki rankingowe online, zarysy i strzałki, efekty na ekranie, kolory stron
i sektorów (każdy z wybieraniem koloru), a na końcu kilka wartości, których zastosowanie nie jest jeszcze znane. Każda mówi,
co robi i jaką wartość ma w grze. Jeszcze nie testowane w grze.

### Gracze komputerowi

Jak grają gracze komputerowi. Gracz komputerowy łączy trzy zestawy wartości: **Domyślny**, swój poziom trudności i swój
profil (oba wybierane w lobby gry); wybierz jeden, by zobaczyć i zmienić jego wartości: kiedy zaczyna atakować, jak silny
chce być, zanim ruszy, jak się broni, jakie jednostki woli i jego karty podstępu. Każdą wartość można zmienić w każdym
zestawie: ta, której zestaw nie wymienia, liczy się w grze jako 0, a nadanie jej liczby dodaje ją do twojego moda. Pod nimi
to, co obowiązuje każdego gracza komputerowego (wartość armii, przy której atakuje, jego atrapy...).
Widziane w grze: karta podstępu usunięta z menu, inna przesunięta w nim, czas trwania karty i to, kiedy Łatwy zaczyna
atakować. Reszta jeszcze nie testowana w grze.

**Skrypty map i misji**, pod spodem: skrypty, które gra uruchamia na swoich mapach (rozdziały kampanii, wyzwania,
Operacje), pokazane jako Python do czytania. **Kopiuj** kopiuje jeden z nich.

## Pole Ulepszenie i badania jednostki

Na stronie jednostki: jednostka, której jest ulepszeniem (**Ulepszenie jednostki**), jej własne ulepszenia oraz cena i czas
jej badania. Wybierz inną jednostkę albo **Żadna: osobna jednostka**. Zobacz [[Edycja jednostek|Edycja-jednostek]].

## Zakładka Wszystkie wartości i pliki

Dwie części, wybierane przełącznikiem nad listą.

**Wszystkie wartości:** dowolny obiekt i dowolna wartość gry, zmienione w twoim modzie: dodaj lub usuń wartość, utwórz lub
usuń obiekt, daj wartości tekstowej własne słowa. Jeszcze nie testowane w grze.

**Pliki:** dowolny plik w paczkach gry: wybierz paczkę, potem plik, by zobaczyć go takim, jaki jest (obraz, tabela tekstów,
skrypt misji...). **Zapisz kopię…** zapisuje go na zewnątrz; **Zamień na mój plik…** wstawia twój plik do moda; **Dodaj
mój plik do tej paczki…** dodaje nowy. Twój mod zachowuje tylko to, co zmieniasz, nigdy kopii pliku gry. Jeszcze nie
testowane w grze.

## Misje i mapy

Skrypty misji można zmieniać, a Studio sprawdza, czy misja jest w menu, czy wczytuje się każdy potrzebny jej plik, i jej
teksty; można ją przesunąć w górę lub w dół jej menu. Na mapie: nazwy miast i wzgórz, nazwane punkty i strefy oraz nazwa
i kierunek elementu mapy. **Notatki** można prowadzić przy jednostce, wartości lub graczu komputerowym. Jeszcze nie
testowane w grze.

## W Launcherze: Przekształć stary mod

Starszy mod w postaci własnych paczek gry, przeznaczony do skopiowania do folderu gry, staje się modem, w który twoja
biblioteka gra obok innych: zobacz [[Instalacja i gra|Instalacja-i-gra]].

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Economy-AI-and-More]]
