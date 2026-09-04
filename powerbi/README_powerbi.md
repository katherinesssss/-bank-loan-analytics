# Дашборд в Power BI

## Файлы для импорта

- `loans_flat_for_powerbi.csv` — уже объединённые кредиты + клиенты (звезда не нужна, можно тащить в один Power Query)
- Либо используй исходные `../data/*.csv` напрямую и построй классическую звёздную схему:
  - `loans` (факты) — связь по `customer_id` с `customers` (измерение)
  - `loan_payments` (факты) — связь по `loan_id` с `loans`
  - `transactions` (факты) — связь по `account_id` с `accounts`, `accounts` связаны с `customers`

## Шаги сборки

1. **Get Data → Text/CSV**, загрузить `loans_flat_for_powerbi.csv`.
2. В Power Query: сменить тип `issue_date`, `birth_date`, `registration_date` на Date;
   `amount`, `interest_rate`, `risk_score` — на Decimal Number.
3. Создать вычисляемый столбец `is_npl`:
   ```
   is_npl = IF(loans[status] IN {"Просрочен", "Дефолт"}, 1, 0)
   ```
4. Создать отдельную таблицу дат (Modeling → New Table):
   ```
   DimDate = CALENDAR(MIN(loans[issue_date]), MAX(loans[issue_date]))
   ```
   и связать с `loans[issue_date]`.

## Ключевые DAX-меры

```
Total Loans Amount = SUM(loans[amount])

Loans Count = COUNTROWS(loans)

NPL Rate % =
DIVIDE(
    CALCULATE(COUNTROWS(loans), loans[is_npl] = 1),
    COUNTROWS(loans)
)

Avg Loan Amount = AVERAGE(loans[amount])

MoM Growth % =
VAR CurrMonth = [Total Loans Amount]
VAR PrevMonth = CALCULATE([Total Loans Amount], DATEADD(DimDate[Date], -1, MONTH))
RETURN DIVIDE(CurrMonth - PrevMonth, PrevMonth)

Repeat Customers % =
VAR CustomersWithLoans = DISTINCTCOUNT(loans[customer_id])
VAR RepeatCustomers =
    CALCULATE(
        DISTINCTCOUNT(loans[customer_id]),
        FILTER(
            VALUES(loans[customer_id]),
            CALCULATE(COUNTROWS(loans)) > 1
        )
    )
RETURN DIVIDE(RepeatCustomers, CustomersWithLoans)
```

## Структура дашборда (1 страница)

- **KPI-карточки сверху:** Total Loans Amount, Loans Count, NPL Rate %, Avg Loan Amount
- **Линейный график:** динамика выдачи по месяцам (issue_date по оси X) + MoM Growth % как вторая ось
- **Столбчатая диаграмма:** NPL Rate % по loan_type
- **Пончиковая диаграмма:** доля объёма выдачи по loan_type
- **Матрица/таблица:** сегмент клиента × тип кредита, значение — Total Loans Amount, с условным форматированием по NPL Rate %
- **Карта (Filled Map):** объём выдачи по городам (`city`)
- **Срезы (slicers):** период (issue_date), сегмент клиента, тип кредита, статус кредита


