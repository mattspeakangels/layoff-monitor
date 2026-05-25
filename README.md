# Layoff AI Monitor

Streamlit dashboard che monitora i layoff nel tech, con focus sulle aziende AI-related.
Nessuna API key richiesta, nessun costo: usa l'API pubblica di Hacker News (Algolia).

## Installazione

```bash
cd layoff_monitor
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## Avvio

```bash
streamlit run app.py
```

L'app apre `http://localhost:8501` nel browser.

## Come funziona

1. **Scraping** — `scraper.py` interroga `hn.algolia.com/api/v1/search_by_date` con query
   tipo "layoffs", "lays off", "cuts jobs" filtrate sull'ultima finestra temporale.
2. **Parsing** — regex su titoli estrae nome azienda, numero dipendenti, percentuale workforce.
3. **Filtro AI** — keyword matching (ai, llm, gpt, openai, anthropic, ml, …) su titolo + URL.
4. **Cache** — risultati cached 30 min via `@st.cache_data` per non martellare l'API.

## Limiti noti (importanti)

| Limite | Impatto |
|---|---|
| Solo storie da HN | Esclude layoff di PMI o non virali su HN |
| Estrazione regex | ~10-20% errori sul nome azienda o conteggio |
| Filtro keyword AI | Genera falsi positivi/negativi |
| API HN rate limit | ~10k req/h, ampiamente sufficiente |

**Non usare come fonte primaria** per decisioni di investimento o HR. È un tool di monitoring.

## Estendere

- Aggiungere fonti: implementare nuovi fetcher in `scraper.py` (es. RSS di TechCrunch, Reddit).
- Migliorare l'estrazione: sostituire le regex con un piccolo classifier o un LLM locale.
- Salvare storico: aggiungere persistenza su SQLite per trend > 1 anno.

## Output atteso

- KPI: storie totali, dipendenti tracciati, aziende uniche, ultimi 30 giorni.
- Bar chart: storie/settimana e dipendenti/settimana.
- Top 15 aziende per dipendenti coinvolti.
- Tabella ordinata per data con link all'articolo e alla discussione HN.
- Export CSV.

## Struttura

```
layoff_monitor/
├── app.py            # UI Streamlit
├── scraper.py        # fetch + parsing HN
├── requirements.txt
└── README.md
```
