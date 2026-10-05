---
title: "Studio 0.9.7 and Launcher 0.4.7: very large map mods now build in minutes"
category: Announcements
order: 5
---
**RUSE Studio 0.9.7** and **RUSE Launcher 0.4.7** are out:
[Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases). Both apps offer the update when they open.

**Very large map mods now build in minutes.** Before, they took a very long time to build, and that's why this
update was needed. The most extreme map mod we have, BATTLES > D-Day with its whole sea drained, took about four
hours. Now it builds in under 10 minutes, with the same result, and we're still working on making it faster.

**How we got there.** It took us roughly 15 hours. One cause was behind three problems: the build opened a
drained sea to units in zones 15 m wide, the size that suits a river, and a sea is a quarter of a million of them,
more than a map's movement can hold. So the build was refused, or ran for hours, or used up 14 GB of memory. Now a
wide dried bed gets zones as big as it has room for. Then we went step by step: where units can go is worked out
for infantry and vehicles at once while the ground is painted, the painting and the riverbed mending run on whole
grids across all the PC's cores, and everything is kept between builds. Every step was checked byte for byte
against the old one. The whole story: [How we got here](https://github.com/sneadtristen6/R.U.S.E-2.0-Project#how-we-got-here).

**Export carries the long part.** When you export a big map mod, the Studio puts what its build worked out for the
map's movement into the mod file, so a player's first build of it is shorter. It holds no game files.

Also in this update:

- The Units tab starts with **Change a unit** and **New unit (import a model)**, so Import model is easy to find.
- Known: navy maps aren't worked out yet. A drained or painted sea builds and loads, but the water still shows.

Everything that changed, before and after:
[Studio notes](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/.github/release-notes/studio.md) ·
[Launcher notes](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/.github/release-notes/launcher.md).
It's the alpha: please report what you find, in 🐞 Bug reports or on the [Discord](https://discord.gg/DbufY4Jfg).
