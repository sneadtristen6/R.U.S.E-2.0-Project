# Modele i kości

> **Potrzebujesz:** RUSE Studio 0.9.8.20 lub nowszego, moda z nową jednostką i Blendera (za darmo), żeby zmieniać kości ·
> **Czas:** 10 minut czytania

Żołnierze, konie i każde stworzenie ruszają się w R.U.S.E., bo ich model 3D ma **kości**. Ta strona mówi, czym są kości,
jak gra ich używa i co znaczy każde pole o kościach na stronie jednostki, i co z nim zrobić. Czołg obraca wieżę i koła
bez animacji, więc ta strona dotyczy głównie żołnierzy, koni i stworzeń.

## Czym są kości

- **Model** to powłoka z punktów, z obrazkami namalowanymi na niej.
- W środku, jak szkielet, są **kości**: ramię, przedramię, dłoń, głowa, każda noga konia. Każda kość wisi na innej
  (dłoń na przedramieniu, przedramię na ramieniu), aż do pierwszej kości.
- Każdy punkt powłoki idzie za kością albo za kilkoma: punkty rękawa idą za ręką. To, jak mocno punkt idzie za każdą
  kością, to jego **waga**.
- **Animacja** porusza kośćmi, klatka po klatce, a powłoka idzie za nimi. Tak żołnierz idzie, celuje i pada.
- W Blenderze kości modelu to jeden obiekt, zwany **armature**.

## Jak gra ich używa

- Gra porusza kośćmi modelu **według ich miejsca na liście kości**, nie według nazw. Animacja zrobiona dla jednego
  modelu pasuje więc tylko do modelu z tymi samymi kośćmi, w tej samej kolejności.
- Niektóre kości mają zadanie: strzał wychodzi z kości u wylotu broni, górna część ciała obraca się do celu przy kości
  kręgosłupa, broń jest pokazywana i chowana na kości, wieża albo koło obraca się na kości. Strona jednostki wymienia
  każdą, której brakuje twojemu modelowi (zobacz **Czy zadziała w grze?** niżej).
- Żołnierz odtwarza **dwie animacje naraz**: jedną na górnej połowie ciała (celowanie, strzelanie) i jedną na dolnej
  (chodzenie, bieganie). Koń z jeźdźcem też: zobacz **Dwie połowy** niżej.
- Nie widziano, by gra animowała model z więcej niż 64 kośćmi.

## Dwa rodzaje modeli

| | Na kościach żołnierza z gry | Z własnymi kośćmi |
|---|---|---|
| **Co to jest** | Żołnierz zmieniony w Blenderze albo twój model założony na kości żołnierza | Koń, koń z jeźdźcem, dowolne stworzenie, zrobione w Blenderze na twoich kościach |
| **Jak go zrobić** | **Otwórz w Blenderze** na karcie oddziału: każdy żołnierz otwiera się ze swoimi kośćmi (zobacz [[Otwórz w Blenderze|Otwórz-w-Blenderze]]) | W Blenderze, potem **Importuj model…** w wierszu żołnierza, pod **Każdy żołnierz** (zobacz [[Importowanie modelu|Importowanie-modelu]]) |
| **Jego animacje** | Te z gry, jak u żołnierza | Własne, z jego pliku |
| **Dwie połowy** | Te z gry: nie ma czego wybierać | Wybierasz je ty (Studio proponuje kość) |
| **Rozmiar i miejsce** | Jak zrobiłeś w Blenderze, na jego kościach | Jak w jego pliku |

Strona mówi, który to rodzaj. Przy modelu na kościach żołnierza z gry: „Twój model jest na kościach żołnierza z gry,
więc zachowuje dwie połowy z gry: nie ma czego wybierać.” Przy modelu z własnymi kośćmi: „Ma własne kości:” i ile.
**Uniwersalny oddział konny** (karta **Jednostki**, **II wojna światowa+**) to oddział z własnymi kośćmi: zobacz
[[Jednostki z innych epok|Jednostki-z-innych-epok]].

## Gdzie strona je pokazuje

Na stronie nowej jednostki wszystko o kościach jest w **Wygląd i ruch**:

