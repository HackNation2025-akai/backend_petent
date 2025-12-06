from __future__ import annotations

from datetime import date, time
from enum import Enum

from pydantic import BaseModel, Field


class AddressSchema(BaseModel):
    street: str | None = None
    house_number: str | None = None
    apartment_number: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None


class PersonSchema(BaseModel):
    pesel: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    birth_date: date | None = None
    birth_place: str | None = None
    phone: str | None = None


class WitnessSchema(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    address: AddressSchema | None = None


class AccidentInfoSchema(BaseModel):
    accident_date: date | None = None
    accident_time: time | None = None
    accident_place: str | None = None
    planned_work_start: time | None = None
    planned_work_end: time | None = None
    injuries_description: str | None = None
    detailed_description: str | None = None
    first_aid_provided: bool | None = None
    first_aid_facility: str | None = None
    investigating_authority: str | None = None
    machine_involved: bool | None = None
    machine_description: str | None = None
    machine_certified: bool | None = None
    machine_registered: bool | None = None


class CorrespondenceType(str, Enum):
    standard = "standard"
    poste_restante = "poste_restante"
    po_box = "po_box"
    postal_compartment = "postal_compartment"


class EWYPFormSchema(BaseModel):
    injured_person: PersonSchema
    injured_address: AddressSchema
    injured_previous_address: AddressSchema | None = None
    injured_correspondence_address: AddressSchema | None = None
    correspondence_type: CorrespondenceType = CorrespondenceType.standard

    business_address: AddressSchema | None = None
    childcare_address: AddressSchema | None = None

    reporter: PersonSchema | None = None
    reporter_address: AddressSchema | None = None
    reporter_previous_address: AddressSchema | None = None
    reporter_correspondence_address: AddressSchema | None = None

    accident_info: AccidentInfoSchema

    witnesses: list[WitnessSchema] = Field(default_factory=list, max_length=3)

    attachments: list[str] = Field(default_factory=list)
    documents_to_deliver: list[str] = Field(default_factory=list)
    documents_deadline: date | None = None

    response_method: str | None = None

    class Config:
        extra = "allow"


