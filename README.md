# 🧮 STARK Proof Generator

**STARK Proof Generator** is a Python application that generates and verifies lightweight cryptographic proofs inspired by the STARK protocol.  
The service exposes a simple HTTP API using **Flask**, designed to run in serverless environments like **Google Cloud Run**.

---

## 🚀 Features

- Generates pseudo-random sequences based on `keccak256`  
- Builds Merkle trees for polynomial commitments  
- Polynomial interpolation and evaluation over a finite field  
- Constructs and verifies FRI layers  
- Exposes an HTTP API for generating proofs  
- Fully deployable on Google Cloud Run

---

## 🧩 API Reference

### `POST /generate-proof`

Generates a cryptographic proof from arbitrary input.

#### Request
```json
{
  "input": "example_input",
  "queries": 2,
  "challenges": {
    "poly_coeffs": [1, 2, 3],
    "folding_coeffs": [],
    "challenges": []
  }
}
