def get_bot_response(user_input):
    text = user_input.lower().strip()

    # ---------------- POLITE RESPONSES ----------------
    if "thank" in text:
        return ("😊 You're welcome!\n"
                "If you have any allergy concerns, feel free to ask.")

    if "thanks" in text:
        return ("😊 Happy to help!\n"
                "Let me know if you experience any symptoms.")

    if text in ["ok", "okay"]:
        return ("👍 Alright.\n"
                "I'm here if you need further assistance.")

    if "bye" in text:
        return ("👋 Goodbye!\n"
                "Stay safe and take care of your health.")

    # ---------------- EMERGENCY DETECTION ----------------
    emergency_keywords = [
        "breathing problem",
        "can't breathe",
        "swelling",
        "throat closing",
        "chest pain",
        "severe reaction",
        "anaphylaxis"
    ]

    for word in emergency_keywords:
        if word in text:
            return ("⚠️ EMERGENCY ALERT!\n"
                    "Your symptoms may indicate a severe allergic reaction.\n"
                    "Please seek immediate medical attention immediately.\n\n"
                    "This system is not a replacement for professional medical care.")

    # ---------------- FOOD ALLERGY ----------------
    if "milk" in text or "peanut" in text or "egg" in text:
        return ("It looks like you may have a food allergy.\n"
                "Avoid consuming suspected foods.\n"
                "Read ingredient labels carefully.\n"
                "Consult an allergist for testing.\n\n"
                "⚕️ Educational guidance only.")

    # ---------------- SKIN ALLERGY ----------------
    if "rash" in text or "itching" in text or "redness" in text:
        return ("Skin allergy symptoms detected.\n"
                "Avoid scratching.\n"
                "Use mild moisturizers.\n"
                "Avoid chemical cosmetics.\n\n"
                "⚕️ Consult a doctor if symptoms persist.")

    # ---------------- ENVIRONMENTAL ALLERGY ----------------
    if "dust" in text or "pollen" in text or "smoke" in text:
        return ("Environmental allergy suspected.\n"
                "Avoid dusty areas.\n"
                "Use masks outdoors.\n"
                "Keep windows closed during pollen season.\n\n"
                "⚕️ Medical consultation recommended.")

    # ---------------- GENERAL ALLERGY INFO ----------------
    if "symptom" in text or "allergy" in text:
        return ("Allergy symptoms may include:\n"
                "- Sneezing\n"
                "- Skin rash\n"
                "- Breathing difficulty\n"
                "- Swelling\n\n"
                "Please describe your symptoms clearly.")

    # ---------------- DEFAULT RESPONSE ----------------
    return ("I am your AI Allergy Assistant.\n"
            "Please describe your symptoms clearly.\n"
            "Example: 'I have skin rash and itching'.")
