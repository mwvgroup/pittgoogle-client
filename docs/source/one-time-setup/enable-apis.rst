.. _enable apis:

Enable APIs for a Google Cloud Project
=======================================

.. contents::
    :depth: 2
    :local:

Every Google service has at least one API that can be used to access it.
These are disabled by default (since there are hundreds -- Gmail, Maps, Pub/Sub, ...)
They must be manually enabled before anyone in your project can use them.

Enabling the following 3 will be enough for most interactions with
Pitt-Google resources.
Follow the links, make sure you've landed in the right project
(there's a dropdown in the blue menu bar), then click "Enable":

- `Pub/Sub <https://console.cloud.google.com/apis/library/pubsub.googleapis.com>`__

- `BigQuery <https://console.cloud.google.com/apis/library/bigquery.googleapis.com>`__

- `Cloud Storage <https://console.cloud.google.com/apis/library/storage-component.googleapis.com>`__

If/when you attempt a call to an API you have not enabled,
the error message provides instructions to enable it.
You can also search the
`API Library <https://console.cloud.google.com/apis/library>`__.
