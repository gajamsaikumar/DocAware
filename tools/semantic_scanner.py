from sentence_transformers import SentenceTransformer, util
import re


class SemanticScanner:
    """Performs semantic risk detection using sentence embeddings."""

    RISK_DESCRIPTIONS = [
        ("non_refundable", "The deposit or payment is non-refundable, so you might lose your money even for a valid reason."),
        ("auto_renewal", "The contract renews automatically for another term unless you cancel it in time."),
        ("long_notice_period", "You must give a very long advance notice (like 60 or 90 days) before you can cancel."),
        ("hidden_fees", "There are extra fees like administrative, processing, or convenience charges that are not obvious."),
        ("liability_waiver", "The other party limits or waives their liability, so they may not be responsible for losses."),
        ("one_sided_termination", "The contract can be terminated by the other party at any time without cause, but you may not have the same right."),
    ]

    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.risk_texts = [desc for _, desc in self.RISK_DESCRIPTIONS]
        self.risk_embeddings = self.model.encode(
            self.risk_texts,
            convert_to_tensor=True
        )

    def scan(self, text: str, threshold: float = 0.5) -> list:
        """Scan document text for semantically risky clauses."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if not sentences:
            return []

        sentence_embeddings = self.model.encode(
            sentences,
            convert_to_tensor=True
        )

        findings = []

        for i, sent_emb in enumerate(sentence_embeddings):
            similarities = util.cos_sim(
                sent_emb,
                self.risk_embeddings
            ).squeeze()

            best_idx = similarities.argmax().item()
            best_score = similarities[best_idx].item()

            if best_score >= threshold:
                category, _ = self.RISK_DESCRIPTIONS[best_idx]

                findings.append({
                    "category": category,
                    "sentence": sentences[i],
                    "score": round(best_score, 3)
                })

        findings.sort(key=lambda x: x["score"], reverse=True)
        return findings