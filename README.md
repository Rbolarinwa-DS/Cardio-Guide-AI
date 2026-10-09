# ❤️ CardioGuide AI

**Understand your heart health, one conversation at a time.**

<p align="center">
  <a href="https://cardio-guid.lovable.app/">
    <img src="https://img.shields.io/badge/🚀_LIVE_DEMO-Open_CardioGuide_AI-16a34a?style=for-the-badge" alt="Open CardioGuide AI Live Demo">
  </a>
</p>

<p align="center">
  A conversational cardiovascular health education assistant built with AI, web research, and source-grounded responses to make complex medical information easier to understand.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-FastAPI-009688?style=flat-square" alt="Python and FastAPI">
  <img src="https://img.shields.io/badge/AI-Groq%20%7C%20GPT--OSS%20120B-7C3AED?style=flat-square" alt="Groq GPT-OSS 120B">
  <img src="https://img.shields.io/badge/Retrieval-Serper-2563EB?style=flat-square" alt="Serper">
  <img src="https://img.shields.io/badge/Database-Neon%20PostgreSQL-16A34A?style=flat-square" alt="Neon PostgreSQL">
  <img src="https://img.shields.io/badge/Frontend-React%20%7C%20TypeScript-3178C6?style=flat-square" alt="React and TypeScript">
</p>

> **Medical disclaimer:** CardioGuide AI is an educational software project, not a medical device. It does not replace professional medical advice, diagnosis, or treatment. Its responses may be inaccurate or incomplete.

---

## Table of Contents

