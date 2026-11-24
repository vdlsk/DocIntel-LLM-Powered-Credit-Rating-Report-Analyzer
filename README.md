# DocIntel – Credit Rating Report Analyzer

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://docintel-llm-powered-credit-rating-report-analyzer-fkd7kbdbjjs.streamlit.app)

**Live demo:** [docintel-llm-powered-credit-rating-report-analyzer-fkd7kbdbjjs.streamlit.app](https://docintel-llm-powered-credit-rating-report-analyzer-fkd7kbdbjjs.streamlit.app)

Upload a credit rating report PDF (CARE, CRISIL, ICRA, India Ratings, Acuité). The app reads it
automatically and shows a **dashboard** (rating, financial charts, ratios, warnings) and a
**chatbot** that answers questions with page citations.

## How it works (5 steps)

1. `loader.py` – reads the PDF page by page (keeps page numbers).
2. `extraction.py` – the AI fills a fixed form (`schema.py`) with rating, outlook, financials, strengths, risks.
3. `analysis.py` – ratios (margin, debt/equity, interest cover) are calculated in **plain Python**, never by the AI.
4. `vectorstore.py` – the PDF text is cut into chunks and saved in a **Chroma** database for search.
5. `chatbot.py` – the two ways of answering a question:
   - **structured** → answer from the extracted numbers
   - **document** → search the PDF (RAG) and cite pages
6. `graph.py` – a **LangGraph agent** that decides which way to answer: a router node asks the AI,
   then the graph follows the matching arrow (`router → structured | document → answer`).

`pipeline.py` runs steps 1–4 for any PDF. `app.py` (Streamlit website) and `api.py` (FastAPI REST API)
both use it. `llm.py` is the only file that knows the AI provider.

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env        # then open .env and paste your API key
streamlit run app.py
```

## Run the REST API (FastAPI)

```bash
uvicorn api:app --reload        # then open http://localhost:8000/docs
```
`POST /reports` (upload PDF) → `POST /reports/{id}/ask` (ask a question) → `GET /reports/{id}`.

## Run with Docker (starts website on :8501 and API on :8000)

```bash
docker compose up --build
```

## Switch between Gemini and OpenAI

Open `.env` and change one line: `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai`.
(Model names can also be changed in `.env`; defaults are in `llm.py`.)

## Test without an API key

```bash
python test_offline.py
```

## Why these choices (good interview answers)

- **Pydantic schema** → the AI must return data in a fixed shape, so the app never breaks on free text.
- **Maths in Python** → LLMs can get arithmetic wrong; code cannot.
- **Page numbers in every chunk** → every answer can be checked against the source.
- **Two routes** → exact numbers come from structured data; explanations come from the document text.
- **LangGraph** → the chat flow is an explicit graph (nodes + conditional edge) instead of if/else, so it is easy to extend with more steps (e.g. a fact-check node).
- **FastAPI** → the same logic is reachable as a REST API, so any other service (e.g. a mobile app) can use it.
- **Docker** → one image runs both the website and the API the same way on any machine.
- **Retry with waiting (tenacity)** → survives temporary rate limits or network errors.
