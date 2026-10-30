# Edycja scenariusza

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.9.8.4 i moda · **Czas:** kilka minut

**Scenariusz** to to, z czym mapa startuje: strefy do zdobycia, punkt startowy każdej strony oraz jednostki i budynki,
które już stoją na polu. Jedna mapa ma ich kilka: po jednym na każdy sposób, w jaki gra ją rozgrywa.

## Trzy sposoby, w jakie gra rozgrywa mapę

To są przyciski w menu głównym R.U.S.E.:

| Przycisk | Co to jest |
|---|---|
| **BITWY** | Swobodna gra przeciw komputerowi na jednej mapie, z graczami, których wybierzesz (w innych grach nazywa się to potyczką). |
| **OPERACJA** | Krótka misja z ustalonymi celami, na gotowym układzie. |
| **KAMPANIA** | Fabuła, rozdział po rozdziale. |

Studio nazywa każdy scenariusz od przycisku, który go uruchamia, a złoty wiersz pod menu scenariuszy mówi dokładnie gdzie:
na przykład **W grze: Bitwy › D-Day (6 graczy)**.

## Wybierz scenariusz

Na początku paska ekranu mapy wybierz **Scenariusz** (obok **Mapa**). Własne elementy mapy (teren, budynki, drzewa, drogi)
są wyblakłe i nie da się ich chwycić przypadkiem; przełącz z powrotem na **Mapa**, by je zmienić. Potem wybierz scenariusz
z menu u góry. Punkty startowe widać jako słupy w kolorze każdej strony, punkty pojawiania się jako białe romby, a strefy
jako zacienione obszary.

## Przesuń punkt startowy lub punkt pojawiania się

1. Po stronie **Scenariusz** kliknij **Przesuń**.
2. Kliknij słup lub romb, potem kliknij miejsce, gdzie ma stać.
3. Aby przywrócić go tam, gdzie miała go gra, kliknij go znowu i wybierz **Przywróć**.

## Dodaj jednostki: jedną lub cały szyk

1. Po stronie **Scenariusz** kliknij **Dodaj jednostkę**.
2. Wybierz rodzaj (Budynki, Lądowe, Piechota, Lotnictwo), potem typ, potem jednostkę z listy (pogrupowanej według nacji).
3. Wybierz **Dla kogo?** Dla Operacji lub rozdziału kampanii lista to własne obozy tego scenariusza, z jego misji:
   **Gracz** (ty: obóz 0 w kampanii) i obozy, którymi gra **Komputer**, każdy ze swoim krajem, plus **Neutralny**.
   Liczba w nawiasie to to, co zostaje zapisane. Mapa z **BITWY** przyjmuje tylko jednostki neutralne (gra uruchamia ją
   bez listy drużyn, więc jednostki gracza nigdy by się tam nie pojawiły).
4. **Ile:** 1, 2, 4, 6, 8 lub 10.
5. Dla więcej niż jednej wybierz **szyk**: linia, kolumna, klin, czworobok lub krąg. Jest zwrócony w górę ekranu: obróć
   widok, by go wycelować. **Odstęp** ustawia liczbę metrów między jednostkami.
6. Okręgi na mapie pokazują, gdzie stanie każda jednostka. Kliknij, by je postawić.

Jednostkę, którą dodałeś, można przesunąć jak każdy punkt pojawiania się albo usunąć przyciskiem **Usuń**.

## Więcej graczy na mapie (do 8)

Każdy gracz startuje w **punkcie startowym** swojej drużyny, jednym na gracza: w 3v3 drużyny 1 i 2 mają każda miejsca
od 1 do 3. 4v4 potrzebuje miejsca 4 w obu.

1. Wybierz scenariusz, który gra rozgrywa online (jego złoty wiersz mówi **Bitwy**), potem na pasku kliknij **Scenariusz**.
2. **Gracze** (po prawej) pokazuje liczbę graczy mapy, tę z gry oznaczoną *(z gry)*. Wybierz nową liczbę, najwyżej 8.
   Wiersz pod spodem wymienia każdy brakujący jeszcze punkt startowy, np. *drużyna 1, miejsce 4*.
3. Kliknij **Dodaj start kwatery głównej**, wybierz **drużynę**, potem kliknij wolny teren, gdzie ten gracz startuje,
   z dala od innych. Punkt zajmuje następne miejsce drużyny, a kamerę i intro bierze od członka drużyny.
4. Gdy wiersz mówi **Każdy gracz ma punkt startowy**, kliknij **Testuj w grze** i otwórz **BITWY**: mapa jest na liście
   z nową liczbą, np. *(8) Cotentin (4v4)*.

Punkt startowy, który dodałeś, przesuwa się przyciskiem **Przesuń** albo usuwa przyciskiem **Usuń**. Więcej niż 8: nie,
lobby gry ma 8 miejsc (sprawdzone 2026-10-02).

> [!NOTE]
> Nowość, jeszcze nie sprawdzona w grze: napisz nam w [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions),
> jak idzie gra na 8 graczy.

