-- ============================================================
--  BizPulse — Supabase Schema
--  Run this entire script in Supabase SQL Editor once
--  Project: https://xhqjfnmjxctnzjmasjnh.supabase.co
-- ============================================================

-- ── USERS ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id                   TEXT PRIMARY KEY,
    business_id               TEXT NOT NULL,
    business_name             TEXT NOT NULL,
    full_name                 TEXT NOT NULL,
    email                     TEXT UNIQUE NOT NULL,
    password_hash             TEXT NOT NULL,
    role                      TEXT NOT NULL DEFAULT 'owner',
    plan_type                 TEXT NOT NULL DEFAULT 'trial',
    plan_status               TEXT NOT NULL DEFAULT 'active',
    subscription_start        DATE,
    subscription_end          DATE,
    created_at                TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    password_reset_requested  TEXT NOT NULL DEFAULT 'no',
    reset_requested_at        TIMESTAMP WITH TIME ZONE,
    must_change_password      TEXT NOT NULL DEFAULT 'no'
);

CREATE INDEX IF NOT EXISTS idx_users_email       ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_business_id ON users(business_id);
CREATE INDEX IF NOT EXISTS idx_users_plan_status ON users(plan_status);

-- ── PRODUCTS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id      TEXT PRIMARY KEY,
    business_id     TEXT NOT NULL,
    product_name    TEXT NOT NULL,
    category        TEXT,
    selling_price   NUMERIC(12, 2) NOT NULL DEFAULT 0,
    cost_price      NUMERIC(12, 2) NOT NULL DEFAULT 0,
    stock_quantity  INTEGER NOT NULL DEFAULT 0,
    reorder_level   INTEGER NOT NULL DEFAULT 5,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_business_id ON products(business_id);

-- ── SALES ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales (
    sale_id         TEXT PRIMARY KEY,
    business_id     TEXT NOT NULL,
    product_id      TEXT NOT NULL,
    product_name    TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    unit_price      NUMERIC(12, 2) NOT NULL,
    total_amount    NUMERIC(12, 2) NOT NULL,
    cost_total      NUMERIC(12, 2) NOT NULL,
    gross_profit    NUMERIC(12, 2) NOT NULL,
    payment_method  TEXT NOT NULL DEFAULT 'Cash',
    sale_date       TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recorded_by     TEXT
);

CREATE INDEX IF NOT EXISTS idx_sales_business_id ON sales(business_id);
CREATE INDEX IF NOT EXISTS idx_sales_sale_date   ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_product_id  ON sales(product_id);

-- ── EXPENSES ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenses (
    expense_id      TEXT PRIMARY KEY,
    business_id     TEXT NOT NULL,
    category        TEXT NOT NULL,
    description     TEXT,
    amount          NUMERIC(12, 2) NOT NULL,
    expense_date    DATE NOT NULL,
    recorded_by     TEXT
);

CREATE INDEX IF NOT EXISTS idx_expenses_business_id  ON expenses(business_id);
CREATE INDEX IF NOT EXISTS idx_expenses_expense_date ON expenses(expense_date);

-- ── PAYMENTS (platform subscription ledger) ────────────────
CREATE TABLE IF NOT EXISTS payments (
    payment_id      TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    business_name   TEXT,
    email           TEXT,
    plan_type       TEXT,
    amount          NUMERIC(12, 2) NOT NULL,
    payment_date    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    note            TEXT
);

CREATE INDEX IF NOT EXISTS idx_payments_user_id      ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments(payment_date);

-- ── ROW LEVEL SECURITY ─────────────────────────────────────
-- Disable RLS — app uses service_role key which bypasses it anyway.
-- Enable RLS later if you add user-level Supabase Auth.
ALTER TABLE users     DISABLE ROW LEVEL SECURITY;
ALTER TABLE products  DISABLE ROW LEVEL SECURITY;
ALTER TABLE sales     DISABLE ROW LEVEL SECURITY;
ALTER TABLE expenses  DISABLE ROW LEVEL SECURITY;
ALTER TABLE payments  DISABLE ROW LEVEL SECURITY;

-- Done! All 5 tables created with indexes.