- [Overview](#overview)
- [Live Demo and Screenshots](#live-demo-and-screenshots)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [How It Works](#how-it-works)
- [Technology Stack](#technology-stack)
- [API Overview](#api-overview)
- [Database Design](#database-design)
- [Healthcare AI Safety](#healthcare-ai-safety)
- [Testing and Evaluation](#testing-and-evaluation)
- [Project Structure](#project-structure)
- [Project Status](#project-status)
- [Roadmap](#roadmap)
- [Limitations](#limitations)
- [Getting Started](#getting-started)
- [Author](#author)

---

## Overview

Cardiovascular health information can be difficult to understand without a medical background. Blood pressure readings, cholesterol levels, medication terminology, and medical reports often contain concepts that are unfamiliar to the people who need to understand them.

General-purpose chatbots can explain medical concepts, but answers may be unsourced, inconsistent, or inappropriate for situations that require professional care.

**CardioGuide AI** aims to make cardiovascular health education more accessible through a conversational interface backed by a dedicated research and response-generation pipeline.

Rather than relying entirely on a language model's internal knowledge, the system retrieves relevant web information, organizes available evidence, and generates accessible explanations with source attribution where available.

The project combines full-stack development, retrieval-augmented generation (RAG), API integration, database persistence, and safety-oriented request routing in one application.

## Live Demo and Screenshots

### Try the application

**[🚀 Open CardioGuide AI — Live Demo](https://cardio-guid.lovable.app/)**

The application is deployed on Lovable. The backend API is hosted separately on Render.

- [Backend API](https://cardio-guide-ai.onrender.com)
- [API Health Check](https://cardio-guide-ai.onrender.com/health)

### Application screenshots

#### 1. Landing Page

![CardioGuide AI landing page](phase_1_research_engine/pictures/landing.png)

#### 2. AI Chat Assistant

![CardioGuide AI chat interface](phase_1_research_engine/pictures/chat.png)

#### 3. Additional Application View

![Additional CardioGuide AI interface](phase_1_research_engine/pictures/extra.png)

---

## Key Features

| Feature | Description |
|---|---|
| Conversational AI assistant | Answers cardiovascular health education questions in accessible language. |
| Query normalization | Handles common abbreviations, misspellings, and informal wording. |
| Intent and topic analysis | Identifies the subject and general purpose of a user's question. |
| Medical web research | Retrieves relevant information through the Serper API. |
| Evidence construction | Organizes retrieved material into context for response generation. |
| LLM integration | Uses Groq-hosted GPT-OSS 120B for language generation. |
| Source attribution | Returns available source information alongside educational responses. |
| Safety-oriented routing | Separates ambiguous, potentially urgent, and out-of-scope requests. |
| Conversation persistence | Stores users, conversations, and messages in PostgreSQL. |
| REST API | Exposes the backend through FastAPI endpoints. |

### Planned educational modules

- **Blood Pressure:** Hypertension, blood pressure readings, and related concepts.
- **Cholesterol:** LDL, HDL, triglycerides, and general cardiovascular risk education.
- **Medication Guide:** General explanations of medication classes and questions to discuss with a clinician.
- **Disease Library:** Educational material about cardiovascular conditions.
- **Lifestyle:** Nutrition, exercise, sleep, stress, and other lifestyle factors.
- **Medical Report Explainer:** A planned extension for explaining medical terminology in plain language.

The availability of a module in the interface does not imply that its content is complete or clinically validated.

---

## Architecture

CardioGuide AI separates the frontend, backend, research pipeline, language model, and persistent data storage.

```text
                    USER
                      |
                      v
          React / TypeScript Frontend
                      |
                      v
             FastAPI Backend
                  (Render)
                      |
                      v
             Query Normalization
                      |
                      v
          Topic and Intent Analysis
                      |
                      v
           Decision and Safety Gate
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Clarify     Urgent      Redirect
          |       Handling         |
          |           |            |
          +-----------+------------+
                      |
             Educational Requests
                      |
                      v
             Research Query Builder
                      |
                      v
              Serper Web Search
                      |
                      v
          Source and Evidence Processing
                      |
                      v
              Evidence Builder
                      |
                      v
             Response Planner
                      |
                      v
             Groq API / GPT-OSS
                      |
                      v
          Response and Safety Checks
                      |
                      v
          Answer + Available Sources
                      |
                      v
             Neon PostgreSQL
        Users, Conversations, Messages
```

### Design principles

- **Separation of concerns:** Query analysis, retrieval, planning, generation, and safety checks are handled by distinct components.
- **Evidence-informed generation:** Retrieved material provides context for educational responses.
- **Explicit routing:** Ambiguous and out-of-scope questions are not treated as ordinary educational requests.
- **Persistent conversations:** Database-backed records allow conversation history to be retrieved.
- **Traceability:** Available source information accompanies responses to help users inspect supporting material.

Retrieval and source attribution improve transparency but do not guarantee that every claim is correct or adequately supported.

## How It Works

A typical educational request follows this sequence:

1. **Receive:** The FastAPI backend receives a user's question.
2. **Normalize:** Common abbreviations, spelling variations, and informal language are handled.
3. **Analyze:** The query is classified by topic and intent.
4. **Route:** The decision gate evaluates ambiguity, urgency, and scope.
5. **Research:** Appropriate educational questions are converted into search queries.
6. **Retrieve:** The web research component retrieves potentially relevant information from approved medical-source domains.
7. **Build evidence:** Retrieved material is processed and organized into usable context.
8. **Plan:** The response planner determines how to structure the answer.
9. **Generate:** Groq-hosted GPT-OSS 120B generates the response using the supplied context.
10. **Validate and return:** Response checks and source handling are applied before the answer is returned to the frontend.
11. **Persist:** The API stores user and assistant messages in the database.

The research pipeline can use sources such as the World Health Organization (WHO), American Heart Association (AHA), and Mayo Clinic. Their inclusion as sources does not imply endorsement or partnership.

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React | User interface |
| Frontend language | TypeScript | Application logic and type safety |
| Styling | Tailwind CSS | Interface styling |
| Frontend development | Lovable | Frontend creation and deployment |
| Backend | Python, FastAPI | REST API and application orchestration |
| Language model | Groq API, GPT-OSS 120B | Educational response generation |
| Web research | Serper API | Search result retrieval |
| Database | Neon PostgreSQL | Persistent application data |
| ORM | SQLAlchemy | Database models and operations |
| Backend hosting | Render | API deployment |
| Containerization | Docker, Docker Compose | Containerized development and deployment |
| Version control | Git, GitHub | Source control |

**Deployment note:** Vercel deployment of the frontend is being explored. The current public frontend link above points to the Lovable deployment.

---

## API Overview

The FastAPI backend exposes endpoints for service health, chat, and conversation retrieval.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Basic service information |
| `GET` | `/health` | Health check |
| `POST` | `/chat` | Submit a question |
| `GET` | `/conversations/{conversation_id}` | Retrieve a conversation |
| `GET` | `/users/{user_id}/conversations` | Retrieve a user's conversations |

### Example chat request

**Endpoint:** `POST /chat`

```json
{
  "question": "What is hypertension?",
  "user_id": "example-user"
}
```

An optional `conversation_id` can be supplied to associate the request with an existing conversation.

### Example response structure

```json
{
  "action": "proceed",
  "answer": "An educational explanation of hypertension.",
  "sources": [],
  "safety_note": null,
  "grounded": true
}
```

This is an illustrative response structure, not a guarantee of the exact answer or source list for every request.

The API can also return additional fields, including topic, intent, response strategy, and processing time, when available.

### Live endpoints

- **Application:** [cardio-guid.lovable.app](https://cardio-guid.lovable.app/)
- **API root:** [cardio-guide-ai.onrender.com](https://cardio-guide-ai.onrender.com)
- **Health:** [cardio-guide-ai.onrender.com/health](https://cardio-guide-ai.onrender.com/health)

---

## Database Design

CardioGuide AI uses Neon PostgreSQL with SQLAlchemy for persistent storage.

The primary database entities are:

| Table | Purpose |
|---|---|
| `users` | Stores user identifiers and creation timestamps. |
| `user_profiles` | Stores optional personalization preferences. |
| `conversations` | Stores conversation metadata and associates conversations with users. |
| `messages` | Stores user and assistant messages with timestamps. |

### Relationship overview

```text
User
 |
 +---- UserProfile
 |
 +---- Conversation
           |
           +---- Message
           +---- Message
           +---- Message
```

This structure provides a foundation for conversation history and future personalization features.

---

## Healthcare AI Safety

CardioGuide AI is designed for **health education rather than clinical decision-making**.

| Intended use | Restricted use |
|---|---|
| Explaining cardiovascular concepts | Providing definitive diagnoses |
| Explaining medical terminology | Making personalized treatment decisions |
| General blood pressure education | Prescribing medication or recommending doses |
| General lifestyle education | Replacing professional medical assessment |
| Explaining available medical sources | Guaranteeing that an answer is clinically correct |

### Safety-oriented components

- Ambiguity detection
- Urgency classification
- Scope classification
- Decision gating
- Evidence-aware response generation
- Response validation and source handling

These controls are intended to reduce unsafe or irrelevant responses. They do not establish clinical validation or guarantee that the system will correctly identify every emergency.

If someone may be experiencing a medical emergency, they should seek immediate professional medical care rather than rely on an AI assistant.

---

## Testing and Evaluation

CardioGuide AI has undergone functional testing across representative backend and API scenarios.

### Tested areas

- Normal cardiovascular education questions.
- Retrieval and source-response structure.
- Ambiguous query handling.
- Urgent-symptom routing.
- Out-of-scope request handling.
- API availability.
- Database-backed conversation persistence.
- Language-model integration.

The backend has passed representative functional tests. These results should not be interpreted as proof of comprehensive clinical accuracy or safety.

### Evaluation framework

Future systematic evaluation will focus on:

| Dimension | Evaluation target |
|---|---|
| Retrieval quality | Hit rate at K |
| Groundedness | Percentage of claims supported by retrieved evidence |
| Relevance | Human-rated relevance to the question |
| Clarity | Readability and user comprehension |
| Safety | Performance on a defined safety test set |
| Source traceability | Percentage of responses with valid, relevant citations |
| Reliability | API error rate and availability |

Quantitative results will be reported once a defined evaluation suite has been run and its results recorded.

---

## Project Structure

The backend project is located in `phase_1_research_engine/`.

```text
cardio-guide-ai/
│
├── api/
│   ├── main.py
│   └── schemas.py
│
├── database/
│   ├── base.py
│   ├── connection.py
│   ├── crud.py
│   └── models.py
│
├── query_engine/
│   ├── ambiguity_detector.py
│   ├── analyzer.py
│   ├── cardio_guide.py
│   ├── decision_gate.py
│   ├── evidence_builder.py
│   ├── normalizer.py
│   ├── research_query_builder.py
│   ├── response_generator.py
│   ├── response_planner.py
│   ├── llm_client.py
│   └── web_searcher.py
│
├── query_engine/tests/
│   └── test_cardio_guide.py
│
├── data/
│   └── cardioguide_queries.csv
│
├── pictures/
│   ├── landing.png
│   ├── chat.png
│   └── extra.png
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
├── .gitignore
├── .env
└── README.md
```

The actual repository may contain additional files. Environment files containing API keys or database credentials should never be committed to GitHub.

**Screenshot paths:** The README references the images using `phase_1_research_engine/pictures/`. Keep the image links aligned with the actual folder location in your GitHub repository.

---

## Project Status

CardioGuide AI has progressed beyond an interface-only prototype.

| Component | Status |
|---|---|
| Product direction and safety boundaries | Implemented |
| Frontend interface | Built and deployed on Lovable |
| FastAPI backend | Deployed on Render |
| Query normalization and routing | Implemented |
| Web research integration | Integrated with Serper |
| LLM response generation | Integrated with Groq |
| Database persistence | Configured with Neon PostgreSQL |
| Source handling | Implemented; requires continued quality evaluation |
| Functional backend tests | Representative tests passed |
| Comprehensive clinical validation | Not established |
| Vercel frontend deployment | Being explored |
| Systematic evaluation results | Further work required |

The application is functional, but the completeness, accuracy, and safety of its medical coverage require continued evaluation.

---

## Roadmap

- [x] Define product direction and target persona.
- [x] Build the frontend experience.
- [x] Implement the FastAPI backend.
- [x] Implement query normalization and request routing.
- [x] Integrate web research through Serper.
- [x] Integrate Groq-hosted GPT-OSS 120B.
- [x] Configure PostgreSQL persistence with Neon.
- [x] Deploy the backend to Render.
- [x] Test representative API and routing scenarios.
- [ ] Complete and verify the preferred frontend deployment.
- [ ] Improve retrieval relevance for complex, multi-part questions.
- [ ] Expand cardiovascular knowledge coverage.
- [ ] Build a repeatable automated evaluation suite.
- [ ] Publish measured retrieval, groundedness, and safety results.
- [ ] Continue security, reliability, and safety testing.

---

## Limitations

- Retrieved sources may not fully address every part of a complex question.
- Search relevance and source availability can vary.
- Language models can produce inaccurate, incomplete, or misleading explanations.
- Source attribution does not guarantee that every claim is supported by the cited material.
- Coverage and quality may vary between cardiovascular topics.
- The application has not been established as a clinically validated medical product.
- Medical recommendations and evidence may change over time.

CardioGuide AI should be used as an educational aid, not as a substitute for professional healthcare.

---

## Getting Started

### Prerequisites

- Python 3.11 or a compatible Python version supported by the project.
- Git.
- Access to the required API services.
- A PostgreSQL database.

### 1. Clone the repository

```bash
git clone https://github.com/Rbolarinwa-DS/cardio-guide-ai.git
cd cardio-guide-ai
```

### 2. Navigate to the backend project

```bash
cd phase_1_research_engine
```

### 3. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Configure environment variables

Create a local `.env` file containing the required configuration:

```dotenv
DATABASE_URL=your_postgresql_connection_string
GROQ_API_KEY=your_groq_api_key
SERPER_API_KEY=your_serper_api_key
```

Use the actual environment-variable names expected by the project. Keep all credentials private and out of version control.

### 6. Start the API

From the backend project directory:

```powershell
python -m uvicorn api.main:app --reload
```

The API should be available at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is normally available at:

```text
http://127.0.0.1:8000/docs
```

Local startup requires valid configuration, network access to the external services, and an accessible database.

---

## Author

**Rahman Bolarinwa**

Computer Science student building projects in machine learning, AI engineering, NLP, retrieval-augmented generation, computer vision, and end-to-end AI deployment.

- **GitHub:** [Rbolarinwa-DS](https://github.com/Rbolarinwa-DS)

---

<p align="center">
  ❤️ <strong>CardioGuide AI</strong>
  <br>
  Making cardiovascular health easier to understand, one conversation at a time.
  <br><br>
  <a href="https://cardio-guid.lovable.app/">
    <img src="https://img.shields.io/badge/🚀_TRY_THE_LIVE_DEMO-16a34a?style=for-the-badge" alt="Try the CardioGuide AI Live Demo">
  </a>
</p>
