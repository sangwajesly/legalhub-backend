"""
Test script for the LegalHub RAG system.

This script demonstrates:
1. Processing a PDF document (Penal Code)
2. Adding documents to the RAG vector store
3. Searching for relevant legal information
4. Testing RAG-augmented chat responses
"""

import asyncio
import os
from pathlib import Path
from app.services.pdf_processor import PDFProcessor
from app.services.rag_service import rag_service
from app.utils.rag_helpers import add_statute_to_rag, search_rag


async def test_pdf_processing():
    """Test PDF processing functionality"""
    print("=" * 50)
    print("Testing PDF Processing")
    print("=" * 50)

    pdf_path = Path("data/pdfs/Penal-Code-eng.pdf")

    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return None

    try:
        # Read PDF content
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()

        # Extract text
        text_content, metadata = PDFProcessor.extract_text_from_pdf(
            pdf_content)

        print(f"✅ PDF processed successfully")
        print(f"   Title: {metadata.get('title', 'Unknown')}")
        print(f"   Pages: {metadata.get('pages', 'Unknown')}")
        print(f"   Text length: {len(text_content)} characters")
        print(f"   First 500 chars: {text_content[:500]}...")

        return text_content, metadata

    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return None


async def test_rag_ingestion():
    """Test adding documents to RAG system"""
    print("\n" + "=" * 50)
    print("Testing RAG Document Ingestion")
    print("=" * 50)

    # First, add some sample legal documents
    print("Adding sample legal documents...")

    try:
        # Add sample contract law
        result1 = await add_statute_to_rag(
            statute_id="sample_contract_law",
            statute_name="Contract Law Basics",
            content="""
            A contract is a legally binding agreement between two or more parties.
            Essential elements of a valid contract include:
            1. Offer: A clear proposal made by one party to another
            2. Acceptance: Unconditional agreement to all terms
            3. Consideration: Something of value exchanged
            4. Capacity: Legal ability to enter contracts
            5. Legality: Purpose must not violate law
            6. Intention: Parties must intend to create legal relations

            Types of contracts:
            - Bilateral contracts: Both parties make promises
            - Unilateral contracts: One party makes a promise
            - Express contracts: Terms stated explicitly
            - Implied contracts: Terms inferred from conduct
            """,
            jurisdiction="General Law",
            section="Contract Formation"
        )
        print(f"✅ Contract law added: {result1['status']}")

        # Add sample criminal law
        result2 = await add_statute_to_rag(
            statute_id="sample_criminal_law",
            statute_name="Criminal Law Principles",
            content="""
            Criminal law deals with offenses against society. Key concepts:

            Elements of Crime:
            1. Actus Reus: The physical act of committing crime
            2. Mens Rea: Criminal intent or knowledge
            3. Causation: Link between act and harm

            Types of Crimes:
            - Felonies: Serious crimes (murder, robbery, rape)
            - Misdemeanors: Lesser crimes (theft, assault)
            - Infractions: Minor violations

            Criminal Defenses:
            - Self-defense
            - Insanity
            - Duress
            - Necessity
            - Mistake of fact

            Criminal Procedure:
            - Investigation
            - Arrest
            - Bail
            - Arraignment
            - Trial
            - Sentencing
            """,
            jurisdiction="Criminal Code",
            section="General Principles"
        )
        print(f"✅ Criminal law added: {result2['status']}")

        return True

    except Exception as e:
        print(f"❌ Error adding documents to RAG: {e}")
        return False


async def test_rag_search():
    """Test searching the RAG system"""
    print("\n" + "=" * 50)
    print("Testing RAG Search Functionality")
    print("=" * 50)

    test_queries = [
        "What are the essential elements of a contract?",
        "What is criminal intent?",
        "How does self-defense work in criminal law?",
        "What are the types of contracts?"
    ]

    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")

        try:
            result = await search_rag(
                query=query,
                top_k=3,
                score_threshold=0.1  # Lower threshold for testing
            )

            if result["status"] == "success":
                print(f"✅ Found {result['results_count']} relevant documents")

                for i, doc in enumerate(result["documents"], 1):
                    score = doc.get('score', 0)
                    source = doc.get("metadata", {}).get(
                        "source", doc.get("source", "unknown"))
                    print(f"   {i}. Score: {score:.3f}")
                    print(f"      Source: {source}")
                    print(f"      Content: {doc.get('content', '')[:200]}...")
            else:
                print(
                    f"❌ Search failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error during search: {e}")


async def test_rag_chat():
    """Test RAG-augmented chat functionality"""
    print("\n" + "=" * 50)
    print("Testing RAG-Augmented Chat")
    print("=" * 50)

    from app.services import langchain_service

    test_messages = [
        "What are the requirements for a valid contract?",
        "Can you explain criminal liability?",
        "What defenses are available in criminal cases?"
    ]

    for message in test_messages:
        print(f"\n💬 User: {message}")

        try:
            # Test RAG-augmented response
            response, retrieved_docs = await langchain_service.generate_rag_response(
                session_id=None,  # No session for testing
                user_id="test_user",
                user_message=message,
                use_rag=True,
                top_k=2
            )

            print(f"🤖 Assistant: {response[:300]}...")
            print(f"📚 Retrieved {len(retrieved_docs)} relevant documents")

            if retrieved_docs:
                print("   Relevant sources:")
                for doc in retrieved_docs[:2]:  # Show first 2
                    source = doc.get("metadata", {}).get(
                        "source", doc.get("source", "unknown"))
                    score = doc.get('score', 0)
                    print(f"   - Score: {score:.3f}, Source: {source}")

        except Exception as e:
            print(f"❌ Error generating RAG response: {e}")


async def main():
    """Main test function"""
    print("🚀 LegalHub RAG System Test")
    print("=" * 50)

    # Test 1: PDF Processing
    # pdf_result = await test_pdf_processing()
    # if not pdf_result:
    #     print("⚠️  PDF processing failed, but continuing with other tests...")

    # Test 2: RAG Ingestion
    ingestion_success = await test_rag_ingestion()
    if not ingestion_success:
        print("❌ RAG ingestion failed, cannot continue with other tests")
        return

    # Test 3: RAG Search
    await test_rag_search()

    # Test 4: RAG Chat
    await test_rag_chat()

    print("\n" + "=" * 50)
    print("🎉 RAG System Testing Complete!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
