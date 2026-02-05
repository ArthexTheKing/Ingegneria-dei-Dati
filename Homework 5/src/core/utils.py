import re
import os
import shutil

def clean_text(text):
    """Pulisce il testo da spazi multipli e whitespace."""
    if not text:
        return ""
    return " ".join(text.split())

def sanitize_filename(title):
    """Sanitizza una stringa per usarla come nome file."""
    title = str(title).replace('$', '')
    # Rimuove comandi latex base
    title = re.sub(r'\\(text|emph|textbf|textit|math[a-z]+)', '', title)
    clean_chars = str.maketrans('', '', '{}[]^\\_')
    title = title.translate(clean_chars)
    title = re.sub(r'[\\/*?:"<>|]', "", title)
    title = " ".join(title.split())
    return title[:150].strip()

def prepare_directory(path):
    """Crea o pulisce la directory di output."""
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)