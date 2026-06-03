# 🏎️ RaceMind AI – Formula 1 Telemetry Intelligence Platform

RaceMind AI is an AI-powered Formula 1 telemetry analysis platform that combines real race telemetry data, tire strategy insights, driver comparisons, and LLM-assisted race engineering explanations into a single interactive dashboard.

Built using **FastAPI**, **FastF1**, **React**, **Recharts**, and **Ollama**, the project allows users to compare drivers, analyze race pace, inspect tire strategies, and ask race-engineer style questions about a Formula 1 race.

---

## 🚀 Features

### 📊 Driver Telemetry Comparison

Compare any two drivers from a race session and visualize:

- Lap-by-lap pace
- Performance trends
- Pace deltas
- Consistency comparisons
- Fastest lap metrics

### 🛞 Tire Strategy Analysis

Visualize race strategy data including:

- Tire compounds
- Stints
- Tire life progression
- Pit stop windows
- Strategy evolution across the race

### 🤖 AI Race Engineer

Generate race-engineer style insights such as:

- Which driver had better pace
- Tire degradation analysis
- Strategy effectiveness
- Performance trends
- Race outcome explanations

### 🧠 Multi-Agent Analysis System

The backend uses specialized analysis agents:

- Telemetry Agent
- Strategy Agent
- Race Context Agent
- Comparison Agent
- LLM Explanation Agent

Each agent contributes evidence before generating a final race-engineer briefing.

### 💬 Ask Engineer

Users can ask natural-language questions such as:

- Why did VER lose pace after lap 34?
- Who managed tyres better?
- Was the pace loss due to degradation or strategy?
- What happened during the middle stint?

The system gathers telemetry evidence and produces an engineering-style response.

### 📋 Driver Discovery

Automatically retrieves available drivers from the loaded race session.

---

## 🏗️ System Architecture

```text
Frontend (React + Recharts)
            │
            ▼
       FastAPI Backend
            │
 ┌──────────┼──────────┐
 │          │          │
 ▼          ▼          ▼
Telemetry  Strategy   AI Analysis
Routes     Routes      Routes
 │          │          │
 └──────────┼──────────┘
            ▼
       FastF1 Data Layer
            │
            ▼
      Monaco GP 2024 Cache
            │
            ▼
      Ollama LLM Engine
```

---

## 🛠️ Tech Stack

### Frontend

- React
- Vite
- Axios
- Recharts
- Tailwind CSS

### Backend

- FastAPI
- FastF1
- Pandas
- Requests
- Python 3.11+

### AI Layer

- Ollama
- Qwen 2.5 7B (default)
- Multi-Agent Prompting

---

## 📁 Project Structure

```text
F1 Analysis
│
├── backend
│   ├── app
│   │   ├── routes
│   │   │   ├── telemetry.py
│   │   │   ├── strategy.py
│   │   │   ├── drivers.py
│   │   │   └── ai_analysis.py
│   │   │
│   │   ├── services
│   │   │   └── llm_engineer.py
│   │   │
│   │   ├── telemetry
│   │   │   └── f1_data.py
│   │   │
│   │   └── main.py
│   │
│   └── cache
│
├── frontend
│   ├── src
│   │   ├── pages
│   │   │   └── Telemetry.jsx
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   └── package.json
│
└── README.md
```

---

## 📡 API Endpoints

### Compare Drivers

```http
GET /compare?driver1=VER&driver2=NOR
```

Response:

```json
{
  "driver1": "VER",
  "driver2": "NOR",
  "comparison": [...]
}
```

---

### Tire Strategy

```http
GET /strategy?driver=VER
```

Response:

```json
{
  "driver": "VER",
  "strategy": [...]
}
```

---

### Available Drivers

```http
GET /drivers
```

Response:

```json
{
  "drivers": ["VER", "NOR", "HAM", "LEC"]
}
```

---

### AI Analysis

```http
GET /ai-analysis?driver1=VER&driver2=NOR
```

Response:

```json
{
  "analysis": [...]
}
```

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/AbhinavPandey-afk/F1-RaceAnalysis.git
cd F1-RaceAnalysis
```

---

### Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

Run backend:

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

---

### Frontend Setup

```bash
cd frontend

npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

## 🤖 Ollama Setup (Optional)

Install Ollama:

https://ollama.com

Pull model:

```bash
ollama pull qwen2.5:7b
```

Run:

```bash
ollama serve
```

The backend automatically connects to:

```text
http://127.0.0.1:11434
```

---

## 📈 Current Dataset

This project currently uses:

```text
2024 Monaco Grand Prix
Race Session
```

cached locally through FastF1.

---

## 🎯 Future Improvements

- Live race telemetry streaming
- Sector-by-sector comparisons
- Speed trace visualization
- DRS analysis
- Corner performance analysis
- Pit stop prediction
- Strategy simulation engine
- Driver ranking system
- Team comparison mode
- Championship analytics dashboard

---

## 📸 Dashboard Features

- Driver comparison dashboard
- Interactive telemetry charts
- Tire strategy visualization
- Performance metric cards
- AI race engineer panel
- Natural language engineer assistant

---

## 👨‍💻 Author

**Abhinav Pandey**

GitHub:
https://github.com/AbhinavPandey-afk

---

## 📜 License

This project is intended for educational, research, and portfolio purposes.

Formula 1 telemetry data is accessed using the FastF1 library and remains subject to the terms of the original data providers.
