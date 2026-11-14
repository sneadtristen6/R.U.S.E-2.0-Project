# Modely a kosti

> **Potřebuješ:** RUSE Studio 0.9.8.20 nebo novější, mod s novou jednotkou a Blender (zdarma), abys mohl měnit kosti ·
> **Zabere:** 10 minut čtení

Vojáci, koně a jakákoli stvoření se v R.U.S.E. hýbou, protože jejich 3D model má **kosti**. Tahle stránka říká, co jsou
kosti, jak je hra používá, co znamená každý rámeček o kostech na stránce jednotky a co s ním dělat. Tank otáčí věží a
koly bez animací, takže tahle stránka je hlavně o vojácích, koních a stvořeních.

## Co jsou kosti

- **Model** je skořápka z bodů, na které jsou namalované obrázky.
- Uvnitř jsou jako kostra **kosti**: paže, předloktí, ruka, hlava, každá noha koně. Každá kost visí na jiné (ruka na
  předloktí, předloktí na paži), až k první kosti.
- Každý bod skořápky jde za kostí, nebo za několika: body rukávu jdou za paží. Jak moc bod jde za každou kostí, je jeho
  **váha**.
- **Animace** hýbe kostmi, snímek po snímku, a skořápka jde za nimi. Tak voják jde, míří a padá.
- V Blenderu jsou kosti modelu jeden objekt, kterému se říká **armature**.

## Jak je hra používá

- Hra hýbe kostmi modelu **podle jejich místa v seznamu kostí**, ne podle jmen. Animace udělaná pro jeden model proto
  sedí jen na model se stejnými kostmi ve stejném pořadí.
- Některé kosti mají úkol: výstřel vychází z kosti u ústí zbraně, horní část těla se otáčí k cíli u kosti páteře, zbraň
  se ukazuje a skrývá na kosti, věž nebo kolo se otáčí na kosti. Stránka jednotky jmenuje každou, která tvému modelu
  chybí (viz **Bude to ve hře fungovat?** níže).
- Voják hraje **dvě animace najednou**: jednu na horní polovině těla (míření, střelba) a jednu na dolní (chůze, běh).
  Kůň s jezdcem taky: viz **Jeho dvě poloviny** níže.
- Hra nebyla viděna animovat model s více než 64 kostmi.

## Dva druhy modelů

| | Na kostech vojáka ze hry | S vlastními kostmi |
|---|---|---|
| **Co to je** | Voják změněný v Blenderu, nebo tvůj model nasazený na kosti vojáka | Kůň, kůň s jezdcem, jakékoli stvoření, udělané v Blenderu na tvých kostech |
| **Jak ho udělat** | **Otevřít v Blenderu** na kartě družstva: každý voják se otevře se svými kostmi (viz [[Otevřít v Blenderu|Otevřít-v-Blenderu]]) | V Blenderu, pak **Importovat model…** v řádku vojáka, pod **Každý voják** (viz [[Import modelu|Import-modelu]]) |
| **Jeho animace** | Ty ze hry, jako voják | Vlastní, z jeho souboru |
| **Jeho dvě poloviny** | Ty ze hry: není co vybírat | Vybíráš je ty (Studio navrhne kost) |
| **Velikost a místo** | Jak jsi ho udělal v Blenderu, na jeho kostech | Jak je v jeho souboru |

Stránka říká, o který jde. U modelu na kostech vojáka ze hry: „Tvůj model je na kostech vojáka ze hry, takže si nechává
dvě poloviny ze hry: není co vybírat.“ U modelu s vlastními kostmi: „Má vlastní kosti:“ a kolik. **Univerzální jízdní
družstvo** (karta **Jednotky**, **2. světová válka+**) je družstvo s vlastními kostmi: viz
[[Jednotky z jiných období|Jednotky-z-jiných-období]].

## Kde je stránka ukazuje

Na stránce nové jednotky je všechno o kostech ve **Vzhled a pohyb**:

