# Setup Secrets su Streamlit Cloud (Versione Definitiva)

## Procedura Automatica (consigliata)

Il TOML è già stato generato e copiato negli appunti. Devi solo:

1. Apri https://share.streamlit.io/
2. Trova l'app `layoff-monitor` → menu ⋮ → **Settings**
3. Sezione **Secrets** → clicca dentro il box
4. **Cmd+V** (incolla)
5. Clicca **Save**

L'app si riavvia in ~30 secondi e funziona.

## Se devi rifare la copia del TOML

```bash
cd "/Users/dottmatt/Desktop/CLAUDE COWORK/layoff_monitor"
cat .secrets/streamlit_secrets.toml | pbcopy
```

## Formato usato

I secrets sono in formato TOML **table** `[firebase]` (più affidabile del JSON string):

```toml
[firebase]
type = "service_account"
project_id = "ai-fires"
private_key_id = "..."
private_key = "..."
client_email = "..."
...
```

`db.py` legge questa table e la passa a `firebase_admin.credentials.Certificate()`.

## Sviluppo locale

In locale `db.py` continua a leggere automaticamente da `.secrets/ai-fires-sa.json`.
Nessuna modifica necessaria.
