# Cover and movement

> **For:** modders · **You need:** RUSE Studio 0.7.2 and a mod · **Proven in the game:** infantry on painted cover
> are hidden; units plan around blocked ground

Two invisible layers decide how a map plays: **cover** (where units hide) and **movement** (where units can go).

## Cover: make a town or a wood units hide in

1. In the bar, click **Cover & movement** (its **Cover** tab). The map turns green where units are hidden today (the map's woods and towns).
2. Pick a tool:
   - **Cover** paints hiding ground (drag);
   - **Uncover** takes it away (drag): the ground it went over is striped white, even where there was no cover to
     take;
   - **Town** puts cover around every building of the town you click. Point at a town first: a ring shows on each
     building it will cover, with the count beside the pointer. **Size** sets how far around each building.
3. After each stroke, a line beside the pointer says what it changed for units ("Cover taken away from 12,000 m²",
   or "No cover here to take away").
4. Tick **Cover** at the top of the map to keep the green showing while you use other tools.

> [!NOTE]
> Placed buildings and trees don't hide units by themselves. After placing a town, click it with **Town**.

## Movement: close ground to units

1. Tick **Where units go** at the top of the map:
   - **red**: no unit can go there (water, cliffs, off the map);
   - **yellow**: infantry only (woods);
   - **purple**: vehicles only.
2. In the bar, click **Cover & movement**, then the **Movement** tab, and drag:
   - **Block**: no unit gets through (a wall, a minefield, a cliff you made);
   - **Block infantry**: vehicles still pass;
   - **Block vehicles**: infantry still pass, as in a wood;
   - **Open**, **Open to infantry**, **Open to vehicles**: let units onto ground the map keeps them off (the reverse
     of Block).
3. Ground a Block or Open stroke went over is striped: blue where units can go, red, yellow or purple where it's
   closed. Beside the pointer, each stroke says how much it closed or opened, or that nothing changed there.

Units plan their route around blocked ground. Buildings you place block units too (see
[[Place buildings and trees|Place-Buildings-and-Trees]]).

**Next:** [[Draw roads|Draw-Roads]]
