# ❤️ CardioGuide AI

### Making cardiovascular health easier to understand, one conversation at a time.

[![Status](https://img.shields.io/badge/Status-Active%20Development-orange)]()
[![Phase](https://img.shields.io/badge/Phase-2%20%7C%20Medical%20Knowledge%20Design-blue)]()
[![Domain](https://img.shields.io/badge/Domain-Healthcare%20AI-red)]()
[![Focus](https://img.shields.io/badge/Focus-Conversational%20AI%20%7C%20RAG%20%7C%20Healthcare-green)]()

---

## 📌 Overview

**CardioGuide AI** is an AI-powered cardiovascular health education platform designed to make complex cardiovascular information easier to understand through conversational AI and structured educational modules.

The platform combines a conversational AI assistant with a curated cardiovascular knowledge base covering diseases, medications, blood pressure, cholesterol, lifestyle, and medical-report terminology. Rather than simply generating responses from a general-purpose language model, the project is being designed around **structured medical knowledge, retrieval-based information access, source validation, and responsible AI boundaries**.

CardioGuide AI is intended to help users **understand** cardiovascular health information in accessible language. It is explicitly designed as an **educational and informational system, not a diagnostic or treatment system**.

The project is currently in active development, with the current focus on designing the medical knowledge architecture and establishing the information pipeline that will eventually support the conversational AI system.

---

# 🎯 Problem Statement

Cardiovascular health information can be difficult for non-specialists to understand.

Medical terminology, clinical reports, medication information, blood-pressure readings, cholesterol measurements, and disease descriptions are often presented in language that assumes medical knowledge.

At the same time, general-purpose conversational AI systems can produce information that is:

* difficult for users to interpret,
* insufficiently grounded in trusted sources,
* inconsistent in how information is presented,
* potentially unsafe when used for medical decision-making.

CardioGuide AI explores how a conversational AI system can be designed to provide **clear, structured, source-grounded cardiovascular education** while maintaining appropriate safety boundaries.

---

# 💡 Project Vision

The goal is not simply to build another chatbot.

The goal is to build a **specialized healthcare education system** in which:

```text
Medical Knowledge
       ↓
Knowledge Structuring
       ↓
Source Validation
       ↓
Retrieval
       ↓
Context-Aware AI Response
       ↓
Accessible Health Explanation
```

The system should be able to transform complex cardiovascular information into explanations that are easier for a general user to understand without presenting the AI as a replacement for a healthcare professional.

---

# 👤 Target User

The initial target persona is:

### Mary — Hypertension Patient

Mary represents a user who may already have cardiovascular-health concerns but finds medical information difficult to understand.

Typical questions may include:

* What does my blood-pressure reading mean?
* What is hypertension?
* What is the difference between systolic and diastolic pressure?
* What does cholesterol have to do with heart health?
* What are the common types of cardiovascular disease?
* What does a medical term in my report mean?
* Why are certain medications commonly used for cardiovascular conditions?
* What lifestyle factors are associated with cardiovascular health?

The system is designed to **educate and explain**, rather than independently diagnose or prescribe.

---

# 🧩 Core Platform Modules

The platform is planned around a consistent navigation structure so that personalization changes the **content and experience**, rather than creating completely different interfaces for different users.

## 1. 🤖 AI Health Assistant

The central conversational interface.

Planned capabilities:

* Cardiovascular health questions
* Plain-language explanations
* Context-aware conversations
* Knowledge retrieval
* Source-grounded responses
* Follow-up explanations
* Topic-specific educational guidance

---

## 2. 🩺 Blood Pressure

Educational module covering:

* Blood-pressure fundamentals
* Systolic and diastolic pressure
* Blood-pressure measurements
* Hypertension education
* Understanding blood-pressure terminology
* Factors associated with blood pressure
* Common questions and misconceptions

---

## 3. 🧪 Cholesterol

Educational information covering:

* What cholesterol is
* LDL and HDL
* Triglycerides
* Cardiovascular risk concepts
* Understanding common cholesterol measurements
* Lifestyle-related information
* Common terminology

---

## 4. 💊 Medication Guide

A structured educational module designed to help users understand cardiovascular medications at a high level.

Planned information structure:

```text
Medication
    ↓
Medication Class
    ↓
General Purpose
    ↓
How It Is Commonly Used
    ↓
Common Terminology
    ↓
Important Safety Information
    ↓
Trusted Sources
```

The module will **not prescribe medication, recommend doses, or replace professional medical advice**.

---

## 5. 📚 Disease Library

A structured cardiovascular knowledge library.

Initial disease scope includes:

* Hypertension
* High Cholesterol
* Coronary Artery Disease
* Heart Failure
* Heart Attack
* Stroke Prevention
* Atrial Fibrillation
* Atherosclerosis
* Rheumatic Heart Disease

Each disease entry is intended to follow a consistent information structure.

### Example structure

```text
Disease
├── Overview
├── What it means
├── Risk Factors
├── Common Symptoms
├── Complications
├── Diagnosis Concepts
├── Prevention
├── Treatment Concepts
├── Frequently Asked Questions
└── Trusted References
```

---

# 🌱 6. Lifestyle

A cardiovascular-health education module covering topics such as:

* Physical activity
* Nutrition
* Smoking and cardiovascular risk
* Sleep
* Stress
* Weight-related cardiovascular risk
* General heart-health habits

The system will focus on **evidence-based education rather than prescriptive medical treatment plans**.

---

# 📄 7. Medical Report Explainer

A planned module designed to help users understand terminology and information appearing in medical reports.

The objective is:

```text
Medical Term / Report Information
              ↓
       Plain-language explanation
              ↓
       Relevant context
              ↓
       Appropriate caution
```

The system should explain terminology without interpreting a report as a definitive diagnosis.

---

# 🧠 AI Architecture

CardioGuide AI is being designed as a **retrieval-augmented conversational system** rather than relying exclusively on a language model's internal knowledge.

### High-level architecture

```text
                    ┌──────────────────────┐
                    │       User           │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    Web Interface     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI          │
                    │   Backend / API       │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Conversational Layer  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Query Understanding  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Retrieval Pipeline  │
                    │       (RAG)          │
                    └──────────┬───────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
        ┌──────────────────┐      ┌──────────────────┐
        │ Vector / Search  │      │ Structured       │
        │ Knowledge Store  │      │ Medical Data     │
        └────────┬─────────┘      └────────┬─────────┘
                 │                         │
                 └────────────┬────────────┘
                              ▼
                    ┌──────────────────────┐
                    │ Retrieved Context    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      LLM / AI        │
                    │ Response Generation  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Safety / Response    │
                    │ Validation Layer     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      User Response   │
                    └──────────────────────┘
```

---

# 📚 Medical Knowledge Architecture

One of the central engineering challenges in CardioGuide AI is deciding **how medical information should be represented before it reaches the AI system**.

Instead of placing large amounts of unstructured text directly into a retrieval system, the project is being designed around structured knowledge categories.

### Planned hierarchy

```text
Cardiovascular Health
│
├── Diseases
│   ├── Hypertension
│   ├── Coronary Artery Disease
│   ├── Heart Failure
│   └── ...
│
├── Medications
│   ├── Medication Classes
│   └── Individual Medications
│
├── Blood Pressure
│
├── Cholesterol
│
├── Lifestyle
│
└── Medical Reports
```

Each knowledge item will contain metadata such as:

```text
topic
category
subtopic
source
source_url
publication_date
last_reviewed
evidence_level
content
```

This structure is intended to improve retrieval, organization, traceability, and future evaluation.

---

# 🔎 Knowledge Collection Pipeline

The project will use a controlled information pipeline rather than collecting arbitrary internet content.

### Planned workflow

```text
Identify Medical Topic
        ↓
Find Authoritative Source
        ↓
Extract Relevant Information
        ↓
Normalize / Structure Content
        ↓
Record Source Metadata
        ↓
Review Content
        ↓
Store Knowledge
        ↓
Prepare for Retrieval
```

The initial knowledge sources will prioritize reputable medical and public-health organizations and established clinical references.

---

# 🤖 RAG Pipeline

The planned retrieval pipeline will follow:

```text
User Question
      ↓
Query Processing
      ↓
Intent / Topic Identification
      ↓
Relevant Knowledge Retrieval
      ↓
Context Ranking
      ↓
Context Assembly
      ↓
LLM Response Generation
      ↓
Safety / Grounding Checks
      ↓
Final Response
```

The purpose of RAG is to provide the language model with **relevant, curated information at response time** rather than relying solely on its pretrained knowledge.

---

# 🛡️ Healthcare AI Safety

Safety is a core design requirement.

CardioGuide AI will explicitly distinguish between:

### Allowed

* Educational explanations
* Definitions
* General cardiovascular information
* Explanation of medical terminology
* General lifestyle education
* Information about medications
* Questions about cardiovascular concepts

### Restricted / Redirected

* Definitive diagnosis
* Personalized treatment decisions
* Medication prescribing
* Dose recommendations
* Emergency medical decision-making
* Claims that the AI can replace a clinician

The system should encourage users to consult qualified healthcare professionals when questions require clinical judgment.

---

# 🏗️ Development Roadmap

The project is organized into the following development phases:

### Phase 1 — Product Discovery & Planning

**Status: ✅ Completed**

* Define product mission
* Identify target user
* Define core modules
* Establish product boundaries
* Define initial cardiovascular scope

### Phase 2 — Medical Knowledge Design

**Status: 🚧 Current**

* Design knowledge taxonomy
* Define disease schemas
* Define medication schemas
* Define source metadata
* Design content structures
* Establish source-validation process

### Phase 3 — Data Collection

**Status: ⏳ Planned**

* Collect authoritative sources
* Extract relevant content
* Normalize information
* Build initial knowledge corpus

### Phase 4 — AI & RAG Design

**Status: ⏳ Planned**

* Select embedding strategy
* Design retrieval architecture
* Implement chunking strategy
* Develop retrieval pipeline
* Integrate language model
* Design grounding mechanisms

### Phase 5 — Database Design

**Status: ⏳ Planned**

* Design relational schema
* Design knowledge storage
* Implement metadata structure
* Connect application and knowledge layers

### Phase 6 — Backend Architecture

**Status: ⏳ Planned**

* Build FastAPI backend
* Implement authentication
* Implement API endpoints
* Connect database
* Implement AI services

### Phase 7 — UI/UX Design

**Status: ⏳ Planned**

* Build application interface
* Implement personalized content experience
* Design conversational interface
* Implement accessibility-focused layouts

### Phase 8 — Frontend Development

**Status: ⏳ Planned**

* Implement React frontend
* Connect backend APIs
* Implement AI assistant
* Implement educational modules

### Phase 9 — AI Integration

**Status: ⏳ Planned**

* Integrate RAG
* Connect LLM
* Implement context management
* Implement response validation
* Evaluate responses

### Phase 10 — Specialized Modules

**Status: ⏳ Planned**

* Blood Pressure
* Cholesterol
* Medication Guide
* Disease Library
* Lifestyle
* Medical Report Explainer

### Phase 11 — Testing

**Status: ⏳ Planned**

* Functional testing
* Retrieval evaluation
* Response-quality evaluation
* Grounding evaluation
* Safety testing
* Edge-case testing

### Phase 12 — Dockerization & Deployment

**Status: ⏳ Planned**

* Containerize services
* Configure production environment
* Deploy backend
* Deploy frontend
* Configure monitoring

### Phase 13 — Documentation

**Status: ⏳ Planned**

* API documentation
* Architecture documentation
* Knowledge-source documentation
* Evaluation results
* Deployment documentation

---

# 🧪 Evaluation Strategy

The project will not evaluate the AI solely on whether an answer "sounds good."

Planned evaluation dimensions include:

| Dimension               | Goal                                            |
| ----------------------- | ----------------------------------------------- |
| **Retrieval Accuracy**  | Retrieve relevant medical information           |
| **Groundedness**        | Keep responses supported by retrieved context   |
| **Answer Relevance**    | Directly address the user's question            |
| **Clarity**             | Explain medical concepts in accessible language |
| **Safety**              | Avoid inappropriate medical recommendations     |
| **Consistency**         | Produce stable answers to similar questions     |
| **Source Traceability** | Identify where information originated           |

---

# 🛠️ Planned Technology Stack

### AI / ML

* Python
* PyTorch
* Hugging Face ecosystem
* Transformer models
* Embedding models
* Retrieval-Augmented Generation

### Backend

* FastAPI
* REST APIs
* Python

### Data

* PostgreSQL
* Vector search / vector database
* Structured medical knowledge base

### Frontend

* React
* TypeScript
* Tailwind CSS

### Deployment

* Docker
* Cloud deployment
* GitHub

> Technology choices may change during development as the architecture is evaluated.

---

# 📁 Planned Repository Structure

```text
cardio-guide-ai/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── main.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   └── package.json
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── schemas/
│
├── knowledge/
│   ├── diseases/
│   ├── medications/
│   ├── blood_pressure/
│   ├── cholesterol/
│   ├── lifestyle/
│   └── medical_reports/
│
├── evaluation/
│   ├── datasets/
│   ├── retrieval/
│   └── responses/
│
├── docs/
│   ├── architecture/
│   ├── knowledge_design/
│   └── evaluation/
│
├── .gitignore
├── README.md
└── LICENSE
```

---

# 📈 Current Development Status

**Current Phase: Phase 2 — Medical Knowledge Design**

### Completed

* Product discovery
* Target persona definition
* Core product architecture
* Navigation structure
* Cardiovascular disease scope
* Initial module definitions
* Healthcare safety boundaries

### Currently Working On

* Medical knowledge taxonomy
* Disease schemas
* Medication schemas
* Source structure
* Knowledge metadata
* Source collection strategy

### Next Milestone

Build the first **validated cardiovascular knowledge corpus** that can serve as the foundation for the future RAG pipeline.

---

# 🎯 Long-Term Objective

CardioGuide AI is ultimately intended to demonstrate how **machine learning, NLP, information retrieval, and software engineering can be combined to build a responsible healthcare education product**.

The project is being developed incrementally, with emphasis on:

**Reliable knowledge → Strong retrieval → Grounded AI → Safe interaction → Useful product**

---

# ⚠️ Disclaimer

CardioGuide AI is an **educational software project**.

It is not a medical device and is not intended to:

* Diagnose diseases
* Prescribe medication
* Recommend medication dosages
* Replace healthcare professionals
* Provide emergency medical advice
* Make clinical decisions on behalf of users

Users should consult qualified healthcare professionals for medical diagnosis, treatment, or other clinical decisions.

---

# 👨‍💻 Developer

**Rahman Bolarinwa**

Computer Science Student | Machine Learning Engineer | AI Developer

Interested in:

* Healthcare AI
* Machine Learning Engineering
* NLP
* Computer Vision
* LLM Applications
* RAG
* Explainable AI
* AI Product Development
* ML Deployment & MLOps

GitHub: **https://github.com/Rbolarinwa-DS**

---

## 📌 Project Status

**🚧 Active Development**

> This repository documents the development of CardioGuide AI from product discovery and medical knowledge design through AI architecture, implementation, evaluation, and deployment.

**Last Updated: August 2026**
