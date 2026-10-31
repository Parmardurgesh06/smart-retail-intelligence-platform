# Smart Retail Intelligence Platform

A beginner-friendly college project using React, FastAPI, MySQL, classical ML, Data Mining, and Business Analytics.

## Current starter version
- React dashboard UI
- Inventory CRUD UI
- Sales recording UI
- FastAPI backend
- SQLite fallback database for immediate local demo
- MySQL schema included separately
- Basic analytics endpoints
- Demand forecasting endpoint with a simple Random Forest baseline
- K-Means customer segmentation endpoint
- Apriori-style market basket analysis implemented without an extra ML package

## Run backend
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API: http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

Then open the Vite URL shown in the terminal.

## MySQL
See `database/schema.sql`. The starter backend uses SQLite so the project runs without MySQL configuration. You can migrate the SQL schema and replace the repository layer with MySQL later.
