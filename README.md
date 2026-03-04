# Cloudbeds Package Dashboard (Starter)

A lightweight starter app for a package coordinator dashboard showing:

- **Upcoming packages/reservations** in the next 14 days
- **Cancelled packages/reservations** in a separate section
- Property filter for **Berlin Encore** and **Berlin Resort**
- Webhook ingestion endpoint for Cloudbeds updates

## Quick start

```bash
python3 server.py
```

Then open: <http://localhost:8000>

## Endpoints

- `POST /webhooks/cloudbeds` - ingest reservation/package updates (booked/modified/cancelled)
- `GET /api/packages/upcoming?days=14&property=all|encore|resort`
- `GET /api/packages/cancelled?days=14&property=all|encore|resort`
- `GET /health`

## Webhook payload (example)

```json
{
  "reservation_id": "CB-12345",
  "property_id": "encore",
  "property_name": "Berlin Encore",
  "guest_name": "Jane Smith",
  "arrival_date": "2026-03-10",
  "departure_date": "2026-03-12",
  "package_name": "Romance Package",
  "package_code": "ROM-01",
  "status": "cancelled",
  "source_updated_at": "2026-03-05T14:25:00Z"
}
```

## Notes for Cloudbeds setup

1. Create webhook subscription(s) in Cloudbeds for reservation/package lifecycle events.
2. Point webhook URL to your public endpoint: `https://<your-domain>/webhooks/cloudbeds`.
3. If available, validate request signatures before processing.
4. Add a scheduled reconciliation job that calls Cloudbeds API every 15–30 minutes.

This starter includes a `CloudbedsClient` stub where you can add the real API integration.
