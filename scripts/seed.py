"""Seed the database with compliance rules, a demo admin, and demo data.

Usage:
    python -m scripts.seed
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.db.base import Base
from app.db.models import ComplianceRule, Product, Scan, User, Violation
from app.db.session import SessionLocal, engine
from app.utils.security import hash_password

RULES = [
    {
        "rule_id": "R6_1_a", "rule_title": "Manufacturer / Packer / Importer Identity",
        "description": "Name and address of manufacturer, packer, or importer.",
        "severity": "CRITICAL", "check_type": "presence+completeness",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R6_1_b", "rule_title": "Common / Generic Name",
        "description": "Common or generic name of the commodity.",
        "severity": "MAJOR", "check_type": "presence",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R6_1_c", "rule_title": "Net Quantity",
        "description": "Net quantity in standard unit of weights and measures.",
        "severity": "CRITICAL", "check_type": "presence+unit_validation",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R6_1_e", "rule_title": "Month and Year of Manufacture",
        "description": "Month and year in which commodity is manufactured.",
        "severity": "CRITICAL", "check_type": "presence+format_validation",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R6_1_f", "rule_title": "Maximum Retail Price",
        "description": "MRP inclusive of all taxes.",
        "severity": "CRITICAL", "check_type": "presence+content_validation",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R6_1_g", "rule_title": "Consumer Care Details",
        "description": "Consumer care number, email or website.",
        "severity": "MAJOR", "check_type": "presence+contact_info",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R6_1_h", "rule_title": "FSSAI License",
        "description": "FSSAI license/registration number (food only).",
        "severity": "CRITICAL", "check_type": "presence+format",
        "applies_to_categories": ["food"],
    },
    {
        "rule_id": "R6_1_i", "rule_title": "Country of Origin",
        "description": "Country of origin for imported goods.",
        "severity": "CRITICAL", "check_type": "presence",
        "applies_to_categories": ["import"],
    },
    {
        "rule_id": "R6_1_j", "rule_title": "Batch / Lot Number",
        "description": "Batch or lot number.",
        "severity": "MAJOR", "check_type": "presence",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R6_2", "rule_title": "Font Size Compliance",
        "description": "Minimum lettering height by package size.",
        "severity": "MAJOR", "check_type": "font_size",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R6_5", "rule_title": "MRP on Principal Display Panel",
        "description": "MRP must be on the principal display panel.",
        "severity": "MAJOR", "check_type": "panel_position",
        "applies_to_categories": None,
    },
    {
        "rule_id": "R26", "rule_title": "No Misleading Declarations",
        "description": "No false or unsubstantiated marketing claims.",
        "severity": "MAJOR", "check_type": "nlp",
        "applies_to_categories": None,
    },
]


def seed_rules(db):
    for r in RULES:
        exists = db.query(ComplianceRule).filter(
            ComplianceRule.rule_id == r["rule_id"]
        ).first()
        if not exists:
            db.add(ComplianceRule(**r))
    db.commit()
    print(f"Seeded {len(RULES)} compliance rules")


def seed_users(db):
    users = [
        {"name": "Admin User", "email": "admin@labelguard.in", "role": "ADMIN",
         "password": "admin123", "state": "Maharashtra", "district": "Mumbai"},
        {"name": "Officer Sharma", "email": "officer@labelguard.in", "role": "OFFICER",
         "password": "officer123", "state": "Maharashtra", "district": "Mumbai"},
        {"name": "Officer Patel", "email": "officer2@labelguard.in", "role": "OFFICER",
         "password": "officer123", "state": "Gujarat", "district": "Ahmedabad"},
        {"name": "Supervisor Rao", "email": "supervisor@labelguard.in", "role": "SUPERVISOR",
         "password": "super123", "state": "Karnataka", "district": "Bengaluru"},
        {"name": "Viewer Singh", "email": "viewer@labelguard.in", "role": "VIEWER",
         "password": "view123", "state": "Delhi", "district": "New Delhi"},
    ]
    for u in users:
        exists = db.query(User).filter(User.email == u["email"]).first()
        if not exists:
            db.add(User(
                name=u["name"], email=u["email"], role=u["role"],
                state=u["state"], district=u["district"],
                hashed_password=hash_password(u["password"]),
            ))
    db.commit()
    print("Seeded demo users")


def seed_demo_data(db):
    admin = db.query(User).filter(User.email == "admin@labelguard.in").first()
    officer = db.query(User).filter(User.email == "officer@labelguard.in").first()
    products = [
        {"name": "Lay's Classic Salted", "brand": "PepsiCo India", "category": "food",
         "barcode": "8901491503573"},
        {"name": "Maggi 2-Minute Noodles", "brand": "Nestle India", "category": "food",
         "barcode": "8901058020318"},
        {"name": "Parle-G Gold", "brand": "Parle Products", "category": "food",
         "barcode": "8901719100035"},
        {"name": "Dettol Handwash", "brand": "Reckitt", "category": "cosmetics",
         "barcode": "8901030508015"},
        {"name": "Colgate Max Fresh", "brand": "Colgate-Palmolive", "category": "cosmetics",
         "barcode": "8901081044008"},
        {"name": "Tata Salt", "brand": "Tata Consumer", "category": "food",
         "barcode": "8904063200018"},
    ]
    statuses = ["COMPLIANT", "NON_COMPLIANT", "NON_COMPLIANT", "PARTIAL",
                "COMPLIANT", "PARTIAL"]
    for p, st in zip(products, statuses):
        prod = db.query(Product).filter(
            Product.barcode == p["barcode"]
        ).first()
        if not prod:
            prod = Product(
                product_name=p["name"], brand=p["brand"], category=p["category"],
                barcode=p["barcode"],
            )
            db.add(prod)
            db.flush()
        scan = Scan(
            product_id=prod.id, officer_id=officer.id if officer else None,
            source="web", status="complete", overall_status=st,
            compliance_score=0.85 if st == "COMPLIANT" else (0.4 if st == "NON_COMPLIANT" else 0.6),
        )
        db.add(scan)
        db.flush()
        if st != "COMPLIANT":
            db.add(Violation(
                scan_id=scan.id, rule_id="R6_1_f",
                rule_title="Maximum Retail Price",
                violation_type="CONTENT", severity="CRITICAL",
                finding="Missing 'inclusive of all taxes' clause",
                found_value="MRP ₹20", expected_format="MRP ₹20 (Inclusive of all taxes)",
            ))
            db.add(Violation(
                scan_id=scan.id, rule_id="R6_2",
                rule_title="Font Size Compliance",
                violation_type="FONT_SIZE", severity="MAJOR",
                finding="Net quantity font height 0.7mm < required 1.0mm",
                found_value="0.70mm", expected_format=">= 1.0mm",
            ))
    db.commit()
    print("Seeded demo products + scans")


def main():
    # Create schema from models (works on SQLite + Postgres, zero-install path).
    import app.db.models  # noqa: F401 - register all tables
    from app.db.base import Base

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_rules(db)
        seed_users(db)
        seed_demo_data(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