## Pusta mapa: postaw kwaterę główną każdego gracza

Mapa zaczęta jako **Pusty teren** lub **Pusty ocean** (**Duplikuj mapę** w zakładce Mapy) nie ma na sobie nic ze
skopiowanej mapy, także jej kwater głównych. **Kwatera główna każdego gracza** (po stronie Scenariusz) wymienia każdą
kwaterę główną, której mapa potrzebuje: kliknij **Umieść**, potem teren, gdzie ma stać. **Testuj w grze** czeka, aż każdy
gracz będzie miał kwaterę główną.

**Rozmiar mapy** (Studio 0.9.8.7) robi nową pustą mapę większą lub mniejszą, pas po pasie: naciśnij **+** przy boku, by
dodać wzdłuż niego pas terenu, albo **−**, by jeden zabrać, potem **Zastosuj ten rozmiar**. Jeszcze nie sprawdzone
w grze.

> [!WARNING]
> Obie puste mapy wciąż mają błędy: używasz ich na własną odpowiedzialność, i napisz nam, co znajdziesz.

## Sektory

**Sektory** (po stronie Scenariusz) zmienia sektory scenariusza, czyli strefy, na których zagrywa się karty podstępu.
Pusta mapa zaczyna bez nich: robisz je sam.
- **Kształty:** przeciągnij punkt w rogu, by przesunąć granicę (sektory, które ją dzielą, przesuwają się razem). Kliknij
  dwukrotnie granicę, by dodać punkt; kliknij punkt prawym przyciskiem, by go usunąć. **Nowy sektor:** przeciągnij
  prostokąt na terenie. **Bez sektora:** przeciągnij prostokąt tam, gdzie nie powinno być sektora. **Usuń sektor** oddaje
  cały jego teren sektorom dookoła.
- **Maluj:** wybierz sektor, potem przeciągaj po terenie, by go malować; „Bez sektora” wyjmuje teren z każdego sektora.
- **Zacznij bez sektorów** lub **Zacznij od sektorów mapy**; **Cofnij** cofa ostatnią zmianę.
- **Utwórz sektory** dzieli całą mapę na sektory mniej więcej tak szerokie, jak mówi **Sektory o boku około** (własne
  mapy gry mają sektory o szerokości od 1 do 3 km), z krętymi granicami; **Inny układ** dzieli je inaczej. Potem
  przeciągaj rogi albo maluj, by zmienić ich kształt.

Widziane w grze: malowane sektory na pustej mapie, nowy sektor narysowany na D-Day i podświetlony samodzielnie przez kartę
podstępu, teren bez sektora (luka na stole mapy, której nie podświetla żadna karta podstępu). Cienkie linie, które Studio
wycina, by sektor pozostał jednym kawałkiem, nie były jeszcze testowane w grze.

## Składy zaopatrzenia na tej mapie

Wybierz skład zaopatrzenia, by dać mu więcej ciężarówek (więcej ciężarówek, więcej pieniędzy w nim), albo użyj **Każdy
skład tutaj**: pomnóż ciężarówki każdego składu (**razy ich ciężarówki**) albo daj wszystkim tę samą liczbę
(**ciężarówek każdy**), potem **Zastosuj**. **Wróć do tych z gry** to cofa. Aby zmienić wszystkie mapy naraz, użyj
**Składy na mapach** w **Ustawienia SI i graczy** ([[Ekonomia, SI i nie tylko|Ekonomia-SI-i-nie-tylko]]). Składy z więcej niż
1000 ciężarówek wymagają Launchera 0.4.8.4 lub nowszego.

## Własna misja

Nowa Operacja lub rozdział kampanii może grać własną misję, z celami, zdarzeniami i ruchami kamery:
[[Tworzenie misji|Tworzenie-misji]].

## Zobacz swoje jednostki w grze

1. Kliknij **Testuj w grze** (u góry Studio). Studio buduje twój mod w zmodowanej kopii gry
   (`RUSE-Instances\Modded game` na dysku twojej gry albo w folderze wybranym w Ustawieniach: jednym na cały PC, także dla Launchera) i uruchamia z niej R.U.S.E. Komunikat na dole
   mówi, co otworzyć, na przykład **BITWY > D-Day**.
2. W menu głównym gry kliknij ten przycisk (**BITWY** dla bitwy), potem wybierz mapę (**D-Day**).
3. Ustaw grę jak zwykle i zacznij. Twoje jednostki pojawią się tam, gdzie je postawiłeś.

> [!NOTE]
> Uruchomienie R.U.S.E. ze Steama uruchamia grę bez twojego moda. Użyj **Testuj w grze** (albo **Graj** w launcherze).

> [!NOTE]
> To, który punkt startowy należy do którego gracza z lobby w bitwie, jest jeszcze testowane. Napisz nam, co znajdziesz,
> w [Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions).

**Dalej:** [[Eksport i udostępnianie|Eksport-i-udostępnianie]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Edit-a-Scenario]]
