# Project Docstrings

## File: `apps/catalog/management/commands/seed_channel.py`
```
Purpose:
    Management command to upsert (create or update) sales channels such as Webshop,
    Amazon, or POS. Reads colon-delimited input from CLI arguments or a file and
    ensures Channel rows exist in the database.

Context:
    Belongs to the catalog app. Provides an easy way to seed or update available
    sales channels without manually editing the database. Useful for initial setup
    or bulk updates of organization-specific sales channels.

Used by:
    - Administrators during project setup (seeding initial channels).
    - CI/CD or deployment scripts to ensure base channels are present.
    - Developers or support staff who need to add/update channels quickly.

Depends on:
    - apps.core.models.Organization (for org resolution by org_code).
    - apps.core.models.Currency (for base currency validation).
    - apps.catalog.models.Channel (the actual target table).
    - Django transaction handling and management command framework.

Example:
    # Seed channels from file
    python manage.py seed_channel --file scripts/channels.txt

    # Seed channels inline via CLI
    python manage.py seed_channel --items "1:WEB:Webshop:shop:EUR:1,1:AMZ:Amazon:marketplace:EUR:1"

    # Dry-run (no DB changes, only validate and print results)
    python manage.py seed_channel --items "1:POS:Point of Sale::EUR:" --dry-run
```

## File: `apps/catalog/management/commands/seed_channel_variant.py`
```
Purpose:
    Management command to upsert (create or update) ChannelVariant rows,
    linking product variants to sales channels. Supports colon-delimited input
    from CLI or file, including publish flags, active states, update markers,
    and optional external IDs from shop systems.

Context:
    Part of the catalog app. Extends seeding of channels by assigning which
    product variants are available in which channels (e.g. Webshop, Amazon).
    Used during initial data setup or ongoing synchronization with external
    sales platforms.

Used by:
    - Administrators to seed product-channel relations.
    - Deployment scripts for initializing sales channel variants.
    - Support staff for one-off updates to channel-variant publishing states.

Depends on:
    - apps.core.models.Organization (to resolve org by org_code).
    - apps.catalog.models.Channel (to resolve channels by code or id).
    - apps.catalog.models.ProductVariant (to resolve product variants by SKU or id).
    - apps.catalog.models.ChannelVariant (target table for persistence).

Example:
    # Dry run (validate only)
    python manage.py seed_channel_variant --file scripts/channel_variants.txt --dry-run

    # Apply from file
    python manage.py seed_channel_variant --file scripts/channel_variants.txt

    # One-off inline seeding
    python manage.py seed_channel_variant --items "1:WEB:SKU-1001:1:1:0,1:AMZ:SKU-2002:::1::AMZ-2002"
```

## File: `apps/catalog/management/commands/seed_manufacturers.py`
```
Purpose:
    Management command to upsert (create or update) Manufacturer records
    based on colon-delimited input provided via CLI. Supports dry-run
    validation without database changes.

Context:
    Part of the catalog app. Ensures the list of manufacturers is
    seeded or updated consistently without manual SQL. Useful for
    initial setup or for bulk adjustments of manufacturer master data.

Used by:
    - Administrators to seed initial manufacturers.
    - Support/deployment scripts to keep manufacturer data in sync.
    - Developers who need to quickly add or adjust manufacturers.

Depends on:
    - apps.catalog.models.manufacturer.Manufacturer (target table).
    - Django management command and ORM update_or_create.

Example:
    # Dry run (no DB changes)
    python manage.py seed_manufacturer --items "1:ACME,2:Contoso" --dry-run

    # Apply changes
    python manage.py seed_manufacturer --items "1:ACME,2:Contoso"
```

## File: `apps/catalog/management/commands/seed_origin.py`
```
Purpose:
    Management command to upsert (create or update) Origin records
    that classify product origin using a single-character code.
    Input is provided as colon-delimited items (code:description).

Context:
    Part of the catalog app. Ensures valid product origin codes (E, N, …)
    exist in the database for classification. Used during project setup
    or whenever new origin codes must be added/updated.

Used by:
    - Administrators to seed initial origin codes.
    - Deployment/support scripts for maintaining standardized origin values.
    - Developers who need to quickly add or update product origin definitions.

Depends on:
    - apps.catalog.models.origin.Origin (target table).
    - Django management command and ORM update_or_create.

Example:
    # Dry run (no DB changes)
    python manage.py seed_origin --items "E:EU,N:Non-EU" --dry-run

    # Apply changes
    python manage.py seed_origin --items "E:EU,N:Non-EU"
```

## File: `apps/catalog/management/commands/seed_packing.py`
```
Purpose:
    Management command to upsert (create or update) Packing records
    for packaging units such as boxes, pallets, or pieces.
    Input is colon-delimited and strictly follows the original SQL
    column order: org_code : packing_code : amount : short_desc [: long_desc].

Context:
    Part of the catalog app. Provides standardized seeding of packing units
    across organizations, ensuring that ERP and webshop share the same
    base packing definitions. Critical for quantity handling and
    procurement consistency.

Used by:
    - Administrators to seed initial packing units.
    - Deployment/support scripts to maintain consistent packing codes.
    - Developers during testing or setup when new packings are required.

Depends on:
    - apps.core.models.organization.Organization (FK resolution).
    - apps.catalog.models.packing.Packing (target table).
    - Python Decimal for fractional amounts (quantized to 3 decimals).
    - Django ORM update_or_create for idempotent upserts.

Example:
    # Dry run (no DB changes)
    python manage.py seed_packing --items "1:1:1:BX" --dry-run

    # Apply simple packings
    python manage.py seed_packing --items "1:1:1:BX,1:2:1:piece"

    # Apply with long description
    python manage.py seed_packing --items "2:30:0.125:PAL:Standard pallet"
```

## File: `apps/catalog/management/commands/seed_product.py`
```
Purpose:
    Management command to upsert Product records into the catalog.
    Accepts colon-delimited items or a file, resolving Organization,
    Manufacturer, and optional ProductGroup. Ensures products are
    uniquely identified by either slug or normalized manufacturer
    part number.

Context:
    Part of the catalog seeding workflow. Used during system setup
    and migrations to preload or update product master data across
    organizations. Ensures consistent slug generation and idempotent
    product creation.

Used by:
    - Administrators to seed or bulk-update products.
    - Import/ETL pipelines when syncing product data from ERP or supplier feeds.
    - Developers to quickly populate test data during local development.

Depends on:
    - apps.core.models.organization.Organization (organization resolution).
    - apps.catalog.models.manufacturer.Manufacturer (required foreign key).
    - apps.catalog.models.product_group.ProductGroup (optional grouping).
    - apps.catalog.models.product.Product (target table).
    - Utility functions for slug normalization and uniqueness.

Key Features:
    - Parses flexible colon-delimited format:
      org_code:manufacturer_code:mpn[:name][:slug][:product_group_code][:active]
    - Auto-generates slug if omitted, enforcing uniqueness per organization.
    - Normalizes MPNs for fallback matching (lowercased, umlaut replacements, non-alnum stripped).
    - Supports dry-run mode for safe validation.
    - Uses atomic transactions for batch safety.

Examples:
    # Dry run with explicit slug
    python manage.py seed_product --items "1:10:ZX-9:Widget ZX-9:widget-zx-9:GRP01:1" --dry-run

    # Apply simple records with and without group/slug
    python manage.py seed_product --items "1:10:ZX-9:Widget ZX-9:::1,1:10:MPN-123::::0"

    # Load from file
    python manage.py seed_product --file scripts/products.txt
```

## File: `apps/catalog/management/commands/seed_product_group.py`
```
Purpose:
    Management command to upsert ProductGroup records by (organization, product_group_code).
    Enables seeding and maintaining product groups per organization in a consistent, idempotent way.

Context:
    Part of the catalog seeding workflow. Used during initial setup, imports, or
    synchronization steps to define or adjust logical product groupings (e.g. Hardware,
    Accessories, No group).

Used by:
    - Administrators when bootstrapping catalog structures.
    - ETL/import processes that need to ensure required product groups exist.
    - Developers when preparing test data for local development.

Depends on:
    - apps.core.models.organization.Organization (for org scoping).
    - apps.catalog.models.product_group.ProductGroup (target model).

Key Features:
    - Accepts colon-delimited items: org_code:product_group_code[:description].
    - Supports empty product_group_code to represent “no group”.
    - Validates code length (max 20 chars) and description length (max 200 chars).
    - Idempotent upsert via `update_or_create`.
    - Supports dry-run mode for safe validation.
    - Runs inside an atomic transaction for batch safety.

Examples:
    # Dry run
    python manage.py seed_product_group --items "1:GRP01:Hardware,1::No group" --dry-run

    # Apply changes
    python manage.py seed_product_group --items "1:GRP01:Hardware,1::No group"
```

## File: `apps/catalog/management/commands/seed_product_media.py`
```
Purpose:
    Management command to upsert ProductMedia entries for products and (optionally)
    their variants. Supports bulk seeding of images, videos, or other media assets
    tied to products in the catalog.

Context:
    Part of the catalog initialization and import workflow. Used to ensure that all
    products have associated media (gallery, main image, etc.) with consistent metadata.
    The command is idempotent and can be run repeatedly to sync media state.

Used by:
    - Admins or ETL scripts importing product catalogs from external sources.
    - Developers preparing demo/test data.
    - Synchronization jobs that need to upsert or update product imagery.

Depends on:
    - apps.core.models.organization.Organization (scoping)
    - apps.catalog.models.product.Product (target relation)
    - apps.catalog.models.product_variant.ProductVariant (optional variant relation)
    - apps.catalog.models.product_media.ProductMedia (main model)

Key Features:
    - Colon-delimited input with up to 12 fields:
      org:product_ref:media_url[:role][:sort_order][:alt_text]
         [:variant_ref][:mime][:width][:height][:file_size][:active]
    - product_ref: product slug (preferred) or numeric id.
    - variant_ref: SKU (preferred) or numeric id (optional).
    - Defaults: role='gallery', sort_order=0, alt_text='', active=True.
    - Length validation on role (20), alt_text (200), mime (100).
    - Idempotent upsert via natural key (organization, product, variant, media_url).
    - Dry-run mode to validate input without DB writes.
    - Full transaction safety.

Examples:
    # Dry run
    python manage.py seed_product_media --items "1:widget-a:https://cdn/img1.jpg:main:0:Front" --dry-run

    # From file
    python manage.py seed_product_media --file scripts/product_media.txt

    # Mixed with optional fields
    python manage.py seed_product_media --items "1:widget-a:https://cdn/img2.jpg:gallery:1::SKU-1001:image/jpeg:1200:1200:154000:1"
```

## File: `apps/catalog/management/commands/seed_product_variant.py`
```
Purpose:
    Management command to upsert ProductVariant records (SKUs) in the catalog.
    Ensures consistent variant data including SKU, barcode, packing, origin,
    state, customs code, weight, and active status.

Context:
    Part of the catalog seeding/import pipeline. Variants are the sellable units
    tied to a Product and enriched with physical/logistic attributes. This command
    allows bulk initialization and safe re-runs (idempotent upserts).

Used by:
    - Admins or ETL scripts during catalog import.
    - Developers/testers preparing demo product data.
    - Integration jobs syncing SKUs from external ERP/PIM systems.

Depends on:
    - apps.core.models.organization.Organization
    - apps.catalog.models.product.Product
    - apps.catalog.models.product_variant.ProductVariant
    - apps.catalog.models.packing.Packing
    - apps.catalog.models.origin.Origin
    - apps.catalog.models.state.State

Key Features:
    - Colon-delimited input with up to 10 fields:
      org:product_id:sku[:barcode][:packing][:origin][:state][:customs][:weight][:active]
    - Default values if omitted:
        packing=2, origin='E', state='A', customs=0, weight=0, active=True.
    - Validation for lengths (SKU ≤120, barcode ≤64, codes length=1).
    - Reference checks: org, product, packing, origin, and state must exist.
    - Upsert strategy:
        1) Match by (organization, sku).
        2) Fallback: (organization, product, packing, origin, state).
    - Dry-run mode to validate input without applying changes.
    - Transactional safety.

Examples:
    # Minimal SKU with defaults
    python manage.py seed_product_variant --items "1:1001:SKU-123"

    # Full variant with explicit attributes
    python manage.py seed_product_variant --items "1:1001:SKU-124:4006381333931:2:E:A:0:0.250:1"

    # From file
    python manage.py seed_product_variant --file scripts/variants.txt
```

