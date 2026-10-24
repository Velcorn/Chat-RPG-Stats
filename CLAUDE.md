# CLAUDE.md

Public, read-only stats dashboard for the Twitch chat RPG at rpg.sola.rip. A GitHub Action collects public data every
15 minutes and publishes a static page on GitHub Pages. See README.md (German) for what it shows and how it calculates.

## Principles

- **Read-only, public data only.** No login, no cookies, never anything but GETs. Nothing automated in the game or chat.
  One exception, by the user's decision (09.10.2026): the static item form table (`FORMS`, `#/spiel/formen`) was checked once by hand against
  market listings read with a login. Nothing in the collector uses a login.
- **Keep requests low.** One collector for everyone; visitors only read the published files. Don't add endpoints or
  per-player requests without need; the watchlist is capped (opt-in for players; the channel owners are on it by default). The board's top 100 also get the watchlist data, but in one pass a day, on the first run of the day (`TOP_WATCH`, about 100 requests at 7 Uhr; the operator's decision, 09.10.2026); since 0.26.0 also in every run those whose board score no longer matches the gear sum of their last profile (`collect.slot_sum`, about 6 a run; the operator's decision, 11.10.2026). The site's operator can ask us to stop at any time.
- **No activity logs per player.** Store values and their changes (gear, silver, stat totals), never a player's
  individual quests or fights with times and channels: that would show when and where someone plays.
- The README's request table must match what `collect.snapshot` actually does.
- **Never mention the operator's other projects or accounts** anywhere (README, docs, page, changelog, comments, commit
  messages). This project stands on its own.

## How to work (Karpathy's guidelines)

1. **Think before coding.** State assumptions; if a request is ambiguous, ask. Check facts against the code and the
   live API (read-only GETs, sparingly).
2. **Simplicity first.** The least code that solves the problem. No speculative features.
3. **Surgical changes.** Touch only what the task needs; match the surrounding style.
4. **Goal-driven execution.** Turn the task into a checkable goal and verify it. For page changes, build and look at
   the page (desktop and phone width).

## Language

Everything users see is German (README, page, issue form, Action replies); code, comments and commits stay
English. Exception: badge labels and the names of workflows that show up in a badge are English (`coverage`, `collect`). Amounts in silver with the German thousands separator (`fmtSilver`), numbers with nouns via `count`. Plain
punctuation: `-` instead of dashes, `...` instead of the ellipsis character, `->` instead of arrows, straight quotes. The README and the page footer carry the vibe-coding notice (mostly AI-written, spot-checked);
keep it.

## After every change

1. `PYTHONPATH=src uv run python -m unittest discover tests` and `uv run ruff check` (the commit hook runs both; CI runs the same hooks plus coverage).
2. Keep the docs current in the same commit, so they never lag the code: README.md (short; what it shows, the request
   table, schedule, setup and commands must be true today), docs/funktionsweise.md (data flow and every calculation)
   and this file's map and facts. Grep them for every number, name and behaviour the change touches, removed things
   included. Operator details (timers, workflow plumbing) belong in docs/funktionsweise.md and this file, not the README.
3. If visitors notice a change, use CalVer YYYY.MM.DD, exactly one version per calendar day, without suffixes.
   The first change of a day sets today's version in `pyproject.toml`, runs `uv lock`, and starts that day's
   `CHANGELOG.md` entry (`## YYYY.MM.DD (DD.MM.YYYY)`). Further changes that day keep the version and append
   bullets to the same entry. Keep groups in this order: Neu, Verbessert, Oberfläche, Behoben, Inkompatibel,
   Geändert, Entfernt, Hinweis, then any additional groups. The changelog lists only visitor-facing changes.
   Historical references through 0.51.3 are old SemVer numbers and need no rewrite. No git tags.
4. Commit, push: `SSH_AUTH_SOCK=$XDG_RUNTIME_DIR/ssh-agent.socket git push`.

## Project map

Python modules live in `src/` (flat, no package; tests and tools need `PYTHONPATH=src`); `site/`, `tests/`, `docs/` stay at the top.

- `src/collect.py`: one run (about 17 requests plus one per new fight plus the profile sweep, ~55; two parts since 0.23.0: `--part core` is published first, `--part profiles` (`read_profiles`, `profiles_state`, record line `part: "profiles"`) runs in the workflow's second job and shows on the next run's page): `snapshot` (the requests), `state_from` (flat current state, incl. the watchlist's gear per slot), `record` (only the changes).
  Writes `data/days/YYYY-MM-DD.jsonl` (one line per run) and `data/state.json` on the `data` branch.
- `src/fightstats.py`: fight statistics for `summary.json` -> `stats` (death share in won fights and per fight (`fallen`), roles, power vs recommendation, hours, channels); only sums per fight, never per player.
- `src/build.py`: replays the day files (`History`, incl. rules log and live share per channel), computes pace, player forecasts, peers, guild standing, fight odds, and current the announced final-boss time (`final_boss_at`), publishes `seasons.json` and immutable generated archives; writes
  `_site/data/changelog.json` (the site changelog parsed from `CHANGELOG.md`), `_site/data/summary.json`, `players.json` (search index), `builds.json` (every known split without names, for the build map), `timelapse.json` (`src/timelapse.py`: percentile curves and histogram shares every six hours, for everyone and each guild), `toplapse.json` (the top-100 board every two hours, `History.board_at`) and `p/<login>.json`.
- `site/index.html`: the whole dashboard (no build step; hash routes `#/<section>/<sub>` with sections `start` (default), `rangliste` (subs incl. `zeitraffer`), `gilden` (subs `vergleich`, `zeitraffer` + one per guild), `spiel` (subs `regeln` (rules, then the measured rule changes), `ausruestung` (`viewMax` best build per class from `TIER_FORMS`, then `viewForms` (static `FORMS` table), then `viewSpecial`), `verbessern`; the old subs `aenderungen`/`formen`/`maximum`/`spezial` are `alias`es in `SECTIONS`); `RULE_LABELS` holds the German rule names), `kaempfe` (subs `uebersicht`, `kraft`, `letzte`; see `SECTIONS`: each sub
  page is a tab in the second row) and `#/changelog` (site changes, linked in the footer), `#/spieler/<login>`).
