def recall_for_question(c, question):
    cm = c.get("compressed_memory", [])
    if cm:
        top = cm[-1]
        return {
            "spoken_out_loud": top.get("summary_belief", "I remember it vaguely."),
            "confidence": float(top.get("confidence_in_memory", 0.5)),
            "volatility": float(top.get("volatility", 0.3))
        }
    return {"spoken_out_loud": f"I don't remember much about '{question}'.", "confidence": 0.3, "volatility": 0.5}
