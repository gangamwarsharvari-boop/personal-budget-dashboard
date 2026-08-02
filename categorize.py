import pandas as pd

CATEGORY_RULES = {
    "Housing": ["rent", "apartments", "mortgage"],
    "Utilities": ["comcast", "xfinity", "pg&e", "electric", "verizon"],
    "Subscriptions": ["netflix", "spotify", "amazon prime", "nytimes"],
    "Insurance": ["geico", "insurance"],
    "Debt Payments": ["credit card payment", "student loan"],
    "Groceries": ["trader joe", "safeway", "whole foods"],
    "Dining Out": ["chipotle", "starbucks", "sushi", "doordash", "pizza", "cheesecake factory"],
    "Transportation": ["shell", "chevron", "uber", "lyft", "transit"],
    "Shopping": ["target", "amazon.com", "best buy", "h&m", "rei"],
    "Health & Fitness": ["cvs", "walgreens", "kaiser", "planet fitness"],
    "Entertainment": ["amc", "steam", "ticketmaster", "bar & grill"],
    "Travel": ["southwest", "airlines", "airbnb", "marriott"],
    "Pets": ["petsmart"],
    "Cash & Misc": ["atm withdrawal", "venmo"],
    "Income": ["payroll", "direct dep", "freelance"],
    # add whatever else you found in Step 4
}

def categorize(description):
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if any(kw in desc for kw in keywords):
            return category
    return "Uncategorized"

def load_and_process(csv_path):
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Amount"] = df["Amount"].astype(float)
    df["Category"] = df["Description"].apply(categorize)
    df["Type"] = df["Amount"].apply(lambda x: "Income" if x > 0 else "Expense")
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df.sort_values("Date").reset_index(drop=True)

def detect_recurring(df):
    exp = df[df["Amount"] < 0].copy()
    exp["AbsAmount"] = exp["Amount"].abs()
    grouped = exp.groupby("Description").agg(
        occurrences=("Amount", "count"),
        avg_amount=("AbsAmount", "mean"),
        months_seen=("Month", "nunique"),
    ).reset_index()
    recurring = grouped[grouped["months_seen"] >= 3].copy()

    # Add amount consistency check - true subscriptions charge the same amount each time
    recurring_std = exp.groupby("Description")["AbsAmount"].std().reset_index()
    recurring_std.columns = ["Description", "amount_std"]
    recurring = recurring.merge(recurring_std, on="Description")
    recurring["amount_std"] = recurring["amount_std"].fillna(0)  # only 1 std value = no variation

    recurring["est_annual_cost"] = recurring["avg_amount"] * 12
    recurring["is_fixed_subscription"] = recurring["amount_std"] < 5

    return recurring.sort_values("est_annual_cost", ascending=False)