| Pole | Gdzie | Co ci mówi |
|---|---|---|
| **Jego kości i animacje** | Wiersz **Dźwięki i animacje**, **Więcej** | Ile kości ma model, i każda animacja z jej długością i liczbą czynności jednostki, które jej używają (model z własnymi kośćmi) |
| **Dwie połowy** | Wiersz **Dźwięki i animacje**, **Więcej** | Gdzie model dzieli się na górną i dolną połowę |
| **Jej animacje** | Wiersz **Dźwięki i animacje**, **Więcej** | Której animacji jednostka używa do każdej czynności: zobacz [[Animacje jednostek|Animacje-jednostek]] |
| **Czy zadziała w grze?** | Wiersz **Model**, **Więcej**; na stronie oddziału **Więcej opcji** pod żołnierzami, potem **Model każdego żołnierza** | Co w modelu mogłoby zatrzymać grę albo wyglądać źle, i jak to naprawić |
| Punkty bez kości | W tym samym miejscu co **Czy zadziała w grze?** | Ile punktów modelu nie idzie za żadną kością |

## Dwie połowy

Gra odtwarza na żołnierzu dwie animacje naraz: jedną na jego **górnej połowie** (celowanie, strzelanie) i jedną na
**dolnej połowie** (chodzenie, bieganie). Jeździec celuje i strzela, gdy jego koń biegnie: jeździec to górna połowa, koń
dolna.

- Model na kościach żołnierza z gry zachowuje połowy z gry: strona mówi „nie ma czego wybierać”.
- Model z własnymi kośćmi dzieli się przy **jednej kości**: ta kość i wszystkie kości pod nią tworzą górną połowę,
  wszystkie inne dolną.

Jak ją wybrać:

1. Na stronie jednostki, w **Wygląd i ruch**, kliknij **Więcej** w wierszu **Dźwięki i animacje**.
2. Pod **Dwie połowy** lista **Górna połowa zaczyna się od** pokazuje najpierw propozycję Studio, oznaczoną
   „(proponowana)”. Studio proponuje pierwszą kość jeźdźca na koniu z jeźdźcem (**bip01** w Uniwersalnym oddziale
   konnym), inaczej pierwszą kość o nazwie spine (jak u żołnierza), inaczej kość, przy której szkielet pierwszy raz się
   rozgałęzia.
3. Dla większości modeli propozycja jest dobra: zostaw ją. Aby ją zmienić, wybierz inną kość z listy. Zapisuje się od
   razu i jest widoczna w grze po następnym budowaniu (**Testuj w grze**).
4. Pod listą strona liczy kości każdej połowy, a **Która kość gdzie** wymienia każdą kość modelu, oznaczoną górna
   połowa albo dolna połowa.
5. Aby wrócić do propozycji, wybierz znowu pierwszy wiersz listy.

Innego podziału niż proponowany jeszcze nie sprawdzono w grze.

## Wagi: za którą kością idzie każdy punkt

Gdy zakładasz własny model (albo hełm, plecak, broń) na kości żołnierza, Blender musi wiedzieć, za którą kością idzie
każdy z jego punktów. To są kroki samego Blendera.

**Twój model na żołnierzu, każdy punkt idzie za najbliższymi kośćmi:**

1. Na karcie oddziału kliknij **Otwórz w Blenderze**: Blender otwiera się z żołnierzami, każdy na swoich kościach.
2. W Blenderze wczytaj swój model przez **File > Import** i umieść go na żołnierzu.
3. Kliknij swój model, potem **Shift+klik** na kości żołnierza: kości na końcu.
4. Naciśnij **Ctrl+P** i wybierz **With Automatic Weights**. Blender policzy wagi za ciebie.
5. Usuń to, czego nie zostawiasz (kształt żołnierza z gry, jeśli twój model zajmuje jego miejsce), ale zostaw jego
   kości.
6. Kliknij **Wyślij do R.U.S.E. Studio** u góry widoku 3D Blendera, potem **Przenieś moje zmiany** w Studio.

**Sztywna część, która idzie za jedną kością (hełm na głowie):**

1. W Blenderze kliknij hełm, potem **Shift+klik** na kości żołnierza.
2. Naciśnij **Ctrl+Tab**, żeby przejść do Pose Mode, i kliknij kość głowy.
3. Naciśnij **Ctrl+P** i wybierz **Bone**. Hełm rusza się teraz z głową i dostaje go tylko ten żołnierz, gdy przeniesiesz
   swoje zmiany.

**Punkty bez kości.** Automatyczne wagi Blendera czasem pomijają kilka punktów. Strona mówi wtedy „{n} punkt(y) twojego
modelu nie mają kości, więc ruszają się tylko z biodrami żołnierza.” Jak to naprawić:

