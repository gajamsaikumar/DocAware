import json
import subprocess


def run_openclaw_scan(file_path: str) -> list:
    try:
        result = subprocess.run(
            ["openclaw", "agent", "--agent", "main", "--config", "openclaw.yaml",
             "--message", f"Please extract the text from {file_path} and then scan it for red flags. Return the results as a JSON list of objects with keys: category, flag, matched_text, page, line."],
            capture_output=True, text=True, timeout=20,check=False
        )
        if result.returncode == 0:
            raw = result.stdout.strip()
            js, je = raw.find("["), raw.rfind("]") + 1
            if js != -1 and je != -1:
                flags = json.loads(raw[js:je])
                if isinstance(flags, list):
                    return flags
        return []
    except Exception:
        return []