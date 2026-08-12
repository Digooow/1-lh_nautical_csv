-- Schema gerado automaticamente
-- Data: 2026-08-12 03:39:46

DROP TABLE IF EXISTS addresses CASCADE;
CREATE TABLE addresses (
    "id" INTEGER,
    "customer_id" INTEGER,
    "address_type" TEXT,
    "postal_code" TEXT,
    "street" TEXT,
    "number" INTEGER,
    "complement" TEXT,
    "district" TEXT,
    "city" TEXT,
    "state" TEXT,
    "country" TEXT,
    "is_primary" TEXT
);

DROP TABLE IF EXISTS attributes CASCADE;
CREATE TABLE attributes (
    "id" INTEGER,
    "name" TEXT,
    "data_type" TEXT
);

DROP TABLE IF EXISTS brands CASCADE;
CREATE TABLE brands (
    "id" INTEGER,
    "name" TEXT,
    "country" TEXT,
    "is_active" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS categories CASCADE;
CREATE TABLE categories (
    "id" INTEGER,
    "name" TEXT,
    "slug" TEXT,
    "parent_category_id" INTEGER,
    "is_active" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS customers CASCADE;
CREATE TABLE customers (
    "id" INTEGER,
    "person_type" TEXT,
    "legal_name" TEXT,
    "trade_name" TEXT,
    "tax_id" TEXT,
    "state_registration" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "is_active" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS employees CASCADE;
CREATE TABLE employees (
    "id" INTEGER,
    "full_name" TEXT,
    "cpf" TEXT,
    "email" TEXT,
    "role" TEXT,
    "primary_location_id" INTEGER,
    "hire_date" DATE,
    "termination_date" DATE,
    "is_active" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS fiscal_invoices CASCADE;
CREATE TABLE fiscal_invoices (
    "id" INTEGER,
    "order_id" INTEGER,
    "nfe_number" TEXT,
    "nfe_access_key" TEXT,
    "series" TEXT,
    "issued_at" TIMESTAMP,
    "status" TEXT,
    "total_amount" NUMERIC,
    "xml_storage_uri" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS goods_receipts CASCADE;
CREATE TABLE goods_receipts (
    "id" INTEGER,
    "purchase_order_id" INTEGER,
    "received_by_employee_id" INTEGER,
    "received_at" TIMESTAMP,
    "notes" TEXT,
    "created_at" TIMESTAMP
);

DROP TABLE IF EXISTS goods_receipt_items CASCADE;
CREATE TABLE goods_receipt_items (
    "id" INTEGER,
    "goods_receipt_id" INTEGER,
    "purchase_order_item_id" INTEGER,
    "quantity_received" NUMERIC
);

DROP TABLE IF EXISTS locations CASCADE;
CREATE TABLE locations (
    "id" INTEGER,
    "name" TEXT,
    "location_type" TEXT,
    "postal_code" TEXT,
    "street" TEXT,
    "number" INTEGER,
    "complement" TEXT,
    "district" TEXT,
    "city" TEXT,
    "state" TEXT,
    "country" TEXT,
    "is_active" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS orders CASCADE;
CREATE TABLE orders (
    "id" INTEGER,
    "order_number" TEXT,
    "channel" TEXT,
    "customer_id" INTEGER,
    "salesperson_id" INTEGER,
    "location_id" INTEGER,
    "status" TEXT,
    "subtotal" NUMERIC,
    "discount_amount" NUMERIC,
    "total" NUMERIC,
    "placed_at" TIMESTAMP,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS order_items CASCADE;
CREATE TABLE order_items (
    "id" INTEGER,
    "order_id" INTEGER,
    "product_variant_id" INTEGER,
    "quantity" INTEGER,
    "unit_price" NUMERIC,
    "icms_rate" NUMERIC,
    "ipi_rate" NUMERIC,
    "line_total" NUMERIC
);

DROP TABLE IF EXISTS payments CASCADE;
CREATE TABLE payments (
    "id" INTEGER,
    "order_id" INTEGER,
    "method" TEXT,
    "installments" INTEGER,
    "amount" NUMERIC,
    "status" TEXT,
    "paid_at" TIMESTAMP,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS products CASCADE;
CREATE TABLE products (
    "id" INTEGER,
    "name" TEXT,
    "description" TEXT,
    "brand_id" INTEGER,
    "category_id" INTEGER,
    "ncm_code" INTEGER,
    "unit_of_measure" TEXT,
    "is_active" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS product_suppliers CASCADE;
CREATE TABLE product_suppliers (
    "product_variant_id" INTEGER,
    "supplier_id" INTEGER,
    "supplier_sku" TEXT,
    "last_quoted_cost" NUMERIC,
    "lead_time_days" INTEGER,
    "is_preferred" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS product_variants CASCADE;
CREATE TABLE product_variants (
    "id" INTEGER,
    "product_id" INTEGER,
    "sku" TEXT,
    "barcode_ean" TEXT,
    "sale_price" NUMERIC,
    "cost_price" NUMERIC,
    "weight_kg" NUMERIC,
    "icms_rate" NUMERIC,
    "ipi_rate" NUMERIC,
    "is_active" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS purchase_orders CASCADE;
CREATE TABLE purchase_orders (
    "id" INTEGER,
    "po_number" TEXT,
    "supplier_id" INTEGER,
    "buyer_id" INTEGER,
    "destination_location_id" INTEGER,
    "status" TEXT,
    "currency" TEXT,
    "subtotal" NUMERIC,
    "total" NUMERIC,
    "placed_at" TIMESTAMP,
    "expected_delivery_at" DATE,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS purchase_order_items CASCADE;
CREATE TABLE purchase_order_items (
    "id" INTEGER,
    "purchase_order_id" INTEGER,
    "product_variant_id" INTEGER,
    "quantity_ordered" INTEGER,
    "unit_cost" NUMERIC,
    "line_total" NUMERIC
);

DROP TABLE IF EXISTS returns CASCADE;
CREATE TABLE returns (
    "id" INTEGER,
    "return_number" TEXT,
    "order_id" INTEGER,
    "customer_id" INTEGER,
    "received_at_location_id" INTEGER,
    "status" TEXT,
    "reason" TEXT,
    "total_refund_amount" NUMERIC,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS return_items CASCADE;
CREATE TABLE return_items (
    "id" INTEGER,
    "return_id" INTEGER,
    "order_item_id" INTEGER,
    "quantity" NUMERIC,
    "action" TEXT,
    "exchange_variant_id" INTEGER,
    "unit_refund_amount" NUMERIC
);

DROP TABLE IF EXISTS stock_levels CASCADE;
CREATE TABLE stock_levels (
    "product_variant_id" INTEGER,
    "location_id" INTEGER,
    "quantity_on_hand" NUMERIC,
    "reorder_point" TEXT,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS stock_movements CASCADE;
CREATE TABLE stock_movements (
    "id" INTEGER,
    "product_variant_id" INTEGER,
    "location_id" INTEGER,
    "movement_type" TEXT,
    "quantity" NUMERIC,
    "reference_table" TEXT,
    "reference_id" INTEGER,
    "employee_id" INTEGER,
    "notes" TEXT,
    "occurred_at" TIMESTAMP,
    "created_at" TIMESTAMP
);

DROP TABLE IF EXISTS suppliers CASCADE;
CREATE TABLE suppliers (
    "id" INTEGER,
    "legal_name" TEXT,
    "trade_name" TEXT,
    "country" TEXT,
    "tax_id" TEXT,
    "tax_id_type" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "contact_name" TEXT,
    "is_active" TEXT,
    "created_at" TIMESTAMP,
    "updated_at" TIMESTAMP
);

DROP TABLE IF EXISTS variant_attribute_values CASCADE;
CREATE TABLE variant_attribute_values (
    "product_variant_id" INTEGER,
    "attribute_id" INTEGER,
    "value" TEXT
);