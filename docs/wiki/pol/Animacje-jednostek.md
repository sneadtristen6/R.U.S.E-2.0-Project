# Animacje jednostek

> **Potrzebujesz:** RUSE Studio 0.9.8.20 lub nowszego i moda; Blendera (za darmo), żeby zmieniać animacje nowej
> jednostki w Blenderze · **Czas:** 10 minut czytania

To, jak rusza się jednostka (stoi, idzie, biegnie, celuje, strzela, ginie), to jej **animacje**. Ta strona mówi, do
czego służą animacje z gry, której jednostka używa do każdej czynności, każdy sposób, by jedną zmienić (dla jednej
jednostki, dla wszystkich, dla jednostek, które wybierzesz, albo w Blenderze), i jak wrócić do tej z gry.

## Czym jest animacja

- Animacja porusza kośćmi modelu w czasie: jeden krok biegu, karabin podniesiony do ramienia, upadek (zobacz
  [[Modele i kości|Modele-i-kości]]).
- Każda rzecz, którą jednostka robi w grze (**czynność**: stoi w miejscu, idzie, biegnie, strzela...), odtwarza
  animację. Żołnierz odtwarza dwie naraz, po jednej na każdą połowę ciała.
- Wiele jednostek dzieli animacje z gry: każdy amerykański strzelec biega tak samo. Zmiana animacji to więc, jeśli nie
  wybierzesz inaczej, zmiana dla wszystkich jednostek, które jej używają.
- Czołgi obracają wieżę i koła bez animacji: tu nie ma dla nich nic do zmiany.

## Animacje z gry i do czego służy każda

**RUSE Decoy** (jego karta u góry Studio) wymienia każdą animację z gry po lewej, pod **Animacje**, według rodzaju:

| Rodzaj | Co zawiera |
|---|---|
| **Piechota** | Strzelcy, bazooki, spadochroniarze i kierowcy: stanie, marsz, bieg, celowanie, strzał, przeładowanie, ucieczka, trafienie i śmierć (górna i dolna część ciała mają własne) |
| **Obsługa dział** | Ludzie przy dziale: w spoczynku, przy przetaczaniu, przygotowaniu, strzale i przeładowaniu |
| **Pojazdy i działa** | Działa rozkładane i składane, w spoczynku i przy strzale, oraz inne ruchome części |
| **Postacie w dowództwie** | Oficerowie przy stole dowództwa w scenach misji (nie używa ich żadna jednostka) |
| **Zwierzęta i otoczenie** | Krowy, konie, kozy, kury, mewy i wiatraki na mapach |

Każda mówi, jak nazywa ją gra i ile jednostek jej używa. Na stronie jednostki czynności nazywają się od tego, co robi
jednostka, pogrupowane tak:

| Grupa | Jej czynności (niektóre) |
|---|---|
| W miejscu | Stoi w miejscu, Kuca, Rozgląda się |
| W ruchu | Idzie, Idzie do tyłu, Biegnie, Biegnie w prawo, Biegnie do tyłu, Ucieka |
| Celowanie i strzelanie | Celuje na stojąco, Celuje idąc, Strzela, Rzuca granat, Przeładowuje |
| Ciężka broń | Celuje z ciężkiej broni, Strzela z ciężkiej broni, Podnosi ciężką broń, Opuszcza ciężką broń |
| Trafienia | Zostaje trafiony, Zostaje trafiony od tyłu, Zostaje trafiony wybuchem |
| Śmierć | Ginie od kuli, Ginie w wybuchu, Leży poległy |
| Skok ze spadochronem | Skacze, Spada, Opada na spadochronie, Ląduje |
| Czynności załogi | Czeka, Idzie naprzód z działem, Idzie do działa, Rozstawia działo, Strzela (członek załogi), Ładuje działo |

## Jej animacje: której używa każda czynność

Jednostka z własnymi animacjami (model z własnymi kośćmi: koń, koń z jeźdźcem, dowolne stworzenie) ma na swojej
stronie tabelę: **Wygląd i ruch**, wiersz **Dźwięki i animacje**, **Więcej**, potem **Jej animacje**.

- **Stoi w miejscu**, **Idzie** i **Biegnie** są pierwsze: to minimum, którego model potrzebuje. Jeśli któraś nie ma
  nic własnego, strona to mówi, i co odtwarza zamiast tego.