## File: `apps/catalog/management/commands/seed_state.py`
```
Purpose:
    Management command to upsert State records. Each State represents a global
    lifecycle or availability flag (e.g. Active, Inactive) and is identified by
    a one-character code.

Context:
    States are referenced by ProductVariant and potentially other catalog
    entities to standardize workflow and status handling. This command seeds or
    updates these global states in an idempotent way.

Used by:
    - Initial system setup to seed required states (e.g., 'A:Active,I:Inactive').
    - Developers/testers preparing demo or test data.
    - Admins or ETL jobs aligning states with external ERP/PIM systems.

Depends on:
    - apps.catalog.models.state.State

Key Features:
    - Colon-delimited input: "code:description".
    - Code must be exactly one uppercase character (CHAR(1)).
    - Description is optional; trimmed to 100 characters.
    - Comma-separated list of multiple states supported.
    - Idempotent upsert by `state_code`.
    - Dry-run mode available for validation only.

Examples:
    # Seed two states (Active, Inactive)
    python manage.py seed_state --items "A:Active,I:Inactive"

    # Dry run to validate input without applying changes
    python manage.py seed_state --items "D:Deleted" --dry-run
```

## File: `apps/catalog/models/channel.py`
```
Purpose:
    Define the Channel model representing a sales or distribution channel
    (e.g., webshop, marketplace) within an organization. Captures its code,
    name, kind, and base currency.

Context:
    Part of the `catalog` app. Channels represent the entry points through which
    products and prices are published. They are used in pricing, procurement,
    and integration with external systems (e.g., shops, marketplaces).

Fields:
    - id (AutoField): Primary key for the channel.
    - organization (FK → core.Organization): The owning organization.
    - channel_code (CharField, max 20): Short code identifying the channel
      within an organization (unique per organization).
    - channel_name (CharField, max 200): Human-readable channel name.
    - kind (CharField, max 50): Type of channel ("shop" or "marketplace").
    - base_currency (FK → core.Currency): Currency in which prices are defined.
    - is_active (BooleanField): Whether this channel is active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple Channels
    - Currency → multiple Channels
    - Channel ↔ Product/Variant pricing via related models (e.g. ChannelVariant)

Used by:
    - Pricing (PriceGroup, PriceList, SalesChannelVariantPrice)
    - Procurement (for supplier channel relations, if applicable)
    - Services for integration with external systems

Depends on:
    - Django ORM
    - core.Organization
    - core.Currency

Example:
    # Get all active marketplace channels for org 1
    Channel.objects.filter(organization__org_code=1, kind="marketplace", is_active=True)
```

## File: `apps/catalog/models/channel_variant.py`
```
Purpose:
    Represent the assignment of a ProductVariant to a sales Channel
    within a specific Organization. Defines availability, publishing
    flags, synchronization state, and external shop IDs.

Context:
    Part of the `catalog` app. Used to manage how product variants
    are distributed into different sales channels (e.g. webshop,
    marketplace). Central for integration and synchronization.

Fields:
    - organization (FK → core.Organization): Owning organization.
    - channel (FK → catalog.Channel): The sales channel.
    - variant (FK → catalog.ProductVariant): The specific product variant.
    - publish (BooleanField): Flag whether this variant is published.
    - is_active (BooleanField): Active/inactive marker.
    - need_shop_update (BooleanField): Marks pending synchronization.
    - shop_product_id (CharField): External shop product identifier.
    - shop_variant_id (CharField): External shop variant identifier.
    - last_synced_at (DateTimeField): Timestamp of last synchronization.
    - last_error (TextField): Stores last sync error message.
    - meta_json (JSONField): Flexible metadata/extensions.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple ChannelVariants
    - Channel → multiple ChannelVariants
    - ProductVariant → multiple ChannelVariants

Used by:
    - Synchronization services to external shops
    - Pricing and publication processes
    - Monitoring/reporting of channel sync states

Depends on:
    - Django ORM
    - core.Organization
    - catalog.Channel
    - catalog.ProductVariant

Example:
    >>> from apps.catalog.models import ChannelVariant
    >>> ChannelVariant.objects.filter(channel__kind="shop", publish=True)
```

## File: `apps/catalog/models/manufacturer.py`
```
Purpose:
    Represent manufacturer (brand or vendor) master data used in the catalog.
    Provides a stable numeric code and optional description for consistent
    brand identification across products and variants.

Context:
    Part of the `catalog` app. Serves as a reference table to associate
    products and variants with their brand/vendor for classification,
    reporting, and external integrations.

Fields:
    - manufacturer_code (SmallIntegerField, PK): Stable business code
      uniquely identifying the manufacturer.
    - manufacturer_description (CharField, max 200): Optional descriptive
      name or label for the manufacturer.

Relations:
    - Referenced by Product and ProductVariant models to indicate brand/vendor.

Used by:
    - Catalog (Product, ProductVariant)
    - Procurement and reporting modules requiring brand information

Depends on:
    - Django ORM

Example:
    >>> from apps.catalog.models import Manufacturer
    >>> Manufacturer.objects.create(manufacturer_code=101, manufacturer_description="ACME Tools")
    <Manufacturer: 101 — ACME Tools>
```

## File: `apps/catalog/models/origin.py`
```
Purpose:
    Define origin master data using a single-letter code.
    Provides a lightweight reference for categorizing products
    or variants by their origin or classification.

Context:
    Part of the `catalog` app. Serves as a reference/master table
    used in product variant definitions to tag items with an origin
    attribute for logistics, reporting, or integration purposes.

Fields:
    - origin_code (CharField, PK, length=1): Unique single-letter code
      identifying the origin.
    - origin_description (CharField, max 100): Optional descriptive
      label or name for the origin.

Relations:
    - Referenced by ProductVariant and potentially other catalog models
      to denote the origin classification of an item.

Used by:
    - Catalog (ProductVariant)
    - Any downstream reporting or integration requiring origin info

Depends on:
    - Django ORM

Example:
    >>> from apps.catalog.models import Origin
    >>> Origin.objects.create(origin_code="E", origin_description="Europe")
    <Origin: E — Europe>
```

## File: `apps/catalog/models/packing.py`
```
Purpose:
    Define packaging unit master data within an organization.
    Each record specifies how items are packed (e.g., single piece,
    box of 10, pallet), including codes, multipliers, and descriptions.

Context:
    Part of the `catalog` app. Used in product and procurement workflows
    to enforce packaging rules for ordering, stock management, and logistics.

Fields:
    - id (AutoField): Surrogate primary key (SERIAL in SQL).
    - organization (FK → core.Organization): Owning organization,
      ensures tenant isolation.
    - packing_code (SmallIntegerField): Business code identifying
      the packing unit within an organization.
    - amount (DecimalField, NUMERIC(10,3)): Multiplier for this unit
      (default 1.000, e.g. "box of 10").
    - packing_short_description (CharField, max 20): Short label for display.
    - packing_description (CharField, max 200): Longer optional description.

Relations:
    - Organization → multiple Packing definitions.
    - Referenced by ProductVariant or Procurement models for correct packaging
      and order handling.

Used by:
    - Catalog (ProductVariant definition)
    - Procurement (ordering logic, minimum order units)

Depends on:
    - Django ORM
    - core.Organization

Example:
    >>> from apps.catalog.models import Packing
    >>> Packing.objects.create(
    ...     organization=org,
    ...     packing_code=10,
    ...     amount=Decimal("10.000"),
    ...     packing_short_description="Box of 10",
    ... )
    <Packing: 10 — Box of 10>
```

## File: `apps/catalog/models/product.py`
```
Purpose:
    Define master product data shared across all variants.
    Stores catalog-wide attributes such as name, manufacturer,
    part number, SEO metadata, and marketing flags.

Context:
    Part of the `catalog` app. Products serve as the base entity for
    all sellable variants (ProductVariant) and are referenced by
    channel-specific models. Provides a stable anchor for procurement,
    pricing, and shop integration.

Fields:
    - id (AutoField): Primary key.
    - organization (FK → core.Organization): Owning organization.
    - name (CharField, 200): Human-readable product name.
    - slug (CharField, 200): Unique slug within an organization.
    - manufacturer (FK → catalog.Manufacturer): Brand or vendor.
    - manufacturer_part_number (CharField, 100): Raw part number.
    - manufacturer_part_number_norm (GeneratedField, 100): Normalized part
      number, computed via PostgreSQL `REGEXP_REPLACE`.
    - product_group (FK → catalog.ProductGroup): Classification/group.
    - description (TextField): Long product description, optional.
    - meta_title / meta_description / keywords: SEO fields.
    - is_new (Boolean): Marketing flag (new release).
    - is_closeout (Boolean): Marketing flag (discontinued).
    - release_date (DateField): Release information.
    - is_active (Boolean): Availability flag.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple Products.
    - Manufacturer → multiple Products.
    - ProductGroup → multiple Products.
    - Referenced by ProductVariant and ChannelVariant.

Used by:
    - Catalog (ProductVariant definitions).
    - Pricing and Procurement modules.
    - External integrations (shop systems, supplier APIs).

Depends on:
    - Django ORM
    - core.Organization
    - catalog.Manufacturer
    - catalog.ProductGroup

Example:
    >>> from apps.catalog.models import Product
    >>> Product.objects.filter(
    ...     organization__org_code=1,
    ...     is_active=True,
    ...     is_closeout=False,
    ... )
```

## File: `apps/catalog/models/product_group.py`
```
Purpose:
    Represents a grouping of products within an organization.
    Each group is identified by a short code and description.

Context:
    Part of the `catalog` app. ProductGroups provide a logical structure
    for organizing Products. Every Product must belong to one ProductGroup.
    Used in imports, seeding, and catalog management.

Fields:
    - id (AutoField): Primary key.
    - organization (FK → core.Organization): Owning organization.
    - product_group_code (CharField, 20): Unique code per organization.
    - product_group_description (CharField, 200): Optional human-readable label.

Relations:
    - Organization → multiple ProductGroups.
    - ProductGroup → multiple Products (via FK in Product).

Used by:
    - apps/catalog/models/product.py (FK to ProductGroup).
    - Import and seeding services that build catalog structures.

Depends on:
    - Django ORM
    - core.Organization

Example:
    >>> from apps.catalog.models import ProductGroup
    >>> pg = ProductGroup.objects.create(
    ...     organization=org,
    ...     product_group_code="FILTERS",
    ...     product_group_description="Air and oil filters"
    ... )
    >>> print(pg)
    FILTERS — Air and oil filters
```

