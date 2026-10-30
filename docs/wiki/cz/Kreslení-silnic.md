# Kreslení silnic

> **Pro:** moddery · **Potřebujete:** RUSE Studio 0.7.4 a mod · **Ověřeno ve hře:** zásobovací trasy vedou po nové
> silnici a ta je namalovaná na terénu

## Zobrazení silnic mapy

Zaškrtněte **Silnice** nahoře nad mapou: vlastní silnice mapy se ukážou zlatě, na terénu, i když ho tvarujete.

## Nakreslení nové silnice

1. Na liště dole klikněte na **Silnice a mosty** (otevře se její záložka **Silnice**). Silnice mapy se ukazují
   zlatě, vaše nové modře.
2. Vyberte nástroj:

| Nástroj | Jak |
|---|---|
| **Rovná** | Klikněte tam, kde silnice začíná, pak tam, kde končí. |
| **Oblouk** | Klikněte na začátek, pak na ohyb, ke kterému se silnice táhne, pak na konec. |
| **Volná** | Klikejte podél trasy; pro ukončení dvakrát klikněte, stiskněte **Enter** nebo klikněte na **Hotovo**. |

3. Za ukazatelem se táhne modrý pás a vedle něj **délka silnice** (Volná ukazuje i úsek od vašeho
   posledního kliknutí). Konec blízko jakékoli silnice se k ní **přichytí** (ukáže to kruh), takže se na ni nová
   silnice napojí: zásobovací náklaďáky mohou jet z jedné na druhou. Nástroje Silnice ukazují, kolik nových silnic
   mapa má a jakou mají celkovou délku.
4. **Esc** zahodí silnici, kterou právě kreslíte; **Zpět** (nebo **Ctrl+Z**) vrátí poslední, **Znovu** (nebo **Ctrl+Y**)
   ji nakreslí znovu.

Nové silnice se hned ukládají do vašeho modu (`maps/<map>/roads.toml`).

## Co nová silnice dělá ve hře

- **Zásobovací trasy ji používají** (ověřeno: trasa zásobovacího skladu vzala novou zkratku přes otevřená pole).
- **Je namalovaná na terénu** barvou silnic mapy, takže ji hráči vidí (ověřeno ve hře). Vypadá jako vlastní
  silnice mapy z výšky i úplně dole u země.
- **Pěchota po ní chodí**, aby se někam dostala rychleji (ověřeno ve hře, Studio 0.8.0).
- **Přes vodu dostane most**: druh mostu té mapy (24 z 32 map nějaký má), jeden díl natažený od břehu k
  břehu, jak to mají mosty hry, a jednotky po něm mohou přejet. Silnice přes některý z vlastních mostů mapy dostane
  na jeho místo nový most. Na mapě bez druhu mostu to sestavení oznámí a voda zůstane uzavřená. (Ověřeno
  ve hře: tanky, pěchota a zásobovací náklaďáky přejíždějí po mostovce.)
- Rostliny a předměty na její trase se odstraní; **Ponechat stromy na nových silnicích** ponechá stromy a keře
  (silnice pod stromy).

## Odebrání vlastních silnic a mostů mapy

V nástrojích **Silnice**:

- **Odebrat silnice mapy:** vlastní silnice mapy zmizí: síť, po které jezdí zásobovací náklaďáky (místo toho jedou
  terénem), i silnice namalované na terénu. Vaše nové silnice zůstanou. Viděno ve hře: silnice zmizí; zásobovací
  náklaďáky jedoucí terénem zatím vyzkoušené nejsou.
- **Odebrat mosty mapy:** vlastní mosty mapy zmizí, i s mostovkami, na kterých jednotky stály. Jednotky přesto přejdou
  tam, kde mosty stály, po terénu pod nimi, pokud nezaškrtnete i další pole. Vaše nové mosty zůstanou.
- **Uzavřít přechody po starých mostech** (s odebranými mosty; od DomesticNukes): terén, kde každý starý most stál nad
  vodou, se jednotkám uzavře a silniční spojení přes něj se přeruší: nic tam nepřejde, ani zásobovací náklaďáky, a
  zbytek silniční sítě zůstane. Vaše nová silnice, která přechází na stejném místě, tam dostane vlastní most. Kdyby
  jejich uzavření odřízlo kus terénu od zbytku, Studio to řekne před sestavením.

Zatím nevyzkoušeno ve hře: odebrání mostů a uzavření jejich přechodů.

## Umístění vlastního mostu

V záložce **Mosty**: vyberte druh, nastavte jeho délku a otočení, pak klikněte na terén tam, kam přijde střed mostu.
Oba konce by měly ležet na suchém břehu. **Zpět** a **Znovu** fungují i tady.

**Podívejte se:** **Vyzkoušet ve hře**, pak v hlavní nabídce hry **BITVY** a mapa. Umístěte blízko své silnice
zásobovací sklad a sledujte jeho trasu.

**Další:** [[Umisťování budov a stromů|Umisťování-budov-a-stromů]]

---

[[Polní příručka|Polní-příručka]] · [[English|Draw-Roads]]
