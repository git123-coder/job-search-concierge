# Job Search Concierge Agent

A multi-agent AI job search assistant built with Google ADK that helps users log job applications, update records, analyze their job search, and receive strategy recommendations using natural language.

---

# Demo
[![Watch the Demo](images/Github_Thumbnail2.png)](https://www.youtube.com/watch?v=4huJWB_kBdE)

# Problem Statement

Managing a job search across multiple companies quickly becomes difficult. Applicants often forget where they applied, which applications require follow-up, and how their overall job search is progressing.

This project provides a conversational AI assistant that centralizes application tracking, analytics, and strategy recommendations through natural language.

---

# Why AI Agents?

A multi-agent architecture allows different responsibilities to remain isolated while collaborating through a Supervisor Agent.

* Supervisor Agent coordinates the workflow.
* Logger Agent manages application records.
* Insights Agent generates analytics.
* Strategy Agent provides personalized recommendations.

This modular design improves maintainability, scalability, and separation of responsibilities.

---

# Key Features

* Live conversational Streamlit interface
* Natural language application logging
* Partial-record preservation
* Conversational record completion
* Conversational record updating
* Job search analytics
* Follow-up recommendations
* Multi-agent architecture
* Audit logging
* Permanent regression test suite

---

# Architecture

```text
User
 │
 ▼
Supervisor Agent
 │
 ├── Logger Agent
 │      │
 │      ├── add_application()
 │      └── update_status()
 │
 ├── Insights Agent
 │      │
 │      ├── get_applications()
 │      ├── calculate_analytics()
 │      └── analyze_job_search() Skill
 │
 └── Strategy Agent
        │
        ├── get_applications()
        ├── calculate_analytics()
        ├── find_stale_applications()
        └── analyze_job_search() Skill
```

---

# Tech Stack

* Python
* Google ADK
* Gemini Flash
* MCP
* Streamlit
* Pandas
* CSV
* Git
* GitHub

---

# Course Concepts Demonstrated

| Concept                  | Demonstration                                       |
| ------------------------ | --------------------------------------------------- |
| Multi-Agent System (ADK) | Supervisor, Logger, Insights and Strategy Agents    |
| MCP                      | Local MCP tools for application management          |
| Security                 | Input validation, tool allow-lists, audit logging   |
| Agent Skills             | Shared `analyze_job_search()` skill                 |
| Antigravity              | Used during project development workflow            |
| Deployability            | Streamlit application with reproducible local setup |

---

# Project Structure

```text

job-search-concierge
 │
 ├── app
 │     │
 │     ├── agent.py
 │     ├── engine.py
 │     ├── security.py			
 │     ├── skills.py
 │     └── tools.py
 │
 ├── app.py
 ├── applications.csv
 ├── audit.log
 ├── README.md
 ├── regression_tests.py
 └── requirements.txt
 
```

---

# Agents

## Supervisor Agent

* Routes requests
* Coordinates specialized agents
* Returns the final response

## Logger Agent

* Log applications
* Preserve incomplete records
* Update existing records
* Conversational record completion

## Insights Agent

Provides:

* Total applications
* Interview count
* Offer count
* Response rate
* Rejection rate
* Stale applications

## Strategy Agent

Provides:

* Follow-up recommendations
* Job search priorities
* Strategy suggestions

---

# MCP Tools

* add_application()
* update_status()
* get_applications()
* calculate_analytics()
* find_stale_applications()

---

# Shared Agent Skill

`analyze_job_search()`

Used by:

* Insights Agent
* Strategy Agent

---

# Setup Instructions

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd job-search-concierge
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a Gemini API Key

1. Sign in to Google AI Studio.
2. Create a new API key.
3. Copy the generated key.

### 5. Configure the API Key

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your-api-key-here
```

Alternatively, set it as an environment variable before running the project:

**macOS / Linux**

```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Windows (PowerShell)**

```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

### 6. Launch the application

```bash
streamlit run app.py
```

### 7. Run the regression test suite (optional)

```bash
python3 regression_tests.py
```

---

# Example Prompts

## Logging

* I applied to Microsoft for SWE today
* Applied
* Microsoft
* SWE

## Updating

* Update Record #15
* Company: NVIDIA
* Role: Software Engineer

## Insights

* How many applications have I submitted?
* How is my job search going?

## Strategy

* What should I follow up on?

## General

* Hi

---

# Data Storage

* applications.csv
* audit.log

---

# Security Features

* Input validation
* Tool allow-lists
* Supervisor-controlled routing
* Audit logging for tool operations
* Restricted agent responsibilities through the Supervisor

---

# Future Improvements

* Database storage
* Authentication
* Cloud deployment
* Resume parsing
* Email integration
* Browser automation
* Web scraping

---

# License

This project is provided for educational and demonstration purposes as part of the Kaggle **AI Agents: Intensive Vibe Coding** Capstone Project.

---

# Author

Capstone project demonstrating:

* Google ADK
* Multi-agent architecture
* MCP
* Agent Skills
* Security controls
* Streamlit frontend
* Natural language interaction
