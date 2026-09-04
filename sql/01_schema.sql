-- =========================================================
-- Bank Loan & Transaction Analytics — схема БД (PostgreSQL)
-- =========================================================

DROP TABLE IF EXISTS loan_payments CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS loans CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id        INT PRIMARY KEY,
    full_name           VARCHAR(150) NOT NULL,
    gender              CHAR(1),
    birth_date          DATE,
    city                VARCHAR(100),
    segment             VARCHAR(20),   -- Retail / Premium / Business
    registration_date   DATE NOT NULL
);

CREATE TABLE accounts (
    account_id      INT PRIMARY KEY,
    customer_id     INT NOT NULL REFERENCES customers(customer_id),
    account_type    VARCHAR(30),   -- Текущий / Сберегательный
    currency        VARCHAR(3),
    open_date       DATE NOT NULL,
    status          VARCHAR(20)    -- Активен / Закрыт
);

CREATE TABLE loans (
    loan_id         INT PRIMARY KEY,
    customer_id     INT NOT NULL REFERENCES customers(customer_id),
    loan_type       VARCHAR(30),   -- Потребительский / Ипотека / Автокредит / Вексель / Кредитная карта
    amount          NUMERIC(14,2) NOT NULL,
    interest_rate   NUMERIC(5,2),
    term_months     INT,
    issue_date      DATE NOT NULL,
    branch          VARCHAR(50),
    status          VARCHAR(20),   -- Активен / Закрыт / Просрочен / Дефолт
    risk_score      NUMERIC(5,3)
);

CREATE TABLE loan_payments (
    payment_id      INT PRIMARY KEY,
    loan_id         INT NOT NULL REFERENCES loans(loan_id),
    due_date        DATE NOT NULL,
    amount_due      NUMERIC(14,2),
    amount_paid     NUMERIC(14,2),
    payment_status  VARCHAR(20)    -- Оплачен вовремя / Просрочен / Не оплачен
);

CREATE TABLE transactions (
    transaction_id      BIGINT PRIMARY KEY,
    account_id           INT NOT NULL REFERENCES accounts(account_id),
    transaction_date     DATE NOT NULL,
    transaction_type     VARCHAR(30),
    amount               NUMERIC(14,2),
    channel               VARCHAR(30)
);

-- Индексы под типичные аналитические запросы
CREATE INDEX idx_loans_customer   ON loans(customer_id);
CREATE INDEX idx_loans_issue_date ON loans(issue_date);
CREATE INDEX idx_payments_loan    ON loan_payments(loan_id);
CREATE INDEX idx_txn_account      ON transactions(account_id);
CREATE INDEX idx_txn_date         ON transactions(transaction_date);

-- Загрузка данных (пример для psql):
-- \copy customers      FROM 'data/customers.csv'      DELIMITER ',' CSV HEADER;
-- \copy accounts        FROM 'data/accounts.csv'        DELIMITER ',' CSV HEADER;
-- \copy loans           FROM 'data/loans.csv'           DELIMITER ',' CSV HEADER;
-- \copy loan_payments   FROM 'data/loan_payments.csv'   DELIMITER ',' CSV HEADER;
-- \copy transactions    FROM 'data/transactions.csv'    DELIMITER ',' CSV HEADER;