| Rámeček | Kde | Co ti řekne |
|---|---|---|
| **Jeho kosti a animace** | Řádek **Zvuky a animace**, **Více** | Kolik kostí model má, a každá animace s délkou a s počtem činností jednotky, které ji hrají (model s vlastními kostmi) |
| **Jeho dvě poloviny** | Řádek **Zvuky a animace**, **Více** | Kde se model dělí na horní a dolní polovinu |
| **Její animace** | Řádek **Zvuky a animace**, **Více** | Jakou animaci jednotka hraje pro každou svou činnost: viz [[Animace jednotek|Animace-jednotek]] |
| **Bude to ve hře fungovat?** | Řádek **Model**, **Více**; na stránce družstva **Další možnosti** pod vojáky, pak **Model každého vojáka** | Co by v modelu mohlo zastavit hru nebo vypadat špatně, a jak to opravit |
| Body bez kosti | Na stejném místě jako **Bude to ve hře fungovat?** | Kolik bodů modelu nejde za žádnou kostí |

## Jeho dvě poloviny

Hra na vojákovi hraje dvě animace najednou: jednu na jeho **horní polovině** (míření, střelba) a jednu na **dolní
polovině** (chůze, běh). Jezdec míří a střílí, zatímco jeho kůň běží: jezdec je horní polovina, kůň dolní.

- Model na kostech vojáka ze hry si nechává poloviny ze hry: stránka píše „není co vybírat“.
- Model s vlastními kostmi se dělí u **jedné kosti**: ta kost a všechny kosti pod ní tvoří horní polovinu, všechny
  ostatní dolní.

Jak ji vybrat:

1. Na stránce jednotky ve **Vzhled a pohyb** klikni na **Více** v řádku **Zvuky a animace**.
2. Pod **Jeho dvě poloviny** seznam **Horní polovina začíná u** ukazuje nejdřív návrh Studia, označený „(navrženo)“.
   Studio navrhne první kost jezdce na koni s jezdcem (**bip01** u Univerzálního jízdního družstva), jinak první kost
   jménem spine (jako u vojáka), jinak kost, kde se kostra poprvé větví.
3. Většině modelů návrh sedí: nech ho být. Chceš-li ho změnit, vyber v seznamu jinou kost. Uloží se hned a ve hře je
   vidět po příštím sestavení (**Vyzkoušet ve hře**).
4. Pod seznamem stránka počítá kosti každé poloviny a **Která kost kam patří** vypíše každou kost modelu s označením
   horní polovina nebo dolní polovina.
5. Pro návrat k návrhu vyber znovu první řádek seznamu.

Jiné rozdělení než navržené zatím nebylo ve hře vyzkoušeno.

## Váhy: za kterou kostí jde každý bod

Když nasadíš vlastní model (nebo helmu, batoh, zbraň) na kosti vojáka, Blender musí vědět, za kterou kostí jde každý
jeho bod. Tohle jsou kroky samotného Blenderu.

**Tvůj model na vojákovi, každý bod jde za nejbližšími kostmi:**

1. Na kartě družstva klikni na **Otevřít v Blenderu**: Blender se otevře s vojáky, každý na svých kostech.
2. V Blenderu načti svůj model přes **File > Import** a umísti ho na vojáka.
3. Klikni na svůj model, pak **Shift+klik** na kosti vojáka: kosti jako poslední.
4. Stiskni **Ctrl+P** a vyber **With Automatic Weights**. Blender spočítá váhy za tebe.
5. Smaž, co si nenecháváš (tvar vojáka ze hry, pokud tvůj model zabírá jeho místo), ale jeho kosti si nech.
6. Klikni na **Poslat do R.U.S.E. Studia** nahoře v 3D pohledu Blenderu, pak ve Studiu na **Přenést moje změny**.

**Tuhý díl, který jde jen za jednou kostí (helma na hlavě):**

1. V Blenderu klikni na helmu, pak **Shift+klik** na kosti vojáka.
2. Stiskni **Ctrl+Tab** pro Pose Mode a klikni na kost hlavy.
3. Stiskni **Ctrl+P** a vyber **Bone**. Helma se teď hýbe s hlavou a dostane ji jen tento voják, když přeneseš změny.

**Body bez kosti.** Automatické váhy Blenderu občas pár bodů vynechají. Stránka pak píše „{n} bod(ů) tvého modelu nemá
kost, takže se hýbou jen s boky vojáka.“ Jak to opravit:

1. Znovu **Otevřít v Blenderu**.
2. Klikni na svůj model a přepni režim Blenderu (vlevo nahoře v 3D pohledu) z **Object Mode** na **Weight Paint**.
3. Ve vlastnostech modelu (zelený trojúhelník) mají **Vertex Groups** jednu skupinu na každou kost: vyber kost, za kterou
   mají ty body jít.
