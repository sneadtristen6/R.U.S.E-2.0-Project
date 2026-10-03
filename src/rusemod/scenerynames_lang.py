"""The words of rusemod.scenerynames' English names in the Studio's other nine languages (words.toml's codes). One row
per English word or phrase: en|fr|ger|ita|spa|pol|ru|cz|jpn|sc. A word with no row (a model or place name: Sherman,
Opel, Cherbourg...) stays as it is in every language. tests/test_scenerynames.py checks every English word the names
use has a row, or is one of KEPT."""

LANGS = ("fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc")

# names that read the same in every language
KEPT = {"Arnhem", "bis", "Blitz", "Cana", "Cassino", "Chaffee", "Cher", "Cherbourg", "Colditz", "Cromwell", "Djem",
        "Dovunque", "El", "Fiat", "GMC", "III", "IV", "Kasserine", "Kübelwagen", "Lee", "Matilda", "Monte", "Opel",
        "Panzer", "Pershing", "Sd.Kfz.", "Sherman", "Stuart", "Topolino", "Traction Avant", "Willys", "x", "Cotentin"}

ROWS = """
(Czech)|(tchèque)|(tschechisch)|(ceco)|(checo)|(czeski)|(чешский)|(český)|(チェコ式)|(捷克式)
(front-drive)|(traction avant)|(Frontantrieb)|(trazione anteriore)|(tracción delantera)|(przedni napęd)|(переднеприводный)|(přední pohon)|(前輪駆動)|(前驱)
administration|administration|Verwaltung|amministrazione|administración|administracja|администрация|správa|管理棟|行政楼
administrative|administratif|Verwaltungs-|amministrativo|administrativo|administracyjny|административный|správní|管理用|行政
adverts|affiches|Werbung|pubblicità|anuncios|reklamy|реклама|reklamy|広告|广告
ammunition|munitions|Munition|munizioni|munición|amunicja|боеприпасы|munice|弾薬|弹药
amphora|amphore|Amphore|anfora|ánfora|amfora|амфора|amfora|アンフォラ|双耳瓶
and|et|und|e|y|i|и|a|と|和
animal|animal|Tier|animale|animal|zwierzę|животное|zvíře|動物|动物
antenna|antenne|Antenne|antenna|antena|antena|антенна|anténa|アンテナ|天线
anti-aircraft|antiaérien|Flugabwehr|contraerea|antiaéreo|przeciwlotniczy|зенитный|protiletadlový|対空|防空
apple tree|pommier|Apfelbaum|melo|manzano|jabłoń|яблоня|jabloň|リンゴの木|苹果树
apples|pommes|Äpfel|mele|manzanas|jabłka|яблоки|jablka|リンゴ|苹果
apples on the|pommes sur|Äpfel auf|mele su|manzanas sobre|jabłka na|яблоки на|jablka na|リンゴ・|苹果在
arch|arche|Bogen|arco|arco|łuk|арка|oblouk|アーチ|拱门
arches|arches|Bögen|archi|arcos|łuki|арки|oblouky|アーチ群|拱门组
artillery|artillerie|Artillerie|artiglieria|artillería|artyleria|артиллерия|dělostřelectvo|砲兵|炮兵
asphalt|asphalte|Asphalt|asfalto|asfalto|asfalt|асфальт|asfalt|アスファルト|沥青
axe|hache|Axt|ascia|hacha|siekiera|топор|sekera|斧|斧头
bag|sac|Sack|sacco|saco|worek|мешок|pytel|袋|袋子
bags|sacs|Säcke|sacchi|sacos|worki|мешки|pytle|袋|袋子
bar|bar|Bar|bar|bar|bar|бар|bar|バー|酒吧
barbed wire|barbelés|Stacheldraht|filo spinato|alambre de espino|drut kolczasty|колючая проволока|ostnatý drát|有刺鉄線|铁丝网
bare|nu|kahl|spoglio|desnudo|nagi|голый|holý|裸の|光秃
barge|péniche|Lastkahn|chiatta|barcaza|barka|баржа|nákladní člun|はしけ|驳船
barn|grange|Scheune|fienile|granero|stodoła|амбар|stodola|納屋|谷仓
barracks|caserne|Kaserne|caserma|cuartel|koszary|казармы|kasárna|兵舎|兵营
barrel|tonneau|Fass|barile|barril|beczka|бочка|sud|樽|木桶
base|base|Basis|base|base|baza|основание|základna|土台|底座
basin|bassin|Becken|vasca|pila|basen|бассейн|nádrž|水盤|水池
basket|panier|Korb|cesto|cesta|kosz|корзина|koš|かご|篮子
baskets|paniers|Körbe|cesti|cestas|kosze|корзины|koše|かご|篮子
bathtub|baignoire|Badewanne|vasca da bagno|bañera|wanna|ванна|vana|浴槽|浴缸
bazooka|bazooka|Bazooka|bazooka|bazuca|bazooka|базука|bazuka|バズーカ|巴祖卡
beach building|bâtiment de plage|Strandgebäude|edificio sulla spiaggia|edificio de playa|budynek plażowy|пляжное здание|plážová budova|海辺の建物|海滩建筑
bed|lit|Bett|letto|cama|łóżko|кровать|postel|ベッド|床
beech|hêtre|Buche|faggio|haya|buk|бук|buk|ブナ|山毛榉
beer|bière|Bier|birra|cerveza|piwo|пиво|pivo|ビール|啤酒
beige|beige|beige|beige|beige|beżowy|бежевый|béžový|ベージュ|米色
bench|banc|Bank|panchina|banco|ławka|скамейка|lavička|ベンチ|长椅
bicycle|vélo|Fahrrad|bicicletta|bicicleta|rower|велосипед|kolo|自転車|自行车
big|grand|groß|grande|grande|duży|большой|velký|大きな|大
big house|grande maison|großes Haus|casa grande|casa grande|duży dom|большой дом|velký dům|大きな家|大房子
big rock|gros rocher|großer Felsen|grande roccia|roca grande|duża skała|большая скала|velká skála|大岩|大岩石
billhook|serpe|Hippe|roncola|podadera|kosa ogrodowa|садовый нож|žabka|鉈鎌|砍刀
birch|bouleau|Birke|betulla|abedul|brzoza|берёза|bříza|シラカバ|白桦
block|bloc|Block|blocco|bloque|blok|блок|blok|ブロック|方块
blue|bleu|blau|blu|azul|niebieski|синий|modrý|青|蓝色
body|carcasse|Karosserie|carcassa|carrocería|karoseria|кузов|karoserie|車体|车身
bollard|borne|Poller|paletto|bolardo|słupek|тумба|patník|車止め|护柱
bollards|bornes|Poller|paletti|bolardos|słupki|тумбы|patníky|車止め|护柱
boots|bottes|Stiefel|stivali|botas|buty|сапоги|boty|ブーツ|靴子
bourg|bourg|Marktflecken|borgo|villa|miasteczko|местечко|městys|町|集镇
box|boîte|Kiste|scatola|caja|pudło|ящик|krabice|箱|箱子
bread|pain|Brot|pane|pan|chleb|хлеб|chléb|パン|面包
bread oven|four à pain|Backofen|forno per il pane|horno de pan|piec chlebowy|хлебная печь|pec na chléb|パン窯|面包炉
bricks|briques|Ziegel|mattoni|ladrillos|cegły|кирпичи|cihly|レンガ|砖块
bridge|pont|Brücke|ponte|puente|most|мост|most|橋|桥
bright|clair|hell|chiaro|claro|jasny|светлый|světlý|明るい|亮色
broken|cassé|kaputt|rotto|roto|zepsuty|сломанный|rozbitý|壊れた|破损
broom|balai|Besen|scopa|escoba|miotła|метла|koště|ほうき|扫帚
brown|marron|braun|marrone|marrón|brązowy|коричневый|hnědý|茶色|棕色
bucket|seau|Eimer|secchio|cubo|wiadro|ведро|kbelík|バケツ|水桶
building|bâtiment|Gebäude|edificio|edificio|budynek|здание|budova|建物|建筑
building piece|élément de bâtiment|Gebäudeteil|parte di edificio|pieza de edificio|element budynku|часть здания|díl budovy|建物の一部|建筑部件
building with porch|bâtiment à porche|Gebäude mit Vordach|edificio con portico|edificio con porche|budynek z gankiem|здание с крыльцом|budova s verandou|ポーチ付きの建物|带门廊的建筑
bundle of sticks|fagot|Reisigbündel|fascina|haz de leña|wiązka chrustu|вязанка хвороста|otep klestí|柴の束|柴捆
bunker|bunker|Bunker|bunker|búnker|bunkier|бункер|bunkr|掩体壕|地堡
bush|buisson|Busch|cespuglio|arbusto|krzak|куст|keř|茂み|灌木
cables|câbles|Kabel|cavi|cables|kable|кабели|kabely|ケーブル|电缆
café|café|Café|caffè|café|kawiarnia|кафе|kavárna|カフェ|咖啡馆
camel|chameau|Kamel|cammello|camello|wielbłąd|верблюд|velbloud|ラクダ|骆驼
camouflage|camouflage|Tarnung|mimetizzazione|camuflaje|kamuflaż|камуфляж|maskování|迷彩|伪装
can|bidon|Kanister|tanica|bidón|kanister|канистра|kanystr|缶|罐
cans|bidons|Kanister|taniche|bidones|kanistry|канистры|kanystry|缶|罐
canvas|bâche|Plane|telone|lona|plandeka|брезент|plachta|幌|帆布
car|voiture|Auto|auto|coche|samochód|автомобиль|auto|自動車|汽车
cargo|cargaison|Ladung|carico|carga|ładunek|груз|náklad|積荷|货物
carpet|tapis|Teppich|tappeto|alfombra|dywan|ковёр|koberec|絨毯|地毯
carriage|wagon|Waggon|vagone|vagón|wagon|вагон|vagon|客車|车厢
cart|charrette|Karren|carretto|carro|wóz|телега|vozík|荷車|手推车
castle|château|Burg|castello|castillo|zamek|замок|hrad|城|城堡
cemetery|cimetière|Friedhof|cimitero|cementerio|cmentarz|кладбище|hřbitov|墓地|墓地
chain|chaîne|Kette|catena|cadena|łańcuch|цепь|řetěz|鎖|链条
chair|chaise|Stuhl|sedia|silla|krzesło|стул|židle|椅子|椅子
checkpoint|poste de contrôle|Kontrollpunkt|posto di blocco|puesto de control|punkt kontrolny|контрольно-пропускной пункт|kontrolní stanoviště|検問所|检查站
chestnut tree|châtaignier|Kastanienbaum|castagno|castaño|kasztanowiec|каштан|kaštan|クリの木|栗树
chili peppers|piments|Chilischoten|peperoncini|guindillas|papryczki chili|перец чили|chilli papričky|唐辛子|辣椒
chimney|cheminée|Schornstein|camino|chimenea|komin|дымоход|komín|煙突|烟囱
church|église|Kirche|chiesa|iglesia|kościół|церковь|kostel|教会|教堂
cloister|cloître|Kreuzgang|chiostro|claustro|krużganek|монастырский двор|ambit|回廊|回廊
closed|fermé|geschlossen|chiuso|cerrado|zamknięty|закрытый|zavřený|閉じた|关闭
coal hatch|trappe à charbon|Kohlenluke|botola del carbone|trampilla de carbón|właz na węgiel|угольный люк|uhelný poklop|石炭口|煤炭口
coffee shop|café|Kaffeehaus|bar|cafetería|kawiarnia|кофейня|kavárna|喫茶店|咖啡店
collapsed|effondré|eingestürzt|crollato|derrumbado|zawalony|обрушенный|zřícený|崩れた|倒塌
colosseum|colisée|Kolosseum|colosseo|coliseo|koloseum|колизей|koloseum|コロッセオ|斗兽场
column|colonne|Säule|colonna|columna|kolumna|колонна|sloup|柱|柱子
command|commandement|Kommando|comando|mando|dowództwo|командование|velitelství|司令部|指挥部
comms|transmissions|Fernmelde-|comunicazioni|comunicaciones|łączność|связь|spojovací|通信|通讯
concrete|béton|Beton|cemento|hormigón|betonowy|бетонный|betonový|コンクリート|混凝土
concrete bollard|plot en béton|Betonpoller|blocco di cemento|bolardo de hormigón|betonowy słupek|бетонная тумба|betonový patník|コンクリート車止め|混凝土护柱
convertible|cabriolet|Cabrio|decappottabile|descapotable|kabriolet|кабриолет|kabriolet|オープンカー|敞篷车
corner|angle|Ecke|angolo|esquina|narożnik|угол|roh|角|转角
corridor|couloir|Gang|corridoio|pasillo|korytarz|коридор|chodba|通路|走廊
cottage|chaumière|Häuschen|casetta|casita|chata|домик|chalupa|小屋|小屋
cow|vache|Kuh|mucca|vaca|krowa|корова|kráva|牛|奶牛
cowshed|étable|Kuhstall|stalla|establo|obora|коровник|kravín|牛舎|牛棚
cowsheds|étables|Kuhställe|stalle|establos|obory|коровники|kravíny|牛舎|牛棚
crane|grue|Kran|gru|grúa|dźwig|кран|jeřáb|クレーン|起重机
crate|caisse|Kiste|cassa|caja|skrzynia|ящик|bedna|木箱|板条箱
crates|caisses|Kisten|casse|cajas|skrzynie|ящики|bedny|木箱|板条箱
crop|culture|Feldfrucht|coltura|cultivo|uprawa|посев|plodina|作物|作物
crops|cultures|Feldfrüchte|colture|cultivos|uprawy|посевы|plodiny|作物|作物
curved|courbe|gebogen|curvo|curvo|zakrzywiony|изогнутый|zakřivený|曲がった|弯曲
cushion|coussin|Kissen|cuscino|cojín|poduszka|подушка|polštář|クッション|坐垫
cut|coupé|geschnitten|tagliato|cortado|ścięty|срезанный|řezaný|切った|割下
cypress|cyprès|Zypresse|cipresso|ciprés|cyprys|кипарис|cypřiš|イトスギ|柏树
decoration|décoration|Dekoration|decorazione|decoración|dekoracja|украшение|dekorace|装飾|装饰
defence|défense|Verteidigung|difesa|defensa|obrona|оборона|obrana|防御|防御
depot|dépôt|Depot|deposito|depósito|skład|склад|sklad|倉庫|仓库
destroyed|détruit|zerstört|distrutto|destruido|zniszczony|разрушенный|zničený|破壊された|被毁
diesel|diesel|Diesel|diesel|diésel|diesel|дизель|nafta|ディーゼル|柴油
dog|chien|Hund|cane|perro|pies|собака|pes|犬|狗
dome|dôme|Kuppel|cupola|cúpula|kopuła|купол|kupole|ドーム|圆顶
door|porte|Tür|porta|puerta|drzwi|дверь|dveře|扉|门
dovecote|pigeonnier|Taubenschlag|colombaia|palomar|gołębnik|голубятня|holubník|鳩小屋|鸽舍
drinking trough|abreuvoir|Tränke|abbeveratoio|abrevadero|poidło|поилка|napajedlo|水飲み桶|饮水槽
dry|sec|trocken|secco|seco|suchy|сухой|suchý|枯れた|干枯
earth|terre|Erde|terra|tierra|ziemia|земля|hlína|土|泥土
edge|bord|Rand|bordo|borde|krawędź|край|okraj|縁|边缘
electric|électrique|elektrisch|elettrico|eléctrico|elektryczny|электрический|elektrický|電気|电力
elm|orme|Ulme|olmo|olmo|wiąz|вяз|jilm|ニレ|榆树
empty|vide|leer|vuoto|vacío|pusty|пустой|prázdný|空の|空
end|bout|Ende|estremità|extremo|koniec|конец|konec|端|末端
entrance|entrée|Eingang|ingresso|entrada|wejście|вход|vchod|入口|入口
equipment|matériel|Ausrüstung|equipaggiamento|equipo|sprzęt|снаряжение|vybavení|装備|装备
factory|usine|Fabrik|fabbrica|fábrica|fabryka|завод|továrna|工場|工厂
far|lointain|fern|lontano|lejano|daleki|дальний|vzdálený|遠景用|远景
farm|ferme|Bauernhof|fattoria|granja|gospodarstwo|ферма|statek|農場|农场
farm building|bâtiment de ferme|Bauernhausgebäude|edificio agricolo|edificio de granja|budynek gospodarczy|хозяйственная постройка|hospodářská budova|農場の建物|农场建筑
farm prop|objet de ferme|Hofgegenstand|oggetto agricolo|objeto de granja|przedmiot gospodarczy|сельский предмет|hospodářský předmět|農場の小物|农场道具
farm tool|outil agricole|Ackergerät|attrezzo agricolo|herramienta agrícola|narzędzie rolnicze|сельхозинструмент|zemědělské nářadí|農具|农具
fence|clôture|Zaun|recinzione|valla|płot|забор|plot|柵|栅栏
fence post|poteau de clôture|Zaunpfahl|palo di recinzione|poste de valla|słupek ogrodzenia|столб забора|plotový sloupek|柵の杭|栅栏柱
field|champ|Feld|campo|campo|pole|поле|pole|畑|田地
field-stone|pierre des champs|Feldstein|pietra di campo|piedra de campo|kamień polny|полевой камень|polní kámen|野石|田石
fig tree|figuier|Feigenbaum|fico|higuera|figowiec|инжир|fíkovník|イチジクの木|无花果树
fir|sapin|Tanne|abete|abeto|jodła|пихта|jedle|モミ|冷杉
fire|feu|Feuer|fuoco|fuego|ogień|огонь|oheň|火|火
fire hydrant|bouche d'incendie|Hydrant|idrante|boca de incendios|hydrant|пожарный гидрант|hydrant|消火栓|消防栓
fish|poisson|Fisch|pesce|pescado|ryba|рыба|ryba|魚|鱼
fishing|pêche|Angel-|pesca|pesca|wędkarski|рыболовный|rybářský|釣り|钓鱼
fishing net|filet de pêche|Fischernetz|rete da pesca|red de pesca|sieć rybacka|рыболовная сеть|rybářská síť|漁網|渔网
flail|fléau|Dreschflegel|correggiato|mayal|cep|цеп|cep|からさお|连枷
flat|plat|flach|piatto|plano|płaski|плоский|plochý|平らな|平
flat-bed|plateau|Pritschen-|pianale|plataforma|platforma|бортовой|valník|平台|平板
flower|fleur|Blume|fiore|flor|kwiat|цветок|květina|花|花
flower field|champ de fleurs|Blumenfeld|campo di fiori|campo de flores|pole kwiatów|цветочное поле|květinové pole|花畑|花田
flowers|fleurs|Blumen|fiori|flores|kwiaty|цветы|květiny|花|花
folding|pliant|Klapp-|pieghevole|plegable|składany|складной|skládací|折りたたみ|折叠
for|pour|für|per|para|dla|для|pro|用|用
foundation|fondations|Fundament|fondamenta|cimientos|fundament|фундамент|základy|基礎|地基
fountain|fontaine|Brunnen|fontana|fuente|fontanna|фонтан|fontána|噴水|喷泉
fuel|carburant|Treibstoff|carburante|combustible|paliwo|топливо|palivo|燃料|燃料
furniture|meubles|Möbel|mobili|muebles|meble|мебель|nábytek|家具|家具
gate|portail|Tor|cancello|portón|brama|ворота|brána|門|大门
generator|groupe électrogène|Generator|generatore|generador|generator|генератор|generátor|発電機|发电机
generic|générique|allgemein|generico|genérico|ogólny|обычный|obecný|汎用|通用
German|allemand|deutsch|tedesco|alemán|niemiecki|немецкий|německý|ドイツの|德国
goat|chèvre|Ziege|capra|cabra|koza|коза|koza|ヤギ|山羊
goods lift|monte-charge|Lastenaufzug|montacarichi|montacargas|winda towarowa|грузовой подъёмник|nákladní výtah|荷物用昇降機|货梯
grass|herbe|Gras|erba|hierba|trawa|трава|tráva|草|草
grasses|herbes|Gräser|erbe|hierbas|trawy|травы|trávy|草|草丛
grave|tombe|Grab|tomba|tumba|grób|могила|hrob|墓|坟墓
green|vert|grün|verde|verde|zielony|зелёный|zelený|緑|绿色
green barrel|tonneau vert|grünes Fass|barile verde|barril verde|zielona beczka|зелёная бочка|zelený sud|緑の樽|绿色木桶
green field|champ vert|grünes Feld|campo verde|campo verde|zielone pole|зелёное поле|zelené pole|緑の畑|绿色田地
grey|gris|grau|grigio|gris|szary|серый|šedý|灰色|灰色
grille|grille|Gitter|griglia|reja|krata|решётка|mříž|格子|格栅
ground|sol|Boden|terreno|suelo|grunt|грунт|půda|地面|地面
ground detail|détail de sol|Bodendetail|dettaglio del terreno|detalle de suelo|detal podłoża|деталь грунта|detail terénu|地面の細部|地面细节
group|groupe|Gruppe|gruppo|grupo|grupa|группа|skupina|群|一组
gun|canon|Geschütz|cannone|cañón|działo|орудие|dělo|砲|火炮
half-timbered|à colombages|Fachwerk-|a graticcio|con entramado|szachulcowy|фахверковый|hrázděný|木骨造りの|半木结构
hangar|hangar|Hangar|hangar|hangar|hangar|ангар|hangár|格納庫|机库
hanging|suspendu|hängend|appeso|colgante|wiszący|висячий|závěsný|吊り下げ|悬挂
hanging drapes|draps suspendus|aufgehängte Tücher|teli appesi|telas colgadas|wiszące płachty|висящие полотна|zavěšené plachty|吊り布|悬挂布
hay|foin|Heu|fieno|heno|siano|сено|seno|干し草|干草
hay store|grenier à foin|Heuschober|fienile|pajar|szopa na siano|сеновал|seník|干し草置き場|干草棚
haystack|meule de foin|Heuhaufen|pagliaio|pajar|stóg siana|стог сена|kupka sena|干し草の山|干草堆
head|tête|Kopf|testa|cabeza|głowa|голова|hlava|頭|头
headquarters|quartier général|Hauptquartier|quartier generale|cuartel general|kwatera główna|штаб|velitelství|本部|总部
hedgehog|hérisson|Panzerigel|riccio cecoslovacco|erizo checo|jeż przeciwczołgowy|ёж|rozsocha|対戦車障害物|反坦克刺猬
helmet|casque|Helm|elmetto|casco|hełm|каска|helma|ヘルメット|头盔
hen|poule|Huhn|gallina|gallina|kura|курица|slepice|ニワトリ|母鸡
high|haut|hoch|alto|alto|wysoki|высокий|vysoký|高い|高
hornbeam|charme|Hainbuche|carpino|carpe|grab|граб|habr|シデ|鹅耳枥
horse|cheval|Pferd|cavallo|caballo|koń|лошадь|kůň|馬|马
house|maison|Haus|casa|casa|dom|дом|dům|家|房屋
hut|cabane|Hütte|capanna|choza|chata|хижина|chatrč|小屋|棚屋
in|dans|in|in|en|w|в|v|の中の|里的
infantry|infanterie|Infanterie|fanteria|infantería|piechota|пехота|pěchota|歩兵|步兵
intelligence|renseignement|Nachrichtendienst|servizi segreti|inteligencia|wywiad|разведка|rozvědka|情報部|情报
jar|jarre|Krug|giara|tinaja|dzban|кувшин|džbán|かめ|坛子
jeep|jeep|Jeep|jeep|jeep|jeep|джип|džíp|ジープ|吉普车
jerrycan|jerrican|Benzinkanister|tanica|bidón|kanister|канистра|kanystr|ジェリカン|油桶
jerrycans|jerricans|Benzinkanister|taniche|bidones|kanistry|канистры|kanystry|ジェリカン|油桶
kiosk|kiosque|Kiosk|chiosco|quiosco|kiosk|киоск|kiosek|キオスク|报亭
ladder|échelle|Leiter|scala|escalera de mano|drabina|лестница|žebřík|はしご|梯子
lamp|lampe|Lampe|lampada|lámpara|lampa|лампа|lampa|ランプ|灯
landmark|monument|Wahrzeichen|monumento|monumento|zabytek|достопримечательность|památka|名所|地标
lavender|lavande|Lavendel|lavanda|lavanda|lawenda|лаванда|levandule|ラベンダー|薰衣草
leaf pile|tas de feuilles|Laubhaufen|mucchio di foglie|montón de hojas|sterta liści|куча листьев|hromada listí|落ち葉の山|落叶堆
leaves|feuilles|Blätter|foglie|hojas|liście|листья|listí|葉|树叶
left|gauche|links|sinistra|izquierda|lewy|левый|levý|左|左
lettuce|salade|Salat|lattuga|lechuga|sałata|салат|salát|レタス|生菜
lid|couvercle|Deckel|coperchio|tapa|pokrywa|крышка|víko|ふた|盖子
lid overturned|couvercle renversé|Deckel umgedreht|coperchio rovesciato|tapa volcada|pokrywa odwrócona|крышка перевёрнута|víko převrácené|ふたが裏返し|盖子翻倒
light|léger|leicht|leggero|ligero|lekki|лёгкий|lehký|軽|轻型
lighthouse|phare|Leuchtturm|faro|faro|latarnia morska|маяк|maják|灯台|灯塔
loaded|chargé|beladen|carico|cargado|załadowany|гружёный|naložený|積載した|满载
logs|bûches|Holzscheite|tronchi|troncos|polana|брёвна|polena|丸太|原木
long|long|lang|lungo|largo|długi|длинный|dlouhý|長い|长
loom|métier à tisser|Webstuhl|telaio|telar|krosno|ткацкий станок|tkalcovský stav|織機|织布机
low|bas|niedrig|basso|bajo|niski|низкий|nízký|低い|矮
low rock|rocher bas|niedriger Felsen|roccia bassa|roca baja|niska skała|низкая скала|nízká skála|低い岩|矮岩石
low wall|muret|Mäuerchen|muretto|murete|murek|низкая стена|zídka|低い塀|矮墙
low wall A|muret A|Mäuerchen A|muretto A|murete A|murek A|низкая стена A|zídka A|低い塀A|矮墙A
lying|couché|liegend|sdraiato|tumbado|leżący|лежащий|ležící|横たわった|躺着
machine|machine|Maschine|macchina|máquina|maszyna|машина|stroj|機械|机器
machine gun|mitrailleuse|Maschinengewehr|mitragliatrice|ametralladora|karabin maszynowy|пулемёт|kulomet|機関銃|机枪
manure|fumier|Mist|letame|estiércol|obornik|навоз|hnůj|堆肥|粪肥
market|marché|Markt|mercato|mercado|targ|рынок|trh|市場|市场
marsh|marais|Sumpf|palude|pantano|bagno|болото|bažina|湿地|沼泽
marsh grass|herbe de marais|Sumpfgras|erba di palude|hierba de pantano|trawa bagienna|болотная трава|bažinná tráva|湿地の草|沼泽草
medical|médical|Sanitäts-|medico|médico|medyczny|медицинский|zdravotnický|医療|医疗
medium|moyen|mittel|medio|mediano|średni|средний|střední|中型|中型
memorial|mémorial|Denkmal|memoriale|memorial|pomnik|мемориал|památník|記念碑|纪念碑
metal|métallique|Metall-|metallico|metálico|metalowy|металлический|kovový|金属製|金属
middle|milieu|Mitte|centro|centro|środek|середина|střed|中央|中间
milestone|borne kilométrique|Meilenstein|pietra miliare|mojón|kamień milowy|верстовой столб|milník|道標|里程碑
military|militaire|militärisch|militare|militar|wojskowy|военный|vojenský|軍用|军用
milk|lait|Milch|latte|leche|mleko|молоко|mléko|牛乳|牛奶
milk can|bidon de lait|Milchkanne|bidone del latte|lechera|bańka na mleko|бидон для молока|konev na mléko|牛乳缶|牛奶罐
mill|moulin|Mühle|mulino|molino|młyn|мельница|mlýn|風車小屋|磨坊
minaret|minaret|Minarett|minareto|minarete|minaret|минарет|minaret|ミナレット|宣礼塔
Monte Cassino|Mont-Cassin|Monte Cassino|Montecassino|Montecassino|Monte Cassino|Монте-Кассино|Monte Cassino|モンテ・カッシーノ|卡西诺山
monument|monument|Monument|monumento|monumento|pomnik|памятник|pomník|記念物|纪念建筑
Mount|mont|Berg|monte|monte|góra|гора|hora|山|山
mule|mulet|Maultier|mulo|mula|muł|мул|mula|ラバ|骡子
music|musique|Musik|musica|música|muzyka|музыка|hudba|音楽|音乐
nailed|cloué|genagelt|inchiodato|clavado|przybity|прибитый|přibitý|釘打ちの|钉住的
nest|nid|Nest|nido|nido|gniazdo|гнездо|hnízdo|陣地|巢
net|filet|Netz|rete|red|sieć|сеть|síť|網|网
Normandy|Normandie|Normandie|Normandia|Normandía|Normandia|Нормандия|Normandie|ノルマンディー|诺曼底
oak|chêne|Eiche|quercia|roble|dąb|дуб|dub|オーク|橡树
of|de|aus|di|de|z|из|z|の|的
oil|huile|Öl|olio|aceite|olej|масло|olej|油|油
old|vieux|alt|vecchio|viejo|stary|старый|starý|古い|旧
olive|olive|Olive|oliva|aceituna|oliwka|олива|oliva|オリーブ|橄榄
olive tree|olivier|Olivenbaum|olivo|olivo|drzewo oliwne|оливковое дерево|olivovník|オリーブの木|橄榄树
olives|olives|Oliven|olive|aceitunas|oliwki|оливки|olivy|オリーブ|橄榄
on|sur|auf|su|sobre|na|на|na|上の|上
on the|sur le|auf dem|sul|sobre el|na|на|na|上の|上的
open|ouvert|offen|aperto|abierto|otwarty|открытый|otevřený|開いた|打开
orange|orange|orange|arancione|naranja|pomarańczowy|оранжевый|oranžový|オレンジ色|橙色
orange tree|oranger|Orangenbaum|arancio|naranjo|drzewo pomarańczowe|апельсиновое дерево|pomerančovník|オレンジの木|橙树
oranges|oranges|Orangen|arance|naranjas|pomarańcze|апельсины|pomeranče|オレンジ|橙子
oven|four|Ofen|forno|horno|piec|печь|pec|窯|炉子
overturned|renversé|umgestürzt|rovesciato|volcado|przewrócony|опрокинутый|převrácený|ひっくり返った|翻倒
pad|plateforme|Plattform|piazzola|plataforma|płyta|площадка|plošina|発着場|平台
palm|palmier|Palme|palma|palmera|palma|пальма|palma|ヤシ|棕榈
palms|palmiers|Palmen|palme|palmeras|palmy|пальмы|palmy|ヤシ|棕榈
papers|papiers|Papiere|carte|papeles|papiery|бумаги|papíry|書類|文件
parasol|parasol|Sonnenschirm|ombrellone|sombrilla|parasol|зонт|slunečník|パラソル|遮阳伞
park|parc|Park|parco|parque|park|парк|park|公園|公园
part|partie|Teil|parte|parte|część|часть|část|部分|部分
pebble|caillou|Kiesel|ciottolo|guijarro|kamyk|камень|oblázek|小石|卵石
piece|morceau|Stück|pezzo|pieza|kawałek|кусок|kus|部品|部件
pig|cochon|Schwein|maiale|cerdo|świnia|свинья|prase|豚|猪
pigsty|porcherie|Schweinestall|porcile|pocilga|chlew|свинарник|chlívek|豚小屋|猪圈
pile|tas|Haufen|mucchio|montón|sterta|куча|hromada|山|堆
pile of planks|tas de planches|Bretterstapel|pila di assi|montón de tablas|sterta desek|штабель досок|hromada prken|板材の山|木板堆
pipe|tuyau|Rohr|tubo|tubería|rura|труба|trubka|パイプ|管道
pitchfork|fourche|Heugabel|forcone|horca|widły|вилы|vidle|干し草フォーク|干草叉
plane|avion|Flugzeug|aereo|avión|samolot|самолёт|letadlo|飛行機|飞机
plank|planche|Brett|asse|tabla|deska|доска|prkno|板|木板
planks|planches|Bretter|assi|tablas|deski|доски|prkna|板|木板
plant|plante|Pflanze|pianta|planta|roślina|растение|rostlina|植物|植物
planter|jardinière|Pflanzkübel|fioriera|jardinera|donica|кашпо|truhlík|プランター|花槽
plants|plantes|Pflanzen|piante|plantas|rośliny|растения|rostliny|植物|植物
plants on|plantes sur|Pflanzen auf|piante su|plantas sobre|rośliny na|растения на|rostliny na|植物・|植物在
plough|charrue|Pflug|aratro|arado|pług|плуг|pluh|すき|犁
pontoon|ponton|Ponton|pontile|pontón|ponton|понтон|ponton|浮き桟橋|浮桥
port|port|Hafen|porto|puerto|port|порт|přístav|港|港口
position|position|Stellung|postazione|posición|stanowisko|позиция|postavení|陣地|阵地
post|poteau|Pfosten|palo|poste|słup|столб|sloup|柱|柱
pot|pot|Topf|vaso|maceta|doniczka|горшок|květináč|鉢|花盆
power|électrique|Strom-|elettrico|eléctrico|energetyczny|электро-|elektrický|電力|电力
press|pressoir|Presse|torchio|prensa|prasa|пресс|lis|圧搾機|压榨机
prickly|épineux|stachelig|spinoso|espinoso|kolczasty|колючий|ostnatý|とげのある|多刺
prickly pear|figuier de Barbarie|Feigenkaktus|fico d'India|chumbera|opuncja|опунция|opuncie|ウチワサボテン|仙人掌
prop|objet|Gegenstand|oggetto|objeto|przedmiot|предмет|předmět|小物|道具
purple|violet|lila|viola|morado|fioletowy|фиолетовый|fialový|紫|紫色
quay|quai|Kai|banchina|muelle|nabrzeże|причал|nábřeží|岸壁|码头
rabbit hutch|clapier|Kaninchenstall|conigliera|conejera|klatka dla królików|крольчатник|králíkárna|ウサギ小屋|兔笼
radio|radio|Funk|radio|radio|radio|радио|rádio|無線|无线电
rake|râteau|Rechen|rastrello|rastrillo|grabie|грабли|hrábě|熊手|耙子
rampart|rempart|Wall|bastione|muralla|wał|вал|val|城壁|城墙
red|rouge|rot|rosso|rojo|czerwony|красный|červený|赤|红色
reeds|roseaux|Schilf|canne|juncos|trzcina|тростник|rákos|アシ|芦苇
research|recherche|Forschung|ricerca|investigación|badania|исследования|výzkum|研究|研究
rifle|fusil|Gewehr|fucile|fusil|karabin|винтовка|puška|小銃|步枪
right|droite|rechts|destra|derecha|prawy|правый|pravý|右|右
river object|objet de rivière|Flussobjekt|oggetto fluviale|objeto de río|obiekt rzeczny|речной объект|říční objekt|川の物|河流物件
riverbank|berge|Flussufer|riva|ribera|brzeg rzeki|берег реки|břeh řeky|川岸|河岸
road|route|Straße|strada|carretera|droga|дорога|silnice|道路|道路
rock|rocher|Felsen|roccia|roca|skała|скала|skála|岩|岩石
rockery|rocaille|Steingarten|giardino roccioso|rocalla|skalniak|альпинарий|skalka|ロックガーデン|假山
rolled|roulé|gerollt|arrotolato|enrollado|zwinięty|свёрнутый|srolovaný|巻いた|卷起
roof|toit|Dach|tetto|tejado|dach|крыша|střecha|屋根|屋顶
roofs|toits|Dächer|tetti|tejados|dachy|крыши|střechy|屋根|屋顶
rope|corde|Seil|corda|cuerda|lina|верёвка|lano|ロープ|绳子
ropes|cordes|Seile|corde|cuerdas|liny|верёвки|lana|ロープ|绳子
rose bush|rosier|Rosenstrauch|rosaio|rosal|krzew róży|розовый куст|růžový keř|バラの茂み|玫瑰丛
round|rond|rund|rotondo|redondo|okrągły|круглый|kulatý|丸い|圆形
row|rangée|Reihe|fila|hilera|rząd|ряд|řada|列|一排
rowing boat|barque|Ruderboot|barca a remi|bote de remos|łódź wiosłowa|гребная лодка|veslice|手漕ぎボート|划艇
rubbish|ordures|Müll|spazzatura|basura|śmieci|мусор|odpadky|ごみ|垃圾
rubble|gravats|Trümmer|macerie|escombros|gruz|обломки|suť|がれき|瓦砾
ruin|ruine|Ruine|rovina|ruina|ruina|руина|zřícenina|廃墟|废墟
ruins|ruines|Ruinen|rovine|ruinas|ruiny|руины|zříceniny|廃墟|废墟
run|course|Lauf|corsa|carrera|wybieg|выгул|výběh|囲い|围栏
sand|sable|Sand|sabbia|arena|piasek|песок|písek|砂|沙子
sandbag|sac de sable|Sandsack|sacco di sabbia|saco terrero|worek z piaskiem|мешок с песком|pytel s pískem|土嚢|沙袋
scaffolding|échafaudage|Gerüst|impalcatura|andamio|rusztowanie|леса|lešení|足場|脚手架
scarecrow|épouvantail|Vogelscheuche|spaventapasseri|espantapájaros|strach na wróble|пугало|strašák|かかし|稻草人
school|école|Schule|scuola|escuela|szkoła|школа|škola|学校|学校
scythe|faux|Sense|falce|guadaña|kosa|коса|kosa|大鎌|镰刀
section|section|Abschnitt|sezione|sección|odcinek|секция|úsek|区画|区段
set|ensemble|Satz|set|conjunto|zestaw|набор|sada|一式|一套
shade|ombrage|Schatten|ombra|sombra|cień|тень|stín|日よけ|遮荫
shed|abri|Schuppen|capanno|cobertizo|szopa|сарай|kůlna|物置|棚子
sheep|mouton|Schaf|pecora|oveja|owca|овца|ovce|羊|绵羊
sheets|draps|Laken|lenzuola|sábanas|prześcieradła|простыни|prostěradla|シーツ|床单
shelter|abri|Unterstand|riparo|refugio|schron|укрытие|úkryt|避難所|掩蔽所
shepherd|berger|Hirte|pastore|pastor|pasterz|пастух|pastýř|羊飼い|牧羊人
shoemaker's|cordonnerie|Schuhmacherei|calzoleria|zapatería|szewc|сапожная мастерская|obuvnictví|靴屋|鞋匠铺
shop|boutique|Laden|negozio|tienda|sklep|магазин|obchod|店|商店
shop front|devanture|Schaufenster|vetrina|escaparate|witryna|витрина|výloha|店先|店面
shop sign|enseigne|Ladenschild|insegna|letrero|szyld|вывеска|vývěsní štít|看板|招牌
shovel|pelle|Schaufel|pala|pala|łopata|лопата|lopata|シャベル|铁锹
sign|panneau|Schild|cartello|señal|znak|знак|cedule|標識|标志
silo|silo|Silo|silo|silo|silos|силос|silo|サイロ|筒仓
siren|sirène|Sirene|sirena|sirena|syrena|сирена|siréna|サイレン|警报器
small|petit|klein|piccolo|pequeño|mały|маленький|malý|小さな|小
small building|petit bâtiment|kleines Gebäude|piccolo edificio|edificio pequeño|mały budynek|небольшое здание|malá budova|小さな建物|小型建筑
small house|petite maison|kleines Haus|casetta|casa pequeña|mały dom|маленький дом|malý dům|小さな家|小房子
spice|épices|Gewürz-|spezie|especias|przypraw|пряностей|koření|香辛料|香料
spice stall|étal d'épices|Gewürzstand|banco delle spezie|puesto de especias|stragan z przyprawami|лавка пряностей|stánek s kořením|香辛料の屋台|香料摊
spices|épices|Gewürze|spezie|especias|przyprawy|пряности|koření|香辛料|香料
spit roast|broche|Spießbraten|spiedo|asador|rożen|вертел|rožeň|丸焼き|烤架
spruce|épicéa|Fichte|abete rosso|pícea|świerk|ель|smrk|トウヒ|云杉
square|carré|quadratisch|quadrato|cuadrado|kwadratowy|квадратный|čtvercový|四角い|方形
stable|écurie|Pferdestall|scuderia|cuadra|stajnia|конюшня|stáj|馬小屋|马厩
stacked|empilé|gestapelt|impilato|apilado|ułożony|сложенный|naskládaný|積み重ねた|堆叠
stairs|escalier|Treppe|scale|escaleras|schody|лестница|schody|階段|楼梯
stake|piquet|Pfahl|paletto|estaca|pal|кол|kůl|杭|木桩
stall|étal|Stand|bancarella|puesto|stragan|прилавок|stánek|屋台|摊位
stand|support|Ständer|supporto|soporte|stojak|стойка|stojan|台|支架
start|début|Anfang|inizio|inicio|początek|начало|začátek|始端|起点
station|gare|Bahnhof|stazione|estación|stacja|станция|nádraží|駅|车站
stem|tige|Stängel|stelo|tallo|łodyga|стебель|stonek|茎|茎
stone|pierre|Stein|pietra|piedra|kamień|камень|kámen|石|石头
stone wall|mur de pierre|Steinmauer|muro di pietra|muro de piedra|kamienny mur|каменная стена|kamenná zeď|石垣|石墙
stones|pierres|Steine|pietre|piedras|kamienie|камни|kameny|石|石头
stony field|champ de pierres|steiniges Feld|campo sassoso|campo pedregoso|kamieniste pole|каменистое поле|kamenité pole|石だらけの畑|石头田
stool|tabouret|Hocker|sgabello|taburete|stołek|табурет|stolička|スツール|凳子
stove|poêle|Herd|stufa|estufa|piecyk|печка|kamna|ストーブ|炉灶
straight|droit|gerade|dritto|recto|prosty|прямой|rovný|まっすぐ|直
straw|paille|Stroh|paglia|paja|słoma|солома|sláma|わら|稻草
street lamp|lampadaire|Straßenlaterne|lampione|farola|latarnia uliczna|уличный фонарь|pouliční lampa|街灯|路灯
stretched|tendu|gespannt|teso|tendido|naciągnięty|натянутый|napnutý|張った|拉伸
stretcher|brancard|Trage|barella|camilla|nosze|носилки|nosítka|担架|担架
structure|structure|Bauwerk|struttura|estructura|konstrukcja|сооружение|stavba|構造物|结构
suitcase|valise|Koffer|valigia|maleta|walizka|чемодан|kufr|スーツケース|手提箱
sun|soleil|Sonne|sole|sol|słońce|солнце|slunce|日|太阳
table|table|Tisch|tavolo|mesa|stół|стол|stůl|テーブル|桌子
tall grass|herbe haute|hohes Gras|erba alta|hierba alta|wysoka trawa|высокая трава|vysoká tráva|背の高い草|高草
tank|char|Panzer|carro armato|tanque|czołg|танк|tank|戦車|坦克
tank factory|usine de chars|Panzerfabrik|fabbrica di carri armati|fábrica de tanques|fabryka czołgów|танковый завод|továrna na tanky|戦車工場|坦克工厂
tannery|tannerie|Gerberei|conceria|curtiduría|garbarnia|кожевня|koželužna|なめし革工場|制革厂
tea room|salon de thé|Teestube|sala da tè|salón de té|herbaciarnia|чайная|čajovna|喫茶室|茶室
tent|tente|Zelt|tenda|tienda de campaña|namiot|палатка|stan|テント|帐篷
tools|outils|Werkzeug|attrezzi|herramientas|narzędzia|инструменты|nářadí|道具|工具
tower|tour|Turm|torre|torre|wieża|башня|věž|塔|塔楼
town|ville|Stadt|città|ciudad|miasto|город|město|町|城镇
town building|bâtiment de ville|Stadtgebäude|edificio cittadino|edificio urbano|budynek miejski|городское здание|městská budova|町の建物|城镇建筑
town hall|mairie|Rathaus|municipio|ayuntamiento|ratusz|ратуша|radnice|役場|市政厅
town house|maison de ville|Stadthaus|casa di città|casa urbana|kamienica|городской дом|městský dům|町家|城镇房屋
town prop|objet de ville|Stadtgegenstand|oggetto cittadino|objeto urbano|przedmiot miejski|городской предмет|městský předmět|町の小物|城镇道具
tractor|tracteur|Traktor|trattore|tractor|ciągnik|трактор|traktor|トラクター|拖拉机
trailer|remorque|Anhänger|rimorchio|remolque|przyczepa|прицеп|přívěs|トレーラー|拖车
tram|tramway|Straßenbahn|tram|tranvía|tramwaj|трамвай|tramvaj|路面電車|电车
transformer|transformateur|Transformator|trasformatore|transformador|transformator|трансформатор|transformátor|変圧器|变压器
tree|arbre|Baum|albero|árbol|drzewo|дерево|strom|木|树
trees|arbres|Bäume|alberi|árboles|drzewa|деревья|stromy|木々|树木
tricycle|tricycle|Dreirad|triciclo|triciclo|trójkołowiec|трицикл|tříkolka|三輪車|三轮车
tricycle, cream|tricycle, crème|Dreirad, creme|triciclo, crema|triciclo, crema|trójkołowiec, kremowy|трицикл, кремовый|tříkolka, krémová|三輪車、クリーム色|三轮车，奶油色
tricycle, wine red|tricycle, bordeaux|Dreirad, weinrot|triciclo, bordeaux|triciclo, burdeos|trójkołowiec, bordowy|трицикл, бордовый|tříkolka, vínová|三輪車、ワインレッド|三轮车，酒红色
truck|camion|Lastwagen|camion|camión|ciężarówka|грузовик|nákladní auto|トラック|卡车
trunk|tronc|Stamm|tronco|tronco|pień|ствол|kmen|幹|树干
tub|bac|Wanne|tinozza|tina|balia|кадка|necky|たらい|木盆
tuna|thon|Thunfisch|tonno|atún|tuńczyk|тунец|tuňák|マグロ|金枪鱼
type|type|Typ|tipo|tipo|typ|тип|typ|型|型
tyre|pneu|Reifen|pneumatico|neumático|opona|шина|pneumatika|タイヤ|轮胎
upper floor|étage|Obergeschoss|piano superiore|piso superior|piętro|верхний этаж|patro|上階|楼层
upturned|retourné|umgedreht|capovolto|boca abajo|odwrócony|перевёрнутый|obrácený|逆さの|倒扣
van|camionnette|Lieferwagen|furgone|furgoneta|furgonetka|фургон|dodávka|バン|厢式车
vehicle|véhicule|Fahrzeug|veicolo|vehículo|pojazd|транспорт|vozidlo|車両|车辆
village|village|Dorf|villaggio|pueblo|wieś|деревня|vesnice|村|村庄
village building|bâtiment de village|Dorfgebäude|edificio di villaggio|edificio de pueblo|budynek wiejski|деревенское здание|vesnická budova|村の建物|村庄建筑
vine|vigne|Weinrebe|vite|vid|winorośl|виноградная лоза|vinná réva|ブドウの木|葡萄藤
vineyard|vignoble|Weinberg|vigneto|viñedo|winnica|виноградник|vinice|ブドウ畑|葡萄园
walkway|passerelle|Steg|passerella|pasarela|kładka|мостки|lávka|通路|走道
wall|mur|Mauer|muro|muro|mur|стена|zeď|壁|墙
warehouse|entrepôt|Lagerhaus|magazzino|almacén|magazyn|склад|skladiště|倉庫|仓库
washing|linge|Wäsche|bucato|colada|pranie|бельё|prádlo|洗濯物|晾晒衣物
watchtower|mirador|Wachturm|torre di guardia|torre de vigilancia|wieża strażnicza|сторожевая вышка|strážní věž|監視塔|瞭望塔
water|eau|Wasser|acqua|agua|woda|вода|voda|水|水
water tower|château d'eau|Wasserturm|torre dell'acqua|depósito de agua|wieża ciśnień|водонапорная башня|vodárenská věž|給水塔|水塔
watering can|arrosoir|Gießkanne|annaffiatoio|regadera|konewka|лейка|konev|じょうろ|洒水壶
weapons|armes|Waffen|armi|armas|broń|оружие|zbraně|武器|武器
weaving|tissage|Weberei|tessitura|tejido|tkactwo|ткачество|tkaní|機織り|纺织
well|puits|Brunnen|pozzo|pozo|studnia|колодец|studna|井戸|水井
wheat|blé|Weizen|grano|trigo|pszenica|пшеница|pšenice|小麦|小麦
wheat field|champ de blé|Weizenfeld|campo di grano|campo de trigo|pole pszenicy|пшеничное поле|pšeničné pole|小麦畑|麦田
wheel|roue|Rad|ruota|rueda|koło|колесо|kolo|車輪|车轮
wheelbarrow|brouette|Schubkarre|carriola|carretilla|taczka|тачка|kolečko|手押し車|独轮车
white|blanc|weiß|bianco|blanco|biały|белый|bílý|白|白色
wicker|osier|Weide|vimini|mimbre|wiklina|ивовый|proutěný|柳細工|柳条
wicker basket|panier en osier|Weidenkorb|cesto di vimini|cesta de mimbre|kosz wiklinowy|плетёная корзина|proutěný koš|柳のかご|柳条篮
wicker suitcase|valise en osier|Weidenkoffer|valigia di vimini|maleta de mimbre|walizka wiklinowa|плетёный чемодан|proutěný kufr|柳のスーツケース|柳条箱
wind pump|éolienne|Windpumpe|pompa a vento|bomba de viento|wiatrak pompowy|ветряной насос|větrné čerpadlo|風車ポンプ|风力水泵
winter prop|objet d'hiver|Winterobjekt|oggetto invernale|objeto invernal|przedmiot zimowy|зимний предмет|zimní předmět|冬の小物|冬季道具
wire|fil de fer|Draht|filo|alambre|drut|проволока|drát|鉄線|铁丝
with walkable deck|avec tablier praticable|mit begehbarer Fahrbahn|con impalcato percorribile|con tablero transitable|z przejezdnym pomostem|с проходимым настилом|s pojízdnou mostovkou|通行可能な床付き|带可通行桥面
without|sans|ohne|senza|sin|bez|без|bez|なし|无
wood|bois|Holz|legno|madera|drewno|дерево|dřevo|木材|木头
wooden|en bois|hölzern|di legno|de madera|drewniany|деревянный|dřevěný|木製|木制
wooden barn|grange en bois|Holzscheune|fienile di legno|granero de madera|drewniana stodoła|деревянный амбар|dřevěná stodola|木の納屋|木谷仓
woodpile|tas de bois|Holzstapel|catasta di legna|pila de leña|stos drewna|поленница|hranice dřeva|薪の山|柴堆
wreck|épave|Wrack|relitto|restos|wrak|остов|vrak|残骸|残骸
yellow|jaune|gelb|giallo|amarillo|żółty|жёлтый|žlutý|黄|黄色
winter look|aspect hivernal|Winteroptik|aspetto invernale|aspecto invernal|wygląd zimowy|зимний вид|zimní vzhled|冬の見た目|冬季外观
Ardennes|Ardennes|Ardennen|Ardenne|Ardenas|Ardeny|Арденны|Ardeny|アルデンヌ|阿登
Europe|Europe|Europa|Europa|Europa|Europa|Европа|Evropa|ヨーロッパ|欧洲
France|France|Frankreich|Francia|Francia|Francja|Франция|Francie|フランス|法国
Germany|Allemagne|Deutschland|Germania|Alemania|Niemcy|Германия|Německo|ドイツ|德国
Holland|Hollande|Holland|Olanda|Holanda|Holandia|Голландия|Holandsko|オランダ|荷兰
Italy|Italie|Italien|Italia|Italia|Włochy|Италия|Itálie|イタリア|意大利
Tunisia|Tunisie|Tunesien|Tunisia|Túnez|Tunezja|Тунис|Tunisko|チュニジア|突尼斯
UK|Royaume-Uni|Großbritannien|Regno Unito|Reino Unido|Wielka Brytania|Великобритания|Velká Británie|イギリス|英国
US|États-Unis|USA|Stati Uniti|EE. UU.|USA|США|USA|アメリカ|美国
USSR|URSS|UdSSR|URSS|URSS|ZSRR|СССР|SSSR|ソ連|苏联
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
