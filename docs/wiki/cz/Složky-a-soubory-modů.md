# Složky a soubory modů

> **Přehled** · Ručně na ně nikdy sahat nemusíte: zapisuje je Studio. Tato stránka je pro chvíle, kdy něco
> vypadá špatně, nebo pro moddery, kteří upravují soubory přímo.

## Kde co je

| Co | Kde |
|---|---|
| Mody Studia | `Documents\RUSE 2.0\Mods\<mod>` (složka Dokumenty); změny map v `Maps`, exportované soubory v `Exports`, zálohy v `Backups`. Ve Studiu je **Nastavení → Kde jsou vaše soubory** otevře jednu po druhé a **Ukázat složku tohoto módu** (nabídka módu) otevře tu, kterou upravujete |
| Nainstalované mody launcheru | `%LOCALAPPDATA%\RUSE Mod Platform\library` |
| Kopie hry s mody | Složka, kterou zvolíte v Nastavení (**Kam se ukládají kopie s módy**, v kterékoli aplikaci); doporučené místo je `RUSE-Instances` na stejném disku jako hra (například `D:\RUSE-Instances`), kde kopie sdílí soubory hry. Na jiném disku je každá kopie úplnou kopií hry: pomalejší a větší. Čistá záloha hry (`RUSE-Backup`) jde vedle ní. |
| Samotná hra | Nikdy se nemění |

Starší verze Studia je ukládaly do `%LOCALAPPDATA%\RUSE Mod Platform` (`mods`, `maps`, `exports`, `mod-backups`): Studio je při prvním spuštění přesune do Dokumentů a řekne vám to.

## Uvnitř modu

```
my-mod/
  mod.toml                    the mod's name, id, version, author (required)
  src/studio.rndf             unit changes made in the Studio
  text/studio.baseunite.csv   names of new units
  files/replace/gen/...png    a unit's paint (from Blender) or a unit's card, under the game texture it changes
  files/cards/<unit>.png      a new unit's own card in the build menu, named after the new unit
  files/models/<unit>.glb     a new unit's own 3D model (Import model), named after the new unit
  maps/<map pack name>/       one folder per map the mod changes:
    terrain.toml                ground brushes (also water, cover and block brushes)
    scenery.toml                buildings, props and trees placed
    scenario.toml               starting points and spawns moved, units added
    cover.toml, movement.toml   cover and movement written by hand
    map.toml                    how many players; or, for a new map, the map it copies and its name
```

## Název složky mapy je název balíku mapy, ne její titul

Hráči znají mapu podle titulu (**Blitz**); soubory hry používají název jejího balíku (**SuperCrossRoads4**). Složka
mapy musí používat název balíku: `maps/SuperCrossRoads4/`, ne `maps/Blitz/`. Dvojici pro každou mapu najdete v [[Názvy map|Názvy-map]],
a seznam map ve Studiu ukazuje obojí: nejdřív titul, název balíku za tečkou.

## Nová mapa

Mod může do BITEV přidat vlastní mapu: kopii dodané mapy nebo prázdný začátek, pod vlastním názvem, kterou pak ostatní
soubory modu přetvoří. Název její složky je název balíku nové mapy (písmena, číslice a `_`) a její `map.toml` říká,
kterou mapu kopíruje a jak ji nazývají nabídky:

```toml
copy_of = "SuperCrossRoads4"   # the shipped map it starts from (its pack name: Blitz)

[name]
us = "Blitz Twin"              # English, used where a language is left out
fr = "Blitz jumeau"
```

`maps/BlitzTwin/terrain.toml` a ostatní pak upravují kopii a Blitz zůstane, jaký byl. Zkopírovat lze kteroukoli mapu,
kterou uvádí BITVY; mapy kampaně a operací ne. Dva hráči potřebují ke společnému hraní stejný mod, jako u každého
modu. Nové mapy se ve hře hrají (2026-10-03) a **Duplikovat mapu** ve Studiu tuto složku udělá za vás.

## Časté chyby

| Chyba | Co se stane | Oprava |
|---|---|---|
| Zip obsahuje složku uvnitř složky | Launcher se podívá o jednu složku níž a najde ho. Dvě a víc níž: řekne, že nenašel žádný mod. | Zazipujte složku, ve které je `mod.toml`. |
| Složka mapy pojmenovaná podle titulu mapy | Sestavení řekne, že to není název balíku mapy. | Přejmenujte ji na název balíku. |
| Ručně upravený soubor má překlep | Kontrola modu jmenuje soubor a řádek. | Opravte ho, nebo ve Studiu **Odložit**. |
| `.exe`, `.dll` nebo skript pro PC uvnitř modu | Odmítnuto: mody nesou jen data (vlastní skripty misí hry, tak jak je ukládá Studio, jsou jediná výjimka). | Vyjměte ho. |

Pokud soubor nejde přečíst, Studio ho nikdy nepřepíše: vaše práce se nikdy neztratí. **Odložit** ho přejmenuje na
`<name>.broken.toml` vedle originálu.

---

[[Polní příručka|Polní-příručka]] · [[English|Mod-Folders-and-Files]]
