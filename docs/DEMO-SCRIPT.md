# Demo Script

<TO FILL: walkthrough for judges>

## Setup (pre-demo)

```bash
python scripts/setup.py
docker compose up -d
```

## 1. The vulnerable app

<TO FILL: show patient-portal running, hit GET /patients/1, observe PHI in response>

## 2. Aegis scan

<TO FILL: `aegis scan demo/patient-portal` — show 10 findings with severities>

## 3. Bob takes over

<TO FILL: launch Bob, point at MCP server, have Bob explain top 3 violations with CFR citations>

## 4. Dashboard

<TO FILL: open localhost:5173, walk through Overview → Findings → Reports tabs>

## 5. Generate evidence package

<TO FILL: `aegis report --format pdf --out audit.pdf` — open the PDF, show CFR-linked evidence>

## Talking points

<TO FILL: why this matters, defensibility, judging criteria mapping>
