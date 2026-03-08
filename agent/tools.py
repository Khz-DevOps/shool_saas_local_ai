import json
import logging
from langchain_core.tools import tool
from agent.responses import INTENT_RESPONSES

log = logging.getLogger("agent")


@tool
def get_school_intent_response(
    query: str,
    intent: str,
    entities: dict,
    confidence: float,
    response_language: str,
    in_scope: bool,
) -> str:
    """Return a predefined response for a given school-related user intent.

    Args:
        query: User query after AI reconstruction according to context.
        intent: The classified intent name from the supported intents list.
        entities: Extracted entities with childernName (list of strings)
                  and complainReason (string).
        confidence: Confidence score of the identified intent in range [0, 1].
        response_language: Language to respond in, matching the user's language (ar/en).
        in_scope: True if the query is within domain scope, False otherwise.

    Returns:
        JSON string with intent and intentAnswer fields.
    """
    log.info(
        "get_school_intent_response  intent=%r  lang=%r  confidence=%.2f  in_scope=%s",
        intent, response_language, confidence, in_scope,
    )

    answer = INTENT_RESPONSES.get(intent) or INTENT_RESPONSES.get("unknown", "")

    result = {
        "intent": intent,
        "query": query,
        "intentAnswer": answer,
        "entities": entities,
        "confidence": confidence,
        "in_scope": in_scope,
    }
    log.debug("tool response  intent=%r  answer_len=%d", intent, len(answer))
    return json.dumps(result, ensure_ascii=False)
