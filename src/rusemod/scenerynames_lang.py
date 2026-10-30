"""The words of rusemod.scenerynames' English names in the Studio's other ten languages (words.toml's codes). One row
per English word or phrase: en|fr|ger|ita|spa|pol|ru|cz|jpn|sc|fa. A word with no row (a model or place name: Sherman,
Opel, Cherbourg...) stays as it is in every language. tests/test_scenerynames.py checks every English word the names
use has a row, or is one of KEPT."""

LANGS = ("fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc", "fa")

# names that read the same in every language
KEPT = {"Arnhem", "bis", "Blitz", "Cana", "Cassino", "Chaffee", "Cher", "Cherbourg", "Colditz", "Cromwell", "Djem",
        "Dovunque", "El", "Fiat", "GMC", "III", "IV", "Kasserine", "Kübelwagen", "Lee", "Matilda", "Monte", "Opel",
        "Panzer", "Pershing", "Sd.Kfz.", "Sherman", "Stuart", "Topolino", "Traction Avant", "Willys", "x", "Cotentin"}

ROWS = """
(Czech)|(tchèque)|(tschechisch)|(ceco)|(checo)|(czeski)|(чешский)|(český)|(チェコ式)|(捷克式)|(چکی)
(front-drive)|(traction avant)|(Frontantrieb)|(trazione anteriore)|(tracción delantera)|(przedni napęd)|(переднеприводный)|(přední pohon)|(前輪駆動)|(前驱)|(دیفرانسیل جلو)
administration|administration|Verwaltung|amministrazione|administración|administracja|администрация|správa|管理棟|行政楼|اداره
administrative|administratif|Verwaltungs-|amministrativo|administrativo|administracyjny|административный|správní|管理用|行政|اداری
adverts|affiches|Werbung|pubblicità|anuncios|reklamy|реклама|reklamy|広告|广告|آگهی‌ها
ammunition|munitions|Munition|munizioni|munición|amunicja|боеприпасы|munice|弾薬|弹药|مهمات
amphora|amphore|Amphore|anfora|ánfora|amfora|амфора|amfora|アンフォラ|双耳瓶|آمفورا
and|et|und|e|y|i|и|a|と|和|و
animal|animal|Tier|animale|animal|zwierzę|животное|zvíře|動物|动物|حیوان
antenna|antenne|Antenne|antenna|antena|antena|антенна|anténa|アンテナ|天线|آنتن
anti-aircraft|antiaérien|Flugabwehr|contraerea|antiaéreo|przeciwlotniczy|зенитный|protiletadlový|対空|防空|پدافند هوایی
apple tree|pommier|Apfelbaum|melo|manzano|jabłoń|яблоня|jabloň|リンゴの木|苹果树|درخت سیب
apples|pommes|Äpfel|mele|manzanas|jabłka|яблоки|jablka|リンゴ|苹果|سیب‌ها
apples on the|pommes sur|Äpfel auf|mele su|manzanas sobre|jabłka na|яблоки на|jablka na|リンゴ・|苹果在|سیب‌ها روی
arch|arche|Bogen|arco|arco|łuk|арка|oblouk|アーチ|拱门|طاق
arches|arches|Bögen|archi|arcos|łuki|арки|oblouky|アーチ群|拱门组|طاق‌ها
artillery|artillerie|Artillerie|artiglieria|artillería|artyleria|артиллерия|dělostřelectvo|砲兵|炮兵|توپخانه
asphalt|asphalte|Asphalt|asfalto|asfalto|asfalt|асфальт|asfalt|アスファルト|沥青|آسفالت
axe|hache|Axt|ascia|hacha|siekiera|топор|sekera|斧|斧头|تبر
bag|sac|Sack|sacco|saco|worek|мешок|pytel|袋|袋子|کیسه
bags|sacs|Säcke|sacchi|sacos|worki|мешки|pytle|袋|袋子|کیسه‌ها
bar|bar|Bar|bar|bar|bar|бар|bar|バー|酒吧|بار
barbed wire|barbelés|Stacheldraht|filo spinato|alambre de espino|drut kolczasty|колючая проволока|ostnatý drát|有刺鉄線|铁丝网|سیم خاردار
bare|nu|kahl|spoglio|desnudo|nagi|голый|holý|裸の|光秃|لخت
barge|péniche|Lastkahn|chiatta|barcaza|barka|баржа|nákladní člun|はしけ|驳船|بارج
barn|grange|Scheune|fienile|granero|stodoła|амбар|stodola|納屋|谷仓|انبار غله
barracks|caserne|Kaserne|caserma|cuartel|koszary|казармы|kasárna|兵舎|兵营|سربازخانه
barrel|tonneau|Fass|barile|barril|beczka|бочка|sud|樽|木桶|بشکه
base|base|Basis|base|base|baza|основание|základna|土台|底座|پایه
basin|bassin|Becken|vasca|pila|basen|бассейн|nádrž|水盤|水池|حوض
basket|panier|Korb|cesto|cesta|kosz|корзина|koš|かご|篮子|سبد
baskets|paniers|Körbe|cesti|cestas|kosze|корзины|koše|かご|篮子|سبدها
bathtub|baignoire|Badewanne|vasca da bagno|bañera|wanna|ванна|vana|浴槽|浴缸|وان
bazooka|bazooka|Bazooka|bazooka|bazuca|bazooka|базука|bazuka|バズーカ|巴祖卡|بازوکا
beach building|bâtiment de plage|Strandgebäude|edificio sulla spiaggia|edificio de playa|budynek plażowy|пляжное здание|plážová budova|海辺の建物|海滩建筑|ساختمان ساحلی
bed|lit|Bett|letto|cama|łóżko|кровать|postel|ベッド|床|تخت
beech|hêtre|Buche|faggio|haya|buk|бук|buk|ブナ|山毛榉|راش
beer|bière|Bier|birra|cerveza|piwo|пиво|pivo|ビール|啤酒|آبجو
beige|beige|beige|beige|beige|beżowy|бежевый|béžový|ベージュ|米色|بژ
bench|banc|Bank|panchina|banco|ławka|скамейка|lavička|ベンチ|长椅|نیمکت
bicycle|vélo|Fahrrad|bicicletta|bicicleta|rower|велосипед|kolo|自転車|自行车|دوچرخه
big|grand|groß|grande|grande|duży|большой|velký|大きな|大|بزرگ
big house|grande maison|großes Haus|casa grande|casa grande|duży dom|большой дом|velký dům|大きな家|大房子|خانهٔ بزرگ
big rock|gros rocher|großer Felsen|grande roccia|roca grande|duża skała|большая скала|velká skála|大岩|大岩石|صخرهٔ بزرگ
billhook|serpe|Hippe|roncola|podadera|kosa ogrodowa|садовый нож|žabka|鉈鎌|砍刀|داس باغبانی
birch|bouleau|Birke|betulla|abedul|brzoza|берёза|bříza|シラカバ|白桦|توس
block|bloc|Block|blocco|bloque|blok|блок|blok|ブロック|方块|بلوک
blue|bleu|blau|blu|azul|niebieski|синий|modrý|青|蓝色|آبی
body|carcasse|Karosserie|carcassa|carrocería|karoseria|кузов|karoserie|車体|车身|بدنه
bollard|borne|Poller|paletto|bolardo|słupek|тумба|patník|車止め|护柱|ستونک
bollards|bornes|Poller|paletti|bolardos|słupki|тумбы|patníky|車止め|护柱|ستونک‌ها
boots|bottes|Stiefel|stivali|botas|buty|сапоги|boty|ブーツ|靴子|چکمه‌ها
bourg|bourg|Marktflecken|borgo|villa|miasteczko|местечко|městys|町|集镇|شهرک
box|boîte|Kiste|scatola|caja|pudło|ящик|krabice|箱|箱子|جعبه
bread|pain|Brot|pane|pan|chleb|хлеб|chléb|パン|面包|نان
bread oven|four à pain|Backofen|forno per il pane|horno de pan|piec chlebowy|хлебная печь|pec na chléb|パン窯|面包炉|تنور نان
bricks|briques|Ziegel|mattoni|ladrillos|cegły|кирпичи|cihly|レンガ|砖块|آجرها
bridge|pont|Brücke|ponte|puente|most|мост|most|橋|桥|پل
bright|clair|hell|chiaro|claro|jasny|светлый|světlý|明るい|亮色|روشن
broken|cassé|kaputt|rotto|roto|zepsuty|сломанный|rozbitý|壊れた|破损|شکسته
broom|balai|Besen|scopa|escoba|miotła|метла|koště|ほうき|扫帚|جارو
brown|marron|braun|marrone|marrón|brązowy|коричневый|hnědý|茶色|棕色|قهوه‌ای
bucket|seau|Eimer|secchio|cubo|wiadro|ведро|kbelík|バケツ|水桶|سطل
building|bâtiment|Gebäude|edificio|edificio|budynek|здание|budova|建物|建筑|ساختمان
building piece|élément de bâtiment|Gebäudeteil|parte di edificio|pieza de edificio|element budynku|часть здания|díl budovy|建物の一部|建筑部件|قطعهٔ ساختمان
building with porch|bâtiment à porche|Gebäude mit Vordach|edificio con portico|edificio con porche|budynek z gankiem|здание с крыльцом|budova s verandou|ポーチ付きの建物|带门廊的建筑|ساختمان با ایوان
bundle of sticks|fagot|Reisigbündel|fascina|haz de leña|wiązka chrustu|вязанка хвороста|otep klestí|柴の束|柴捆|دستهٔ هیزم
bunker|bunker|Bunker|bunker|búnker|bunkier|бункер|bunkr|掩体壕|地堡|سنگر بتنی
bush|buisson|Busch|cespuglio|arbusto|krzak|куст|keř|茂み|灌木|بوته
cables|câbles|Kabel|cavi|cables|kable|кабели|kabely|ケーブル|电缆|کابل‌ها
café|café|Café|caffè|café|kawiarnia|кафе|kavárna|カフェ|咖啡馆|کافه
camel|chameau|Kamel|cammello|camello|wielbłąd|верблюд|velbloud|ラクダ|骆驼|شتر
camouflage|camouflage|Tarnung|mimetizzazione|camuflaje|kamuflaż|камуфляж|maskování|迷彩|伪装|استتار
can|bidon|Kanister|tanica|bidón|kanister|канистра|kanystr|缶|罐|حلب
cans|bidons|Kanister|taniche|bidones|kanistry|канистры|kanystry|缶|罐|حلب‌ها
canvas|bâche|Plane|telone|lona|plandeka|брезент|plachta|幌|帆布|برزنت
car|voiture|Auto|auto|coche|samochód|автомобиль|auto|自動車|汽车|خودرو
cargo|cargaison|Ladung|carico|carga|ładunek|груз|náklad|積荷|货物|محموله
carpet|tapis|Teppich|tappeto|alfombra|dywan|ковёр|koberec|絨毯|地毯|فرش
carriage|wagon|Waggon|vagone|vagón|wagon|вагон|vagon|客車|车厢|واگن
cart|charrette|Karren|carretto|carro|wóz|телега|vozík|荷車|手推车|گاری
castle|château|Burg|castello|castillo|zamek|замок|hrad|城|城堡|قلعه
cemetery|cimetière|Friedhof|cimitero|cementerio|cmentarz|кладбище|hřbitov|墓地|墓地|گورستان
chain|chaîne|Kette|catena|cadena|łańcuch|цепь|řetěz|鎖|链条|زنجیر
chair|chaise|Stuhl|sedia|silla|krzesło|стул|židle|椅子|椅子|صندلی
checkpoint|poste de contrôle|Kontrollpunkt|posto di blocco|puesto de control|punkt kontrolny|контрольно-пропускной пункт|kontrolní stanoviště|検問所|检查站|ایست بازرسی
chestnut tree|châtaignier|Kastanienbaum|castagno|castaño|kasztanowiec|каштан|kaštan|クリの木|栗树|درخت شاه‌بلوط
chili peppers|piments|Chilischoten|peperoncini|guindillas|papryczki chili|перец чили|chilli papričky|唐辛子|辣椒|فلفل تند
chimney|cheminée|Schornstein|camino|chimenea|komin|дымоход|komín|煙突|烟囱|دودکش
church|église|Kirche|chiesa|iglesia|kościół|церковь|kostel|教会|教堂|کلیسا
cloister|cloître|Kreuzgang|chiostro|claustro|krużganek|монастырский двор|ambit|回廊|回廊|رواق صومعه
closed|fermé|geschlossen|chiuso|cerrado|zamknięty|закрытый|zavřený|閉じた|关闭|بسته
coal hatch|trappe à charbon|Kohlenluke|botola del carbone|trampilla de carbón|właz na węgiel|угольный люк|uhelný poklop|石炭口|煤炭口|دریچهٔ زغال
coffee shop|café|Kaffeehaus|bar|cafetería|kawiarnia|кофейня|kavárna|喫茶店|咖啡店|قهوه‌خانه
collapsed|effondré|eingestürzt|crollato|derrumbado|zawalony|обрушенный|zřícený|崩れた|倒塌|فروریخته
colosseum|colisée|Kolosseum|colosseo|coliseo|koloseum|колизей|koloseum|コロッセオ|斗兽场|کولوسئوم
column|colonne|Säule|colonna|columna|kolumna|колонна|sloup|柱|柱子|ستون
command|commandement|Kommando|comando|mando|dowództwo|командование|velitelství|司令部|指挥部|فرماندهی
comms|transmissions|Fernmelde-|comunicazioni|comunicaciones|łączność|связь|spojovací|通信|通讯|مخابرات
concrete|béton|Beton|cemento|hormigón|betonowy|бетонный|betonový|コンクリート|混凝土|بتنی
concrete bollard|plot en béton|Betonpoller|blocco di cemento|bolardo de hormigón|betonowy słupek|бетонная тумба|betonový patník|コンクリート車止め|混凝土护柱|ستونک بتنی
convertible|cabriolet|Cabrio|decappottabile|descapotable|kabriolet|кабриолет|kabriolet|オープンカー|敞篷车|کروک
corner|angle|Ecke|angolo|esquina|narożnik|угол|roh|角|转角|گوشه
corridor|couloir|Gang|corridoio|pasillo|korytarz|коридор|chodba|通路|走廊|راهرو
cottage|chaumière|Häuschen|casetta|casita|chata|домик|chalupa|小屋|小屋|کلبه
cow|vache|Kuh|mucca|vaca|krowa|корова|kráva|牛|奶牛|گاو
cowshed|étable|Kuhstall|stalla|establo|obora|коровник|kravín|牛舎|牛棚|گاودانی
cowsheds|étables|Kuhställe|stalle|establos|obory|коровники|kravíny|牛舎|牛棚|گاودانی‌ها
crane|grue|Kran|gru|grúa|dźwig|кран|jeřáb|クレーン|起重机|جرثقیل
crate|caisse|Kiste|cassa|caja|skrzynia|ящик|bedna|木箱|板条箱|جعبهٔ چوبی
crates|caisses|Kisten|casse|cajas|skrzynie|ящики|bedny|木箱|板条箱|جعبه‌های چوبی
crop|culture|Feldfrucht|coltura|cultivo|uprawa|посев|plodina|作物|作物|محصول
crops|cultures|Feldfrüchte|colture|cultivos|uprawy|посевы|plodiny|作物|作物|محصولات
curved|courbe|gebogen|curvo|curvo|zakrzywiony|изогнутый|zakřivený|曲がった|弯曲|خمیده
cushion|coussin|Kissen|cuscino|cojín|poduszka|подушка|polštář|クッション|坐垫|کوسن
cut|coupé|geschnitten|tagliato|cortado|ścięty|срезанный|řezaný|切った|割下|بریده
cypress|cyprès|Zypresse|cipresso|ciprés|cyprys|кипарис|cypřiš|イトスギ|柏树|سرو
decoration|décoration|Dekoration|decorazione|decoración|dekoracja|украшение|dekorace|装飾|装饰|تزئین
defence|défense|Verteidigung|difesa|defensa|obrona|оборона|obrana|防御|防御|دفاع
depot|dépôt|Depot|deposito|depósito|skład|склад|sklad|倉庫|仓库|انبار
destroyed|détruit|zerstört|distrutto|destruido|zniszczony|разрушенный|zničený|破壊された|被毁|ویران
diesel|diesel|Diesel|diesel|diésel|diesel|дизель|nafta|ディーゼル|柴油|گازوئیل
dog|chien|Hund|cane|perro|pies|собака|pes|犬|狗|سگ
dome|dôme|Kuppel|cupola|cúpula|kopuła|купол|kupole|ドーム|圆顶|گنبد
door|porte|Tür|porta|puerta|drzwi|дверь|dveře|扉|门|در
dovecote|pigeonnier|Taubenschlag|colombaia|palomar|gołębnik|голубятня|holubník|鳩小屋|鸽舍|کبوترخانه
drinking trough|abreuvoir|Tränke|abbeveratoio|abrevadero|poidło|поилка|napajedlo|水飲み桶|饮水槽|آبشخور
dry|sec|trocken|secco|seco|suchy|сухой|suchý|枯れた|干枯|خشک
earth|terre|Erde|terra|tierra|ziemia|земля|hlína|土|泥土|خاک
edge|bord|Rand|bordo|borde|krawędź|край|okraj|縁|边缘|لبه
electric|électrique|elektrisch|elettrico|eléctrico|elektryczny|электрический|elektrický|電気|电力|برقی
elm|orme|Ulme|olmo|olmo|wiąz|вяз|jilm|ニレ|榆树|نارون
empty|vide|leer|vuoto|vacío|pusty|пустой|prázdný|空の|空|خالی
end|bout|Ende|estremità|extremo|koniec|конец|konec|端|末端|انتها
entrance|entrée|Eingang|ingresso|entrada|wejście|вход|vchod|入口|入口|ورودی
equipment|matériel|Ausrüstung|equipaggiamento|equipo|sprzęt|снаряжение|vybavení|装備|装备|تجهیزات
factory|usine|Fabrik|fabbrica|fábrica|fabryka|завод|továrna|工場|工厂|کارخانه
far|lointain|fern|lontano|lejano|daleki|дальний|vzdálený|遠景用|远景|دور
farm|ferme|Bauernhof|fattoria|granja|gospodarstwo|ферма|statek|農場|农场|مزرعه
farm building|bâtiment de ferme|Bauernhausgebäude|edificio agricolo|edificio de granja|budynek gospodarczy|хозяйственная постройка|hospodářská budova|農場の建物|农场建筑|ساختمان مزرعه
farm prop|objet de ferme|Hofgegenstand|oggetto agricolo|objeto de granja|przedmiot gospodarczy|сельский предмет|hospodářský předmět|農場の小物|农场道具|شیء مزرعه
farm tool|outil agricole|Ackergerät|attrezzo agricolo|herramienta agrícola|narzędzie rolnicze|сельхозинструмент|zemědělské nářadí|農具|农具|ابزار کشاورزی
fence|clôture|Zaun|recinzione|valla|płot|забор|plot|柵|栅栏|حصار
fence post|poteau de clôture|Zaunpfahl|palo di recinzione|poste de valla|słupek ogrodzenia|столб забора|plotový sloupek|柵の杭|栅栏柱|تیرک حصار
field|champ|Feld|campo|campo|pole|поле|pole|畑|田地|کشتزار
field-stone|pierre des champs|Feldstein|pietra di campo|piedra de campo|kamień polny|полевой камень|polní kámen|野石|田石|سنگ لاشه
fig tree|figuier|Feigenbaum|fico|higuera|figowiec|инжир|fíkovník|イチジクの木|无花果树|درخت انجیر
fir|sapin|Tanne|abete|abeto|jodła|пихта|jedle|モミ|冷杉|نراد
fire|feu|Feuer|fuoco|fuego|ogień|огонь|oheň|火|火|آتش
fire hydrant|bouche d'incendie|Hydrant|idrante|boca de incendios|hydrant|пожарный гидрант|hydrant|消火栓|消防栓|شیر آتش‌نشانی
fish|poisson|Fisch|pesce|pescado|ryba|рыба|ryba|魚|鱼|ماهی
fishing|pêche|Angel-|pesca|pesca|wędkarski|рыболовный|rybářský|釣り|钓鱼|ماهیگیری
fishing net|filet de pêche|Fischernetz|rete da pesca|red de pesca|sieć rybacka|рыболовная сеть|rybářská síť|漁網|渔网|تور ماهیگیری
flail|fléau|Dreschflegel|correggiato|mayal|cep|цеп|cep|からさお|连枷|خرمن‌کوب
flat|plat|flach|piatto|plano|płaski|плоский|plochý|平らな|平|صاف
flat-bed|plateau|Pritschen-|pianale|plataforma|platforma|бортовой|valník|平台|平板|کفی
flower|fleur|Blume|fiore|flor|kwiat|цветок|květina|花|花|گل
flower field|champ de fleurs|Blumenfeld|campo di fiori|campo de flores|pole kwiatów|цветочное поле|květinové pole|花畑|花田|کشتزار گل
flowers|fleurs|Blumen|fiori|flores|kwiaty|цветы|květiny|花|花|گل‌ها
folding|pliant|Klapp-|pieghevole|plegable|składany|складной|skládací|折りたたみ|折叠|تاشو
for|pour|für|per|para|dla|для|pro|用|用|برای
foundation|fondations|Fundament|fondamenta|cimientos|fundament|фундамент|základy|基礎|地基|پی
fountain|fontaine|Brunnen|fontana|fuente|fontanna|фонтан|fontána|噴水|喷泉|آب‌نما
fuel|carburant|Treibstoff|carburante|combustible|paliwo|топливо|palivo|燃料|燃料|سوخت
furniture|meubles|Möbel|mobili|muebles|meble|мебель|nábytek|家具|家具|مبلمان
gate|portail|Tor|cancello|portón|brama|ворота|brána|門|大门|دروازه
generator|groupe électrogène|Generator|generatore|generador|generator|генератор|generátor|発電機|发电机|ژنراتور
generic|générique|allgemein|generico|genérico|ogólny|обычный|obecný|汎用|通用|عمومی
German|allemand|deutsch|tedesco|alemán|niemiecki|немецкий|německý|ドイツの|德国|آلمانی
goat|chèvre|Ziege|capra|cabra|koza|коза|koza|ヤギ|山羊|بز
goods lift|monte-charge|Lastenaufzug|montacarichi|montacargas|winda towarowa|грузовой подъёмник|nákladní výtah|荷物用昇降機|货梯|بالابر بار
grass|herbe|Gras|erba|hierba|trawa|трава|tráva|草|草|علف
grasses|herbes|Gräser|erbe|hierbas|trawy|травы|trávy|草|草丛|علف‌ها
grave|tombe|Grab|tomba|tumba|grób|могила|hrob|墓|坟墓|قبر
green|vert|grün|verde|verde|zielony|зелёный|zelený|緑|绿色|سبز
green barrel|tonneau vert|grünes Fass|barile verde|barril verde|zielona beczka|зелёная бочка|zelený sud|緑の樽|绿色木桶|بشکهٔ سبز
green field|champ vert|grünes Feld|campo verde|campo verde|zielone pole|зелёное поле|zelené pole|緑の畑|绿色田地|کشتزار سبز
grey|gris|grau|grigio|gris|szary|серый|šedý|灰色|灰色|خاکستری
grille|grille|Gitter|griglia|reja|krata|решётка|mříž|格子|格栅|توری
ground|sol|Boden|terreno|suelo|grunt|грунт|půda|地面|地面|زمین
ground detail|détail de sol|Bodendetail|dettaglio del terreno|detalle de suelo|detal podłoża|деталь грунта|detail terénu|地面の細部|地面细节|جزئیات زمین
group|groupe|Gruppe|gruppo|grupo|grupa|группа|skupina|群|一组|گروه
gun|canon|Geschütz|cannone|cañón|działo|орудие|dělo|砲|火炮|توپ
half-timbered|à colombages|Fachwerk-|a graticcio|con entramado|szachulcowy|фахверковый|hrázděný|木骨造りの|半木结构|نیمه‌چوبی
hangar|hangar|Hangar|hangar|hangar|hangar|ангар|hangár|格納庫|机库|آشیانه
hanging|suspendu|hängend|appeso|colgante|wiszący|висячий|závěsný|吊り下げ|悬挂|آویزان
hanging drapes|draps suspendus|aufgehängte Tücher|teli appesi|telas colgadas|wiszące płachty|висящие полотна|zavěšené plachty|吊り布|悬挂布|پارچه‌های آویزان
hay|foin|Heu|fieno|heno|siano|сено|seno|干し草|干草|علف خشک
hay store|grenier à foin|Heuschober|fienile|pajar|szopa na siano|сеновал|seník|干し草置き場|干草棚|انبار علف خشک
haystack|meule de foin|Heuhaufen|pagliaio|pajar|stóg siana|стог сена|kupka sena|干し草の山|干草堆|کومهٔ علف خشک
head|tête|Kopf|testa|cabeza|głowa|голова|hlava|頭|头|سر
headquarters|quartier général|Hauptquartier|quartier generale|cuartel general|kwatera główna|штаб|velitelství|本部|总部|مقر فرماندهی
hedgehog|hérisson|Panzerigel|riccio cecoslovacco|erizo checo|jeż przeciwczołgowy|ёж|rozsocha|対戦車障害物|反坦克刺猬|خارپشت ضدتانک
helmet|casque|Helm|elmetto|casco|hełm|каска|helma|ヘルメット|头盔|کلاه‌خود
hen|poule|Huhn|gallina|gallina|kura|курица|slepice|ニワトリ|母鸡|مرغ
high|haut|hoch|alto|alto|wysoki|высокий|vysoký|高い|高|بلند
hornbeam|charme|Hainbuche|carpino|carpe|grab|граб|habr|シデ|鹅耳枥|ممرز
horse|cheval|Pferd|cavallo|caballo|koń|лошадь|kůň|馬|马|اسب
house|maison|Haus|casa|casa|dom|дом|dům|家|房屋|خانه
hut|cabane|Hütte|capanna|choza|chata|хижина|chatrč|小屋|棚屋|آلونک
in|dans|in|in|en|w|в|v|の中の|里的|در
infantry|infanterie|Infanterie|fanteria|infantería|piechota|пехота|pěchota|歩兵|步兵|پیاده‌نظام
intelligence|renseignement|Nachrichtendienst|servizi segreti|inteligencia|wywiad|разведка|rozvědka|情報部|情报|اطلاعات
jar|jarre|Krug|giara|tinaja|dzban|кувшин|džbán|かめ|坛子|خمره
jeep|jeep|Jeep|jeep|jeep|jeep|джип|džíp|ジープ|吉普车|جیپ
jerrycan|jerrican|Benzinkanister|tanica|bidón|kanister|канистра|kanystr|ジェリカン|油桶|گالن
jerrycans|jerricans|Benzinkanister|taniche|bidones|kanistry|канистры|kanystry|ジェリカン|油桶|گالن‌ها
kiosk|kiosque|Kiosk|chiosco|quiosco|kiosk|киоск|kiosek|キオスク|报亭|کیوسک
ladder|échelle|Leiter|scala|escalera de mano|drabina|лестница|žebřík|はしご|梯子|نردبان
lamp|lampe|Lampe|lampada|lámpara|lampa|лампа|lampa|ランプ|灯|چراغ
landmark|monument|Wahrzeichen|monumento|monumento|zabytek|достопримечательность|památka|名所|地标|بنای شاخص
lavender|lavande|Lavendel|lavanda|lavanda|lawenda|лаванда|levandule|ラベンダー|薰衣草|اسطوخودوس
leaf pile|tas de feuilles|Laubhaufen|mucchio di foglie|montón de hojas|sterta liści|куча листьев|hromada listí|落ち葉の山|落叶堆|تودهٔ برگ
leaves|feuilles|Blätter|foglie|hojas|liście|листья|listí|葉|树叶|برگ‌ها
left|gauche|links|sinistra|izquierda|lewy|левый|levý|左|左|چپ
lettuce|salade|Salat|lattuga|lechuga|sałata|салат|salát|レタス|生菜|کاهو
lid|couvercle|Deckel|coperchio|tapa|pokrywa|крышка|víko|ふた|盖子|درپوش
lid overturned|couvercle renversé|Deckel umgedreht|coperchio rovesciato|tapa volcada|pokrywa odwrócona|крышка перевёрнута|víko převrácené|ふたが裏返し|盖子翻倒|درپوش واژگون
light|léger|leicht|leggero|ligero|lekki|лёгкий|lehký|軽|轻型|سبک
lighthouse|phare|Leuchtturm|faro|faro|latarnia morska|маяк|maják|灯台|灯塔|فانوس دریایی
loaded|chargé|beladen|carico|cargado|załadowany|гружёный|naložený|積載した|满载|بارزده
logs|bûches|Holzscheite|tronchi|troncos|polana|брёвна|polena|丸太|原木|کنده‌ها
long|long|lang|lungo|largo|długi|длинный|dlouhý|長い|长|دراز
loom|métier à tisser|Webstuhl|telaio|telar|krosno|ткацкий станок|tkalcovský stav|織機|织布机|دستگاه بافندگی
low|bas|niedrig|basso|bajo|niski|низкий|nízký|低い|矮|کوتاه
low rock|rocher bas|niedriger Felsen|roccia bassa|roca baja|niska skała|низкая скала|nízká skála|低い岩|矮岩石|صخرهٔ کوتاه
low wall|muret|Mäuerchen|muretto|murete|murek|низкая стена|zídka|低い塀|矮墙|دیوار کوتاه
low wall A|muret A|Mäuerchen A|muretto A|murete A|murek A|низкая стена A|zídka A|低い塀A|矮墙A|دیوار کوتاه A
lying|couché|liegend|sdraiato|tumbado|leżący|лежащий|ležící|横たわった|躺着|خوابیده
machine|machine|Maschine|macchina|máquina|maszyna|машина|stroj|機械|机器|دستگاه
machine gun|mitrailleuse|Maschinengewehr|mitragliatrice|ametralladora|karabin maszynowy|пулемёт|kulomet|機関銃|机枪|مسلسل
manure|fumier|Mist|letame|estiércol|obornik|навоз|hnůj|堆肥|粪肥|کود
market|marché|Markt|mercato|mercado|targ|рынок|trh|市場|市场|بازار
marsh|marais|Sumpf|palude|pantano|bagno|болото|bažina|湿地|沼泽|مرداب
marsh grass|herbe de marais|Sumpfgras|erba di palude|hierba de pantano|trawa bagienna|болотная трава|bažinná tráva|湿地の草|沼泽草|علف مرداب
medical|médical|Sanitäts-|medico|médico|medyczny|медицинский|zdravotnický|医療|医疗|پزشکی
medium|moyen|mittel|medio|mediano|średni|средний|střední|中型|中型|متوسط
memorial|mémorial|Denkmal|memoriale|memorial|pomnik|мемориал|památník|記念碑|纪念碑|یادبود
metal|métallique|Metall-|metallico|metálico|metalowy|металлический|kovový|金属製|金属|فلزی
middle|milieu|Mitte|centro|centro|środek|середина|střed|中央|中间|میانه
milestone|borne kilométrique|Meilenstein|pietra miliare|mojón|kamień milowy|верстовой столб|milník|道標|里程碑|سنگ کیلومتر
military|militaire|militärisch|militare|militar|wojskowy|военный|vojenský|軍用|军用|نظامی
milk|lait|Milch|latte|leche|mleko|молоко|mléko|牛乳|牛奶|شیر
milk can|bidon de lait|Milchkanne|bidone del latte|lechera|bańka na mleko|бидон для молока|konev na mléko|牛乳缶|牛奶罐|ظرف شیر
mill|moulin|Mühle|mulino|molino|młyn|мельница|mlýn|風車小屋|磨坊|آسیاب
minaret|minaret|Minarett|minareto|minarete|minaret|минарет|minaret|ミナレット|宣礼塔|مناره
Monte Cassino|Mont-Cassin|Monte Cassino|Montecassino|Montecassino|Monte Cassino|Монте-Кассино|Monte Cassino|モンテ・カッシーノ|卡西诺山|مونته کاسینو
monument|monument|Monument|monumento|monumento|pomnik|памятник|pomník|記念物|纪念建筑|بنای تاریخی
Mount|mont|Berg|monte|monte|góra|гора|hora|山|山|کوه
mule|mulet|Maultier|mulo|mula|muł|мул|mula|ラバ|骡子|قاطر
music|musique|Musik|musica|música|muzyka|музыка|hudba|音楽|音乐|موسیقی
nailed|cloué|genagelt|inchiodato|clavado|przybity|прибитый|přibitý|釘打ちの|钉住的|میخ‌کوب‌شده
nest|nid|Nest|nido|nido|gniazdo|гнездо|hnízdo|陣地|巢|لانه
net|filet|Netz|rete|red|sieć|сеть|síť|網|网|تور
Normandy|Normandie|Normandie|Normandia|Normandía|Normandia|Нормандия|Normandie|ノルマンディー|诺曼底|نرماندی
oak|chêne|Eiche|quercia|roble|dąb|дуб|dub|オーク|橡树|بلوط
of|de|aus|di|de|z|из|z|の|的|از
oil|huile|Öl|olio|aceite|olej|масло|olej|油|油|روغن
old|vieux|alt|vecchio|viejo|stary|старый|starý|古い|旧|قدیمی
olive|olive|Olive|oliva|aceituna|oliwka|олива|oliva|オリーブ|橄榄|زیتون
olive tree|olivier|Olivenbaum|olivo|olivo|drzewo oliwne|оливковое дерево|olivovník|オリーブの木|橄榄树|درخت زیتون
olives|olives|Oliven|olive|aceitunas|oliwki|оливки|olivy|オリーブ|橄榄|زیتون‌ها
on|sur|auf|su|sobre|na|на|na|上の|上|روی
on the|sur le|auf dem|sul|sobre el|na|на|na|上の|上的|روی
open|ouvert|offen|aperto|abierto|otwarty|открытый|otevřený|開いた|打开|باز
orange|orange|orange|arancione|naranja|pomarańczowy|оранжевый|oranžový|オレンジ色|橙色|نارنجی
orange tree|oranger|Orangenbaum|arancio|naranjo|drzewo pomarańczowe|апельсиновое дерево|pomerančovník|オレンジの木|橙树|درخت پرتقال
oranges|oranges|Orangen|arance|naranjas|pomarańcze|апельсины|pomeranče|オレンジ|橙子|پرتقال‌ها
oven|four|Ofen|forno|horno|piec|печь|pec|窯|炉子|تنور
overturned|renversé|umgestürzt|rovesciato|volcado|przewrócony|опрокинутый|převrácený|ひっくり返った|翻倒|واژگون
pad|plateforme|Plattform|piazzola|plataforma|płyta|площадка|plošina|発着場|平台|سکو
palm|palmier|Palme|palma|palmera|palma|пальма|palma|ヤシ|棕榈|نخل
palms|palmiers|Palmen|palme|palmeras|palmy|пальмы|palmy|ヤシ|棕榈|نخل‌ها
papers|papiers|Papiere|carte|papeles|papiery|бумаги|papíry|書類|文件|کاغذها
parasol|parasol|Sonnenschirm|ombrellone|sombrilla|parasol|зонт|slunečník|パラソル|遮阳伞|چتر آفتابی
park|parc|Park|parco|parque|park|парк|park|公園|公园|پارک
part|partie|Teil|parte|parte|część|часть|část|部分|部分|قسمت
pebble|caillou|Kiesel|ciottolo|guijarro|kamyk|камень|oblázek|小石|卵石|سنگریزه
piece|morceau|Stück|pezzo|pieza|kawałek|кусок|kus|部品|部件|تکه
pig|cochon|Schwein|maiale|cerdo|świnia|свинья|prase|豚|猪|خوک
pigsty|porcherie|Schweinestall|porcile|pocilga|chlew|свинарник|chlívek|豚小屋|猪圈|خوکدانی
pile|tas|Haufen|mucchio|montón|sterta|куча|hromada|山|堆|توده
pile of planks|tas de planches|Bretterstapel|pila di assi|montón de tablas|sterta desek|штабель досок|hromada prken|板材の山|木板堆|تودهٔ تخته
pipe|tuyau|Rohr|tubo|tubería|rura|труба|trubka|パイプ|管道|لوله
pitchfork|fourche|Heugabel|forcone|horca|widły|вилы|vidle|干し草フォーク|干草叉|چنگک
plane|avion|Flugzeug|aereo|avión|samolot|самолёт|letadlo|飛行機|飞机|هواپیما
plank|planche|Brett|asse|tabla|deska|доска|prkno|板|木板|تخته
planks|planches|Bretter|assi|tablas|deski|доски|prkna|板|木板|تخته‌ها
plant|plante|Pflanze|pianta|planta|roślina|растение|rostlina|植物|植物|گیاه
planter|jardinière|Pflanzkübel|fioriera|jardinera|donica|кашпо|truhlík|プランター|花槽|جاگلدانی
plants|plantes|Pflanzen|piante|plantas|rośliny|растения|rostliny|植物|植物|گیاهان
plants on|plantes sur|Pflanzen auf|piante su|plantas sobre|rośliny na|растения на|rostliny na|植物・|植物在|گیاهان روی
plough|charrue|Pflug|aratro|arado|pług|плуг|pluh|すき|犁|گاوآهن
pontoon|ponton|Ponton|pontile|pontón|ponton|понтон|ponton|浮き桟橋|浮桥|پانتون
port|port|Hafen|porto|puerto|port|порт|přístav|港|港口|بندر
position|position|Stellung|postazione|posición|stanowisko|позиция|postavení|陣地|阵地|موضع
post|poteau|Pfosten|palo|poste|słup|столб|sloup|柱|柱|تیرک
pot|pot|Topf|vaso|maceta|doniczka|горшок|květináč|鉢|花盆|گلدان
power|électrique|Strom-|elettrico|eléctrico|energetyczny|электро-|elektrický|電力|电力|برق
press|pressoir|Presse|torchio|prensa|prasa|пресс|lis|圧搾機|压榨机|پرس
prickly|épineux|stachelig|spinoso|espinoso|kolczasty|колючий|ostnatý|とげのある|多刺|خاردار
prickly pear|figuier de Barbarie|Feigenkaktus|fico d'India|chumbera|opuncja|опунция|opuncie|ウチワサボテン|仙人掌|انجیر هندی
prop|objet|Gegenstand|oggetto|objeto|przedmiot|предмет|předmět|小物|道具|شیء
purple|violet|lila|viola|morado|fioletowy|фиолетовый|fialový|紫|紫色|بنفش
quay|quai|Kai|banchina|muelle|nabrzeże|причал|nábřeží|岸壁|码头|اسکله
rabbit hutch|clapier|Kaninchenstall|conigliera|conejera|klatka dla królików|крольчатник|králíkárna|ウサギ小屋|兔笼|لانهٔ خرگوش
radio|radio|Funk|radio|radio|radio|радио|rádio|無線|无线电|رادیو
rake|râteau|Rechen|rastrello|rastrillo|grabie|грабли|hrábě|熊手|耙子|شن‌کش
rampart|rempart|Wall|bastione|muralla|wał|вал|val|城壁|城墙|بارو
red|rouge|rot|rosso|rojo|czerwony|красный|červený|赤|红色|قرمز
reeds|roseaux|Schilf|canne|juncos|trzcina|тростник|rákos|アシ|芦苇|نی‌ها
research|recherche|Forschung|ricerca|investigación|badania|исследования|výzkum|研究|研究|تحقیق
rifle|fusil|Gewehr|fucile|fusil|karabin|винтовка|puška|小銃|步枪|تفنگ
right|droite|rechts|destra|derecha|prawy|правый|pravý|右|右|راست
river object|objet de rivière|Flussobjekt|oggetto fluviale|objeto de río|obiekt rzeczny|речной объект|říční objekt|川の物|河流物件|شیء رود
riverbank|berge|Flussufer|riva|ribera|brzeg rzeki|берег реки|břeh řeky|川岸|河岸|کنارهٔ رود
road|route|Straße|strada|carretera|droga|дорога|silnice|道路|道路|جاده
rock|rocher|Felsen|roccia|roca|skała|скала|skála|岩|岩石|صخره
rockery|rocaille|Steingarten|giardino roccioso|rocalla|skalniak|альпинарий|skalka|ロックガーデン|假山|باغچهٔ سنگی
rolled|roulé|gerollt|arrotolato|enrollado|zwinięty|свёрнутый|srolovaný|巻いた|卷起|لوله‌شده
roof|toit|Dach|tetto|tejado|dach|крыша|střecha|屋根|屋顶|بام
roofs|toits|Dächer|tetti|tejados|dachy|крыши|střechy|屋根|屋顶|بام‌ها
rope|corde|Seil|corda|cuerda|lina|верёвка|lano|ロープ|绳子|طناب
ropes|cordes|Seile|corde|cuerdas|liny|верёвки|lana|ロープ|绳子|طناب‌ها
rose bush|rosier|Rosenstrauch|rosaio|rosal|krzew róży|розовый куст|růžový keř|バラの茂み|玫瑰丛|بوتهٔ گل سرخ
round|rond|rund|rotondo|redondo|okrągły|круглый|kulatý|丸い|圆形|گرد
row|rangée|Reihe|fila|hilera|rząd|ряд|řada|列|一排|ردیف
rowing boat|barque|Ruderboot|barca a remi|bote de remos|łódź wiosłowa|гребная лодка|veslice|手漕ぎボート|划艇|قایق پارویی
rubbish|ordures|Müll|spazzatura|basura|śmieci|мусор|odpadky|ごみ|垃圾|زباله
rubble|gravats|Trümmer|macerie|escombros|gruz|обломки|suť|がれき|瓦砾|آوار
ruin|ruine|Ruine|rovina|ruina|ruina|руина|zřícenina|廃墟|废墟|ویرانه
ruins|ruines|Ruinen|rovine|ruinas|ruiny|руины|zříceniny|廃墟|废墟|ویرانه‌ها
run|course|Lauf|corsa|carrera|wybieg|выгул|výběh|囲い|围栏|آغل
sand|sable|Sand|sabbia|arena|piasek|песок|písek|砂|沙子|شن
sandbag|sac de sable|Sandsack|sacco di sabbia|saco terrero|worek z piaskiem|мешок с песком|pytel s pískem|土嚢|沙袋|کیسهٔ شن
scaffolding|échafaudage|Gerüst|impalcatura|andamio|rusztowanie|леса|lešení|足場|脚手架|داربست
scarecrow|épouvantail|Vogelscheuche|spaventapasseri|espantapájaros|strach na wróble|пугало|strašák|かかし|稻草人|مترسک
school|école|Schule|scuola|escuela|szkoła|школа|škola|学校|学校|مدرسه
scythe|faux|Sense|falce|guadaña|kosa|коса|kosa|大鎌|镰刀|داس
section|section|Abschnitt|sezione|sección|odcinek|секция|úsek|区画|区段|قطعه
set|ensemble|Satz|set|conjunto|zestaw|набор|sada|一式|一套|مجموعه
shade|ombrage|Schatten|ombra|sombra|cień|тень|stín|日よけ|遮荫|سایه‌بان
shed|abri|Schuppen|capanno|cobertizo|szopa|сарай|kůlna|物置|棚子|انباری
sheep|mouton|Schaf|pecora|oveja|owca|овца|ovce|羊|绵羊|گوسفند
sheets|draps|Laken|lenzuola|sábanas|prześcieradła|простыни|prostěradla|シーツ|床单|ملافه‌ها
shelter|abri|Unterstand|riparo|refugio|schron|укрытие|úkryt|避難所|掩蔽所|پناهگاه
shepherd|berger|Hirte|pastore|pastor|pasterz|пастух|pastýř|羊飼い|牧羊人|چوپان
shoemaker's|cordonnerie|Schuhmacherei|calzoleria|zapatería|szewc|сапожная мастерская|obuvnictví|靴屋|鞋匠铺|کفاشی
shop|boutique|Laden|negozio|tienda|sklep|магазин|obchod|店|商店|مغازه
shop front|devanture|Schaufenster|vetrina|escaparate|witryna|витрина|výloha|店先|店面|ویترین مغازه
shop sign|enseigne|Ladenschild|insegna|letrero|szyld|вывеска|vývěsní štít|看板|招牌|تابلوی مغازه
shovel|pelle|Schaufel|pala|pala|łopata|лопата|lopata|シャベル|铁锹|بیل
sign|panneau|Schild|cartello|señal|znak|знак|cedule|標識|标志|تابلو
silo|silo|Silo|silo|silo|silos|силос|silo|サイロ|筒仓|سیلو
siren|sirène|Sirene|sirena|sirena|syrena|сирена|siréna|サイレン|警报器|آژیر
small|petit|klein|piccolo|pequeño|mały|маленький|malý|小さな|小|کوچک
small building|petit bâtiment|kleines Gebäude|piccolo edificio|edificio pequeño|mały budynek|небольшое здание|malá budova|小さな建物|小型建筑|ساختمان کوچک
small house|petite maison|kleines Haus|casetta|casa pequeña|mały dom|маленький дом|malý dům|小さな家|小房子|خانهٔ کوچک
spice|épices|Gewürz-|spezie|especias|przypraw|пряностей|koření|香辛料|香料|ادویه
spice stall|étal d'épices|Gewürzstand|banco delle spezie|puesto de especias|stragan z przyprawami|лавка пряностей|stánek s kořením|香辛料の屋台|香料摊|دکهٔ ادویه
spices|épices|Gewürze|spezie|especias|przyprawy|пряности|koření|香辛料|香料|ادویه‌ها
spit roast|broche|Spießbraten|spiedo|asador|rożen|вертел|rožeň|丸焼き|烤架|سیخ کباب
spruce|épicéa|Fichte|abete rosso|pícea|świerk|ель|smrk|トウヒ|云杉|کاج نوئل
square|carré|quadratisch|quadrato|cuadrado|kwadratowy|квадратный|čtvercový|四角い|方形|چهارگوش
stable|écurie|Pferdestall|scuderia|cuadra|stajnia|конюшня|stáj|馬小屋|马厩|اصطبل
stacked|empilé|gestapelt|impilato|apilado|ułożony|сложенный|naskládaný|積み重ねた|堆叠|روی‌هم‌چیده
stairs|escalier|Treppe|scale|escaleras|schody|лестница|schody|階段|楼梯|پله‌ها
stake|piquet|Pfahl|paletto|estaca|pal|кол|kůl|杭|木桩|چوب‌میخ
stall|étal|Stand|bancarella|puesto|stragan|прилавок|stánek|屋台|摊位|دکه
stand|support|Ständer|supporto|soporte|stojak|стойка|stojan|台|支架|نگهدارنده
start|début|Anfang|inizio|inicio|początek|начало|začátek|始端|起点|آغاز
station|gare|Bahnhof|stazione|estación|stacja|станция|nádraží|駅|车站|ایستگاه
stem|tige|Stängel|stelo|tallo|łodyga|стебель|stonek|茎|茎|ساقه
stone|pierre|Stein|pietra|piedra|kamień|камень|kámen|石|石头|سنگ
stone wall|mur de pierre|Steinmauer|muro di pietra|muro de piedra|kamienny mur|каменная стена|kamenná zeď|石垣|石墙|دیوار سنگی
stones|pierres|Steine|pietre|piedras|kamienie|камни|kameny|石|石头|سنگ‌ها
stony field|champ de pierres|steiniges Feld|campo sassoso|campo pedregoso|kamieniste pole|каменистое поле|kamenité pole|石だらけの畑|石头田|کشتزار سنگلاخ
stool|tabouret|Hocker|sgabello|taburete|stołek|табурет|stolička|スツール|凳子|چهارپایه
stove|poêle|Herd|stufa|estufa|piecyk|печка|kamna|ストーブ|炉灶|اجاق
straight|droit|gerade|dritto|recto|prosty|прямой|rovný|まっすぐ|直|مستقیم
straw|paille|Stroh|paglia|paja|słoma|солома|sláma|わら|稻草|کاه
street lamp|lampadaire|Straßenlaterne|lampione|farola|latarnia uliczna|уличный фонарь|pouliční lampa|街灯|路灯|چراغ خیابان
stretched|tendu|gespannt|teso|tendido|naciągnięty|натянутый|napnutý|張った|拉伸|کشیده
stretcher|brancard|Trage|barella|camilla|nosze|носилки|nosítka|担架|担架|برانکارد
structure|structure|Bauwerk|struttura|estructura|konstrukcja|сооружение|stavba|構造物|结构|سازه
suitcase|valise|Koffer|valigia|maleta|walizka|чемодан|kufr|スーツケース|手提箱|چمدان
sun|soleil|Sonne|sole|sol|słońce|солнце|slunce|日|太阳|آفتاب
table|table|Tisch|tavolo|mesa|stół|стол|stůl|テーブル|桌子|میز
tall grass|herbe haute|hohes Gras|erba alta|hierba alta|wysoka trawa|высокая трава|vysoká tráva|背の高い草|高草|علف بلند
tank|char|Panzer|carro armato|tanque|czołg|танк|tank|戦車|坦克|تانک
tank factory|usine de chars|Panzerfabrik|fabbrica di carri armati|fábrica de tanques|fabryka czołgów|танковый завод|továrna na tanky|戦車工場|坦克工厂|کارخانهٔ تانک
tannery|tannerie|Gerberei|conceria|curtiduría|garbarnia|кожевня|koželužna|なめし革工場|制革厂|دباغ‌خانه
tea room|salon de thé|Teestube|sala da tè|salón de té|herbaciarnia|чайная|čajovna|喫茶室|茶室|چای‌خانه
tent|tente|Zelt|tenda|tienda de campaña|namiot|палатка|stan|テント|帐篷|چادر
tools|outils|Werkzeug|attrezzi|herramientas|narzędzia|инструменты|nářadí|道具|工具|ابزارها
tower|tour|Turm|torre|torre|wieża|башня|věž|塔|塔楼|برج
town|ville|Stadt|città|ciudad|miasto|город|město|町|城镇|شهر
town building|bâtiment de ville|Stadtgebäude|edificio cittadino|edificio urbano|budynek miejski|городское здание|městská budova|町の建物|城镇建筑|ساختمان شهری
town hall|mairie|Rathaus|municipio|ayuntamiento|ratusz|ратуша|radnice|役場|市政厅|شهرداری
town house|maison de ville|Stadthaus|casa di città|casa urbana|kamienica|городской дом|městský dům|町家|城镇房屋|خانهٔ شهری
town prop|objet de ville|Stadtgegenstand|oggetto cittadino|objeto urbano|przedmiot miejski|городской предмет|městský předmět|町の小物|城镇道具|شیء شهری
tractor|tracteur|Traktor|trattore|tractor|ciągnik|трактор|traktor|トラクター|拖拉机|تراکتور
trailer|remorque|Anhänger|rimorchio|remolque|przyczepa|прицеп|přívěs|トレーラー|拖车|یدک
tram|tramway|Straßenbahn|tram|tranvía|tramwaj|трамвай|tramvaj|路面電車|电车|تراموا
transformer|transformateur|Transformator|trasformatore|transformador|transformator|трансформатор|transformátor|変圧器|变压器|ترانسفورماتور
tree|arbre|Baum|albero|árbol|drzewo|дерево|strom|木|树|درخت
trees|arbres|Bäume|alberi|árboles|drzewa|деревья|stromy|木々|树木|درختان
tricycle|tricycle|Dreirad|triciclo|triciclo|trójkołowiec|трицикл|tříkolka|三輪車|三轮车|سه‌چرخه
tricycle, cream|tricycle, crème|Dreirad, creme|triciclo, crema|triciclo, crema|trójkołowiec, kremowy|трицикл, кремовый|tříkolka, krémová|三輪車、クリーム色|三轮车，奶油色|سه‌چرخه، کرم
tricycle, wine red|tricycle, bordeaux|Dreirad, weinrot|triciclo, bordeaux|triciclo, burdeos|trójkołowiec, bordowy|трицикл, бордовый|tříkolka, vínová|三輪車、ワインレッド|三轮车，酒红色|سه‌چرخه، زرشکی
truck|camion|Lastwagen|camion|camión|ciężarówka|грузовик|nákladní auto|トラック|卡车|کامیون
trunk|tronc|Stamm|tronco|tronco|pień|ствол|kmen|幹|树干|تنه
tub|bac|Wanne|tinozza|tina|balia|кадка|necky|たらい|木盆|تشت
tuna|thon|Thunfisch|tonno|atún|tuńczyk|тунец|tuňák|マグロ|金枪鱼|ماهی تن
type|type|Typ|tipo|tipo|typ|тип|typ|型|型|نوع
tyre|pneu|Reifen|pneumatico|neumático|opona|шина|pneumatika|タイヤ|轮胎|لاستیک
upper floor|étage|Obergeschoss|piano superiore|piso superior|piętro|верхний этаж|patro|上階|楼层|طبقهٔ بالا
upturned|retourné|umgedreht|capovolto|boca abajo|odwrócony|перевёрнутый|obrácený|逆さの|倒扣|وارونه
van|camionnette|Lieferwagen|furgone|furgoneta|furgonetka|фургон|dodávka|バン|厢式车|ون
vehicle|véhicule|Fahrzeug|veicolo|vehículo|pojazd|транспорт|vozidlo|車両|车辆|وسیلهٔ نقلیه
village|village|Dorf|villaggio|pueblo|wieś|деревня|vesnice|村|村庄|روستا
village building|bâtiment de village|Dorfgebäude|edificio di villaggio|edificio de pueblo|budynek wiejski|деревенское здание|vesnická budova|村の建物|村庄建筑|ساختمان روستایی
vine|vigne|Weinrebe|vite|vid|winorośl|виноградная лоза|vinná réva|ブドウの木|葡萄藤|تاک
vineyard|vignoble|Weinberg|vigneto|viñedo|winnica|виноградник|vinice|ブドウ畑|葡萄园|تاکستان
walkway|passerelle|Steg|passerella|pasarela|kładka|мостки|lávka|通路|走道|گذرگاه
wall|mur|Mauer|muro|muro|mur|стена|zeď|壁|墙|دیوار
warehouse|entrepôt|Lagerhaus|magazzino|almacén|magazyn|склад|skladiště|倉庫|仓库|انبار کالا
washing|linge|Wäsche|bucato|colada|pranie|бельё|prádlo|洗濯物|晾晒衣物|رخت‌های پهن‌شده
watchtower|mirador|Wachturm|torre di guardia|torre de vigilancia|wieża strażnicza|сторожевая вышка|strážní věž|監視塔|瞭望塔|برج دیدبانی
water|eau|Wasser|acqua|agua|woda|вода|voda|水|水|آب
water tower|château d'eau|Wasserturm|torre dell'acqua|depósito de agua|wieża ciśnień|водонапорная башня|vodárenská věž|給水塔|水塔|برج آب
watering can|arrosoir|Gießkanne|annaffiatoio|regadera|konewka|лейка|konev|じょうろ|洒水壶|آب‌پاش
weapons|armes|Waffen|armi|armas|broń|оружие|zbraně|武器|武器|سلاح‌ها
weaving|tissage|Weberei|tessitura|tejido|tkactwo|ткачество|tkaní|機織り|纺织|بافندگی
well|puits|Brunnen|pozzo|pozo|studnia|колодец|studna|井戸|水井|چاه
wheat|blé|Weizen|grano|trigo|pszenica|пшеница|pšenice|小麦|小麦|گندم
wheat field|champ de blé|Weizenfeld|campo di grano|campo de trigo|pole pszenicy|пшеничное поле|pšeničné pole|小麦畑|麦田|گندم‌زار
wheel|roue|Rad|ruota|rueda|koło|колесо|kolo|車輪|车轮|چرخ
wheelbarrow|brouette|Schubkarre|carriola|carretilla|taczka|тачка|kolečko|手押し車|独轮车|فرغون
white|blanc|weiß|bianco|blanco|biały|белый|bílý|白|白色|سفید
wicker|osier|Weide|vimini|mimbre|wiklina|ивовый|proutěný|柳細工|柳条|حصیری
wicker basket|panier en osier|Weidenkorb|cesto di vimini|cesta de mimbre|kosz wiklinowy|плетёная корзина|proutěný koš|柳のかご|柳条篮|سبد حصیری
wicker suitcase|valise en osier|Weidenkoffer|valigia di vimini|maleta de mimbre|walizka wiklinowa|плетёный чемодан|proutěný kufr|柳のスーツケース|柳条箱|چمدان حصیری
wind pump|éolienne|Windpumpe|pompa a vento|bomba de viento|wiatrak pompowy|ветряной насос|větrné čerpadlo|風車ポンプ|风力水泵|تلمبهٔ بادی
winter prop|objet d'hiver|Winterobjekt|oggetto invernale|objeto invernal|przedmiot zimowy|зимний предмет|zimní předmět|冬の小物|冬季道具|شیء زمستانی
wire|fil de fer|Draht|filo|alambre|drut|проволока|drát|鉄線|铁丝|سیم
with walkable deck|avec tablier praticable|mit begehbarer Fahrbahn|con impalcato percorribile|con tablero transitable|z przejezdnym pomostem|с проходимым настилом|s pojízdnou mostovkou|通行可能な床付き|带可通行桥面|با کفِ قابل عبور
without|sans|ohne|senza|sin|bez|без|bez|なし|无|بدون
wood|bois|Holz|legno|madera|drewno|дерево|dřevo|木材|木头|چوب
wooden|en bois|hölzern|di legno|de madera|drewniany|деревянный|dřevěný|木製|木制|چوبی
wooden barn|grange en bois|Holzscheune|fienile di legno|granero de madera|drewniana stodoła|деревянный амбар|dřevěná stodola|木の納屋|木谷仓|انبار چوبی
woodpile|tas de bois|Holzstapel|catasta di legna|pila de leña|stos drewna|поленница|hranice dřeva|薪の山|柴堆|تودهٔ هیزم
wreck|épave|Wrack|relitto|restos|wrak|остов|vrak|残骸|残骸|لاشه
yellow|jaune|gelb|giallo|amarillo|żółty|жёлтый|žlutý|黄|黄色|زرد
winter look|aspect hivernal|Winteroptik|aspetto invernale|aspecto invernal|wygląd zimowy|зимний вид|zimní vzhled|冬の見た目|冬季外观|ظاهر زمستانی
Ardennes|Ardennes|Ardennen|Ardenne|Ardenas|Ardeny|Арденны|Ardeny|アルデンヌ|阿登|آردن
Europe|Europe|Europa|Europa|Europa|Europa|Европа|Evropa|ヨーロッパ|欧洲|اروپا
France|France|Frankreich|Francia|Francia|Francja|Франция|Francie|フランス|法国|فرانسه
Germany|Allemagne|Deutschland|Germania|Alemania|Niemcy|Германия|Německo|ドイツ|德国|آلمان
Holland|Hollande|Holland|Olanda|Holanda|Holandia|Голландия|Holandsko|オランダ|荷兰|هلند
Italy|Italie|Italien|Italia|Italia|Włochy|Италия|Itálie|イタリア|意大利|ایتالیا
Tunisia|Tunisie|Tunesien|Tunisia|Túnez|Tunezja|Тунис|Tunisko|チュニジア|突尼斯|تونس
UK|Royaume-Uni|Großbritannien|Regno Unito|Reino Unido|Wielka Brytania|Великобритания|Velká Británie|イギリス|英国|بریتانیا
US|États-Unis|USA|Stati Uniti|EE. UU.|USA|США|USA|アメリカ|美国|آمریکا
USSR|URSS|UdSSR|URSS|URSS|ZSRR|СССР|SSSR|ソ連|苏联|شوروی
"""


def table() -> dict[str, dict[str, str]]:
    """{English word or phrase: {language: its words there}}."""
    out = {}
    for line in ROWS.strip().splitlines():
        cells = line.split("|")
        if len(cells) != 1 + len(LANGS):
            raise ValueError(f"scenerynames_lang: {line!r} has {len(cells)} cells, not {1 + len(LANGS)}")
        out[cells[0]] = dict(zip(LANGS, cells[1:]))
    return out
