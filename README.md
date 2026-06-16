
## SAP types
- SAP ECC (ERP Central Component): custom, old, db integration by compny's db 
- SAP S/4HANA: SAP db & cloud, modern, db integration by SAP db(we can make it click integration like google login in regular apps) 

## DB:
1. Database: copilot_db
Execute these queries in your Copilot internal database to handle the AI state and automation engine.

```
-- Table: automation_rules
CREATE TABLE automation_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    target_table VARCHAR(255) NOT NULL,
    condition_column VARCHAR(255) NOT NULL,
    condition_threshold NUMERIC NOT NULL,
    action_intent VARCHAR(255) NOT NULL,
    action_payload JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Table: chat_history
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    user_prompt TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    executed_action VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
2. Database: sap_mock_db
Execute these queries in your SAP simulation database. The foreign keys are set up to map relationships accurately.

```
-- Module: SAP MM (Materials Management)

CREATE TABLE sap_mm_materials (
    material_id VARCHAR(50) PRIMARY KEY,
    description VARCHAR(255) NOT NULL,
    stock_qty INTEGER NOT NULL DEFAULT 0,
    minimum_stock INTEGER NOT NULL,
    unit_price NUMERIC NOT NULL
);

CREATE TABLE sap_mm_purchase_requisitions (
    pr_id VARCHAR(50) PRIMARY KEY,
    material_id VARCHAR(50) REFERENCES sap_mm_materials(material_id),
    requested_qty INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    created_date DATE DEFAULT CURRENT_DATE
);

-- Module: SAP PP (Production Planning)

CREATE TABLE sap_pp_production_runs (
    run_id VARCHAR(50) PRIMARY KEY,
    line_id VARCHAR(50) NOT NULL,
    target_output INTEGER NOT NULL,
    actual_output INTEGER NOT NULL,
    defect_qty INTEGER NOT NULL DEFAULT 0,
    run_date DATE NOT NULL
);

-- Module: SAP PM (Plant Maintenance)

CREATE TABLE sap_pm_downtime_logs (
    log_id VARCHAR(50) PRIMARY KEY,
    line_id VARCHAR(50) NOT NULL,
    downtime_minutes INTEGER NOT NULL,
    fault_category VARCHAR(100) NOT NULL,
    root_cause_desc TEXT NOT NULL,
    incident_date DATE NOT NULL
);

CREATE TABLE sap_pm_work_orders (
    wo_id VARCHAR(50) PRIMARY KEY,
    log_id VARCHAR(50) REFERENCES sap_pm_downtime_logs(log_id),
    status VARCHAR(50) NOT NULL,
    repair_cost NUMERIC NOT NULL
);

-- Module: SAP FICO (Finance & Controlling)

CREATE TABLE sap_fico_cost_centers (
    cost_center_id VARCHAR(50) PRIMARY KEY,
    department_name VARCHAR(255) NOT NULL,
    annual_budget NUMERIC NOT NULL,
    spent_budget NUMERIC NOT NULL DEFAULT 0.0
);
```
## dockerfile:
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: copilot_admin
      POSTGRES_PASSWORD: hackathon_password
      # We will use a script to initialize our two DBs
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db

  frontend:
    build: ./frontend
    command: npm run dev -- --host 0.0.0.0
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  pgdata:
