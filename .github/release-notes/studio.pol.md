**RUSE Studio, wersja zapoznawcza dla modderów.** Przeglądaj jednostki gry w dowolnym z jej dziesięciu języków,
zmieniaj je we własnym modzie i testuj go w grze. Twoja instalacja Steam nigdy nie jest zmieniana.

**0.9.7:** bardzo duże mody map budują się teraz w kilka minut. Wcześniej ich budowanie trwało bardzo długo i dlatego
ta aktualizacja była potrzebna. A **Eksportuj mod…** zabiera ze sobą to, co wyliczyło budowanie, więc pierwsze
budowanie takiego moda u gracza jest krótsze.

- **Najbardziej ekstremalny mod mapy, jaki mamy** (mapa „D-Day” z osuszonym morzem: 154 pociągnięcia wyrównania,
  135 pociągnięć malowania, 33 385 usuniętych budynków) budował się około czterech godzin. Teraz buduje się w **mniej
  niż 10 minut**, bez zachowywania czegokolwiek z wcześniejszego budowania, a pliki gry wychodzą takie same. Zajęło nam
  to około 15 godzin; gdzie się zacinało i dlaczego: [Jak tu doszliśmy](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here)
  (po angielsku). Wciąż pracujemy nad tym, by było szybciej.

| Wcześniej | Teraz |
|---|---|
| Mapa przekształcona na przestrzeni kilometrów mogła budować się godzinami, wyczerpać pamięć komputera albo zostać odrzucona jako zbyt duża dla ruchu na mapie. | Jej teren jest przekształcany w kilka sekund, koryta rzek naprawiane, a teren malowany na wszystkich rdzeniach komputera, zaś ruch wyliczany na dwóch kolejnych, gdy teren jest malowany. Każdy krok daje te same pliki co wcześniej. |
| Osuszone morze pozostawało zamknięte dla jednostek. | Szerokie suche dno dostaje strefy ruchu tak duże, na ile pozwala miejsce. **Jeszcze niesprawdzone w grze:** jednostki na otwartym morzu. |
| Przebudowa po małej zmianie wyliczała dużą mapę od nowa. | To, co zrobiono, zostaje: niezmienione malowanie zajmuje pół sekundy, niezmieniony ruch pochodzi z pamięci podręcznej budowania, a nowe pociągnięcie przemalowuje tylko kafelki, do których sięga. |
| Pierwsze budowanie dużego moda mapy u gracza wyliczało wszystko od nowa. | **Eksportuj mod…** zapisuje w modzie to, co budowanie wyliczyło dla ruchu na mapie (`maps/<map>/solved.bin`). Jest to powiązane z plikiem gry dla tej mapy i nie zawiera żadnych plików gry. Budowanie gracza to wykorzystuje, sprawdza każdą odpowiedź i daje te same pliki. Malowanie terenu i koryta rzek wciąż powstają na każdym komputerze. |
| Importuj model pojawiał się tylko na stronie nowej jednostki: trudno go było znaleźć. | Karta Jednostki zaczyna się od dwóch przycisków: **Zmień jednostkę** i **Nowa jednostka (import modelu)**. Wybierz jednostkę wyjściową, nazwij ją, Utwórz: jej strona otwiera się przy Importuj model. Strona jednostki z gry ma **Nowa jednostka z tej…**. |
| Flaga okrętu (76) mówiła, że jednostka z nią porusza się po wodzie. | Mówi, że jednostka w ogóle się nie porusza, jak budynek (jeszcze niesprawdzone w grze). |

Znane: **mapy morskie nie są jeszcze dopracowane.** Osuszone lub pomalowane morze buduje się i wczytuje, ale woda wciąż
jest widoczna.
