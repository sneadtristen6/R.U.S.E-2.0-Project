# Otevřít v Blenderu

> **Potřebuješ:** RUSE Studio 0.9.8.20 nebo novější, mod a Blender (zdarma) · **Zabere:** 5 minut čtení

**Otevřít v Blenderu** vezme jednotku do Blenderu, bezplatného 3D programu, abys mohl změnit její tvar, kosti nebo
barvy; **Přenést moje změny** dá do tvého modu, co jsi tam udělal. Je to jedno tlačítko pro celou jednotku: **Co jde do
Blenderu** vedle něj říká, co odchází, a všechno, co odškrtneš, zůstane, jak je. Tahle stránka ho projde krok za krokem.

Animace se tímto tlačítkem nemění: mění se v RUSE Decoy (viz [[Animace jednotek|Animace-jednotek]]). Vlastní animace
modelu jdou s ním do Blenderu a vracejí se s ním.

## Kde tlačítko je

| Jednotka | Kde | Co se vrátí |
|---|---|---|
| Družstvo, které jsi udělal (nová jednotka tvého modu) | Velké **Otevřít v Blenderu** na jeho kartě, nahoře na jeho stránce | Jeho vojáci, každý zvlášť; jejich barvy |
| Jakákoli jiná jednotka, kterou jsi udělal (tank, letadlo) | **Vzhled a pohyb**, řádek **Model**, **Více**: rámeček **Změnit v Blenderu** | Celý její model (i kosti, jsou-li její vlastní), její barvy |
| Jednotka hry (ne družstvo) | Stejný rámeček | Jen její barvy: maluj na ni, zbytek zůstane z hry |
| Družstvo hry | Jeho karta říká, ať z něj nejdřív uděláš novou jednotku: **Nová jednotka z této…** | Jen jeho **Vlastní uniforma**, malovaná z jeho řádku **Uniforma** (**Otevřít v Blenderu**, pak **Přenést**) |

Na tomto PC není Blender? Stránka ukáže **Získat Blender (zdarma)**, které otevře stránku stažení Blenderu, a **Vybrat
Blender…**, abys Studiu ukázal, kde je `blender.exe`, pokud už ho máš.

## Co jde do Blenderu

Klikni na **Co jde do Blenderu ▾** vedle tlačítka. Na začátku je zaškrtnuté všechno. Odškrtni část, chceš-li ji nechat,
jak je: **Přenést moje změny** ji pak nechá, jaká byla, ať s ní Blender udělal cokoli.

| Vidíš | Znamená to |
|---|---|
| **Jeho vojáci**, pak každý voják („Střelec 1“, „Voják s bazukou 5“...) | Zaškrtnutí vojáci se otevřou vedle sebe v jednom Blenderu. Změň kteréhokoli: změní se jen ten, kterého změníš. |
| **Který model:** **Model střelců** nebo **Model vojáka s těžkou zbraní** | Družstvo s vlastními kostmi (Univerzální jízdní družstvo): jeden model najednou, s jeho kostmi a animacemi. |
| **Jeho model** | Tvar jednotky (jednotky, která není družstvo). |
| **Jeho kosti** | Její kosti (jen model s vlastními kostmi). Odškrtnuté: kosti tvého modu se vrátí, jak byly. |
| **Jeho barvy** | Její obrázky. Odškrtnuté: obrázky tvého modu se vrátí, jak byly. |

Dobré vědět:

- **Jen barvy** (její model nebo každý voják odškrtnutý): Blender se otevře s obrázky k malování a vrátí se jen barvy.
  Tak se maluje **Vlastní uniforma** družstva, pro všechny vojáky najednou. Družstvo ve výchozí uniformě to nemůže:
  „Nejprve vyberte Vlastní uniformu“ (výchozí uniformu nosí i jiná družstva a osádky). Nejdřív vyber **Vlastní
  uniforma** v jeho řádku **Uniforma**, ve **Vzhled a pohyb**.
- **Jeho kosti** odškrtnuté, ale v Blenderu se kost přidala, odebrala nebo přejmenovala: kosti si nejde nechat, takže se
  vrátí, jak je Blender poslal, a Studio to řekne.
- Družstvo vojáků ze hry nemá **Jeho kosti**: jeho vojáci se vrátí na kosti vojáka ze hry, ať s nimi Blender udělal
  cokoli.
- Nic zaškrtnuté: Studio napíše „Nejdřív zaškrtni, co jde do Blenderu: model, jeho kosti nebo jeho barvy.“

## Tam a zpět, krok za krokem

1. **Otevři ho.** Klikni na **Otevřít v Blenderu**. Blender se otevře (pár sekund to trvá) s tím, co jsi zaškrtl.
2. **Změň ho.** Maluj, měň tvar, nasaď vlastní model na kosti vojáka (viz [[Modely a kosti|Modely-a-kosti]], „Váhy“).
   To málo, co je potřeba vědět, je napsané nahoře v 3D pohledu Blenderu.
