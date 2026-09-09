# Volve Field: Drilling NPT vs. Well Productivity

Analysis of non-productive time across the Volve drilling campaign, and whether
the wells that were hardest to drill were the wells worth drilling.

> **Status:** Phase 0 complete — scaffold and schema in place. Analysis in progress.

## The question

Volve's drilling campaign consumed significant non-productive time. Where did it
go, what did it plausibly cost, and did high-NPT wells deliver proportionally
higher production?

## Headline finding

_To be filled in. One sentence, with a number._

## Stack

Python (extraction, parsing) → PostgreSQL (star schema) → Power BI (report)

## Reproduce

Environment and schema: [`docs/SETUP.md`](docs/SETUP.md).
Getting the data: [`docs/DOWNLOAD.md`](docs/DOWNLOAD.md).

Short version:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit it
psql -U volve_app -d volve -f sql/01_ddl_dimensions.sql
psql -U volve_app -d volve -f sql/02_ddl_facts.sql
python src/00_download.py --tree          # browse the Azure container
python src/00_download.py --get "<prefix>"
python src/01_inventory.py
```

## Repository layout

| Path | Contents |
|---|---|
| `src/` | Extraction, parsing, classification, load |
| `sql/` | Schema DDL, transforms, analysis queries |
| `data/reference/` | NPT taxonomy, wellbore name map — **versioned** |
| `data/raw/`, `data/interim/` | Local only, gitignored (licence) |
| `docs/` | Setup, methodology, data dictionary, full report |
| `powerbi/` | Report file |

## Important caveats

- **Costs are modelled, not actual.** Equinor did not publish AFE data. The cost
  layer derives from published North Sea day rates with a stated spread
  multiplier. Absolute figures are indicative; the ranking of NPT categories is
  the durable result.
- **~20 wellbores.** This is a descriptive operational review, not a statistical
  or predictive study.
- **Sidetracks are separate wellbores**, with the parent well available as a
  rollup. See the methodology note for why.

## Data licence

Volve field dataset, released by Equinor ASA and the Volve licence partners for
study, research and development purposes. See [`LICENCE-DATA.md`](LICENCE-DATA.md).
No source data is redistributed in this repository.

## Code licence

MIT — see `LICENSE`. Covers the code only, not the data.
