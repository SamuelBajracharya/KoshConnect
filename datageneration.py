import random
from datetime import datetime, timedelta
import uuid
import io
import time

# --- 1. DEFINE PERSONAS ---
# This is the "brain" of the generator. You can add new personas here.

PERSONA_DEFINITIONS = {
    "BIKESH_KTM_STUDENT": {
        "user": {
            "id": "a1b2c3d4-e5f6-7788-9900-aabbccddeeff",
            "email": "bikesh.maharjan@student.example.com",
            "name": "Bikesh Maharjan",
        },
        "accounts": [
            {
                "id": "b2a1c3d4-e5f6-7788-9900-aabbccddeeff",
                "bank": "Nabil Bank",
                "mask": "**** 1234",
                "type": "Student Savings (Allowance)",
                "balance": 15000,
            },
            {
                "id": "c3d4e5f6-a1b2-7788-9900-aabbccddeeff",
                "bank": "eSewa Bank",
                "mask": "**** 5678",
                "type": "Freelancer (Gig Money)",
                "balance": 10000,
            },
        ],
        "stock_holdings": [
            ("AAPL", "Apple Inc.", 2.750000, 205.50, 228.90, "USD"),
            ("MSFT", "Microsoft Corporation", 1.400000, 390.20, 436.10, "USD"),
            ("NVDA", "NVIDIA Corporation", 0.850000, 810.00, 965.20, "USD"),
        ],
        "income": [
            # (day_of_month, account_id_key, merchant, desc, amount_range)
            (1, "accounts.0.id", "Family", "Monthly Allowance", (15000, 15000)),
            (
                10,
                "accounts.1.id",
                "Freelance Client",
                "Graphic Design Gig",
                (5000, 10000),
            ),
        ],
        "regular_daily": [
            (
                0.95,
                "accounts.0.id",
                "Food",
                "College Canteen",
                "Daily Khaja",
                (180, 250),
            ),
            (
                0.9,
                "accounts.0.id",
                "Transport",
                "Ride-Hailing",
                "Pathao to College",
                (90, 130),
            ),
            (
                0.9,
                "accounts.0.id",
                "Transport",
                "Ride-Hailing",
                "inDrive Home",
                (80, 120),
            ),
        ],
        "regular_monthly": [
            # (day_of_month, account_id_key, category, merchant, desc, amount_range)
        ],
        "occasional_probabilistic": [
            (
                0.1,
                "accounts.1.id",
                "Food",
                "Local Cafe",
                "Coffee with Friends",
                (300, 700),
            ),
            (
                0.06,
                "accounts.1.id",
                "Entertainment",
                "Restaurant",
                "Weekend Dinner",
                (1000, 2500),
            ),
            (
                0.03,
                "accounts.1.id",
                "Entertainment",
                "QFX Cinemas",
                "Movie Ticket",
                (500, 700),
            ),
            (
                0.03,
                "accounts.1.id",
                "Shopping",
                "Daraz/Bhatbhateni",
                "Clothes Shopping",
                (2000, 5000),
            ),
            (
                0.1,
                "accounts.0.id",
                "Utilities",
                "Ncell/NTC",
                "Mobile Top-up",
                (200, 500),
            ),
        ],
        "rare_large_date_specific": [
            # (date_str 'YYYY-MM-DD', account_id_key, category, merchant, desc, amount_range, type)
            (
                "2025-04-10",
                "accounts.0.id",
                "Maintenance",
                "Laptop Repair",
                "Laptop Service/Repair",
                (3000, 5000),
                "DEBIT",
            ),
            (
                "2025-06-15",
                "accounts.1.id",
                "Travel",
                "Pokhara Trip",
                "Bus & Hotel (Trip)",
                (10000, 15000),
                "DEBIT",
            ),
            (
                "2025-10-25",
                "accounts.1.id",
                "Shopping",
                "Electronics Store",
                "New Headphones (Want)",
                (8000, 8000),
                "DEBIT",
            ),
        ],
    },
    "ROHAN_SOFTWARE_DEV": {
        "user": {
            "id": "e4a5b6c7-d8e9-40a1-a2c3-d4e5f6a7b8c9",
            "email": "rohan.pradhan@techcompany.com",
            "name": "Rohan Pradhan",
        },
        "accounts": [
            {
                "id": "f1a2b3c4-d5e6-47f8-89a0-b1c2d3e4f5a6",
                "bank": "NIC Asia Bank",
                "mask": "**** 9876",
                "type": "Salary Account",
                "balance": 75000,
            },
            {
                "id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6",
                "bank": "Khalti",
                "mask": "98********",
                "type": "Digital Wallet",
                "balance": 5000,
            },
        ],
        "stock_holdings": [
            ("AAPL", "Apple Inc.", 5.000000, 198.00, 228.90, "USD"),
            ("GOOGL", "Alphabet Inc. Class A", 4.500000, 170.40, 186.75, "USD"),
            ("AMZN", "Amazon.com, Inc.", 7.200000, 177.90, 204.35, "USD"),
            ("MSFT", "Microsoft Corporation", 2.800000, 401.80, 436.10, "USD"),
        ],
        "income": [
            # (day_of_month, account_id_key, merchant, desc, amount_range)
            (28, "accounts.0.id", "TechCompany Inc.", "Monthly Salary", (60000, 60000))
        ],
        "regular_daily": [
            (
                0.95,
                "accounts.0.id",
                "Food",
                "Office Canteen",
                "Office Lunch",
                (400, 600),
            ),
            (
                0.7,
                "accounts.1.id",
                "Food",
                "Local Cafe",
                "Evening Snacks/Coffee",
                (300, 500),
            ),
        ],
        "regular_monthly": [
            (1, "accounts.0.id", "Rent", "Landlord", "Monthly Rent", (20000, 20000)),
            (
                2,
                "accounts.0.id",
                "Groceries",
                "Bhatbhateni",
                "Monthly Groceries",
                (3000, 4000),
            ),
            (
                10,
                "accounts.0.id",
                "Utilities",
                "Worldlink",
                "Internet Bill",
                (1500, 1500),
            ),
            (12, "accounts.0.id", "Utilities", "NEA", "Electricity Bill", (500, 1000)),
        ],
        "occasional_probabilistic": [
            (
                0.15,
                "accounts.0.id",
                "Transport",
                "Petrol Pump",
                "Bike Petrol",
                (480, 520),
            ),
            (
                0.1,
                "accounts.0.id",
                "Food",
                "Restaurant",
                "Dinner with Colleagues",
                (1500, 3000),
            ),
            (
                0.06,
                "accounts.0.id",
                "Entertainment",
                "QFX Cinemas",
                "Movie Ticket",
                (500, 700),
            ),
            (
                0.03,
                "accounts.0.id",
                "Shopping",
                "Daraz/Zara",
                "Clothes Shopping",
                (3000, 8000),
            ),
        ],
        "rare_large_date_specific": [
            (
                "2025-01-15",
                "accounts.0.id",
                "Maintenance",
                "Bike Workshop",
                "Bike Servicing",
                (6500, 6500),
                "DEBIT",
            ),
            (
                "2025-04-15",
                "accounts.0.id",
                "Maintenance",
                "Bike Workshop",
                "Bike Servicing",
                (6500, 6500),
                "DEBIT",
            ),
            (
                "2025-07-15",
                "accounts.0.id",
                "Maintenance",
                "Bike Workshop",
                "Bike Servicing",
                (6500, 6500),
                "DEBIT",
            ),
            (
                "2025-10-15",
                "accounts.0.id",
                "Maintenance",
                "Bike Workshop",
                "Bike Servicing",
                (6500, 6500),
                "DEBIT",
            ),
            (
                "2025-03-20",
                "accounts.0.id",
                "Travel",
                "Travel Agency",
                "Trip with Friends (Chitlang)",
                (8000, 12000),
                "DEBIT",
            ),
            (
                "2025-09-10",
                "accounts.0.id",
                "Travel",
                "Travel Agency",
                "Trip with Friends (Mustang)",
                (25000, 40000),
                "DEBIT",
            ),
            (
                "2025-10-20",
                "accounts.0.id",
                "Income",
                "TechCompany Inc.",
                "Dashain Bonus (5%)",
                (3000, 3000),
                "CREDIT",
            ),
        ],
    },
    # --- NEW PERSONA ADDED HERE ---
    "PRIYA_BANK_MANAGER": {
        "user": {
            "id": "d1e2f3a4-b5c6-47d8-a9b0-c1d2e3f4a5b6",
            "email": "priya.shrestha@bank.com",
            "name": "Priya Shrestha",
        },
        "accounts": [
            {
                "id": "a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c7",
                "bank": "NMB Bank",
                "mask": "**** 1122",
                "type": "Salary Account",
                "balance": 80000,
            },
            {
                "id": "b2c3d4e5-f6a7-4b8c-9d0e-f1a2b3c4d5e6",
                "bank": "eSewa",
                "mask": "98********",
                "type": "Digital Wallet",
                "balance": 10000,
            },
        ],
        "stock_holdings": [
            ("TSLA", "Tesla, Inc.", 3.200000, 215.00, 242.40, "USD"),
            ("AAPL", "Apple Inc.", 4.100000, 201.25, 228.90, "USD"),
            ("NVDA", "NVIDIA Corporation", 1.100000, 845.00, 965.20, "USD"),
            ("AMZN", "Amazon.com, Inc.", 3.700000, 182.00, 204.35, "USD"),
        ],
        "income": [
            # (day_of_month, account_id_key, merchant, desc, amount_range)
            (28, "accounts.0.id", "NMB Bank", "Monthly Salary", (70000, 70000))
        ],
        "regular_daily": [
            # (prob_per_day, account_id_key, category, merchant, desc, amount_range)
            # Food (Same as Software Dev)
            (
                0.95,
                "accounts.0.id",
                "Food",
                "Work Canteen",
                "Work Lunch",
                (400, 600),
            ),
            (
                0.7,
                "accounts.1.id",
                "Food",
                "Local Cafe",
                "Evening Snacks/Coffee",
                (300, 500),
            ),
            # Transport (70rs go, 70rs come)
            (
                0.95,
                "accounts.1.id",
                "Transport",
                "Ride-Hailing",
                "Pathao to Office",
                (65, 80),
            ),
            (
                0.95,
                "accounts.1.id",
                "Transport",
                "Ride-Hailing",
                "inDrive Home",
                (65, 80),
            ),
            # Skincare (3+ days a week, expensive)
            (
                0.5,
                "accounts.1.id",
                "Shopping",
                "Skincare/Makeup",
                "Skincare/Makeup Purchase",
                (1000, 3000),
            ),
        ],
        "regular_monthly": [
            # (day_of_month, account_id_key, category, merchant, desc, amount_range)
            # NO RENT
            (
                2,
                "accounts.0.id",
                "Groceries",
                "Bhatbhateni",
                "Monthly Groceries",
                (5000, 7000),
            ),
            (
                10,
                "accounts.0.id",
                "Utilities",
                "Worldlink",
                "Internet Bill",
                (1500, 1500),
            ),
            (12, "accounts.0.id", "Utilities", "NEA", "Electricity Bill", (1000, 1500)),
        ],
        "occasional_probabilistic": [
            # (prob_per_day, account_id_key, category, merchant, desc, amount_range)
            # Outings ~3 times/month
            (
                0.1,
                "accounts.0.id",
                "Food",
                "Restaurant",
                "Dinner/Outing",
                (2000, 4000),
            ),
            # Clothes Shopping ~2 times/month
            (
                0.06,
                "accounts.0.id",
                "Shopping",
                "Zara/Mango",
                "Clothes Shopping",
                (5000, 10000),
            ),
        ],
        "rare_large_date_specific": [
            # (date_str 'YYYY-MM-DD', account_id_key, category, merchant, desc, amount_range, type)
            # Trips
            (
                "2025-03-01",
                "accounts.0.id",
                "Travel",
                "Travel Agency",
                "Trip to Pokhara",
                (15000, 20000),
                "DEBIT",
            ),
            (
                "2025-09-05",
                "accounts.0.id",
                "Travel",
                "Vistara",
                "Trip to Delhi",
                (30000, 40000),
                "DEBIT",
            ),
            # Bonus (8% of 70k = 5600)
            (
                "2025-10-20",
                "accounts.0.id",
                "Income",
                "NMB Bank",
                "Dashain Bonus (8%)",
                (5600, 5600),
                "CREDIT",
            ),
        ],
    },
}

