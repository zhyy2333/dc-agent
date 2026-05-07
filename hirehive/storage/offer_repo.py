"""Offer repository."""

import json
from hirehive.storage.engine import get_connection
from hirehive.models.offer import Offer


def save_offer(offer: Offer) -> int:
    conn = get_connection()
    row = conn.execute(
        """INSERT INTO offer (application_id, company, position, base_salary,
           bonus_months, equity, benefits, work_mode, location, commute_minutes,
           growth_potential, expires_at, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING id""",
        (offer.application_id, offer.company, offer.position, offer.base_salary,
         offer.bonus_months, offer.equity, json.dumps(offer.benefits, ensure_ascii=False),
         offer.work_mode, offer.location, offer.commute_minutes,
         offer.growth_potential, offer.expires_at, offer.status),
    ).fetchone()
    conn.commit()
    conn.close()
    return row["id"]


def get_offers(status: str | None = None) -> list[dict]:
    conn = get_connection()
    query = "SELECT * FROM offer WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY received_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_offer_status(offer_id: int, status: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE offer SET status = ? WHERE id = ?", (status, offer_id))
    conn.commit()
    conn.close()
