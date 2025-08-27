# 📘 Developer Notes

This file consolidates our **project conventions, models, Makefile usage, and import strategy**  
— all in one place, for easy reference.  
Everything here is in **English** and formatted for a single `.md` file.

---

## 🚀 Development Philosophy

- **One model = one file**  
  Each Django model lives in its own file under `apps/<app>/models/`.
- **Explicit imports**  
  No automatic `__init__.py` loaders. Always import the model directly from its file, e.g.:

  # python
  from apps.procurement.models.supplier_product import SupplierProduct

- **Reset vs Migration**  
  - During early development: `make resetdb` wipes and reseeds the database (⚠️ data loss).
  - After first release: use migrations only, to preserve customer data.  
    → Think of migrations as an **upgrade path** for production data.

---

## 📂 Project Structure (snapshot)

- `apps/catalog/models/product.py` → **Product master data**  
- `apps/catalog/models/product_variant.py` → **Sellable units (SKU/EAN, logistics, constraints)**  
- `apps/procurement/models/supplier_product.py` → **Links product variant to a supplier**  
- `apps/procurement/models/supplier_price.py` → **Supplier price lists (with sub-table for quantity-based prices)**  
- `apps/core/models/currency.py` → **ISO-4217 currencies**

---

## 🛠️ Models

### Product (`apps/catalog/models/product.py`)
- Organization, name, slug.
- Manufacturer + part number (with normalized field).
- Group, description, SEO metadata.
- Flags: `is_new`, `is_closeout`, `release_date`, `is_active`.
- Timestamps.

**Constraints:**  
- Unique per organization + slug.  
- Unique per org + manufacturer + normalized part number.  

---

### ProductVariant (`apps/catalog/models/product_variant.py`)
- Organization, product, packing, origin, state.
- Identity: `sku`, `ean`, `barcode`.
- Logistics: customs code, weight, dimensions, eCl@ss code.
- Stock & availability: `stock_quantity`, `available_stock`, `is_available`, `shipping_free`.
- Order constraints: `min_purchase`, `max_purchase`, `purchase_steps`.
- Flags: `is_active`, `is_topseller`.
- Timestamps.

**Constraints:**  
- SKU unique per org.  
- Combination of product + packing + origin + state unique per org.  

---

### SupplierProduct (`apps/procurement/models/supplier_product.py`)
- Organization, supplier, variant.
- Supplier-specific SKU and description.
- Procurement attributes: `pack_size`, `min_order_qty`, `lead_time_days`.
- Flags: `is_active`, `is_preferred`.
- Notes + timestamps.

**Constraints:**  
- One supplier ↔ variant ↔ org combination is unique.  
- Positive checks on pack size, MOQ, and lead time.

---

### SupplierPrice (`apps/procurement/models/supplier_price.py`)
- Foreign key → `SupplierProduct`.
- Currency (FK to `Currency`).
- `unit_price` (nullable if quantity prices exist).
- Validity: `valid_from`, `valid_to`.
- Flags: `is_active`.
- Timestamps.

**Constraints:**  
- Unique per supplier product + currency + valid_from.  

---

### SupplierQuantityPrice (`apps/procurement/models/supplier_quantity_price.py`)
- Foreign key → `SupplierPrice`.
- Quantity threshold (`min_quantity`).
- Unit price at that threshold.

**Constraints:**  
- Unique per supplier price + min_quantity.  

---

### Currency (`apps/core/models/currency.py`)
- Primary key: `code` (ISO-4217).
- Name, symbol, decimal places.
- Active flag.

---

## 📦 Supplier Price Import Logic

When importing from supplier API:

- If **unit price** changes → insert new `SupplierPrice` entry.  
- If only **validity window** changes → update `valid_to` and insert new row for new `valid_from`.  
- If price unchanged → only update `updated_at`.  
- Quantity-based prices go to `SupplierQuantityPrice`.  

---

## 📑 Makefile (important targets)

# bash
make migrate        # Apply migrations
make makemigrations # Generate migrations
make run            # Run dev server
make resetdb        # ⚠ Reset database (drop + create + migrate + seed)
make seed           # Seed base data
make lint           # flake8 checks
make format         # black auto-format
make isort          # sort imports
make test           # run pytest
make coverage       # run tests with coverage

---

## ✅ Import Strategy

- **Explicit imports only** (never rely on auto-loading `__init__.py`).  
- Example:

  # python
  from apps.catalog.models.product import Product
  from apps.procurement.models.supplier_product import SupplierProduct
  from apps.procurement.models.supplier_price import SupplierPrice
  from apps.procurement.models.supplier_quantity_price import SupplierQuantityPrice

---

## 🧭 Workflow Conventions

- **One feature per commit**, one file at a time (~≤150 lines).  
- Always include path + old vs new code when editing.  
- Use `make resetdb` during pre-release.  
- After go-live → only migrations.  

---

## 🔮 Future Notes

- Shop system doesn’t read directly from DB; it’s fed via APIs.  
- ERP + sales support is the central source of truth.  
- Taxes are neutral in procurement (focus is net purchase).  
- SEO/marketing fields exist on `Product`.  
- Prices belong to **sales channel context** (future extension).  
