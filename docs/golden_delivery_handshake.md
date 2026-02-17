# Golden Delivery ↔ FlexyFins Handshake

## Stable event envelope

```json
{
  "mission_id": "VAL-1771035623",
  "mission_name": "GOLDEN_DELIVERY",
  "node_id": "node_payment_router",
  "capability_id": "cap_payment_router_v5_0_0",
  "event_type": "MANIFEST_GENERATED",
  "status": "VERIFIED",
  "amount": 19.0,
  "currency": "USD",
  "reason_code": "",
  "message": "Settlement provider: lemonsqueezy. Order tagged. Delivery dispatched.",
  "proof_ref": "reports/value_propositions/manifest_VAL-1771035623.md",
  "timestamp_utc": "2026-02-17T15:10:11Z",
  "meta": {
    "gateway_primary": "lemonsqueezy",
    "gateway_fallback": "shopier",
    "shopify_order_id": "1234567890",
    "tags": ["settlement:lemonsqueezy", "golden:verified"]
  }
}
```

## Endpoint

- POST `/api/gd/ingest`
- Query: none
- Auth: TBD (recommended: token header)

## Required conventions

- `mission_id` MUST follow `VAL-` pattern
- `proof_ref` MUST point to manifest/proof artifact
- Failures MUST set `reason_code`
