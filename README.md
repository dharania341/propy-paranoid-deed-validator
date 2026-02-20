# Propy – Paranoid Deed Validator

## Overview

This project demonstrates a safe architecture for using LLMs in financial and blockchain-sensitive workflows.

The LLM is used **only for structured extraction** from messy OCR text.

All validation and financial logic is enforced deterministically in Python.

---

## Architecture

### 1. Extraction Layer (LLM)
- temperature = 0
- Strict JSON output
- Used only to parse messy OCR text

### 2. Validation Layer (Deterministic)
The system performs strict checks:

- Date ordering validation (Recorded date cannot precede Signed date)
- Numeric vs written amount cross-validation
- County normalization using fuzzy matching
- Hard failure on inconsistencies

### 3. Enrichment Layer
- County normalization via RapidFuzz
- Tax rate lookup from local reference JSON
- Closing tax calculation

---

## Validation Strategy

This system intentionally does NOT rely on the LLM for:

- Date validation
- Monetary consistency
- Business logic enforcement
- Tax computation

All validation is deterministic and explicitly fails on inconsistencies.

This ensures unsafe data cannot be recorded to a blockchain ledger.

---

## Expected Behavior

The provided sample deed intentionally fails validation:

1. Recorded date occurs before signed date
2. $1,250,000 ≠ "One Million Two Hundred Thousand"

The system throws explicit errors instead of silently correcting data.

---

## Run Instructions

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_key_here
python app.py
---

## Engineering Philosophy

This system treats the LLM as a probabilistic parser — not a source of truth.

All financial correctness, legal consistency, and business logic are enforced deterministically in code.

Design principle:

- LLM = Fuzzy extraction
- Code = Deterministic truth

In blockchain-sensitive systems, silent correction is dangerous.
Explicit failure is safer than implicit acceptance.

This project demonstrates how to safely integrate AI into high-integrity financial systems.
