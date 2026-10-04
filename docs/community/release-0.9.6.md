---
title: "Studio 0.9.6 and Launcher 0.4.6: import your own 3D models"
category: Announcements
order: 4
---
**RUSE Studio 0.9.6** and **RUSE Launcher 0.4.6** are out:
[Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases). Both apps offer the update when they open.

**Import your own 3D models.** On a new unit's page, **Import model…** takes a **.3ds** or **.glb** from Blender or any
3D tool and fits it to the unit it copies: its size, its turret on that unit's turret, its pictures as textures of its
own. The game builds it, drives it and turns its turret like the original. How:
[Import a model](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/wiki/Import-a-Model).

**The first model brought into R.U.S.E. from another 3D program:** an M1 Abrams, a new US tank beside the Sherman,
seen in the game (bought at the Armor Base with its own card, built, turning its turret). It's a mod in
[Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods): tick **M1 Abrams** in the Launcher's **Supported mods**.
Model: "Tank Abrams" by ags, free at [downloadfree3d.com](https://downloadfree3d.com/3d-models/vehicles/tank/tank-abrams/).
Early: its tracks and wheels don't turn yet, and the gun flash and wreck are the Sherman's.

![Two M1 Abrams at a US base, imported with RUSE Studio](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/units-abrams-two-at-base.jpg)

Also in this update:

- **Test in game** and the Launcher's **Play** start at once when nothing changed, and a build reuses what it made
  last time (a big test mod took 213 s every time; now 68 s after the first build).
- **Delete map** for the maps you made with Duplicate map (to the Recycle Bin, where you can get them back).
- **Erase the whole map**, and erasing big areas in seconds.
- Roads follow ground you reshaped, and flattened riverbeds are filled from their banks. New: not yet seen in the game
  at scale, please report what you find.
- Fixed: a new unit with its own card crashed the game when it was built (0.9.5).

Everything that changed, before and after:
[Studio notes](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/.github/release-notes/studio.md) ·
[Launcher notes](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/.github/release-notes/launcher.md).
It's the alpha: please report what you find, in 🐞 Bug reports or on the [Discord](https://discord.gg/DbufY4Jfg).
