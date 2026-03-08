# =============================================================
# Anil Pathak's Agentic Healthcare Assistant
# Capstone Project — Agentic Healthcare Assistant for Medical
#                    Task Automation
# =============================================================
# Submitted by  : Anil Pathak
# Generated with: Claude (Anthropic) AI Coding Assistant
# File          : tools/rag_tool.py
# Purpose       : RAG (Retrieval-Augmented Generation) pipeline.
#                 Builds and queries a FAISS vector store from
#                 patient PDF reports. Retrieves semantically
#                 relevant chunks and generates structured medical
#                 summaries using GPT-4o-mini.
#                 Compatible with langchain 1.2.x / openai 2.x —
#                 does not use deprecated RetrievalQA chain.
# =============================================================

import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

# Import centralised paths from config
from config import REPORTS_DIR, VECTOR_STORE_DIR as VECTOR_STORE_PATH

load_dotenv()


# ── Embeddings helper ─────────────────────────────────────────

def _get_embeddings() -> OpenAIEmbeddings:
    """
    Initialise and return the OpenAI embeddings model.
    Uses text-embedding-3-small for cost-effective dense retrieval.

    Returns:
        OpenAIEmbeddings: Configured embeddings instance.
    """
    return OpenAIEmbeddings(model="text-embedding-3-small")


# ── Vector store management ───────────────────────────────────

def build_vector_store(force_rebuild: bool = False) -> FAISS | None:
    """
    Build a FAISS vector store from all PDF reports in the reports
    directory, or load an existing one if already built.

    Each PDF page is split into overlapping chunks and embedded.
    Metadata (source file, patient name hint) is attached to each
    chunk to support patient-specific filtering during retrieval.

    Args:
        force_rebuild (bool): If True, rebuild even if a saved store
                              exists. Useful after adding new PDFs.

    Returns:
        FAISS | None: Loaded or newly built vector store,
                      or None if no PDFs are available.
    """
    # Load existing vector store if available and rebuild not forced
    if os.path.exists(VECTOR_STORE_PATH) and not force_rebuild:
        print("📦 Loading existing vector store...")
        return FAISS.load_local(
            VECTOR_STORE_PATH,
            _get_embeddings(),
            allow_dangerous_deserialization=True
        )

    print("🔨 Building vector store from PDF reports...")
    all_docs = []

    if not os.path.exists(REPORTS_DIR):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        return None

    pdf_files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".pdf")]
    if not pdf_files:
        print("⚠️  No PDF reports found in data/reports/")
        return None

    # Load and tag each PDF with patient metadata
    for pdf_file in pdf_files:
        pdf_path = os.path.join(REPORTS_DIR, pdf_file)
        try:
            loader = PyPDFLoader(pdf_path)
            docs   = loader.load()
            for doc in docs:
                # Attach source and patient hint for retrieval filtering
                doc.metadata["source_file"]  = pdf_file
                doc.metadata["patient_hint"] = (
                    pdf_file.replace("sample_report_", "")
                             .replace(".pdf", "")
                             .title()
                )
            all_docs.extend(docs)
            print(f"  ✅ Loaded: {pdf_file} ({len(docs)} pages)")
        except Exception as e:
            print(f"  ❌ Error loading {pdf_file}: {e}")

    if not all_docs:
        return None

    # Split documents into overlapping chunks for better retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ".", " "]
    )
    chunks = splitter.split_documents(all_docs)
    print(f"  📄 Total chunks created: {len(chunks)}")

    # Build FAISS index and persist to disk
    embeddings  = _get_embeddings()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
    vectorstore.save_local(VECTOR_STORE_PATH)
    print(f"  💾 Vector store saved to: {VECTOR_STORE_PATH}")

    return vectorstore


# ── Public tool functions ────────────────────────────────────

def retrieve_patient_history(patient_name: str, query: str = "") -> str:
    """
    Retrieve and summarise a patient's medical history from PDF reports
    using RAG (Retrieval-Augmented Generation).

    Constructs a semantic query, retrieves the top-5 most relevant
    document chunks from the FAISS vector store, and passes them to
    GPT-4o-mini to generate a structured medical summary.

    Note: Does NOT use the deprecated RetrievalQA chain. Uses
    retriever.invoke() + direct LLM call for langchain 1.2.x compatibility.

    Args:
        patient_name (str): Name of the patient to retrieve history for.
        query        (str): Optional specific question about the patient.
                            If empty, a full history summary is generated.

    Returns:
        str: JSON string with status, summary text, and source files.

    Example:
        result = retrieve_patient_history("Anjali Mehra",
                                          "What medications is she on?")
    """
    try:
        vectorstore = build_vector_store()

        if vectorstore is None:
            return json.dumps({
                "status": "error",
                "message": "No PDF reports available. Please add reports to data/reports/"
            })

        # Build a rich semantic query combining patient name and specific question
        if query:
            full_query = (
                f"For patient {patient_name}: {query}. "
                f"Provide a clear, structured medical summary."
            )
        else:
            full_query = (
                f"Provide a comprehensive medical history summary for patient {patient_name}. "
                f"Include: diagnosis, medications, vital signs, lab results, and treatment plan."
            )

        # Retrieve top-5 semantically relevant chunks
        retriever     = vectorstore.as_retriever(search_kwargs={"k": 5})
        retrieved_docs = retriever.invoke(full_query)

        # Collect context and unique source files
        context_parts = []
        sources       = []
        for doc in retrieved_docs:
            context_parts.append(doc.page_content)
            src = doc.metadata.get("source_file", "unknown")
            if src not in sources:
                sources.append(src)

        context = "\n\n---\n\n".join(context_parts)

        # Generate structured summary with GPT-4o-mini
        llm      = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content=(
                "You are a medical assistant. Using only the patient records provided, "
                "give a clear and structured medical summary. "
                "Include sections: Diagnosis, Medications, Vital Signs, "
                "Lab Results (flag abnormals), Treatment Plan, and Follow-up Alerts. "
                "If information is not available in the records, say 'Not available'."
            )),
            HumanMessage(content=(
                f"Query: {full_query}\n\n"
                f"Patient Records:\n{context}"
            ))
        ]
        response = llm.invoke(messages)

        return json.dumps({
            "status":  "success",
            "patient": patient_name,
            "summary": response.content,
            "sources": sources
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


def search_across_all_patients(medical_query: str) -> str:
    """
    Search across all patient PDF reports for a specific medical query.
    Returns the top matching chunks with patient attribution.

    Args:
        medical_query (str): Medical topic or condition to search for.

    Returns:
        str: JSON string with status and list of matching result excerpts.

    Example:
        result = search_across_all_patients("HbA1c elevated diabetes")
    """
    try:
        vectorstore = build_vector_store()

        if vectorstore is None:
            return json.dumps({"status": "error", "message": "No reports loaded."})

        # Similarity search returns top-6 matching chunks across all patients
        docs    = vectorstore.similarity_search(medical_query, k=6)
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content[:500],
                "source":  doc.metadata.get("source_file", "unknown"),
                "patient": doc.metadata.get("patient_hint", "unknown")
            })

        return json.dumps({
            "status":  "success",
            "query":   medical_query,
            "results": results
        })

    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
