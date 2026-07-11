"""Guardrails: input sanitization, PII redaction for logs, and output validation.

Kept lightweight and deterministic - these run on every request, so no LLM calls.
"""

from __future__ import annotations

import re

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WS = re.compile(r"[ \t]{3,}")

# PII patterns for log redaction (best-effort; not a substitute for a DLP system).
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"\b(?:\+?\d[\d\s().-]{7,}\d)\b")
_CC = re.compile(r"\b(?:\d[ -]?){13,16}\b")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

MAX_INPUT_CHARS = 8000


def clean_user_text(text: str) -> str:
    """Sanitize inbound user text: strip control chars, cap length, tidy whitespace."""
    if not isinstance(text, str):
        return ""
    text = _CONTROL.sub("", text)
    text = _WS.sub("  ", text)
    text = text.strip()
    return text[:MAX_INPUT_CHARS]


def redact_pii(text: str) -> str:
    """Mask emails, phone numbers, card- and SSN-like sequences for safe logging."""
    if not isinstance(text, str) or not text:
        return text
    text = _EMAIL.sub("[email]", text)
    text = _SSN.sub("[ssn]", text)
    text = _CC.sub(lambda m: "[card]" if len(re.sub(r"\D", "", m.group())) >= 13 else m.group(), text)
    text = _PHONE.sub(lambda m: "[phone]" if len(re.sub(r"\D", "", m.group())) >= 9 else m.group(), text)
    return text


def redact_pii_processor(_logger, _name, event_dict):
    """structlog processor: redact PII from string values in log events."""
    for k, v in list(event_dict.items()):
        if isinstance(v, str):
            event_dict[k] = redact_pii(v)
    return event_dict
