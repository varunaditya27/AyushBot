"""AyushBot Backend — Database Models (SQLAlchemy ORM).

Defines the SQLite schema for offline-first syncing with Android devices.
Models mirror `/android/app/src/main/java/com/ayushbot/app/data/local/entity/`.
"""

from __future__ import annotations

import time
from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now_ms() -> int:
	return int(time.time() * 1000)


class Base(DeclarativeBase):
	__abstract__ = True


class Patient(Base):
	__tablename__ = "patients"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	abha_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
	name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
	age_months: Mapped[int] = mapped_column(Integer, nullable=False)
	sex: Mapped[str] = mapped_column(String(16), nullable=False)
	village: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
	asha_id: Mapped[str] = mapped_column(String(64), nullable=False)
	created_at: Mapped[int] = mapped_column(Integer, default=_now_ms, nullable=False)

	cases: Mapped[List["Case"]] = relationship(
		back_populates="patient",
		cascade="all, delete-orphan",
		passive_deletes=True,
	)


class Case(Base):
	__tablename__ = "cases"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	patient_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
	)
	timestamp: Mapped[int] = mapped_column(Integer, default=_now_ms, nullable=False)
	spo2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
	heart_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
	temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
	weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
	symptoms: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
	risk_tier: Mapped[str] = mapped_column(String(16), default="LOW", nullable=False)
	sync_status: Mapped[str] = mapped_column(
		String(16), default="PENDING", nullable=False
	)

	patient: Mapped["Patient"] = relationship(back_populates="cases")
	recommendation: Mapped[Optional["Recommendation"]] = relationship(
		back_populates="case",
		cascade="all, delete-orphan",
		passive_deletes=True,
		uselist=False,
	)

	__table_args__ = (
		Index("ix_cases_patient_timestamp", "patient_id", "timestamp"),
		Index("ix_cases_sync_status", "sync_status"),
	)


class Recommendation(Base):
	__tablename__ = "recommendations"

	id: Mapped[str] = mapped_column(String(64), primary_key=True)
	case_id: Mapped[str] = mapped_column(
		String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, unique=True
	)
	primary_diagnosis: Mapped[str] = mapped_column(String(256), nullable=False)
	confidence: Mapped[str] = mapped_column(String(16), default="Low", nullable=False)
	differential_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
	action_plan: Mapped[str] = mapped_column(Text, default="", nullable=False)
	referral_facility: Mapped[Optional[str]] = mapped_column(
		String(128), nullable=True
	)
	drug_dosage: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
	counseling: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	citation_source: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
	citation_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	created_at: Mapped[int] = mapped_column(Integer, default=_now_ms, nullable=False)

	case: Mapped["Case"] = relationship(back_populates="recommendation")
