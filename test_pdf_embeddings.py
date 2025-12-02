"""
Test script to process PDF documents and test vector embeddings for the RAG system.

This script demonstrates:
1. Processing the Penal Code PDF
2. Adding it to the ChromaDB vector store
3. Testing similarity search
4. Testing RAG-augmented queries
"""

import asyncio
import os
from pathlib import Path
from app.services.pdf_processor import PDFProcessor
from app.services.rag_service import rag_service
from app.utils.rag_helpers import add_statute_to_rag, search_rag


async def test_pdf_processing():
    """Test processing the Penal Code PDF"""
    print("=" * 60)
    print("Testing PDF Processing: Penal Code")
    print("=" * 60)

    pdf_path = Path("data/pdfs/Penal-Code-eng.pdf")

    if not pdf_path.exists():
        print(f"❌ PDF file not found: {pdf_path}")
        return None

    try:
        print(f"📄 Processing PDF: {pdf_path}")

        # Read PDF content
        with open(pdf_path, "rb") as f:
            pdf_content = f.read()

        print(f"📏 File size: {len(pdf_content)} bytes")

        # Extract text using PDF processor
        text_content, metadata = PDFProcessor.extract_text_from_pdf(pdf_content)

        print("✅ PDF processed successfully!")
        print(f"   📊 Text length: {len(text_content)} characters")
        print(f"   📄 Pages: {metadata.get('pages', 'Unknown')}")
        print(f"   📝 Title: {metadata.get('title', 'Unknown')}")
        print(f"   👤 Author: {metadata.get('author', 'Unknown')}")

        # Show first few lines of content
        lines = text_content.split('\n')[:10]
        print("\n📖 First 10 lines of content:")
        for i, line in enumerate(lines, 1):
            print("2d")

        return text_content, metadata

    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return None


async def test_vector_embeddings():
    """Test adding the Penal Code to vector store and searching"""
    print("\n" + "=" * 60)
    print("Testing Vector Embeddings & Search")
    print("=" * 60)

    # First process the PDF
    pdf_result = await test_pdf_processing()
    if not pdf_result:
        print("❌ Cannot test embeddings without PDF content")
        return

    text_content, metadata = pdf_result

    try:
        print("🔄 Adding Penal Code to RAG vector store...")

        # Split the text into manageable chunks (since it's a long document)
        # For testing, we'll take the first portion and split it into sections
        max_chunk_length = 2000  # Characters per chunk
        chunks = []

        # Simple chunking by paragraphs (split on double newlines)
        paragraphs = text_content.split('\n\n')
        current_chunk = ""
        chunk_count = 0

        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chunk_length:
                current_chunk += para + "\n\n"
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    chunk_count += 1
                current_chunk = para + "\n\n"

                # Limit to first 10 chunks for testing
                if chunk_count >= 10:
                    break

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        print(f"📦 Split into {len(chunks)} chunks for embedding")

        # Add chunks to RAG system
        added_count = 0
        for i, chunk in enumerate(chunks):
            try:
                statute_id = f"penal_code_chunk_{i+1}"
                result = await add_statute_to_rag(
                    statute_id=statute_id,
                    statute_name=f"Penal Code - Section {i+1}",
                    content=chunk,
                    jurisdiction="Cameroon",
                    section=f"Part {i+1}",
                )

                if result["status"] == "success":
                    added_count += 1
                    print(f"✅ Added chunk {i+1}/{len(chunks)}")
                else:
                    print(f"⚠️  Failed to add chunk {i+1}: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"❌ Error adding chunk {i+1}: {e}")

        print(f"🎉 Successfully added {added_count}/{len(chunks)} chunks to vector store")

        return added_count > 0

    except Exception as e:
        print(f"❌ Error in vector embeddings test: {e}")
        return False


async def test_similarity_search():
    """Test similarity search on the embedded Penal Code"""
    print("\n" + "=" * 60)
    print("Testing Similarity Search")
    print("=" * 60)

    # Test queries related to criminal law
    test_queries = [
        "What is murder?",
        "How is theft defined?",
        "What are the penalties for assault?",
        "What constitutes robbery?",
        "How is fraud punished?",
        "What are the elements of a crime?",
        "What is self-defense in criminal law?",
    ]

    print(f"🔍 Testing {len(test_queries)} search queries...")

    for query in test_queries:
        print(f"\n💡 Query: '{query}'")

        try:
            result = await search_rag(
                query=query,
                top_k=3,
                score_threshold=0.1  # Lower threshold for testing
            )

            if result["status"] == "success":
                found_count = result["results_count"]
                print(f"   📊 Found {found_count} relevant sections")

                if found_count > 0:
                    for i, doc in enumerate(result["documents"], 1):
                        score = doc['score']
                        source = doc['metadata'].get('source', 'unknown')
                        content_preview = doc['content'][:150].replace('\n', ' ')
                        print(f"      {i}. Score: {score:.3f}, Source: {source}")
                        print(f"         Content: {content_preview}...")
                else:
                    print("   📭 No relevant sections found")
            else:
                print(f"   ❌ Search failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"   💥 Error during search: {e}")


async def test_rag_augmented_response():
    """Test RAG-augmented AI responses"""
    print("\n" + "=" * 60)
    print("Testing RAG-Augmented AI Responses")
    print("=" * 60)

    from app.services import langchain_service

    test_questions = [
        "What are the penalties for murder under Cameroonian law?",
        "How is theft defined in the Penal Code?",
        "What constitutes self-defense?",
        "What are the different types of crimes?",
    ]

    print(f"🤖 Testing {len(test_questions)} RAG-augmented questions...")

    for question in test_questions:
        print(f"\n❓ Question: {question}")

        try:
            # Test RAG-augmented response
            response, retrieved_docs = await langchain_service.generate_rag_response(
                session_id=None,  # No session for testing
                user_id="test_user",
                user_message=question,
                use_rag=True,
                top_k=3
            )

            print(f"🤖 AI Response: {response[:200]}...")
            print(f"📚 Retrieved {len(retrieved_docs)} relevant documents")

            if retrieved_docs:
                print("   📖 Sources:")
                for doc in retrieved_docs[:2]:  # Show first 2
                    print(f"      - Score: {doc['score']:.3f}, Source: {doc['metadata'].get('source', 'unknown')}")
        except Exception as e:
            print(f"❌ Error generating RAG response: {e}")


async def main():
    """Main test function"""
    print("🚀 LegalHub PDF Vector Embeddings Test")
    print("=" * 60)

    # Test 1: Process PDF
    pdf_result = await test_pdf_processing()
    if not pdf_result:
        print("❌ PDF processing failed, cannot continue")
        return

    # Test 2: Vector embeddings
    embeddings_success = await test_vector_embeddings()
    if not embeddings_success:
        print("❌ Vector embeddings failed, cannot continue")
        return

    # Test 3: Similarity search
    await test_similarity_search()

    # Test 4: RAG responses
    await test_rag_augmented_response()

    print("\n" + "=" * 60)
    print("🎉 PDF Vector Embeddings Test Complete!")
    print("=" * 60)
    print("✅ Successfully processed Penal Code PDF")
    print("✅ Created vector embeddings")
    print("✅ Tested similarity search")
    print("✅ Tested RAG-augmented responses")


if __name__ == "__main__":
    asyncio.run(main())
