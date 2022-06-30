..
    This is the docstring for the pittgoogle module.
    The file is intended to be included in pubsub.rst.

Usage
------

.. note::

    This module relies on :mod:`pittgoogle.auth` to authenticate API calls. The examples
    given below use the :ref:`service account <service account>` option and assume that
    your :ref:`environment variables <set env vars>` are set.

TL;DR
~~~~~~~

-   Listen to a stream by using a :class:`Consumer()`.

-   The :ref:`user callback` determines how the alerts are processed and stored.

-   There are a few different groups of settings in :class:`ConsumerSettings`
    for things like stopping conditions and the alert format
    (follow the type definitions of the attributes).

.. important::

    :meth:`Consumer.stream()` opens a streaming pull in a background thread and blocks
    the main thread while the stream is open
    (which is determined by stopping conditions in the settings).
    **Use** `Ctrl + C` **at any time to regain control of the terminal.**
    If you somehow regain control of the main thread while the stream is still open
    in the background (which you can do on purpose using the kwarg ``block=False``),
    call :meth:`Consumer.stop()`.
    In either case, the consumer will attempt to close the stream gracefully
    and exit the background thread.

.. _consumer basic:

The most basic example
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pittgoogle.pubsub import Consumer, ConsumerSettings, CallbackSettings

Use a :class:`Consumer()` to manage a Pub/Sub subscription and pull messages.
The most basic instantiation looks like this:

.. code-block:: python

    consumer = Consumer(ConsumerSettings())

See :class:`ConsumerSettings` to learn everything that's available.
It contains attributes holding a

-   :class:`SubscriberClient()`

-   :class:`Subscription()`

-   :class:`FlowConfigs()`

-   :class:`CallbackSettings()`

The attributes allow you to call all of their associated properties and methods
through the consumer.
For example, you can use:

.. code-block::  python

    consumer.subscription.delete()

In the default case shown above, the consumer will try to create a **client** using
authentication information stored in environment variables.
It will then connect to a **subscription** using the default settings.
If the subscription doesn't exist in Pub/Sub, it will be created.

The next call will open a streaming pull on the subscription, which will run in
the background.
The default **flow configs** include conservative stopping conditions that are meant to
support you during testing, to prevent the stream from running out of control.

We need to supply a :ref:`user callback` in the **callback settings**, which will
determine how the alerts are processed and stored. There is a template in the user
callback section. Here, we will use an example function that simply passes the alert
back to the consumer with a request to store it in :attr:`Consumer.results` for later
access. It is provided as a (static) method of the consumer for convenience
(:meth:`Consumer.collect_alert`), but see the warning below.

Open the stream and process messages:

.. code-block:: python

    consumer = Consumer(
        ConsumerSettings(
            callback_settings=CallbackSettings(user_callback=Consumer.collect_alert),
        )
    )

    results = consumer.stream()  # returns consumer.results

By default, the consumer will **block** the main thread while the stream is open.
Use `Ctrl + C` at any time to close the stream and regain control of the terminal.

.. warning::

    If you choose to send results back to the consumer through the
    :attr:`~pittgoogle.types.Response.result` attribute
    (as is done in :meth:`Consumer.collect_alert`),
    the results will not be available until the background thread has been closed.
    This increases the potential that collected results will fill up your memory,
    and also means that the results may be lost if a thread crashes.
    This option can be useful for testing, but it should not be combined with a
    large value of :attr:`FlowConfigs.max_results`.

.. _callbacks:

Callbacks Explainer
-------------------

(You may wish to jump directly to :ref:`user callback`.)

In Pub/Sub, a streaming pull happens in a background thread.
Thus, message processing should be handled by a callback function.
The callback should process a single message, persist the needed results, and then
:ref:`ack or nack <ack and nack>` the message.
The callback is passed into the background thread by the client when it opens the
stream.

The :class:`Consumer` uses two callbacks:
its :ref:`own callback() method <consumer callback>`
and a :ref:`user callback <user callback>`.
These are explained below.

