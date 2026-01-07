import json
import requests
from rich.console import Console

console = Console()

def stream_chat(url, payload):
    with requests.post(url, json=payload, stream=True) as r:
        r.raise_for_status()
        output = ""
        for line in r.iter_lines():
            if not line:
                continue
            data = json.loads(line.decode())
            if "message" in data:
                content = data["message"].get("content", "")
                output += content
                console.print(content, end="", soft_wrap=True)
            if data.get("done"):
                console.print()
                break
        return output

def chat(url, payload):
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.json()["message"]["content"]
