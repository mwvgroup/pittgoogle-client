.. _cost:

Costs
--------------

A baseline level of data access is free.
This is structured as a usage quota that renews monthly --  the first `X` (amount) of
usage each month is free, where `X` depends on the service (Pub/Sub,
BigQuery, Cloud Storage).
Some examples are given in the table below.
If you exceed the limit and have not set up billing your access will be restricted until
the quota renews.
:ref:`Projects <projects>` are free.
No credit card is required.

.. list-table:: Pricing Examples (as of Aug. 2021)
    :class: tight-table
    :widths: 15 20 20 20
    :header-rows: 1

    * - Service
      - Activity
      - Free Tier quota
      - Price beyond Free Tier
    * - BigQuery
      - querying data
      - 1 TB per month
      - $5.00 per TB
    * - Pub/Sub
      - message delivery
      - 10 GB per month
      - $40 per TB

You cannot be charged unless you create a billing account and attach it to your project.
In this case, the pricing structure is "pay-as-you-go".
There are some options listed below to offset costs.
Free quotas still apply.

Here are links that might be useful:

- `Free Tier <https://cloud.google.com/free>`__
- `$300 Free Trial <https://cloud.google.com/free/docs/gcp-free-tier?authuser=1#free-trial>`__
- `$5000 Research Credits <https://edu.google.com/programs/credits/research/?modal_active=none>`__
- `Pricing structure <https://cloud.google.com/pricing>`__
  (scroll to "Only pay for what you use")
- `Detailed price list <https://cloud.google.com/pricing/list>`__
  (search for "BigQuery", "Cloud Storage", "Pub/Sub");
- `Pricing calculator <https://cloud.google.com/products/calculator?skip_cache=true>`__
  (same search as above)
- `Create a billing account
  <https://cloud.google.com/billing/docs/how-to/manage-billing-account>`__
- `Enable billing for a project
  <https://cloud.google.com/billing/docs/how-to/modify-project#enable_billing_for_a_project>`__