## File: `apps/catalog/models/product_media.py`
```
Purpose:
    Stores media assets (images, videos, documents) for products and variants.
    Each entry represents one media file with metadata, linked either to a
    Product or to a specific ProductVariant.

Context:
    Part of the `catalog` app. Used to manage product images, thumbnails,
    and other media for display in shop systems and marketplaces.

Fields:
    - id (BigAutoField): Primary key.
    - organization (FK → core.Organization): Owner of the media record.
    - product (FK → catalog.Product): Product to which this media belongs.
    - variant (FK → catalog.ProductVariant, optional): Specific variant if media
      is variant-specific; otherwise null.
    - role (CharField, 20): Media role (e.g., "gallery", "thumbnail").
    - sort_order (SmallIntegerField): Ordering within the role group.
    - alt_text (CharField, 200): Alternative text for accessibility/SEO.
    - media_url (TextField): URL to the media file (e.g., CDN link).
    - mime (CharField, 100): MIME type if available (e.g., image/jpeg).
    - width_px / height_px (IntegerField): Dimensions of the media (optional).
    - file_size (IntegerField): File size in bytes (optional).
    - is_active (BooleanField): Active flag for filtering.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple ProductMedia
    - Product → multiple ProductMedia
    - ProductVariant → multiple ProductMedia (optional)

Used by:
    - apps.catalog.models.Product (reverse FK)
    - apps.catalog.models.ProductVariant (reverse FK)
    - API / frontend layers for rendering product galleries

Depends on:
    - core.Organization
    - catalog.Product
    - catalog.ProductVariant

Example:
    >>> from apps.catalog.models import ProductMedia
    >>> pm = ProductMedia.objects.create(
    ...     organization=org,
    ...     product=prod,
    ...     role="gallery",
    ...     media_url="https://cdn.example.com/img123.jpg",
    ...     alt_text="Front view of the product"
    ... )
    >>> print(pm)
    [org=1] product=123 gallery #1
```

## File: `apps/catalog/models/product_variant.py`
```
Purpose:
    Defines the ProductVariant entity, which represents a sellable unit (SKU).
    Captures identifiers, logistics data, order constraints, availability,
    and marketing attributes that extend the base Product.

Context:
    Belongs to the `catalog` app. Each ProductVariant links a Product with
    its Packing, Origin, and State. Variants are the concrete SKUs used for
    procurement, pricing, stock, and sales channel operations.

Fields:
    - organization (FK → core.Organization): Owning organization (multi-tenant scope).
    - product (FK → catalog.Product): The base product this variant belongs to.
    - packing (FK → catalog.Packing): Packaging unit of this variant.
    - origin (FK → catalog.Origin): Origin classification code.
    - state (FK → catalog.State): State classification code.
    - sku (CharField, 120): Internal stock-keeping unit identifier.
    - ean (CharField, 14): Standardized GTIN/EAN code (optional, indexed).
    - barcode (CharField, 64): Non-standard or supplier barcode (optional).
    - customs_code (IntegerField): Customs tariff number (optional).
    - weight / width / height / length (DecimalField): Logistics dimensions.
    - eclass_code (CharField, 16): International eCl@ss classification (optional).
    - stock_quantity / available_stock (IntegerField): Stock and availability data.
    - is_available (BooleanField): Availability flag from supplier API.
    - shipping_free (BooleanField): Free shipping flag.
    - min_purchase / max_purchase / purchase_steps (IntegerField): Order constraints.
    - is_topseller (BooleanField): Marketing flag for top seller status.
    - is_active (BooleanField): Whether this variant is active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple ProductVariants
    - Product → multiple ProductVariants
    - Packing → multiple ProductVariants
    - Origin → multiple ProductVariants
    - State → multiple ProductVariants
    - ProductVariant ↔ ChannelVariant (publish variants to channels)
    - ProductVariant ↔ SupplierProduct (procurement linkage)

Used by:
    - apps.catalog.models.Product
    - apps.catalog.models.ChannelVariant
    - apps.procurement.models.SupplierProduct
    - apps.pricing.models.SalesChannelVariantPrice

Depends on:
    - core.Organization
    - catalog.Product
    - catalog.Packing
    - catalog.Origin
    - catalog.State

Example:
    >>> from apps.catalog.models import ProductVariant
    >>> pv = ProductVariant.objects.create(
    ...     organization=org,
    ...     product=prod,
    ...     packing=pack,
    ...     origin=orig,
    ...     state=state,
    ...     sku="SKU-123",
    ...     ean="4006381333931",
    ...     weight="1.250",
    ... )
    >>> print(pv)
    [org=1] SKU=SKU-123 (product_id=42)
```

## File: `apps/catalog/models/state.py`
```
Purpose:
    Defines the State master data entity, represented by a single-letter code.
    Used to classify product variants by condition/state within the catalog.

Context:
    Part of the `catalog` app. Each ProductVariant references a State to
    indicate its condition (e.g., new, refurbished, used).

Fields:
    - state_code (CharField, 1, PK): Single-letter identifier of the state.
    - state_description (CharField, 100): Optional descriptive label.

Relations:
    - ProductVariant → references State via FK.

Used by:
    - apps.catalog.models.ProductVariant (FK relation via state)

Depends on:
    - Django ORM
    - core.Organization (indirectly via ProductVariant usage)

Example:
    >>> from apps.catalog.models import State
    >>> s = State.objects.create(state_code="N", state_description="New")
    >>> print(s)
    N — New
```

## File: `apps/catalog/services/channel_ops.py`
```
Purpose:
    Service layer for managing Channel records in a safe, reusable way.
    Provides an atomic upsert operation that ensures consistency across
    organizations and currencies.

Context:
    Channels represent sales or distribution endpoints (e.g., Webshop, Amazon,
    Point of Sale) and are always scoped to an organization with a base
    currency. This service is the programmatic counterpart to the seeding
    commands and is designed for use by other services, views, or ETL jobs.

Used by:
    - Import/ETL jobs synchronizing external channel definitions.
    - Admin features or APIs that create or update channels dynamically.
    - Test fixtures or bootstrap scripts needing idempotent channel setup.

Depends on:
    - apps.core.models.Organization
    - apps.core.models.Currency
    - apps.catalog.models.Channel

Key Features:
    - Idempotent upsert by (organization, channel_code).
    - Enforces required fields: org_code, channel_code, channel_name,
      base_currency_code.
    - Validates references to Organization and Currency.
    - Supports optional fields: kind (default "shop"), is_active (default True).
    - Trims string lengths to model constraints.

Example:
    >>> from apps.catalog.services.channel_ops import upsert_channel
    >>> ch, created = upsert_channel({
    ...     "org_code": 1,
    ...     "channel_code": "WEB",
    ...     "channel_name": "Webshop",
    ...     "base_currency_code": "EUR"
    ... })
    >>> print(ch.id, created)  # channel primary key, created=True/False
```

## File: `apps/catalog/services/channel_variant_ops.py`
```
Purpose:
    Service layer for managing ChannelVariant records. Provides a safe,
    reusable, and idempotent upsert interface for linking product variants
    to sales/distribution channels.

Context:
    A ChannelVariant represents the relationship between a sales channel
    (e.g., Webshop, Amazon) and a specific ProductVariant (SKU). It stores
    publishing state, external IDs, sync metadata, and activity flags.
    This service complements the seeding commands and is intended to be used
    by ETL jobs, admin features, or APIs.

Used by:
    - Import pipelines synchronizing product listings with external channels.
    - Admin operations or APIs that create/update channel listings.
    - Integration jobs that update publishing status or sync metadata.

Depends on:
    - apps.core.models.Organization
    - apps.catalog.models.Channel
    - apps.catalog.models.ProductVariant
    - apps.catalog.models.ChannelVariant

Key Features:
    - Atomic upsert by (organization, channel, variant).
    - Enforces required fields: org_code, channel_id, variant_id.
    - Supports optional flags and metadata:
        publish, is_active, need_shop_update,
        shop_product_id, shop_variant_id,
        last_synced_at, last_error, meta_json.
    - Raises ValidationError for missing required fields.

Example:
    >>> from apps.catalog.services.channel_variant_ops import upsert_channel_variant
    >>> payload = {
    ...     "org_code": 1,
    ...     "channel_id": 10,
    ...     "variant_id": 123,
    ...     "publish": True,
    ...     "is_active": True,
    ...     "need_shop_update": False,
    ...     "shop_product_id": "SKU-9999",
    ...     "shop_variant_id": "SKU-9999-V1",
    ...     "meta_json": {"synced_by": "import"},
    ... }
    >>> cv, created = upsert_channel_variant(payload)
    >>> print(cv.id, created)
```

## File: `apps/catalog/services/product_ops.py`
```
Purpose:
    Service layer for managing Product records. Provides a transactional,
    idempotent upsert function that enforces business keys and validates
    references to related entities.

Context:
    A Product represents a catalog entry tied to an Organization,
    Manufacturer, and optionally a ProductGroup. This service is designed
    to be used by import pipelines, admin features, or API endpoints to
    safely create or update product records.

Used by:
    - Seeding commands for products.
    - Import/ETL jobs that sync manufacturer data into the catalog.
    - Admin operations and APIs that create/update product definitions.

Depends on:
    - apps.core.models.Organization
    - apps.catalog.models.Manufacturer
    - apps.catalog.models.ProductGroup
    - apps.catalog.models.Product

Key Features:
    - Atomic upsert by (organization, manufacturer, manufacturer_part_number, slug).
    - Resolves foreign keys (Organization, Manufacturer, ProductGroup).
    - Enforces required fields: org_code, manufacturer_code,
      manufacturer_part_number, name, slug.
    - Optional fields: product_group_code, is_active.
    - Raises ValidationError for missing required fields.

Example:
    >>> from apps.catalog.services.product_ops import upsert_product
    >>> payload = {
    ...     "org_code": 1,
    ...     "manufacturer_code": 10,
    ...     "manufacturer_part_number": "ZX-9",
    ...     "name": "Widget ZX-9",
    ...     "slug": "widget-zx-9",
    ...     "product_group_code": "GRP01",
    ...     "is_active": True,
    ... }
    >>> p, created = upsert_product(payload)
    >>> print(p.id, created)
```

## File: `apps/catalog/services/variant_ops.py`
```
Purpose:
    Service layer for managing ProductVariant records. Provides a transactional,
    idempotent upsert function that supports both SKU-based and business-key–
    based selectors for flexible variant creation and updates.

Context:
    A ProductVariant (SKU) represents a specific sellable unit of a Product.
    Variants may differ by packing, origin, state, customs code, or barcode.
    This service abstracts the variant creation/update logic to enforce
    consistent handling across imports, admin features, and APIs.

Used by:
    - Import/ETL pipelines that generate or update SKUs.
    - Seeding scripts for initial data population.
    - Business logic that maintains catalog consistency.

Depends on:
    - apps.core.models.Organization
    - apps.catalog.models.Product
    - apps.catalog.models.ProductVariant
    - apps.catalog.models.Packing
    - apps.catalog.models.Origin
    - apps.catalog.models.State

Key Features:
    - Required fields: org_code, product_id.
    - Preferred selector: (org, sku).
    - Alternative selector: (org, product, packing, origin, state).
    - Generates a fallback SKU when not provided.
    - Resolves references to Packing, Origin, and State if codes are supplied.
    - Atomic transaction guarantees idempotency and consistency.
    - Raises ValidationError for missing required fields.

Example:
    >>> from apps.catalog.services.variant_ops import upsert_variant
    >>> payload = {
    ...     "org_code": 1,
    ...     "product_id": 1001,
    ...     "sku": "SKU-123",
    ...     "barcode": "4006381333931",
    ...     "packing_code": 2,
    ...     "origin_code": "E",
    ...     "state_code": "A",
    ...     "customs_code": 0,
    ...     "weight": "0.250",
    ...     "is_active": True,
    ... }
    >>> v, created = upsert_variant(payload)
    >>> print(v.id, created)
```