- Każda czynność ma listę animacji modelu. Wybierz jedną albo zostaw pierwszy wiersz, **Najbliższa**: wtedy odtwarza
  najbliższą, jaką ma model, a wiersz mówi którą. Najbliższa znaczy, w tej kolejności: animacja nazwana tak jak ta
  czynność (stand albo idle, walk, run albo gallop, fire, death...), a jeśli nie ma, to co odtwarza najbliższa czynność
  (chodzenie odtwarza bieg, strzał celowanie albo stanie). Gra odtwarza to, co mówi strona: budowanie stosuje tę samą
  regułę.
- **Wszystkie inne czynności** wymienia resztę, według grup.
- **Na długich trasach** to jej ostatni wiersz. Na długiej trasie drogą gra wsadza oddział do jego ciężarówki.
  Jednostka z własnymi animacjami może zamiast tego jechać sama, odtwarzając jedną z nich w pętli (swój bieg, jeśli
  zostawisz pierwszy wiersz), z prędkością swojej ciężarówki. Wybierz **W swojej ciężarówce**, żeby zostawić ciężarówkę.

Jednostka skopiowana z jednostki z własnymi animacjami używa tych samych.

## Zmiana animacji w RUSE Decoy

1. Na stronie jednostki, w **Wygląd i ruch**, kliknij **Zmień w RUSE Decoy** w wierszu **Dźwięki i animacje**. RUSE
   Decoy otwiera się na tej jednostce: jej dźwięki, potem **Jej animacje** z każdą animacją, której używa. (Albo otwórz
   kartę **RUSE Decoy** i wybierz rodzaj pod **Animacje**.)
2. Kliknij **Obejrzyj i zmień…** przy animacji. Odtwarza się w 3D na jednostce, która jej używa: przeciągnij, żeby ją
   obrócić, kółko przybliża. Widok 3D raz potrzebuje internetu.
3. Otwarta ze strony jednostki, pierwsza linia pyta **Zmień dla**:
   - **Tylko ta jednostka**: ta jednostka odtwarza własną kopię animacji, z twoimi zmianami; wszystkie inne odtwarzają ją
     jak wcześniej. To wybór na start, chyba że animacja jest już zmieniona dla wszystkich jednostek.
   - **Wszystkie jednostki, które jej używają**: zmiana trafia do samej animacji, dla wszystkich jednostek, które jej
     używają (liczba mówi ile).
   - **Twoja kopia** i jej nazwa: widać ją, gdy ta jednostka używa twojej kopii (niżej); wtedy to ona jest wyborem na
     start.
4. Zmień ją:
   - **Tempo**: 100% to tempo gry, 200% dwa razy szybciej, 50% dwa razy wolniej. Zapisuje się, gdy puścisz.
   - **Użyj zamiast**: inna animacja tego samego ciała na jej miejscu (strzelcy mogliby biegać tak, jak uciekają).
   - **Kość**, z **Rozmiar**, **Obrót wokół** i **Obrót**: część ciała większa albo obrócona przez całą animację.
   - **Motion capture**: ruch prawdziwego człowieka na jej miejscu (zobacz [[Muzyka i dźwięki|Muzyka-i-dźwięki]]).
5. Kliknij **Gotowe**. Każda zmiana zapisuje się w twoim modzie od razu i trafia do gry, gdy testujesz albo
   eksportujesz.

## Kopia animacji, dla jednostek, które wybierzesz

**Kopiuj tę animację…** robi kopię, której używają tylko jednostki i żołnierze, których zaznaczysz: własny bieg dla
trzech twoich oddziałów, na przykład, i tylko dla żołnierza z bazooką czwartego.

1. W oknie animacji kliknij **Kopiuj tę animację…**, nadaj kopii nazwę (widzisz ją tylko ty) i kliknij **Zrób kopię**.
   Zaczyna się taka, jaka jest teraz animacja, i otwiera się w tym samym oknie.
2. Zmień ją jak wyżej.
3. W **Kto jej używa** zaznacz jednostki, które używają kopii: najpierw **Twoje jednostki**, potem **Jednostki z gry**.
   Pod jednostką, w której używa jej kilku żołnierzy albo kilka części, zaznacz tylko niektóre. **Znajdź jednostkę**
   szuka po nazwie albo kraju.
