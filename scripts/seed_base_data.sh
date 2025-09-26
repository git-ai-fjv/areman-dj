#!/usr/bin/env bash
# Created according to the user's permanent Copilot Base Instructions.
set -euo pipefail

# Resolve repository root (one level up from this script), then cd there
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${ROOT_DIR}"

# Activate venv if present (optional)
if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi



### mandant:
echo "****************** Seed Mandant  ********************************"
python manage.py seed_organization --items "1:Areman"
# Call Django management command (works from repo root)
echo "****************** Seed Manufacturer  ********************************"
python manage.py seed_manufacturers --items "1:indefinite,2:Komatsu"
echo "****************** Seed origin  ********************************"
python manage.py seed_origin --items "O:original,A:alternate,E:Erstausruester"
echo "****************** Seed packing  ********************************"
python manage.py seed_packing --items "1:1:1:l,1:2:1:piece,1:3:1:pauschal,1:10:10:10 l,1:20:20:20 l,1:60:60:60 l,1:60:200:200 l,1:80:1000:1000 l"
echo "****************** Seed currency  ********************************"
python manage.py seed_currency --items "EUR:Euro:€:2,USD:US Dollar:$:2,GBP:Pound Sterling:£:2"
echo "****************** Seed price groups  ********************************"
python manage.py seed_price_group --items "1::no price Group,1:1:price group 1,1:2:price group 2"
echo "****************** Seed product groups  ********************************"
python manage.py seed_product_group --items "1::no product group,1:1:product group 1,1:2:product group 2"
echo "****************** Seed state  ********************************"
python manage.py seed_state --items "N:new,U:used,R:reman"

echo "****************** source_types  ********************************"
python manage.py seed_import_source_types

echo "****************** default dummy ********************************"
python manage.py seed_suppliers --items "1:SUPP01:Default dummy Supplier for tests:0"
python manage.py seed_suppliers --items "1:70001:Elsaesser:1"
python manage.py seed_suppliers --items "1:70002:Kuhn:1"
echo "****************** data types for import ********************************"
python manage.py seed_import_transform_types
python manage.py seed_import_data_types
echo "****************** create default for import ********************************"
python manage.py seed_import_defaults --org 1 --valid-from 2025-01-01
echo "****************** seed fuer komatsu (Kuhn) ********************************"
python manage.py seed_import_map_komatsu --supplier 70002 --org 1

echo "****************** Create superuser ********************************"



DJANGO_SUPERUSER_USERNAME=fjv \
DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD=1 \
python manage.py createsuperuser --noinput || true

