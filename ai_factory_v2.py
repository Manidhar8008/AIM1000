import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timedelta
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, f"manager_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
logging.getLogger().addHandler(console)

# Config
SCRIPTS = [
    ("Sniper", "python sniper_bot_v4.py", 600),
    ("Factory", "python ai_factory_v2_advanced.py", 900),
]
CSV_EXPECTED = os.path.join(ROOT, "Sniper_Hourly_Leads.csv")
MISSION_CONTROL = os.path.join(ROOT, "Mission_Control.html")
CYCLE_INTERVAL_SECONDS = 4 * 60  # run every 4 minutes
MAX_RETRIES = 2

def run_command(name, cmd, timeout):
    logging.info("Running step: %s -> %s", name, cmd)
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        logging.info("%s stdout:\n%s", name, proc.stdout.strip())
        if proc.stderr:
            logging.warning("%s stderr:\n%s", name, proc.stderr.strip())
        if proc.returncode != 0:
            logging.error("%s failed with code %s", name, proc.returncode)
            return False
        logging.info("%s completed successfully", name)
        return True
    except subprocess.TimeoutExpired:
        logging.error("%s timed out after %s seconds", name, timeout)
        return False
    except Exception as e:
        logging.exception("Exception while running %s: %s", name, e)
        return False

def validate_csv(path):
    if not os.path.exists(path):
        logging.warning("Expected CSV not found: %s", path)
        return False
    try:
        import pandas as pd
        df = pd.read_csv(path)
        if df.empty:
            logging.warning("CSV exists but is empty: %s", path)
            return False
        # minimal columns check
        for col in ("Job Title", "Company", "Apply Link"):
            if col not in df.columns:
                logging.warning("CSV missing expected column '%s'", col)
                return False
        # drop NaNs and empty rows
        df = df.dropna(subset=['Job Title', 'Company'], how='any')
        df['Job Title'] = df['Job Title'].astype(str).str.strip()
        df['Company'] = df['Company'].astype(str).str.strip()
        df = df[(df['Job Title'] != "") & (df['Company'] != "")]
        if df.empty:
            logging.warning("CSV has no valid rows after cleaning.")
            return False
        return True
    except Exception as e:
        logging.exception("Error validating CSV: %s", e)
        return False

def open_tracker():
    if os.path.exists(MISSION_CONTROL):
        try:
            logging.info("Opening tracker: %s", MISSION_CONTROL)
            os.startfile(os.path.abspath(MISSION_CONTROL))
        except Exception:
            logging.exception("Failed to open Mission_Control.html (os.startfile)")

def run_cycle():
    logging.info("===== CYCLE START =====")
    for name, cmd, timeout in SCRIPTS:
        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            logging.info("Step %s attempt %d/%d", name, attempt, MAX_RETRIES)
            if run_command(name, cmd, timeout):
                success = True
                break
            logging.warning("Retrying %s (attempt %d)", name, attempt + 1)
            time.sleep(3)
        if not success:
            logging.error("Step '%s' failed after %d attempts — aborting cycle", name, MAX_RETRIES)
            return False

        # after sniper step, ensure CSV exists & is valid
        if name.lower().startswith("sniper"):
            if not validate_csv(CSV_EXPECTED):
                logging.error("CSV validation failed after sniper. Aborting cycle.")
                return False

    # open mission control if created
    open_tracker()
    logging.info("===== CYCLE END =====")
    return True

def main_loop():
    logging.info("Autopilot manager started. Interval: %d seconds", CYCLE_INTERVAL_SECONDS)
    # initial run
    run_cycle()
    next_run = datetime.now() + timedelta(seconds=CYCLE_INTERVAL_SECONDS)
    while True:
        now = datetime.now()
        if now >= next_run:
            run_cycle()
            next_run = now + timedelta(seconds=CYCLE_INTERVAL_SECONDS)
        time.sleep(5)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logging.info("Shutdown requested by user.")
    except Exception:
        logging.exception("Unexpected manager crash.")