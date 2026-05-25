#!/usr/bin/env python3
"""Standalone ETL runner per GitHub Actions / cron / esecuzione manuale.

Uso:
    python scripts/cron_etl.py [days_back]

Default: days_back=90. Esce con codice != 0 se la pipeline fallisce.

Streamlit è importato dai moduli sottostanti ma le sue chiamate (st.spinner,
st.warning, st.cache_data) sono no-op quando lo script non gira dentro
un'app, quindi non c'è bisogno di un context fittizio.
"""

from __future__ import annotations

import os
import sys
import time

# Permetti `import db` quando lo script è lanciato da una working dir diversa
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def main() -> int:
    days_back = int(sys.argv[1]) if len(sys.argv) > 1 else 90

    print(f"[cron-etl] Starting ETL pipeline (days_back={days_back})", flush=True)
    started = time.time()

    # Import qui (non a top-level) così se le credenziali mancano il messaggio
    # di errore sopra è già stato stampato.
    from etl import run_etl

    stats = run_etl(days_back=days_back)
    elapsed = time.time() - started

    print(f"[cron-etl] Done in {elapsed:.1f}s", flush=True)
    print(f"[cron-etl]   fetched: {stats['total_fetched']}", flush=True)
    print(f"[cron-etl]   scored:  {stats['total_scored']}", flush=True)
    print(f"[cron-etl]   written: {stats['total_written']}", flush=True)

    if stats["errors"]:
        print("[cron-etl] ERRORS:", flush=True)
        for err in stats["errors"]:
            print(f"  - {err}", flush=True)
        # Fallisci solo se NESSUN evento è stato fetchato (problema upstream).
        # Errori parziali (es. una fonte RSS down) non devono rompere il job.
        if stats["total_fetched"] == 0:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
