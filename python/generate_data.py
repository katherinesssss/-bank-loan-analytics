"""
Генерация синтетического датасета для pet-проекта
"Bank Loan & Transaction Analytics".

Имитирует данные банка: клиенты, счета, кредиты/векселя (в т.ч.
модуль выдачи векселей, аналогичный проекту T1/VTB), платежи по
кредитам и транзакции по счетам.

Данные полностью синтетические, сгенерированы с помощью Faker.
"""

import random
from datetime import date, timedelta

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker("ru_RU")
Faker.seed(42)
random.seed(42)
np.random.seed(42)

N_CUSTOMERS = 800
N_ACCOUNTS = 1000
N_LOANS = 1500
START_DATE = date(2022, 1, 1)
END_DATE = date(2025, 12, 31)

SEGMENTS = ["Retail", "Premium", "Business"]
SEGMENT_WEIGHTS = [0.65, 0.20, 0.15]

CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
    "Казань", "Нижний Новгород", "Челябинск", "Самара", "Уфа", "Ростов-на-Дону",
]

LOAN_TYPES = ["Потребительский", "Ипотека", "Автокредит", "Вексель", "Кредитная карта"]
LOAN_TYPE_WEIGHTS = [0.35, 0.15, 0.15, 0.20, 0.15]

LOAN_AMOUNT_RANGES = {
    "Потребительский": (50_000, 800_000),
    "Ипотека": (2_000_000, 12_000_000),
    "Автокредит": (400_000, 3_000_000),
    "Вексель": (100_000, 5_000_000),
    "Кредитная карта": (30_000, 300_000),
}

LOAN_TERM_MONTHS = {
    "Потребительский": [12, 24, 36, 48],
    "Ипотека": [120, 180, 240, 300],
    "Автокредит": [24, 36, 48, 60],
    "Вексель": [3, 6, 9, 12],
    "Кредитная карта": [12, 24, 36],
}

BRANCHES = [f"Отделение №{i}" for i in range(1, 16)]
CHANNELS = ["Онлайн", "Отделение", "Банкомат", "Колл-центр"]
TXN_TYPES = ["Пополнение", "Списание", "Перевод", "Оплата услуг", "Погашение кредита"]


def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 0)))