## File: `apps/core/management/commands/seed_currency.py`
```
Management command to seed or update Currency records in the database.

This command supports both direct item strings (via --items) and external
files (via --file). Each currency is defined in a compact colon-delimited
format:

    code:name[:symbol][:decimal_places][:active]

Arguments:
  --items   Comma-separated entries with the above format.
  --file    Path to a text file containing one entry per line.
  --dry-run Validate and parse input without persisting any changes.

Behavior:
  • Upserts currencies by primary key 'code' (ISO-4217).
  • Default values: symbol="", decimal_places=2, active=True.
  • Input is validated and trimmed to model field length constraints.
  • Provides summary of created/updated records or dry-run output.

Examples:
  python manage.py seed_currency --items "EUR:Euro:€:2,USD:US Dollar:$:2"
  python manage.py seed_currency --file scripts/currencies.txt
```

## File: `apps/core/management/commands/seed_organization.py`
```
Purpose:
    Management command to seed or update Organization rows from colon-delimited
    input or a file. Supports dry-run validation.

Context:
    Part of the `core` app. Used during initial setup or data imports to ensure
    organizations (mandants) exist in the database.

Used by:
    - Developers and ops during setup via `python manage.py seed_organization`
    - Other seed commands that require existing Organization rows (e.g. packing,
      product, product group)

Depends on:
    - apps.core.models.organization.Organization
    - Django transaction management
    - Standard management command infrastructure

Example:
    python manage.py seed_organization --items "1:Main Org,2:Test Mandant"
    python manage.py seed_organization --file scripts/organizations.txt
```

## File: `apps/core/models/currency.py`
```
Purpose:
    Reference table for ISO-4217 currencies.
    Stores currency code, name, symbol, decimal precision, and active status.

Context:
    Used throughout the system to enforce consistent currency handling
    (pricing, procurement, sales, finance).

Fields:
    - code (CharField, PK): ISO 4217 currency code (e.g., "USD", "EUR").
    - name (CharField): Full currency name (e.g., "US Dollar").
    - symbol (CharField): Display symbol (e.g., "$", "€").
    - decimal_places (SmallInteger): Allowed decimals (0–6; EUR=2).
    - is_active (Bool): Whether this currency is active.
    - created_at / updated_at: System timestamps, DB-managed.

Constraints:
    - decimal_places must be between 0 and 6.

Example:
    >>> from apps.core.models import Currency
    >>> eur = Currency.objects.create(code="EUR", name="Euro", symbol="€", decimal_places=2)
    >>> str(eur)
    'EUR — Euro'
```

## File: `apps/core/models/organization.py`
```
Purpose:
    Master data table for organizations (tenants/mandants).
    Provides a scoped context for all other business entities.

Context:
    Every business object (customer, supplier, product, pricing, etc.)
    is linked to an Organization via org_code.

Fields:
    - org_code (SmallInteger, PK): Unique code identifying the organization.
    - org_description (CharField): Optional description/name.

Constraints:
    - org_code is the primary key.
    - No additional constraints defined.

Example:
    >>> from apps.core.models import Organization
    >>> org = Organization.objects.create(org_code=1, org_description="Main Company")
    >>> str(org)
    'Main Company'
```

## File: `apps/imports/api/api_client_base.py`
```
Purpose:
    Provides a reusable base client for Store-API style integrations.
    Handles session setup, request headers, and POST requests with error handling.

Context:
    Part of the `imports` app. Serves as the common foundation for external
    API connectors (e.g. Shopware, suppliers). Ensures consistent logging,
    authentication, and error reporting.

Used by:
    - Specialized API clients in `apps/imports/api/` that inherit from BaseApiClient
    - Import services that need to fetch or push data to external systems

Depends on:
    - requests (HTTP session handling)
    - logging for structured error reporting
    - apps.imports.api.api_client_base.ApiError for request failures

Example:
    from apps.imports.api.api_client_base import BaseApiClient

    client = BaseApiClient(base_url="https://shop/api", access_key="xyz123")
    response = client._post("search/product", {"filter": []})
    print(response.status_code, response.json())
```

## File: `apps/imports/api/elsaesser_filter_client.py`
```
Purpose:
    Implements a dedicated API client for the Filter-Technik (Elsaesser) Shopware 6.6 Store API.
    Provides authentication, product lookup (by manufacturer number or SKU), and bulk fetch with pagination.

Context:
    Part of the `imports.api` module. Extends the shared `BaseApiClient`
    to handle supplier-specific login and product retrieval logic.
    Used to synchronize or import product master data from the external supplier system.

Used by:
    - Import pipelines in `apps/imports/services/` (for fetching supplier catalog data)
    - Management commands for seeding or updating product data
    - Developers (manual CLI execution in `__main__` for testing integration)

Depends on:
    - apps.imports.api.api_client_base.BaseApiClient (HTTP logic, headers, error handling)
    - requests (for HTTP communication)
    - logging and traceback for error/debug output
    - Shopware 6.6 Store API (Filter-Technik endpoint)

Example:
    from apps.imports.api.elsaesser_filter_client import FilterTechnikApiClient

    client = FilterTechnikApiClient(
        base_url="https://www.filter-technik.de/store-api",
        access_key="ACCESS_KEY",
        username="user@example.com",
        password="secret"
    )
    client.login()
    product = client.get_product_by_sku("SKU-12345")
    print(product)
```

## File: `apps/imports/management/commands/import_elsaesser.py`
```
Purpose:
    Management command to import products from the Elsässer Filter-Technik Store API
    into the database. Products are first logged in `ImportRun` and stored as raw JSON
    payloads in `ImportRawRecord` for further processing.

Context:
    Part of the `apps.imports` app. Runs as a Django management command.
    Used to synchronize supplier catalogs into the import pipeline.
    Supports dry-run mode for previewing data without database writes.

Used by:
    - Developers (manual execution via `python manage.py import_elsaesser`)
    - Automated import jobs (cron / scheduled tasks)
    - Downstream services that consume `ImportRun` and `ImportRawRecord`

Depends on:
    - apps.imports.api.elsaesser_filter_client.FilterTechnikApiClient (API access)
    - apps.imports.models.ImportRun (import session tracking)
    - apps.imports.models.ImportRawRecord (raw product payloads)
    - apps.imports.models.ImportSourceType (to classify source type)
    - apps.partners.models.Supplier (supplier reference)
    - Django transaction management and logging

Example:
    # Dry run: fetch and preview 50 products without DB writes
    python manage.py import_elsaesser --supplier ELS01 --dry-run --limit 50

    # Real import: insert all products for supplier 'ELS01'
    python manage.py import_elsaesser --supplier ELS01
```

## File: `apps/imports/management/commands/import_komatsu.py`
```
Purpose:
    Management command to import Komatsu product data from Excel files into
    `ImportRun` and `ImportRawRecord`. Supports both automatic detection of
    the newest file and explicit file path overrides.

Context:
    Part of the `apps.imports` app. Runs as a Django management command.
    Used to bring supplier Excel catalogs into the import pipeline, with
    validation and dry-run support.

Used by:
    - Developers (manual execution via `python manage.py import_komatsu`)
    - Automated import jobs (scheduled data ingestion)
    - Downstream processing tasks that consume `ImportRun` and `ImportRawRecord`

Depends on:
    - pandas (Excel parsing)
    - apps.imports.models.ImportRun (import session tracking)
    - apps.imports.models.ImportRawRecord (raw Excel rows storage)
    - apps.imports.models.ImportSourceType (to classify source type)
    - apps.partners.models.Supplier (supplier reference)
    - Django transaction management and logging

Example:
    # Auto-detect newest file and import
    python manage.py import_komatsu --supplier SUPP01

    # Dry run (preview up to 20 rows, no DB changes)
    python manage.py import_komatsu --supplier SUPP01 --dry-run

    # Import specific file
    python manage.py import_komatsu --supplier SUPP01 --file apps/imports/data/SUPP01/2025/08/komatsu_06-25.xlsx
```

## File: `apps/imports/management/commands/seed_import_data_types.py`
```
Purpose:
    Management command to seed default data types (str, int, decimal, bool, date, datetime)
    into the `ImportDataType` table. Ensures the system has the required baseline
    for describing import field types.

Context:
    Part of the `apps.imports` app. Used during initial setup or migrations
    to populate the database with standard import data types.

Used by:
    - Developers (manual execution via `python manage.py seed_import_data_types`)
    - Initial project setup scripts
    - Any process that relies on consistent `ImportDataType` definitions

Depends on:
    - apps.imports.models.import_data_type.ImportDataType
    - Django management command framework

Example:
    # Seed default data types
    python manage.py seed_import_data_types
```

## File: `apps/imports/management/commands/seed_import_defaults.py`
```
Purpose:
    Management command to seed an `ImportGlobalDefaultSet` with related
    `ImportGlobalDefaultLine` entries. Ensures organizations have baseline
    default mappings for import processing.

Context:
    Part of the `apps.imports` app. Used during system setup or onboarding
    to initialize import defaults for a given organization.

Used by:
    - Developers and operators via `python manage.py seed_import_defaults`
    - Import processing logic that relies on a default set of rules

Depends on:
    - apps.core.models.organization.Organization
    - apps.imports.services.import_defaults_ops.seed_initial_defaults
    - Django management command framework

Example:
    # Seed defaults for first organization (today as valid_from)
    python manage.py seed_import_defaults

    # Seed defaults for organization 1, with explicit date
    python manage.py seed_import_defaults --org 1 --valid-from 2025-01-01
```

## File: `apps/imports/management/commands/seed_import_source_types.py`
```
Purpose:
    Management command to seed default `ImportSourceType` records. Ensures
    consistent source type classification for imports (file, API, manual, other).

Context:
    Part of the `apps.imports` app. Used during system setup or migrations
    to initialize baseline source type records.

Used by:
    - Developers and operators via `python manage.py seed_import_source_types`
    - Import commands that require a valid ImportSourceType reference
      (e.g., `import_komatsu`, `import_elsaesser`)

Depends on:
    - apps.imports.models.import_source_type.ImportSourceType
    - Django management command framework

Example:
    # Seed all default import source types
    python manage.py seed_import_source_types
```

## File: `apps/imports/management/commands/seed_import_transform_types.py`
```
Purpose:
    Management command to seed the `ImportTransformType` table with
    predefined transformation types (e.g., uppercase, lowercase, int, decimal).
    Ensures that import pipelines have a consistent set of transform functions.

Context:
    Part of the `apps.imports` app. Used during setup or migrations
    to initialize transformation options for import processing.

Used by:
    - Developers and operators via `python manage.py seed_import_transform_types`
    - Import pipeline services that apply transformation rules on raw values

Depends on:
    - apps.imports.models.import_transform_type.ImportTransformType
    - Django management command framework

Example:
    # Seed all default transform types
    python manage.py seed_import_transform_types
```

## File: `apps/imports/management/commands/universal_excel_importer.py`
```
Purpose:
    Generic Excel importer that loads spreadsheet rows into ImportRawRecord.
    Performs no field mapping — it only stores cleaned raw rows as JSON for later
    supplier-specific transformation.

Context:
    Part of the `apps.imports` app. Used to handle bulk uploads of supplier Excel files
    and to initialize raw import runs in a standardized way.

Used by:
    - Operators via `python manage.py universal_excel_importer`
    - Downstream import pipeline services that map raw records to business objects

Depends on:
    - apps.imports.models.import_run.ImportRun
    - apps.imports.models.import_raw_record.ImportRawRecord
    - apps.imports.models.import_source_type.ImportSourceType
    - apps.partners.models.supplier.Supplier
    - pandas for reading Excel files

Example:
    # Preview 20 rows without persisting them
    python manage.py universal_excel_importer --supplier SUPP01 --dry-run

    # Import the latest Excel file for a supplier
    python manage.py universal_excel_importer --supplier SUPP01
```

