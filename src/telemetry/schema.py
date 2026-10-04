from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class OperationType(str, Enum):
    AGENT_MESSAGE = "AGENT_MESSAGE"
    TOOL_INVOCATION = "TOOL_INVOCATION"
    TOOL_RESPONSE = "TOOL_RESPONSE"
    CAPABILITY_CHECK = "CAPABILITY_CHECK"
    POLICY_ENFORCEMENT = "POLICY_ENFORCEMENT"
    RISK_EVALUATION = "RISK_EVALUATION"


class OutcomeType(str, Enum):
    SUCCESS = "SUCCESS"
    BLOCKED = "BLOCKED"
    REALIGNED = "REALIGNED"
    FAILED = "FAILED"
    PENDING = "PENDING"


class TelemetryEvent(BaseModel):
    """Structured Telemetry Model for M2M Agentic Interactions."""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    session_id: str = Field(..., description="Unique run/session ID")
    agent_id: str = Field(..., description="ID of the acting agent")
    parent_agent: Optional[str] = Field(
        default=None, description="ID of parent/delegating agent if applicable"
    )
    tool_id: Optional[str] = Field(
        default=None, description="ID of invoked tool if applicable"
    )
    operation: OperationType = Field(..., description="Type of operation performed")
    requested_capability: Optional[str] = Field(
        default=None, description="Capability requested for operation/tool"
    )
    granted_capability: bool = Field(
        default=True, description="Whether capability check was granted"
    )
    outcome: OutcomeType = Field(
        default=OutcomeType.SUCCESS, description="Result outcome of operation"
    )
    text_context: str = Field(
        default="",
        description="Observable agent message, tool input/output, or context summary (NO private chain-of-thought)",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metrics, graph transition tags, or risk scores",
    )
