# Contributing to RUSE 2.0

Thanks for wanting to help. RUSE 2.0 is the RUSE Studio (make units and maps) and the RUSE Launcher (play them), for
R.U.S.E. (2010). There are many ways to help, and most of them need no code.

## Report a bug

- Use the apps' **Report a problem** button: it fills in the app and its version for you. Or post in
  [Discussions → Bug reports](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions), whose form asks for
  what we need. Quick questions about a problem are welcome on the [Discord](https://discord.gg/DbufY4Jfg) too.
- Say what you did step by step, what happened and what you expected. Copy any message the app showed, and drag in
  screenshots. In-game screenshots from the game's own key keep the camera next to them, which helps a lot.
- Please don't paste paths that show your Windows user name: `%LOCALAPPDATA%\...` is enough.
- Check you're on the latest version first: each app offers its updates when it starts.

A security problem (a mod or a file that can harm a player's PC, an update that installs although it doesn't match,
a leaked key) goes privately, never in a public post: [SECURITY.md](SECURITY.md) says how.

The bugs we know about are listed in [issue #15](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/issues/15).

## Test in the game

Many of the build's checks rest on how R.U.S.E. behaves, and each one is only settled once it's seen in a match.
Anyone with the game can help: try a feature in a match and report what you saw, with screenshots, in
[Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions). It's one of the most useful things
you can do.

## Ideas and questions

Come and talk on the project's [Discord](https://discord.gg/DbufY4Jfg), or post them in
[Discussions](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/discussions). The
[field manual](https://github.com/sneadtristen6/R.U.S.E-2.0-Project/wiki) explains the apps; the README's
"Questions? Ask any AI" section shows how to get quick answers about the project.

## Code

1. You need Python 3.11 or newer, on Windows (where the apps run) or Linux. The code is in `src/`: `rusemod` (the
   game's files and the mod system), `ruse_mod_engine` (LittleGroove's RUSE-Mod-Manager engine, for `.rmod` mods) and
   the two apps, `ruse_studio` and `ruse_launcher`. The README's "For contributors" section describes each part.
2. Run the tests before you send a change. They use small made-up files, so no game is needed:

   ```
   py -3 -m unittest discover -s tests
   ```

   with `PYTHONPATH=src`. GitHub runs them on every push and pull request, on Windows and Linux.
3. Run `py -3 tools/check_public.py`. It fails when game files or private material would reach this public repo;
   GitHub runs it too.
4. Open a pull request against `main` and fill in its template: what it changes, how you checked it, and anything
   still untested in the game.

A few rules the project keeps:

- **Never write into the game's folder.** Everything the apps build goes into a modded copy or the platform's own
  folder.
- **No game files in the repo.** Tests make their own small files.
- **A rule about how the game behaves is tested in the game before the build enforces it,** or it's marked as not
  tested yet.
- **Say what was and wasn't checked.** Release notes and messages say what was seen in the game.
- **Plain words** in anything a player reads, in all ten of the apps' languages (`src/ruse_studio/words.toml`,
  `src/ruse_launcher/words.toml`).

## Credit

Everyone who helps is welcome in the README's credits. Tell us the name you'd like to be credited under.

## Code of conduct

Everyone taking part agrees to the [code of conduct](CODE_OF_CONDUCT.md). By contributing you agree that your work is
shared under the project's [license](LICENSE) (GPL-3.0).