## File: `apps/imports/models/import_data_type.py`
```
Purpose:
    Defines the available datatypes for mapping and transformation during imports.
    Ensures consistent typing when parsing external data sources into the system.

Context:
    Part of the `imports` app. Used by the import framework to validate and
    transform incoming values into the correct Python representation.

Fields:
    - code (CharField, 30, unique): Short code identifier (e.g., "str", "int", "decimal").
    - description (CharField, 100): Human-readable label for the type.
    - python_type (CharField, 50): Python type or handler string (e.g., "decimal.Decimal").

Relations:
    - No direct foreign keys. Acts as a reference/master table.

Used by:
    - Import pipeline and mapping services to resolve field datatypes.
    - Validation logic for ensuring correct type conversion.

Depends on:
    - Django ORM

Example:
    >>> from apps.imports.models import ImportDataType
    >>> t = ImportDataType.objects.create(
    ...     code="bool",
    ...     description="Boolean",
    ...     python_type="bool"
    ... )
    >>> print(t)
    bool (Boolean)
```

## File: `apps/imports/models/import_error_log.py`
```
Purpose:
    Logs errors that occur during the import process while transforming
    raw records into structured ERP tables.

Context:
    Part of the `imports` app. Provides visibility into failures when
    processing ImportRawRecord entries inside an ImportRun.

Fields:
    - import_run (FK → imports.ImportRun): The run during which the error occurred.
    - line_number (IntegerField, nullable): Source line number in the raw file.
    - error_message (TextField): Description of the error encountered.
    - payload (JSONField, nullable): Optional snapshot of the input data.
    - created_at (DateTimeField): Timestamp when the error was logged.

Relations:
    - ImportRun → multiple ImportErrorLogs

Used by:
    - Import framework to persist errors for later inspection.
    - Admin/UI for debugging failed imports.

Depends on:
    - apps.imports.models.ImportRun
    - Django ORM

Example:
    >>> from apps.imports.models import ImportErrorLog, ImportRun
    >>> run = ImportRun.objects.first()
    >>> ImportErrorLog.objects.create(
    ...     import_run=run,
    ...     line_number=42,
    ...     error_message="Invalid price format",
    ...     payload={"sku": "X123", "price": "abc"}
    ... )
    <ImportErrorLog: Error in run 1 line 42: Invalid price format>
```

## File: `apps/imports/models/import_global_default_line.py`
```
Purpose:
    Represents a single line entry within a global default set for imports.
    Each line maps a target field path to a default value, optionally with
    a transform and enforced datatype.

Context:
    Belongs to the imports domain. Used when building base dictionaries of
    defaults (e.g., for products, variants, suppliers) before mapping raw
    import data. Provides consistent fallback values across an organization.

Fields:
    - set (FK → ImportGlobalDefaultSet): The owning default set.
    - target_path (CharField, 255): Path of the field (e.g., "product.name").
    - default_value (JSONField): The fallback value for this path.
    - transform (FK → ImportTransformType): Optional transform to apply.
    - is_required (BooleanField): Whether the field must be present.
    - target_datatype (FK → ImportDataType): Defines the expected datatype.

Relations:
    - ImportGlobalDefaultSet → multiple ImportGlobalDefaultLine
    - ImportTransformType → multiple ImportGlobalDefaultLine
    - ImportDataType → multiple ImportGlobalDefaultLine

Used by:
    - apps/imports/services/defaults.py (build_base_dict, applying defaults)

Depends on:
    - apps.imports.models.import_global_default_set.ImportGlobalDefaultSet
    - apps.imports.models.import_data_type.ImportDataType
    - apps.imports.models.import_transform_type.ImportTransformType

Example:
    >>> from apps.imports.models import ImportGlobalDefaultLine
    >>> line = ImportGlobalDefaultLine.objects.create(
    ...     set=default_set,
    ...     target_path="product.state_code",
    ...     default_value="active",
    ...     target_datatype=dt_str
    ... )
    >>> print(line)
    product.state_code = active
```

## File: `apps/imports/models/import_global_default_set.py`
```
Purpose:
    Represents the head record for global default configurations that apply
    to all suppliers within an organization. Each set has a description and
    validity date that determines which defaults are active at a given time.

Context:
    Part of the imports domain. Used as a container for multiple
    ImportGlobalDefaultLine entries that define specific default values.
    Provides versioning of defaults by validity period.

Fields:
    - organization (FK → core.Organization): Owner of the default set.
    - description (CharField, 255): Human-readable description.
    - valid_from (DateField): Start date from which the defaults are active.
    - created_at (DateTimeField): Timestamp when the set was created.

Relations:
    - Organization → multiple ImportGlobalDefaultSet
    - ImportGlobalDefaultSet → multiple ImportGlobalDefaultLine

Used by:
    - apps/imports/services/defaults.py (get_active_default_set, build_base_dict)

Depends on:
    - apps.core.models.Organization
    - apps.imports.models.import_global_default_line.ImportGlobalDefaultLine

Example:
    >>> from apps.imports.models import ImportGlobalDefaultSet
    >>> default_set = ImportGlobalDefaultSet.objects.create(
    ...     organization=org,
    ...     description="Default product values",
    ...     valid_from="2025-01-01",
    ... )
    >>> print(default_set)
    Default product values (from 2025-01-01)
```

## File: `apps/imports/models/import_map_detail.py`
```
Purpose:
    Represents a single mapping rule that defines how a field from the source
    import payload is transformed and assigned to a standardized target path.

Context:
    Part of the imports domain. Each ImportMapDetail belongs to an
    ImportMapSet, forming a collection of rules that describe how to
    process supplier or external data into the ERP structure.

Fields:
    - map_set (FK → ImportMapSet): Parent set grouping related map details.
    - source_path (CharField, 255): Path of the source field in the raw payload.
    - target_path (CharField, 255): Path in the standardized dict where the
      value will be stored.
    - target_datatype (FK → ImportDataType): Datatype the value should be
      converted to.
    - transform (CharField, 50, nullable): Optional transformation to apply
      (e.g., uppercase, decimal).
    - is_required (BooleanField): Marks if the target field is mandatory.

Relations:
    - ImportMapSet → multiple ImportMapDetail
    - ImportDataType → multiple ImportMapDetail

Used by:
    - Import processing pipeline to transform raw supplier data.
    - apps.imports.services.transform_utils.apply_transform

Depends on:
    - apps.imports.models.import_map_set.ImportMapSet
    - apps.imports.models.import_data_type.ImportDataType

Example:
    >>> from apps.imports.models import ImportMapDetail, ImportMapSet, ImportDataType
    >>> dt = ImportDataType.objects.get(code="decimal")
    >>> ms = ImportMapSet.objects.first()
    >>> detail = ImportMapDetail.objects.create(
    ...     map_set=ms,
    ...     source_path="Listenpreis",
    ...     target_path="price.price",
    ...     target_datatype=dt,
    ...     transform="decimal",
    ...     is_required=True,
    ... )
    >>> print(detail)
    Listenpreis → price.price (decimal)
```

## File: `apps/imports/models/import_map_set.py`
```
Purpose:
    Represents a configuration set that defines how raw import data from a
    supplier and source type should be mapped into the ERP structure.

Context:
    Part of the imports domain. Each ImportMapSet groups multiple
    ImportMapDetail entries that specify field-level mapping rules.
    Defines which mapping applies for a given supplier and source type,
    with a start date of validity.

Fields:
    - organization (FK → core.Organization): The organization this mapping belongs to.
    - supplier (FK → partners.Supplier): The supplier providing the import data.
    - source_type (FK → imports.ImportSourceType): The type of import source (file, API, etc.).
    - description (CharField, 255): Human-readable description of the mapping set.
    - valid_from (DateField): Date from which this mapping is effective.
    - created_at (DateTimeField): Timestamp when the mapping set was created.

Relations:
    - Organization → multiple ImportMapSet
    - Supplier → multiple ImportMapSet
    - ImportSourceType → multiple ImportMapSet
    - ImportMapSet → multiple ImportMapDetail (child rules)

Used by:
    - Import processing engine to determine which mapping rules to apply
      for supplier imports.
    - apps.imports.models.import_map_detail.ImportMapDetail

Depends on:
    - apps.core.models.Organization
    - apps.partners.models.Supplier
    - apps.imports.models.import_source_type.ImportSourceType

Example:
    >>> from apps.imports.models import ImportMapSet
    >>> ms = ImportMapSet.objects.create(
    ...     organization=org,
    ...     supplier=supplier,
    ...     source_type=src_type,
    ...     description="Default CSV mapping",
    ...     valid_from="2025-01-01",
    ... )
    >>> print(ms)
    SUPP01 / file (from 2025-01-01)
```

## File: `apps/imports/models/import_raw_record.py`
```
Purpose:
    Stores raw unmodified data from supplier or customer imports. Acts as the
    first persistence layer for payloads before transformation or validation.

Context:
    Belongs to the imports domain. Each ImportRawRecord links to an ImportRun
    and captures a single line/item from the input (JSON, XML, CSV, etc.).
    Used for auditing, debugging, error handling, and retries.

Fields:
    - import_run (FK → ImportRun): The import run this record belongs to.
    - line_number (IntegerField): Sequential number within the run (starting at 1).
    - payload (JSONField): Full raw payload from the external source.
    - supplier_product_reference (CharField, 255, optional): Supplier’s identifier
      (SKU, part number) for fast lookup.
    - product_is_imported / price_is_imported (BooleanField): Flags whether
      this record was successfully imported into ERP/price tables.
    - product_imported_at / price_imported_at (DateTimeField, optional): Timestamps
      for successful imports.
    - is_product_import_error / is_price_import_error (BooleanField): Flags whether
      import attempts failed.
    - error_message_product_import / error_message_price_import (TextField, optional):
      Detailed error messages for failed imports.
    - retry_count_product_import / retry_count_price_import (PositiveIntegerField):
      Number of retries attempted for this record.

Relations:
    - ImportRun → multiple ImportRawRecord (1:n).

Used by:
    - Import pipelines for auditing, retry handling, and debugging.
    - Error logging/reporting systems.

Depends on:
    - apps.imports.models.ImportRun

Example:
    >>> from apps.imports.models import ImportRawRecord, ImportRun
    >>> run = ImportRun.objects.first()
    >>> rec = ImportRawRecord.objects.create(
    ...     import_run=run,
    ...     line_number=1,
    ...     payload={"Part Number": "X123", "Price": "12.50"},
    ...     supplier_product_reference="X123",
    ... )
    >>> print(rec)
    Run 1, line 1, ref=X123
```

## File: `apps/imports/models/import_run.py`
```
Purpose:
    Represents a single supplier import execution (header record).
    Tracks metadata about the run, including timing, status, source, and counts.

Context:
    Belongs to the imports domain. Each ImportRun serves as the parent entity
    for ImportRawRecord entries and error logs. Used to monitor the lifecycle
    of an import job.

Fields:
    - supplier (FK → Supplier): Supplier this run belongs to.
    - source_type (FK → ImportSourceType): Type of source (e.g., file, API, CSV).
    - source_file (CharField, 500, optional): Path or identifier of the imported file.
    - started_at (DateTimeField): Timestamp when the import started.
    - finished_at (DateTimeField, optional): Timestamp when the import finished.
    - status (CharField, 20): Run status ("running", "success", "failed").
    - total_records (IntegerField, optional): Number of raw records fetched.
    - is_processed (BooleanField): Whether the run has been processed into ERP tables.
    - processed_at (DateTimeField, optional): Timestamp when records were processed.

Relations:
    - Supplier → multiple ImportRuns (1:n).
    - ImportRun → multiple ImportRawRecord (1:n).
    - ImportRun → multiple ImportErrorLog (1:n).

Used by:
    - Import pipelines for execution tracking and reporting.
    - Error logging and auditing mechanisms.

Depends on:
    - apps.partners.models.Supplier
    - apps.imports.models.ImportSourceType

Example:
    >>> from apps.imports.models import ImportRun
    >>> run = ImportRun.objects.create(
    ...     supplier=supplier,
    ...     source_type=source_type,
    ...     source_file="/imports/supplier_2025-01.csv"
    ... )
    >>> print(run)
    ImportRun 1 — SUPPLIERX at 2025-01-10 12:00
```

