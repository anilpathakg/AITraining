"""
Medical Search Tool
Primary sources: MedlinePlus (NLM/NIH) + WHO
Fallback: DuckDuckGo (ddgs)
Summarizes results using GPT-4o-mini.
"""

import json
import urllib.request
import urllib.parse
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

MEDLINE_API = "https://wsearch.nlm.nih.gov/ws/query"


def _search_medlineplus(query: str, max_results: int = 5) -> list:
    """Search MedlinePlus (NLM/NIH) — free, no API key required."""
    try:
        params = urllib.parse.urlencode({
            "db": "healthTopics",
            "term": query,
            "retmax": max_results
        })
        url = f"{MEDLINE_API}?{params}"
        req = urllib.request.Request(url, headers={"User-Agent": "HealthcareAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")

        results = []
        summaries = re.findall(r"<content name=['\"]FullSummary['\"]>(.*?)</content>", raw, re.DOTALL)
        titles = re.findall(r"<content name=['\"]title['\"]>(.*?)</content>", raw, re.DOTALL)
        urls = re.findall(r"<url>(.*?)</url>", raw)

        for i in range(min(len(summaries), max_results)):
            title = re.sub(r"<[^>]+>", "", titles[i]).strip() if i < len(titles) else "MedlinePlus Article"
            summary = re.sub(r"<[^>]+>", "", summaries[i]).strip()[:600]
            href = urls[i].strip() if i < len(urls) else "https://medlineplus.gov"
            if title and summary:
                results.append({
                    "title": title,
                    "body": summary,
                    "href": href,
                    "source": "MedlinePlus (NLM/NIH)"
                })
        return results
    except Exception as e:
        return []


def _search_who(query: str, max_results: int = 3) -> list:
    """Fetch WHO health topic search results."""
    try:
        encoded = urllib.parse.quote(query)
        url = f"https://www.who.int/search#q={encoded}&sort=relevancy&f:typef=[Pages]"
        req = urllib.request.Request(url, headers={"User-Agent": "HealthcareAssistant/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8")

        titles = re.findall(r"<h3[^>]*>(.*?)</h3>", raw, re.DOTALL)
        paras = re.findall(r'<p[^>]*class="[^"]*summary[^"]*"[^>]*>(.*?)</p>', raw, re.DOTALL)

        results = []
        for i in range(min(max_results, len(titles))):
            title = re.sub(r"<[^>]+>", "", titles[i]).strip()
            body = re.sub(r"<[^>]+>", "", paras[i]).strip()[:400] if i < len(paras) else ""
            if title and len(title) > 5:
                results.append({
                    "title": title,
                    "body": body,
                    "href": "https://www.who.int/news-room/fact-sheets",
                    "source": "WHO"
                })
        return results[:max_results]
    except Exception:
        return []


def _search_ddgs_fallback(query: str, max_results: int = 4) -> list:
    """DuckDuckGo fallback — only used if trusted sources return nothing."""
    try:
        from ddgs import DDGS
        ddgs = DDGS()
        raw = list(ddgs.text(query + " medical information treatment", max_results=max_results))
        for r in raw:
            r["source"] = "Web Search (DuckDuckGo - fallback)"
        return raw
    except Exception:
        return []


def search_medical_information(query: str, max_results: int = 5) -> str:
    """
    Search for medical information using trusted sources in priority order:
    1. MedlinePlus (NLM/NIH) — primary trusted source
    2. WHO — secondary trusted source
    3. DuckDuckGo — fallback only if above return nothing
    """
    try:
        all_results = []
        sources_used = []

        # Primary: MedlinePlus
        medline_results = _search_medlineplus(query, max_results=4)
        if medline_results:
            all_results.extend(medline_results)
            sources_used.append("MedlinePlus (NLM/NIH)")

        # Secondary: WHO
        who_results = _search_who(query, max_results=2)
        if who_results:
            all_results.extend(who_results)
            sources_used.append("WHO")

        # Fallback: DuckDuckGo only if no trusted results
        if not all_results:
            all_results = _search_ddgs_fallback(query, max_results=5)
            if all_results:
                sources_used.append("Web Search (DuckDuckGo - fallback)")

        if not all_results:
            return json.dumps({
                "status": "no_results",
                "message": f"No results found for: {query}",
                "summary": ""
            })

        context_parts = []
        source_list = []
        for i, r in enumerate(all_results, 1):
            title = r.get("title", "")
            body = r.get("body", "")
            href = r.get("href", "")
            src = r.get("source", "Unknown")
            context_parts.append(f"[{i}] SOURCE: {src}\nTitle: {title}\nContent: {body}\nURL: {href}")
            source_list.append({"title": title, "url": href, "source": src})

        context = "\n\n".join(context_parts)

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        messages = [
            SystemMessage(content=(
                "You are a medical information assistant using content from trusted sources "
                "(MedlinePlus/NLM/NIH and WHO). Summarize the information clearly with these sections: "
                "1. Overview, 2. Key Symptoms or Features, 3. Treatment Options, 4. Important Notes. "
                "Always conclude with: 'This information is sourced from trusted medical authorities "
                "(MedlinePlus/WHO/NIH). Please consult a qualified healthcare professional for "
                "personal medical advice.'"
            )),
            HumanMessage(content=(
                f"Medical Query: {query}\n\n"
                f"Content from Trusted Sources:\n{context}\n\n"
                f"Please provide a clear, structured medical summary."
            ))
        ]

        response = llm.invoke(messages)
        trusted_count = len([s for s in source_list if "DuckDuckGo" not in s.get("source", "")])

        return json.dumps({
            "status": "success",
            "query": query,
            "summary": response.content,
            "sources_used": sources_used,
            "sources": source_list[:6],
            "trusted_source_count": trusted_count,
            "raw_result_count": len(all_results)
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": str(e),
            "query": query
        })


def get_drug_information(drug_name: str) -> str:
    """Get information about a specific drug or medication."""
    query = f"{drug_name} drug uses dosage side effects contraindications"
    return search_medical_information(query)


def get_disease_overview(disease_name: str) -> str:
    """Get a comprehensive overview of a disease."""
    query = f"{disease_name} disease overview symptoms diagnosis treatment"
    return search_medical_information(query)
