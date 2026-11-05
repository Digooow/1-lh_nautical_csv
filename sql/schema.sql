-- =============================================================================
-- LH Nautical — Schema Relacional Completo (PostgreSQL 16)
-- =============================================================================
-- Inclui:
--   1. Tipagem estrita (BOOLEAN, NUMERIC(12,2), NUMERIC(12,3), CHAR(8), DATE, TIMESTAMP)
--   2. Chaves primárias (simples e compostas) e chaves estrangeiras (37 relacionamentos)
--   3. Índices analíticos para aceleração de joins e agregações temporais
--   4. Views canônicas (Single Source of Truth) para pedidos comercialmente válidos
-- =============================================================================

DROP VIEW IF EXISTS vw_valid_order_items;
DROP VIEW IF EXISTS vw_valid_orders;

DROP TABLE IF EXISTS stock_movements CASCADE;
DROP TABLE IF EXISTS stock_levels CASCADE;
DROP TABLE IF EXISTS return_items CASCADE;
DROP TABLE IF EXISTS returns CASCADE;
DROP TABLE IF EXISTS goods_receipt_items CASCADE;
DROP TABLE IF EXISTS goods_receipts CASCADE;
DROP TABLE IF EXISTS purchase_order_items CASCADE;
DROP TABLE IF EXISTS purchase_orders CASCADE;
DROP TABLE IF EXISTS fiscal_invoices CASCADE;
DROP TABLE IF EXISTS payments CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS product_suppliers CASCADE;
DROP TABLE IF EXISTS variant_attribute_values CASCADE;
DROP TABLE IF EXISTS product_variants CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS addresses CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS brands CASCADE;
DROP TABLE IF EXISTS attributes CASCADE;
DROP TABLE IF EXISTS locations CASCADE;

-- -----------------------------------------------------------------------------
-- 1. Tabelas Dimensionais e Cadastrais
-- -----------------------------------------------------------------------------

CREATE TABLE locations (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    location_type TEXT NOT NULL,
    postal_code   TEXT NOT NULL,
    street        TEXT NOT NULL,
    number        INTEGER NOT NULL,
    complement    TEXT,
    district      TEXT NOT NULL,
    city          TEXT NOT NULL,
    state         CHAR(2) NOT NULL,
    country       CHAR(2) NOT NULL,
    is_active     BOOLEAN NOT NULL,
    created_at    TIMESTAMP NOT NULL,
    updated_at    TIMESTAMP NOT NULL
);

CREATE TABLE attributes (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    data_type TEXT NOT NULL
);

