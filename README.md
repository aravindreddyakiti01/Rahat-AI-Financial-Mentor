# Rahat — AI Financial Mentor for Gig Workers

Rahat is a mobile-first AI financial mentor designed for gig workers whose income is irregular but whose financial obligations are recurring. Instead of treating every conversation as a fresh interaction, Rahat learns from meaningful financial decisions and outcomes over time. 

The core loop is:
$$\text{Decision} \longrightarrow \text{Action} \longrightarrow \text{Outcome} \longrightarrow \text{Memory} \longrightarrow \text{Better Future Decision}$$

---

## 1. Problem

Gig workers (delivery drivers, ride-share partners, freelancers) often deal with:
- **Irregular daily/weekly income** ($\text{₹430}$ to $\text{₹1,300/day}$)
- **Recurring bills and obligations** (monthly bike EMIs, room rent)
- **Unpredictable earning patterns** across weekdays vs. weekend surges
- **Difficulty planning toward financial goals** without creating daily cashflow stress
- **Financial decisions that depend on what happened previously**

Traditional budgeting applications primarily track static transactions. Rahat focuses on the **reasoning layer**: understanding the worker's current financial state together with relevant historical experiences.

---

## 2. Solution

Rahat combines:
- **Current financial data** (SQLite transactional ledger)
- **Long-term experiential memory** (Hindsight memory service)
- **Goal progress tracking** (deterministic calculations)
- **Recurring obligations** (loan EMIs, due dates)
- **Income patterns** (weekday averages vs. weekend surge rhythms)
- **An agentic reasoning workflow** (LangGraph + Gemini LLM)

This allows Rahat to answer not only *"What is my financial situation?"*, but also *"What should I do differently based on what happened before?"*

---

## 3. System Architecture

```
                       FLUTTER MOBILE APP
                               │
                               ▼
                        FASTAPI BACKEND
                               │
                               ▼
                        LANGGRAPH AGENT
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
             SQLITE          REDIS        HINDSIGHT
          (Current Facts)  (Session)  (Long-Term Memory)
                │              │              │
                └──────────────┼──────────────┘
                               │
                               ▼
                          GEMINI LLM
```

### Component Roles

| Component | Purpose |
| :--- | :--- |
| **Flutter** | Mobile application UI (`MentorScreen`, `MoneyScreen`, `MemoryScreen`, `InsightsScreen`, `SettingsScreen`) |
| **FastAPI** | High-performance Python backend & REST API Gateway |
| **LangGraph** | Agentic workflow orchestration (`StateGraph` state engine) |
| **Gemini** | LLM reasoning gateway (`gemini-3.1-flash-lite-preview` cascade with deterministic fallback) |
| **Hindsight** | Long-term outcome-aware experiential memory engine |
| **Redis** | Temporary session state & rate limiting cache (with zero-downtime FakeRedis fallback) |
| **SQLite** | Factual application database (transactions, active goals, fixed obligations, financial plans) |

---

## 4. Agentic Workflow

```
User Message
     ↓
Parse Intent
     ↓
Load Current Financial State (SQLite)
     ↓
Retrieve Relevant Hindsight Memories
     ↓
Reason with LLM (Gemini)
     ↓
Decision Router
     ↓
Execute Controlled Action (Tool Execution)
     ↓
Generate Response
     ↓
Record Meaningful Outcome (Hindsight)
```

> **Important Engineering Design:** The LLM does **not** directly modify the database. Financial write operations (recording earnings, logging fuel expenses, creating goals, updating savings progress) are performed strictly through **controlled backend tools** (`record_transaction`, `create_goal`, `update_goal`, `create_financial_plan`).

---

## 5. Hindsight Long-Term Memory Architecture

