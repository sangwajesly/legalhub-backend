import asyncio
from app.services.firebase_service import firebase_service
from app.models.lawyer import Lawyer, firestore_lawyer_to_model # Import firestore_lawyer_to_model

async def verify_lawyers_in_firestore():
    """
    Verifies that dummy lawyer data exists in the Firestore 'lawyers' collection.
    """
    print("--- Verifying lawyers in Firestore ---")
    
    try:
        lawyers_ref = firebase_service.db.collection("lawyers")
        # Ensure stream is awaited as Firestore operations are now wrapped
        docs = await asyncio.to_thread(lawyers_ref.stream)
        
        found_lawyers = []
        for doc in docs:
            lawyer_data = doc.to_dict()
            print(f"DEBUG: Raw Firestore data for doc {doc.id}: {lawyer_data}")
            # Use firestore_lawyer_to_model for correct conversion
            lawyer = firestore_lawyer_to_model(lawyer_data, doc.id) 
            found_lawyers.append(lawyer)
        
        if found_lawyers:
            print(f"Found {len(found_lawyers)} lawyers in Firestore:")
            for lawyer in found_lawyers:
                print(f"- UID: {lawyer.uid}, Display Name: {lawyer.display_name}, Email: {lawyer.email}")
        else:
            print("No lawyers found in Firestore.")
            
    except Exception as e:
        print(f"Error verifying lawyers: {e}")
        
    print("--- Verification complete ---")

if __name__ == "__main__":
    _ = firebase_service # Initialize Firebase service
    asyncio.run(verify_lawyers_in_firestore())
