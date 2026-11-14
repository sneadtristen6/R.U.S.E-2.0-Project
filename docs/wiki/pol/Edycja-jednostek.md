# Edycja jednostek

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio i moda · **Czas:** tyle, ile chcesz

## Znajdź jednostkę

Zakładka **Jednostki** wymienia każdą jednostkę i każdy budynek. Zawęź listę za pomocą:

- pola **Szukaj** (nazwy kodowe lub nazwy, które widzą gracze, w dowolnym z dziesięciu języków gry: przycisk języka u góry).
  Każde wpisane słowo musi pasować; **#tagi** zawężają listę (`#us`, `#germany`, `#air`, `#armor`, `#new` dla nowych
  jednostek twojego moda; wpisz `#`, by zobaczyć wszystkie), a twoje ostatnie wyszukiwania są zachowywane;
- etykiet **Rodzaj** i **Nacja**;
- menu **typ**: do czego jednostka służy, np. kwatera główna, pieniądze, fabryki, forty i atrapy dla budynków, albo
  fabryka, która ją buduje.

## Zmień wartość

1. Kliknij jednostkę. Jej wartości są wymienione według sekcji (cena, pancerz, prędkość, broń...).
2. Wpisz nową wartość. Zostaje od razu zapisana w twoim modzie; obok widać wartość z gry.
3. **Cofnij** obok wartości przywraca wartość z gry.

## Flagi: czym jednostka jest i co potrafi

Flagi to przełączniki włącz/wyłącz, ponumerowane od 0 do 104, które mówią grze, czym jest jednostka (samolot, ciężarówka,
piechota, budynek...) i co potrafi (wjechać do lasu, widzieć dookoła, strzelać tylko na rozkaz...). Na stronie jednostki
widać je jako etykiety, każda ze swoją nazwą: najedź na jedną, by zobaczyć dokładnie, co robi, jak jej używać i na ile
jesteśmy tego pewni. Krzyżyk usuwa flagę; **Dodaj flagę…** dodaje nową, z listy posortowanej według tego, do czego flagi
służą.

**Przewodnik po flagach: wszystkie wyjaśnione** (pod flagami) otwiera całą listę, z polem wyszukiwania. O każdej fladze
mówi:

- **Co to jest i co robi** w grze;
- **Jak jej używać**;
- **Jak pewni jesteśmy:** *sprawdzone w grze*, *z jednostek gry* (co mają wspólnego jednostki gry, które ją mają),
  *oczekiwane, jeszcze niesprawdzone*, *gra ustawia ją sama* (gra włącza je i wyłącza w trakcie działania: na liście
  jednostki nic nie robią) lub *nieużywana*.

**Studio sprawdza flagi każdej jednostki** za każdym razem, gdy je zmieniasz, i jeszcze raz przed startem gry:

- **Znane awarie zatrzymują budowanie**, więc gra nigdy z nimi nie startuje. Strona jednostki mówi dlaczego i proponuje
  poprawkę (**Usuń 62**, **Dodaj 100**):
  - 62 (ciężarówka) lub 63 (ciężarówka budowlana) na czymkolwiek, co nie jest ciężarówką: gra się wywraca na starcie
    meczu;
  - 99 (samolot zwiadowczy) na samolocie z bronią, bez 100 (myśliwiec): gra się wywraca, gdy samolot zostaje wysłany do
    ataku. Użyj pola **Rola** (Zwiadowczy zachowuje swoje ataki) albo dodaj 100;
  - 59 (transport spadochroniarzy) na czymkolwiek innym niż samolot albo na samolocie bez jednostki do zrzucenia.
- **To, co według oczekiwań psuje jednostkę, jest ostrzeżeniem**, a nie zatrzymaniem: 2 (samolot) na jednostce lądowej,
  4 (budynek) lub 49 na jednostce, 6 lub 76 na jednostce, która powinna się ruszać (stoi w miejscu), 42 (piechota) na
  pojeździe, albo zdjęcie 43 (jej drużyna ją liczy) lub 22 (gracz może wydawać jej rozkazy).

