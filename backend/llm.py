# backend/llm.py

import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os


class KnowledgeBaseEngine:
    def __init__(self):
        self._llm = None
        self._embeddings = None
        self.retriever = None
        self.docs = []
        self.initialized = False

    # ---------------- LLM ----------------
    @property
    def llm(self):
        if not self._llm:
            self._llm = ChatOllama(
                model="llama3.2:1b",
                temperature=0.3,
                num_predict=150,
                num_ctx=2048
            )
        return self._llm

    # ---------------- Embeddings ----------------
    @property
    def embeddings(self):
        if not self._embeddings:
            self._embeddings = OllamaEmbeddings(model="llama3.2:1b")
        return self._embeddings

    # ---------------- KB INIT (CSV) ----------------
    def ensure_kb_initialized(self):
        if self.initialized:
            return

        kb_path = os.path.join("backend", "data", "knowledge_base.csv")
        print("Initializing Knowledge Base from CSV...")

        df = pd.read_csv(kb_path)

        self.docs = []
        texts = []

        for _, row in df.iterrows():
            text = f"""
            Title: {row.get('title')}
            Category: {row.get('category', 'General')}
            Tags: {row.get('tags', '')}
            Content: {row.get('content', '')}
            """
            texts.append(text.strip())
            self.docs.append(text.strip())

        self.retriever = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings
        ).as_retriever(search_kwargs={"k": 3})

        self.initialized = True
        print(f"KB initialized with {len(self.docs)} articles")

    # ---------------- Article Recommendation ----------------
    def recommend_articles(self, ticket_text: str):
        self.ensure_kb_initialized()

        docs = self.retriever.invoke(ticket_text)

        # ✅ RETURN STRINGS ONLY
        return [d.page_content for d in docs]

    # ---------------- AI SOLUTION ----------------
    def generate_solution(self, ticket_text: str) -> str:
        self.ensure_kb_initialized()

        articles = self.recommend_articles(ticket_text)
        if not articles:
            return "No relevant knowledge base articles found."

        prompt = ChatPromptTemplate.from_template(
            """
            You are an IT support assistant.
            Use the following knowledge to answer the ticket briefly and clearly.

            Knowledge:
            {context}

            Ticket:
            {ticket}
            """
        )

        chain = prompt | self.llm | StrOutputParser()

        # ✅ RETURNS PURE STRING
        return chain.invoke({
            "context": articles[0],
            "ticket": ticket_text
        })


# Singleton instance
kb_engine = KnowledgeBaseEngine()
