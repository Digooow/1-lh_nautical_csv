DROP TABLE IF EXISTS addresses CASCADE;
CREATE TABLE addresses ("id" TEXT, "customer_id" TEXT, "address_type" TEXT, "postal_code" TEXT, "street" TEXT, "number" TEXT, "complement" TEXT, "district" TEXT, "city" TEXT, "state" TEXT, "country" TEXT, "is_primary" TEXT);
\COPY addresses FROM '/tmp/addresses.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS attributes CASCADE;
CREATE TABLE attributes ("id" TEXT, "name" TEXT, "data_type" TEXT);
\COPY attributes FROM '/tmp/attributes.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS brands CASCADE;
CREATE TABLE brands ("id" TEXT, "name" TEXT, "country" TEXT, "is_active" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY brands FROM '/tmp/brands.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS categories CASCADE;
CREATE TABLE categories ("id" TEXT, "name" TEXT, "slug" TEXT, "parent_category_id" TEXT, "is_active" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY categories FROM '/tmp/categories.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS customers CASCADE;
CREATE TABLE customers ("id" TEXT, "person_type" TEXT, "legal_name" TEXT, "trade_name" TEXT, "tax_id" TEXT, "state_registration" TEXT, "email" TEXT, "phone" TEXT, "is_active" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY customers FROM '/tmp/customers.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS employees CASCADE;
CREATE TABLE employees ("id" TEXT, "full_name" TEXT, "cpf" TEXT, "email" TEXT, "role" TEXT, "primary_location_id" TEXT, "hire_date" TEXT, "termination_date" TEXT, "is_active" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY employees FROM '/tmp/employees.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS fiscal_invoices CASCADE;
CREATE TABLE fiscal_invoices ("id" TEXT, "order_id" TEXT, "nfe_number" TEXT, "nfe_access_key" TEXT, "series" TEXT, "issued_at" TEXT, "status" TEXT, "total_amount" TEXT, "xml_storage_uri" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY fiscal_invoices FROM '/tmp/fiscal_invoices.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS goods_receipts CASCADE;
CREATE TABLE goods_receipts ("id" TEXT, "purchase_order_id" TEXT, "received_by_employee_id" TEXT, "received_at" TEXT, "notes" TEXT, "created_at" TEXT);
\COPY goods_receipts FROM '/tmp/goods_receipts.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS goods_receipt_items CASCADE;
CREATE TABLE goods_receipt_items ("id" TEXT, "goods_receipt_id" TEXT, "purchase_order_item_id" TEXT, "quantity_received" TEXT);
\COPY goods_receipt_items FROM '/tmp/goods_receipt_items.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS locations CASCADE;
CREATE TABLE locations ("id" TEXT, "name" TEXT, "location_type" TEXT, "postal_code" TEXT, "street" TEXT, "number" TEXT, "complement" TEXT, "district" TEXT, "city" TEXT, "state" TEXT, "country" TEXT, "is_active" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY locations FROM '/tmp/locations.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS orders CASCADE;
CREATE TABLE orders ("id" TEXT, "order_number" TEXT, "channel" TEXT, "customer_id" TEXT, "salesperson_id" TEXT, "location_id" TEXT, "status" TEXT, "subtotal" TEXT, "discount_amount" TEXT, "total" TEXT, "placed_at" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY orders FROM '/tmp/orders.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS order_items CASCADE;
CREATE TABLE order_items ("id" TEXT, "order_id" TEXT, "product_variant_id" TEXT, "quantity" TEXT, "unit_price" TEXT, "icms_rate" TEXT, "ipi_rate" TEXT, "line_total" TEXT);
\COPY order_items FROM '/tmp/order_items.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS payments CASCADE;
CREATE TABLE payments ("id" TEXT, "order_id" TEXT, "method" TEXT, "installments" TEXT, "amount" TEXT, "status" TEXT, "paid_at" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY payments FROM '/tmp/payments.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS products CASCADE;
CREATE TABLE products ("id" TEXT, "name" TEXT, "description" TEXT, "brand_id" TEXT, "category_id" TEXT, "ncm_code" TEXT, "unit_of_measure" TEXT, "is_active" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY products FROM '/tmp/products.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS product_suppliers CASCADE;
CREATE TABLE product_suppliers ("product_variant_id" TEXT, "supplier_id" TEXT, "supplier_sku" TEXT, "last_quoted_cost" TEXT, "lead_time_days" TEXT, "is_preferred" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY product_suppliers FROM '/tmp/product_suppliers.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS product_variants CASCADE;
CREATE TABLE product_variants ("id" TEXT, "product_id" TEXT, "sku" TEXT, "barcode_ean" TEXT, "sale_price" TEXT, "cost_price" TEXT, "weight_kg" TEXT, "icms_rate" TEXT, "ipi_rate" TEXT, "is_active" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY product_variants FROM '/tmp/product_variants.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS purchase_orders CASCADE;
CREATE TABLE purchase_orders ("id" TEXT, "po_number" TEXT, "supplier_id" TEXT, "buyer_id" TEXT, "destination_location_id" TEXT, "status" TEXT, "currency" TEXT, "subtotal" TEXT, "total" TEXT, "placed_at" TEXT, "expected_delivery_at" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY purchase_orders FROM '/tmp/purchase_orders.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS purchase_order_items CASCADE;
CREATE TABLE purchase_order_items ("id" TEXT, "purchase_order_id" TEXT, "product_variant_id" TEXT, "quantity_ordered" TEXT, "unit_cost" TEXT, "line_total" TEXT);
\COPY purchase_order_items FROM '/tmp/purchase_order_items.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS returns CASCADE;
CREATE TABLE returns ("id" TEXT, "return_number" TEXT, "order_id" TEXT, "customer_id" TEXT, "received_at_location_id" TEXT, "status" TEXT, "reason" TEXT, "total_refund_amount" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY returns FROM '/tmp/returns.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS return_items CASCADE;
CREATE TABLE return_items ("id" TEXT, "return_id" TEXT, "order_item_id" TEXT, "quantity" TEXT, "action" TEXT, "exchange_variant_id" TEXT, "unit_refund_amount" TEXT);
\COPY return_items FROM '/tmp/return_items.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS stock_levels CASCADE;
CREATE TABLE stock_levels ("product_variant_id" TEXT, "location_id" TEXT, "quantity_on_hand" TEXT, "reorder_point" TEXT, "updated_at" TEXT);
\COPY stock_levels FROM '/tmp/stock_levels.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS stock_movements CASCADE;
CREATE TABLE stock_movements ("id" TEXT, "product_variant_id" TEXT, "location_id" TEXT, "movement_type" TEXT, "quantity" TEXT, "reference_table" TEXT, "reference_id" TEXT, "employee_id" TEXT, "notes" TEXT, "occurred_at" TEXT, "created_at" TEXT);
\COPY stock_movements FROM '/tmp/stock_movements.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS suppliers CASCADE;
CREATE TABLE suppliers ("id" TEXT, "legal_name" TEXT, "trade_name" TEXT, "country" TEXT, "tax_id" TEXT, "tax_id_type" TEXT, "email" TEXT, "phone" TEXT, "contact_name" TEXT, "is_active" TEXT, "created_at" TEXT, "updated_at" TEXT);
\COPY suppliers FROM '/tmp/suppliers.csv' WITH (FORMAT CSV, HEADER true);

DROP TABLE IF EXISTS variant_attribute_values CASCADE;
CREATE TABLE variant_attribute_values ("product_variant_id" TEXT, "attribute_id" TEXT, "value" TEXT);
\COPY variant_attribute_values FROM '/tmp/variant_attribute_values.csv' WITH (FORMAT CSV, HEADER true);

