# Budynki i menu budowy

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.9.8.8 lub nowszego i moda · **Zajmuje:** kilka minut

Budynki każdej nacji, to, co oferują ich menu budowy i w jakiej kolejności, oraz własne budynki. Widziane w grze.

## Tablica budynków

Otwórz zakładkę **Nacje**: pod każdą nacją **Budynki i jednostki** pokazuje jej budynki jako wiersze, każdy będący
rzędem jednostek, które oferuje menu budowy tego budynku, w kolejności z gry. Obok nazwy każdej nacji **Zachowaj jednostki** przywraca wszystkie jej jednostki do menu budowy, jak w grze, a **Zacznij pusty** usuwa je wszystkie, żebyś sam zapełnił jej budynki. **Badania**, nad nacjami: **Bez badań** sprawia, że każdą jednostkę każdej nacji można budować od początku; **Zachowaj badania z gry** przywraca jednostkom z gry ich badania. Oba najpierw pytają.

- **+** dodaje jednostkę do budynku: jedną z własnych jednostek nacji, kopię jednostki innej nacji albo
  [[jednostkę z innej epoki|Jednostki-z-innych-epok]]. Kopia trafia do twojego moda, nazwana tak, jak nazywa ją gra.
- **Przeciągnij** jednostkę wzdłuż jej wiersza, by zmienić jej miejsce w menu, albo na inny budynek, by budować ją
  tam.
- **×** wyjmuje jednostkę z menu budowy. Jest ukryta, nie usunięta: jednostka nadal jest w plikach gry.
- **Badanie…**, potem **Umieść pod tą** na jednostce, po której ma przyjść: jest badana z tamtej (w dowolnym z budynków
  nacji). **Do zbudowania od początku** nie wymaga badania. **Koszt badania** i **Czas badania (s)** są obok.

Każdy wiersz mówi, ile ma jednostek. Budynek, któremu nie zostało nic do budowania, pokazuje w grze, gdy się go wybierze,
listę budynków kwatery głównej. Więcej niż 10 jednostek w jednym budynku, samolot w budynku lądowym albo pojazd na
Lotnisku: jeszcze nie sprawdzone w grze.

Strona jednostki w zakładce **Jednostki** mówi, gdzie jest budowana („Budowana w budynku BAZA CZOŁGÓW: miejsce 2
z 6”), a **Pokaż w budynkach** otwiera jej wiersz.

## Grupy

W grze lista budowy budynku pokazuje każdą grupę w jednym rzędzie: jednostkę i jej ulepszenia (Panzer IV i Panther).
Tablica pokazuje grupy każdego budynku, każdą z jej liczbą (**4 z 6**), i ile grup ma budynek (**7 z 10 grup**).

- Nowa jednostka trafia do grupy swojego rodzaju w swoim budynku albo do osobnej grupy, gdy budynek nie ma żadnej tego
  rodzaju. **+** przy grupie albo upuszczenie na nią umieszcza ją tam; **Nowa grupa** zaczyna nową.
- Grupa mieści najwyżej 6 (jej jednostki i karty badań), a budynek najwyżej 10 grup, żeby jego lista zmieściła się na
  ekranie. Kolejna jest odrzucana: wyjmij jednostkę albo umieść ją w budynku z własnymi jednostkami (**Dodaj budynek…**).
- Jednostka bez typu karty w grze (ciężarówka, wyrzutnia V2): wybierz jej grupę.

Jeszcze nie sprawdzone w grze.

## Dodaj budynek

**Dodaj budynek…** pod tablicą nacji: wybierz budynek gry, który kopiuje (**Kopia budynku**), w polu **Nazwa**
nadaj mu nazwę, potem jedno z dwojga:

- **Buduje te same jednostki co skopiowany budynek**, albo
- **Buduje własne jednostki**: własny wiersz i własna karta na pasku budowy gry, wypełniane przyciskiem **+**. Do trzech
  na nację.

Drugi i trzeci budynek z własnymi jednostkami wymagają małej łatki gry na więcej budynków. Studio pobiera ją raz
i wstawia tylko do twojej zmodowanej kopii gry, nigdy do gry w twoim folderze Steam.

## Własny wygląd budynku

Na stronie nowego budynku **Importuj model…** wstawia własny model 3D (.glb, .gltf lub .3ds) w miejsce jednej części
wyglądu, który kopiuje: głównego budynku fabryki lub kwatery głównej albo części, którą wybierzesz. Twój model dostaje
rozmiar tej części i stoi tam, gdzie ona stała; reszta wyglądu zostaje. Własne budynki gry pozostają takie, jakie są:
najpierw zrób z jednego z nich nowy budynek.

**Jego obraz w menu budowy:** obracaj i przybliżaj model, aż będzie dobrze wyglądał w przerywanej ramce, potem użyj
tego widoku. Zobacz [[Importowanie modelu|Importowanie-modelu]], by dowiedzieć się o modelach ogólnie.

## Co widziano w grze

Widziane: zmiany na tablicy (jednostki dodane, przesunięte, wyjęte, badane z innej), skopiowany budynek, budynek
z własnymi jednostkami i jego karta na pasku budowy, drugi i trzeci taki budynek z łatką gry oraz własny model i obraz
budynku.

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Buildings-and-Build-Menus]]
