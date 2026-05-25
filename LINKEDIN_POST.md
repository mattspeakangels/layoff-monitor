# LinkedIn Post — Layoff AI Monitor

## Versione consigliata (italiano, ~180 parole)

> Ho passato una giornata a costruire una cosa che non mi serve, solo per vedere se potevo farla.
>
> Si chiama **Layoff AI Monitor** ed è una dashboard che traccia i licenziamenti nel mondo tech, in particolare quelli in cui l'AI viene citata come causa. Aggrega Hacker News, TechCrunch e Google News, estrae azienda e numero di dipendenti dal titolo con un po' di regex, e assegna a ogni evento due punteggi (1–5): quanto è verificabile la notizia e quanto è plausibile che l'AI c'entri davvero.
>
> Non l'ho scritta da solo. Ho lavorato fianco a fianco con Claude (Anthropic) in Claude Code: io decidevo *cosa* serviva, lui scriveva il codice. Backend Firestore, ETL on-demand, UI ispirata ai terminal finanziari (3 varianti grafiche, dark/light switchabile). Tutto in poche ore.
>
> Non c'è un modello di business. Non sto vendendo niente. È solo una dimostrazione di una cosa che ormai dovrebbe essere ovvia: oggi la barriera tra "ho un'idea" e "ho un prodotto online" è la curiosità di provarci.
>
> I dati si aggiornano ogni 6 ore via GitHub Actions, quindi quello che vedi è sempre fresco.
>
> 👉 [link all'app]
>
> 🛠 Stack: Streamlit · Firebase · Plotly · GitHub Actions · Claude Code
> 📦 Codice open su GitHub: [link al repo]

---

## Hook alternativi (se quello sopra non ti convince)

### A — Provocatorio
> "Quanto ci vuole oggi a costruire un prodotto da zero? Una giornata, se hai voglia di provare."

### B — Numerico
> "1 giorno · 0 righe di codice scritte a mano · 1 dashboard funzionante e online. Ecco cosa è successo."

### C — Onesto
> "Ho costruito un'app che non mi serve, solo per capire fino a dove arriva un essere umano + un LLM nel 2026. Risultato: molto più in là di quanto pensassi."

### D — Diretto al punto
> "Tracciare i layoff tech con focus AI. Idea → online in un giorno. Co-pilota: Claude."

---

## Cosa allegare al post

LinkedIn premia i post con visual. Tre opzioni in ordine di efficacia:

1. **Screenshot della dashboard** (variante Signal, dark) — la più "wow" perché sembra un terminale finanziario. Apri http://localhost:8501 + Cmd+Shift+4 per cattura. Mostra: header + KPI con sparkline + chart.
2. **Carosello 3 immagini**: (a) dashboard, (b) detail card di una notizia, (c) screenshot del codice in Claude Code che fa una modifica live.
3. **Video screencast 30 secondi**: switch variante Signal → Pulse → Radar + scroll dei dati. Usa QuickTime → File → New Screen Recording.

---

## Hashtag consigliati

Non più di 5, mirati, niente generici tipo `#tech` o `#innovation`:

```
#ClaudeCode #AIAgents #BuiltWithAI #IndieHacker #DataViz
```

Per audience più mainstream italiana:
```
#IntelligenzaArtificiale #AI #SideProject #Streamlit #OpenSource
```

---

## Timing

- **Quando postare**: martedì o mercoledì, 8:30–9:30 o 12:30–13:30 (italia)
- **Evita**: venerdì pomeriggio, lunedì mattina
- **Primo commento**: nel primo commento metti link aggiuntivi (repo GitHub, articolo Anthropic su Claude Code) — LinkedIn penalizza i link nel corpo del post

---

## Cose da NON fare

- ❌ Non dire "rivoluzionario", "disruptivo", "game changer"
- ❌ Non mettere emoji a inizio frase (LinkedIn-cringe)
- ❌ Non chiudere con "Cosa ne pensi? 👇" — fake engagement bait
- ❌ Non taggare 15 persone per arrivare al feed (fa l'effetto opposto)
- ✅ Una persona vera (es. tagga Anthropic Italia o chi ti ha ispirato) vale 10 tag a caso

---

## Followup (se il post funziona)

Se il post fa più di 50 reazioni, prepara un secondo post **una settimana dopo** con:
- Lezione tecnica imparata (es. "Perché i secret di Firebase su Streamlit Cloud sono un incubo, e come l'ho risolto in 5 minuti con Claude")
- Una stat sull'app (es. "In 7 giorni l'app ha tracciato X eventi, ecco i 3 più interessanti")

Mantenere il ritmo è più importante del singolo post virale.

---

# POST 2 — Follow-up (una settimana dopo)

## Versione consigliata (italiano, ~210 parole)

> Una settimana fa ho pubblicato Layoff AI Monitor. Oggi voglio raccontare la parte che nessuno mostra: dove mi sono incartato.
>
> Per mettere l'app online su Streamlit Cloud serviva configurare le credenziali Firebase. Ho passato quasi un'ora a sbattere la testa: continuavo a ricevere `json.decoder.JSONDecodeError`. Provavo a incollare il JSON delle credenziali nei Secrets di Streamlit in tutti i formati possibili — virgolette singole, doppie, triple, escape dei `\n` nella private key. Niente funzionava.
>
> A un certo punto ho fatto due cose:
>
> 1. **Ho cambiato modello.** Stavo usando un Claude più piccolo, sono passato a Opus 4.7.
> 2. **Ho smesso di insistere.** Gli ho detto: "risolvi in modo definitivo, fai tutto tu".
>
> In 5 minuti la soluzione era trovata: i Secrets di Streamlit Cloud sono TOML, non JSON. Inutile incollare una stringa JSON e sperare che il parser la mastichi — meglio usare il formato TOML *table*:
>
> ```toml
> [firebase]
> type = "service_account"
> project_id = "..."
> private_key = "..."
> ```
>
> Streamlit lo restituisce direttamente come dict. Zero parsing, zero escape, zero dolore.
>
> La lezione vera non è tecnica. È: quando un approccio non funziona dopo 30 minuti, **non insistere — cambia strategia** (o modello). Il vero costo non è il tempo perso, è il momentum che si rompe.
>
> 👉 Codice e setup completo: [link al repo]

---

## Hook alternativi per il Post 2

### A — Più tecnico, per developer
> "JSON in TOML è una trappola. Ho perso un'ora prima di capirlo. Il fix sta in 4 righe."

### B — Meta, sulla collaborazione AI
> "La cosa più utile che ho imparato lavorando con un LLM non è quando ascoltarlo. È quando dirgli di smettere e cambiare strategia."

### C — Storytelling
> "'Mi hai rotto il c***o' — la frase che ho scritto a Claude prima di risolvere il mio bug. (Spoiler: ha funzionato.)"

### D — Numerico
> "60 minuti persi · 1 cambio di modello · 5 minuti per risolvere. Storia di un bug Firebase."

---

## Visual da allegare al Post 2

1. **Screenshot del before/after del file `db.py`** (la funzione `_get_credentials()`) — mostra side-by-side l'approccio JSON-string fallito vs. TOML-table funzionante. Si capisce in 2 secondi.
2. **Screenshot della chat con Claude** dove digiti "risolvi in modo definitivo" — autenticità pura. Se non vuoi mostrare la frustration vera, screenshot generico della conversazione.
3. **Snippet TOML** colorato (usa carbon.now.sh per fare un'immagine bella del blocco `[firebase]`).

---

## Hashtag Post 2 (più tecnici del primo)

```
#Firebase #Streamlit #ClaudeCode #DevOps #Python
```

Se vuoi audience italiana mainstream più larga:
```
#Programmazione #ClaudeAI #Tutorial #BugFix #DeveloperLife
```

---

## Perché questa serie funziona

I due post sono complementari:

| Post | Messaggio | Audience |
|---|---|---|
| **#1** | "Si può fare" | Curiosi, non-developer, manager |
| **#2** | "Ecco *come* si fa davvero, con i casini veri" | Developer, tech-lead, chi vuole replicare |

Insieme costruiscono credibilità: il primo attira, il secondo dimostra che non era marketing.

---

## Idee per Post #3 e #4 (se vuoi continuare)

- **#3 (2 settimane dopo)**: "Cosa ho imparato osservando 100 layoff tech con focus AI". Diventi *fonte* invece di *creatore*. Trasforma l'app in giornalismo dati.
- **#4 (1 mese dopo)**: "Il vero costo di un side-project con AI: 0€ in API, X€ in caffè. Bilancio onesto." Trasparenza assoluta sui costi → ad alta condivisibilità.
