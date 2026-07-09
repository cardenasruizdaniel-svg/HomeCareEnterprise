from pathlib import Path
import json

LOG_FILE=Path("logs/auditoria.log")

def guardar_evento(evento:dict):
    LOG_FILE.parent.mkdir(exist_ok=True)
    with LOG_FILE.open("a",encoding="utf-8") as f:
        f.write(json.dumps(evento,ensure_ascii=False)+"\n")