4. Nic nie używa kopii, dopóki nie zaznaczysz jednostki: wiersz pod jej nazwą mówi do tego czasu „żadna jednostka
   jeszcze jej nie używa”.

Każda kopia jest po lewej w RUSE Decoy pod **Twoje kopie**: otwórz ją tam albo **Usuń kopię**. Własna kopia jednostki
(**Tylko ta jednostka**) albo animacja zmieniona w Blenderze ma dla tej jednostki pierwszeństwo przed kopią: lista mówi
to obok.

## Zmiana animacji nowej jednostki w Blenderze

Dla nowej jednostki zrobionej w twoim modzie (jednostka z gry potrzebuje najpierw nowej jednostki zrobionej z niej):

1. Na stronie jednostki kliknij **Zmień w RUSE Decoy**. Nad jej animacjami kliknij **Zmień jego animacje w Blenderze**.
   Blender otwiera się z jednostką i każdą animacją, której używa, każda nazwana od tego, co w niej robi, a po niej
   nazwa, jaką nadaje jej gra.
2. Na dole Blendera Action Editor je wymienia: wybierz jedną. **Spacja** ją odtwarza.
3. Kliknij kość, naciśnij **Ctrl+Tab**, żeby przejść do Pose Mode, **R**, żeby ją obrócić (**G** ją przesuwa), potem
   **I**, żeby zachować pozę w tej klatce. Zrób to w każdej klatce, którą zmieniasz: Blender sam przechodzi od jednej
   zachowanej pozy do następnej.
4. Kliknij **Wyślij do R.U.S.E. Studio** u góry widoku 3D Blendera: wychodzi każda animacja, zmieniona czy nie.
5. W RUSE Decoy kliknij **Przenieś moje zmiany**. Mówi, które wróciły zmienione: są teraz własne tej jednostki. Wszystkie
   inne jednostki i każda animacja, której nie dotknąłeś, zostają jak wcześniej.

Tylko ustawiaj kości w pozach: nie zmieniaj ich nazw, nie usuwaj ich i nie przesuwaj ich w Edit Mode. Inaczej Studio
nic nie przyjmie i powie, które kości.

Model z własnymi kośćmi (koń, dowolne stworzenie) wysyła własne animacje, pod ich własnymi nazwami. Ta, którą zmienisz,
zajmuje swoje miejsce: każda czynność, która jej używała, używa jej zmienionej.

## Powrót do animacji z gry

| Aby usunąć | Kliknij | Gdzie |
|---|---|---|
| Zmianę dla wszystkich jednostek | **Wróć do wersji z gry** | Wiersz animacji w RUSE Decoy albo jej okno |
| Własną kopię tej jednostki (**Tylko ta jednostka**) | **Wróć do tego, czego używają wszystkie jednostki** | Wiersz animacji na liście jednostki albo jej okno |
| Zmiany kopii (nazwa i zaznaczenia zostają) | **Wróć do animacji z gry** | Okno kopii |
| Kopię, całą | **Usuń kopię** | **Twoje kopie** |
| Zmianę zrobioną w Blenderze | Cofnij ją w Blenderze, dopóki ten Blender jest jeszcze otwarty, potem **Przenieś moje zmiany**: cofa się też w twoim modzie | Blender, potem RUSE Decoy |

Przyciski wyżej nie usuwają zmiany zrobionej w Blenderze.

## Co może ci powiedzieć Przenieś moje zmiany

