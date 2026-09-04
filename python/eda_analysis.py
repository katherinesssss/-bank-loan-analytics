"""
Разведочный анализ данных (EDA) по кредитному портфелю банка.

Отвечает на бизнес-вопросы:
  1. Как менялся объём выдачи кредитов во времени?
  2. Какая структура портфеля по типам кредитов?
  3. Где выше уровень просрочки (NPL) — по типу кредита и сегменту клиента?
  4. Как выглядит когортный анализ "выдача -> просрочка" по месяцам?
  5. Есть ли связь между процентной ставкой и риском дефолта?

Результат: графики в /images и сводные таблицы в консоли.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams["figure.dpi"] = 110
plt.rcParams["font.size"] = 10

DATA_DIR = "../data"
IMG_DIR = "../images"

customers = pd.read_csv(f"{DATA_DIR}/customers.csv", parse_dates=["birth_date", "registration_date"])
loans = pd.read_csv(f"{DATA_DIR}/loans.csv", parse_dates=["issue_date"])
loan_payments = pd.read_csv(f"{DATA_DIR}/loan_payments.csv", parse_dates=["due_date"])
transactions = pd.read_csv(f"{DATA_DIR}/transactions.csv", parse_dates=["transaction_date"])

loans = loans.merge(customers[["customer_id", "segment", "city"]], on="customer_id", how="left")

# ---------------------------------------------------------------
# 1. Динамика выдачи кредитов по месяцам
# ---------------------------------------------------------------
monthly = (
    loans.assign(month=loans["issue_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("month")["amount"]
    .sum()
)

fig, ax = plt.subplots(figsize=(9, 4))
monthly.plot(ax=ax, marker="o", linewidth=1.5)
ax.set_title("Динамика выдачи кредитов по месяцам")
ax.set_ylabel("Сумма выдачи, руб.")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e6:.0f} млн"))
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/01_monthly_issuance.png")
plt.close()

# ---------------------------------------------------------------
# 2. Структура портфеля по типам кредитов
# ---------------------------------------------------------------
by_type = loans.groupby("loan_type")["amount"].agg(["count", "sum"]).sort_values("sum", ascending=False)
print("\n=== Портфель по типам кредитов ===")
print(by_type)

fig, ax = plt.subplots(figsize=(6, 6))
ax.pie(
    by_type["sum"],
    labels=by_type.index,
    autopct="%1.0f%%",
    startangle=90,
    wedgeprops={"edgecolor": "white"},
)
ax.set_title("Доля типов кредитов в общем объёме выдачи")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/02_loan_type_share.png")
plt.close()

# ---------------------------------------------------------------
# 3. NPL (просрочка) по типу кредита и сегменту клиента
# ---------------------------------------------------------------
loans["is_npl"] = loans["status"].isin(["Просрочен", "Дефолт"])

npl_by_type = loans.groupby("loan_type")["is_npl"].mean().sort_values(ascending=False) * 100
npl_by_segment = loans.groupby("segment")["is_npl"].mean().sort_values(ascending=False) * 100

print("\n=== NPL rate (%) по типу кредита ===")
print(npl_by_type.round(1))
print("\n=== NPL rate (%) по сегменту клиента ===")
print(npl_by_segment.round(1))

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
npl_by_type.plot(kind="bar", ax=axes[0], color="#c0392b")
axes[0].set_title("NPL rate по типу кредита")
axes[0].set_ylabel("%")
axes[0].tick_params(axis="x", rotation=30)

npl_by_segment.plot(kind="bar", ax=axes[1], color="#2980b9")
axes[1].set_title("NPL rate по сегменту клиента")
axes[1].set_ylabel("%")
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/03_npl_breakdown.png")
plt.close()

# ---------------------------------------------------------------
# 4. Когортный анализ: выдача -> итоговый NPL по месяцу выдачи
# ---------------------------------------------------------------
cohort = (
    loans.assign(cohort_month=loans["issue_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("cohort_month")
    .agg(loans_issued=("loan_id", "count"), npl_loans=("is_npl", "sum"))
)
cohort["npl_rate_pct"] = (cohort["npl_loans"] / cohort["loans_issued"] * 100).round(1)

fig, ax = plt.subplots(figsize=(9, 4))
cohort["npl_rate_pct"].plot(ax=ax, marker="o", color="#8e44ad")
ax.set_title("NPL rate по когортам месяца выдачи кредита")
ax.set_ylabel("NPL rate, %")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/04_npl_by_cohort.png")
plt.close()

# ---------------------------------------------------------------
# 5. Связь ставки и риска дефолта
# ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7, 5))
colors = loans["is_npl"].map({True: "#e74c3c", False: "#27ae60"})
ax.scatter(loans["interest_rate"], loans["amount"], c=colors, alpha=0.4, s=15)
ax.set_xlabel("Процентная ставка, %")
ax.set_ylabel("Сумма кредита, руб.")
ax.set_title("Ставка vs сумма кредита (красный = просрочка/дефолт)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x/1e6:.1f} млн"))
plt.tight_layout()
plt.savefig(f"{IMG_DIR}/05_rate_vs_amount_risk.png")
plt.close()

print("\nГрафики сохранены в", IMG_DIR)