Przydatne, sprawdzone w grze: zdejmij razem **11, 21 i 55**, by wpuścić pojazd do lasu; **1** daje dowolnej jednostce
ogień pośredni; **71** widzi dookoła; **77** strzela tylko na rozkaz.

**Własne typy flag** (Studio 0.9.8.8): **Utwórz lub zmień typy flag…** pod flagami jednostki tworzy nazwany zestaw flag
gry, każda ustawiona na **Wł.** lub **Wył.**, z jednym zdaniem o tym, do czego służy. **Nadaj typ flag…** na dowolnej
jednostce włącza i wyłącza te flagi za jednym razem; zdjęcie go przywraca flagi jednostki takie, jakie były. Zmień typ,
a zmienia się też każda jednostka, która go ma. Gra reaguje tylko na własne flagi, więc typ łączy to, co one już robią.
Jeszcze nie sprawdzone w grze.

## Zrób nową jednostkę

Nowa jednostka zaczyna jako kopia jednostki z gry, z własną nazwą, więc możesz ją zmieniać bez ruszania oryginału.
Zakładka Jednostki ma u góry dwa przyciski: **Zmień jednostkę** (lista, potem wartości jednostki i Blender) oraz
**Nowa jednostka (import modelu)**. Przy **Nowa jednostka** wybierz jednostkę, od której zaczynasz, nadaj jej nazwę
i kliknij **Utwórz**; potem zmieniaj ją jak każdą inną. Albo wybierz jednostkę i na jej stronie wybierz **Nowa jednostka…**.

## Zmień wygląd jednostki

Strona jednostki pokazuje jej **Model 3D**: przeciągnij, by go obrócić, przewiń, by przybliżyć.

Pod spodem **Wygląd i ruch** zbiera wszystko o tym, jak jednostka wygląda i się porusza, wiersz na każdą rzecz, w
kolejności, w jakiej pracujesz: **Model**, **Jego żołnierze** (oddział, którego strzelcy i żołnierz z ciężką bronią
mają różne modele), **Dźwięki i animacje** i **Jedzie w**. Każdy wiersz mówi, co jednostka ma teraz, i ma jeden
przycisk do zwykłej czynności; **Więcej** pokazuje na miejscu pozostałe opcje tego wiersza. Wszystko, co zmienisz, od
razu zapisuje się w twoim modzie: nic do zapisywania, żadnego folderu do wybierania. Przemalowanie, własna kopia
modelu, mundur oddziału i własny model są w wierszu **Model**; dźwięki i animacje zmieniasz w RUSE Decoy z wiersza
**Dźwięki i animacje** (**Zmień w RUSE Decoy**): animację tylko dla tej jednostki albo dla wszystkich jednostek, które
jej używają, dźwięk dla wszystkich jednostek, które go używają.

- **Zmień w Blenderze:** kliknij **Otwórz w Blenderze** (Blender jest darmowy; jeśli Studio go nie znajdzie, strona
  proponuje **Pobierz Blendera (za darmo)** i **Wybierz Blendera…**, by wskazać, gdzie jest `blender.exe`). Jednostka
  otwiera się ze swoimi obrazami, gotowa do malowania na modelu. Maluj, potem kliknij **Przenieś moje zmiany**: twoje
  malowanie trafia do twojego moda. Widziane w grze, z bliska i z daleka.
  Jednostka twojego moda otwiera się cała, jej model i malowanie zaznaczone w **Co trafia do Blendera**: odznacz model, żeby tylko malować. Cały jej model przez Blendera nie był jeszcze sprawdzany w grze.
- **Jej karta w menu budowy:** obracaj i przybliżaj model 3D, aż będzie dobrze wyglądał w przerywanej ramce, potem
  kliknij **Użyj tego widoku jako karty**. **Karta z gry** przywraca poprzednią. Widziane w grze. Nowa jednostka ma
  własną kartę: jednostka, którą kopiuje, zachowuje swój obraz.