1. Znowu **Otwórz w Blenderze**.
2. Kliknij swój model i przełącz tryb Blendera (u góry po lewej w widoku 3D) z **Object Mode** na **Weight Paint**.
3. We właściwościach modelu (zielony trójkąt) **Vertex Groups** ma jedną grupę na kość: wybierz kość, za którą mają iść
   te punkty.
4. Pomaluj te punkty.
5. **Wyślij do R.U.S.E. Studio**, potem **Przenieś moje zmiany**.

## Czy zadziała w grze?

Studio sprawdza model na kościach względem animacji, które odtwarza, i względem części i strzałów jednostki, którą
kopiuje. Budowanie moda sprawdza to ponownie, ze wszystkimi twoimi zmianami. Problem nigdy cię nie blokuje: mówi, co się
stanie i jak to naprawić.

**Gdzie:** na stronie nowej jednostki, **Wygląd i ruch**, wiersz **Model**, **Więcej**. Na stronie oddziału: **Więcej
opcji** pod żołnierzami, potem **Model każdego żołnierza**.

Gdy wszystko jest dobrze, mówi: „Nie znaleziono niczego, co zatrzymałoby grę: każda odtwarzana animacja ma jego kości, a
każda kość potrzebna częściom i strzałom jest na miejscu.” (z liczbą kości).

### Co znaczy każda odpowiedź

Każdy problem mówi trzy rzeczy: co nie pasuje, co gra z tym zrobi i jak to naprawić. Środkowy wiersz to jeden z tych:

| Strona mówi | Co to znaczy | Co zrobić |
|---|---|---|
| To może zatrzymać grę: zdarzyło się to w teście. | Gra zatrzymała się tak w jednym z naszych testów. | Napraw przed testem. |
| To może zatrzymać grę (jeszcze nie sprawdzone w grze). | Oczekuje się, że gra się zatrzyma. | Napraw przed testem. |
| Gra to odtworzy, ale będzie wyglądać źle (jeszcze nie sprawdzone w grze). | Ruszyłyby się niewłaściwe kości. | Napraw albo przetestuj i popatrz. |
| Jednostka nadal walczy, ale jej strzałów nie będzie widać: zdarzyło się to w teście. | Zadaje obrażenia, ale nie widać żadnego strzału. | Dodaj kość, którą wymienia strona. |
| Jeszcze nie sprawdzone w grze: gra może go nie animować. | Więcej kości, niż widziano, by gra animowała. | Połącz albo usuń kości. |
| Nadal działa, ale może nie tak, jak chcesz. | Uwaga o jego dwóch połowach. | Sprawdź **Dwie połowy**. |

### Każdy problem i jego naprawa

**Animacje, które nie pasują do kości modelu.** Strona mówi, ile animacji, dla ilu czynności i dlaczego nie pasują:
„Poruszają {a} kośćmi, a twój model ma ich {b}.” (albo „tylko {b}”), albo tyle kości, ale „inaczej nazwanych”, albo „w
innej kolejności”. Te animacje zrobiono dla innych kości.

- Jeśli jednostka odtwarza na twoim modelu animacje z gry: daj tym czynnościom własne animacje twojego modelu.
  **Importuj model…** wnosi każdą animację z pliku twojego modelu, a w **Jej animacje** wybierasz, której używa każda
  czynność ([[Animacje jednostek|Animacje-jednostek]]).
- Jeśli to własne animacje twojego modelu, zrobione dla innego modelu: zrób je od nowa w Blenderze na kościach tego
  modelu, potem zaimportuj model ponownie.

**Kość, której jednostka potrzebuje.** Na przykład: „Strzelcy: strzały wychodzą z kości o nazwie Fx_Tir_01, a twój
model jej nie ma.” (albo: górna część ciała obraca się tam do celu, broń jest tam pokazywana i chowana, część jest tam
trzymana, wieża albo koło się tam obraca, ciało tam spoczywa, holowane działo tam się zaczepia). Jak dodać kość w
Blenderze:

1. Otwórz model w Blenderze: **Otwórz w Blenderze** z zaznaczonym **Jego kości** (zobacz
   [[Otwórz w Blenderze|Otwórz-w-Blenderze]]) albo twój własny plik Blendera.
2. Kliknij kości (armature) i naciśnij **Tab**, żeby przejść do Edit Mode.
3. Naciśnij **Shift+A**: nowa kość pojawia się tam, gdzie jest kursor 3D Blendera.
4. Naciśnij **F2** i wpisz dokładnie nazwę, którą podaje strona (na przykład `Fx_Tir_01`). Jeśli twój model ma tę kość
   pod inną nazwą, zmień raczej nazwę tamtej.
