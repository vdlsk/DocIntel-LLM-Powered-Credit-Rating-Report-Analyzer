"""
extraction.py - ask the AI to read the report and fill our fixed form (CreditReport).
If the AI call fails (network / rate limit), tenacity retries a few times with waiting.
"""
from tenacity import retry, stop_after_attempt, wait_exponential
from llm import get_llm
from schema import CreditReport

MAX_CHARS = 80_000   # keep the prompt a safe size

PROMPT = """You are reading a credit rating report from an Indian rating agency.
Fill the requested form using ONLY information written in the report.
If a value is not in the report, leave it empty (null). Do not guess or calculate.
Keep money values in INR crore as printed. List financial years oldest first.

REPORT:
{text}
"""


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20), reraise=True)
def extract_report(pages) -> CreditReport:
    text = "\n".join(f"[Page {p.metadata['page']}]\n{p.page_content}" for p in pages)[:MAX_CHARS]
    structured_llm = get_llm().with_structured_output(CreditReport)
    return structured_llm.invoke(PROMPT.format(text=text))
