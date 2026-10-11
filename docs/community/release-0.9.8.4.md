---
title: "Studio 0.9.8.4 and Launcher 0.4.8.4: mods download on every PC"
category: Announcements
order: 9
---
**RUSE Studio 0.9.8.4** and **RUSE Launcher 0.4.8.4** are out:
[Releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases). A quick fix.

![RUSE Launcher, with Browse mods at the bottom](https://raw.githubusercontent.com/sneadtristen6/R.U.S.E-2.0-Project/main/docs/images/launcher.jpg)

**Mods download on every PC.** On some PCs no mod would download: "certificate verify failed: unable to get local
issuer certificate". Windows hadn't fetched the certificate GitHub is checked against yet, and the apps couldn't ask
it to. Now they ask Windows, as a browser does, and try again. The apps' own updates too.

**If your Launcher shows that error now,** its update can't download either: get **RUSE-Launcher-Setup-0.4.8.4.exe**
from the [launcher releases](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases?q=launcher) in your
browser and run it. It installs over the old one, as the update does.

Not tried yet on a PC that had the problem.

Bugs and questions: [Bug reports](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions/categories/bug-reports).
