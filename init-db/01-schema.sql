-- 생산 라인
CREATE TABLE production_lines (
    line_id VARCHAR(20) PRIMARY KEY,
    line_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'stopped'
);

-- 제품
CREATE TABLE products (
    product_id VARCHAR(20) PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    unit_price INTEGER
);

-- 생산 실적
CREATE TABLE production_records (
    record_id SERIAL PRIMARY KEY,
    line_id VARCHAR(20) REFERENCES production_lines(line_id),
    product_id VARCHAR(20) REFERENCES products(product_id),
    production_date DATE DEFAULT CURRENT_DATE,
    target_qty INTEGER,
    produced_qty INTEGER,
    defect_qty INTEGER DEFAULT 0
);

-- 품질 검사
CREATE TABLE quality_inspections (
    inspection_id SERIAL PRIMARY KEY,
    record_id INTEGER REFERENCES production_records(record_id),
    defect_type VARCHAR(50),
    defect_count INTEGER
);