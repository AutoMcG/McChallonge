# mcrobotcombatevents

Independent package for scraping Robot Combat Events pages into JSON.

## Install

From this package directory:

```bash
pip install -e .
```

## Usage

```bash
rce-export 7187 -o build/event_7187.json
```

Or run as a module:

```bash
python -m mcrobotcombatevents 7187 -o build/event_7187.json
```