def gen_customers(n: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        gender = random.choice(["M", "F"])
        full_name = fake.name_male() if gender == "M" else fake.name_female()
        birth_date = fake.date_of_birth(minimum_age=19, maximum_age=70)
        reg_date = random_date(START_DATE, END_DATE)
        segment = random.choices(SEGMENTS, weights=SEGMENT_WEIGHTS)[0]
        rows.append({
            "customer_id": i,
            "full_name": full_name,
            "gender": gender,
            "birth_date": birth_date,
            "city": random.choice(CITIES),
            "segment": segment,
            "registration_date": reg_date,
        })
    return pd.DataFrame(rows)


def gen_accounts(n: int, customers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        cust = customers.sample(1).iloc[0]
        open_date = max(cust["registration_date"], random_date(START_DATE, END_DATE))
        status = random.choices(["Активен", "Закрыт"], weights=[0.85, 0.15])[0]
        rows.append({
            "account_id": i,
            "customer_id": cust["customer_id"],
            "account_type": random.choice(["Текущий", "Сберегательный"]),
            "currency": random.choices(["RUB", "USD", "EUR"], weights=[0.9, 0.06, 0.04])[0],
            "open_date": open_date,
            "status": status,
        })
    return pd.DataFrame(rows)


def gen_loans(n: int, customers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        cust = customers.sample(1).iloc[0]
        loan_type = random.choices(LOAN_TYPES, weights=LOAN_TYPE_WEIGHTS)[0]
        lo, hi = LOAN_AMOUNT_RANGES[loan_type]
        amount = round(random.uniform(lo, hi), -3)
        term = random.choice(LOAN_TERM_MONTHS[loan_type])
        issue_date = max(cust["registration_date"], random_date(START_DATE, END_DATE))
        rate = round(random.uniform(6.5, 24.9), 2)

        # Итоговый статус кредита зависит от даты выдачи и "качества" клиента
        risk_score = random.random()
        months_since_issue = (END_DATE.year - issue_date.year) * 12 + (END_DATE.month - issue_date.month)
        if months_since_issue >= term:
            status = "Просрочен" if risk_score < 0.08 else "Закрыт"
        else:
            if risk_score < 0.06:
                status = "Просрочен"
            elif risk_score < 0.10:
                status = "Дефолт"
            else:
                status = "Активен"

        rows.append({
            "loan_id": i,
            "customer_id": cust["customer_id"],
            "loan_type": loan_type,
            "amount": amount,
            "interest_rate": rate,
            "term_months": term,
            "issue_date": issue_date,
            "branch": random.choice(BRANCHES),
            "status": status,
            "risk_score": round(risk_score, 3),
        })
    return pd.DataFrame(rows)


def gen_loan_payments(loans: pd.DataFrame) -> pd.DataFrame:
    rows = []
    payment_id = 1
    for _, loan in loans.iterrows():
        monthly_payment = round(loan["amount"] / loan["term_months"] * (1 + loan["interest_rate"] / 100 / 12), 2)
        n_payments_made = min(
            loan["term_months"],
            (END_DATE.year - loan["issue_date"].year) * 12 + (END_DATE.month - loan["issue_date"].month),
        )
        for m in range(1, max(n_payments_made, 0) + 1):
            due_date = loan["issue_date"] + timedelta(days=30 * m)
            if due_date > END_DATE:
                break
            r = random.random()
            if loan["status"] in ("Просрочен", "Дефолт") and r < 0.35:
                pay_status = "Просрочен" if r > 0.12 else "Не оплачен"
                paid_amount = 0 if pay_status == "Не оплачен" else monthly_payment
            else:
                pay_status = "Оплачен вовремя"
                paid_amount = monthly_payment
            rows.append({
                "payment_id": payment_id,
                "loan_id": loan["loan_id"],
                "due_date": due_date,
                "amount_due": monthly_payment,
                "amount_paid": paid_amount,
                "payment_status": pay_status,
            })
            payment_id += 1
    return pd.DataFrame(rows)


def gen_transactions(n: int, accounts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        acc = accounts.sample(1).iloc[0]
        txn_date = random_date(max(acc["open_date"], START_DATE), END_DATE)
        txn_type = random.choice(TXN_TYPES)
        amount = round(random.uniform(200, 150_000), 2)
        if txn_type in ("Списание", "Перевод", "Оплата услуг", "Погашение кредита"):
            amount = -amount
        rows.append({
            "transaction_id": i,
            "account_id": acc["account_id"],
            "transaction_date": txn_date,
            "transaction_type": txn_type,
            "amount": amount,
            "channel": random.choice(CHANNELS),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    customers = gen_customers(N_CUSTOMERS)
    accounts = gen_accounts(N_ACCOUNTS, customers)
    loans = gen_loans(N_LOANS, customers)
    loan_payments = gen_loan_payments(loans)
    transactions = gen_transactions(20_000, accounts)

    customers.to_csv("../data/customers.csv", index=False)
    accounts.to_csv("../data/accounts.csv", index=False)
    loans.to_csv("../data/loans.csv", index=False)
    loan_payments.to_csv("../data/loan_payments.csv", index=False)
    transactions.to_csv("../data/transactions.csv", index=False)

    print("Готово! Сгенерированы файлы:")
    print(f"  customers.csv      — {len(customers)} строк")
    print(f"  accounts.csv       — {len(accounts)} строк")
    print(f"  loans.csv          — {len(loans)} строк")
    print(f"  loan_payments.csv  — {len(loan_payments)} строк")
    print(f"  transactions.csv   — {len(transactions)} строк")
