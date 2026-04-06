import os

from src.core.openai_provider import OpenAIProvider
from src.core.local_provider import LocalProvider
from src.core.gemini_provider import GeminiProvider
from src.telemetry.logger import logger
import uuid

DEFAULT = os.getenv("DEFAULT_PROVIDER","local")
RUN_ID = os.getenv("RUN_ID", str(uuid.uuid4())[:8])
PROMPT = """Mình muốn ứng tuyển vào lab Trí tuệ nhân tạo (AI Lab) của trường vào cuối tháng này. Bạn tìm giúp mình tài liệu ôn tập Machine Learning cơ bản và lên lịch ôn thi thực hành mỗi ngày 2 tiếng từ giờ đến lúc thi nhé.
"""

if DEFAULT == "local":
    provider = LocalProvider(model_path=os.getenv("LOCAL_MODEL_PATH"))
else:
    provider = GeminiProvider(api_key=os.getenv("GEMINI_API_KEY"))

logger.log_event("CHATBOT_RUN", {"run_id": RUN_ID, "provider": DEFAULT})
resp = provider.generate(PROMPT, run_type="chatbot")
content = resp.get("content","")
print(content)
logger.log_event("CHATBOT_RESPONSE", {"run_id": RUN_ID, "provider": resp.get("provider","unknown"), "content_preview": content[:300]})
