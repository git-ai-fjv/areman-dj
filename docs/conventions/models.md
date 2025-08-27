# 📄 Project Conventions

This document describes our binding conventions for Django apps, models, imports, and structure.  
All developers must follow these rules. Legacy code will be migrated step by step.

---

## 1. General Principles

- **One model = one file**  
  Each Django model is stored in its own file under `apps/<app>/models/`.

  Example:

  apps/catalog/models/product.py  
  apps/catalog/models/product_variant.py  
  apps/procurement/models/supplier_product.py  
  apps/procurement/models/supplier_price.py  
  apps/procurement/models/supplier_quantity_price.py  

- **No dynamic loaders**  
  We do **not** use `__init__.py` autoloading for models.  
  Explicit imports only.

- **Explicit imports**  
  Always import by full path:

  # python
  from apps.catalog.models.product import Product  
  from apps.catalog.models.product_variant import ProductVariant  
  from apps.procurement.models.supplier_product import SupplierProduct  
  from apps.procurement.models.supplier_price import SupplierPrice  
  from apps.procurement.models.supplier_quantity_price import SupplierQuantityPrice  

---

## 2. Imports

- Group order:  
  1. Python standard library  
  2. Third-party packages  
  3. Local apps (`apps.<app>.models.<file>`)

- Never use relative imports like `from .product import Product`.

---

## 3. Migrations

- Each model lives in its own file → migrations are explicit and traceable.  
- During development: `make resetdb` is allowed.  
- For customer environments: **never** reset, only use `makemigrations` + `migrate`.

---

## 4. Philosophy

- **Clarity over brevity**: Explicit imports are longer, but make the codebase transparent.  
- **Separation of concerns**: Models, services, selectors, admin, and management commands are split by folder.  
- **Consistency first**: Every developer must follow this structure, no exceptions.

---
