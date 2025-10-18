🌌 J.A.R.V.I.S. – Your Personal AI Assistant

Jarvis is an AI virtual assistant designed to enhance learning and development workflows. It’s a futuristic companion that understands voice or text commands, summarizes documents, and connects with APIs — powered by the Gemini AI model.

🚀 How to Run the Project Locally
🧠 Frontend Setup (Vite + React)

Open the terminal in the frontend folder.

Run the following commands:

npm install
npm run dev


Your app will start locally — open the URL shown in the terminal (usually http://localhost:5173).

⚙️ Backend Setup (FastAPI)

Open a new terminal in the backend folder.

Install dependencies and run the server:

pip install uv
uv run uvicorn main:app


The backend will start on:

http://127.0.0.1:8000


Ensure your frontend API calls use this backend URL while running locally.

🎯 Epic Overview
🌟 Features

Chat + Voice Interaction:
Talk to Jarvis using text or your voice. It uses the Web Speech API for voice input and can respond using TTS.

PDF Summarization:
Upload PDFs for Jarvis to summarize or extract insights using Gemini AI.

Webpage Summarization:
Enter a URL and get a summarized version of the article or content.

Spotify Control:
Manage playback (play, pause, skip) using natural voice commands.

Gemini AI Integration:
All natural language understanding and summarization tasks are powered by the Gemini API.

🧩 Tech Stack
Layer	Tech
Frontend	Vite + React, 
Voice I/O	Web Speech API, pyttsx3
Backend	Python + FastAPI
AI API	Gemini API
PDF Parsing	PyMuPDF
Web Scraping	newspaper3k, BeautifulSoup
Spotify API	Spotify Web API
🧠 Core AI Concepts

Prompting:
User input is converted into structured prompts for Gemini to process (chat, summarize, or perform actions).

Structured Output:
Gemini returns data in JSON for predictable responses (summaries, Spotify commands, etc.).

Function Calling:
Jarvis connects Gemini’s understanding to tools like Spotify or PDF summarizers.

RAG (Retrieval-Augmented Generation):
Enables grounded responses using embeddings from PDFs or web content — minimizing hallucinations.

