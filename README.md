# AI Support Engine 🚀

An AI-powered system that analyzes support tickets and recommends the most relevant knowledge base articles using Ollama + LangChain.

## Features
- Ticket understanding using LLM
- Knowledge base recommendations
- Pandas-based LangChain agent
- Local LLM (Ollama)
- FastAPI backend
- Deployable architecture

## Tech Stack
- Python
- FastAPI
- LangChain
- Ollama
- Pandas
- Streamlit

## Setup
```bash
pip install -r requirements.txt
ollama run tinyllama
uvicorn backend.main:app --reload
