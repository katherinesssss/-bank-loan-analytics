-- =========================================================
-- Bank Loan & Transaction Analytics — аналитические запросы
-- =========================================================
-- Каждый блок отвечает на конкретный бизнес-вопрос.
-- Специально включены оконные функции (RANK, SUM OVER, LAG,
-- NTILE) — как отдельная тренировка этой темы.


-- -----------------------------------------------------------
-- 1. Динамика выдачи кредитов по месяцам и типам
-- -----------------------------------------------------------
SELECT
    DATE_TRUNC('month', issue_date)::date AS month,
    loan_type,
    COUNT(*)                              AS loans_issued,
    SUM(amount)                           AS total_amount
FROM loans
GROUP BY 1, 2
ORDER BY 1, 2;


-- -----------------------------------------------------------
-- 2. Running total (нарастающий итог) выдачи кредитов по месяцам
--    — классика на SUM() OVER (ORDER BY ...)
-- -----------------------------------------------------------
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', issue_date)::date AS month,
        SUM(amount)                           AS amount_issued
    FROM loans
    GROUP BY 1
)
SELECT
    month,
    amount_issued,
    SUM(amount_issued) OVER (ORDER BY month)                       AS running_total,
    ROUND(AVG(amount_issued) OVER (
        ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                                            AS moving_avg_3m
FROM monthly
ORDER BY month;


-- -----------------------------------------------------------
-- 3. Изменение объёма выдач месяц к месяцу (MoM, %)
--    — LAG()
-- -----------------------------------------------------------
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', issue_date)::date AS month,
        SUM(amount)                           AS amount_issued
    FROM loans
    GROUP BY 1
)
SELECT
    month,
    amount_issued,
    LAG(amount_issued) OVER (ORDER BY month)                AS prev_month_amount,
    ROUND(
        100.0 * (amount_issued - LAG(amount_issued) OVER (ORDER BY month))
        / NULLIF(LAG(amount_issued) OVER (ORDER BY month), 0), 1
    )                                                         AS mom_growth_pct
FROM monthly
ORDER BY month;


-- -----------------------------------------------------------
-- 4. Топ-10 клиентов по сумме выданных кредитов
--    — RANK() / DENSE_RANK()
-- -----------------------------------------------------------
SELECT
    c.customer_id,
    c.full_name,
    c.segment,
    SUM(l.amount)                                            AS total_loans_amount,
    COUNT(l.loan_id)                                          AS loans_count,
    RANK() OVER (ORDER BY SUM(l.amount) DESC)                 AS rank_by_amount
FROM loans l
JOIN customers c ON c.customer_id = l.customer_id
GROUP BY c.customer_id, c.full_name, c.segment
ORDER BY rank_by_amount
LIMIT 10;


-- -----------------------------------------------------------
-- 5. Ранжирование кредитов внутри каждого клиента по дате выдачи
--    (какой это по счёту кредит у клиента) — ROW_NUMBER() + PARTITION BY
-- -----------------------------------------------------------
SELECT
    customer_id,
    loan_id,
    issue_date,
    loan_type,
    amount,
    ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY issue_date) AS loan_seq_number
FROM loans
ORDER BY customer_id, loan_seq_number;


-- -----------------------------------------------------------
-- 6. Просрочка (NPL) по когортам месяца выдачи
--    Доля кредитов, ушедших в статус "Просрочен"/"Дефолт",
--    среди всех выданных в этом месяце
-- -----------------------------------------------------------
SELECT
    DATE_TRUNC('month', issue_date)::date                      AS cohort_month,
    COUNT(*)                                                    AS loans_issued,
    COUNT(*) FILTER (WHERE status IN ('Просрочен', 'Дефолт'))   AS npl_loans,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status IN ('Просрочен', 'Дефолт'))
        / COUNT(*), 1
    )                                                             AS npl_rate_pct
FROM loans
GROUP BY 1
ORDER BY 1;


-- -----------------------------------------------------------
-- 7. Просроченные платежи по типам кредитов
-- -----------------------------------------------------------
SELECT
    l.loan_type,
    COUNT(*)                                                       AS total_payments,
    COUNT(*) FILTER (WHERE p.payment_status <> 'Оплачен вовремя')  AS late_or_missed,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE p.payment_status <> 'Оплачен вовремя')
        / COUNT(*), 1
    )                                                                AS late_rate_pct
FROM loan_payments p
JOIN loans l ON l.loan_id = p.loan_id
GROUP BY l.loan_type
ORDER BY late_rate_pct DESC;


-- -----------------------------------------------------------
-- 8. Сегментация клиентов по сумме кредитов на квартили — NTILE()
-- -----------------------------------------------------------
WITH totals AS (
    SELECT
        c.customer_id,
        c.full_name,
        SUM(l.amount) AS total_amount
    FROM loans l
    JOIN customers c ON c.customer_id = l.customer_id
    GROUP BY c.customer_id, c.full_name
)
SELECT
    customer_id,
    full_name,
    total_amount,
    NTILE(4) OVER (ORDER BY total_amount DESC) AS quartile   -- 1 = топ-25% клиентов
FROM totals
ORDER BY total_amount DESC;


-- -----------------------------------------------------------
-- 9. Повторные клиенты (взяли более одного кредита) — доля от всех
-- -----------------------------------------------------------
WITH loans_per_customer AS (
    SELECT customer_id, COUNT(*) AS loans_count
    FROM loans
    GROUP BY customer_id
)
SELECT
    COUNT(*) FILTER (WHERE loans_count > 1)                        AS repeat_customers,
    COUNT(*)                                                        AS total_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE loans_count > 1) / COUNT(*), 1) AS repeat_rate_pct
FROM loans_per_customer;


-- -----------------------------------------------------------
-- 10. Активность по счетам: средний чек транзакции по каналам
-- -----------------------------------------------------------
SELECT
    channel,
    transaction_type,
    COUNT(*)                          AS txn_count,
    ROUND(AVG(ABS(amount)), 2)        AS avg_amount,
    ROUND(SUM(amount), 2)             AS net_amount
FROM transactions
GROUP BY channel, transaction_type
ORDER BY channel, txn_count DESC;
