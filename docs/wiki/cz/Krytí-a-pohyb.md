# Krytí a pohyb

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.7.2 a mod · **Ověřeno ve hře:** pěchota na namalovaném krytu
> je skrytá; jednotky plánují cestu kolem zablokovaného terénu

O tom, jak se mapa hraje, rozhodují dvě neviditelné vrstvy: **kryt** (kde se jednotky skrývají) a **pohyb** (kam
jednotky mohou).

## Kryt: město nebo les, ve kterém se jednotky skryjí

1. Na liště klikněte na **Kryt a pohyb** (jeho záložka **Kryt**). Mapa zezelená tam, kde jsou jednotky teď skryté (lesy a města mapy).
2. Vyberte nástroj:
   - **Kryt** maluje terén, ve kterém se jednotky skryjí (tažením);
   - **Odkrýt** ho odebírá (tažením): terén, přes který přejel, je bíle pruhovaný, i tam, kde žádný kryt k odebrání
     nebyl;
   - **Město** dá kryt kolem každé budovy města, na které kliknete. Nejdřív na město ukažte: na každé budově, kterou
     pokryje, se ukáže kruh a vedle ukazatele jejich počet. **Velikost** určuje, jak daleko kolem každé budovy.
3. Po každém tahu řádek vedle ukazatele řekne, co se pro jednotky změnilo („Krytí odebráno z 12 000 m²“,
   nebo „Tady není krytí k odebrání“).
4. Zaškrtněte **Kryt** nahoře nad mapou, aby zelená zůstala vidět, i když používáte jiné nástroje.

> [!NOTE]
> Umístěné budovy a stromy samy jednotky neskrývají. Po umístění města na něj klikněte nástrojem **Město**.

## Pohyb: uzavřete terén jednotkám

1. Zaškrtněte **Kam jednotky mohou** nahoře nad mapou:
   - **červená**: tam nemůže žádná jednotka (voda, útesy, mimo mapu);
   - **žlutá**: jen pěchota (lesy);
   - **fialová**: jen vozidla.
2. Na liště klikněte na **Kryt a pohyb**, pak na záložku **Pohyb**, a táhněte:
   - **Zablokovat**: neprojde žádná jednotka (zeď, minové pole, útes, který jste vytvořili);
   - **Zablokovat pěchotě**: vozidla dál projedou;
   - **Zablokovat vozidlům**: pěchota dál projde, jako v lese;
   - **Otevřít**, **Otevřít pěchotě**, **Otevřít vozidlům**: pustí jednotky na terén, kam je mapa nepouští (opak
     Zablokovat).
3. Terén, přes který přejel tah Zablokovat nebo Otevřít, je pruhovaný: modře tam, kam jednotky mohou, červeně, žlutě
   nebo fialově tam, kde je uzavřený. Vedle ukazatele každý tah řekne, kolik uzavřel nebo otevřel, nebo že se tam nic
   nezměnilo.

Jednotky plánují trasu kolem zablokovaného terénu. Budovy, které umístíte, jednotky také blokují (viz
[[Umisťování budov a stromů|Umisťování-budov-a-stromů]]).

**Další:** [[Kreslení silnic|Kreslení-silnic]]

---

[[Polní příručka|Polní-příručka]] · [[English|Cover-and-Movement]]
