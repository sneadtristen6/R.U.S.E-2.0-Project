# Export and share

> **For:** modders · **You need:** RUSE Studio and a finished mod · **Takes:** 5 minutes

## 1. Export

1. Open the **Mod** menu and pick **Export mod...**.
2. Fill in the **version** (three numbers, like `1.0.0`), your name and a line about what the mod does.
3. Pick where to save. The Studio builds the mod once on your game, to record the game build it was made on and its
   **fingerprint** (a short code that's the same for everyone with the same mods), then saves one file:
   `<your-mod>-<version>.rusemod`.

That file is all a player needs: they add it in RUSE Launcher ([[Install and play|Install-and-Play]]).

**Big map mods:** a map changed all over can take the build minutes to work out (where units can go on ground you
opened, for one). You wait for that once. The export puts what the build worked out into the file, so a player's
first build is shorter. It holds our own numbers only, never a file of the game's, and it's locked with the game's
own file for that map: it opens only on a PC that has the game. Movement only so far; not seen in the game yet.

When the export is done, the Studio opens **Share your mod** with the file's size, its SHA-256 checksum and its entry
for the list, ready to copy. You can open it again any time from the **Mod** menu (**Share your mod...**).

## 2. Share: add it to the supported mods

Made a mod? Add it to the list and become a contributor. RUSE Launcher's **Supported mods** tab shows the mods on
the list at [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods), and players install them in one
click (new players get them offered on the launcher's first start):

1. Upload the `.rusemod` (a GitHub Release is easiest: your own repository's, or the list's).
2. Open a pull request to [sneadtristen6/Ruse-Mods](https://github.com/sneadtristen6/Ruse-Mods) that adds your mod's
   entry to `index.toml`: paste the entry Share your mod shows and put the file's link in `download`. The size and
   SHA-256 must be the ones the export showed: the launcher refuses a download that doesn't match, so nobody can swap
   your file for another.
3. Or post it in [Discussions > Mods & maps](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions) with a
   screenshot and what it changes (drag the `.rusemod` into the post), and it's added to the list for you.

A cheat or a test tool (free units, instant building...) gets the tag `"cheat"`: the launcher shows it in its own
group, "Cheats and test tools (optional)", and never ticks or downloads it unless the player does. A new version is a
new file with a new version number: a published file never changes.

The entry's exact format:
[MOD_FORMAT.md, section 15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/docs/MOD_FORMAT.md#15-the-mod-index-supported-mods).

## What a mod can hold

Data only: numbers, texts, maps, models, textures. Programs (`.exe`, `.dll`, scripts that run on a PC) are refused by
both apps. One exception: the game's own mission scripts, as the Studio saves them. They run inside the game and can do
anything it can, so install those only from authors you trust ([SECURITY.md](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/blob/main/SECURITY.md)).

## Good practice

- Keep your mod folder: the `.rusemod` is for players, the folder is what the Studio edits.
- Say in your post what other mods yours needs or clashes with.
- Credit the people whose work you build on.
