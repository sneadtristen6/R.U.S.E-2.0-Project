# Export and share

> **For:** modders · **You need:** RUSE Studio and a finished mod · **Takes:** 5 minutes

## 1. Export

1. Open the **Mod** menu and pick **Export mod...**.
2. Fill in the **version** (three numbers, like `1.0.0`), your name and a line about what the mod does.
3. Pick where to save. The Studio builds the mod once on your game, to record the game build it was made on and its
   **fingerprint** (a short code that's the same for everyone with the same mods), then saves one file:
   `<your-mod>-<version>.rusemod`.

That file is all a player needs: they add it in RUSE Launcher ([[Install and play|Install-and-Play]]).

## 2. Share

**Today:** post it in [Discussions > Mods & maps](https://github.com/sneadtristen6/Ruse-Mod-Platform/discussions)
with a screenshot and what it changes (drag the `.rusemod` into the post), or share it on Discord.

**Coming: Browse mods.** The launcher will list the community's mods and install them in one click. To be listed,
your mod goes in a public index on GitHub:

1. Attach the `.rusemod` to a GitHub Release (your own repository's, or the index's).
2. Open a pull request to the index adding your mod's entry: id, name, version, download link, the file's size and
   its SHA-256 checksum. The launcher refuses a download that doesn't match the checksum, so nobody can swap your
   file for another.
3. A new version is a new file with a new version number: a published file never changes.

The entry's exact format:
[MOD_FORMAT.md, section 15](https://github.com/sneadtristen6/Ruse-Mod-Platform/blob/main/docs/MOD_FORMAT.md#15-the-mod-index-browse-mods).

## What a mod can hold

Data only: numbers, texts, maps, models, textures. Programs (`.exe`, `.dll`, scripts that run on a PC) are refused by
both apps, so installing a mod is always safe.

## Good practice

- Keep your mod folder: the `.rusemod` is for players, the folder is what the Studio edits.
- Say in your post what other mods yours needs or clashes with.
- Credit the people whose work you build on.