## File: `apps/imports/models/import_source_type.py`
```
Purpose:
    Defines available import source types (e.g., file, API, manual).
    Serves as a reference table for categorizing import runs and mappings.

Context:
    Part of the imports domain. Each ImportRun references an ImportSourceType
    to indicate where the data originated from. Used in mapping and logging.

Fields:
    - code (CharField, 20, unique): Short identifier (e.g., "file", "api").
    - description (CharField, 100): Human-readable description.

Relations:
    - ImportSourceType → multiple ImportRuns (1:n).
    - ImportSourceType → multiple ImportMapSets (1:n).

Used by:
    - ImportRun (source_type FK).
    - ImportMapSet (source_type FK).

Depends on:
    - Django ORM (constraints, unique checks).

Example:
    >>> from apps.imports.models import ImportSourceType
    >>> t = ImportSourceType.objects.create(code="file", description="File Import")
    >>> print(t)
    file — File Import
```

## File: `apps/imports/models/import_transform_type.py`
```
Purpose:
    Registry of supported transformation functions used in import mapping.
    Provides a unique code and description for each transform.

Context:
    Part of the imports domain. Transform types define how raw values
    from import payloads should be processed before saving.

Fields:
    - code (CharField, 50, unique): Identifier of the transform (e.g., "uppercase", "int").
    - description (CharField, 255): Human-readable description of the transformation.

Relations:
    - ImportTransformType → multiple ImportGlobalDefaultLines (1:n).
    - ImportTransformType → used in mapping definitions (FKs).

Used by:
    - ImportGlobalDefaultLine (transform FK).
    - Mapping and ETL logic to dynamically apply transforms.

Depends on:
    - Django ORM.

Example:
    >>> from apps.imports.models import ImportTransformType
    >>> t = ImportTransformType.objects.create(code="uppercase", description="Convert text to upper case")
    >>> print(t)
    uppercase — Convert text to upper case
```

## File: `apps/imports/services/defaults.py`
```
Purpose:
    Provides utilities for retrieving and assembling active global default sets
    into structured dictionaries for use during import processing.

Context:
    Part of the `apps.imports.services` package.
    Used to look up ImportGlobalDefaultSet entries and group their lines
    (e.g., product, variant, price, supplier, supplier_product) into nested dicts.

Used by:
    - Import pipelines and services that need a ready-to-use defaults dictionary
    - Local testing (via __main__ execution)

Depends on:
    - apps.imports.models.import_global_default_set.ImportGlobalDefaultSet
    - Django ORM for querying active default sets
    - django.utils.timezone for date comparison

Example:
    from apps.imports.services.defaults import build_base_dict

    base_dict = build_base_dict(org_id=1)
    print(base_dict["product"]["name"])
```

## File: `apps/imports/services/import_defaults_ops.py`
```
Purpose:
    Service functions to create and manage ImportGlobalDefaultSet and
    ImportGlobalDefaultLine entries. Provides helpers for seeding a
    baseline of default values used during the import pipeline.

Context:
    Part of the `apps.imports.services` package.
    Encapsulates default handling logic so that management commands
    (e.g. seed_import_defaults) can reuse it consistently.

Used by:
    - apps/imports/management/commands/seed_import_defaults.py
    - Any future import pipelines requiring baseline defaults

Depends on:
    - apps.imports.models.import_global_default_set.ImportGlobalDefaultSet
    - apps.imports.models.import_global_default_line.ImportGlobalDefaultLine
    - apps.imports.models.import_data_type.ImportDataType
    - apps.core.models.organization.Organization
    - Django transaction management

Example:
    from apps.imports.services import import_defaults_ops as ops
    from apps.core.models.organization import Organization
    from datetime import date

    org = Organization.objects.first()
    default_set, created = ops.seed_initial_defaults(org, date.today())
    print(default_set.id, created)
```

## File: `apps/imports/services/transform_utils.py`
```
Purpose:
    Utility functions for applying transformations to raw import values
    (string normalization, type conversion, boolean parsing, etc.).

Context:
    Part of the `apps.imports.services` package.
    Used to enforce consistent transformations across import pipelines
    based on configured ImportTransformType entries.

Used by:
    - apps/imports/services/import_defaults_ops.py
    - Any importer or service applying ImportTransformType mappings

Depends on:
    - apps.imports.models.import_transform_type.ImportTransformType
    - Python stdlib: decimal.Decimal for numeric conversion

Example:
    from apps.imports.services.transform_utils import apply_transform
    from apps.imports.models.import_transform_type import ImportTransformType

    transform = ImportTransformType(code="uppercase")
    result = apply_transform("hello", transform)
    print(result)  # "HELLO"
```

## File: `apps/partners/management/commands/seed_suppliers.py`
```
Purpose:
    Management command to upsert Supplier records into the database based on
    colon-delimited input. Supports parsing and validation of supplier data
    and ensures idempotent updates.

Context:
    Part of the `apps.partners.management.commands` package.
    Used to populate or refresh suppliers for a given organization during
    bootstrapping, testing, or data migrations.

Used by:
    - Manual execution via `python manage.py seed_suppliers`
    - Setup scripts for initializing suppliers in development/test environments

Depends on:
    - apps.core.models.organization.Organization
    - apps.partners.models.supplier.Supplier
    - Django ORM (update_or_create, transaction.atomic)

Example:
    # Create a default test supplier (inactive)
    python manage.py seed_suppliers --items "1:SUPP01:Default dummy Supplier:0"

    # Create multiple suppliers (active + inactive)
    python manage.py seed_suppliers --items "1:SUPP01:Main Supplier:1,1:SUPP02:Backup Supplier:0"
```

## File: `apps/partners/models/customer.py`
```
Purpose:
    Represents customer master data within an organization.
    Each customer is uniquely identified by a customer code and
    may include contact and billing information.

Context:
    Part of the partners app. Customers are organizationally scoped
    entities used for sales, invoicing, and integrations.

Fields:
    - organization (FK → core.Organization): Owning organization.
    - customer_code (CharField, 20): Unique customer code per organization.
    - is_active (BooleanField): Flag to indicate if the customer is active.
    - customer_description (CharField, 200): Optional description/name.
    - contact_name (CharField, 100): Primary contact person.
    - email (CharField, 200): Contact email address.
    - phone (CharField, 50): Primary phone number.
    - website (CharField, 200): Website URL.
    - tax_id (CharField, 50): Tax or VAT identifier.
    - address_line1 (CharField, 200): Address line 1.
    - address_line2 (CharField, 200): Address line 2.
    - postal_code (CharField, 20): Postal or ZIP code.
    - city (CharField, 100): City name.
    - country_code (CharField, 2): ISO 3166-1 alpha-2 code.
    - payment_terms (CharField, 50): Payment term shorthand (e.g., NET30).
    - comment (CharField, 200): Optional internal comment.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple Customers

Used by:
    - Sales, invoicing, procurement, and integration modules.

Depends on:
    - apps.core.models.Organization
    - Django ORM

Example:
    >>> from apps.partners.models import Customer
    >>> c = Customer.objects.create(
    ...     organization=org,
    ...     customer_code="CUST001",
    ...     customer_description="ACME Corp",
    ...     email="contact@acme.com"
    ... )
    >>> print(c)
    CUST001 — ACME Corp
```

## File: `apps/partners/models/supplier.py`
```
Purpose:
    Represents supplier master data within an organization.
    Each supplier is uniquely identified by a supplier code and
    may include commercial, contact, and logistical information.

Context:
    Part of the partners app. Suppliers are organizationally scoped
    entities used for procurement, import mapping, and integrations.

Fields:
    - organization (FK → core.Organization): Owning organization.
    - supplier_code (CharField, 20): Unique supplier code per organization.
    - is_active (BooleanField): Whether the supplier is active.
    - supplier_description (CharField, 200): Optional description/name.
    - contact_name (CharField, 100): Primary contact person.
    - email (CharField, 200): Contact email address.
    - phone (CharField, 50): Primary phone number.
    - website (CharField, 200): Website URL.
    - tax_id (CharField, 50): Tax/VAT identifier.
    - address_line1 (CharField, 200): Address line 1.
    - address_line2 (CharField, 200): Address line 2.
    - postal_code (CharField, 20): Postal/ZIP code.
    - city (CharField, 100): City name.
    - country_code (CharField, 2): ISO 3166-1 alpha-2 code.
    - payment_terms (CharField, 50): Payment term shorthand (e.g., NET30).
    - is_preferred (BooleanField): Whether marked as preferred supplier.
    - lead_time_days (SmallIntegerField): Typical lead time in days.
    - comment (CharField, 200): Optional internal comment.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple Suppliers

Used by:
    - Procurement workflows
    - Import mapping (apps/imports)
    - Inventory and purchase order processing

Depends on:
    - apps.core.models.Organization
    - Django ORM

Example:
    >>> from apps.partners.models import Supplier
    >>> s = Supplier.objects.create(
    ...     organization=org,
    ...     supplier_code="SUP001",
    ...     supplier_description="MegaParts Ltd.",
    ...     email="sales@megaparts.com"
    ... )
    >>> print(s)
    SUP001 — MegaParts Ltd.
```

## File: `apps/partners/services/filtertechnik_api.py`
```
Purpose:
    Service client for interacting with the Filter-Technik (Shopware Store-API).
    Handles context token retrieval and provides helper methods to fetch product
    data, e.g. by SKU.

Context:
    Located in `apps.partners.services`. This client is used by importers and
    partner integrations to query live product data from the Filter-Technik API.

Used by:
    - Import commands (e.g., `import_elsaesser`)
    - Partner services or background jobs needing product lookups

Depends on:
    - requests (HTTP requests to the Shopware Store-API)
    - Python stdlib (uuid, traceback)

Example:
    client = FilterTechnikApiClient(
        base_url="https://www.filter-technik.de/store-api",
        access_key="SWSCQU9ZETYXSGPTB2DSAFM2WQ"
    )
    client.ensure_context()
    product = client.get_product_by_sku("12345")
    print(product)
```

## File: `apps/partners/services/supplier_ops.py`
```
Purpose:
    Service functions to upsert (create or update) Supplier records in the database.
    Encapsulates supplier persistence logic in a reusable API for other services.

Context:
    Located in `apps.partners.services`. Provides write-access operations on the
    Supplier model, independent of management commands or imports.

Used by:
    - Seed commands (e.g., `seed_suppliers`)
    - Import services or pipelines that create/update suppliers
    - Potential API endpoints for supplier administration

Depends on:
    - apps.core.models.Organization
    - apps.partners.models.Supplier
    - Django transaction management and ValidationError

Example:
    from apps.partners.services.supplier_ops import upsert_supplier

    payload = {
        "org_code": 1,
        "supplier_code": "SUP-1001",
        "supplier_description": "Main Widgets Supplier",
        "email": "contact@widgets.example",
        "phone": "+49-123-456789",
        "is_preferred": True,
        "lead_time_days": 14,
    }
    supplier, created = upsert_supplier(payload)
    print(f"Supplier: {supplier}, created={created}")
```

