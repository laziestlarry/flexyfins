from __future__ import annotations

from typing import Any, Dict, Tuple

# Evidence tiers: higher = more financially credible
EVIDENCE_TIERS: Dict[str, int] = {
    "PAYMENT_SUCCEEDED": 1,
    "PAYMENT_VERIFIED": 1,
    "ORDER_TAGGED": 2,
    "DELIVERY_DISPATCHED": 3,
    "PROOF_MINTED": 3,
    "SETTLEMENT_CONFIRMED": 4,
}

# Simple runbook map: reason_code -> (title, steps[])
RUNBOOKS: Dict[str, Tuple[str, list[str]]] = {
    "webhook_invalid": (
        "Webhook signature invalid",
        [
            "Confirm webhook secret matches provider settings.",
            "Rotate webhook secret and update Secret Manager / env var.",
            "Replay webhook event from provider dashboard.",
        ],
    ),
    "auth_failed": (
        "Authorization failed",
        [
            "Confirm API token scopes (Shopify Admin, MoR provider).",
            "Rotate token and redeploy service.",
            "Verify env vars are present at runtime (not local-only).",
        ],
    ),
    "tag_failed": (
        "Shopify tagging failed",
        [
            "Check SHOPIFY_ADMIN_TOKEN scopes: write_orders/read_orders.",
            "Confirm SHOPIFY_STORE_URL is correct (myshop.myshopify.com).",
            "Retry tagging with exponential backoff; emit FAILURE envelope on final try.",
        ],
    ),
    "delivery_failed": (
        "Delivery dispatch failed",
        [
            "Verify delivery asset exists and URL is reachable.",
            "Check storage permissions (GCS signed URL or public object).",
            "Re-dispatch delivery and emit DELIVERY_DISPATCHED once confirmed.",
        ],
    ),
    "payout_pending": (
        "Settlement pending",
        [
            "Record payout expected date in meta.payout_expected_at.",
            "Run daily payout scan job.",
            "Emit SETTLEMENT_CONFIRMED once payout reference is observed.",
        ],
    ),
}
