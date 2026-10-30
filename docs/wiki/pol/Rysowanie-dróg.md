# Rysowanie dróg

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio 0.7.4 i moda · **Sprawdzone w grze:** trasy zaopatrzenia idą nową
> drogą, a ona jest namalowana na terenie

## Zobacz drogi mapy

Zaznacz **Drogi** u góry mapy: własne drogi mapy pokazują się na złoto, na terenie, gdy go kształtujesz.

## Narysuj nową drogę

1. Na pasku na dole kliknij **Drogi i mosty** (otwiera się jego zakładka **Drogi**). Drogi mapy widać na złoto,
   twoje nowe na niebiesko.
2. Wybierz narzędzie:

| Narzędzie | Jak |
|---|---|
| **Prosta** | Kliknij, gdzie droga się zaczyna, potem gdzie się kończy. |
| **Łuk** | Kliknij początek, potem punkt, ku któremu wygina się zakręt, potem koniec. |
| **Dowolna** | Klikaj wzdłuż trasy; kliknij dwukrotnie, naciśnij **Enter** albo kliknij **Zakończ**, by ją skończyć. |

3. Za kursorem idzie niebieska wstęga, a obok niej **długość drogi** (Dowolna pokazuje też odcinek od ostatniego
   kliknięcia). Koniec blisko dowolnej drogi **przyczepia się do niej** (pierścień pokazuje gdzie), więc nowa droga
   się z nią łączy: ciężarówki zaopatrzenia mogą jechać z jednej na drugą. Narzędzia Drogi pokazują, ile nowych dróg
   ma mapa, i ich łączną długość.
4. **Esc** porzuca rysowaną drogę; **Cofnij** (albo **Ctrl+Z**) zabiera ostatnią, **Ponów** (albo **Ctrl+Y**)
   rysuje ją znowu.

Nowe drogi zapisują się w twoim modzie od razu (`maps/<map>/roads.toml`).

## Co nowa droga robi w grze

- **Trasy zaopatrzenia jej używają** (sprawdzone: trasa składu zaopatrzenia poszła nowym skrótem przez otwarte pola).
- **Jest namalowana na terenie** we własnym kolorze dróg mapy, więc gracze ją widzą (sprawdzone w grze). Wygląda jak
  własne drogi mapy, z wysoka i tuż przy ziemi.
- **Piechota idzie nią**, by szybciej dokądś dotrzeć (sprawdzone w grze, Studio 0.8.0).
- **Nad wodą dostaje most**: własnego rodzaju mapy (ma go 24 z 32 map), jeden element rozciągnięty od brzegu do
  brzegu, tak jak własne mosty gry, a jednostki mogą po nim przejechać. Droga po jednym z własnych mostów mapy dostaje
  w jego miejsce nowy most. Na mapie bez rodzaju mostu budowanie to mówi, a woda pozostaje zamknięta. (Sprawdzone
  w grze: czołgi, piechota i ciężarówki zaopatrzenia przejeżdżają po jezdni mostu.)
- Rośliny i obiekty na jej drodze są usuwane; **Zachowaj drzewa na nowych drogach** zachowuje drzewa i krzewy (droga
  pod drzewami).

## Usuń własne drogi i mosty mapy

W narzędziach **Drogi**:

- **Usuń drogi z mapy:** własne drogi mapy znikają: sieć, którą jeżdżą ciężarówki zaopatrzenia (zamiast tego jadą
  na przełaj), i drogi namalowane na terenie. Twoje nowe drogi zostają. Widziane w grze: drogi znikają; ciężarówki
  zaopatrzenia jadące na przełaj nie są jeszcze sprawdzone.
- **Usuń mosty z mapy:** własne mosty mapy znikają razem z pomostami, po których stały jednostki. Jednostki nadal
  przechodzą tam, gdzie stały, po terenie pod nimi, chyba że zaznaczysz też następne pole. Twoje nowe mosty zostają.
- **Zamknij przejścia po dawnych mostach** (gdy mosty są usunięte; od DomesticNukes): teren, gdzie każdy dawny most
  stał nad wodą, jest zamknięty dla jednostek, a połączenia drogowe przez niego są przecięte: nic tam nie przechodzi,
  także ciężarówki zaopatrzenia, a reszta sieci dróg zostaje. Twoja nowa droga, która przecina wodę w tym samym
  miejscu, dostaje tam własny most. Jeśli zamknięcie ich odcięłoby kawałek terenu od reszty, Studio mówi o tym przed
  budowaniem.

Jeszcze nie sprawdzone w grze: usuwanie mostów i zamykanie przejść po nich.

## Postaw własny most

W zakładce **Mosty**: wybierz rodzaj, ustaw jego długość i obrót, potem kliknij teren, gdzie ma być środek mostu.
Oba końce powinny opierać się na suchym brzegu. **Cofnij** i **Ponów** działają tu też.

**Zobacz to:** **Testuj w grze**, potem w menu głównym gry **BITWY** i ta mapa. Postaw skład zaopatrzenia blisko
swojej drogi i obserwuj jego trasę.

**Dalej:** [[Rozmieszczanie budynków i drzew|Rozmieszczanie-budynków-i-drzew]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Draw-Roads]]
