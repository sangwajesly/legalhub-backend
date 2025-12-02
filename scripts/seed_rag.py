"""
Script to seed the RAG system with documents from various sources.

This can be run as a one-time setup or periodically to sync documents.
"""

import asyncio
import logging
from typing import List, Dict, Any

from app.utils.rag_helpers import (
    add_article_to_rag,
    add_case_law_to_rag,
    add_statute_to_rag,
    batch_add_documents,
)
from app.services import firebase_service

logger = logging.getLogger(__name__)


async def seed_rag_from_firebase():
    """
    Seed the RAG vector store with all articles from Firebase.
    
    This function:
    1. Fetches all published articles from Firebase
    2. Converts them to RAG-compatible format
    3. Adds embeddings and stores in ChromaDB
    """
    try:
        logger.info("Starting RAG seeding from Firebase articles...")
        
        # Fetch articles from Firebase
        articles = await firebase_service.get_all_articles()
        
        if not articles:
            logger.warning("No articles found in Firebase")
            return {"status": "warning", "message": "No articles found"}
        
        logger.info(f"Found {len(articles)} articles in Firebase")
        
        # Process each article
        success_count = 0
        error_count = 0
        
        for article in articles:
            try:
                result = await add_article_to_rag(
                    article_id=article.uid,
                    title=article.title,
                    content=article.content,
                    author=article.author_id,
                    category=getattr(article, "category", "general"),
                    url=getattr(article, "url", None),
                )
                
                if result["status"] == "success":
                    success_count += 1
                else:
                    error_count += 1
                    logger.warning(f"Failed to add article {article.uid}: {result.get('error')}")
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing article {article.uid}: {e}")
        
        logger.info(f"RAG seeding complete: {success_count} added, {error_count} failed")
        return {
            "status": "success",
            "total": len(articles),
            "added": success_count,
            "failed": error_count,
        }
    
    except Exception as e:
        logger.error(f"Error seeding RAG from Firebase: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


async def seed_sample_legal_documents():
    """
    Seed the RAG system with sample legal documents for testing.
    
    This creates example documents about common legal topics.
    """
    try:
        logger.info("Seeding RAG with sample legal documents...")
        
        # Sample contract law document
        await add_article_to_rag(
            article_id="sample_contract_001",
            title="Essential Elements of a Valid Contract",
            content="""
            A contract is a legally binding agreement between two or more parties. 
            For a contract to be enforceable, it must contain all essential elements:
            
            1. Offer: A clear proposal made by one party (offeror) to another (offeree)
            2. Acceptance: Unconditional agreement to all terms of the offer
            3. Consideration: Something of value exchanged between parties
            4. Capacity: All parties must have legal capacity to enter the contract
            5. Legality: The purpose must not violate any law
            6. Mutual Intention: Both parties must intend to create legal relations
            
            Examples of valid contracts:
            - Employment agreements
            - Sales agreements
            - Lease agreements
            - Service contracts
            
            Types of contracts:
            - Bilateral: Both parties make promises
            - Unilateral: One party makes a promise
            - Express: Terms explicitly stated
            - Implied: Terms inferred from conduct
            """,
            author="Legal Education",
            category="contract_law",
        )
        
        # Sample criminal law document
        await add_article_to_rag(
            article_id="sample_criminal_001",
            title="Introduction to Criminal Law",
            content="""
            Criminal law deals with offenses against society. Key concepts include:
            
            Elements of a Crime:
            1. Actus Reus (guilty act): The physical act of committing a crime
            2. Mens Rea (guilty mind): The criminal intent or knowledge
            3. Causation: Direct link between act and harm
            
            Types of Crimes:
            - Felonies: Serious crimes (murder, rape, robbery)
            - Misdemeanors: Lesser crimes (theft, assault)
            - Violations: Minor infractions
            
            Defenses to Criminal Charges:
            - Self-defense
            - Insanity
            - Duress
            - Necessity
            - Mistake of fact
            - Impossibility
            
            Criminal Procedures:
            - Arrest and custody
            - Bail and bond
            - Arraignment
            - Trial
            - Sentencing
            """,
            author="Legal Education",
            category="criminal_law",
        )
        
        # Sample tort law document
        await add_article_to_rag(
            article_id="sample_tort_001",
            title="Understanding Tort Law and Liability",
            content="""
            Tort law provides remedies for civil wrongs (non-criminal harm). 
            
            Types of Torts:
            
            1. Intentional Torts:
            - Assault: Threat of immediate harm
            - Battery: Unauthorized harmful contact
            - False imprisonment: Unlawful confinement
            - Intentional infliction of emotional distress
            - Trespass: Unauthorized entry on property
            
            2. Negligence:
            - Duty of care
            - Breach of duty
            - Causation
            - Damages
            
            3. Strict Liability:
            - No need to prove fault
            - Examples: Product liability, abnormally dangerous activities
            
            Damages:
            - Compensatory: For actual losses
            - Punitive: To punish egregious conduct
            - Nominal: Symbolic damages
            """,
            author="Legal Education",
            category="tort_law",
        )
        
        logger.info("Sample legal documents added successfully")
        return {
            "status": "success",
            "message": "Sample documents added",
            "count": 3,
        }
    
    except Exception as e:
        logger.error(f"Error seeding sample documents: {e}")
        return {
            "status": "error",
            "error": str(e),
        }


async def main():
    """Main seeding function"""
    print("LegalHub RAG Seeding Script")
    print("=" * 50)
    
    # Seed with sample documents first
    print("\n1. Seeding sample legal documents...")
    sample_result = await seed_sample_legal_documents()
    print(f"   Result: {sample_result}")
    
    # Seed with Firebase articles
    print("\n2. Seeding articles from Firebase...")
    firebase_result = await seed_rag_from_firebase()
    print(f"   Result: {firebase_result}")
    
    print("\n" + "=" * 50)
    print("RAG seeding complete!")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run seeding
    asyncio.run(main())
