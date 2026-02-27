from __future__ import annotations

from app.services.repository import fetch_all


def local_assistant_reply(prompt: str) -> str:
    prompt_l = prompt.lower()
    if "quote" in prompt_l:
        return "Use a 3-tier quote: base scope, optional upgrades, and rush fee. Clarify timeline and payment milestones."
    if "invoice" in prompt_l:
        return "Recommend 50% deposit, net-15 final payment, and late fee language after day 7."
    if "tax" in prompt_l:
        return "Set aside 20-30% of net income monthly. Track deductible expenses like software, mileage, and equipment."

    tips = fetch_all("SELECT memory FROM memories ORDER BY created_at DESC LIMIT 3")
    context = " ".join(t["memory"] for t in tips) if tips else "No stored memory context yet."
    return f"Local assistant response (offline mode). Context: {context}"
