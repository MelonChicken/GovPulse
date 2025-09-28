from typing import List, Dict, Any
import yaml
from pathlib import Path

def load_endpoints(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    eps = data.get("endpoints", [])
    out = []
    for e in eps:
        out.append({"name": e["name"], "url": e["url"]})
    return out