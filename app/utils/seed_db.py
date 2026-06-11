"""
Database Seeding Utility for Offline/Local mode
"""

import logging
from datetime import datetime, UTC
from typing import Dict, Any
from app.config import settings
from app.models.user import User, user_model_to_firestore
from app.models.lawyer import Lawyer, lawyer_model_to_firestore
from app.utils.security import hash_password
from app.services.firebase_service import firebase_service

logger = logging.getLogger(__name__)

MOCK_LAWYERS = [
    {
        "uid": "l1",
        "displayName": "Ngono Odile",
        "email": "odile.ngono@legalhub.cm",
        "profilePicture": "/images/lawyers/lawyer1.png",
        "bio": "Senior constitutional lawyer with over 16 years interpreting and litigating cases under the Constitution of Cameroon. Advised government bodies on constitutional reform and electoral compliance.",
        "location": "Yaoundé, Cameroon",
        "licenseNumber": "CAM-2008-011",
        "jurisdictions": ["Cameroon"],
        "practiceAreas": ["Constitutional Law", "Electoral Law"],
        "hourlyRate": 75000.0,
        "yearsExperience": 16,
        "languages": ["fr", "en"],
        "verified": True,
        "rating": 4.9,
        "numReviews": 143,
    },
    {
        "uid": "l2",
        "displayName": "Nkongho Paul",
        "email": "paul.nkongho@legalhub.cm",
        "profilePicture": "/images/lawyers/lawyer2.jpg",
        "bio": "Defence attorney specialising in criminal procedure under Law No. 2005/007. Represented clients across Cameroon in criminal matters ranging from petty offences to felonies.",
        "location": "Douala, Cameroon",
        "licenseNumber": "CAM-2012-094",
        "jurisdictions": ["Cameroon"],
        "practiceAreas": ["Criminal Law", "Criminal Procedure"],
        "hourlyRate": 55000.0,
        "yearsExperience": 12,
        "languages": ["en", "fr"],
        "verified": True,
        "rating": 4.8,
        "numReviews": 211,
    },
    {
        "uid": "l3",
        "displayName": "Fombu Grace",
        "email": "grace.fombu@legalhub.cm",
        "profilePicture": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=200&q=80",
        "bio": "Specialist in family law and customary court proceedings in the North West Region. Advocates for women's rights in customary marriages and inheritance disputes.",
        "location": "Bamenda, Cameroon",
        "licenseNumber": "CAM-2014-042",
        "jurisdictions": ["Cameroon"],
        "practiceAreas": ["Family & Customary Law"],
        "hourlyRate": 35000.0,
        "yearsExperience": 10,
        "languages": ["en"],
        "verified": True,
        "rating": 4.9,
        "numReviews": 88,
    },
    {
        "uid": "l4",
        "displayName": "Atanga Erica",
        "email": "erica.atanga@legalhub.cm",
        "profilePicture": "https://images.unsplash.com/photo-1589156280159-27698a70f29e?auto=format&fit=crop&w=200&q=80",
        "bio": "Employment lawyer focused on worker rights, wrongful dismissal, and contract reviews under the Cameroonian Labour Code. Based in the South West Region.",
        "location": "Buea, Cameroon",
        "licenseNumber": "CAM-2016-081",
        "jurisdictions": ["Cameroon"],
        "practiceAreas": ["Labour Law", "Employment"],
        "hourlyRate": 28000.0,
        "yearsExperience": 8,
        "languages": ["en", "fr"],
        "verified": True,
        "rating": 4.7,
        "numReviews": 76,
    },
    {
        "uid": "l5",
        "displayName": "Mbarga Richard",
        "email": "richard.mbarga@legalhub.cm",
        "profilePicture": "/images/lawyers/lawyer3.jpg",
        "bio": "Corporate lawyer assisting SMEs and multinationals with business registration, compliance, and commercial contracts under OHADA law in Cameroon.",
        "location": "Yaoundé, Cameroon",
        "licenseNumber": "CAM-2010-023",
        "jurisdictions": ["Cameroon", "OHADA"],
        "practiceAreas": ["Business Law", "Corporate Law"],
        "hourlyRate": 65000.0,
        "yearsExperience": 14,
        "languages": ["fr", "en"],
        "verified": True,
        "rating": 4.8,
        "numReviews": 109,
    },
    {
        "uid": "l6",
        "displayName": "Tchouaket Jean-Marie",
        "email": "jeanmarie.tchouaket@legalhub.cm",
        "profilePicture": "/images/lawyers/lawyer4.jpg",
        "bio": "Specialist in the Cameroonian Mining Code and related decrees. Advises extraction companies, artisanal miners, and state agencies on licensing, environmental obligations, and disputes.",
        "location": "Douala, Cameroon",
        "licenseNumber": "CAM-2013-057",
        "jurisdictions": ["Cameroon"],
        "practiceAreas": ["Mining Law", "Natural Resources"],
        "hourlyRate": 80000.0,
        "yearsExperience": 11,
        "languages": ["fr", "en"],
        "verified": True,
        "rating": 4.6,
        "numReviews": 54,
    },
    {
        "uid": "l7",
        "displayName": "Ndikum Cynthia",
        "email": "cynthia.ndikum@legalhub.cm",
        "profilePicture": "https://images.unsplash.com/photo-1567532939604-b6b5b0db2604?auto=format&fit=crop&w=200&q=80",
        "bio": "Tax and fiscal law practitioner with deep knowledge of the Cameroon Finance Law. Helps businesses and individuals navigate tax obligations and dispute resolutions with the DGI.",
        "location": "Bafoussam, Cameroon",
        "licenseNumber": "CAM-2015-099",
        "jurisdictions": ["Cameroon"],
        "practiceAreas": ["Tax Law", "Finance Law"],
        "hourlyRate": 40000.0,
        "yearsExperience": 9,
        "languages": ["fr", "en"],
        "verified": True,
        "rating": 4.7,
        "numReviews": 92,
    },
    {
        "uid": "l8",
        "displayName": "Ewane Bertrand",
        "email": "bertrand.ewane@legalhub.cm",
        "profilePicture": "https://images.unsplash.com/photo-1536896407451-6e3dd976edd1?auto=format&fit=crop&w=200&q=80",
        "bio": "Electoral and constitutional law counsel with experience in election observation, candidate eligibility disputes, and civic rights under the Electoral Code of Cameroon.",
        "location": "Yaoundé, Cameroon",
        "licenseNumber": "CAM-2017-104",
        "jurisdictions": ["Cameroon"],
        "practiceAreas": ["Electoral Law", "Constitutional Law"],
        "hourlyRate": 30000.0,
        "yearsExperience": 7,
        "languages": ["en", "fr"],
        "verified": False,
        "rating": 4.5,
        "numReviews": 47,
    }
]


