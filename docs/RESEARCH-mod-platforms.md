# How CurseForge, Nexus Mods, ModDB and Thunderstore work, and what we take (2026-09-30)

The owner asked: "see what you can find on the code that CurseForge has on how it made its platform, and others like
it, like ModDB, Nexus". This is what's public, and what each idea would mean here. Ideas only: none of their code is
copied (Vortex is GPL-3.0 and Thunderstore AGPL-3.0; this project is MIT).

## What's public

| Platform | Code | What we can read |
|---|---|---|
| **Nexus Mods** | **Vortex**, its mod manager, is open source (GPL-3.0, [github.com/Nexus-Mods/Vortex](https://github.com/Nexus-Mods/Vortex)), plus its extension API | how a manager deploys mods, handles conflicts and load order; the site is closed |
| **CurseForge** | closed (Overwolf); a public REST API ([docs.curseforge.com](https://docs.curseforge.com/rest-api/)) and its moderation docs | how files are identified (fingerprints) and checked on upload |
| **ModDB** | closed | its structure: mods, addons, files; releases; staff-checked mirrors |
| **Thunderstore** | open source (a Django site, AGPL-3.0, [github.com/thunderstore-io/Thunderstore](https://github.com/thunderstore-io/Thunderstore)) | a whole mod site and its package format: the nearest thing to "the code of how a platform was made" |

## Findings, and what we'd take

**1. Never touch the game: deploy by links.** Vortex puts mods in place with hard links or symbolic links, so the
game's own files stay untouched and a purge undoes everything.
→ *We already do this, one step safer:* the launcher builds a separate copy (`RUSE-Instances`) from hard links, and
the Steam install is never written to.

**2. Conflicts are shown per file, and settled by a rule.** Vortex has no single global load order: when two mods
change the same file it says so, and the player sets "A loads after B"; a settled conflict gets a green mark.
→ *Take:* our launcher already says which mods clash. Go further: name **what** both change (a unit and its value:
"both set the Sherman's price"), and let the player pick the winner per conflict; keep it in the mod set and its
lockfile, so friends get the same outcome.

**3. Recognize files by their fingerprint.** CurseForge hashes every uploaded file (a Murmur2 fingerprint); its app
hashes the files it finds on a PC and asks the API what they are, so mods a player dropped in by hand get recognized,
named and offered updates.
→ *Take (the owner's "people putting files in the wrong folder"):* our index already holds each package's SHA-256.
The launcher can hash any `.rusemod` / `.zip` it's given, or finds in its library folder or Downloads, and match it
to the index: the right name, the version, "update available", even when the file was renamed or put in the wrong
place. Plan C6.

**4. Every upload is checked before anyone can download it.** CurseForge runs antivirus (ESET and ClamAV), refuses
runnable files (`.exe`, `.sh`, `.bat`), refuses duplicates of an earlier upload, and screens the text; files wait in
review for minutes to three workdays. Nexus scans with VirusTotal; more than 4 engines flagging a file quarantines it
for a moderator, and each file shows a badge (green: scanned and clean). ModDB only serves files from its own
staff-checked mirrors.
→ *Take:* our mods are data only (the apps refuse programs), which removes most of the risk. For the public index
(plan C1), a check that runs on every pull request to `Ruse-Mods`: download the package, check its size and SHA-256,
run our own package check (one mod folder, no programs, a valid `mod.toml`), refuse a duplicate id or a changed
published file; optionally a VirusTotal scan. The launcher shows a "checked" badge on entries that passed.

**5. One page per mod, many files under it.** CurseForge: a project (the page: description, images, links) holds
many files (one per version), each reviewed on its own. ModDB tells full releases ("standalone") from patches.
→ *Take:* our index lists one entry per version already. Add a mod page in the launcher (the mod's README rendered,
its pictures, its versions and changelog), and later patch releases.

**6. A mod package presents itself.** Thunderstore's package is a zip with `manifest.json` (name, version, a
250-character description, website, dependencies as `team-name-version`), `README.md` shown as the mod's page, and a
256×256 `icon.png`; the manager installs dependencies by itself.
→ *Take:* our `.rusemod` already carries `mod.toml` and `README.md`. Add an `icon.png` (256×256) and screenshots,
and put the icon's address in the index, so Browse mods shows cards with pictures, the way the game's own unit cards
look. Dependencies are already in `mod.toml` (MOD_FORMAT §3).

**7. Modpacks point at exact files.** A CurseForge modpack's `manifest.json` lists each mod by project and file id;
Nexus has Collections; Thunderstore has profiles shared by code.
→ *Take:* our mod sets and their shared load order are the same idea. Publishing a set to the index as a pack (each
mod at an exact version and SHA-256) makes "RUSE 2.0 in one click" (plan C2) and pairs with join codes (C4).

**8. Where the files live, and who pays.** All three host the files themselves; Nexus asks for an account and sells
Premium for faster downloads, CurseForge is paid for by Overwolf's ads, ModDB runs its own mirrors.
→ *We stay at no cost:* GitHub Releases hold the files and a small public repository is the index (MOD_FORMAT §15).
Listing releases on ModDB and Nexus as well, for reach, stays plan C5.

## In order, for this project

1. The launcher recognizes a mod file by its SHA-256 against the index (finding 3): C6.
2. A check on every pull request to the index (finding 4), then create `Ruse-Mods`: C1.
3. Icons, pictures and a mod page in Browse mods (findings 5 and 6): with C1.
4. Conflicts named per unit and value, settled per conflict (finding 2).
5. Packs of exact versions (finding 7): C2.

Sources: [Vortex](https://www.nexusmods.com/site/about/vortex) and its
[file conflicts guide](https://github.com/Nexus-Mods/Vortex/wiki/MODDINGWIKI-Users-General-Managing-File-Conflicts);
[Nexus virus scanning](https://help.nexusmods.com/article/128-anti-virus-false-positives) and
[quarantine](https://help.nexusmods.com/article/117-why-has-my-mod-been-quarantined);
[CurseForge REST API](https://docs.curseforge.com/rest-api/) and
[content review](https://docs.curseforge.com/docs/content-management/moderation/reviewing-content/);
[ModDB overview](https://www.moddb.com/features/overview-about-using-moddb);
[Thunderstore package format](https://wiki.thunderstore.io/mods/creating-a-package) and
[modpacks](https://wiki.thunderstore.io/sharing-your-mods/modpacks-and-profiles).
