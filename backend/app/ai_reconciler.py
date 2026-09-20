import os
import json
import re
from typing import Dict, Any, List, Optional
import httpx
from .models import Project, EvidenceSubmission

SYSTEM_PROMPT = """You are the MkatabaWatch Public Procurement Reconciliation Engine for Tanzanian public contracts.
Your role is to compare official public procurement claims with evidence submitted by community monitors and citizens.

CRITICAL SAFETY & INTEGRITY DIRECTIVES:
1. NEVER accuse any contractor, government entity, or person of corruption, fraud, theft, bribery, or illegal conduct.
2. NEVER state a violation or wrongdoing as an established fact.
3. You only perform factual discrepancy identification between stated contractual parameters (dates, values, progress) and observed physical evidence.
4. If observations suggest physical work is behind the official expected timeline, use neutral, objective terminology: "discrepancy noted between observed construction milestone and expected completion date", "independent field verification recommended".
5. Always maintain the presumption of administrative delay, weather disruptions, or data reporting lag rather than misconduct.
6. Your response MUST be valid JSON adhering strictly to this schema:
{
  "status": "consistent" | "discrepancy_flagged" | "needs_more_evidence",
  "confidence": "low" | "medium" | "high",
  "supporting_points": ["point 1", "point 2"],
  "concerning_points": ["point 1", "point 2"],
  "summary": "1-2 sentence plain-language explanation.",
  "recommendation": "Independent field verification recommended." | "No discrepancy detected at this time." | "Insufficient evidence to assess."
}
"""

FORBIDDEN_ACCUSATION_WORDS = [
    "corrupt", "corruption", "fraud", "fraudulent", "embezzle", "embezzlement",
    "bribe", "bribery", "stole", "stealing", "criminal", "crime", "illegal", "guilty", "thief"
]

def sanitize_reconciliation_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validates that the output strictly follows safety constraints and contains no defamatory accusations."""
    text_content = (
        data.get("summary", "") + " " +
        " ".join(data.get("supporting_points", [])) + " " +
        " ".join(data.get("concerning_points", [])) + " " +
        data.get("recommendation", "")
    ).lower()

    for word in FORBIDDEN_ACCUSATION_WORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_content):
            # Replace / sanitize to neutral phrasing
            data["summary"] = re.sub(
                r'\b' + re.escape(word) + r'\b',
                "discrepancy requiring review",
                data.get("summary", ""),
                flags=re.IGNORECASE
            )
            data["recommendation"] = "Independent field verification recommended."

    # Enforce allowed status and recommendation enums
    if data.get("status") not in ["consistent", "discrepancy_flagged", "needs_more_evidence"]:
        data["status"] = "needs_more_evidence"

    if data.get("confidence") not in ["low", "medium", "high"]:
        data["confidence"] = "medium"

    if data.get("recommendation") not in [
        "Independent field verification recommended.",
        "No discrepancy detected at this time.",
        "Insufficient evidence to assess."
    ]:
        if data["status"] == "discrepancy_flagged":
            data["recommendation"] = "Independent field verification recommended."
        elif data["status"] == "consistent":
            data["recommendation"] = "No discrepancy detected at this time."
        else:
            data["recommendation"] = "Insufficient evidence to assess."

    return data


async def reconcile_with_llm(project: Project, evidence_items: List[EvidenceSubmission]) -> Dict[str, Any]:
    """Reconciles official project records with community evidence using an LLM (Claude API or OpenAI) with fallback."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    user_prompt = f"""
OFFICIAL PROCUREMENT RECORD:
- OCID: {project.ocid}
- Project Title: {project.title}
- Procuring Entity: {project.buyer}
- Contractor: {project.contractor}
- Contract Value: {project.currency} {project.contract_value:,.2f}
- Location / Region: {project.location_name or project.region}
- Contract Period: Start {project.start_date or 'N/A'}, Expected Completion {project.expected_completion_date or 'N/A'} (Duration: {project.duration_days or 'N/A'} days)
- Official Reported Status: {project.official_status}
- Official Reported Progress: {str(project.official_reported_progress) + '%' if project.official_reported_progress is not None else 'Not reported in official feed'}

COMMUNITY EVIDENCE SUBMISSIONS ({len(evidence_items)} report(s)):
"""
    for idx, e in enumerate(evidence_items, 1):
        user_prompt += f"""