async def seed_local_db():
    """Seed the local mock database with the mock lawyers l1 through l8"""
    if not settings.USE_LOCAL_DATABASE:
        logger.info("Skipping local DB seeding because USE_LOCAL_DATABASE is False.")
        return

    logger.info("Initializing local database seeding...")
    hashed_pwd = hash_password("Password123")

    for raw_lawyer in MOCK_LAWYERS:
        uid = raw_lawyer["uid"]
        
        # 1. Create or update User record
        try:
            user_doc_ref = firebase_service.db.collection("users").document(uid)
            doc_snap = user_doc_ref.get()
            
            # Create user model
            user = User(
                uid=uid,
                email=raw_lawyer["email"],
                displayName=raw_lawyer["displayName"],
                role="lawyer",
                profilePicture=raw_lawyer["profilePicture"],
                emailVerified=True,
                createdAt=datetime.now(UTC),
                updatedAt=datetime.now(UTC),
            )
            
            firestore_user_data = user_model_to_firestore(user)
            firestore_user_data["passwordHash"] = hashed_pwd
            firestore_user_data["uid"] = uid
            
            # Save User
            user_doc_ref.set(firestore_user_data)
            logger.info(f"Seeded User: {raw_lawyer['email']} (UID: {uid})")
            
        except Exception as e:
            logger.error(f"Error seeding user {uid}: {e}")

        # 2. Create or update Lawyer profile record
        try:
            lawyer_doc_ref = firebase_service.db.collection("lawyers").document(uid)
            
            lawyer = Lawyer(
                uid=uid,
                displayName=raw_lawyer["displayName"],
                email=raw_lawyer["email"],
                profilePicture=raw_lawyer["profilePicture"],
                bio=raw_lawyer["bio"],
                location=raw_lawyer["location"],
                licenseNumber=raw_lawyer["licenseNumber"],
                jurisdictions=raw_lawyer["jurisdictions"],
                practiceAreas=raw_lawyer["practiceAreas"],
                hourlyRate=raw_lawyer["hourlyRate"],
                yearsExperience=raw_lawyer["yearsExperience"],
                languages=raw_lawyer["languages"],
                verified=raw_lawyer["verified"],
                rating=raw_lawyer["rating"],
                numReviews=raw_lawyer["numReviews"],
                createdAt=datetime.now(UTC),
                updatedAt=datetime.now(UTC),
            )
            
            # Save Lawyer
            lawyer_doc_ref.set(lawyer_model_to_firestore(lawyer))
            logger.info(f"Seeded Lawyer profile: {raw_lawyer['displayName']} (UID: {uid})")
            
        except Exception as e:
            logger.error(f"Error seeding lawyer profile {uid}: {e}")

    logger.info("Local database seeding completed successfully.")
