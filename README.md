# FormIQ — AI-Assisted Multi-Tenant Survey Platform

> **A multi-tenant survey platform with an AI question-generation agent**, dynamic survey builder, shareable public links, response analytics, and JSON export — built with Django, PostgreSQL, MongoDB, and LangGraph.

[![Django](https://img.shields.io/badge/Django-5.x-092E20?style=flat&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Metadata-4169E1?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Surveys%20%26%20Questions-47A248?style=flat&logo=mongodb)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-Rate%20Limiting-DC382D?style=flat&logo=redis)](https://redis.io/)
[![LangGraph](https://img.shields.io/badge/LangGraph-AI%20Agent-000000?style=flat)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Gemini-Google%20AI-4285F4?style=flat&logo=google)](https://deepmind.google/technologies/gemini/)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-0B0D0E?style=flat)](https://railway.app/)
[![Solo Build](https://img.shields.io/badge/Built%20by-Solo%20Developer-blueviolet?style=flat)]()

🌐 **Live Demo:** `[link coming soon]`
📁 **GitHub:** `[https://github.com/akash123-dot/FormIQ-AI-Assisted-Multi-Tenant-Survey-Platform/tree/main?tab=readme-ov-file]`

---

## The Problem

Building a survey tool sounds simple — until you think about multi-tenancy, question type variety, response aggregation, and the blank-page problem of "what questions should I even ask?" Most survey tools are either too rigid (fixed templates) or require users to know exactly what they want before they start. And sharing a survey publicly usually means a separate link management system bolted on as an afterthought.

**FormIQ solves this** with a clean survey builder that supports three question types, a shareable public link per survey out of the box, and an optional AI agent that reads your survey title, description, and existing questions — then generates contextually relevant new ones in whatever quantity and type you specify.

---

## What is FormIQ?

**FormIQ** is a multi-tenant survey platform where each user owns their surveys in complete isolation. It has two modes for building questions: **manual** (you write them yourself) and **AI Builder** (Gemini generates them based on your survey context). Surveys are shared via a unique public link, responses are collected into MongoDB, and a dashboard shows response counts and charts per survey. Full surveys can be exported as JSON at any time.

**Built solo. Deployed on Railway.**

---

## Architecture Overview

FormIQ uses a **split-database architecture** — PostgreSQL for structured relational data (users, survey metadata, public links), and MongoDB for flexible document storage (survey question collections and response submissions). Redis handles rate limiting across all API endpoints. The AI agent runs synchronously within the Django request cycle using a LangGraph ReAct loop.

```mermaid
flowchart TD

    A[User] --> B[Start Survey]

    B --> C[Enter Name & Description]

    C --> D[Save Survey]

    D --> D1[(MongoDB: Survey Collection)]
    D --> D2[(PostgreSQL: Metadata + Survey Link)]

    D --> E{Choose Mode}

    E -->|Manual| F[Add Questions]
    F --> F1[Text / Single Choice / Multiple Choice]
    F1 --> G[Submit Questions]
    G --> G1[(MongoDB: Question Collection)]

    E -->|AI Builder| H[Enter Number of Questions]
    H --> I[AI Analyze]
    I --> I1[Use Name + Description + Existing Questions]
    I1 --> J[Generate Questions]

    J --> K{User Action}

    K -->|Save All| G1
    K -->|Save Selected| G1
    K -->|Regenerate| H
    K -->|Back to Manual| F
    K -->|View Survey| L[Display Survey]

    G --> L

    subgraph RATE_LIMITING [Rate Limiting Layer]
        R1[Applied Across All APIs / Functions]
    end
```

---

## How It Works — Full Flow

> **📹 GIF Placeholder — Survey Builder: Create survey → Choose mode → generates questions → Save to MongoDB**
<p align="center">
  <img src="https://github.com/user-attachments/assets/435f1c8f-ae49-4c81-a521-40038ef20091" width="700"/>
</p>

### Step 1 — Create a Survey

User enters a **name** and **description**. On save:
- Survey document created in **MongoDB** (Survey Collection)
- Survey metadata + a unique **shareable public link** saved in **PostgreSQL**

Both writes happen on survey creation so the public link is available immediately, before any questions are added.

### Step 2 — Choose a Mode

After creating the survey, the user picks how to build their questions:

| Mode | Description |
|------|-------------|
| **Manual** | User writes questions directly, choosing type for each |
| **AI Builder** | User specifies how many (and what type of) questions to generate — AI handles the rest |

These modes are not mutually exclusive. A user can start with AI Builder, take the generated questions they like, and then switch to Manual to add more.

---

### Manual Mode

User adds questions one at a time, selecting a type for each:

- **Text** — open-ended free text response
- **Single Choice** — one answer from a list of options
- **Multiple Choice** — one or more answers from a list of options

All questions are submitted and saved to **MongoDB** (Question Collection) under the survey's document.

During building, the user can **view the live survey** at any point to see exactly how it will look to respondents.

---

### AI Builder Mode

> **📹 GIF Placeholder — AI Builder: Enter prompt → Agent generates questions → User saves selected or all**
<p align="center">
  <img src="https://github.com/user-attachments/assets/8103b315-5f4f-4367-b3b2-df6231fa96a7" width="700"/>
</p>

The user specifies:
- How many questions to generate (e.g. `5`)
- Optionally, what type (e.g. `"only single choice"`, `"at least 3 multiple choice"`)
- Or just a free prompt (e.g. `"generate 5 questions about customer satisfaction"`)

The AI agent then runs with full awareness of:
- The survey **title**
- The survey **description**
- The **questions already added** to the survey (to avoid duplicates and maintain coherence)

#### The LangGraph ReAct Agent

The AI agent is built as a **ReAct-style loop** using LangGraph — not a single LLM call. The graph looks like this:

```python
graph = StateGraph(AgentState)
graph.add_node('our_agent', model_call)   # Gemini decides what to do
graph.add_node('tools', ToolNode(tools=tools))  # Tools execute actions

graph.add_edge('tools', 'our_agent')      # After tool use, back to agent
graph.set_entry_point('our_agent')

graph.add_conditional_edges(
    'our_agent',
    should_continue,
    {
        'continue': 'tools',   # Agent wants to use a tool
        'end': END             # Agent is done
    }
)
```

The agent receives the survey context and user request. It reasons about what questions to generate, calls the question-generation tool, evaluates the output, and either iterates (if the count or type isn't satisfied yet) or ends. This loop means the agent can self-correct — if the first tool call only generates 3 questions but 5 were requested, it reasons about what's missing and calls the tool again.

**After generation**, the user has three options:
- **Save All** — add every generated question to the survey in one click
- **Save Selected** — pick specific questions to keep
- **Regenerate** — discard and run the agent again with the same or modified prompt

All saved questions go to **MongoDB** (Question Collection).

---

## Survey Sharing & Responses

Each survey has a **unique public link** generated at creation time and stored in PostgreSQL. Sharing this link requires no authentication — anyone with the link can submit a response.

Submissions are saved to **MongoDB** alongside the survey's question collection. The survey owner can see:
- Total response count per survey
- Per-question response breakdown
- Bar or pie chart visualization of responses (user's choice)
- Export the full survey + all responses as a **JSON file**

> **📹 GIF Placeholder — Dashboard & Analytics: Survey list → Click survey → View response charts → Export JSON**
<p align="center">
  <img src="https://github.com/user-attachments/assets/aeb267c7-e9f1-4bdd-9b37-080dc2ee4a29" width="700"/>
 
</p>
---

## User Dashboard

The dashboard is scoped strictly per user — **no user can see another user's surveys** (multi-tenant isolation enforced at the query layer). Each user sees:

| Feature | Detail |
|---------|--------|
| Survey list | All surveys with response count and creation date |
| Edit survey | Add more questions, update name/description |
| Delete survey | Removes from both PostgreSQL and MongoDB |
| View public link | Copy-ready shareable URL |
| Response charts | Pie or bar chart per question |
| Export | Full survey + responses as JSON |

---

## Full Tech Stack

| Technology | Role | Why |
|---|---|---|
| **Django** | Web framework, auth, routing | Sessions-based auth, clean ORM for PostgreSQL, rapid view development |
| **PostgreSQL** | User data, survey metadata, public links | Relational data with strict ownership — the right tool for structured, queryable records |
| **MongoDB** | Survey questions, response submissions | Document model fits naturally for variable-length question arrays and free-form responses |
| **Redis** | Rate limiting | Lightweight counter store; prevents API abuse without adding infrastructure complexity |
| **LangGraph** | AI agent orchestration | ReAct loop allows the agent to reason, use tools, and self-correct — more reliable than a single prompt |
| **Gemini (Google)** | Question generation | Strong instruction-following for structured JSON output of typed survey questions |
| **Railway** | Deployment | Simple container-based deployment with managed PostgreSQL, MongoDB, and Redis add-ons |

---

## Key Engineering Decisions

### Why split PostgreSQL and MongoDB?
Survey metadata (owner, creation date, public link, response count) is relational and benefits from foreign keys, indexes, and joins — PostgreSQL is the right store. Survey questions and responses are variable-length, schema-flexible documents: a single-choice question has options, a text question doesn't, and response shape depends on question type. Forcing this into a relational schema means nullable columns or a separate options table with joins on every read. MongoDB's document model stores each survey's questions as a natural nested array, making reads and writes simpler and faster for that data shape.

### Why a LangGraph ReAct agent instead of a single Gemini prompt?
A single prompt asking Gemini to "generate 5 single-choice questions" works most of the time — but fails silently when the count is wrong, the type mix is off, or the questions duplicate ones already in the survey. The ReAct loop gives the agent the ability to check its own output against the user's requirements and iterate. The `should_continue` conditional edge means the agent runs the tool again if it hasn't satisfied the request yet, rather than returning a subtly wrong result that the user has to manually fix.

### Why Redis only for rate limiting (not caching)?
FormIQ's data access patterns don't have a hot read path that would benefit from caching — survey dashboards are per-user, responses are per-survey, and neither is read frequently enough to justify cache invalidation complexity. Adding a cache layer without a clear performance problem it solves is unnecessary infrastructure. Redis earns its place here as the rate limit counter store, which is exactly what it's fast at — atomic increments on short-lived keys.

### Why Django sessions instead of JWT?
FormIQ is a server-rendered Django application, not a headless API with a separate frontend. Django's session framework is the natural choice — sessions are stored server-side, revocation is immediate (just delete the session), and there's no token management complexity. JWT makes sense when you need stateless auth across distributed services or a mobile client. Here it would add complexity with no benefit.

### Why shareable public links generated at survey creation?
Generating the link at creation (rather than at publish time) means the owner always has a stable URL they can share or embed before the survey is finalized. It also simplifies the data model — the link is a property of the survey, not a separate publish state. The public submission endpoint simply checks if the survey exists and accepts responses regardless of how many questions are currently attached.

### Why multi-tenant isolation at the query layer?
Every dashboard query filters by the authenticated user's ID — `Survey.objects.filter(owner=request.user)`. There is no shared survey pool and no admin bypass. This means even if a survey ID is guessed or leaked, fetching it through the dashboard returns a 404 for any user who doesn't own it. The public submission link is intentionally the only unauthenticated surface, and it only allows writing responses, not reading survey ownership data.

---

## Routes Reference

### Auth
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/auth/register/` | Register new user |
| POST | `/auth/login/` | Login, creates Django session |
| POST | `/auth/logout/` | Logout, clears session |

### Surveys
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/surveys/create/` | Create new survey → saves to PostgreSQL + MongoDB |
| GET | `/surveys/` | List all surveys for authenticated user |
| GET | `/surveys/{id}/` | View survey detail + response stats |
| PUT | `/surveys/{id}/edit/` | Edit survey name/description |
| DELETE | `/surveys/{id}/delete/` | Delete survey from PostgreSQL + MongoDB |
| GET | `/surveys/{id}/export/` | Export full survey + responses as JSON |

### Questions
| Method | Route | Description |
|--------|-------|-------------|
| POST | `/surveys/{id}/questions/add/` | Add question manually (text / single / multiple choice) |
| POST | `/surveys/{id}/questions/ai-generate/` | Run AI agent → return generated questions |
| POST | `/surveys/{id}/questions/save-selected/` | Save specific AI-generated questions |
| POST | `/surveys/{id}/questions/save-all/` | Save all AI-generated questions |

### Public Submission
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/s/{public_link}/` | Display public survey (no auth required) |
| POST | `/s/{public_link}/submit/` | Submit survey response → saved to MongoDB |

### Dashboard & Analytics
| Method | Route | Description |
|--------|-------|-------------|
| GET | `/dashboard/` | Survey list with response counts |
| GET | `/dashboard/{id}/analytics/` | Response charts (pie / bar) per question |

---

## Local Setup

### Prerequisites
- Docker + Docker Compose
- A `.env` file (see below)

### Run

```bash
git clone [repo link coming soon]
cd formiq
cp .env.example .env   # fill in your keys
docker compose up --build
```

App available at `http://localhost:8000`.

---

## Environment Variables

```env
# Django
SECRET_KEY=your-django-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/formiq

# MongoDB
MONGODB_URI=mongodb://localhost:27017/formiq

# Redis (rate limiting)
REDIS_URL=redis://localhost:6379/0

# Gemini (AI question generation)
GEMINI_API_KEY=your-gemini-api-key
```

---

## Future Roadmap

- [ ] Question reordering via drag-and-drop
- [ ] Survey response notifications (email on new submission)
- [ ] Async AI generation via Celery (for very large question counts)
- [ ] PDF export of survey results with embedded charts
- [ ] Survey expiry date / max response limit
- [ ] Conditional question logic (show question B only if answer to A is X)

---

## Author

**Akash** — Built solo end to end.

GitHub: `[https://github.com/akash123-dot/FormIQ-AI-Assisted-Multi-Tenant-Survey-Platform/tree/main?tab=readme-ov-file]` · Built with Django, PostgreSQL, MongoDB, LangGraph, Gemini, Redis
