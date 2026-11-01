# Foldery i pliki modów

> **Informacje** · Nigdy nie musisz ich ruszać ręcznie: zapisuje je Studio. Ta strona jest na wypadek, gdy coś wygląda
> źle, albo dla modderów, którzy edytują pliki bezpośrednio.

## Gdzie co jest

| Co | Gdzie |
|---|---|
| Mody Studio | `%LOCALAPPDATA%\RUSE Mod Platform\mods\<mod>` (wklej to w pasek adresu Eksploratora plików) |
| Mody zainstalowane w launcherze | `%LOCALAPPDATA%\RUSE Mod Platform\library` |
| Zmodowane kopie gry | Folder, który wybierzesz w Ustawieniach (**Gdzie trafiają kopie z modami**, w dowolnej z aplikacji); zalecane miejsce to `RUSE-Instances` na tym samym dysku co gra (na przykład `D:\RUSE-Instances`), gdzie kopia dzieli pliki z grą. Na innym dysku każda kopia jest pełną kopią gry: wolniejszą i większą. Czysta kopia zapasowa gry (`RUSE-Backup`) trafia obok. |
| Sama gra | Nigdy nie jest zmieniana |

## Wewnątrz moda

```
my-mod/
  mod.toml                    the mod's name, id, version, author (required)
  src/studio.rndf             unit changes made in the Studio
  text/studio.baseunite.csv   names of new units
  files/replace/gen/...png    a unit's paint (from Blender) or a unit's card, under the game texture it changes
  files/cards/<unit>.png      a new unit's own card in the build menu, named after the new unit
  files/models/<unit>.glb     a new unit's own 3D model (Import model), named after the new unit
  menu_groups.toml            the group of its building's build list each new unit stands in (the Studio writes it)
  maps/<map pack name>/       one folder per map the mod changes:
    terrain.toml                ground brushes (also water, cover and block brushes)
    scenery.toml                buildings, props and trees placed
    scenario.toml               starting points and spawns moved, units added
    cover.toml, movement.toml   cover and movement written by hand
    map.toml                    how many players; or, for a new map, the map it copies and its name
```

## Nazwa folderu mapy to nazwa paczki mapy, a nie jej tytuł

Gracze znają mapę po tytule (**Blitz**); pliki gry używają jej nazwy paczki (**SuperCrossRoads4**). Folder mapy musi
używać nazwy paczki: `maps/SuperCrossRoads4/`, a nie `maps/Blitz/`. Pary dla każdej mapy są w [[Nazwy map|Nazwy-map]],
a lista map w Studio pokazuje obie nazwy: najpierw tytuł, nazwę paczki po kropce.

## Nowa mapa

Mod może dodać własną mapę do menu BITWY: kopię mapy z gry albo pusty start, pod własną nazwą, którą pozostałe pliki moda
potem przekształcają. Nazwa jej folderu to nazwa paczki nowej mapy (litery, cyfry i `_`), a jej `map.toml` mówi, którą
mapę kopiuje i jak nazywają ją menu:

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from (its pack name: Blitz)

[name]
us = "Blitz Twin"              # English, used where a language is left out
fr = "Blitz jumeau"
```

`maps/BlitzTwin/terrain.toml` i reszta plików edytują wtedy kopię, a Blitz zostaje taki, jaki był. Skopiować można każdą
mapę z listy BITWY; map kampanii i Operacji nie. Dwóch graczy potrzebuje tego samego moda, by zagrać na niej razem, jak
przy każdym modzie. Nowe mapy działają w grze (2026-10-03), a **Duplikuj mapę** w Studio robi ten folder za ciebie.

## Częste błędy

| Błąd | Co się dzieje | Poprawka |
|---|---|---|
| Zip zawiera folder w folderze | Launcher zagląda jeden folder niżej i go znajduje. Dwa lub więcej niżej: mówi, że nie znalazł moda. | Spakuj folder, w którym jest `mod.toml`. |
| Folder mapy nazwany od tytułu mapy | Budowanie mówi, że to nie jest nazwa paczki mapy. | Zmień nazwę na nazwę paczki. |
| Plik edytowany ręcznie ma literówkę | Kontrola moda podaje plik i wiersz. | Popraw go albo użyj **Odłóż** w Studio. |
| `.exe`, `.dll` lub skrypt PC w modzie | Odrzucony: mody niosą tylko dane (własne skrypty misji gry, w postaci, w jakiej zapisuje je Studio, są jedynym wyjątkiem). | Usuń go. |

Jeśli pliku nie da się odczytać, Studio nigdy go nie nadpisuje: twoja praca nigdy nie przepada. **Odłóż** zmienia jego
nazwę na `<name>.broken.toml` obok oryginału.

---

[[Podręcznik polowy|Podręcznik-polowy]] · [[English|Mod-Folders-and-Files]]
