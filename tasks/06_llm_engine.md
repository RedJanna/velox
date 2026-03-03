# Task 06: LLM Engine (OpenAI GPT + Function Calling)

> **BEFORE YOU START — Read these skill files:**
> - `skills/coding_standards.md`
> - `skills/anti_hallucination.md`
> - `skills/error_handling.md`

## Objective
Implement the LLM integration layer: OpenAI client, system prompt assembly, response parsing, and function/tool definitions for function calling.

## Reference
- `docs/master_prompt_v2.md` — A1-A13 (entire runtime spec)
- `src/velox/config/constants.py` — Intent, State, RiskFlag enums
- `src/velox/models/conversation.py` — InternalJSON, LLMResponse models

## Files to Create/Modify

### 1. `src/velox/llm/client.py`

OpenAI async client wrapper.

```python
from openai import AsyncOpenAI

class LLMClient:
    def __init__(self, settings):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.primary_model = settings.openai_model          # gpt-4o
        self.fallback_model = settings.openai_fallback_model # gpt-4o-mini
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

    async def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
    ) -> dict:
        """Send chat completion request with retry and fallback."""
        # Try primary model
        # On rate limit (429) or timeout: wait + retry (max 2 retries)
        # On 3rd failure: try fallback model
        # On fallback failure: raise LLMUnavailableError
        # Track token usage (prompt_tokens, completion_tokens)

    async def chat_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> tuple[str, list[dict]]:
        """Chat with function calling. Returns (content, tool_calls)."""
        # If response has tool_calls: return them for execution
        # If response has content: return it as final response
        # Handle parallel tool calls
```

### 2. `src/velox/llm/prompt_builder.py`

Assembles the full system prompt for each conversation turn.

```python
class PromptBuilder:
    def __init__(self, hotel_profile, escalation_matrix, template_library):
        self.hotel_profile = hotel_profile
        self.escalation_matrix = escalation_matrix
        self.template_library = template_library

    def build_system_prompt(self, hotel_id: int) -> str:
        """Build complete system prompt."""
        # Combine:
        # 1. A section from master_prompt (role, language, tone, rules)
        #    - This is the STATIC part, loaded once at startup
        # 2. HOTEL_PROFILE data (dynamic per hotel)
        # 3. FACILITY_POLICIES (from hotel profile)
        # 4. ESCALATION_MATRIX summary
        # 5. TEMPLATE_LIBRARY references
        # 6. FAQ_DATA summary
        # Keep total system prompt under ~8000 tokens

    def build_messages(
        self,
        conversation: Conversation,
        new_user_message: str,
        system_events: list[dict] | None = None,
    ) -> list[dict]:
        """Build OpenAI messages array."""
        messages = []
        # 1. System message (build_system_prompt)
        # 2. Conversation history (last 20 messages)
        #    - If >20 messages: prepend summary of older messages
        # 3. System events (approval.updated, payment.updated) as system messages
        # 4. New user message
        # 5. Instruction: "Respond with USER_MESSAGE and INTERNAL_JSON"
        return messages

    def summarize_old_messages(self, messages: list[Message]) -> str:
        """Create summary of messages beyond context window."""
        # Simple: extract key entities and last intent
```

### 3. `src/velox/llm/response_parser.py`

Parse LLM output into structured data.

```python
class ResponseParser:
    @staticmethod
    def parse(raw_content: str) -> LLMResponse:
        """Parse LLM response into USER_MESSAGE + INTERNAL_JSON."""
        # Strategy 1: Look for ```json ... ``` block for INTERNAL_JSON
        # Strategy 2: Look for "INTERNAL_JSON:" marker
        # Strategy 3: Try to parse entire response as JSON
        # Fallback: Use raw content as USER_MESSAGE, empty INTERNAL_JSON

    @staticmethod
    def validate_internal_json(data: dict) -> InternalJSON:
        """Validate and coerce INTERNAL_JSON into Pydantic model."""
        # Use InternalJSON model with defaults for missing fields

    @staticmethod
    def extract_tool_calls(internal_json: InternalJSON) -> list[dict]:
        """Extract tool calls from INTERNAL_JSON for execution."""
```

### 4. `src/velox/llm/function_registry.py`

OpenAI function calling tool definitions.

```python
def get_tool_definitions() -> list[dict]:
    """Return all tool definitions for OpenAI function calling."""
    return [
        # booking.availability
        {
            "type": "function",
            "function": {
                "name": "booking_availability",
                "description": "Check room availability for given dates and guest count",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hotel_id": {"type": "integer"},
                        "checkin_date": {"type": "string", "format": "date"},
                        "checkout_date": {"type": "string", "format": "date"},
                        "adults": {"type": "integer"},
                        "chd_count": {"type": "integer", "default": 0},
                        "chd_ages": {"type": "array", "items": {"type": "integer"}},
                        "currency": {"type": "string", "default": "EUR"}
                    },
                    "required": ["hotel_id", "checkin_date", "checkout_date", "adults"]
                }
            }
        },
        # booking_quote, stay_create_hold, booking_create_reservation,
        # booking_get_reservation, booking_modify, booking_cancel,
        # restaurant_availability, restaurant_create_hold,
        # restaurant_confirm, restaurant_modify, restaurant_cancel,
        # transfer_get_info, transfer_create_hold,
        # transfer_confirm, transfer_modify, transfer_cancel,
        # approval_request, payment_request_prepayment,
        # notify_send, handoff_create_ticket, crm_log, faq_lookup
        # ... (define all tools with full JSON Schema parameters)
    ]
```

Define ALL tools listed in master_prompt_v2.md sections A8.1-A8.5.

## Pipeline Flow
```
User message arrives
    |
    v
PromptBuilder.build_messages(conversation, user_msg)
    |
    v
LLMClient.chat_with_tools(messages, tools)
    |
    v
If tool_calls returned:
    Execute tools -> Append results -> Call LLM again
    (loop until no more tool_calls or max 5 iterations)
    |
    v
ResponseParser.parse(final_content)
    |
    v
LLMResponse(user_message, internal_json)
```

## Important Notes
- System prompt must NOT include sensitive data (real phone numbers, API keys)
- INTERNAL_JSON is NEVER sent to the user
- Tool results are appended as "tool" role messages for multi-turn tool calling
- Max 5 tool call iterations per user message to prevent infinite loops
- Log token usage for cost tracking

## Expected Outcome
- LLM receives full context and returns structured responses
- Function calling works for all defined tools
- Responses are reliably parsed into USER_MESSAGE + INTERNAL_JSON
- Fallback model kicks in when primary is unavailable
