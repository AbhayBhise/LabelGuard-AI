"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("role", sa.String(30), nullable=False, server_default="OFFICER"),
        sa.Column("state", sa.String(50), nullable=True),
        sa.Column("district", sa.String(50), nullable=True),
        sa.Column("department", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "products",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("barcode", sa.String(50), nullable=True),
        sa.Column("product_name", sa.Text(), nullable=True),
        sa.Column("brand", sa.Text(), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), onupdate=sa.func.now()),
    )
    op.create_index("ix_products_barcode", "products", ["barcode"])

    op.create_table(
        "compliance_rules",
        sa.Column("rule_id", sa.String(20), primary_key=True),
        sa.Column("rule_title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("check_type", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("applies_to_categories", sa.JSON(), nullable=True),
    )

    op.create_table(
        "scans",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Uuid(),
            sa.ForeignKey("products.id"),
            nullable=True,
        ),
        sa.Column(
            "officer_id",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("scanned_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("location_lat", sa.DECIMAL(9, 6), nullable=True),
        sa.Column("location_lng", sa.DECIMAL(9, 6), nullable=True),
        sa.Column("source", sa.String(50), server_default="web"),
        sa.Column("raw_image_url", sa.Text(), nullable=True),
        sa.Column("processed_image_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="processing"),
        sa.Column("overall_status", sa.String(20), nullable=True),
        sa.Column("compliance_score", sa.DECIMAL(4, 3), nullable=True),
        sa.Column("net_weight_grams", sa.DECIMAL(10, 2), nullable=True),
    )

    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "scan_id",
            sa.Uuid(),
            sa.ForeignKey("scans.id"),
            nullable=False,
        ),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("extracted_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.DECIMAL(5, 4), nullable=True),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.Column(
            "extraction_method", sa.String(50), server_default="ocr"
        ),
    )
    op.create_index(
        "ix_extracted_fields_scan_id", "extracted_fields", ["scan_id"]
    )

    op.create_table(
        "violations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "scan_id",
            sa.Uuid(),
            sa.ForeignKey("scans.id"),
            nullable=False,
        ),
        sa.Column("rule_id", sa.String(20), nullable=False),
        sa.Column("rule_title", sa.Text(), nullable=True),
        sa.Column("rule_description", sa.Text(), nullable=True),
        sa.Column("violation_type", sa.String(30), server_default="MISSING"),
        sa.Column("severity", sa.String(20), server_default="MAJOR"),
        sa.Column("finding", sa.Text(), nullable=True),
        sa.Column("found_value", sa.Text(), nullable=True),
        sa.Column("expected_format", sa.Text(), nullable=True),
        sa.Column("evidence_image_url", sa.Text(), nullable=True),
        sa.Column("evidence_bbox", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_violations_scan_id", "violations", ["scan_id"])


def downgrade() -> None:
    op.drop_table("violations")
    op.drop_table("extracted_fields")
    op.drop_table("scans")
    op.drop_table("compliance_rules")
    op.drop_table("products")
    op.drop_table("users")
