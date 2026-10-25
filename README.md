# Nexora AI 🚀 

**Nexora AI** is a modern, full-stack AI assistant designed to provide an interactive conversational experience with streaming responses and persistent chat history.

🌐 **Live Demo:** [https://nexora-1-nxe6.onrender.com/](https://nexora-1-nxe6.onrender.com/)

📂 **GitHub Repository:** [Nexora](https://github.com/bhaveshkumbhalwar/Nexora)

## ✨ Features

- **AI-powered conversations** — Ask questions and receive AI-generated responses.
- **Streaming responses** — View responses as they are generated.
- **Chat history** — Save and retrieve conversations.
- **Responsive UI** — Clean interface built for a smooth user experience.
- **REST API** — FastAPI backend for handling chat requests.
- **Cloud deployment** — Frontend and backend hosted on Render.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| React + Vite | Frontend |
| TypeScript | Type-safe development |
| Tailwind CSS | UI styling |
| Python + FastAPI | Backend API |
| SQLAlchemy + SQLite | Conversation storage |
| Gemini-compatible API | AI-generated responses |
| Render | Deployment |

## 🏗️ Architecture

```text
User
  ↓
React + Vite Frontend
  ↓
FastAPI Backend
  ↓
Gemini-compatible AI API
  ↓
Streaming Response
  ↓
User Interface
```

Conversation history is managed through the backend and stored in the database.

## 🚀 Run Locally

**1. Clone the repository**

```bash
git clone https://github.com/bhaveshkumbhalwar/Nexora.git
cd Nexora
```

**2. Set up the backend**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure the required environment variables using `backend/.env.example`, then start the backend:

```bash
uvicorn app.main:app --reload
```

**3. Set up the frontend**

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Configure `VITE_API_URL` to point to your local backend API, following the project's environment configuration.

## 🔐 Security

- Keep API keys and credentials in backend environment variables.
- Never commit `.env` files or secrets to GitHub.
- Configure CORS to allow trusted frontend origins.

## 👨‍💻 Author

**Bhavesh Kumbhalwar**

- GitHub: [@bhaveshkumbhalwar](https://github.com/bhaveshkumbhalwar)
- Project: [Nexora AI](https://nexora-1-nxe6.onrender.com/)

## 📄 License


