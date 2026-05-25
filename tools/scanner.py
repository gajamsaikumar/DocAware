import re


class RiskScorer:
    """Handles regex-based risk detection and document risk scoring."""

    RED_FLAGS = [
        ("non_refundable", r"(non[-\s]?refundable|no refund)", "Non-refundable payment or deposit"),
        ("auto_renewal", r"(auto[-\s]?renewal|automatic\s+renewal|automatically\s+renew|renews\s+automatically)", "Automatic renewal"),
        ("long_notice_period", r"(\d{2,3}[-\s]?days?\s*(?:prior\s)?written?\s*notice)", "Long notice period"),
        ("hidden_fees", r"(administrative fee|processing fee|convenience fee|additional charge|service charge)", "Potential hidden fee"),
        ("liability_waiver", r"(not\s+liable|waive\s+(any|all)\s+liability|limitation\s+of\s+liability)", "Liability waiver"),
        ("one_sided_termination", r"(terminate\s+(this\s+)?agreement\s+(at\s+any\s+time|without\s+cause|with\s+immediate\s+effect))", "One-sided termination"),
        ("cancellation_fee", r"(cancellation fee|termination fee|early exit fee|exit charge)", "Cancellation fee"),
        ("unilateral_changes", r"(reserve the right to change|may modify terms at any time|terms may change without notice)", "One-sided changes"),
        ("price_increase", r"(price may increase|fees may be increased|charges may change)", "Price increase"),
        ("data_privacy", r"(share your data|third[-\s]?party data sharing|personal data may be shared)", "Data privacy concern"),
        ("indemnity", r"(indemnify|hold harmless)", "Broad indemnity"),
        ("penalty_clause", r"(penalty charge|financial penalty|breach fee)", "Penalty clause")
    ]

    SEVERITY = {
        "non_refundable": "High",
        "auto_renewal": "High",
        "liability_waiver": "High",
        "one_sided_termination": "High",
        "indemnity": "High",

        "long_notice_period": "Medium",
        "hidden_fees": "Medium",
        "data_privacy": "Medium",
        "price_change": "Medium",
        "debt_recovery": "Medium",
        "unilateral_changes": "Medium",
        "cancellation_fee": "Medium",
        "penalty_clause": "Medium",
    }       

    def scan(self, page_texts: list) -> list:
        """Run regex-based red flag detection."""
        findings = []

        for page_num, page_content in page_texts:
            lines = page_content.splitlines()

            for line_num, line in enumerate(lines, start=1):
                for category, pattern, label in self.RED_FLAGS:
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

    def calculate_score(self, flags: list) -> dict:
        """Calculate overall document risk score."""
        if not flags:
            return {"level": "Low", "score": 0, "breakdown": {}}

        severity_to_points = {"High": 3, "Medium": 2, "Low": 1}
        total = 0
        breakdown = {"High": 0, "Medium": 0, "Low": 0}

        for flag in flags:
            severity = self.SEVERITY.get(flag.get("category", ""), "Low")
            breakdown[severity] += 1
            total += severity_to_points[severity]

        max_possible = len(flags) * 3
        score = min(
            round((total / max_possible) * 10) if max_possible > 0 else 0,
            10
        )

        if score >= 7:
            level = "High"
        elif score >= 4:
            level = "Medium"
        else:
            level = "Low"

        return {
            "level": level,
            "score": score,
            "breakdown": breakdown
        }