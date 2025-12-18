import asyncio
from app.services.rag_service import rag_service
from app.services import langchain_service # Used to generate RAG response
from app.services.firebase_service import firebase_service # To ensure Firebase is initialized
from app.utils.faiss_store import get_vector_store # To clear vector store if needed

async def test_rag_context_adherence():
    """
    Tests the RAG pipeline to ensure it adheres to provided context
    and doesn't provide mock responses.
    """
    print("--- Testing RAG Pipeline Context Adherence ---")
    
    # 1. Prepare a unique test document
    test_document_id = "eldoria_capital_info"
    test_document_content = "The capital of the fictional country of Eldoria is Silverwood, known for its shimmering towers and advanced magical academies. The primary export of Eldoria is refined moonstone."
    test_document_source = "fictional_lore_db"
    
    document = {
        "id": test_document_id,
        "content": test_document_content,
        "source": test_document_source,
        "metadata": {"title": "Eldoria Geographic Information", "author": "GPT-Gemini"}
    }

    # 2. Add the unique document to the RAG vector store
    print(f"Adding test document '{test_document_id}' to RAG...")
    try:
        # Assuming rag_service.add_documents handles chunking and embedding
        result = await rag_service.add_documents([document])
        if result.get("added", 0) > 0:
            print(f"Successfully added {result.get('added')} chunks of document '{test_document_id}'.")
        else:
            print(f"Failed to add document '{test_document_id}'. Result: {result}")
            # If nothing was added, try to debug why.
            # This might mean the document was already there or an error occurred silently.
            # For robust testing, we might want to clear the vector store first.
            vector_store = await get_vector_store()
            if vector_store:
                await vector_store.clear_and_reinitialize()
                result = await rag_service.add_documents([document])
                if result.get("added", 0) > 0:
                    print(f"Retried and successfully added {result.get('added')} chunks of document '{test_document_id}'.")
                else:
                    print(f"Retry also failed to add document '{test_document_id}'. Exiting test.")
                    return
            else:
                print("Vector store not initialized. Exiting test.")
                return


    except Exception as e:
        print(f"Error adding document to RAG: {e}")
        return

    # 3. Formulate a query answerable only by the new document
    query_message_capital = "What is the capital of Eldoria?"
    query_message_export = "What is Eldoria's main export?"
    query_message_unrelated = "Who was the first president of the USA?" # Should not be answered by context

    # 4. Execute the query and analyze the response
    print(f"\nQuerying RAG with: '{query_message_capital}'")
    reply_capital, retrieved_docs_capital = await langchain_service.generate_rag_response(
        session_id="test_session_rag_capital",
        user_id="test_user_rag",
        user_message=query_message_capital,
        use_rag=True,
        top_k=1,
    )
    print(f"RAG Reply (Capital): {reply_capital}")
    print(f"Retrieved Documents (Capital): {[d.get('id') for d in retrieved_docs_capital]}")
    
    assert "Silverwood" in reply_capital, "RAG did not correctly identify the capital from context."
    assert any(d.get("id") == test_document_id for d in retrieved_docs_capital), "RAG did not retrieve the correct document for capital query."
    print("Verification successful for capital query.")

    print(f"\nQuerying RAG with: '{query_message_export}'")
    reply_export, retrieved_docs_export = await langchain_service.generate_rag_response(
        session_id="test_session_rag_export",
        user_id="test_user_rag",
        user_message=query_message_export,
        use_rag=True,
        top_k=1,
    )
    print(f"RAG Reply (Export): {reply_export}")
    print(f"Retrieved Documents (Export): {[d.get('id') for d in retrieved_docs_export]}")
    
    assert "moonstone" in reply_export or "Moonstone" in reply_export, "RAG did not correctly identify the export from context."
    assert any(d.get("id") == test_document_id for d in retrieved_docs_export), "RAG did not retrieve the correct document for export query."
    print("Verification successful for export query.")

    print(f"\nQuerying RAG with unrelated question: '{query_message_unrelated}'")
    reply_unrelated, retrieved_docs_unrelated = await langchain_service.generate_rag_response(
        session_id="test_session_rag_unrelated",
        user_id="test_user_rag",
        user_message=query_message_unrelated,
        use_rag=True,
        top_k=1,
    )
    print(f"RAG Reply (Unrelated): {reply_unrelated}")
    print(f"Retrieved Documents (Unrelated): {[d.get('id') for d in retrieved_docs_unrelated]}")
    
    # Check if the model explicitly states it doesn't know or refers to lack of information
    # This assumes RAG_SYSTEM_PROMPT_TEMPLATE guides it correctly.
    assert "not provided" in reply_unrelated or "cannot answer" in reply_unrelated or "don't have enough" in reply_unrelated, \
           "RAG should indicate lack of context for unrelated questions."
    print("Verification successful for unrelated query (model indicates lack of context).")

    print("\n--- RAG Pipeline Context Adherence Test Complete ---")

if __name__ == "__main__":
    _ = firebase_service # Initialize Firebase service
    asyncio.run(test_rag_context_adherence())