# --- 2. SQL Generation Logic ---


def get_random_time(date_obj):
    """Returns a random datetime object within the given date."""
    return date_obj + timedelta(
        hours=random.randint(7, 22),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )


def write_transaction(
    f, account_id, date, amount, desc, merchant, category, type="DEBIT"
):
    """Helper function to write a single transaction line."""
    date_str = get_random_time(date).isoformat() + "Z"
    amount_str = f"{amount:.2f}"
    # Escape single quotes in descriptions/merchants
    desc_sql = desc.replace("'", "''")
    merchant_sql = merchant.replace("'", "''")
    transaction_id = str(uuid.uuid4())
    f.write(
        f"INSERT INTO transactions (transaction_id, account_id, date, amount, currency, type, status, description, merchant, category) VALUES ('{transaction_id}', '{account_id}', '{date_str}', {amount_str}, 'NPR', '{type}', 'COMPLETED', '{desc_sql}', '{merchant_sql}', '{category}');\n"
    )
    return 1  # Return 1 to count the transaction


def write_stock_instrument(
    f, user_id, symbol, name, quantity, average_buy_price, current_price, currency
):
    symbol_sql = symbol.replace("'", "''")
    name_sql = name.replace("'", "''")
    currency_sql = currency.replace("'", "''")
    stock_id = str(uuid.uuid4())
    f.write(
        "INSERT INTO stock_instruments (id, user_id, symbol, name, quantity, average_buy_price, current_price, currency) "
        f"VALUES ('{stock_id}', '{user_id}', '{symbol_sql}', '{name_sql}', {quantity:.6f}, {average_buy_price:.6f}, {current_price:.6f}, '{currency_sql}');\n"
    )


