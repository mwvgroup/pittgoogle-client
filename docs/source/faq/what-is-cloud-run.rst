What is Cloud Functions and Cloud Run?
======================================

Google `Cloud Functions <https://cloud.google.com/functions/docs/concepts/overview>`__ and
Google `Cloud Run <https://cloud.google.com/run/docs/overview/what-is-cloud-run>`__
are managed-compute services run by Google Cloud.
They both run containers that are configured as HTTP endpoints.
They can be used to process live message streams by attaching Pub/Sub push subscriptions.
Incoming requests (i.e., messages) are processed in parallel.
The number of container instances scales automatically and nearly instantaneously to meet incoming demand.
Differences between the services are essentially tradeoffs between efficiency (at large scale) and ease of use.
