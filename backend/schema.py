from typing import Literal, Optional, List
from pydantic import BaseModel, Field


class PropertyContact(BaseModel):
    company: Optional[str] = Field(None, description="Name of the brokerage company, e.g., CBRE, Kausch GmbH")
    email: Optional[str] = Field(None, description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")


class PropertyAddress(BaseModel):
    street: Optional[str] = Field(None, description="Street name and number")
    postal_code: Optional[str] = Field(None, description="German ZIP code (PLZ)")
    city: str = Field(..., description="City name, e.g., Berlin, Hamburg")
    district: Optional[str] = Field(None, description="District or neighborhood")


class RealEstateOffer(BaseModel):
    offer_date: Optional[str] = Field(None, description="Date of the offer or email interaction in YYYY-MM-DD format")
    subject_title: str = Field(..., description="Main headline or subject line of the email")

    # Literal enforces exactly these two values at Pydantic validation time.
    # If Gemini returns "existing investment" (space) or any other variant,
    # model_validate() raises a ValidationError immediately instead of
    # silently storing garbage in the database.
    asset_classification: Literal["land_development", "existing_investment"] = Field(
        ..., description="Type of asset — must be exactly 'land_development' or 'existing_investment'"
    )

    address: PropertyAddress = Field(..., description="Location details")
    contact: Optional[PropertyContact] = Field(None, description="Broker details")

    # --- Land Development Fields ---
    plot_size_sqm: Optional[float] = Field(None, description="Size of the land plot in square meters (Grundstücksfläche). Only populate if asset_classification is 'land_development'")
    planned_units: Optional[int] = Field(None, description="Planned apartment/commercial units (Wohneinheiten / WE). Only populate if asset_classification is 'land_development'")
    building_permit_status: Optional[str] = Field(None, description="Status of permission, e.g., 'Baugenehmigung erteilt', 'Bauvorbescheid genehmigt'. Only populate if asset_classification is 'land_development'")

    # --- Existing Investment Fields ---
    current_annual_net_rent_eur: Optional[float] = Field(None, description="Annual net rent income (Netto-Kaltmiete p.a.). Only populate if asset_classification is 'existing_investment'")
    target_yield_percent: Optional[float] = Field(None, description="Yield percentage (Rendite). Only populate if asset_classification is 'existing_investment'")
    total_existing_units: Optional[int] = Field(None, description="Total units currently existing. Only populate if asset_classification is 'existing_investment'")
    key_tenants: List[str] = Field(default=[], description="List of major anchor tenants, e.g., Fresenius")
    purchase_price_eur: Optional[float] = Field(None, description="Asking/purchase price in EUR (Kaufpreis). Always extract this if mentioned.")
    total_living_area_sqm: Optional[float] = Field(None, description="Total living/usable area in sqm (Wohnfläche / Nutzfläche gesamt).")