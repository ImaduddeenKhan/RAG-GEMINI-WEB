# server/rag.py
import os
import tempfile
from typing import Dict, Any, List

from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_community.vectorstores import FAISS            # <-- updated import
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA

load_dotenv()

class RAGEngine:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.vectorstore = None
        self.retriever = None
        self.qa = None
        self.doc_count = 0
        self.file_name = None

    def _load_docs(self, file_path: str, file_name: str):
        if file_name.lower().endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif file_name.lower().endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")
        return loader.load()

    def build_index(self, file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            docs = self._load_docs(tmp_path, file_name)
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_documents(docs)

            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
            self.retriever = self.vectorstore.as_retriever()
            self.qa = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=self.retriever,
                return_source_documents=True
            )
            self.doc_count = len(chunks)
            self.file_name = file_name
            return {
                "status": "ok",
                "message": "Index built successfully",
                "chunks": self.doc_count,
                "file": file_name
            }
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    def ask(self, question: str) -> Dict[str, Any]:
        if not self.qa:
            return {"status": "error", "message": "No document uploaded yet."}

        result = self.qa(question)
        answer = result.get("result", "")
        source_docs = result.get("source_documents", [])

        sources: List[Dict[str, Any]] = []
        for i, d in enumerate(source_docs, 1):
            meta = dict(d.metadata or {})
            page = meta.get("page", None)
            text = (d.page_content or "").strip().replace("\n", " ")
            snippet = text[:400] + ("..." if len(text) > 400 else "")
            sources.append({
                "id": i,
                "page": page,
                "metadata": meta,
                "snippet": snippet
            })

        return {
            "status": "ok",
            "answer": answer,
            "sources": sources
        }

# singleton
engine = RAGEngine()