4. Přemaluj ty body.
5. **Poslat do R.U.S.E. Studia**, pak **Přenést moje změny**.

## Bude to ve hře fungovat?

Studio kontroluje model na kostech proti animacím, které hraje, a proti částem a výstřelům jednotky, kterou kopíruje.
Sestavení modu to zkontroluje znovu, se všemi tvými změnami. Problém tě nikdy nezastaví: řekne, co se stane a jak to
opravit.

**Kde:** na stránce nové jednotky, **Vzhled a pohyb**, řádek **Model**, **Více**. Na stránce družstva: **Další
možnosti** pod vojáky, pak **Model každého vojáka**.

Když je všechno v pořádku, píše: „Nenašlo se nic, co by zastavilo hru: každá přehrávaná animace má jeho kosti a každá
kost, kterou potřebují části a výstřely, tam je.“ (s počtem kostí).

### Co znamená každá odpověď

Každý problém říká tři věci: co nesedí, co s tím hra udělá a jak to opravit. Prostřední řádek je jeden z těchto:

| Stránka píše | Co to znamená | Co dělat |
|---|---|---|
| Tohle může zastavit hru: stalo se to v testu. | Hra se tak zastavila v jednom z našich testů. | Oprav to před testem. |
| Tohle může zastavit hru (ve hře zatím nevyzkoušeno). | Čeká se, že se hra zastaví. | Oprav to před testem. |
| Hra to přehraje, ale bude to vypadat špatně (ve hře zatím nevyzkoušeno). | Hýbaly by se špatné kosti. | Oprav to, nebo to vyzkoušej a podívej se. |
| Jednotka dál bojuje, ale její výstřely nebude vidět: stalo se to v testu. | Způsobuje škody, ale výstřel není vidět. | Přidej kost, kterou stránka jmenuje. |
| Ve hře zatím nevyzkoušeno: hra ho možná nebude animovat. | Víc kostí, než hra kdy byla viděna animovat. | Spoj nebo smaž kosti. |
| Pořád to funguje, ale možná ne tak, jak chceš. | Poznámka k jeho dvěma polovinám. | Zkontroluj **Jeho dvě poloviny**. |

### Každý problém a jeho oprava

**Animace, které nesedí na kosti modelu.** Stránka říká, kolik animací, pro kolik činností a proč nesedí: „Hýbou {a}
kostmi a tvůj model jich má {b}.“ (nebo „jen {b}“), nebo stejně kostí, ale „jinak pojmenovaných“, nebo „v jiném
pořadí“. Ty animace byly udělané pro jiné kosti.

- Když jednotka hraje na tvém modelu animace ze hry: dej těm činnostem vlastní animace tvého modelu. **Importovat
  model…** přinese každou animaci ze souboru tvého modelu a v **Její animace** vybereš, kterou hraje každá činnost
  ([[Animace jednotek|Animace-jednotek]]).
- Když jsou to vlastní animace tvého modelu, udělané pro jiný model: udělej je znovu v Blenderu na kostech tohoto modelu
  a model znovu naimportuj.

**Kost, kterou jednotka potřebuje.** Například: „Střelci: výstřely vycházejí z kosti jménem Fx_Tir_01 a tvůj model ji
nemá.“ (nebo: horní část těla se tam otáčí k cíli, zbraň se tam ukazuje a skrývá, díl se tam drží, věž nebo kolo se tam
otáčí, tělo tam spočívá, tažené dělo se tam zapřahá). Jak kost přidat v Blenderu:

1. Otevři model v Blenderu: **Otevřít v Blenderu** se zaškrtnutým **Jeho kosti** (viz
   [[Otevřít v Blenderu|Otevřít-v-Blenderu]]), nebo vlastní soubor Blenderu.
2. Klikni na kosti (armature) a stiskni **Tab** pro Edit Mode.
3. Stiskni **Shift+A**: nová kost se objeví tam, kde je 3D kurzor Blenderu.
4. Stiskni **F2** a napiš přesně jméno, které uvádí stránka (například `Fx_Tir_01`). Má-li tvůj model tu kost pod jiným
   jménem, přejmenuj raději ji.