5. We właściwościach kości (ikona kości), w **Relations**, ustaw jako **Parent** kość, z którą rusza się ta część: dla
   strzału kość, z którą rusza się broń.
6. Naciśnij **G** i przesuń nową kość tam, gdzie ta część powinna być: dla strzału na koniec lufy broni.
7. Naciśnij znowu **Tab**, kliknij **Wyślij do R.U.S.E. Studio**, potem **Przenieś moje zmiany** (albo wyeksportuj własny
   plik i kliknij **Importuj inny…**). **Czy zadziała w grze?** sprawdza model ponownie.

**Za dużo kości.** „Twój model ma {n} kości. Nie widziano, by gra animowała model z więcej niż 64 kośćmi.” W Blenderze
połącz albo usuń kości, aż będzie ich 64 lub mniej, potem przenieś model z powrotem.

**Podział.** „Podział przy {bone}, pierwszej kości modelu, umieszcza wszystkie kości w górnej połowie, więc animacje
dolnej połowy (chodzenie, bieganie) niczego nie poruszają.”: wybierz kość niżej w **Dwie połowy**, tam, gdzie zaczyna
się górna część ciała. „Kości wybranej do podziału, {bone}, nie ma już w twoim modelu, więc dzieli się przy {used}.”:
wybierz kość ponownie.

**Drugi model oddziału na innych kościach.** „Jego model ma własne kości, inne niż model twoich strzelców, więc odgrywa
to, co w kopiowanej jednostce, zrobione na kościach żołnierza z gry: to może zatrzymać grę.” Model żołnierza z ciężką
bronią musi być na tych samych kościach co model strzelców, żeby używać ich animacji: zrób jego model z modelu strzelców
w Blenderze, potem zaimportuj go w jego wierszu. Usunięcie modelu strzelców usuwa też jego model.

## Jak zrobić model z własnymi kośćmi w Blenderze

1. **Jego kości:** twój model na armature z twoimi kośćmi, nazwanymi jak chcesz, i jego wagi
   (**Ctrl+P > With Automatic Weights**, wyżej).
2. **Jego animacje:** jedna action na animację (w Blenderze **Dope Sheet > Action Editor**). Nazwij każdą według tego,
   co pokazuje: co najmniej **stand** (albo **idle**), **walk** i **run** (albo **gallop**); znane są też **fire**,
   **aim**, **reload**, **hit**, **death**, **crouch**, **look**, **flee** i **grenade**. Nazwa w rodzaju **t_fire** (albo
   **hr_t_fire**) gra tylko na górnej połowie, a **b_run** (albo **hr_b_run**) tylko na dolnej: jeźdźca i jego konia.
3. **Wyeksportuj go:** **File > Export > glTF 2.0**, format **glTF Binary (.glb)**, z zaznaczonym **Animation**.
4. **Zaimportuj go** na nowy oddział: zobacz [[Importowanie modelu|Importowanie-modelu]].
5. **Sprawdź jego stronę:** **Jego kości i animacje** (każda animacja dotarła, i ile czynności jej używa), **Dwie
   połowy**, **Jej animacje**, **Czy zadziała w grze?**
6. **Testuj w grze.**

Zmieniłeś go potem w Blenderze? Zaimportuj go ponownie: każda czynność zachowuje swoją animację, dopóki animacja o tej
nazwie jest jeszcze w pliku.

## Co sprawdzono w grze

- Uniwersalny oddział konny, zrobiony w ten sposób (strzelcy i żołnierz z bazooką na koniach, model z własnymi
  kośćmi): strzelają, podróżują sami na długich trasach, a każdy koń pada razem z jeźdźcem (listopad 2026).
- Żołnierz oddziału zmieniony w Blenderze na kościach żołnierza z gry, z punktami zważonymi tam (listopad 2026).
- Jeszcze nie sprawdzone w grze: inny podział niż proponowany, i każdy problem, który strona oznacza „jeszcze nie
  sprawdzone w grze”.

Nadal utknąłeś? Zapytaj na [Discordzie](https://discord.gg/h54t5baNsC) albo zajrzyj do
[[Gdy coś pójdzie nie tak|Gdy-coś-pójdzie-nie-tak]].

**Dalej:** [[Animacje jednostek|Animacje-jednostek]] · [[Otwórz w Blenderze|Otwórz-w-Blenderze]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Models-and-Bones]]
