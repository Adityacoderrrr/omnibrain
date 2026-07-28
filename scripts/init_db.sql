-- Database Initialization Script for OmniBrain PostgreSQL Data Source

CREATE TABLE IF NOT EXISTS sales_records (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    region VARCHAR(50) NOT NULL,
    product VARCHAR(100) NOT NULL,
    revenue NUMERIC(12, 2) NOT NULL,
    units_sold INTEGER NOT NULL,
    margin NUMERIC(5, 4) NOT NULL
);

-- Seed Initial Enterprise Historical Dataset
INSERT INTO sales_records (date, region, product, revenue, units_sold, margin)
VALUES
    ('2026-01-10', 'US', 'Cloud Subscription', 50000.00, 100, 0.8200),
    ('2026-02-15', 'US', 'Professional Services', 100000.00, 50, 0.4500),
    ('2026-03-01', 'EU', 'Cloud Subscription', 40000.00, 80, 0.8000),
    ('2026-04-12', 'APAC', 'Hardware Appliances', 30000.00, 15, 0.3000),
    ('2026-05-20', 'US', 'Enterprise License', 120000.00, 10, 0.8800),
    ('2026-06-18', 'EU', 'Professional Services', 65000.00, 30, 0.5000)
ON CONFLICT (id) DO NOTHING;
