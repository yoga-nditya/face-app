from __future__ import annotations

from pydantic import BaseModel


class PersonOut(BaseModel):
    name: str


class RecognizeSuccess(BaseModel):
    code: int = 200 
    success: bool = True
    person: PersonOut
    confidence: float


class ErrorResponse(BaseModel):
    code: int 
    success: bool = False
    reason: str  
    message: str


class AttendanceOut(BaseModel):
    timestamp: str
    confidence: float


class CheckInSuccess(BaseModel):
    code: int = 200
    success: bool = True
    person: PersonOut
    attendance: AttendanceOut


class RebuildResponse(BaseModel):
    success: bool = True
    total_images: int
    processed: int
    failed: int
    people_in_index: int
    duration_ms: int