- **Własna kopia modelu:** jednostka rysowana modelem z gry dzieli malowanie z każdą jednostką rysowaną tym samym
  modelem. **Daj mu własną kopię modelu** (na jej stronie) robi ten sam model z własnymi teksturami: wtedy **Otwórz w
  Blenderze** maluje tylko tę jednostkę. Działa dla nowych jednostek i dla tych z gry.
- **Mundur oddziału:** żołnierze jednej nacji w grze noszą wszyscy jeden obraz (USA: jej GI, Rangersi i spadochroniarze
  oraz załogi jej dział i pojazdów), więc **Domyślny mundur** nie jest tu przemalowywany. Wybierz **Własny mundur**, by dać
  oddziałowi własny, potem pomaluj go w Blenderze. Widziane w grze.
- **Jedzie w:** ciężarówka, w którą oddział lub działo zamienia się na drogach: ta z gry, innej nacji albo kopia
  ciężarówki, którą zrobiłeś i przemalowałeś. Widziane w grze.
- **Własny model (nowe jednostki):** **Importuj model…** wczytuje model 3D z Blendera lub dowolnego narzędzia 3D. Zobacz
  [[Importowanie modelu|Importowanie-modelu]]. Jednostka z gry zachowuje swój model: jej strona ma **Nowa jednostka z tej…**,
  by zrobić nową jednostkę, na którą trafi model.
- **Gdzie jest trzymany jej model:** **Więcej** w wierszu **Model** zaczyna się od tego, gdzie twój mod trzyma własny model jednostki na twoim komputerze (albo będzie go trzymał, gdy już go dostanie), z **Pokaż w folderze**, by otworzyć ten folder. **Zmień w Blenderze** oddziału mówi, gdzie są trzymane twoje pliki Blendera, z własnym **Pokaż w folderze**.
- **Nowa jednostka od początku do końca:** **Nowa jednostka (import modelu)** u góry zakładki Jednostki, wybierz
  jednostkę wyjściową (czołg dla czołgu, oddział dla żołnierzy albo konia z jeźdźcem), nazwij ją i kliknij **Utwórz**.
  Potem przejdź w dół przez **Wygląd i ruch**: jej model, jej żołnierzy, jej animacje, jej dźwięki, jej ciężarówkę.
  Daj jej kartę, ustaw cenę i wartości, potem **Testuj w grze**. Duży mod z wieloma nowymi jednostkami to te same
  kroki dla każdej: każda jednostka trzyma to wszystko w twoim modzie pod własną nazwą.
- **Jednostka, która niesie swojego jeźdźca (koń, motocykl):** jeden model z jeźdźcem i tym, na czym jedzie, na jednym
  szkielecie, z własnymi animacjami (co najmniej stanie, chód i bieg), zaimportowany na skopiowany oddział: zobacz
  [[Importowanie modelu|Importowanie-modelu]], część o modelu z własnymi kośćmi i animacjami. Uniwersalny oddział konny zrobiono tak
  w Studiu i zagrano w grze (listopad 2026); nic innego zrobionego w ten sposób nie było jeszcze próbowane w grze.

## Pancerz

**Pancerz** na stronie jednostki wybiera jeden z poziomów pancerza gry (czołgi mają od 1 do 5, liczba na tarczy).
Jednostka z nim walczy, a jej karta i menu budowy go pokazują. Zmiana liczby w samej części pancerza sprawiała, że
jednostka walczyła z jedną wartością, a jej karta pokazywała inną, więc tej części nie da się już zmieniać bezpośrednio.
Widziane w grze.

## Badania: czego jest ulepszeniem

Strona jednostki ma pole **Ulepszenie i badania**: jednostka, której jest ulepszeniem (**Ulepszenie jednostki**), jej
własne ulepszenia oraz cena i czas jej badania. Wybierz inną jednostkę z tego samego menu budowy albo **Żadna: osobna
jednostka**, by można ją było kupić od początku. Czas badania można wpisać w sekundach lub minutach (wybór obok).

