..
    This is the docstring for the pittgoogle.pubsub module.
    The file is intended to be included in docs/source/api/pubsub.rst.

Usage
------

.. note::

    This module relies on :mod:`pittgoogle.auth` to authenticate API calls.
    The examples given below assume the use of a :ref:`service account <service account>` and :ref:`environment variables <set env vars>`.

TL;DR
~~~~~~~

-   Listen to a stream using a :class:`Consumer()`.

-   The :ref:`user callback <user callback>` determines how the alerts are processed and stored.

-   There are settings for the connection, user callback, and flow control.

.. important::

    :meth:`Consumer.stream()` opens a streaming pull in a background thread and blocks
    the main thread while the stream is open.
    Use `Ctrl + C` at any time to regain control of the terminal.

    If the main thread unblocks while the stream is still open (e.g., if you send ``block=False``),
    call :meth:`Consumer.stop()`.

    In either case, the consumer will attempt to close the stream gracefully
    and exit the background thread.

.. _consumer basic:

Basic example
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pittgoogle import pubsub

Use a :class:`Consumer()` to manage a Pub/Sub subscription and pull messages.
The most basic instantiation looks like this:

.. code-block:: python

    consumer = pubsub.Consumer()

**Connection**:
This will create a default :class:`SubscriberClient` and connect to a default :class:`Subscription`.
If the subscription doesn't exist in Pub/Sub, it will be created.

The client and subscription are attached as attributes.
You have access to all of their associated attributes and methods.
For example, if you want to delete the subscription use:

.. code-block::  python

    consumer.subscription.delete()

**Callback**:
We need to supply a :ref:`user callback <user callback>` to do anything beyond counting the alerts.
This determines how the alerts are processed and stored.
There is a template in the user callback section linked above.
Here, we will use an example function that simply passes the alert back to the consumer,
requesting that it be stored in :attr:`results` for later access.
It is provided as a (static) method of the consumer for convenience
(:meth:`request_to_collect`), but see the warning below.

**Flow configs**:
The next call will open a streaming pull on the subscription, which will run in
the background.
The default flow configs include conservative stopping conditions that are meant to
support testing, to prevent the stream from running out of control.

Open the stream and process messages:

.. code-block:: python

    consumer = Consumer(user_callback=Consumer.request_to_collect)

    results = consumer.stream()  # returns consumer.results once the stream closes

By default, the consumer will **block** the main thread while the stream is open.
**Use** `Ctrl + C` **at any time to close the stream and regain control of the terminal.**

.. warning::

    If you choose to send results back to the consumer through the
    :attr:`~pittgoogle.types.Response.result` attribute
    (like the callback example :meth:`request_to_collect`),
    **the results will not be available until the background thread has been closed**.
    This increases the potential that collected results will fill up your memory,
    and also means that the results may be lost if a thread crashes.
    This option can be useful for testing, but should be used with caution.
    In particular, limit the amount of data requested in :attr:`unpack` and/or
    use a small value for :attr:`max_results`.

.. _callbacks:

Callbacks Explainer
-------------------

(You may wish to jump directly to :ref:`user callback <user callback>`.)

In Pub/Sub, a streaming pull happens in a background thread.
Thus, message processing should be handled by a callback.
The callback should process a single message, persist the needed results, and then
:ref:`ack or nack <ack and nack>` the message.
The callback is passed into the background thread by the client when it opens the
stream.

The :class:`Consumer` uses two callbacks:
its :ref:`own callback() method <consumer callback>`
and a :ref:`user callback <user callback>`.
They are explained below.

**Kafka comparison**: The callback is perhaps the biggest difference between
implementations that use Pub/Sub versus Kafka.
Pulling an Apache Kafka stream typically results in Kafka returning a batch of messages.
The user can then process messages at-will by iterating through the batch.
You can mimic this behavior by using :meth:`Consumer.request_to_collect` as your
user callback, but this is recommended for testing only.
See the example above.

.. _consumer callback:

Consumer callback
~~~~~~~~~~~~~~~~~~~~~~

The consumer's :meth:`~Consumer.callback()` method is called on each incoming message.
It will:

#.  Unpack the Pub/Sub message into an :class:`~pittgoogle.types.Alert()`,
    populating only the attributes reqested in :attr:`~Consumer.unpack`.

#.  Send the :class:`~pittgoogle.types.Alert()` through the :ref:`user callback <user callback>`.

#.  Handle the :class:`~pittgoogle.types.Response()` returned by the user callback.
    This may include storing data in :attr:`Consumer().results`
    and :ref:`ack'ing or nack'ing <ack and nack>` the message.

#.  Communicate with the foreground thread.

.. _user callback:

**\*\* User callback \*\***
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A :attr:`~Consumer.user_callback` is a function supplied by the user that should:

#.  accept a single alert as input (:class:`pittgoogle.types.Alert`)

#.  process it

#.  store the results

#.  return a :class:`pittgoogle.types.Response`

Here are some important characteristics:

-   It can include arbitrary logic but it must be self-contained --
    it will run in the background and thus it
    **cannot rely on the state of the foreground thread**.

-   It can accept keyword arguments, but they must be supplied to the consumer through
    :attr:`~Consumer.user_kwargs` before opening the stream.

-   It should store its own results --
    for example, by sending to a database or writing to a file.
    There is an option to have the consumer save and return the results for you,
    but this is intended for testing only.
    See the warning above.

Here is a template:

.. code-block:: python

    def my_user_callback(alert):
        # alert is a pittgoogle.types.Alert()
        # populated according to the unpack parameter
        metadata_dict = alert.metadata
        alert_dict = alert.dict

        try:
            # process the alert here
            # and save your results
            pass

        except:
            ack = False

        else:
            ack = True

        # see the pittgoogle.types.Response() docstring
        # to understand what happens next
        return Response(ack=ack)

And here's how to use it:

.. code-block:: python

    consumer = Consumer(
        user_callback=my_user_callback,
        unpack=["dict", "metadata"],
    )

    consumer.stream()

By default, this will block until the stream is closed.
**Use** `Ctrl + C` **at any time to close the stream and regain control of the terminal.**

.. _ack and nack:

ack and nack
~~~~~~~~~~~~~~

A :class:`pittgoogle.types.Response()` (returned by a :ref:`user callback <user callback>`)
contains the boolean attribute :attr:`~Response.ack`, which indicates whether the message
should be ack'd (``ack=True``) or nack'd (``ack=False``).

**ack** is short for acknowledge.
ack should be used when the message has been processed successfully -- or at least to
an acceptable level such that the client/user does not need to see the message again.
The message will be dropped from the subscription[\*].

**nack** is the opposite of ack.
A nack'd message will remain in the subscription, and Pub/Sub will redeliver it to a
client at some arbitrary time in the future.
(Redelivery is usually immediate, though can be affected by, for example, the number of
messages in the subscription.)

In Pub/Sub, the subscriber client should either ack or nack each message it receives.
The consumer's :class:`~Consumer.handle_response()` method does this automatically,
based on the :class:`~pittgoogle.types.Response()` returned by the :ref:`user callback <user callback>`.

**Kafka comparison**:
This is a similar concept to setting the offset in an Apache Kafka topic/subscription.
However, a major difference is that Pub/Sub messages are not ordered[\*], so one cannot
"fast-forward" or "rewind" the stream in the same way.
Every Pub/Sub message is delivered, processed, and ack'd or nack'd independently.

[\*] True by default, but the subscription can be configured differently.
