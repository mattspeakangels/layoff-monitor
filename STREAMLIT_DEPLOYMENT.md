# Deployment su Streamlit Cloud

## Istruzioni Rapide

1. Vai su https://streamlit.io/cloud
2. Accedi con il tuo account GitHub
3. Fai click su **"New app"**
4. Seleziona:
   - Repository: `mattspeakangels/layoff-monitor`
   - Branch: `main`
   - Main file path: `app.py`
5. Fai click su **"Deploy"**

## Configurare i Secrets

Dopo il deploy, vai su **Settings → Secrets**:

1. Apri l'editor dei secrets
2. Incolla il JSON delle credenziali Firebase con questa struttura:

```toml
FIREBASE_CREDENTIALS = """{"type": "service_account", "project_id": "ai-fires", ...}"""
```

**Dove prendere il JSON:**
- Il file `.secrets/ai-fires-sa.json` è nel tuo repo locale
- Copia il contenuto completo di quel file e incollalo tra le triple virgolette
- Mantieni la struttura TOML: `FIREBASE_CREDENTIALS = """<JSON_COMPLETO_QUI>"""`

3. Fai click su **"Save"**

L'app si aggiornerà automaticamente e userai i secrets di Streamlit Cloud.

## Note

- Il file `.secrets/ai-fires-sa.json` è usato solo in sviluppo locale
- Per il cloud, i secrets vanno configurati nel dashboard di Streamlit
- Il `.gitignore` esclude `.secrets/` e `.streamlit/secrets.toml`