def generate_sql_for_persona(persona_name, definitions, start_date, end_date):
    """
    Main generation function.
    """
    start_time = time.time()

    if persona_name not in definitions:
        print(f"Error: Persona '{persona_name}' not found in definitions.")
        return

    persona = definitions[persona_name]
    output_file = f"{persona_name.lower()}_transactions_1_year.sql"

    # Use StringIO for high-speed in-memory string building
    f = io.StringIO()

    # --- Write SQL Header ---
    f.write(f"-- Hyper-realistic 1-Year Transaction Data for Persona: {persona_name}\n")
    f.write(f"-- Generated on: {datetime.now().isoformat()}\n")
    f.write("\n")

    f.write("-- 1) CREATE TABLES\n")
    f.write(
        "CREATE TABLE IF NOT EXISTS users (\n    user_id UUID PRIMARY KEY,\n    username VARCHAR NOT NULL UNIQUE,\n    phonenumber VARCHAR NOT NULL UNIQUE,\n    full_name VARCHAR NOT NULL,\n    hashed_password VARCHAR NOT NULL,\n    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()\n);\n\n"
    )
    f.write(
        "CREATE TABLE IF NOT EXISTS accounts (\n    account_id UUID PRIMARY KEY,\n    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,\n    bank_name VARCHAR NOT NULL,\n    account_number_masked VARCHAR NOT NULL,\n    account_type VARCHAR NOT NULL,\n    balance NUMERIC(12,2) NOT NULL\n);\n\n"
    )
    f.write(
        "CREATE TABLE IF NOT EXISTS transactions (\n    transaction_id UUID PRIMARY KEY,\n    account_id UUID NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,\n    date TIMESTAMPTZ NOT NULL,\n    amount NUMERIC(10,2) NOT NULL,\n    currency VARCHAR(3) NOT NULL,\n    type VARCHAR(10) NOT NULL,\n    status VARCHAR(15) NOT NULL,\n    description VARCHAR,\n    merchant VARCHAR,\n    category VARCHAR\n);\n\n"
    )
    f.write(
        "CREATE TABLE IF NOT EXISTS stock_instruments (\n    id UUID PRIMARY KEY,\n    user_id VARCHAR(64) NOT NULL,\n    symbol VARCHAR(20) NOT NULL,\n    name VARCHAR(255),\n    quantity NUMERIC(18,6) NOT NULL DEFAULT 0,\n    average_buy_price NUMERIC(18,6),\n    current_price NUMERIC(18,6),\n    currency VARCHAR(10),\n    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),\n    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),\n    CONSTRAINT uq_stock_instruments_user_id_id UNIQUE (user_id, id),\n    CONSTRAINT uq_stock_instruments_user_id_symbol UNIQUE (user_id, symbol)\n);\n\n"
    )

    f.write(
        "CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);\n"
        "CREATE INDEX IF NOT EXISTS ix_users_phonenumber ON users (phonenumber);\n"
        "CREATE INDEX IF NOT EXISTS ix_stock_instruments_user_id ON stock_instruments (user_id);\n\n"
    )

    f.write("-- 2) Insert persona (user + account)\n")
    user = persona["user"]

    # --- THIS IS THE FIXED LINE ---
    start_timestamp_str = f"{start_date.strftime('%Y-%m-%d')}T10:00:00Z"
    username = user.get("username") or user["email"].split("@")[0]
    if len(username) > 32:
        username = username[:32]

    phone_number_seed = int(uuid.UUID(user["id"]).int % 100000000)
    phonenumber = user.get("phonenumber") or f"98{phone_number_seed:08d}"
    hashed_password = user.get(
        "hashed_password",
        "$2b$12$PsoHAtQzRQeGTzRGFj06ge64vKnjHRcIzmkJgTY3VouoMVTRO5Pyy",
    )

    f.write(
        f"INSERT INTO users (user_id, username, phonenumber, full_name, hashed_password, created_at) VALUES ('{user['id']}', '{username}', '{phonenumber}', '{user['name']}', '{hashed_password}', '{start_timestamp_str}') ON CONFLICT (user_id) DO NOTHING;\n"
    )
    # -----------------------------

    # Helper to resolve account_id from persona keys like "accounts.0.id"
    def get_account_id(key_str):
        keys = key_str.split(".")  # e.g., ['accounts', '0', 'id']
        return persona[keys[0]][int(keys[1])][keys[2]]

    for acc in persona["accounts"]:
        f.write(
            f"INSERT INTO accounts (user_id, account_id, bank_name, account_number_masked, account_type, balance) VALUES ('{user['id']}', '{acc['id']}', '{acc['bank']}', '{acc['mask']}', '{acc['type']}', {acc['balance']:.2f}) ON CONFLICT (account_id) DO NOTHING;\n"
        )

    f.write("\n-- 3) STOCK HOLDINGS\n")
    for symbol, name, quantity, avg_buy, current_price, currency in persona.get(
        "stock_holdings", []
    ):
        write_stock_instrument(
            f,
            user["id"],
            symbol,
            name,
            quantity,
            avg_buy,
            current_price,
            currency,
        )

    f.write("\n-- 4) TRANSACTIONS (1 Year)\n")

    # --- Generate Transaction Loop ---
    current_date = start_date
    day_count = 0
    transaction_count = 0

    # Build fast-lookup dicts for date-based events
    income_days = {day: rules for (day, *rules) in persona["income"]}
    monthly_days = {day: rules for (day, *rules) in persona.get("regular_monthly", {})}
    rare_dates = {date: rules for (date, *rules) in persona["rare_large_date_specific"]}

    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        # 1. RARE & HUGE (Date Specific)
        if date_str in rare_dates:
            acc_key, cat, merch, desc, (min_amt, max_amt), type = rare_dates[date_str]
            amt = random.uniform(min_amt, max_amt)
            transaction_count += write_transaction(
                f,
                get_account_id(acc_key),
                current_date,
                amt,
                desc,
                merch,
                cat,
                type=type,
            )

        # 2. INCOME (Monthly Day Specific)
        if current_date.day in income_days:
            acc_key, merch, desc, (min_amt, max_amt) = income_days[current_date.day]
            amt = random.uniform(min_amt, max_amt)
            transaction_count += write_transaction(
                f,
                get_account_id(acc_key),
                current_date,
                amt,
                desc,
                merch,
                "Income",
                type="CREDIT",
            )

        # 3. REGULAR MONTHLY (Day Specific)
        if current_date.day in monthly_days:
            acc_key, cat, merch, desc, (min_amt, max_amt) = monthly_days[
                current_date.day
            ]
            amt = random.uniform(min_amt, max_amt)
            transaction_count += write_transaction(
                f, get_account_id(acc_key), current_date, amt, desc, merch, cat
            )

        # 4. REGULAR DAILY (Probabilistic)
        for prob, acc_key, cat, merch, desc, (min_amt, max_amt) in persona[
            "regular_daily"
        ]:
            if random.random() < prob:
                amt = random.uniform(min_amt, max_amt)
                transaction_count += write_transaction(
                    f, get_account_id(acc_key), current_date, amt, desc, merch, cat
                )

        # 5. OCCASIONAL (Probabilistic)
        for prob, acc_key, cat, merch, desc, (min_amt, max_amt) in persona[
            "occasional_probabilistic"
        ]:
            if random.random() < prob:
                amt = random.uniform(min_amt, max_amt)
                transaction_count += write_transaction(
                    f, get_account_id(acc_key), current_date, amt, desc, merch, cat
                )

        current_date += timedelta(days=1)
        day_count += 1

    # --- 5. Write to File ---
    try:
        with open(output_file, "w", encoding="utf-8") as sql_file:
            sql_file.write(f.getvalue())

        end_time = time.time()
        duration = end_time - start_time

        print(
            f"\nSuccess! \nGenerated {transaction_count} transactions for '{persona_name}' over {day_count} days."
        )
        print(f"File saved as: {output_file}")
        print(f"Generation took: {duration:.4f} seconds.")

    except Exception as e:
        print(f"\nError writing to file: {e}")
    finally:
        f.close()


# --- 3. RUN THE SCRIPT ---
if __name__ == "__main__":

    # --- CONFIGURATION ---
    # *** CHANGE THIS to select your persona ***
    SELECTED_PERSONA = (
        "PRIYA_BANK_MANAGER"  # or "ROHAN_SOFTWARE_DEV", "BIKESH_KTM_STUDENT"
    )
    START_DATE = datetime(2025, 1, 1)
    END_DATE = datetime(2025, 12, 31)
    # ---------------------

    print(f"Generating 1-year data for persona: '{SELECTED_PERSONA}'...")
    generate_sql_for_persona(
        SELECTED_PERSONA, PERSONA_DEFINITIONS, START_DATE, END_DATE
    )