3. **Pošli ho.** Klikni na **Poslat do R.U.S.E. Studia** vlevo nahoře v 3D pohledu Blenderu.
4. **Přenes ho.** Ve Studiu teď tlačítko říká **Přenést moje změny**: klikni na něj. Stránka řekne, co přišlo: u družstva
   kdo se změnil a kdo ne, u jakékoli jiné jednotky soubor modelu, a co se zachovalo, protože bylo odškrtnuté.
5. **Vyzkoušet ve hře** to ukáže.

Blender můžeš nechat otevřený a udělat další kolo: změnit, poslat, přenést.

## Přenést moje změny

- **Blender je ještě otevřený?** **Přenést moje změny** ho nejdřív požádá, ať pošle, a počká (až minutu).
- **Zavíráš Blender?** Nejdřív klikni na **Poslat do R.U.S.E. Studia**: co jsi neposlal, zůstane v Blenderu a Studio to
  nikdy neuvidí.
- **Zavřel jsi ho po odeslání?** Tlačítko říká **Přenést moje změny**, dokud na něj neklikneš, a vezme, co jsi poslal
  naposledy. Na kartě družstva se odeslání udělané po posledním přenesení (nebo po **Přidat vojáka**) ukáže jako malé
  **Přenést moje změny** pod velkým tlačítkem, když je Blender zavřený: vezme, co jsi poslal naposledy.
- **Ještě nic neodesláno:** „Z Blenderu se zatím nic nevrátilo: v Blenderu klikni nahoře na Poslat do R.U.S.E. Studia,
  pak tady na Přenést moje změny.“
- Jeden Blender najednou pro jednotku: dokud ji Blender má, tlačítko Studia říká **Přenést moje změny**.

## Odložené odeslání

**Odeslání** je to, co Blender poslal tlačítkem **Poslat do R.U.S.E. Studia**. Když Blender znovu otevřeš dřív, než
přeneseš poslední odeslání:

- **Družstvo:** to odeslání se odloží ve složce Blenderu tvého modu, ve složce pojmenované `sent-not-brought-` s datem a
  časem, a nový Blender začne z toho, co má tvůj mod. Nic se neztratí, ale karta to zatím neřekne a nemá tlačítko, jak ho
  přenést: soubory jsou v `Documents\RUSE 2.0\Mods\<tvůj mod>\blender\<název jednotky>\squad\`.
- **Jakákoli jiná jednotka se zaškrtnutým modelem:** nic se neodkládá: další **Otevřít v Blenderu** začne z toho, co jsi
  poslal naposledy.
- **Animace v RUSE Decoy:** každé odložené odeslání je vypsané nad animacemi jednotky („Odesláno z Blenderu, nikdy
  nepřeneseno, odloženo ...“), s **Přenést odložené odeslání**, abys ho převzal, nebo **Přesunout do Koše**.

## Kde jsou tvoje soubory Blenderu

Ve složce tvého modu, `Documents\RUSE 2.0\Mods\<tvůj mod>\blender\<název jednotky>\`: soubory družstva ve `squad`, RUSE
Decoy v `animations`. Do modu se při exportu nedávají. Na stránce družstva **Další možnosti** říkají, kde jsou, s
**Ukázat ve složce**.

## Co se může pokazit

| Co se děje | Proč a co dělat |
|---|---|
| Blender se otevře prázdný | Podívej se v okně Blenderu po chybě (**Window > Toggle System Console**) a napiš nám na Discord. |
| Voják, na kterého jsem nesáhl, je označený jako změněný | Všechno, co se liší, se počítá jako změna, i přejmenovaný objekt. Jeho vzhled zůstane, jaký byl. |
| „Není na žádném vojákovi, takže neodesláno: ...“ | Něco, co jsi přinesl do Blenderu, není ani na kostech vojáka, ani v jeho kolekci: nasaď to na něj a pošli znovu. |
| Bod mého modelu se hýbe jen s boky | Nemá kost: viz [[Modely a kosti|Modely-a-kosti]], „Body bez kosti“. |
| Části ztratily lesk nebo barvu strany | Stránka je jmenuje: materiál přejmenovaný nebo nový v Blenderu se vrátí obyčejný. Nech materiálům jména, se kterými se Blender otevřel. |
| Nový tvar mé jednotky ze hry se nevrátil | U jednotky hry se vrací jen barvy. Udělej z ní novou jednotku, chceš-li měnit tvar. |

## Co bylo vyzkoušeno ve hře

- Barvy z Blenderu na jednotce, vidět zblízka i zdálky.
- Družstvo otevřené v Blenderu, jeden voják změněný a přenesený sám (listopad 2026).
- Ve hře zatím nevyzkoušeno: celý model tanku přes Blender a to, co **Co jde do Blenderu** zachová (vyzkoušeno s
  Blenderem a Studiem, mimo hru).

Pořád nevíš? Zeptej se na [Discordu](https://discord.gg/h54t5baNsC), nebo se podívej na
[[Když se něco pokazí|Když-se-něco-pokazí]].

**Další:** [[Změna družstva|Změna-družstva]] · [[Modely a kosti|Modely-a-kosti]] · [[Animace jednotek|Animace-jednotek]]

---

[[Polní příručka|Polní-příručka]] · [[English|Open-in-Blender]]
