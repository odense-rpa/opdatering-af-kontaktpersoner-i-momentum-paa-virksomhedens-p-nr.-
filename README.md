# Opdatering af kontaktpersoner i Momentum på virksomhedens P-nr.

Robotten deaktiverer kontaktpersoner i Momentum for en given virksomhed ved at filtrere dem, der allerede er registreret som sagsbehandlere, fra og deaktivere de resterende.

## Hvad gør robotten?

1. Henter listen over sagsbehandlere (sagsbehandlere) for virksomheden med UUID `4224e7fb-40c9-409c-938e-8aae62d5d753` fra Momentum.
2. Henter listen over kontaktpersoner (kontaktpersoner) for samme virksomhed fra Momentum.
3. Filtrerer kontaktpersoner med kontaktrollekoden `057CBDC6-155E-45F8-BE9A-6E10A7C63906` (sagsbehandler-rollen) fra.
4. Filtrerer yderligere kontaktpersoner fra, hvis navn matcher en sagsbehandlers visningsnavn.
5. Tilføjer de resterende kontaktpersoner (navn og ID) til arbejdskøen.
6. Deaktiverer statussen for hver kontaktperson i Momentum via API'et.
7. Registrerer hvert afsluttet arbejdselement i ODK Tracker mod SQL Server.

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **Automation Server** (arbejdskø)
- Adgang til **Momentum** (produktion)
- Adgang til **Odense SQL Server** (ODK Tracker)

## Installation

```sh
uv sync
```

## Konfiguration

Credentials registreres i Automation Server:

- `Momentum - produktion` — kræver felterne `username`, `password`, `base_url`, `api_key` og `resource`
- `Odense SQL Server` — forbindelse til ODK Tracker-databasen

Miljøvariabler:

| Variabel | Beskrivelse |
|---|---|
| `ATS_URL` | Base-URL til Automation Server API (f.eks. `http://localhost/api`) |
| `ATS_TOKEN` | Bearer-token til Automation Server |
| `ATS_WORKQUEUE_OVERRIDE` | Valgfrit: tilsidesæt arbejdskø-ID |

## Kørsel

```sh
uv run python main.py --queue   # Fyld arbejdskøen
uv run python main.py           # Behandl arbejdskøen
```

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Klient til Automation Server (arbejdskøer og credentials) |
| `momentum-client` | Klient til Momentum sagsstyringssystem (hentning og opdatering af kontaktpersoner) |
| `odk-tools` | ODK-værktøjer inkl. Tracker til logning af afsluttede opgaver i SQL-databasen |

## GDPR og sikkerhed

Robotten behandler navne og interne ID'er på kontaktpersoner tilknyttet en virksomhed i Momentum. Disse oplysninger kan udgøre personoplysninger, hvis kontakterne er fysiske personer. Data lagres midlertidigt i arbejdskøen på Automation Server og slettes igen, når køen er behandlet. Adgang til Automation Server og rapporter herfra bør begrænses til relevante medarbejdere.
