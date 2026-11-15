"""
Support rung of a spaced-repetition card: how much help its next exercise gives.

The rungs run scaffold -> cue -> bare -> varied. A confident review (quality
4-5) fades the card one rung toward varied, a miss (quality 0-2) brings it one
rung back toward scaffold, and a hard pass (quality 3) keeps it where it is.
update-db.py moves the rung on every review; read-db.py hands every card its
rung, so the skills read one field.
"""

RUNGS = ("scaffold", "cue", "bare", "varied")


def rung_of(item):
    """The card's current rung. A card reviewed before rungs existed starts on
    cue when its last answer was confident, else on scaffold, as does a card
    never reviewed."""
    rung = item.get("rung")
    if rung in RUNGS:
        return rung
    confident = item.get("total_reviews", 0) > 0 and (item.get("last_quality") or 0) >= 4
    return "cue" if confident else "scaffold"


def next_rung(rung, quality):
    """The rung after a review of this quality (0-5)."""
    i = RUNGS.index(rung)
    if quality >= 4:
        i = min(i + 1, len(RUNGS) - 1)
    elif quality <= 2:
        i = max(i - 1, 0)
    return RUNGS[i]


if __name__ == "__main__":  # smoke self-check
    assert [next_rung("scaffold", 5), next_rung("varied", 5)] == ["cue", "varied"]
    assert [next_rung("bare", 2), next_rung("scaffold", 0), next_rung("bare", 3)] == \
        ["cue", "scaffold", "bare"]
    assert rung_of({}) == "scaffold"
    assert rung_of({"total_reviews": 2, "last_quality": 5}) == "cue"
    assert rung_of({"total_reviews": 0, "last_quality": 4}) == "scaffold"
    print("fading.py self-check OK")
