"""Unit tests for Pydantic request and response schemas."""

import pytest
from pydantic import ValidationError

from app.models.schemas import ChatRequest, FaultCodeLookupRequest


def test_chat_request_rejects_short_question():
    """Verify that a question under 2 characters raises a validation error."""
    with pytest.raises(ValidationError):
        ChatRequest(question="A")


def test_chat_request_rejects_long_question():
    """Verify that a question over 4000 characters raises a validation error."""
    with pytest.raises(ValidationError):
        ChatRequest(question="X" * 4001)


def test_chat_request_rejects_invalid_top_k_below_minimum():
    """Verify that top_k below 1 raises a validation error."""
    with pytest.raises(ValidationError):
        ChatRequest(question="How to fix code 999?", top_k=0)


def test_chat_request_rejects_invalid_top_k_above_maximum():
    """Verify that top_k above 12 raises a validation error."""
    with pytest.raises(ValidationError):
        ChatRequest(question="How to fix code 999?", top_k=13)


def test_chat_request_rejects_invalid_mode():
    """Verify that an unsupported mode raises a validation error."""
    with pytest.raises(ValidationError):
        ChatRequest(question="Valid question text", mode="creative")


def test_fault_code_request_rejects_empty_code():
    """Verify that an empty fault code raises a validation error."""
    with pytest.raises(ValidationError):
        FaultCodeLookupRequest(code="")


def test_fault_code_request_rejects_long_code():
    """Verify that a fault code over 80 characters raises a validation error."""
    with pytest.raises(ValidationError):
        FaultCodeLookupRequest(code="E" * 81)