Evidence #{idx} (ID: {e.id}):
- Observation Type: {e.observation_type}
- Submitted By: {e.submitted_by} ({e.provenance})
- Timestamp: {e.timestamp}
- Coordinates: Lat {e.gps_lat}, Lng {e.gps_lng}
- Description: {e.description}
- Has Photo: {'Yes' if e.photo_url else 'No'}
- Seeded Demo Data: {'Yes' if e.is_seeded_demo_data else 'No'}
"""

    user_prompt += "\nEvaluate whether the submitted community observations align with the official contract scope, timeline, and deliverables. Return ONLY JSON."

    # 1. Try Anthropic Claude API if key exists and isn't placeholder
    if api_key and not api_key.startswith("your_"):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 1000,
                        "system": SYSTEM_PROMPT,
                        "messages": [{"role": "user", "content": user_prompt}]
                    }
                )
                if res.status_code == 200:
                    payload = res.json()
                    content = payload["content"][0]["text"]
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        parsed = json.loads(json_match.group(0))
                        return sanitize_reconciliation_output(parsed)
        except Exception as err:
            print(f"[AI Reconciler] Anthropic API failed: {err}. Falling back to rule-based analysis.")

    # 2. Try OpenAI API if key exists and isn't placeholder
    if openai_key and not openai_key.startswith("your_"):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openai_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "response_format": {"type": "json_object"}
                    }
                )
                if res.status_code == 200:
                    payload = res.json()
                    content = payload["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return sanitize_reconciliation_output(parsed)
        except Exception as err:
            print(f"[AI Reconciler] OpenAI API failed: {err}. Falling back to rule-based analysis.")

    # 3. Deterministic Heuristic Engine (Guarantees demo works smoothly offline/without API keys)
    return run_heuristic_reconciliation(project, evidence_items)


def run_heuristic_reconciliation(project: Project, evidence_items: List[EvidenceSubmission]) -> Dict[str, Any]:
    """Deterministic, objective rule engine that operates in strict compliance with transparency guidelines."""
    if not evidence_items:
        return {
            "status": "needs_more_evidence",
            "confidence": "low",
            "supporting_points": ["Official contract details recorded from NeST portal."],
            "concerning_points": ["No on-the-ground community evidence has been recorded for this contract yet."],
            "summary": "This project currently has an official procurement record but no on-site community monitoring reports.",
            "recommendation": "Insufficient evidence to assess."
        }

    discrepancy_signals = []
    consistency_signals = []
    concerning_types = ["not_started", "delayed", "incomplete", "poor_quality", "cannot_be_found"]

    for ev in evidence_items:
        if ev.observation_type in concerning_types:
            label = ev.observation_type.replace('_', ' ').title()
            discrepancy_signals.append(f"Monitor reported '{label}' on {ev.timestamp[:10] if ev.timestamp else 'recent date'}: {ev.description}")
        elif ev.observation_type == "appears_completed":
            consistency_signals.append(f"Monitor confirmed visible completion on {ev.timestamp[:10] if ev.timestamp else 'recent date'}: {ev.description}")
        else:
            consistency_signals.append(f"Field report noted: {ev.description}")

    # Check official expected completion date vs today
    if project.expected_completion_date:
        today_iso = "2026-09-20"
        if project.expected_completion_date < today_iso:
            if not consistency_signals or discrepancy_signals:
                discrepancy_signals.append(
                    f"Official contractual completion date was {project.expected_completion_date[:10]}, but on-site evidence indicates outstanding work."
                )

    if len(discrepancy_signals) > 0:
        confidence = "high" if len(discrepancy_signals) >= 2 or any(e.photo_url for e in evidence_items) else "medium"
        return sanitize_reconciliation_output({
            "status": "discrepancy_flagged",
            "confidence": confidence,
            "supporting_points": consistency_signals or [f"Contract officially awarded to {project.contractor} for {project.currency} {project.contract_value:,.2f}."],
            "concerning_points": discrepancy_signals,
            "summary": f"Notable divergence observed between the contractual schedule and {len(discrepancy_signals)} on-site community observation(s). Physical verification is warranted to ascertain ground reality.",
            "recommendation": "Independent field verification recommended."
        })
    elif len(consistency_signals) > 0:
        confidence = "high" if any(e.photo_url for e in evidence_items) else "medium"
        return sanitize_reconciliation_output({
            "status": "consistent",
            "confidence": confidence,
            "supporting_points": consistency_signals + [f"Reported field observations correspond with contractual scope ({project.title})."],
            "concerning_points": [],
            "summary": "Submitted community evidence aligns with the contractual commitments and expected milestones for this project.",
            "recommendation": "No discrepancy detected at this time."
        })
    else:
        return sanitize_reconciliation_output({
            "status": "needs_more_evidence",
            "confidence": "low",
            "supporting_points": [f"Procurement record active under {project.buyer}."],
            "concerning_points": ["Submitted reports lack sufficient verifiable technical detail."],
            "summary": "Existing evidence reports are inconclusive and require additional photographic or GPS verification.",
            "recommendation": "Insufficient evidence to assess."
        })
