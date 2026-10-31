"""RUSE Guard's window-API calls, shared by the Launcher and the Studio (both include GuardCalls in their API): the
terms the player agreed to, the process-scan choice, and whether fair play is switched on. The first-start agreement
(shared/agreement.js) reads and sets these, so both apps need them. Uses the API's `self._home`. DomesticNukes'
design; rusemod.guard / rusemod.fairplay.
"""
from rusemod import fairplay, guard
from rusemod.home import save_settings, settings


class GuardCalls:
    _guard_server = ""   # where bundles go when the player set no server: the app window sets the project's own

    def use_guard_server(self) -> None:
        """From the app window: a match's evidence goes to the project's RUSE Guard server unless the player set
        another. Tests don't call this, so their bundles stay in the outbox and never leave the PC."""
        self._guard_server = guard.SERVER

    def guard_status(self) -> dict:
        """The player's RUSE Guard settings: the terms version agreed to (0: none yet), whether the process scan may
        run in multiplayer matches, the server's address ("" = evidence kept in the outbox), and the dev key."""
        return guard.settings_of(settings(self._home), self._guard_server) | {
            "dev_key": guard.dev_key(self._home).reason, "terms_version": guard.TERMS_VERSION}

    def _save_guard(self, key: str, value) -> dict:
        values = settings(self._home)
        g = values.get("guard") if isinstance(values.get("guard"), dict) else {}
        g[key] = value
        values["guard"] = g
        save_settings(self._home, values)
        return self.guard_status()

    def guard_accept_terms(self) -> dict:
        """The player agreed to RUSE Guard's terms (what multiplayer matches collect, the scan, reviews, appeals)."""
        return self._save_guard("terms", guard.TERMS_VERSION)

    def fair_play_on(self) -> dict:
        """Whether fair play is switched on (rusemod.fairplay.ON): off, the agreement and badges show none of it."""
        return {"on": fairplay.ON}
