**RUSE Launcher, an early test version.** It finds R.U.S.E. through Steam, lists your mod sets, and **Play** builds a
modded copy of the game and starts it. Your Steam install is never changed.

Not there yet: making mod sets in the window. For now a mod set is a small text file in
`%LOCALAPPDATA%\RUSE Mod Platform\sets\` (the **Open mod sets folder** button opens it), for example `half-price.toml`:

    name = "Half-price test"
    mods = ["C:/path/to/a/mod/folder"]

Example mods are in the repo's `examples` folder. Problems and ideas: GitHub Issues.
