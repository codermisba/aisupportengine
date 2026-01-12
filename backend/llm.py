# # import requests
# # import json

# # OLLAMA_URL = "http://localhost:11434/api/generate"
# # MODEL_NAME = "llama3.2:1b"


# # def query_llm(prompt: str) -> str:
# #     """
# #     Sends a prompt to the local Ollama LLM and returns the response text.
# #     """
# #     payload = {
# #         "model": MODEL_NAME,
# #         "prompt": prompt,
# #         "stream": False
# #     }

# #     response = requests.post(OLLAMA_URL, json=payload, timeout=120)
# #     response.raise_for_status()

# #     data = response.json()
# #     return data.get("response", "").strip()


# # llm.py
# import requests
# import pandas as pd
# from typing import List, Dict

# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2:1b"

# # ---------------------------
# # Load Knowledge Base
# # ---------------------------
# KB_PATH = "knowledge_base_sample.csv"
# kb_df = pd.read_csv(KB_PATH)

# # ---------------------------
# # Simple Agent Memory
# # ---------------------------
# conversation_memory: List[Dict[str, str]] = []

# def update_memory(user: str, assistant: str):
#     conversation_memory.append({
#         "user": user,
#         "assistant": assistant
#     })
#     # keep last 5 interactions
#     if len(conversation_memory) > 5:
#         conversation_memory.pop(0)

# # ---------------------------
# # Ollama Query
# # ---------------------------
# def query_llm(prompt: str, temperature: float = 0.2) -> str:
#     payload = {
#         "model": MODEL_NAME,
#         "prompt": prompt,
#         "temperature": temperature,
#         "stream": False
#     }
#     response = requests.post(OLLAMA_URL, json=payload, timeout=120)
#     response.raise_for_status()
#     return response.json().get("response", "").strip()

# # ---------------------------
# # Agent Reasoning
# # ---------------------------
# def recommend_with_agent(ticket_text: str, top_k: int = 3):
#     kb_snippets = "\n".join(
#         f"""
# Title: {row['title']}
# Category: {row.get('category', 'General')}
# Tags: {row.get('tags', '')}
# Content: {row['content'][:200]}
# """
#         for _, row in kb_df.iterrows()
#     )

#     memory_text = "\n".join(
#         f"User: {m['user']}\nAssistant: {m['assistant']}"
#         for m in conversation_memory
#     )

#     prompt = f"""
# You are an AI Support Agent.

# Previous Context:
# {memory_text}

# Knowledge Base:
# {kb_snippets}

# Ticket:
# {ticket_text}

# TASK:
# 1. Recommend TOP {top_k} most relevant articles
# 2. Use article title, category, tags
# 3. Give relevance score between 0 and 1
# 4. Return ONLY valid JSON in this format:

# [
#   {{
#     "title": "",
#     "category": "",
#     "tags": "",
#     "score": 0.0,
#     "reason": ""
#   }}
# ]
# """

#     response = query_llm(prompt)
#     update_memory(ticket_text, response)

#     return response
