# 🔍 AI Hallucination Risk Auditor

**Corporate AI Integrity Governance System | India Business Context**

The first MBA-level framework to systematically measure and govern AI hallucination
risk in Indian business decision-making — across Finance, HR, Legal, Marketing,
and Operations.

---

## 📁 Project Structure

```
ai_hallucination_auditor/
├── app.py                        # ← Streamlit entry point (Home page)
├── config.py                     # ← All constants and configuration
├── requirements.txt              # ← Python dependencies
├── README.md
├── .streamlit/
│   └── config.toml               # ← Dark theme + server settings
├── pages/
│   ├── 1_Dashboard.py            # ← Charts and KPI overview
│   ├── 2_Run_Audit.py            # ← LLM testing runner
│   ├── 3_Results_Log.py          # ← Filterable results + export
│   └── 4_CAIGS_Framework.py      # ← Governance scorecard
├── auditor/
│   ├── __init__.py
│   ├── scorer.py                 # ← Hallucination scoring engine
│   ├── llm_runner.py             # ← Multi-LLM API calls
│   └── caigs.py                  # ← CAIGS scorecard computation
└── data/
    └── ground_truth.json         # ← 50 verified India business prompts
```

---

## 🚀 Deploy on Streamlit Cloud (Free — Recommended)

### Step 1 — Push to GitHub

```bash
cd ai_hallucination_auditor
git init
git add .
git commit -m "Initial commit — AI Hallucination Auditor"
# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/ai-hallucination-auditor.git
git branch -M main
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud

1. Go to **https://share.streamlit.io**
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your repository: `ai-hallucination-auditor`
5. Set **Main file path**: `app.py`
6. Click **"Deploy!"**

Your app will be live at:
`https://YOUR_USERNAME-ai-hallucination-auditor-app-XXXX.streamlit.app`

### Step 3 — Add API Keys as Secrets (Important!)

In Streamlit Cloud → Your App → **Settings → Secrets**, add:

```toml
OPENAI_API_KEY    = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
GOOGLE_API_KEY    = "AIza..."
```

Then in `pages/2_Run_Audit.py`, replace the text_input defaults with:
```python
openai_key    = st.text_input("OpenAI Key",    value=st.secrets.get("OPENAI_API_KEY", ""))
anthropic_key = st.text_input("Anthropic Key", value=st.secrets.get("ANTHROPIC_API_KEY", ""))
google_key    = st.text_input("Google Key",    value=st.secrets.get("GOOGLE_API_KEY", ""))
```

---

## 🤗 Deploy on Hugging Face Spaces (Free)

### Step 1 — Create a Space

1. Go to **https://huggingface.co/spaces**
2. Click **"Create new Space"**
3. Name it: `ai-hallucination-auditor`
4. Select **SDK: Streamlit**
5. Select **Hardware: CPU Basic (Free)**
6. Click **"Create Space"**

### Step 2 — Upload files

**Option A — Via Web UI (easiest):**
1. In your Space, click **"Files"** tab → **"Add file"**
2. Upload all files maintaining this folder structure:
   - `app.py` (root)
   - `config.py` (root)
   - `requirements.txt` (root)
   - `pages/1_Dashboard.py`
   - `pages/2_Run_Audit.py`
   - `pages/3_Results_Log.py`
   - `pages/4_CAIGS_Framework.py`
   - `auditor/__init__.py`
   - `auditor/scorer.py`
   - `auditor/llm_runner.py`
   - `auditor/caigs.py`
   - `data/ground_truth.json`
   - `.streamlit/config.toml`

**Option B — Via Git:**
```bash
git clone https://huggingface.co/spaces/YOUR_HF_USERNAME/ai-hallucination-auditor
cp -r ai_hallucination_auditor/* ai-hallucination-auditor/
cd ai-hallucination-auditor
git add .
git commit -m "Deploy AI Hallucination Auditor"
git push
```

### Step 3 — Add API Keys as Secrets

In Hugging Face Space → **Settings → Variables and Secrets**:

| Name | Value |
|------|-------|
| `OPENAI_API_KEY` | `sk-...` |
| `ANTHROPIC_API_KEY` | `sk-ant-...` |
| `GOOGLE_API_KEY` | `AIza...` |

Then update `pages/2_Run_Audit.py` to read from environment:
```python
import os
openai_key    = st.text_input("OpenAI Key",    value=os.environ.get("OPENAI_API_KEY", ""))
anthropic_key = st.text_input("Anthropic Key", value=os.environ.get("ANTHROPIC_API_KEY", ""))
google_key    = st.text_input("Google Key",    value=os.environ.get("GOOGLE_API_KEY", ""))
```

---

## 💻 Run Locally

```bash
# 1. Clone / download the project
cd ai_hallucination_auditor

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file (optional, for local use)
echo "OPENAI_API_KEY=sk-..."    >> .env
echo "ANTHROPIC_API_KEY=sk-..." >> .env
echo "GOOGLE_API_KEY=AIza..."   >> .env

# 5. Run
streamlit run app.py
```

App opens at: **http://localhost:8501**

---

## 🔑 Getting API Keys

| Provider | URL | Free Tier |
|----------|-----|-----------|
| OpenAI   | https://platform.openai.com/api-keys | $5 credit on signup |
| Anthropic | https://console.anthropic.com | $5 credit on signup |
| Google Gemini | https://aistudio.google.com/app/apikey | Free tier available |

---

## 📊 How to Use

1. **Open the app** → Home page shows overview and test suite coverage
2. **Go to 🧪 Run Audit** → Enter your API key(s) in the sidebar
3. **Select domains** (e.g., Finance + Legal) and a model (e.g., GPT-4o)
4. **Set prompts per domain** (5–10 for quick test, up to 10 for full)
5. **Click ▶ Start Audit** → Watch results stream live
6. **Go to 📊 Dashboard** → See hallucination rates by domain
7. **Go to 📋 Results Log** → Filter, inspect, download CSV/Excel
8. **Go to 🏛 CAIGS Framework** → Get your A–D governance grade

---

## 🧠 Research Methodology

### Scoring Formula
```
composite_score = (semantic_similarity × w_sem)
                + (numerical_accuracy  × w_num)
                + (rouge_l             × w_rouge)
                + (keyword_coverage    × 0.10)

# Weights by risk level:
# critical: sem=0.30, num=0.50, rouge=0.20
# high:     sem=0.40, num=0.40, rouge=0.20
# medium:   sem=0.50, num=0.30, rouge=0.20
# low:      sem=0.60, num=0.20, rouge=0.20
```

### CAIGS Score Formula
```
caigs_score = 100 - Σ(domain_weighted_hallucination_rate)

# Domain weights:
# Finance=30%, Legal=25%, HR=20%, Operations=15%, Marketing=10%

# Grade:  A=85+,  B=70+,  C=55+,  D=<55
```

---

## 📄 Citation (for Research Use)

```
AI Hallucination Risk Auditor: A Corporate Governance Framework
for LLM Output Verification in Indian Business Contexts.
CAIGS v1.0 — Corporate AI Integrity Governance Scorecard.
[Your Name], [Institution], 2024.
```

---

## ⚠️ Disclaimer

Ground truth is based on Indian regulations as of 2024. Always verify with
qualified CA / legal professionals for actual business decisions. This tool
is for research and educational purposes only.
