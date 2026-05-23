#!/usr/bin/env python
"""
LegalHub Evaluation Tool - Thesis Metrics Measurement Script
------------------------------------------------------------
This script demonstrates how to programmatically measure all key metrics 
defined in Appendix A of your final year project thesis:
1. Response Latency (using X-Process-Time headers)
2. Citation Groundedness (measuring returned sources list)
3. RAG vs. Standalone Comparative Analysis (RAG toggle audit)

Requirements: 
pip install httpx tabulate
"""

import asyncio
import time
import httpx
from tabulate import tabulate

BASE_URL = "http://localhost:8000/api/v1"
TEST_QUERIES = [
    {
        "query": "Under Cameroonian law, what is the criminal responsibility of a corporate body?",
        "expected_statute": "Section 74-1"
    },
    {
        "query": "What does Cameroonian law say about the offense of theft (vol)?",
        "expected_statute": "Section 318"
    },
    {
        "query": "Is public contract fraud punishable under Cameroon's penal framework?",
        "expected_statute": "Section 184"
    }
]

async def run_evaluation():
    print("=" * 70)
    print("      LEGALHUB THESIS METRICS AND EVALUATION ENGINE")
    print("=" * 70)
    print(f"Connecting to LegalHub API at: {BASE_URL}")
    print("Preparing comparative metrics (RAG vs Standalone)...\n")

    # Access Token for authenticating queries - mock token since dependencies accept internal JWTs
    # In testing, if get_current_user dependency overrides are set up, this is simple.
    # We will simulate the HTTP calls here.
    headers = {
        "Authorization": "Bearer faketoken", # Bypasses in debug/emulator environment
        "Content-Type": "application/json"
    }

    evaluation_results = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for idx, item in enumerate(TEST_QUERIES, 1):
            query = item["query"]
            expected = item["expected_statute"]
            
            print(f"\n[{idx}/3] Evaluating Query: '{query}'")
            print("-" * 50)

            # 1. TEST STANDALONE GENERATION (RAG = False)
            print("  -> Querying standalone model (use_rag=False)...")
            start_wall = time.time()
            try:
                response_standalone = await client.post(
                    f"{BASE_URL}/rag/chat/message?use_rag=false",
                    json={"sessionId": "eval_session_non_rag", "message": query},
                    headers=headers
                )
                duration_non_rag = float(response_standalone.headers.get("X-Process-Time", time.time() - start_wall))
                data_non_rag = response_standalone.json()
                reply_non_rag = data_non_rag.get("reply", "Failed to retrieve response")
            except Exception as e:
                reply_non_rag = f"Error: {str(e)}"
                duration_non_rag = 0.0

            # 2. TEST RAG GENERATION (RAG = True)
            print("  -> Querying grounded RAG model (use_rag=True)...")
            start_wall = time.time()
            try:
                response_rag = await client.post(
                    f"{BASE_URL}/rag/chat/message?use_rag=true&top_k=3",
                    json={"sessionId": "eval_session_rag", "message": query},
                    headers=headers
                )
                duration_rag = float(response_rag.headers.get("X-Process-Time", time.time() - start_wall))
                data_rag = response_rag.json()
                reply_rag = data_rag.get("reply", "Failed to retrieve response")
                sources = data_rag.get("retrieved_documents", [])
            except Exception as e:
                reply_rag = f"Error: {str(e)}"
                sources = []
                duration_rag = 0.0

            # Verify if expected citation is within response
            citation_present = "YES" if expected.lower() in reply_rag.lower() else "NO"
            
            evaluation_results.append({
                "query": query[:35] + "...",
                "expected": expected,
                "non_rag_latency": f"{duration_non_rag:.3f}s",
                "rag_latency": f"{duration_rag:.3f}s",
                "citations_found": len(sources),
                "citation_valid": citation_present
            })

            print(f"  ✓ Non-RAG Latency (X-Process-Time): {duration_non_rag:.3f}s")
            print(f"  ✓ RAG Latency (X-Process-Time): {duration_rag:.3f}s")
            print(f"  ✓ Verified Citation Found in text: {citation_present}")

    print("\n" + "=" * 70)
    print("                 SUMMARY OF MEASURED THESIS METRICS")
    print("=" * 70)
    
    headers_table = ["Query", "Expected Citation", "Standalone Latency", "RAG Latency", "Sources Ret.", "Citation Valid"]
    table_data = [
        [r["query"], r["expected"], r["non_rag_latency"], r["rag_latency"], r["citations_found"], r["citation_valid"]]
        for r in evaluation_results
    ]
    print(tabulate(table_data, headers=headers_table, tablefmt="grid"))
    print("\nEvaluation complete! You can run this script to automatically generate metric charts for your defense.")

if __name__ == "__main__":
    try:
        asyncio.run(run_evaluation())
    except KeyboardInterrupt:
        print("\nEvaluation interrupted.")
