**Root Cause Analysis — Logic Deadlock in Date Calculation**

- **Case**: Input: "Lập kế hoạch học tập từ nay đến 30/04."
- **Observation**: Agent invoked `date_utils(target="30/04")`; the date tool rejected the argument because it requires ISO `YYYY-MM-DD`.
- **Root Cause**: System Prompt did not instruct the agent to normalize short dates (e.g., append a 4‑digit year). The agent passed a partial date that failed tool validation.
- **Immediate Fix**: Added explicit prompt guidance and pre-call normalization in `ReActAgent._execute_tool` (see src/agent/agent.py) to convert `DD/MM` / `D-M` / `DD/MM/YY` into `YYYY-MM-DD` (defaulting to current year).
- **Impact**: Blocks scheduling workflows and can cause agent loops or early termination when date tools validate strictly.
- **Recommendations**:
  - Add input schema/validation for date tools and emit telemetry when normalization occurs.
  - Provide a shared `normalize_date()` helper in `src/tools` and/or make `date_utils` accept common human formats.
  - Add integration tests for partial dates and end-of-year edge cases.
  - Update system prompt and user docs to recommend year-inclusive dates.
