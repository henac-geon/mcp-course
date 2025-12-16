-- 라인 3개
INSERT INTO production_lines VALUES
('LINE-01', '조립라인 1', 'running'),
('LINE-02', '조립라인 2', 'running'),
('LINE-03', '포장라인 1', 'maintenance');

-- 제품 2개
INSERT INTO products VALUES
('PROD-A', '스마트 센서', 25000),
('PROD-B', '컨트롤러', 80000);

-- 실적 4개
INSERT INTO production_records (line_id, product_id, production_date, target_qty, produced_qty, defect_qty) VALUES
('LINE-01', 'PROD-A', CURRENT_DATE, 800, 780, 12),
('LINE-02', 'PROD-B', CURRENT_DATE, 400, 385, 8),
('LINE-01', 'PROD-A', CURRENT_DATE - 1, 800, 790, 10),
('LINE-02', 'PROD-B', CURRENT_DATE - 1, 400, 395, 5);

-- 품질 검사 3개
INSERT INTO quality_inspections (record_id, defect_type, defect_count) VALUES
(1, '외관불량', 7),
(1, '치수불량', 5),
(2, '기능불량', 8);