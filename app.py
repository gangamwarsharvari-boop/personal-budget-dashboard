import streamlit as st
import pandas as pd
import plotly.express as px
from categorize import load_and_process, detect_recurring

st.set_page_config(page_title="Personal Budget Dashboard", layout="wide")
st.title("💰 Personal Budget Dashboard")

uploaded = st.file_uploader("Upload transaction CSV", type=["csv"])
csv_path = uploaded if uploaded is not None else "sample_transactions.csv"

df = load_and_process(csv_path)
months = sorted(df["Month"].unique())
sel_months = st.multiselect("Filter by month", months, default=months)
df = df[df["Month"].isin(sel_months)]

income = df.loc[df["Amount"] > 0, "Amount"].sum()
expenses = -df.loc[df["Amount"] < 0, "Amount"].sum()
net = income - expenses
savings_rate = (net / income * 100) if income else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Income", f"${income:,.0f}")
c2.metric("Total Expenses", f"${expenses:,.0f}")
c3.metric("Net Savings", f"${net:,.0f}")
c4.metric("Savings Rate", f"{savings_rate:.1f}%")
st.divider()

left, right = st.columns([1, 1.3])

with left:
    st.subheader("Spending by Category")
    exp_df = df[(df["Amount"] < 0) & (df["Category"] != "Income")].copy()
    exp_df["Amount"] = exp_df["Amount"].abs()
    cat_summary = exp_df.groupby("Category")["Amount"].sum().reset_index().sort_values("Amount", ascending=False)
    fig_pie = px.pie(cat_summary, names="Category", values="Amount", hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

with right:
    st.subheader("Income vs. Expenses by Month")
    monthly = df.groupby(["Month", "Type"])["Amount"].sum().abs().reset_index()
    fig_bar = px.bar(monthly, x="Month", y="Amount", color="Type", barmode="group")
    st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("Monthly Spending Trend by Category")
trend = exp_df.groupby(["Month", "Category"])["Amount"].sum().reset_index()
fig_line = px.line(trend, x="Month", y="Amount", color="Category", markers=True)
st.plotly_chart(fig_line, use_container_width=True)

st.subheader("Detected Recurring Charges")
recurring = detect_recurring(df)

show_only_subscriptions = st.checkbox("Show only fixed subscriptions/bills")
if show_only_subscriptions:
    recurring = recurring[recurring["is_fixed_subscription"]]

st.dataframe(
    recurring[["Description", "occurrences", "avg_amount", "est_annual_cost"]].rename(
        columns={"occurrences": "Times Seen", "avg_amount": "Avg Amount ($)",
                 "est_annual_cost": "Est. Annual Cost ($)"}
    ).round(2),
    use_container_width=True,
)

st.subheader("All Transactions")
st.dataframe(
    df[["Date", "Description", "Amount", "Category", "Type"]].sort_values("Date", ascending=False),
    use_container_width=True,
)
