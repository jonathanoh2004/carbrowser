# CarBrowser — CSE 412 Group 22

A Flask-based web application for browsing and managing a sports car catalog.
Built on top of a PostgreSQL relational database.

---

## Prerequisites

Make sure you have the following installed:

- Python 3.x
- PostgreSQL
- pgAdmin 4 (optional but recommended)
- pip

---

## 1. Setting Up the Database

### Step 1: Create the database

Open pgAdmin or your terminal and create a new database called `carbrowser`.

In pgAdmin: right-click Databases → Create → Database → name it `carbrowser`.

Or in terminal:
```
psql -U postgres -c "CREATE DATABASE carbrowser;"
```

### Step 2: Load the database dump

Open a terminal and run:

```
psql -U postgres -d carbrowser -f car_project_dump.sql
```

It will prompt for your postgres password. You may see some warnings about
roles not existing — these are harmless and the data will load correctly.

### Step 3: Verify the data loaded

In pgAdmin's Query Tool or psql, run:

```sql
SELECT COUNT(*) FROM car;
SELECT COUNT(*) FROM brand;
SELECT COUNT(*) FROM "user";
```

You should see approximately 1007 cars and 38 brands.

---

## 2. Setting Up and Running the App

### Step 1: Install dependencies

```
pip install flask psycopg2-binary
```

### Step 2: Configure the database connection

Open `db.py` and update the connection details to match your local setup:

```python
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="carbrowser",
        user="postgres",
        password="YOUR_PASSWORD_HERE"
    )
```

Replace `YOUR_PASSWORD_HERE` with your actual PostgreSQL password.

### Step 3: Run the app

```
python app.py
```

### Step 4: Open in browser

Navigate to:

```
http://127.0.0.1:5000
```

---

## File Structure

```
carbrowser/
├── app.py               # Flask backend with all routes
├── db.py                # Database connection setup
├── car_project_dump.sql # Full PostgreSQL database dump
├── README.md
└── templates/
    ├── base.html        # Base layout
    ├── index.html       # Home page with stats
    ├── cars.html        # Car browser with filters
    ├── lists.html       # List management
    ├── list_detail.html # Individual list view and CRUD
    └── users.html       # User management
```

---

## Test Login Credentials

| Name         | Email                  | Password  |
|--------------|------------------------|-----------|
| Pranav Battu | pranav@example.com     | pass123   |
| Alex Johnson | alex@example.com       | alexpass  |
| Maria Lopez  | maria@example.com      | maria456  |

---

## Tech Stack

- **Frontend:** HTML, Jinja2 templates
- **Backend:** Python, Flask
- **Database:** PostgreSQL
- **Driver:** psycopg2
