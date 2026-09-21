# Shortlyst

An intelligent HR automation platform that uses a **fully local RAG (Retrieval-Augmented Generation) pipeline** to intelligently screen, rank, and shortlist candidates — no cloud API keys required. Built on a modern React + Node.js full-stack architecture with [Ollama](https://ollama.com) powering local AI inference.

---

## 🎯 Overview

This project addresses the critical HR challenge of **resume screening at scale** — moving far beyond keyword filters to build a system that *understands* candidates:

- **Deep Job Understanding** — Embeds the full job description semantically, not just keyword-scans it
- **Contextual Relevance** — Vector similarity between JD and resume chunks captures semantic fit even when terminology differs
- **Signal Integration** — Combines two AI signals: dense vector similarity (60%) + local LLM reasoning (40%)
- **Precise Shortlist** — Delivers a ranked, scored list of candidates with strengths, gaps, and a hire recommendation

---

## 📸 Screenshots

<details>
<summary>Click to view screenshots</summary>

### 1. Landing Page — Dark Mode Hero
![Landing Page](screenshots/Screenshot%202026-03-26%20152606.png)

### 2. Upload Interface — Job Description & Candidates
![Upload Interface](screenshots/Screenshot%202026-03-26%20152632.png)

### 3. Results Dashboard — Top Talent Overview
![Results Dashboard](screenshots/Screenshot%202026-03-26%20152724.png)

### 4. Candidate Analysis — Ranking, Strengths & Gaps
![Candidate Analysis](screenshots/Screenshot%202026-03-26%20152744.png)

</details>

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 📄 **PDF Resume Parsing** | Extracts text from PDF resumes using `pdf-parse` |
| 🧠 **Local RAG Pipeline** | Fully offline AI ranking — runs on your machine via Ollama |
| 🔢 **Semantic Embeddings** | `nomic-embed-text` converts JD and resumes into dense vectors for deep semantic matching |
| 🤖 **Local LLM Analysis** | `llama3.2` analyses each candidate and generates structured insights |
| 📊 **Hybrid Scoring Engine** | Combines cosine similarity (60%) + LLM assessment (40%) for accurate rankings |
| 📈 **Interactive Dashboard** | SVG radial score charts and summary panels for instant insights |
| 🏅 **Candidate Ranking** | Ranked shortlist with match scores, strengths, gaps, and hire recommendation |
| 🎨 **Premium UI** | Dark-mode SaaS design with micro-animations and responsive layout |
| 📝 **Dual JD Input** | Supports both pasting text and uploading a PDF job description |
| 📎 **Bulk Resume Upload** | Drag-and-drop interface for uploading multiple resumes simultaneously |
| 🔒 **Privacy First** | Everything is processed locally — no data leaves your machine |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (React + Vite)                    │
│   JD Input (text/PDF)  →  Resume Upload  →  Results Dashboard│
└─────────────────────────┬───────────────────────────────────┘
                          │  POST /api/analyze
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVER (Express + TypeScript)             │
│                                                             │
│  Multer → pdf-parse → ┌──────────────────────────────────┐ │
│                        │         RAG Pipeline              │ │
│                        │                                  │ │
│                        │  1. Embed JD (nomic-embed-text)  │ │
│                        │  2. Chunk + Embed Resumes        │ │
│                        │  3. Cosine Similarity Scoring    │ │
│                        │  4. LLM Analysis (llama3.2)      │ │
│                        │  5. Combine Scores (60/40 split) │ │
│                        │  6. Sort → CandidateAnalysis[]   │ │
│                        └────────────────┬─────────────────┘ │
└─────────────────────────────────────────┼─────────────────┘
                                          │
                          ┌───────────────▼───────────────┐
                          │    Ollama  (localhost:11434)   │
                          │  • nomic-embed-text (vectors)  │
                          │  • llama3.2 (chat / reasoning) │
                          └───────────────────────────────┘
```

---

## 🧠 RAG Pipeline — How It Works

The scoring system combines two complementary signals:

### 1. Semantic Similarity (60% weight)
- The job description is embedded into a dense vector using `nomic-embed-text`
- Each resume is split into overlapping 512-character chunks, and each chunk is embedded
- **Cosine similarity** is computed between the JD vector and every resume chunk
- The average of the top-3 chunk similarities gives a raw semantic score (0–1)

### 2. LLM Assessment (40% weight)
- For each candidate, the JD and resume text are passed to `llama3.2`
- The LLM returns structured JSON: `candidateName`, `llmScore` (0–100), `keyStrengths[]`, `keyGaps[]`
- This captures nuanced reasoning that pure vector similarity may miss

### Combined Score Formula
```
matchScore = round((semanticScore × 100 × 0.6) + (llmScore × 0.4))
```

| Score Range | Recommendation |
|---|---|
| 80 – 100 | ✅ Strong Fit |
| 50 – 79 | 🟡 Moderate Fit |
| 0 – 49 | ❌ Not Fit |

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| **React 19** | UI framework with hooks-based architecture |
| **TypeScript** | Type-safe development |
| **Vite** | Lightning-fast build tool and dev server |
| **TailwindCSS 4** | Utility-first CSS framework |
| **Axios** | HTTP client for API communication |
| **React Icons** | Icon library |

### Backend
| Technology | Purpose |
|---|---|
| **Node.js 18+ / Express** | REST API server |
| **TypeScript** | Type-safe server-side development |
| **Ollama** | Local LLM runtime (embedding + chat inference) |
| **nomic-embed-text** | High-quality text embedding model |
| **llama3.2** | Local chat LLM for candidate analysis |
| **pdf-parse** | PDF text extraction |
| **Multer** | Multipart file upload handling |
| **dotenv** | Environment variable management |

---

## 📋 Prerequisites

- **Node.js** 18+ and **npm**
- **[Ollama](https://ollama.com)** installed and running

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd SkillMatch
```

### 2. Install Ollama models

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 3. Set up the Backend

```bash
cd server
npm install
```

The `.env` file is already configured with sensible defaults. To customize, copy the example:

```bash
cp .env.example .env
```

Default `.env` contents:
```env
PORT=3001
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_CHAT_MODEL=llama3.2
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### 4. Set up the Frontend

```bash
cd ../client
npm install
```

---

## 💡 Usage

### Start Ollama (if not already running)

```bash
ollama server
```

### Start the Backend Server

```bash
cd server
npm run dev
```

The API server will start at `http://localhost:3001`. You'll see a startup health check:

```
🚀 Server running on http://localhost:3001
🧠 Local LLM Configuration:
   Ollama:      http://localhost:11434
   Chat Model:  llama3.2
   Embed Model: nomic-embed-text
   Status:      ✅ Connected (2 models available)
```

### Start the Frontend Dev Server

```bash
cd client
npm run dev
```

Open `http://localhost:5173`

### Using the Application

1. **Enter a Job Description** — Paste text directly or upload a PDF
2. **Upload Resumes** — Drag and drop one or more candidate resumes (PDF format, up to 20 at once)
3. **Click "Analyze Resumes"** — The RAG pipeline processes all resumes locally
4. **Review Results** — Explore the ranked shortlist with scores, strengths, gaps, and hire recommendations

---

## 📊 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | Main analysis — JD + resumes → ranked candidates |
| `POST` | `/api/upload-jd` | Upload/validate a JD (PDF or text) |
| `POST` | `/api/upload-resumes` | Upload and preview resume files |
| `GET` | `/api/health/llm` | Check Ollama connectivity and available models |
| `GET` | `/health` | Basic server health check |

---

## 📁 Project Structure

```
SkillMatch/
├── client/                          # React Frontend (Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── CandidateCard.tsx    # Individual candidate result card
│   │   │   ├── JDInput.tsx          # Job description input (text/PDF)
│   │   │   ├── ResumeDropzone.tsx   # Resume upload drag-and-drop
│   │   │   ├── ResultsDashboard.tsx # Analysis results dashboard
│   │   │   └── LoadingSpinner.tsx   # Loading state component
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx      # Hero landing page
│   │   │   ├── AnalyzePage.tsx      # Upload & configure analysis
│   │   │   └── ResultsPage.tsx      # Results route
│   │   ├── services/
│   │   │   └── api.ts               # Axios API client (proxied to :3001)
│   │   └── types/
│   │       └── index.ts             # Shared TypeScript interfaces
│   ├── vite.config.ts               # Vite proxy config (/api → :3001)
│   └── package.json
│
├── server/                          # Express Backend
│   ├── src/
│   │   ├── middleware/
│   │   │   └── errorHandler.ts      # Global Express error handler
│   │   ├── routes/
│   │   │   └── analyze.ts           # /api/analyze + upload routes
│   │   ├── services/
│   │   │   ├── ollamaService.ts     # Ollama REST wrapper (embed/chat)
│   │   │   ├── ragService.ts        # RAG pipeline orchestration
│   │   │   └── pdfService.ts        # PDF text extraction
│   │   └── index.ts                 # Express server entry point
│   ├── .env                         # Environment variables
│   ├── .env.example                 # Environment template
│   ├── package.json
│   └── tsconfig.json
│
├── screenshots/                     # App screenshots
├── .gitignore
└── README.md
```

---

## 🔮 Future Enhancements

- [ ] Streaming analysis updates (WebSocket progress for large batches)
- [ ] Support for DOCX resumes
- [ ] Custom model selection in the UI
- [ ] Persistent history of past analyses
- [ ] Export ranked results as CSV / PDF report
- [ ] Integration with ATS (Applicant Tracking Systems)
- [ ] Multi-language resume support
- [ ] Adjustable scoring weights (semantic vs. LLM) via UI slider

---

## 🚧 Challenges & Solutions

### Challenge 1: Unstructured Resume Formats
**Problem:** Resumes come in wildly different formats — multi-column, tables, creative layouts.
**Solution:** `pdf-parse` extracts raw text and the LLM handles interpreting it regardless of layout.

### Challenge 2: Accurate Candidate-JD Matching
**Problem:** Simple keyword matching misses context (e.g., "React" vs "React Native").
**Solution:** Dense vector embeddings capture semantic similarity. The LLM layer adds contextual reasoning on top.

### Challenge 3: Fully Local, No API Key
**Problem:** Cloud LLM APIs introduce cost, latency, and privacy concerns.
**Solution:** Ollama runs `llama3.2` and `nomic-embed-text` locally. Zero external calls, zero API keys, full privacy.

---

## 🙏 Acknowledgments

- **[Ollama](https://ollama.com)** for making local LLM inference accessible
- **[nomic-embed-text](https://huggingface.co/nomic-ai/nomic-embed-text-v1)** for high-quality open-source embeddings
- **[Meta Llama 3.2](https://llama.meta.com/)** for the capable local chat model
- **[pdf-parse](https://www.npmjs.com/package/pdf-parse)** for PDF text extraction
- **[TailwindCSS](https://tailwindcss.com)** for rapid UI development
