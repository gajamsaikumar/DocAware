import sys
import re

# These are the risky phrases we want to find.
# Each entry has: a short name, a regular expression pattern, and a plain-English label.
RED_FLAGS = [
    ("non_refundable", r"(non[-\s]?refundable|no refund)", "Non-refundable payment or deposit"),

    ("auto_renewal",
     r"(auto[-\s]?renewal|automatic\s+renewal|automatically\s+renew|renews\s+automatically)",
     "Automatic contract renewal"),

    ("long_notice_period",
     r"(\d{2,3}[-\s]?days?\s*(?:prior\s)?written?\s*notice)",
     "Unusually long notice period"),

    ("hidden_fees",
     r"(administrative fee|processing fee|convenience fee|additional charge|service charge)",
     "Potential hidden fee"),

    ("liability_waiver",
     r"(not\s+liable|waive\s+(any|all)\s+liability|limitation\s+of\s+liability)",
     "Liability waiver or limitation"),

    ("one_sided_termination",
     r"(terminate\s+(this\s+)?agreement\s+(at\s+any\s+time|without\s+cause|with\s+immediate\s+effect))",
     "One-sided termination clause"),

    ("cancellation_fee",
     r"(cancellation fee|termination fee|early exit fee|exit charge)",
     "Excessive cancellation fee"),

    ("unilateral_changes",
     r"(reserve the right to change|may modify terms at any time|terms may change without notice)",
     "One-sided contract changes"),

    ("price_increase",
     r"(price may increase|fees may be increased|charges may change)",
     "Automatic price increase"),

    ("data_privacy",
     r"(share your data|third[-\s]?party data sharing|personal data may be shared)",
     "Data privacy concern"),

    ("indemnity",
     r"(indemnify|hold harmless)",
     "Broad indemnity clause"),

    ("penalty_clause",
     r"(penalty charge|financial penalty|breach fee)",
     "Penalty clause")
]
SEVERITY = {
    "non_refundable": "High",
    "auto_renewal": "High",
    "long_notice_period": "Medium",
    "hidden_fees": "Medium",
    "liability_waiver": "High",
    "one_sided_termination": "High",
}

def scan_text_with_pages(page_texts: list) -> list:
    findings = []
    for page_num, page_content in page_texts:
        lines = page_content.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for category, pattern, label in RED_FLAGS:
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    start = max(0, match.start() - 20)
                    end = min(len(line), match.end() + 20)
                    context = line[start:end].strip()
                    findings.append({
                        "category": category,
                        "flag": label,
                        "matched_text": match.group(),
                        "page": page_num,
                        "line": line_num,
                        "context": context
                    })
    unique = []
    seen = set()

    for item in findings:
        key = (
            item["category"],
            item["page"],
            item["matched_text"]
        )

        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique

def calculate_risk_score(flags: list) -> dict:
    """Return overall severity, score out of 10, and breakdown."""
    if not flags:
        return {"level": "Low", "score": 0, "breakdown": {}}

    severity_to_points = {"High": 3, "Medium": 2, "Low": 1}
    total = 0
    breakdown = {"High": 0, "Medium": 0, "Low": 0}
    for f in flags:
        sev = SEVERITY.get(f.get("category", ""), "Low")
        breakdown[sev] = breakdown.get(sev, 0) + 1
        total += severity_to_points.get(sev, 1)

    # Scale to 1‑10
    max_possible = len(flags) * 3
    score = min(round((total / max_possible) * 10) if max_possible > 0 else 0, 10)
    if score >= 7:
        level = "High"
    elif score >= 4:
        level = "Medium"
    else:
        level = "Low"
    return {"level": level, "score": score, "breakdown": breakdown}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/scanner.py <text_file_or_raw_text>")
        sys.exit(1)

    # If the argument is a file that exists, read it. Otherwise treat it as raw text.
    import os
    input_path = sys.argv[1]
    if os.path.isfile(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = input_path

    results = scan_text(text)
    if results:
        print(f"Found {len(results)} potential red flag(s):\n")
        for i, r in enumerate(results, 1):
            print(f"{i}. [{r['flag']}] (line {r['line']}) – \"{r['matched_text']}\"")
            print(f"   Context: ...{r['context']}...\n")
    else:
        print("No red flags detected.")