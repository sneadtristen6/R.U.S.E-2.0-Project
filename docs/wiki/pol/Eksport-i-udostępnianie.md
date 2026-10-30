# Eksport i udostępnianie

> **Dla:** modderów · **Potrzebujesz:** RUSE Studio i gotowego moda · **Czas:** 5 minut

## 1. Eksport

1. Otwórz menu **Mod** i wybierz **Eksportuj mod…**.
2. Wypełnij pole **Wersja** (trzy liczby, np. `1.0.0`), swoje imię i jeden wiersz o tym, co robi mod.
3. Wybierz, gdzie zapisać. Studio buduje mod raz na twojej grze, by zapisać wersję gry, na której powstał, i jego
   **odcisk palca** (krótki kod, taki sam u każdego, kto ma te same mody), potem zapisuje jeden plik:
   `<your-mod>-<version>.rusemod`.

Ten plik to wszystko, czego potrzebuje gracz: dodaje go w RUSE Launcher ([[Instalacja i gra|Instalacja-i-gra]]).

**Duże mody map:** przy mapie zmienionej w całości budowanie może liczyć kilka minut (na przykład, gdzie jednostki mogą
przejść po terenie, który otworzyłeś). Czekasz na to raz. Eksport wkłada do pliku to, co budowanie wyliczyło, więc
pierwsze budowanie u gracza jest krótsze. Plik zawiera tylko nasze własne liczby, nigdy pliku gry, i jest zablokowany
własnym plikiem gry dla tej mapy: otwiera się tylko na PC, który ma grę. Na razie tylko ruch; jeszcze nie widziane w grze.

Po zakończeniu eksportu Studio otwiera **Udostępnij swój mod** z rozmiarem pliku, jego sumą kontrolną SHA-256 i jego
wpisem na listę, gotowymi do skopiowania. Możesz to otworzyć znowu w każdej chwili z menu **Mod** (**Udostępnij swój
mod…**).

## 2. Udostępnij: dodaj go do obsługiwanych modów

Zrobiłeś mod? Dodaj go do listy i zostań współtwórcą. Zakładka **Obsługiwane mody** w RUSE Launcher pokazuje mody z listy
na [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), a gracze instalują je jednym kliknięciem (nowi
gracze dostają je w propozycji przy pierwszym uruchomieniu launchera):

1. Wgraj plik `.rusemod` (najłatwiej jako GitHub Release: twojego własnego repozytorium albo listy).
2. Otwórz pull request do [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), który dodaje wpis twojego
   moda do `index.toml`: wklej wpis, który pokazuje Udostępnij swój mod, i wstaw link do pliku w `download`. Rozmiar
   i SHA-256 muszą być tymi, które pokazał eksport: launcher odrzuca pobranie, które się nie zgadza, więc nikt nie może
   podmienić twojego pliku na inny.
3. Albo opublikuj go w [Discussions > Mods & maps](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) ze
   zrzutem ekranu i opisem tego, co zmienia (przeciągnij `.rusemod` do posta), a zostanie dodany do listy za ciebie.

Kod lub narzędzie testowe (darmowe jednostki, natychmiastowe budowanie...) dostaje tag `"cheat"`: launcher pokazuje go we
własnej grupie, „Kody i narzędzia testowe (opcjonalne)”, i nigdy go nie zaznacza ani nie pobiera, chyba że zrobi to
gracz. Nowa wersja to nowy plik z nowym numerem wersji: opublikowany plik nigdy się nie zmienia.

Dokładny format wpisu:
[MOD_FORMAT.md, sekcja 15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/docs/MOD_FORMAT.md#15-the-mod-index-supported-mods).

## Edytuj zainstalowany mod

W menu moda w Studio **Edytuj zainstalowany mod…** wymienia każdy mod, który ma Launcher (z polem wyszukiwania). Twój
własny otwiera swój projekt. Cudzy staje się twoją kopią z własną nazwą (nie może wziąć nazwy oryginału): twoje zmiany
trafiają do niej, a aktualizacja oryginału nigdy ich nie wymaże. Mod z RUSE Mod Manager (`.rmod`) jest przekształcany
w swojej kopii, więc jego zmiany wartości stają się zmianami Studio, które możesz zmieniać.

## Co może zawierać mod

Tylko dane: liczby, teksty, mapy, modele, tekstury. Programy (`.exe`, `.dll`, skrypty uruchamiane na PC) są odrzucane
przez obie aplikacje. Jeden wyjątek: własne skrypty misji gry, w postaci, w jakiej zapisuje je Studio. Działają wewnątrz
gry i mogą zrobić wszystko, co może gra, więc instaluj je tylko od autorów, którym ufasz ([SECURITY.md](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/SECURITY.md)).

## Dobre praktyki

- Zachowaj folder swojego moda: `.rusemod` jest dla graczy, a folder to to, co edytuje Studio.
- Napisz w poście, jakich innych modów twój potrzebuje albo z którymi się gryzie.
- Podziękuj ludziom, na których pracy budujesz.

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Export-and-Share]]
