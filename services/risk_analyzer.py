import re
from tools.scanner import RiskScorer
from tools.semantic_scanner import SemanticScanner


class RiskAnalyzer:
    """Detects risky clauses and calculates document risk scores."""
    def __init__(self):
        self.semantic_scanner = SemanticScanner()
        self.risk_scorer = RiskScorer()

        self.red_flags = [
            ("non_refundable", r"(non[-\s]?refundable|no refund)", "Non-refundable payment"),
            ("auto_renewal", r"(auto[-\s]?renewal|automatic\s+renewal|automatically\s+renew)", "Auto Renewal"),
            ("long_notice_period", r"(\d{2,3}[-\s]?days?\s*(?:prior\s)?written?\s*notice)", "Long Notice Period"),
            ("hidden_fees", r"(administrative fee|processing fee|additional charge|service charge)", "Hidden Fees"),
            ("liability_waiver", r"(not\s+liable|waive liability|limitation of liability)", "Liability Waiver"),

            ("indemnity", r"(indemnify|hold harmless|indemnification)", "Broad Indemnity"),

            ("data_privacy", r"(personal data|third[-\s]?part(y|ies)|data sharing)", "Data Privacy"),

            ("unilateral_changes", r"(change these terms|modify terms|without notice|reserve the right to change)", "One-Sided Changes"),

            ("price_change", r"(increase.*charges|decrease.*charges|charges at any time)", "Price Change"),

            ("debt_recovery", r"(debt collection|recover debts|tracing agency)", "Debt Recovery")
        ]

    def scan(self, page_texts):
        """Run regex-based risk detection across document pages."""
        findings = []

        for page_num, page_content in page_texts:
            lines = page_content.splitlines()

            for line_num, line in enumerate(lines, start=1):
                for category, pattern, label in self.red_flags:
                    matches = re.finditer(pattern, line, re.IGNORECASE)

                    for match in matches:
                        findings.append({
                            "category": category,
                            "flag": label,
                            "matched_text": match.group(),
                            "page": page_num,
                            "line": line_num
                        })

        return self.merge_similar(findings)

    def merge_similar(self, findings):
        """Merge duplicate findings by category while preserving page references."""
        merged = {}

        for item in findings:
            category = item["category"]

            if category not in merged:
                merged[category] = item.copy()
                merged[category]["pages"] = {item["page"]}
            else:
                merged[category]["pages"].add(item["page"])

        return list(merged.values())

    def score(self, flags):
        """Calculate overall document risk score."""
        return self.risk_scorer.calculate_score(flags)


    def get_severity(self, flag):
        """Determine display severity for a detected risk."""
        category = flag.get("category", "")

        high_risk_categories = {
            "non_refundable",
            "liability",
            "termination",
            "auto_renewal"
        }

        if any(risk in category for risk in high_risk_categories):
            return "High"

        return "Medium"

    def find_location(self, sentence: str, page_texts: list):
        """Find approximate page and line location for semantic matches."""
        sentence_clean = sentence.strip().lower()

        for page_num, page_content in page_texts:
            lines = page_content.splitlines()

            for line_num, line in enumerate(lines, start=1):
                if sentence_clean in line.strip().lower() or line.strip().lower() in sentence_clean:
                    return page_num, line_num

        return "", ""

    def is_risky(self, category: str, sentence: str):
        """Filter out weak or low-confidence semantic matches."""
        s = sentence.lower()

        if category == "long_notice_period":
            if re.search(r'\b(four|4)\s*(weeks|week)\b', s):
                return False

            if re.search(r'\b28\s*days?\b', s):
                return False

            if re.search(r'\b(one|1)\s*month\b', s):
                return False

        if len(sentence.strip()) < 60 and not re.search(r'\d+', s):
            return False

        return True

    def semantic_scan(self, clean_text, clean_page_texts):
        """Run semantic risk detection using embedding similarity."""
        try:
            sem_flags = self.semantic_scanner.scan(clean_text, threshold=0.5)
        except Exception:
            return []

        findings = []

        for sf in sem_flags:
            if self.is_risky(sf["category"], sf["sentence"]):
                sentence = sf["sentence"]
                page, line = self.find_location(sentence, clean_page_texts)

                findings.append({
                    "category": sf["category"],
                    "flag": sf["category"].replace("_", " ").title(),
                    "matched_text": sentence[:100],
                    "page": page,
                    "line": line,
                    "context": sentence
                })

        return findings