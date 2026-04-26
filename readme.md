# Jewelry Pricing Tool

A lightweight web-based jewelry pricing system built with Python (Flask) for internal team use.
This tool helps calculate product prices using configurable formulas, manage SKUs, and export pricing data to Excel.

---

## Features

* Add, edit, delete, and duplicate jewelry products
* Formula-based pricing engine (metal + diamond + making + margin)
* Auto-generated SKU IDs (RNG, NEC, BRC formats)
* Configurable rates (gold, diamond, margin)
* Dashboard with search, filter, and sorting
* Excel export with full cost breakdown
* Local database (SQLite)

---

## Tech Stack

* Backend: Python (Flask)
* Database: SQLite
* Frontend: HTML, CSS, JavaScript
* Excel Export: pandas + openpyxl

---

## Project Structure

```
jewelry_pricing_tool/
│
├── app.py
├── database.db
├── config.json
├── requirements.txt
│
├── templates/
├── static/
├── utils/
├── models/
```

---

## Pricing Logic

Metal Price = Weight × Gold Rate × Purity Factor
Diamond Price = Carat × Rate
Total Cost = Metal + Diamond + Making
Final Price = Total Cost × (1 + Margin%)

Purity factors:

* 14k = 0.585
* 18k = 0.75

All rates are configurable via config.json.

---

## Getting Started

1. Clone the repository

```
git clone https://github.com/mracuity/jewelry-pricing-tool.git
cd jewelry-pricing-tool
```

2. Install dependencies

```
pip install -r requirements.txt
```

3. Run the application

```
python app.py
```

4. Open in browser

http://localhost:5000

---

## Configuration

Edit config.json to update:

* Gold rate (per gram)
* Diamond rate (per carat)
* Default margin
* Currency symbol

---

## Excel Export

Export all products including:

* Product details
* Metal cost
* Diamond cost
* Making charges
* Final price

---

## Limitations

* SQLite is not ideal for multiple concurrent users
* No authentication system (intended for internal use)
* Not optimized for large-scale deployment

---

## Future Improvements

* PostgreSQL database support
* User authentication and roles
* Multi-currency pricing
* Batch upload via Excel
* API integration

---

## Use Case

* Jewelry manufacturers
* Internal pricing teams
* E-commerce catalog preparation

---

## License

Copyright (c) 2026 [Mr Acuity](https://dev.mracuity.com).

All rights reserved.

This software is provided for viewing purposes only.
No permission is granted to use, copy, modify, merge, publish, distribute, sublicense, or sell copies of the software without explicit written permission from the author.