"""
System Settings model for LegalHub Backend
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


def utc_now():
    """Get current UTC datetime (timezone-aware)"""
    return datetime.now(timezone.utc)


class SystemSettings(BaseModel):
    """
    General system settings stored in Firestore
    Collection: settings/
    Document ID: config
    """
    maintenance_mode: bool = Field(default=False, alias="maintenanceMode")
    allow_registration: bool = Field(default=True, alias="allowRegistration")
    min_app_version: str = Field(default="1.0.0", alias="minAppVersion")
    featured_lawyers_limit: int = Field(
        default=5, alias="featuredLawyersLimit")
    support_email: str = Field(
        default="support@legalhub.com", alias="supportEmail")

    # Flexible field for extra configuration
    extra_config: Dict[str, Any] = Field(
        default_factory=dict, alias="extraConfig")

    updated_at: datetime = Field(default_factory=utc_now, alias="updatedAt")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "maintenance_mode": False,
                "allow_registration": True,
                "min_app_version": "1.0.0",
                "featured_lawyers_limit": 5,
                "support_email": "support@legalhub.com",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


def settings_model_to_firestore(settings: SystemSettings) -> dict:
    """Convert SystemSettings model to Firestore-safe dict"""
    return settings.model_dump(by_alias=True)
