Get alerts for testing
======================

Setup
-----

.. code-block:: python

    import pittgoogle

Get alerts from a Pub/Sub subscription
--------------------------------------

If you need to create the subscription, follow the example in :class:`pittgoogle.Subscription`.

Here are examples that get an alert from each of our "loop" streams:

.. code-block:: python

    # Choose one of the following
    loop_sub = pittgoogle.Subscription("rubin-loop", schema_name="lsst.v7_1.alert")
    loop_sub = pittgoogle.Subscription("elasticc-loop", schema_name="elasticc.v0_9_1.alert")
    loop_sub = pittgoogle.Subscription("ztf-loop", schema_name="ztf")

    loop_sub.touch()

    alert = loop.pull_batch(max_messages=1)[0]

Get alerts from a file on disk
-------------------------------

.. code-block:: python

    # [TODO] Add code snippet


Get alerts from Cloud Storage
-----------------------------

.. code-block:: python

    # [TODO] Add code snippet

Get alerts from BigQuery
-------------------------
.. code-block:: python

    # [TODO] Add code snippet
