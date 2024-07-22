What is Pub/Sub?
=================

Google `Pub/Sub <https://cloud.google.com/pubsub/docs/overview>`__ is a messaging service that
uses the publish-subscribe pattern.
Publishers and subscribers communicate asynchronously, with the Pub/Sub service handling all message storage and delivery.
Publishers send messages to a topic, and Pub/Sub immediately delivers them to all attached subscriptions.
Subscriptions can be configured to either push messages to a client automatically or to wait for a client to make a pull request.
The owner of the topic sets the access rights that determine who is allowed to attach a subscription.
Messages published to a topic prior to a subscription being created will not be available to the subscriber.
By default, Pub/Sub messages are not ordered.
