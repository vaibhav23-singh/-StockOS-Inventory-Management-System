# ⬡ StockOS — Inventory Management System

A full-stack stock management application built with **Flask**, **MySQL**, and a custom HTML/CSS/JS frontend.

---

## Tech Stack

| Layer    | Technology              |
|----------|-------------------------|
| Frontend | HTML5, CSS3, Vanilla JS, Chart.js |
| Backend  | Python 3.11 + Flask     |
| Database | MySQL 8.0               |
| Deploy   | Docker Compose (optional) |

---

## Features

- **Dashboard** — Live KPIs, stock movement chart (30-day), category breakdown donut chart
- **Product Management** — Add, edit, delete products with SKU, pricing, supplier, and location
- **Stock Transactions** — Stock In / Stock Out / Adjustment with audit trail
- **Category Management** — Organize products into categories
- **Low Stock Alerts** — Visual alerts with progress bars for products below reorder level
- **Product Detail View** — Per-product transaction history
- **Search & Filter** — Full-text search, category filter, low-stock toggle

---

## Project Structure

```
stock-app/
├── backend/
│   ├── app.py              # Flask API (all routes)
│   ├── requirements.txt    # Python dependencies
│   ├── schema.sql          # MySQL schema + indexes
│   ├── Dockerfile
│   └── .env.example        # Environment variables template
├── frontend/
│   └── index.html          # Complete SPA (no build step needed)
├── docker-compose.yml
├── nginx.conf
└── README.md
```

---

## Quick Start — Docker (Recommended)

```bash
# Clone / download the project
cd stock-app

# Start all services (MySQL + Flask + Nginx)
docker-compose up -d

# View logs
docker-compose logs -f backend

# Open the app
open http://localhost:8080
```

The database is seeded automatically with sample categories and products.

---

## Manual Setup (Local Dev)

### 1. MySQL

```sql
-- Create the database
mysql -u root -p < backend/schema.sql
```

### 2. Flask Backend

```bash
cd backend

# Copy and configure environment
cp .env.example .env
# Edit .env with your MySQL credentials

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
# → Runs on http://localhost:5000
```

### 3. Frontend

Just open `frontend/index.html` in a browser — no build step required.

> **Note:** If you open the file directly (`file://`), you may need to configure CORS.  
> Use a simple HTTP server instead:
> ```bash
> cd frontend
> python -m http.server 3000
> # → Open http://localhost:3000
> ```

---

## API Reference

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all products (supports `?search=`, `?category=`, `?low_stock=true`) |
| GET | `/api/products/:id` | Get product + transaction history |
| POST | `/api/products` | Create product |
| PUT | `/api/products/:id` | Update product |
| DELETE | `/api/products/:id` | Delete product |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | List recent transactions |
| POST | `/api/transactions` | Create transaction (IN / OUT / ADJUSTMENT) |

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | List categories with product count |
| POST | `/api/categories` | Create category |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard` | KPIs, charts data, alerts |
| GET | `/api/health` | Health check |

---

## Database Schema

```sql
categories (id, name, description, created_at)

products (id, sku, name, description, category_id,
          quantity, unit_price, cost_price,
          reorder_level, supplier, location,
          created_at, updated_at)

transactions (id, product_id, type[IN|OUT|ADJUSTMENT],
              quantity, reference, notes, user, created_at)
```

---

## Environment Variables

```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=stock_management
FLASK_ENV=development
FLASK_DEBUG=1
```