Gdy usuwasz jednostkę, z której badane są inne, **Ustawienia > Badania** decyduje, co się stanie: **Najpierw mnie
ostrzeż** (domyślnie), **Odmów** albo **Połącz je ponownie** z jej własnym rodzicem. Jednostka, która została badana
z jednostki, której już nie ma, mówi to tutaj i na pasku kontroli, a budowanie zatrzymuje się na niej, dopóki nie
wybierzesz innej.

Jednostka pokazana w swoim menu budowy musi być badana z jednostki, która też jest tam pokazana: najpierw ta, którą możesz
zbudować, po niej badanie. Jednostka pokazana w dacie bitwy, w której jednostka, z której jest badana, jest ukryta,
zatrzymuje grę, gdy to menu budowy się otwiera (widziane w grze), więc pasek kontroli ją wymienia, a budowanie się na niej
zatrzymuje. Pokaż znowu tę drugą jednostkę albo wybierz inną, z której ma być badana, albo żadną. **Nacje > Ukryj
wszystkie** robi to za ciebie: jednostka badana z ukrytej staje się dostępna do kupienia od początku.

## Jednostki z innych epok

366 jednostek od I wojny światowej po dziś, każda będąca darmowym modelem 3D innego autora, możesz dodać do moda jako
nowe jednostki, w ich prawdziwym rozmiarze i dostępne po zbadaniu: zobacz [[Jednostki z innych epok|Jednostki-z-innych-epok]].

## Broń i amunicja

Pole **Broń** na stronie jednostki wymienia jej broń (Broń 1 to działo główne). **Jak działają broń i amunicja**, pod
nim, też ma te kroki.

1. **Każda broń strzela jedną amunicją.** Lista obok niej wybiera którą: dowolną amunicję z gry, posortowaną według typu
   (AP, HE, przeciwlotnicza, karabiny maszynowe, bomby, rakiety...), albo kopię, którą zrobiłeś. Razem z nią przychodzą
   błysk wylotowy i dźwięk.
2. **Amunicja decyduje, co robi broń:** jej obrażenia, zasięg, szybkostrzelność i w co może trafić. **Otwórz amunicję**,
   by zobaczyć i zmienić jej liczby.
3. **Zmiana amunicji zmienia każdą jednostkę, która nią strzela** (strona amunicji je wymienia). Tylko dla jednej
   jednostki: na stronie amunicji kliknij **Kopiuj tę amunicję…**, zmień kopię, potem wybierz kopię na liście broni.
   Suwak **Zasięg** broni pyta o to samo: tylko ta jednostka czy każda jednostka z tą amunicją.
4. **Trafia** (pod bronią) wybiera cele naziemne, samoloty lub jedne i drugie. Pole **Rola** samolotu ustawia, jak
   atakuje (niżej).
5. **Dodawanie i usuwanie broni nie jest jeszcze możliwe:** broń jest powiązana z animacjami modelu, a tak daleko
   jeszcze nie doszliśmy.

**Jej nazwa w grze** (na stronie amunicji, Studio 0.9.8.8): jak gra nazywa amunicję, jej **Nazwa** (Medium cal.,
MG 42) i jej **Rodzaj** (AP shell). Wpisz nowe słowa i zapisz: każdy język je pokazuje, dopóki nie zmienisz któregoś
osobno przyciskiem **Zmień słowa…**; **Słowa z gry** usuwa twoje. Skopiowana amunicja nazywa się tak, jak ją nazwiesz.
Jeszcze nie sprawdzone w grze.