CREATE TABLE brands (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    country    CHAR(2),
    is_active  BOOLEAN NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE categories (
    id                 INTEGER PRIMARY KEY,
    name               TEXT NOT NULL UNIQUE,
    slug               TEXT NOT NULL UNIQUE,
    parent_category_id INTEGER REFERENCES categories(id) DEFERRABLE INITIALLY DEFERRED,
    is_active          BOOLEAN NOT NULL,
    created_at         TIMESTAMP NOT NULL,
    updated_at         TIMESTAMP NOT NULL
);

CREATE TABLE customers (
    id                 INTEGER PRIMARY KEY,
    person_type        CHAR(2) NOT NULL CHECK (person_type IN ('PF', 'PJ')),
    legal_name         TEXT NOT NULL,
    trade_name         TEXT,
    tax_id             TEXT NOT NULL UNIQUE,
    state_registration TEXT,
    email              TEXT,
    phone              TEXT,
    is_active          BOOLEAN NOT NULL,
    created_at         TIMESTAMP NOT NULL,
    updated_at         TIMESTAMP NOT NULL
);

CREATE TABLE suppliers (
    id           INTEGER PRIMARY KEY,
    legal_name   TEXT NOT NULL,
    trade_name   TEXT,
    country      CHAR(2) NOT NULL,
    tax_id       TEXT NOT NULL UNIQUE,
    tax_id_type  TEXT NOT NULL,
    email        TEXT NOT NULL,
    phone        TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    is_active    BOOLEAN NOT NULL,
    created_at   TIMESTAMP NOT NULL,
    updated_at   TIMESTAMP NOT NULL
);

CREATE TABLE employees (
    id                  INTEGER PRIMARY KEY,
    full_name           TEXT NOT NULL,
    cpf                 CHAR(11) NOT NULL UNIQUE,
    email               TEXT NOT NULL UNIQUE,
    role                TEXT NOT NULL,
    primary_location_id INTEGER NOT NULL REFERENCES locations(id),
    hire_date           DATE NOT NULL,
    termination_date    DATE,
    is_active           BOOLEAN NOT NULL,
    created_at          TIMESTAMP NOT NULL,
    updated_at          TIMESTAMP NOT NULL
);

CREATE TABLE addresses (
    id           INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    address_type TEXT NOT NULL,
    postal_code  TEXT NOT NULL,
    street       TEXT NOT NULL,
    number       INTEGER NOT NULL,
    complement   TEXT,
    district     TEXT NOT NULL,
    city         TEXT NOT NULL,
    state        CHAR(2) NOT NULL,
    country      CHAR(2) NOT NULL,
    is_primary   BOOLEAN NOT NULL
);

CREATE TABLE products (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    brand_id        INTEGER NOT NULL REFERENCES brands(id),
    category_id     INTEGER NOT NULL REFERENCES categories(id),
    ncm_code        CHAR(8) NOT NULL,
    unit_of_measure TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP NOT NULL
);

CREATE TABLE product_variants (
    id          INTEGER PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    sku         TEXT NOT NULL UNIQUE,
    barcode_ean CHAR(13),
    sale_price  NUMERIC(12,2) NOT NULL,
    cost_price  NUMERIC(12,2) NOT NULL,
    weight_kg   NUMERIC(12,3) NOT NULL,
    icms_rate   NUMERIC(5,2) NOT NULL,
    ipi_rate    NUMERIC(5,2) NOT NULL,
    is_active   BOOLEAN NOT NULL,
    created_at  TIMESTAMP NOT NULL,
    updated_at  TIMESTAMP NOT NULL
);

CREATE TABLE variant_attribute_values (
    product_variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    attribute_id       INTEGER NOT NULL REFERENCES attributes(id),
    value              TEXT,
    PRIMARY KEY (product_variant_id, attribute_id)
);

CREATE TABLE product_suppliers (
    product_variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    supplier_id        INTEGER NOT NULL REFERENCES suppliers(id),
    supplier_sku       TEXT,
    last_quoted_cost   NUMERIC(12,2) NOT NULL,
    lead_time_days     INTEGER NOT NULL,
    is_preferred       BOOLEAN NOT NULL,
    created_at         TIMESTAMP NOT NULL,
    updated_at         TIMESTAMP NOT NULL,
    PRIMARY KEY (product_variant_id, supplier_id)
);

-- -----------------------------------------------------------------------------
-- 2. Tabelas Transacionais (Vendas, Suprimentos, Devoluções e Estoque)
-- -----------------------------------------------------------------------------

CREATE TABLE orders (
    id              INTEGER PRIMARY KEY,
    order_number    TEXT NOT NULL UNIQUE,
    channel         TEXT NOT NULL CHECK (channel IN ('ecommerce', 'pos')),
    customer_id     INTEGER NOT NULL REFERENCES customers(id),
    salesperson_id  INTEGER REFERENCES employees(id),
    location_id     INTEGER NOT NULL REFERENCES locations(id),
    status          TEXT NOT NULL CHECK (status IN ('paid', 'confirmed', 'cancelled', 'draft')),
    subtotal        NUMERIC(12,2) NOT NULL,
    discount_amount NUMERIC(12,2) NOT NULL,
    total           NUMERIC(12,2) NOT NULL,
    placed_at       TIMESTAMP NOT NULL,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP NOT NULL
);

CREATE TABLE order_items (
    id                 INTEGER PRIMARY KEY,
    order_id           INTEGER NOT NULL REFERENCES orders(id),
    product_variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    quantity           INTEGER NOT NULL CHECK (quantity > 0),
    unit_price         NUMERIC(12,2) NOT NULL,
    icms_rate          NUMERIC(5,2) NOT NULL,
    ipi_rate           NUMERIC(5,2) NOT NULL,
    line_total         NUMERIC(12,2) NOT NULL
);

CREATE TABLE payments (
    id           INTEGER PRIMARY KEY,
    order_id     INTEGER NOT NULL REFERENCES orders(id),
    method       TEXT NOT NULL,
    installments INTEGER NOT NULL,
    amount       NUMERIC(12,2) NOT NULL,
    status       TEXT NOT NULL,
    paid_at      TIMESTAMP,
    created_at   TIMESTAMP NOT NULL,
    updated_at   TIMESTAMP NOT NULL
);

CREATE TABLE fiscal_invoices (
    id              INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL UNIQUE REFERENCES orders(id),
    nfe_number      TEXT NOT NULL UNIQUE,
    nfe_access_key  CHAR(44) NOT NULL UNIQUE,
    series          CHAR(3) NOT NULL,
    issued_at       TIMESTAMP NOT NULL,
    status          TEXT NOT NULL,
    total_amount    NUMERIC(12,2) NOT NULL,
    xml_storage_uri TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP NOT NULL
);

CREATE TABLE purchase_orders (
    id                      INTEGER PRIMARY KEY,
    po_number               TEXT NOT NULL UNIQUE,
    supplier_id             INTEGER NOT NULL REFERENCES suppliers(id),
    buyer_id                INTEGER NOT NULL REFERENCES employees(id),
    destination_location_id INTEGER NOT NULL REFERENCES locations(id),
    status                  TEXT NOT NULL,
    currency                CHAR(3) NOT NULL,
    subtotal                NUMERIC(12,2) NOT NULL,
    total                   NUMERIC(12,2) NOT NULL,
    placed_at               TIMESTAMP NOT NULL,
    expected_delivery_at    DATE,
    created_at              TIMESTAMP NOT NULL,
    updated_at              TIMESTAMP NOT NULL
);

CREATE TABLE purchase_order_items (
    id                 INTEGER PRIMARY KEY,
    purchase_order_id  INTEGER NOT NULL REFERENCES purchase_orders(id),
    product_variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    quantity_ordered   INTEGER NOT NULL,
    unit_cost          NUMERIC(12,2) NOT NULL,
    line_total         NUMERIC(12,2) NOT NULL
);

CREATE TABLE goods_receipts (
    id                      INTEGER PRIMARY KEY,
    purchase_order_id       INTEGER NOT NULL REFERENCES purchase_orders(id),
    received_by_employee_id INTEGER NOT NULL REFERENCES employees(id),
    received_at             TIMESTAMP NOT NULL,
    notes                   TEXT,
    created_at              TIMESTAMP NOT NULL
);

CREATE TABLE goods_receipt_items (
    id                     INTEGER PRIMARY KEY,
    goods_receipt_id       INTEGER NOT NULL REFERENCES goods_receipts(id),
    purchase_order_item_id INTEGER NOT NULL REFERENCES purchase_order_items(id),
    quantity_received      NUMERIC(12,3) NOT NULL
);

CREATE TABLE returns (
    id                      INTEGER PRIMARY KEY,
    return_number           TEXT NOT NULL UNIQUE,
    order_id                INTEGER NOT NULL REFERENCES orders(id),
    customer_id             INTEGER NOT NULL REFERENCES customers(id),
    received_at_location_id INTEGER NOT NULL REFERENCES locations(id),
    status                  TEXT NOT NULL,
    reason                  TEXT,
    total_refund_amount     NUMERIC(12,2) NOT NULL,
    created_at              TIMESTAMP NOT NULL,
    updated_at              TIMESTAMP NOT NULL
);

CREATE TABLE return_items (
    id                  INTEGER PRIMARY KEY,
    return_id           INTEGER NOT NULL REFERENCES returns(id),
    order_item_id       INTEGER NOT NULL REFERENCES order_items(id),
    quantity            NUMERIC(12,3) NOT NULL,
    action              TEXT NOT NULL,
    exchange_variant_id INTEGER REFERENCES product_variants(id),
    unit_refund_amount  NUMERIC(12,2) NOT NULL
);

CREATE TABLE stock_levels (
    product_variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    location_id        INTEGER NOT NULL REFERENCES locations(id),
    quantity_on_hand   NUMERIC(12,3) NOT NULL,
    reorder_point      NUMERIC(12,3),
    updated_at         TIMESTAMP NOT NULL,
    PRIMARY KEY (product_variant_id, location_id)
);

CREATE TABLE stock_movements (
    id                 INTEGER PRIMARY KEY,
    product_variant_id INTEGER NOT NULL REFERENCES product_variants(id),
    location_id        INTEGER NOT NULL REFERENCES locations(id),
    movement_type      TEXT NOT NULL,
    quantity           NUMERIC(12,3) NOT NULL,
    reference_table    TEXT,
    reference_id       INTEGER,
    employee_id        INTEGER REFERENCES employees(id),
    notes              TEXT,
    occurred_at        TIMESTAMP NOT NULL,
    created_at         TIMESTAMP NOT NULL
);

-- -----------------------------------------------------------------------------
-- 3. Índices para Consultas Analíticas
-- -----------------------------------------------------------------------------

CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
CREATE INDEX idx_orders_channel_status_date ON orders(channel, status, (created_at::DATE));
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_variant_id ON order_items(product_variant_id);
CREATE INDEX idx_product_variants_product_id ON product_variants(product_id);
CREATE INDEX idx_products_category_id ON products(category_id);

-- -----------------------------------------------------------------------------
-- 4. Views Canônicas (Fonte Única da Verdade)
-- -----------------------------------------------------------------------------
-- Regra de Negócio Central:
-- Pedidos com status 'cancelled' (cancelados) ou 'draft' (rascunho não efetivado)
-- não representam receita ou demanda realizada e são excluídos das métricas
-- comerciais, rankings de clientes, séries temporais e matriz de recomendação.
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW vw_valid_orders AS
SELECT
    id,
    order_number,
    channel,
    customer_id,
    salesperson_id,
    location_id,
    status,
    subtotal,
    discount_amount,
    total,
    placed_at,
    created_at,
    updated_at
FROM orders
WHERE status IN ('paid', 'confirmed');

CREATE OR REPLACE VIEW vw_valid_order_items AS
SELECT
    oi.id AS order_item_id,
    o.id AS order_id,
    o.customer_id,
    o.channel,
    o.status,
    o.created_at,
    oi.product_variant_id,
    pv.product_id,
    p.name AS product_name,
    p.category_id,
    c.name AS category_name,
    oi.quantity,
    oi.unit_price,
    oi.line_total
FROM vw_valid_orders o
JOIN order_items oi      ON oi.order_id = o.id
JOIN product_variants pv ON pv.id = oi.product_variant_id
JOIN products p          ON p.id = pv.product_id
JOIN categories c        ON c.id = p.category_id;

