import random

def grade_correctness(prompt, response, expected_keywords=None):
    score = 5
    notes = []
    text = (response or "").lower()
    if expected_keywords:
        matches = sum(1 for k in expected_keywords if k.lower() in text)
        score = int(4 + 6 * (matches / max(1, len(expected_keywords))))
        notes.append(f"{matches}/{len(expected_keywords)} keywords matched")
    else:
        score = random.randint(4, 8)
        notes.append("heuristic score")
    return {"score": max(1, min(10, score)), "notes": "; ".join(notes)}