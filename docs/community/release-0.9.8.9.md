---
title: "Studio 0.9.8.9 and Launcher 0.4.8.9: mods install on more PCs, and a safer picture reader"
category: Announcements
order: 14
---
**RUSE Studio 0.9.8.9** and **RUSE Launcher 0.4.8.9** are out:
[Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases). Both apps offer the update when they open.

![R.U.S.E. 2.0](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/ruse-2-0-brand.png)

A small fix-up update:

- **Fixed, reported by a player:** on some PCs no mod would install ("unable to get issuer certificate"), because
  Windows there hasn't got the certificate GitHub's downloads are checked against and can't fetch it. Both apps now
  also try with the list of certificates Firefox uses, which they carry.
- **Safer pictures:** the library both apps read pictures with (Pillow) is now version 13.0.0, with its fixes for
  specially made picture files that could crash the app, use up its memory, or worse.
- **Tighter code:** the 12 warnings GitHub's code check gave on this project are answered. Nothing changes in how
  the apps work.

Everything that changed:
[Studio notes](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/.github/release-notes/studio.md) ·
[Launcher notes](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/.github/release-notes/launcher.md).