The callback is perhaps the biggest difference between implementations that use Pub/Sub
versus Kafka.
Pulling an Apache Kafka stream typically results in Kafka returning a batch of messages.
The user can then process messages at-will by iterating through the batch.
You can mimic this behavior by using :meth:`Consumer.collect_alert` as your
user callback, but this is recommended for testing only.
See the example above.

.. _consumer callback:

Consumer callback
~~~~~~~~~~~~~~~~~~~~~~

The consumer's :meth:`~Consumer.callback()` method is called automatically
on each incoming message.
This method will:

#.  Unpack the Pub/Sub message into an :class:`~pittgoogle.types.Alert()`,
    populating only the attributes reqested in :attr:`~CallbackSettings.unpack`.

#.  Send the :class:`~pittgoogle.types.Alert()` through the :ref:`user callback`.

#.  Handle the :class:`~pittgoogle.types.Response()` returned by the user callback.
    This may include storing data in :attr:`Consumer().results`
    and :ref:`ack'ing or nack'ing <ack and nack>` the message.

#.  Communicate with the foreground thread.

.. _user callback:

User callback
~~~~~~~~~~~~~~~~~

A :attr:`~CallbackSettings.user_callback` is a function supplied by the user that
should:

#.  accept a single alert as input (:class:`pittgoogle.types.Alert`)

#.  process it

#.  store the results

#.  return a :class:`pittgoogle.types.Response`

Here are some important characteristics of the function:

-   It can include arbitrary logic but it must be self-contained --
    it will run in the background, and thus
    **cannot rely on the state of the foreground thread**.

-   It can accept keyword arguments, but they must be supplied to the consumer before
    opening the stream (see :attr:`~CallbackSettings.user_kwargs`).

-   Idealy, it should store its own results --
    for example, by sending to a database or writing to a file.
    There is an option to have the consumer store results for you,
    but see the warning above.

Here is a template:

.. code-block:: python

    def my_user_callback(alert):
        # alert is an instance of pittgoogle.types.Alert
        # populated according to a callback setting called unpack
        alert_dict = alert.dict

        try:
            # process the alert here
            # and save your results
            pass

        except:
            ack = False

        else:
            ack = True

        return Response(ack=ack, result=None)

And here's how to use it:

.. code-block:: python

    consumer = Consumer(
        ConsumerSettings(
            callback_settings=CallbackSettings(user_callback=my_user_callback),
        )
    )

    consumer.stream()  # returns None, since my_user_callback() stores its own results

Use `Ctrl + C` at any time to close the stream and regain control of the terminal.

.. _ack and nack:

ack and nack
~~~~~~~~~~~~~~

A :class:`pittgoogle.types.Response()` (to be returned by a :ref:`user callback`)
contains the boolean attribute :attr:`~Response.ack`, which indicates whether the message
should be ack'd (``ack=True``) or nack'd (``ack=False``).

**ack** is short for acknowledge.
ack should be used when the message has been processed successfully -- or at least to
an acceptable level such that the client/user does not need to see the message again.
Once Pub/Sub receives the ack, the message will be dropped from the subscription[*].

**nack** is the opposite of ack.
A nack'd message will remain in the subscription, and Pub/Sub will redeliver it to a
client at some arbitrary time in the future.
(Redelivery is usually immediate, though can be affected by, for example, the number of
messages in the subscription.)

In Pub/Sub, the subscriber client should either ack or nack each message it receives.
The consumer's :class:`~Consumer.handle_response()` method does this automatically,
based on the :class:`~pittgoogle.types.Response()` returned by the :ref:`user callback`.

This is a similar concept to setting the offset in an Apache Kafka topic/subscription.
However, a major difference is that Pub/Sub messages are not ordered[\*], so one cannot
"fast-forward" or "rewind" the stream in the same way.
Instead, every Pub/Sub message is delivered, processed, and ack'd or nack'd
independently.

[\*] Unless the subscription has been explicitly configured to behave otherwise.