- Guilds without members but with a treasury are read too (`collect.snapshot`); `build` keeps them out of `guilds` and only counts their boss results in `guild_boss`.
- `src/finale.py` (2026.10.25): the season review's story for `summary.json` -> `finale` (`top_story`: highest score over time, who reached it first, who held it how long; `records`: donors, Kampfkraft), from `History` only.
- `src/archive.py`: at a season boundary, builds the final public dataset and copies it to `data/seasons/<id>/`, then updates `data/seasons.json`. It refuses to replace an existing archive and does not reset live collection state.
- Season UI: the corner selector uses `?s=<id>` to prefix all dashboard data reads with `data/seasons/<id>/`; `#/saison` is the live or archived chronicle and comparison page. Archived normal tabs remain fully browsable.
- `src/watchlist.py` + `watchlist.txt`: the list (channel owners by default, others opt-in), changed by the issue form via `.github/workflows/watchlist.yml`; below the marker line `collect.AUTO_MARK` the board's top 100, rewritten by `watchlist.sync` (`--sync`, a step of `collect.yml`) whenever they change. Only the part above the marker is read in every run.
- `collect.stat_digest`/`player_stats` (0.27.0): per fight the fighters counted by role and stat in steps of 10 (`sx`, no names), `fightstats.stat_curves` sums the won boss fights per boss for the Kampfkraft page.
- `fightstats.UPDATE` (04.10.2026, the story update) splits `eras.after`/`eras.before` for the fight pages.
- `tests/`: `test_collect.py`, `test_pipeline.py` (build), `test_fightstats.py`, `test_watchlist.py`, `test_timelapse.py`, `test_site.py` (the page script parses with `node --check`).
- `docs/funktionsweise.md`: German detail: data flow, storage, watchlist, every calculation. README stays short.
- `.pre-commit-config.yaml` (prek: ruff, tests, hygiene, plain punctuation), `.github/workflows/ci.yml` (hooks + coverage; writes
  the coverage badge with `.github/badge.py` to the `badges` branch, don't commit there), `.github/dependabot.yml`.
- `.github/workflows/collect.yml` (name `collect`): schedule (4-22 UTC, collect.py skips outside 7-24 Berlin), data branch, Pages deploy.
  GitHub's schedule fired once a day on 30.09.2026, so `deploy/chat-rpg-stats-collect.{service,timer}` (systemd user timer
  on the operator's machine) dispatches the workflow every 15 minutes, 7-24 Berlin time.

## Game API facts

- Public without login: `/api/rules`, `/api/leaderboard?by=gear|gold&limit=100` (max 100; `silver` and `level` return
  the gear board), `/api/players/{login}`, `/api/guilds`, `/api/guilds/{login}` (all members with gear score and
  donations), `/api/combat/history` (last 20 fights, about a day), `/api/combat/history/{id}` (one fight: fighters with role and alive, `crowd.tally` and per-fighter damage/taken/healing/boosted summed per role (`rsum`), `guildName`/`summonedBy`/`guildOnly`/`treasuryChange` kept as `gn`/`by`/`go`/`gc` in the digest; `power`, `gearScore`, `averagePower`, `recommendedGear` are 0 there), `/api/combat?kompakt=true` (the fight the site still shows: average gear and power, recommendation, `battle`), `/api/channels` (with `chatMode`), `/api/rules`, `/api/compendium` (not read any more: the page showed what the game shows itself, removed in 0.22.0), `/api/guilds/first-kills` (once a day, `collect.first_kills_state`), the game's changelog (a JS literal in the `/changelog` page's script chunk, found via the entry script's router; `collect.read_changelog`, once a day, written by the build as `changelog.json`) (the trader endpoint is not used).
  `/api/market/board` needs a login (not used).
- The leaderboard lags the guild pages by a few minutes.
- `gearScore` on the guild pages (members, guild total) is Kampfkraft (gear plus `talentBonus`; measured 07.10.2026: gear 328, power 360) and the user finds it too unreliable to rank by. The plain gear score (atk + def + sup, equal to a profile's `gearScore`) comes from the board (top 100, its own value), the watchlist profiles and the collector's sweep (`sweep_batch`: a slice of ~1/60 of the active guild members off the board per run, from `/api/players/{login}`, cursor `sweep_after` in the state). It is `players[login]["gs"]` (history series `gs`); `gear` stays the Kampfkraft and only feeds the guild totals and the player page's "power" row. Inactive players are never read: no `gs`, no page, no rank. Rank, pace, risers, forecast and the guild average use `gs`. The fight pages' Kampfkraft is the fight's average `power` against the recommendation.
- Play window 7-24 Berlin time; nothing changes at night.