5. Ve vlastnostech kosti (ikona kosti) v **Relations** nastav jako **Parent** kost, se kterou se díl hýbe: pro výstřel
   kost, se kterou se hýbe zbraň.
6. Stiskni **G** a přesuň novou kost tam, kam díl patří: pro výstřel na konec hlavně zbraně.
7. Znovu stiskni **Tab**, klikni na **Poslat do R.U.S.E. Studia**, pak na **Přenést moje změny** (nebo vyexportuj vlastní
   soubor a klikni na **Importovat jiný…**). **Bude to ve hře fungovat?** model zkontroluje znovu.

**Příliš mnoho kostí.** „Tvůj model má {n} kostí. Hra nebyla viděna animovat model s více než 64 kostmi.“ V Blenderu
spoj nebo smaž kosti, až jich bude 64 nebo míň, pak model přenes zpět.

**Rozdělení.** „Rozdělení u {bone}, první kosti tvého modelu, dává všechny kosti do horní poloviny, takže animace dolní
poloviny (chůze, běh) nehýbou ničím.“: vyber v **Jeho dvě poloviny** kost níž, tam, kde začíná horní část těla. „Kost
vybraná pro rozdělení, {bone}, už v tvém modelu není, takže se dělí u {used}.“: vyber kost znovu.

**Druhý model družstva na jiných kostech.** „Jeho model má vlastní kosti, jiné než model tvých střelců, takže hraje to,
co v kopírované jednotce, udělané na kostech vojáka ze hry: to může hru zastavit.“ Model vojáka s těžkou zbraní musí být
na stejných kostech jako model střelců, aby hrál jejich animace: udělej jeho model z modelu střelců v Blenderu, pak ho
naimportuj v jeho řádku. Odebrání modelu střelců odebere i jeho model.

## Jak udělat model s vlastními kostmi v Blenderu

1. **Jeho kosti:** tvůj model na armature s tvými kostmi, pojmenovanými jak chceš, a jeho váhy
   (**Ctrl+P > With Automatic Weights**, výše).
2. **Jeho animace:** jedna action na animaci (v Blenderu **Dope Sheet > Action Editor**). Pojmenuj každou podle toho, co
   ukazuje: aspoň **stand** (nebo **idle**), **walk** a **run** (nebo **gallop**); známé jsou i **fire**, **aim**,
   **reload**, **hit**, **death**, **crouch**, **look**, **flee** a **grenade**. Jméno jako **t_fire** (nebo
   **hr_t_fire**) hraje jen na horní polovině a **b_run** (nebo **hr_b_run**) jen na dolní: jezdcova a koňova.
3. **Vyexportuj ho:** **File > Export > glTF 2.0**, formát **glTF Binary (.glb)**, se zaškrtnutým **Animation**.
4. **Naimportuj ho** na nové družstvo: viz [[Import modelu|Import-modelu]].
5. **Zkontroluj jeho stránku:** **Jeho kosti a animace** (dorazila každá animace a kolik činností každou hraje), **Jeho
   dvě poloviny**, **Její animace**, **Bude to ve hře fungovat?**
6. **Vyzkoušet ve hře.**

Změnil jsi ho pak v Blenderu? Naimportuj ho znovu: každá činnost si nechá svou animaci, dokud je animace toho jména
ještě v souboru.

## Co bylo vyzkoušeno ve hře

- Univerzální jízdní družstvo, udělané takhle (střelci a voják s bazukou na koních, model s vlastními kostmi): střílejí,
  na dlouhých přesunech jedou sami za sebe a každý kůň padá se svým jezdcem (listopad 2026).
- Voják družstva změněný v Blenderu na kostech vojáka ze hry, s body zváženými tam (listopad 2026).
- Ve hře zatím nevyzkoušeno: jiné rozdělení než navržené a každý problém, který stránka označí „ve hře zatím
  nevyzkoušeno“.

Pořád nevíš? Zeptej se na [Discordu](https://discord.gg/h54t5baNsC), nebo se podívej na
[[Když se něco pokazí|Když-se-něco-pokazí]].

**Další:** [[Animace jednotek|Animace-jednotek]] · [[Otevřít v Blenderu|Otevřít-v-Blenderu]]

---

[[Polní příručka|Polní-příručka]] · [[English|Models-and-Bones]]