| Mówi | Co zrobić |
|---|---|
| „Zmienione w Blenderze, teraz własne tej jednostki: ...” | Nic: zadziałało. **Testuj w grze** to pokaże. |
| „Każda animacja wróciła taka, jaka wyszła.” | Nic nie zostało zmienione. Czy każdą pozę zachowałeś klawiszem **I**? |
| „Zrobione w Blenderze, jeszcze nieodtwarzane przez żadną akcję: ...” | Nowa animacja nie jest przyjmowana. Zapisz ją w Blenderze (**File > Save**), żeby ją zachować. |
| „Nieodesłane (usunięte lub przemianowane w Blenderze), więc grają jak wcześniej: ...” | Przywróć jej nazwę w Blenderze, jeśli chcesz swoją zmianę. |
| „Te grają tylko na jednej połowie ciała ... więc w grze mogą nie być widoczne” | Kości, które poruszyłeś, są w drugiej połowie: poruszaj kośćmi połowy, która ją odtwarza. |
| „Kości zrobione w Blenderze, których szkielet tej jednostki nie ma ...” | Nowej kości nie da się odtworzyć; reszta dotarła. |
| „Edytor NLA Blendera odtwarza te z własnym czasem ...” | Gra odtwarza je tak, jak pokazuje je Action Editor. |
| „Scena Blendera szła w ... klatkach na sekundę, a gra idzie w 30 ...” | Ustaw Blendera na 30 klatek na sekundę, żeby widzieć tempo gry. |
| „Scena Blendera ma włączone Time Stretching ...” | Ustaw Old i New na tę samą liczbę, żeby widzieć tempo gry. |
| „Żadna czynność tej jednostki nie odtwarza tych animacji ...” | Wybierz ją dla czynności w **Jej animacje** na stronie jednostki. |
| „Zmienione w Studio, odkąd wyszły do Blendera, a odesłane z Blendera bez zmian, więc zostaje zmiana ze Studio ...” | Nic: twoja zmiana z RUSE Decoy zostaje. |
| „Zmienione także w Studio, odkąd wyszły do Blendera: zmiana z Blendera zastępuje zmianę ze Studio ...” | Nic, jeśli chcesz zmiany z Blendera; jeśli nie, zrób swoją zmianę w RUSE Decoy jeszcze raz. |
| „Od ostatniego przeniesienia twoich zmian z Blendera nie przyszło nic nowego.” | Najpierw kliknij **Wyślij do R.U.S.E. Studio** w Blenderze. |

## Co może pójść nie tak

- **W grze nic się nie zmienia:** zmiana dla **Tylko ta jednostka** jest widoczna tylko na tej jednostce, a kopia tylko
  na jednostkach zaznaczonych dla niej. Zmiana zrobiona w Blenderze ma dla tej jednostki pierwszeństwo przed późniejszą
  zmianą tej samej animacji przez **Tylko ta jednostka** albo kopię (reguła Studio; jeszcze nie sprawdzone w grze).
- **„Tylko nowa jednostka zrobiona w tym modzie dostaje własne animacje”**: to jednostka z gry. Najpierw zrób z niej
  nową jednostkę (**Nowa jednostka z tej…** na jej stronie).
- **Na stronie brakuje Jej animacje:** tabela jest tylko dla jednostki z własnymi animacjami (model z własnymi kośćmi).
  Wszystkie inne jednostki używają animacji z gry: zmieniaj je w RUSE Decoy.
- **Wysyłka, której nigdy nie przeniosłeś:** ponowne otwarcie Blendera ją odkłada. RUSE Decoy pokazuje ją z **Przenieś
  odłożoną wysyłkę** i **Przenieś do Kosza** (zobacz [[Otwórz w Blenderze|Otwórz-w-Blenderze]]).

## Co sprawdzono w grze

- Zmiany animacji w RUSE Decoy dla wszystkich jednostek, które ich używają (Studio 0.9.8.8).
- **Tylko ta jednostka**: oddział tańczący w miejscu, gdy wszystkie inne oddziały stały jak wcześniej (listopad 2026).
- **Kopiuj tę animację…**: kopia używana przez jeden oddział i przez jednego żołnierza innego (listopad 2026).
- **Zmień jego animacje w Blenderze**: oddział stojący i biegnący z podniesioną ręką, i Uniwersalne oddziały konne,
  których konie trzymają głowy w górze (listopad 2026).
- Własne animacje Uniwersalnego oddziału konnego, wybrane przez **Najbliższa**, i jazda samemu na długich trasach
  (listopad 2026).
- Jeszcze nie sprawdzone w grze: tempo, zamiennik albo kość zmienione tylko dla jednej jednostki, i inna animacja
  wybrana ręcznie w **Jej animacje**.

Nadal utknąłeś? Zapytaj na [Discordzie](https://discord.gg/h54t5baNsC) albo zajrzyj do
[[Gdy coś pójdzie nie tak|Gdy-coś-pójdzie-nie-tak]].

**Dalej:** [[Otwórz w Blenderze|Otwórz-w-Blenderze]] · [[Modele i kości|Modele-i-kości]]

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Unit-Animations]]