Rahat integrates [Hindsight](https://github.com/vectorize-io/hindsight) for long-term experiential memory across 5 structured categories:

1. `PROFILE_FACT`: Stable user characteristics (e.g. Hero Splendor EMI obligation)
2. `PREFERENCE`: Expressed planning preferences (e.g. preferred weekend surge savings)
3. `PLAN`: Formulated financial pacing plans
4. `OUTCOME`: Real-world results and friction after a plan or action (linked to plans via `related_plan_id`)
5. `PATTERN`: Derived behavioral or earning rhythms (e.g. weekend earnings are 2x weekday average)

### Factual vs. Experiential Memory Boundary

| Storage Engine | Memory Responsibility | Example Data |
| :--- | :--- | :--- |
| **SQLite** | Factual transactional data | Raw income entries, fuel expense logs, active goal amounts, EMI due dates |
| **Hindsight** | Meaningful experiential information | Previous plans, missed/achieved outcomes, earning surge patterns, learned preferences |

> **Architectural Principle:** $\text{Raw transactions} \longrightarrow \text{SQLite}$ | $\text{Meaningful experiences} \longrightarrow \text{Hindsight}$

### Official Hindsight Resources:
- [Hindsight GitHub Repository](https://github.com/vectorize-io/hindsight)
- [Hindsight Documentation](https://hindsight.vectorize.io/)
- [What is Agent Memory?](https://vectorize.io/what-is-agent-memory)

---

## 6. Before / After Example: Outcome-Aware Learning Loop

### Without Outcome Memory (Generic Chatbot):
> **User:** *"I need ₹4,500 for my EMI in five days. What should I do?"*  
> **Generic Agent:** *"Try earning ₹900 per day for the next five days."*  
> *(Ignores weekday vs. weekend earning realities and repeats a failed target)*

### With Rahat Outcome Memory:
> **System Retrieves:**  
> - **Previous Plan:** Flat ₹900/day daily savings target  
> - **Recorded Outcome (Sept 16):** Target missed because weekday earnings were low (~₹500/day saved)  
> - **Observed Pattern:** Weekend surge earnings are 2x weekday average  
>
> **Rahat Adaptive Guidance:**  
> *"Instead of repeating a rigid ₹900/day target that caused weekday stress, here is an **Adaptive Surge Allocation** plan based on your actual earning patterns:*  
> - **Weekdays (Mon–Fri):** Reserve a lighter ₹270/day  
> - **Weekend Surge (Sat–Sun):** Allocate ₹810/day from peak shift earnings  
> *This clears your ₹2,700 remaining EMI on time without leaving you short on daily fuel cash."*

---

## 7. Features

### Financial Management
- Record income & delivery payouts
- Log fuel & operating expenses
- Track savings goals with progress percentages and days remaining
- Manage recurring obligations (bike EMIs, room rent)
- View daily, 7-day, and monthly cashflow summaries

### AI Mentor
- Natural-language financial Q&A
- Grounded financial planning
- Goal progress reasoning
- Outcome-aware adaptive recommendations

### Long-Term Memory
- Profile facts & obligations
- User preferences
- Financial plans & strategy tracking
- Real-world outcomes linked to plans (`related_plan_id`)
- Earning & spending behavioral patterns

### Mobile Experience (Flutter)
- **Mentor Screen:** AI chat & grounded advice with "Why this advice?" evidence drawer
- **Money Screen:** Cashflow summary, goal cards, and transaction ledger
- **Memory Screen:** Chronological Hindsight timeline with filtering and search
- **Insights Screen:** Grounded statistics (weekend surge advantage, fuel expense ratio)
- **Settings Screen:** Profile, preferences, memory reset, and financial disclaimers

---

## 8. Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Mobile Frontend** | Flutter (Dart) |
| **Backend Gateway** | Python 3.14 / FastAPI / Uvicorn |
| **Agent Orchestration** | LangGraph (`StateGraph`) |
| **LLM Gateway** | Google Gemini API (`gemini-3.1-flash-lite-preview` cascade) |
| **Long-Term Memory** | Hindsight Memory Service |
| **Session Cache** | Redis / FakeRedis fallback |
| **Database** | SQLite (`sqlite3`) |
| **Testing** | Automated Pytest / Python Async Test Suites |

---

## 9. Repository Structure

```
Rahat-AI-Financial-Mentor/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── backend/
│   ├── app/
│   │   ├── agent/
│   │   │   ├── graph.py
│   │   │   ├── llm.py
│   │   │   ├── state.py
│   │   │   └── tools.py
│   │   ├── core/
│   │   │   ├── cache.py
│   │   │   └── config.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── repository.py
│   │   ├── memory/
│   │   │   └── hindsight.py
│   │   ├── routers/
│   │   │   ├── agent.py
│   │   │   ├── finance.py
│   │   │   ├── goals.py
│   │   │   └── memory.py
│   │   ├── schemas/
│   │   └── main.py
│   ├── .env.example
│   ├── requirements.txt
│   ├── test_rahat.py
│   ├── test_step2.py
│   ├── test_step3.py
│   ├── test_step4.py
│   ├── test_step5.py
│   ├── test_step6.py
│   └── verify_step6_goals.py
├── mobile/
│   ├── lib/
│   │   ├── models/
│   │   ├── screens/
│   │   ├── services/
│   │   └── main.dart
│   ├── assets/
│   └── pubspec.yaml
└── docs/
    ├── architecture/
    │   └── architecture.md
    ├── demo/
    │   └── demo.md
    └── screenshots/
        └── README.md
```

---

## 10. Installation & Setup

### Prerequisites
- Python 3.10+
- Flutter SDK 3.19+ (for mobile app)

### Step 1: Set Up Backend
```bash
cd backend
python -m venv .venv
```

**Windows:**
```powershell
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` in the `backend/` directory:
```bash
cp .env.example .env
```

Set your Gemini API key in `backend/.env`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
```
> **Security Note:** Never commit your `.env` file to Git. It is automatically ignored by `.gitignore`.

---

## 11. Running the Application

### Running Backend API
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
- **Backend Service:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`

### Running Flutter Mobile App
```bash
cd mobile
flutter pub get
flutter run
```

---

## 12. Testing & Verification

The Rahat implementation has been verified through a 6-step automated test suite:

```
======================================================================
  RAHAT AUTOMATED TEST SUITE VERIFICATION SUMMARY
======================================================================
  Step 1 (Foundational Architecture):         4 / 4   PASS
  Step 2 (Financial Persistence):            15 / 15  PASS
  Step 3 (LangGraph Agent Workflow):         15 / 15  PASS
  Step 4 (Hindsight Memory System):          18 / 18  PASS
  Step 5 (Real LLM Integration & Chat):      20 / 20  PASS
  Step 6 (Goals & Adaptive Planning):        19 / 19  PASS
======================================================================
  CUMULATIVE VERIFIED TOTAL:                 91 / 91 PASS (100%)
======================================================================
```

Run all test suites:
```bash
cd backend
python test_rahat.py
python test_step2.py
python test_step3.py
python test_step4.py
python test_step5.py
python test_step6.py
```

---

## 13. Screenshots & Demo

### Screenshots
Screenshots are located in `docs/screenshots/`:
- `01_mentor.png`: AI Mentor screen with "Why this advice?" evidence modal
- `02_money.png`: Cashflow overview, active goal progress, and transaction ledger
- `03_memory.png`: Chronological Hindsight memory timeline
- `04_insights.png`: Earning pattern analysis and fuel cost ratio

### Video Demo
- **Watch the Rahat 60-Second Demo Video:** `[YouTube Demo Link]`
- Detailed walkthrough script available at `docs/demo/demo.md`.

---

## 14. Current Limitations

- **Voice Interaction:** Speech-to-text input is designed in the UI layer; audio processing pipeline is scheduled for a post-hackathon release.
- **Receipt OCR:** Receipt scanning UI placeholder exists; document vision integration is planned as a subsequent module.
- **Deterministic Memory Ranking:** Memory retrieval currently uses keyword + type relevance scoring; semantic vector embeddings will be integrated in future Hindsight updates.
- **Historical Horizon:** Earning pattern analysis relies on available historical transaction logs (7–30 day window).

---

## 15. Roadmap

- [x] Flutter mobile architecture & key screens
- [x] SQLite financial persistence (income, expenses, goals, obligations)
- [x] LangGraph agentic workflow & intent routing
- [x] Hindsight long-term experiential memory service
- [x] Real Gemini LLM integration with candidate model cascade
- [x] Deterministic goal-progress calculations
- [x] Irregular-income Adaptive Surge Allocation planning
- [x] Plan → Outcome memory linking (`related_plan_id`)
- [ ] Voice conversation pipeline
- [ ] Receipt OCR document vision
- [ ] Vector embedding semantic search in Hindsight

---

## 16. Security & Financial Safety

- **API Credentials:** Keys are stored strictly in `.env` files and loaded via environment variables.
- **Secrets Protection:** No credentials or API keys are committed to the repository.
- **Control Flow Boundary:** All database write operations are performed through controlled backend tools (`record_transaction`, `create_goal`).
- **User Isolation:** All SQLite and Hindsight queries strictly isolate data by `user_id`.
- **Advisory Boundary:** Rahat provides practical budgeting/cash-flow guidance only; it refuses to offer investment, stock, tax, or loan advice.

---

## 17. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
