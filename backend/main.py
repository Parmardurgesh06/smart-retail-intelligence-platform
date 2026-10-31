from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from pathlib import Path
from datetime import date, timedelta
import random
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import r2_score
from sklearn.metrics import mean_squared_error
DB = Path(__file__).with_name("retail.db")
app = FastAPI(title="Smart Retail Intelligence API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000",
                   "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        reorder_level INTEGER NOT NULL DEFAULT 10
    );
    CREATE TABLE IF NOT EXISTS sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        sale_date TEXT NOT NULL,
        total REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sale_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sale_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );
    """)
    if c.execute("SELECT COUNT(*) n FROM products").fetchone()["n"] == 0:
        products = [
            ("Rice 5kg","Grocery",320,42,10),
            ("Milk 1L","Dairy",58,8,12),
            ("Bread","Bakery",40,25,10),
            ("Butter","Dairy",55,14,8),
            ("Tea 250g","Beverages",120,30,10),
            ("Sugar 1kg","Grocery",48,50,12),
            ("Biscuits","Snacks",30,18,10),
            ("Shampoo","Personal Care",180,7,10),
        ]
        c.executemany("INSERT INTO products(name,category,price,stock,reorder_level) VALUES(?,?,?,?,?)", products)
    if c.execute("SELECT COUNT(*) n FROM customers").fetchone()["n"] == 0:
        c.executemany("INSERT INTO customers(name) VALUES(?)", [(f"Customer {i}",) for i in range(1, 16)])
    if c.execute("SELECT COUNT(*) n FROM sales").fetchone()["n"] == 0:
        products = c.execute("SELECT * FROM products").fetchall()
        today = date.today()
        random.seed(7)
        for d in range(45, 0, -1):
            for _ in range(random.randint(2, 6)):
                p = random.choice(products)
                qty = random.randint(1, 4)
                total = round(p["price"] * qty, 2)
                cur = c.execute(
                    "INSERT INTO sales(customer_id,sale_date,total) VALUES(?,?,?)",
                    (random.randint(1,15), str(today-timedelta(days=d)), total)
                )
                c.execute(
                    "INSERT INTO sale_items(sale_id,product_id,quantity,price) VALUES(?,?,?,?)",
                    (cur.lastrowid,p["id"],qty,p["price"])
                )
    c.commit()
    c.close()

init_db()

class ProductIn(BaseModel):
    name: str
    category: str
    price: float
    stock: int
    reorder_level: int = 10

class SaleItemIn(BaseModel):
    product_id: int
    quantity: int

class SaleIn(BaseModel):
    customer_id: int = 1
    items: list[SaleItemIn]

@app.get("/")
def root():
    return {"message":"Smart Retail Intelligence API is running"}

@app.get("/products")
def products():
    c=conn()
    rows=c.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    c.close()
    return [dict(r) for r in rows]

@app.post("/products")
def add_product(p: ProductIn):
    c=conn()
    cur=c.execute(
        "INSERT INTO products(name,category,price,stock,reorder_level) VALUES(?,?,?,?,?)",
        (p.name,p.category,p.price,p.stock,p.reorder_level)
    )
    c.commit()
    row=c.execute("SELECT * FROM products WHERE id=?",(cur.lastrowid,)).fetchone()
    c.close()
    return dict(row)

@app.put("/products/{product_id}")
def update_product(product_id:int,p:ProductIn):
    c=conn()
    c.execute("UPDATE products SET name=?,category=?,price=?,stock=?,reorder_level=? WHERE id=?",
              (p.name,p.category,p.price,p.stock,p.reorder_level,product_id))
    c.commit()
    row=c.execute("SELECT * FROM products WHERE id=?",(product_id,)).fetchone()
    c.close()
    if not row: raise HTTPException(404,"Product not found")
    return dict(row)

@app.delete("/products/{product_id}")
def delete_product(product_id:int):
    c=conn()
    c.execute("DELETE FROM products WHERE id=?",(product_id,))
    c.commit(); c.close()
    return {"message":"Product deleted"}

@app.post("/sales")
def create_sale(s: SaleIn):
    if not s.items: raise HTTPException(400,"Sale must contain items")
    c=conn()
    total=0
    try:
        for item in s.items:
            p=c.execute("SELECT * FROM products WHERE id=?",(item.product_id,)).fetchone()
            if not p: raise HTTPException(404,f"Product {item.product_id} not found")
            if item.quantity <= 0 or p["stock"] < item.quantity:
                raise HTTPException(400,f"Insufficient stock for {p['name']}")
            total += p["price"] * item.quantity
        cur=c.execute("INSERT INTO sales(customer_id,sale_date,total) VALUES(?,?,?)",
                      (s.customer_id,str(date.today()),round(total,2)))
        sale_id=cur.lastrowid
        for item in s.items:
            p=c.execute("SELECT * FROM products WHERE id=?",(item.product_id,)).fetchone()
            c.execute("INSERT INTO sale_items(sale_id,product_id,quantity,price) VALUES(?,?,?,?)",
                      (sale_id,item.product_id,item.quantity,p["price"]))
            c.execute("UPDATE products SET stock=stock-? WHERE id=?",(item.quantity,item.product_id))
        c.commit()
        return {"sale_id":sale_id,"total":round(total,2)}
    finally:
        c.close()

@app.get("/sales")
def sales():
    c=conn()
    rows=c.execute("""SELECT s.id,s.customer_id,s.sale_date,s.total,
                      COALESCE(GROUP_CONCAT(p.name || ' x' || si.quantity, ', '),'') items
                      FROM sales s
                      LEFT JOIN sale_items si ON s.id=si.sale_id
                      LEFT JOIN products p ON p.id=si.product_id
                      GROUP BY s.id ORDER BY s.id DESC LIMIT 100""").fetchall()
    c.close()
    return [dict(r) for r in rows]

@app.get("/analytics")
def analytics():

    c = conn()

    # Basic KPIs
    revenue = c.execute(
        "SELECT COALESCE(SUM(total), 0) v FROM sales"
    ).fetchone()["v"]

    sales_count = c.execute(
        "SELECT COUNT(*) v FROM sales"
    ).fetchone()["v"]

    products = c.execute(
        "SELECT COUNT(*) v FROM products"
    ).fetchone()["v"]

    low = c.execute(
        "SELECT COUNT(*) v FROM products WHERE stock <= reorder_level"
    ).fetchone()["v"]

    # Average Order Value
    average_order_value = (
        revenue / sales_count
        if sales_count > 0
        else 0
    )

    # Daily Sales
    daily = c.execute("""
        SELECT
            sale_date,
            ROUND(SUM(total), 2) revenue
        FROM sales
        GROUP BY sale_date
        ORDER BY sale_date
    """).fetchall()

    # Monthly Revenue
    monthly = c.execute("""
        SELECT
            substr(sale_date, 1, 7) month,
            ROUND(SUM(total), 2) revenue
        FROM sales
        GROUP BY substr(sale_date, 1, 7)
        ORDER BY month
    """).fetchall()

    # Top Products
    top = c.execute("""
        SELECT
            p.name,
            SUM(si.quantity) quantity,
            ROUND(SUM(si.quantity * si.price), 2) revenue
        FROM sale_items si
        JOIN products p
            ON p.id = si.product_id
        GROUP BY p.id
        ORDER BY quantity DESC
        LIMIT 8
    """).fetchall()

    # Category-wise Sales
    category = c.execute("""
        SELECT
            p.category,
            SUM(si.quantity) quantity,
            ROUND(SUM(si.quantity * si.price), 2) revenue
        FROM sale_items si
        JOIN products p
            ON p.id = si.product_id
        GROUP BY p.category
        ORDER BY revenue DESC
    """).fetchall()

    c.close()

    return {

        "kpis": {
            "revenue": round(revenue, 2),
            "sales": sales_count,
            "products": products,
            "low_stock": low,
            "average_order_value":
                round(average_order_value, 2)
        },

        "daily_sales": [
            dict(x)
            for x in daily
        ],

        "monthly_sales": [
            dict(x)
            for x in monthly
        ],

        "top_products": [
            dict(x)
            for x in top
        ],

        "category_sales": [
            dict(x)
            for x in category
        ]
    }

def sales_dataframe():
    c=conn()
    rows=c.execute("""SELECT s.sale_date,p.id product_id,p.name,SUM(si.quantity) quantity
                      FROM sales s JOIN sale_items si ON s.id=si.sale_id
                      JOIN products p ON p.id=si.product_id
                      GROUP BY s.sale_date,p.id ORDER BY s.sale_date""").fetchall()
    c.close()
    df=pd.DataFrame([dict(r) for r in rows])
    return df

@app.get("/ml/forecast/{product_id}")
def forecast(product_id:int, days:int=7):
    df=sales_dataframe()
    if df.empty: return {"product_id":product_id,"predictions":[]}
    df=df[df.product_id==product_id].copy()
    if len(df)<10:
        avg=float(df.quantity.mean()) if len(df) else 0
        return {"product_id":product_id,"method":"historical_mean_baseline",
                "predictions":[{"date":str(date.today()+timedelta(days=i+1)),"demand":round(avg,2)} for i in range(days)]}
    df["date"]=pd.to_datetime(df.sale_date)
    df=df.set_index("date").resample("D")["quantity"].sum().fillna(0).reset_index()
    for lag in [1,2,3,7]:
        df[f"lag_{lag}"]=df.quantity.shift(lag)
    df=df.dropna()
    if len(df)<8:
        avg=float(df.quantity.mean())
        return {"product_id":product_id,"method":"historical_mean_baseline",
                "predictions":[{"date":str(date.today()+timedelta(days=i+1)),"demand":round(avg,2)} for i in range(days)]}
    X=df[[f"lag_{x}" for x in [1,2,3,7]]]
    y=df.quantity
    model=RandomForestRegressor(n_estimators=150,random_state=42,max_depth=6)
    model.fit(X,y)
    history=list(df.quantity.astype(float))
    preds=[]
    for i in range(days):
        row=[[history[-1],history[-2],history[-3],history[-7]]]
        pred=max(0,float(model.predict(row)[0]))
        history.append(pred)
        preds.append({"date":str(date.today()+timedelta(days=i+1)),"demand":round(pred,2)})
    return {"product_id":product_id,"method":"RandomForestRegressor_with_lag_features","predictions":preds}

@app.get("/ml/segments")
def segments():
    c=conn()
    rows=c.execute("""SELECT c.id customer_id,c.name,
                      COALESCE(SUM(s.total),0) total_spending,
                      COUNT(DISTINCT s.id) purchases
                      FROM customers c LEFT JOIN sales s ON c.id=s.customer_id
                      GROUP BY c.id""").fetchall()
    c.close()
    data=pd.DataFrame([dict(r) for r in rows])
    if len(data)<3: return []
    data["avg_order_value"]=data["total_spending"]/data["purchases"].replace(0,1)
    X=data[["total_spending","purchases","avg_order_value"]].fillna(0)
    scaled=StandardScaler().fit_transform(X)
    k=min(3,len(data))
    km=KMeans(n_clusters=k,random_state=42,n_init=10)
    data["cluster"]=km.fit_predict(scaled)
    return data.round(2).to_dict(orient="records")

@app.get("/data-mining/apriori")
def apriori(min_support: float = 0.15, min_confidence: float = 0.0):
    """Find frequent product combinations and generate association rules.

    min_support and min_confidence are proportions between 0 and 1.
    Example: /data-mining/apriori?min_support=0.005&min_confidence=0.0
    """
    if not 0 <= min_support <= 1:
        raise HTTPException(status_code=400, detail="min_support must be between 0 and 1")
    if not 0 <= min_confidence <= 1:
        raise HTTPException(status_code=400, detail="min_confidence must be between 0 and 1")

    c = conn()
    try:
        rows = c.execute(
            """SELECT s.id AS sale_id, p.name
               FROM sales AS s
               JOIN sale_items AS si ON s.id = si.sale_id
               JOIN products AS p ON p.id = si.product_id
               ORDER BY s.id"""
        ).fetchall()
    finally:
        c.close()

    baskets = {}
    for row in rows:
        baskets.setdefault(row["sale_id"], set()).add(row["name"])

    transactions = list(baskets.values())
    transaction_count = len(transactions)
    print("APRIORI TRANSACTION COUNT:", transaction_count)
    if transaction_count == 0:
        return []

    # Calculate support for each itemset as a fraction of all transactions.
    def support(itemset):
        return sum(itemset.issubset(transaction) for transaction in transactions) / transaction_count

    item_counts = {}
    for transaction in transactions:
        for item in transaction:
            item_counts[item] = item_counts.get(item, 0) + 1

    frequent_support = {
        frozenset([item]): count / transaction_count
        for item, count in item_counts.items()
        if count / transaction_count >= min_support
    }
    current_level = set(frequent_support.keys())
    k = 2

    # Generate itemsets of size 2, 3, ... until no frequent itemsets remain.
    while current_level:
        current_list = sorted(current_level, key=lambda itemset: sorted(itemset))
        candidates = set()
        for i in range(len(current_list)):
            for j in range(i + 1, len(current_list)):
                candidate = current_list[i] | current_list[j]
                if len(candidate) != k:
                    continue
                # Apriori pruning: every (k-1)-subset must be frequent.
                if all(
                    frozenset(subset) in current_level
                    for subset in __import__("itertools").combinations(candidate, k - 1)
                ):
                    candidates.add(candidate)

        next_level = set()
        for candidate in candidates:
            candidate_support = support(candidate)
            if candidate_support >= min_support:
                frequent_support[candidate] = candidate_support
                next_level.add(candidate)

        current_level = next_level
        k += 1

    # Generate rules from every frequent itemset with 2 or more items.
    from itertools import combinations
    rules = []
    for itemset, itemset_support in frequent_support.items():
        if len(itemset) < 2:
            continue
        ordered_items = sorted(itemset)
        for antecedent_size in range(1, len(ordered_items)):
            for antecedent_items in combinations(ordered_items, antecedent_size):
                antecedent = frozenset(antecedent_items)
                consequent = itemset - antecedent
                antecedent_support = frequent_support.get(antecedent)
                consequent_support = frequent_support.get(consequent)
                if not antecedent_support or not consequent_support:
                    continue
                confidence = itemset_support / antecedent_support
                lift = confidence / consequent_support
                if confidence >= min_confidence:
                    rules.append({
                        "antecedent": ", ".join(sorted(antecedent)),
                        "consequent": ", ".join(sorted(consequent)),
                        "support": round(itemset_support, 4),
                        "confidence": round(confidence, 4),
                        "lift": round(lift, 4),
                    })

    rules.sort(key=lambda rule: (rule["lift"], rule["confidence"]), reverse=True)
    # Keep the original API response shape: a JSON list of association rules.
    return rules[:100]

@app.get("/ml/forecast")
def demand_forecast(product_id: int):

    c = conn()

    rows = c.execute("""
        SELECT
            s.sale_date,
            SUM(si.quantity) AS demand
        FROM sales s
        JOIN sale_items si
            ON s.id = si.sale_id
        WHERE si.product_id = ?
        GROUP BY s.sale_date
        ORDER BY s.sale_date
    """, (product_id,)).fetchall()

    product = c.execute(
        "SELECT id, name, stock FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()

    c.close()

    if not product:
        return {
            "error": "Product not found"
        }

    if len(rows) < 14:
        return {
            "error": "Not enough sales history. Need at least 14 days of sales data."
        }

    # Convert database data to DataFrame
    df = pd.DataFrame(
        [dict(row) for row in rows]
    )

    df["sale_date"] = pd.to_datetime(
        df["sale_date"]
    )

    # Create complete daily data
    df = df.set_index("sale_date")

    df = df.asfreq("D", fill_value=0)

    df = df.reset_index()

    # Feature Engineering
    df["day"] = df["sale_date"].dt.day
    df["day_of_week"] = df["sale_date"].dt.dayofweek
    df["month"] = df["sale_date"].dt.month

    df["lag_1"] = df["demand"].shift(1)
    df["lag_7"] = df["demand"].shift(7)

    df["rolling_7"] = (
        df["demand"]
        .shift(1)
        .rolling(7)
        .mean()
    )

    # Remove rows containing NaN
    df = df.dropna()

    if len(df) < 7:
        return {
            "error": "Not enough data after feature engineering."
        }

    features = [
        "day",
        "day_of_week",
        "month",
        "lag_1",
        "lag_7",
        "rolling_7"
    ]

    X = df[features]
    y = df["demand"]

    # Time-based train/test split
    split = int(len(df) * 0.8)

    X_train = X.iloc[:split]
    X_test = X.iloc[split:]

    y_train = y.iloc[:split]
    y_test = y.iloc[split:]

    # Random Forest
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42
    )

    model.fit(
        X_train,
        y_train
    )

    # Test prediction
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(
        y_test,
        y_pred
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            y_pred
        )
    )

    r2 = r2_score(
        y_test,
        y_pred
    )

    # Future demand prediction
    last_date = df["sale_date"].max()

    future_predictions = []

    temp = df.copy()
    temp["demand"]=temp["demand"].astype(float)

    for i in range(7):

        next_date = (
            last_date +
            pd.Timedelta(days=i + 1)
        )

        last_values = temp["demand"].values

        lag_1 = last_values[-1]

        if len(last_values) >= 7:
            lag_7 = last_values[-7]
        else:
            lag_7 = last_values[-1]

        rolling_7 = np.mean(
            last_values[-7:]
        )

        future_X = pd.DataFrame([{
            "day": next_date.day,
            "day_of_week": next_date.dayofweek,
            "month": next_date.month,
            "lag_1": lag_1,
            "lag_7": lag_7,
            "rolling_7": rolling_7
        }])

        prediction = model.predict(
            future_X
        )[0]

        prediction = max(
            0,
            round(float(prediction), 2)
        )

        future_predictions.append({
            "date": next_date.strftime("%Y-%m-%d"),
            "predicted_demand": prediction
        })

        temp.loc[len(temp)] = [
            next_date,
            prediction,
            next_date.day,
            next_date.dayofweek,
            next_date.month,
            lag_1,
            lag_7,
            rolling_7
        ]

    total_predicted_demand = sum(
        x["predicted_demand"]
        for x in future_predictions
    )

    recommendation = (
        "Restock"
        if product["stock"] < total_predicted_demand
        else "Stock Sufficient"
    )

    return {

        "product": {
            "id": product["id"],
            "name": product["name"],
            "current_stock": product["stock"]
        },

        "model": "Random Forest Regressor",

        "metrics": {
            "mae": round(float(mae), 2),
            "rmse": round(float(rmse), 2),
            "r2": round(float(r2), 2)
        },

        "forecast": future_predictions,

        "total_predicted_demand": round(
            total_predicted_demand,
            2
        ),

        "recommendation": recommendation
    }