## File: `apps/pricing/management/commands/seed_price_group.py`
```
Purpose:
    Management command to upsert PriceGroup records into the database from a
    colon-delimited string. Supports dry-run mode for validation.

Context:
    Part of the `apps.pricing` app. Provides a simple seeding mechanism for
    organizations’ price groups via the Django management interface.

Used by:
    - Initial data setup (seeding default or test price groups)
    - Automated deployment or import pipelines where price groups must exist

Depends on:
    - apps.core.models.Organization
    - apps.pricing.models.PriceGroup
    - Django BaseCommand, transaction handling, CommandError

Example:
    python manage.py seed_price_groups --items "1:PG01:Retail,1::No group"
    python manage.py seed_price_groups --items "1:PG01:Retail" --dry-run
```

## File: `apps/pricing/models/currency_rate.py`
```
Purpose:
    Represents daily exchange rates between two currencies.
    Stores conversion factors (base → quote) with full precision
    and enforces uniqueness per date.

Context:
    Part of the core app. Used by pricing, procurement, and reporting
    to convert between currencies for transactions and analytics.

Fields:
    - base (FK → core.Currency): Base currency of the rate.
    - quote (FK → core.Currency): Quote currency of the rate.
    - rate (DecimalField, 16,8): Conversion factor (e.g., 1.12345678).
    - rate_date (DateField): Date the rate applies to.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Currency (base) → multiple CurrencyRates
    - Currency (quote) → multiple CurrencyRates

Used by:
    - Pricing and ERP calculations
    - Reports requiring currency normalization
    - Procurement processes involving multi-currency suppliers

Depends on:
    - apps.core.models.Currency
    - Django ORM (constraints, validators)

Example:
    >>> from apps.core.models import CurrencyRate, Currency
    >>> usd = Currency.objects.get(code="USD")
    >>> eur = Currency.objects.get(code="EUR")
    >>> cr = CurrencyRate.objects.create(base=usd, quote=eur, rate="0.92345678", rate_date="2025-09-26")
    >>> print(cr)
    USD/EUR @ 0.92345678 (2025-09-26)
```

## File: `apps/pricing/models/price_group.py`
```
Purpose:
    Represents a logical grouping of prices within an organization.
    Allows categorization of product or customer prices into groups
    such as retail, wholesale, or special contract pricing.

Context:
    Belongs to the pricing domain. PriceGroups are used to define
    customer-specific or organization-specific pricing structures.

Fields:
    - organization (FK → core.Organization): The owning organization.
    - price_group_code (CharField, max 20): Unique code per organization.
    - price_group_description (CharField, max 200): Optional descriptive name.

Relations:
    - Organization → multiple PriceGroups
    - Referenced by PriceList or SalesChannelVariantPrice
      to determine applicable prices.

Used by:
    - Pricing logic for ERP/shops
    - Import routines that map supplier/customer pricing
    - Reporting modules for analyzing price segmentation

Depends on:
    - apps.core.models.Organization

Example:
    >>> from apps.pricing.models import PriceGroup
    >>> pg = PriceGroup.objects.create(
    ...     organization=org,
    ...     price_group_code="WHOLESALE",
    ...     price_group_description="Wholesale customer pricing"
    ... )
    >>> print(pg)
    WHOLESALE — Wholesale customer pricing
```

## File: `apps/pricing/models/price_list.py`
```
Purpose:
    Represents a price list definition within an organization.
    Each price list groups together prices in a given currency and
    can be used for either sales or procurement contexts.

Context:
    Belongs to the pricing domain. PriceLists are the containers for
    product/variant pricing records and are associated with a single currency.

Fields:
    - organization (FK → core.Organization): The owning organization.
    - price_list_code (CharField, max 20): Unique code per organization.
    - price_list_description (CharField, max 200): Human-readable description.
    - kind (CharField, max 1): Type of list, 'S' (sales) or 'P' (procurement).
    - currency (FK → core.Currency): Currency of all prices in this list.
    - is_active (BooleanField): Whether the price list is active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple PriceLists
    - Currency → multiple PriceLists
    - PriceList → referenced by price detail tables (e.g., variant prices)

Used by:
    - Sales processes to fetch customer price lists
    - Procurement processes to manage supplier price lists
    - Pricing services and ERP import routines

Depends on:
    - apps.core.models.Organization
    - apps.core.models.Currency

Example:
    >>> from apps.pricing.models import PriceList
    >>> pl = PriceList.objects.create(
    ...     organization=org,
    ...     price_list_code="RETAIL-2025",
    ...     price_list_description="Retail price list for 2025",
    ...     kind="S",
    ...     currency=eur
    ... )
    >>> print(pl)
    [Org1] RETAIL-2025 (S)
```

## File: `apps/pricing/models/sales_channel_variant_price.py`
```
Purpose:
    Represents the price of a specific ChannelVariant within a PriceList.
    Each record defines the value of a variant’s price in a given sales channel
    for a specific time period.

Context:
    Belongs to the pricing domain. Used to track sales prices across
    different channels (shops, marketplaces) and supports time-based
    validity for price changes.

Fields:
    - organization (FK → core.Organization): The owning organization.
    - price_list (FK → pricing.PriceList): The price list this price belongs to.
    - channel_variant (FK → catalog.ChannelVariant): The sales channel + variant.
    - valid_from (DateTimeField): Timestamp when the price becomes effective.
    - price (DecimalField): The actual price (non-negative, up to 12,4 digits).
    - valid_to (DateTimeField): Optional end date for the price validity.
    - need_update (BooleanField): Whether the price requires a sync/update.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple SalesChannelVariantPrices
    - PriceList → multiple SalesChannelVariantPrices
    - ChannelVariant → multiple SalesChannelVariantPrices

Used by:
    - Pricing services to fetch current or historical prices
    - Import and sync jobs to update shop/marketplace prices
    - ERP processes for reporting and analytics

Depends on:
    - apps.core.models.Organization
    - apps.pricing.models.PriceList
    - apps.catalog.models.ChannelVariant

Example:
    >>> from apps.pricing.models import SalesChannelVariantPrice
    >>> scvp = SalesChannelVariantPrice.objects.create(
    ...     organization=org,
    ...     price_list=pl,
    ...     channel_variant=cv,
    ...     valid_from="2025-01-01T00:00:00Z",
    ...     price="99.9900"
    ... )
    >>> print(scvp)
    [org=1] RETAIL-2025/ChannelVariant(123) @ 99.9900 from 2025-01-01 00:00:00
```

## File: `apps/pricing/models/tax_class.py`
```
Purpose:
    Defines tax classes for products and services, including name and rate.
    Used to determine applicable tax percentages (e.g., 19% VAT).

Context:
    Part of the pricing domain. Each TaxClass represents a distinct taxation
    rule that can be applied to price calculations in ERP and shop systems.

Fields:
    - name (CharField, unique): Human-readable name for the tax class (e.g., "Standard VAT").
    - rate (DecimalField, 5,4): Tax rate as a decimal fraction (0–1, e.g., 0.1900 = 19%).
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - May be referenced by products, price rules, or invoice logic in other models.

Used by:
    - Pricing and billing systems to apply the correct tax rate
    - ERP processes for compliance and reporting
    - Import and catalog services for mapping external tax definitions

Depends on:
    - Django ORM (validation and constraints)

Example:
    >>> from apps.pricing.models import TaxClass
    >>> vat = TaxClass.objects.create(name="Standard VAT", rate="0.1900")
    >>> print(vat)
    Standard VAT (0.1900)
```

## File: `apps/pricing/services/price_list_ops.py`
```
Purpose:
    Service layer providing operations for creating or updating PriceList
    records from a dictionary payload. Ensures idempotent upserts.

Context:
    Part of the `apps.pricing` app. Encapsulates business logic for price list
    management and avoids scattering ORM logic across the project.

Used by:
    - Management commands that seed or import price lists
    - Other services or API endpoints dealing with pricing structures

Depends on:
    - apps.core.models.Organization
    - apps.core.models.Currency
    - apps.pricing.models.PriceList
    - Django transaction handling and ValidationError

Example:
    from apps.pricing.services.price_list_ops import upsert_price_list

    payload = {
        "org_code": 1,
        "price_list_code": "PL01",
        "kind": "retail",
        "currency_code": "EUR",
        "price_list_description": "Retail price list",
        "is_active": True,
    }
    pl, created = upsert_price_list(payload)
    print(pl, created)
```

## File: `apps/pricing/services/price_ops.py`
```
Purpose:
    Service layer providing operations for creating or updating
    SalesChannelVariantPrice records from dictionary payloads.
    Handles validation, foreign key resolution, and timezone safety.

Context:
    Part of the `apps.pricing` app. Centralizes price handling logic
    for sales channel variants to keep management commands and APIs lean.

Used by:
    - Import and synchronization jobs that assign prices to channel variants
    - Management commands or services that need to update prices in bulk

Depends on:
    - apps.core.models.Organization
    - apps.pricing.models.PriceList
    - apps.catalog.models.ChannelVariant
    - apps.pricing.models.SalesChannelVariantPrice
    - Django transaction management and timezone utilities

Example:
    from apps.pricing.services.price_ops import upsert_sales_channel_variant_price
    from datetime import datetime

    payload = {
        "org_code": 1,
        "price_list_id": 10,
        "channel_variant_id": 42,
        "valid_from": datetime(2025, 1, 1, 0, 0),
        "price": "19.99",
        "need_update": True,
    }
    scvp, created = upsert_sales_channel_variant_price(payload)
    print(scvp, created)
```

## File: `apps/procurement/models/purchase_order.py`
```
Purpose:
    Represents a purchase order created by an organization to procure goods
    from a supplier. Captures order number, status, currency, and delivery info.

Context:
    Part of the procurement domain. Purchase orders are used to formalize
    and track purchasing activities, serving as the header document for
    ordered items.

Fields:
    - organization (FK → core.Organization): Owning organization.
    - supplier (FK → partners.Supplier): Supplier to whom the order is placed.
    - order_number (CharField, max 30): Unique identifier per organization.
    - status (CharField, max 20): Workflow state ("draft", "approved", "ordered",
      "received", "cancelled").
    - currency (FK → core.Currency): Currency in which the order is placed.
    - expected_date (DateField, optional): Expected delivery date.
    - notes (TextField, optional): Freeform remarks.
    - is_active (BooleanField): Whether the order is currently active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple PurchaseOrders
    - Supplier → multiple PurchaseOrders
    - Currency → multiple PurchaseOrders
    - To be extended by PurchaseOrderLine for itemized order positions.

Used by:
    - Procurement workflows to manage supplier orders.
    - ERP processes for stock, invoicing, and financial reconciliation.
    - Reporting to track supplier performance and order statuses.

Depends on:
    - apps.core.models.Organization
    - apps.core.models.Currency
    - apps.partners.models.Supplier

Example:
    >>> from apps.procurement.models import PurchaseOrder
    >>> po = PurchaseOrder.objects.create(
    ...     organization=org,
    ...     supplier=sup,
    ...     order_number="PO-2025-001",
    ...     status="draft",
    ...     currency=eur,
    ... )
    >>> print(po)
    [org=1] PO PO-2025-001 (draft)
```

