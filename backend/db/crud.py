"""AyushBot Backend — CRUD helpers for core entities."""

from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db.models import Case, Patient, Recommendation


# ---------------------------------------------------------------------------
# Patient CRUD
# ---------------------------------------------------------------------------

def create_patient(db: Session, patient_data: dict) -> Patient:
    patient = Patient(**patient_data)
    try:
        db.add(patient)
        db.flush()
        return patient
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Failed to create patient; integrity error") from exc


def get_patient(db: Session, patient_id: str) -> Optional[Patient]:
    return db.query(Patient).filter(Patient.id == patient_id).one_or_none()


def list_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
    return db.query(Patient).offset(skip).limit(limit).all()


def update_patient(db: Session, patient_id: str, updates: dict) -> Optional[Patient]:
    patient = get_patient(db, patient_id)
    if not patient:
        return None
    for key, value in updates.items():
        if hasattr(patient, key):
            setattr(patient, key, value)
    db.flush()
    return patient


def delete_patient(db: Session, patient_id: str) -> bool:
    patient = get_patient(db, patient_id)
    if not patient:
        return False
    db.delete(patient)
    db.flush()
    return True


# ---------------------------------------------------------------------------
# Case CRUD
# ---------------------------------------------------------------------------

def create_case(db: Session, case_data: dict) -> Case:
    case = Case(**case_data)
    try:
        db.add(case)
        db.flush()
        return case
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Failed to create case; integrity error") from exc


def create_cases_bulk(db: Session, cases: Iterable[dict]) -> List[Case]:
    created: List[Case] = []
    try:
        for payload in cases:
            record = Case(**payload)
            db.add(record)
            created.append(record)
        db.flush()
        return created
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Failed to create cases; integrity error") from exc


def get_case(db: Session, case_id: str) -> Optional[Case]:
    return db.query(Case).filter(Case.id == case_id).one_or_none()


def list_cases(db: Session, skip: int = 0, limit: int = 100) -> List[Case]:
    return db.query(Case).offset(skip).limit(limit).all()


def list_cases_by_patient(
    db: Session, patient_id: str, skip: int = 0, limit: int = 100
) -> List[Case]:
    return (
        db.query(Case)
        .filter(Case.patient_id == patient_id)
        .order_by(Case.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_case(db: Session, case_id: str, updates: dict) -> Optional[Case]:
    case = get_case(db, case_id)
    if not case:
        return None
    for key, value in updates.items():
        if hasattr(case, key):
            setattr(case, key, value)
    db.flush()
    return case


def delete_case(db: Session, case_id: str) -> bool:
    case = get_case(db, case_id)
    if not case:
        return False
    db.delete(case)
    db.flush()
    return True


# ---------------------------------------------------------------------------
# Recommendation CRUD
# ---------------------------------------------------------------------------

def create_recommendation(db: Session, recommendation_data: dict) -> Recommendation:
    recommendation = Recommendation(**recommendation_data)
    try:
        db.add(recommendation)
        db.flush()
        return recommendation
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Failed to create recommendation; integrity error") from exc


def get_recommendation(db: Session, recommendation_id: str) -> Optional[Recommendation]:
    return (
        db.query(Recommendation)
        .filter(Recommendation.id == recommendation_id)
        .one_or_none()
    )


def get_recommendation_by_case(db: Session, case_id: str) -> Optional[Recommendation]:
    return db.query(Recommendation).filter(Recommendation.case_id == case_id).one_or_none()


def list_recommendations(
    db: Session, skip: int = 0, limit: int = 100
) -> List[Recommendation]:
    return db.query(Recommendation).offset(skip).limit(limit).all()


def update_recommendation(
    db: Session, recommendation_id: str, updates: dict
) -> Optional[Recommendation]:
    recommendation = get_recommendation(db, recommendation_id)
    if not recommendation:
        return None
    for key, value in updates.items():
        if hasattr(recommendation, key):
            setattr(recommendation, key, value)
    db.flush()
    return recommendation


def delete_recommendation(db: Session, recommendation_id: str) -> bool:
    recommendation = get_recommendation(db, recommendation_id)
    if not recommendation:
        return False
    db.delete(recommendation)
    db.flush()
    return True
