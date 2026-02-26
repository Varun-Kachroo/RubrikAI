# 📊 RubriqAI — AI Rubric Evaluation Assistant

RubriqAI is an intelligent, AI-powered grading tool built with **Streamlit** and powered by **Groq's LLM API**. It enables educators to evaluate student answers criterion-by-criterion using customizable rubrics, supporting single questions, multi-question assignments, and live online tests.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Single Question Mode** | Grade one question at a time with a custom rubric |
| 📚 **Multi-Question Assignment** | Bundle multiple questions under one assignment with a shared rubric |
| 🌐 **Online Test Hosting** | Host live tests with unique codes; students submit via browser |
| 🤖 **AI Rubric Generation** | Let AI auto-generate an appropriate rubric from your questions |
| 📋 **CSV Batch Import** | Upload a CSV with questions + student answers for bulk grading |
| 💾 **Assignment Database** | Save, load, rename, export, and delete assignments persistently |
| 📊 **Evaluation History** | View per-student scores, download assessment reports as CSV |
| 🔍 **Similarity Analysis** | Detect answer similarity across students |
| 📝 **Model Answer Generation** | Generate an ideal model answer for any question + rubric |

---

## 🗂️ Project Structure

```
rubrikAI/
├── app.py                  # Main Streamlit application (entry point)
├── evaluator.py            # Core AI evaluation logic (Groq API)
├── prompts.py              # Prompt templates for evaluation & rubric generation
├── multi_question.py       # Multi-question assignment management
├── database.py             # SQLite database layer (assignments & evaluations)
├── test_hosting.py         # Online test hosting (create & manage live tests)
├── similarity_analysis.py  # Answer similarity detection utilities
├── utils.py                # Score calculation & performance helpers
├── styles.py               # UI styling helpers
├── ui_components.py        # Reusable Streamlit UI components
├── api_simple.py           # Simple REST API server for online test submissions
├── launch.py               # Launcher script (starts app + API together)
├── index.html              # Teacher dashboard for online tests
├── student.html            # Student portal for submitting online test answers
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (API keys) — not committed
```

---

## 🚀 Running Locally

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/rubrikAI.git
cd rubrikAI
```

### 2. Create & Activate a Virtual Environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Your API Key

Create a `.env` file in the project root:

```bash
touch .env
```

Add your [Groq API key](https://console.groq.com) to `.env`:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

### 5. Launch the Application

**Option A — Streamlit only (recommended for grading):**

```bash
streamlit run app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

**Option B — Full launch (Streamlit + API server for Online Test mode):**

```bash
python launch.py
```

This starts:
- Streamlit app at [http://localhost:8501](http://localhost:8501)
- REST API server at [http://localhost:8000](http://localhost:8000)
- Student portal at [http://localhost:8000/student.html](http://localhost:8000/student.html)

---

## 📋 CSV Import Format

You can batch-import assignments using a CSV file with three sections:

```csv
CRITERIA,TOTAL MARKS
Understanding,5
Accuracy,5
Explanation,3

QUESTIONS,
1,Explain the water cycle.
2,What causes seasons?

STUDENTS,
Alice,"Water evaporates from oceans...","Earth's axial tilt causes..."
Bob,"Water goes up then comes down.","Earth moves around sun."
```

Download ready-to-use templates from the **CSV Templates** section in the sidebar.

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GROQ_API_KEY` | Your Groq LLM API key | ✅ Yes |

Get a free API key at [https://console.groq.com](https://console.groq.com).

---

## 🛠️ Tech Stack

- **Frontend / UI:** [Streamlit](https://streamlit.io)
- **AI / LLM:** [Groq API](https://console.groq.com) (LLaMA-based models)
- **Database:** SQLite (via Python's `sqlite3`)
- **Data Processing:** Pandas, NumPy, scikit-learn
- **Language:** Python 3.9+

---

## 📄 License

This project is open-source. Feel free to fork, modify, and use it for educational purposes.
