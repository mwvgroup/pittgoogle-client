.. _cost:

Costs
--------------

The Pitt-Google Alert Broker makes data available in Google Cloud repositories.
The data are public and user-pays, meaning that anyone can access as much or little as they want, and everyone pays for what *they* use.
Making the data available in this way can allow us to support a very large number of users.
Payment goes to Google (not Pitt-Google Broker).
All authentication and billing is managed through Google Cloud projects.

Compared to more traditional computing costs, cloud charges are much smaller but more frequent.
Some example charges are given in the table below.
Small projects can run for free.
Google provides a baseline level of "free tier" access, structured as a usage quota that renews monthly.
No credit card or billing account is required.
Other cost-offset options include $300 in free credits available to everyone, and $5000 in research credits available to many academics (see links below).
Large projects can use as much as they want to pay for.
Google's structure is "pay-as-you-go" with a monthly billing cycle, cancel at any time.

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
