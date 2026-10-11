# Make a mission

> **For:** modders · **You need:** RUSE Studio 0.9.8.4 or later · **Takes:** 20 minutes for a first one

A new **Operation** or **campaign chapter** you make in the Studio can play a mission of its own: its sides, its goals,
what happens when (events) and its own camera moves. Everything is on the map screen's **Scenario** side.

## 1. Make the map

1. **Maps** tab: pick an Operation or a campaign chapter in the list and click **Duplicate map**.
2. **Which one to copy:** the Operation or chapter. **Start from:** the map as it is, or **Blank Terrain** (flat land,
   nothing on it: it starts with a mission of its own, because the copied mission needs the map's own things).
3. Give it a name. The copy plays the mission it copies until you give it its own.

## 2. Switch to Scenario

At the start of the map screen's bar, pick **Scenario** (beside **Map**). The map's own things (ground, buildings,
roads) show faded and can't be grabbed by accident; switch back to **Map** to change them.

## 3. Give it a mission

Click **Mission**, then **Give it a mission of its own**. It starts with the copied mission's **Sides** (a mission keeps
as many human sides as the one it copies).
- **Time limit** (minutes, 0 for none) and what happens when it runs out (defeat, victory or nothing).
- **How it's won:** every main goal done, or only by an event's victory.
- **Sides:** each side's nation, difficulty, money, and whether the computer plays it.
- **Opening camera move:** a camera move played as the mission loads.

## 4. Places, units and groups

- **Add a spot or zone:** named points and round or square zones the goals and events use.
- **Add unit:** units placed at the start. Give them a **Group** name to order them in events or make destroying them a
  goal.
- **Add HQ start:** where a player's HQ starts (on a blank map you place every one; Test in game waits until you have).

## 5. Goals

**Goals > Add a goal.** Each goal is **main** (counts towards the win) or a **bonus**, with its text (English; the other
nine languages behind *Other languages*, empty ones show the English) and how it's done:
- a unit of the player's reaches a **zone**;
- a **group** is destroyed;
- a **time** has passed;
- an **event** completes it.
A goal shows at the start, or when an event shows it.

## 6. Events: When → Do

**Events > Add an event.** **When:** at the start, after a time (repeating if you like), when a side's units enter a
zone, when a group is destroyed, or when a goal is done. **Then** its steps, in turn: a message, bring in units, move a
group along points, attack another group, hold a zone, an artillery strike, a bombing run, paratroopers, a camera move,
give a side money, show or complete a goal, victory, defeat, wait, or hand a side to the computer.

## 7. Camera moves

**Camera moves > Add a camera move**, then click points on the map (the height box sets how high), and a spot
it keeps facing (**Look at...**). **Play it here** to check it in the view. Use it as the mission's opening, or in an event.

## 8. Test it

The box under the trays (**Before Test in game**) lists anything the build would stop on. Then **Test in game**: your
mission is in its own menu entry.

## What's been seen in the game

Seen: the mission's own camera move as it opens, the goals panel, goals by zone, by a group destroyed and after a time,
units brought in, moves, attacks, holding a zone, an artillery strike, a bombing run, repeating events, money given, a
side handed to the computer, victory in an Operation and in a chapter. Not tried yet: paratroopers, a camera move set
off by an event, events on a zone or a group destroyed, a goal done by an event, more than one human side.

**Blank Terrain is still buggy:** use it at your own discretion, and tell us what you find.

**Next:** [[Edit a scenario|Edit-a-Scenario]] · [[Export and share|Export-and-Share]]