**Klasa broni** (na stronie amunicji, Studio 0.9.8.17): jaką część obrażeń amunicja zadaje każdemu rodzajowi celu.
**Nowa klasa broni…** otwiera po jednej liczbie dla każdego: budynki i umocnienia, samoloty, spadochroniarze w locie,
piechota, lekkie pojazdy (transportery), pancerz od 1 do 5 i ciężarówki budowlane. 1 to pełne obrażenia, 2 podwójne,
0,5 połowa, a 0 oznacza, że w ogóle nie może atakować tego celu. **Zapisz klasę** daje amunicji własną kopię tabeli
obrażeń gry, więc obrażenia żadnej innej amunicji się nie zmieniają, ale dostaje ją każda jednostka, która strzela tą
amunicją (tylko dla jednej jednostki najpierw użyj **Kopiuj tę amunicję…**). Przycisk nazywa się wtedy
**Zmień tę klasę broni…**; **Wróć do klasy z gry** usuwa kopię, a usunięcie skopiowanej amunicji zabiera ze sobą jej
klasę. Widziane w grze: drużyny strzelców, których amunicja dostała liczby przeciw czołgom, strzelały do czołgów
z karabinów i je uszkadzały. Samego przycisku nie kliknięto jeszcze w Studio.

**Prędkość pocisku:** prędkość pocisku amunicji i jego opór decydują, kiedy trafienie nastąpi: wolniejszy pocisk
trafia później, a do ruchomego celu celuje się z wyprzedzeniem o czas lotu (wiadomo to z tego, jak działa gra; jeszcze
nie sprawdzone w teście).

## Zmień rolę samolotu (Studio 0.9.8.5)

Strona samolotu ma pole **Rola**: **Myśliwiec**, **Myśliwiec-bombowiec**, **Bombowiec** lub **Zwiadowczy**. Razem z nią
zmienia się to, jak samolot lata i atakuje, jak używają go gracze komputerowi, i słowa w jego menu budowy.

- **Bombowiec:** bombowiec zrzuca bomby w prostym nalocie i tylko z komory bombowej. Najpierw wybierz bomby dla jednej z
  jego broni (Broń, niżej), potem zrób z niego Bombowiec: jego bomby trafiają do komory bombowej skopiowanej z bombowca
  z gry i tam możesz je zmieniać. To poprawka dla myśliwca-bombowca z bombami dywanowymi, który nic nie zrzucał.
  Widziane w grze.
- **Zwiadowczy:** samolot z działkami zachowuje zdolność ataku (pole mówi **Zwiadowczy, z zachowaniem ataków**)
  i dostaje widzenie zwiadowców. Widziane w grze ze Stuką i ME109.
- Samolot spadochroniarzy zachowuje swoją rolę. **Cofnij** obok pola przywraca rolę z gry, a jego bomby tam, gdzie były.

## Zrób z pojazdu zwiad (Studio 0.9.8.5)

Pole **Rola** pojazdu lądowego: **Rozpoznanie** daje mu widzenie samochodów zwiadowczych (dużo dalsze niż czołgu),
sposób, w jaki używają ich gracze komputerowi, ich słowa w menu budowy, i może on wjeżdżać do lasu. Pozostaje tak samo
wytrzymały i uzbrojony jak był. Widziane w grze z Panzerem IV.

## W co trafia broń (Studio 0.9.8.5)

Pod każdą bronią **Trafia** wybiera **Cele naziemne**, **Samoloty** lub **Cele naziemne i samoloty**. Samoloty: broń
strzela kopią swojej amunicji, która trafia samoloty (i nic nie robi celom naziemnym). Oba: zachowuje swoją amunicję
i dostaje obok drugą broń na samoloty, tak jak działa przeciwlotnicze z gry mają po jednej na każde. Czołg strzelający
do samolotów jest widziany w grze; działko samolotu ustawione na same cele naziemne nie zadaje jeszcze obrażeń.

## Przetestuj

**Testuj w grze** buduje mod i uruchamia R.U.S.E. Szukaj jednostki tam, gdzie jest budowana (w jej fabryce), w bitwie (menu główne: **BITWY**, potem mapa).

**Dalej:** [[Eksport i udostępnianie|Eksport-i-udostępnianie]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Edit-Units]]