## File: `apps/procurement/models/purchase_order_line.py`
```
Purpose:
    Represents a line item within a purchase order, detailing the product,
    quantity, and price agreed at the time of order placement.

Context:
    Part of the procurement domain. PurchaseOrderLine items belong to a
    PurchaseOrder and specify the concrete products (via SupplierProduct),
    quantities, and pricing used in supplier transactions.

Fields:
    - organization (FK → core.Organization): Owning organization.
    - purchase_order (FK → procurement.PurchaseOrder): Parent purchase order.
    - row_no (SmallIntegerField): Line number, unique per order and organization.
    - supplier_product (FK → procurement.SupplierProduct): Product reference
      from a supplier catalog.
    - qty (DecimalField): Quantity ordered, must be > 0.
    - price_at_order (DecimalField): Unit price at the time of order, >= 0.
    - note (TextField, optional): Freeform note for this line.
    - is_active (BooleanField): Whether the line is active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - PurchaseOrder → multiple PurchaseOrderLines
    - SupplierProduct → multiple PurchaseOrderLines
    - Organization → multiple PurchaseOrderLines

Used by:
    - Procurement workflows for order fulfillment and invoicing.
    - Stock management and ERP integrations to update inventory.
    - Reporting on purchase details and supplier performance.

Depends on:
    - apps.core.models.Organization
    - apps.procurement.models.PurchaseOrder
    - apps.procurement.models.SupplierProduct

Example:
    >>> from apps.procurement.models import PurchaseOrderLine
    >>> pol = PurchaseOrderLine.objects.create(
    ...     organization=org,
    ...     purchase_order=po,
    ...     row_no=1,
    ...     supplier_product=sp,
    ...     qty=10,
    ...     price_at_order="99.99",
    ... )
    >>> print(pol)
    [org=1] PO=PO-2025-001 #1 -> SP=SP-123
```

## File: `apps/procurement/models/supplier_price.py`
```
Purpose:
    Represents supplier-specific purchasing price headers. Defines currency,
    validity ranges, and optional flat prices. Tiered pricing details are
    maintained in SupplierQuantityPrice.

Context:
    Part of the procurement domain. SupplierPrice acts as the header for
    supplier pricing definitions. It ensures each supplier product has
    structured pricing information that may include validity periods and
    multiple tiers.

Fields:
    - supplier_product (FK → procurement.SupplierProduct): The product this
      supplier price belongs to.
    - currency (FK → core.Currency): Currency of the price list (ISO 4217).
    - unit_price (DecimalField, optional): Flat fallback price, without VAT.
    - min_quantity (DecimalField, optional): Minimum quantity for applying the
      flat unit price.
    - valid_from / valid_to (DateField, optional): Validity period of this price.
    - is_active (BooleanField): Whether this price is currently active.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - SupplierProduct → multiple SupplierPrices
    - SupplierPrice → multiple SupplierQuantityPrices (via related_name="prices")
    - Currency → multiple SupplierPrices

Used by:
    - Procurement for cost calculation, supplier integration, and order validation.
    - ERP workflows that determine applicable purchasing prices.

Depends on:
    - apps.procurement.models.SupplierProduct
    - apps.core.models.Currency
    - apps.procurement.models.SupplierQuantityPrice (child table)

Example:
    >>> from apps.procurement.models import SupplierPrice
    >>> sp = SupplierPrice.objects.create(
    ...     supplier_product=supplier_product,
    ...     currency=eur,
    ...     unit_price="12.50",
    ...     min_quantity="5",
    ... )
    >>> print(sp)
    SP-123 12.50 EUR
```

## File: `apps/procurement/models/supplier_product.py`
```
Purpose:
    Defines the SupplierProduct entity, linking a ProductVariant with a Supplier.
    Stores supplier-specific identifiers, packaging details, ordering constraints,
    and procurement metadata. Forms the basis for managing supplier relationships
    for each variant.

Context:
    Part of the procurement domain. This model allows the system to store and
    differentiate how the same product variant is offered by different suppliers.
    It supports lead times, MOQs, and supplier-specific SKUs.

Fields:
    - organization (FK → core.Organization): Tenant scoping.
    - supplier (FK → partners.Supplier): The supplying vendor.
    - variant (FK → catalog.ProductVariant): The product variant being supplied.
    - supplier_sku (CharField): Supplier’s internal SKU/article number.
    - supplier_description (CharField): Supplier-provided description.
    - pack_size (DecimalField): Number of base units per supplier pack.
    - min_order_qty (DecimalField): Minimum order quantity at supplier.
    - lead_time_days (IntegerField): Delivery lead time in days.
    - is_active (BooleanField): Marks if the supplier product is valid.
    - is_preferred (BooleanField): Flags a preferred supplier.
    - notes (TextField): Free-text notes for procurement.
    - created_at / updated_at (DateTimeField): Audit timestamps.

Relations:
    - Organization → multiple SupplierProducts
    - Supplier → multiple SupplierProducts
    - ProductVariant → multiple SupplierProducts
    - SupplierProduct → SupplierPrice (child records for price tiers)

Used by:
    - Procurement processes for creating purchase orders.
    - Supplier price management (via SupplierPrice and SupplierQuantityPrice).
    - ERP functions that calculate cost or choose preferred supplier.

Depends on:
    - apps.core.models.Organization
    - apps.partners.models.Supplier
    - apps.catalog.models.ProductVariant
    - apps.procurement.models.SupplierPrice (downstream dependency)

Example:
    >>> from apps.procurement.models import SupplierProduct
    >>> sp = SupplierProduct.objects.create(
    ...     organization=org,
    ...     supplier=supplier,
    ...     variant=variant,
    ...     supplier_sku="SUP-12345",
    ...     pack_size=10,
    ...     min_order_qty=50,
    ...     lead_time_days=7,
    ... )
    >>> print(sp)
    [org=1] supplier=SUP sku=SUP-12345 -> variant=SKU-001
```

## File: `apps/procurement/models/supplier_quantity_price.py`
```
Purpose:
    Defines quantity-based price tiers for a supplier’s product.
    Complements SupplierPrice by enabling stepped pricing models when
    a single flat price (unit_price) is not sufficient.

Context:
    Part of the procurement domain. This model allows tiered pricing
    based on minimum order quantities. For example, buying 100 units
    may have a lower unit price than buying 10.

Fields:
    - supplier_price (FK → SupplierPrice): Links to the supplier price header.
    - min_quantity (DecimalField): Minimum quantity for this tier.
    - unit_price (DecimalField): Net purchase price per unit (excl. VAT).

Relations:
    - SupplierPrice → multiple SupplierQuantityPrice (tiers).
    - SupplierQuantityPrice belongs to exactly one SupplierPrice.

Used by:
    - Procurement calculations (choosing correct tier for an order).
    - ERP price imports from suppliers with graduated pricing.
    - PO line creation when selecting best available tier.

Depends on:
    - apps.procurement.models.SupplierPrice

Constraints:
    - Unique per (supplier_price, min_quantity).
    - Ordered by min_quantity ascending.

Example:
    >>> from apps.procurement.models import SupplierQuantityPrice
    >>> tier = SupplierQuantityPrice.objects.create(
    ...     supplier_price=sp,
    ...     min_quantity=100,
    ...     unit_price=9.99,
    ... )
    >>> print(tier)
    100+ → 9.99 (EUR)
```

## File: `apps/procurement/services/supplier_price_ops.py`
```
Purpose:
    Provides safe operations for inserting or updating supplier prices.
    Ensures that duplicate entries are avoided and price history is maintained
    by deactivating old records when values change.

Context:
    Part of the `apps.procurement` app. Encapsulates business logic for
    supplier price management, keeping importers and synchronization jobs clean.

Used by:
    - Importers that load supplier price data (CSV, API, Excel)
    - Procurement workflows updating tiered pricing
    - Services that manage SupplierProduct cost data

Depends on:
    - apps.procurement.models.SupplierPrice
    - apps.procurement.models.SupplierQuantityPrice
    - django.utils.timezone for timestamp handling
    - Python's decimal for monetary precision

Example:
    from decimal import Decimal
    from apps.procurement.services.supplier_price_ops import SupplierPriceOps

    supplier_product = SupplierProduct.objects.get(id=1)
    new_price = SupplierPriceOps.upsert_price(
        supplier_product=supplier_product,
        currency="EUR",
        unit_price=Decimal("9.99"),
        quantity_prices=[(Decimal("10"), Decimal("9.50"))],
        valid_from=timezone.now().date(),
    )
    print(new_price.id, new_price.unit_price)
```

## File: `apps/procurement/services/supplier_product_ops.py`
```
Purpose:
    Provides operations to safely insert or update SupplierProduct records.
    Ensures consistent links between Organization, Supplier, and ProductVariant.

Context:
    Part of the `apps.procurement` app. Encapsulates business logic for
    managing supplier-specific product definitions.

Used by:
    - Import pipelines that load supplier catalog data
    - Procurement services that need to attach variants to suppliers
    - Synchronization jobs for maintaining supplier SKU references

Depends on:
    - apps.core.models.Organization
    - apps.partners.models.Supplier
    - apps.catalog.models.ProductVariant
    - apps.procurement.models.SupplierProduct
    - Django transaction management

Example:
    from apps.procurement.services.supplier_product_ops import upsert_supplier_product

    payload = {
        "org_code": 1,
        "supplier_id": 42,
        "variant_id": 99,
        "supplier_sku": "SUP-ART-2025",
        "pack_size": 10,
        "min_order_qty": 100,
        "lead_time_days": 14,
        "is_active": True,
        "supplier_description": "10mm Steel Bolts",
        "notes": "Special pricing valid until 2025-12-31",
    }
    sp, created = upsert_supplier_product(payload)
    print(sp.id, created)
```

## File: `apps/sales/models/sales_order.py`
```
Purpose:
    Represents the header of a sales order, scoped by organization.
    Tracks business partner, currency, status, and important dates.

Context:
    Part of the sales domain. This table is the parent for sales order lines
    and drives fulfillment, invoicing, and reporting.

Fields:
    - organization (FK → Organization): Tenant isolation.
    - customer (FK → Customer): Buyer reference.
    - order_number (CharField): Unique per organization.
    - status (CharField): Lifecycle state (draft|confirmed|shipped|invoiced|cancelled).
    - currency (FK → Currency): Transaction currency.
    - expected_date (DateField): Optional promised delivery date.
    - notes (TextField): Optional free-text notes.
    - is_active (Bool): Logical deletion flag.
    - created_at / updated_at: System timestamps.

Relations:
    - SalesOrder → multiple SalesOrderLine (items).
    - Linked to invoicing, shipping, and pricing modules.

Constraints:
    - (organization, order_number) unique.
    - (organization, id) unique for safety.
    - Status restricted by check constraint.

Example:
    >>> from apps.sales.models import SalesOrder
    >>> so = SalesOrder.objects.create(
    ...     organization=org,
    ...     customer=cust,
    ...     order_number="SO-2025-001",
    ...     currency=eur,
    ... )
    >>> print(so)
    [org=MyOrg] SO SO-2025-001 (draft)
```

## File: `apps/sales/models/sales_order_line.py`
```
Purpose:
    Represents an individual line item in a sales order.
    Each line links to a product variant, with ordered quantity and price.

Context:
    Child of SalesOrder. Used to record which items are sold,
    at which price, and in what quantity. Basis for fulfillment and invoicing.

Fields:
    - organization (FK → Organization): Tenant isolation.
    - sales_order (FK → SalesOrder): Parent sales order reference.
    - row_no (SmallInteger): Unique row number per order.
    - variant (FK → ProductVariant): Ordered product variant.
    - qty (Decimal): Ordered quantity (> 0).
    - price_at_order (Decimal): Net price per unit at time of order.
    - note (TextField): Optional line-level note.
    - is_active (Bool): Logical deletion flag.
    - created_at / updated_at: System timestamps.

Constraints:
    - (organization, sales_order, row_no) unique.
    - qty must be > 0.
    - price_at_order must be ≥ 0.

Example:
    >>> from apps.sales.models import SalesOrderLine
    >>> line = SalesOrderLine.objects.create(
    ...     organization=org,
    ...     sales_order=so,
    ...     row_no=1,
    ...     variant=variant,
    ...     qty=10,
    ...     price_at_order=99.99,
    ... )
    >>> print(line)
    [org=MyOrg] SO=SO-2025-001 #1 -> VAR=SKU123
```
