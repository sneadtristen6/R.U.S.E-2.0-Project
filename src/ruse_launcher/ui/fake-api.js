// A made-up LauncherApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=notfound shows the "game not found" state). It does nothing in the real launcher window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
  const sets = [
    { id: "vanilla", name: "Vanilla", description: "The game as Steam installed it.", mods: [], mod_names: [] },
    { id: "half-price", name: "Half-price test", description: "Every building costs half.",
      mods: ["D:/mods/half-price-buildings"], mod_names: ["half-price-buildings"] },
    { id: "ruse2", name: "RUSE 2.0", description: "Balance, new units and China (draft).",
      mods: ["D:/mods/ruse2-core", "D:/mods/ruse2-china"], mod_names: ["ruse2-core", "ruse2-china"] },
    { id: "broken", name: "Old test", description: "", mods: [], mod_names: [], error: "it lists no mods" },
  ];
  const script = [
    "Building the modded copy of R.U.S.E. for Half-price test in D:\\RUSE-Instances\\half-price…",
    "load order: half-price-buildings",
    "  note     left 4 debug-info copies as shipped (everything_debuginfo.cpp.gladndfbin, …)",
    "0 error(s), 0 warning(s), 3 note(s)",
    "changed: genglad\\patchable\\gfx\\everything.cpp.gladndfbin",
    "fingerprint: S1HP-X6PM",
    "modded copy ready: D:\\RUSE-Instances\\half-price  {'linked': 37, 'copied': 23, 'written': 1}",
    "Starting R.U.S.E. from the modded copy…",
  ];
  let playing = null;
  window.pywebview = {
    api: {
      status: async () => mode === "notfound"
        ? { found: false, message: "We couldn't find R.U.S.E. Is it installed through Steam?" }
        : { found: true, game_dir: "D:\\Steam\\steamapps\\common\\R.U.S.E", build: "24687178", drive: "D:",
            message: "Found R.U.S.E. on D: (build 24687178)" },
      mod_sets: async () => sets,
      open_sets_folder: async () => "C:\\Users\\you\\AppData\\Local\\RUSE Mod Platform\\sets",
      choose_game_folder: async () => ({ found: true, drive: "D:", build: "24687178",
        message: "Found R.U.S.E. on D: (build 24687178)" }),
      play: async (id) => {
        playing = { id, step: 0, lines: id === "vanilla" ? ["Starting R.U.S.E. through Steam…"] : script };
        return { job: "fake" };
      },
      job: async (_job, since) => {
        playing.step = Math.min(playing.step + 2, playing.lines.length);
        const done = playing.step >= playing.lines.length;
        return { id: "fake", state: done ? "done" : "running", message: done ? "R.U.S.E. is starting." : "",
          lines: playing.lines.slice(since, playing.step), count: playing.step };
      },
    },
  };
  window.addEventListener("load", () => window.dispatchEvent(new Event("pywebviewready")));
})();
