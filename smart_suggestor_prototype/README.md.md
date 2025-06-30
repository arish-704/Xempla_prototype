
<h1 align="center">🧠 Xempla Smart Suggestor AI</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Xempla-Decision%20Support-blueviolet?style=for-the-badge" />
  <img src="https://img.shields.io/badge/AI-Smart%20Suggestor-success?style=for-the-badge&logo=openai" />
  <img src="https://img.shields.io/badge/Prototype-Ready-orange?style=for-the-badge" />
</p>

<p align="center"><b>A decision-first assistant designed to empower O&M professionals using AI-driven insights aligned with Xempla's philosophy.</b></p>

---

## 💡 Vision

The future of operations & maintenance lies in decision-first intelligence. This prototype aligns with Xempla’s Discover → Investigate → Implement → Evaluate cycle.

> ❝ Instead of just showing data, we aim to help act on it. ❞

---

## 🚀 Key Highlights

| 🔍 Problem                           | 💡 Smart Suggestor Solution                                            |
|------------------------------------|------------------------------------------------------------------------|
| Data overload, unclear next steps | 🧠 Translates sensor logs into actionable suggestions                  |
| Technicians lack context           | 💬 Semantic chatbot provides historical + technical insights           |
| Unstructured decision logs         | 📓 Captures and evaluates each action using structured feedback        |

---

## 🛠 Tech Stack

| Tool/Library         | Role                                       |
|----------------------|--------------------------------------------|
| Python               | Backend logic                              |
| Streamlit (optional) | UI prototype                               |
| HuggingFace          | Local language model for reasoning         |
| SQLite               | Minimal local decision logging              |
| Mermaid.js           | Diagrams and flow visualization (markdown) |

---

## 🔄 How It Works

```
flowchart TD
    A[User Query / Prompt] --> B[Text Preprocessing]
    B --> C[Decision Logic Engine]
    C --> D[Suggested Action or Explanation]
    D --> E[Evaluation Recommendation]
    E --> F[Output Response]
```

---

## 📂 Project Structure

```
xempla-smart-suggestor/
├── README.md
├── suggestor_engine.py          # Core logic for AI recommendations
├── Xempla_Smart_Suggestor.ipynb # Notebook explaining prototype
├── flowchart.png                # Decision flowchart (image)
├── requirements.txt             # Dependencies
└── .env                         # (Optional) for API keys
```

---

## ✨ Sample Interaction

```plaintext
User: Why did Pump A spike last night?

AI: Based on historical logs, Pump A showed similar spikes during filter clogging last quarter. 
Recommend checking inlet pressure. Last maintenance was 34 days ago.

User: What was done last time?

AI: Previous fix involved replacing the pre-filter and increasing inspection frequency.
```

---

## 📦 requirements.txt

```txt
transformers
pandas
streamlit
openai
scikit-learn
```

---

## 📈 Future Possibilities

- IoT sensor integration (real-time inference)
- Team-level task tracking
- QR-based checklists for on-ground workflows
- Dynamic model tuning based on usage logs

---

## 🤝 Contribution

If you have ideas to evolve this into a full microservice for Xempla’s platform — feel free to fork and suggest!

---

## 📨 Submission

This repository and prototype were submitted as part of my application to [Xempla](https://xempla.io).

📹 A video walkthrough is also attached to showcase how this aligns with Xempla's vision.

---

## 👨‍💻 Author

Made with intent by [Arish Shahid](https://www.linkedin.com/in/arishshahid)

---
