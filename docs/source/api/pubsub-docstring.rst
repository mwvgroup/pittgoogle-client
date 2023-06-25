..
    This is the docstring for the pittgoogle.pubsub module.
    The file is intended to be included in docs/source/api/pubsub.rst.

Usage
------

.. note::

    This module relies on :mod:`pittgoogle.auth` to authenticate API calls.
    The examples given below assume the use of a :ref:`service account <service account>` and :ref:`environment variables <set env vars>`.


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

**Callback**:
We need to supply a :ref:`user callback <user callback>` to do anything beyond counting the alerts.
This determines how the alerts are processed and stored.
There is a template in the user callback section linked above.
Here, we will use an example function that simply passes the alert back to the consumer,
requesting that it be stored in :attr:`results` for later access.
It is provided as a (static) method of the consumer for convenience
(:meth:`request_to_collect`), but see the warning below.

Open the stream and process messages:

.. code-block:: python

    consumer = Consumer(subscription="ztf-loop", msg_callback=msg_callback)

    results = consumer.stream()

By default, the consumer will **block** the main thread while the stream is open.
**Use** `Ctrl + C` **at any time to close the stream and regain control of the terminal.**

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

A :attr:`~Consumer.msg_callback` is a function supplied by the user that should:

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

    def my_msg_callback(alert):
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
        msg_callback=my_msg_callback,
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


Pub/Sub Explainer
-----------------

**Topics and subscriptions are distinct entities**

    -   A message can only be *published* to a *topic*, and it can only be *received* via a *subscription*.

**Messages are *independent* of each other**

    -   Messages are *tracked and treated individually* throughout their lifecycle.
        There is no specific association between any two messages, and the fate of one does not affect the fate of another.
    -   Messages are *not ordered*\footnote{by default. need to connect this same footnote to lots of things}.
        In other words, nothing can be inferred about the order in which two messages were *published* based solely on the order in which they are *received*.

**The basic lifecycle of a message is as follows:**

    -   A publisher client sends the message to a topic.
    -   Pub/Sub immediately delivers a separate copy to each subscription that is attached to the topic.
        *No other subscription will ever be able to access the message*, even if that subscription was / is attached to the same topic at an earlier / later time.
    -   The message will remain in a given subscription until either:
            a)  it is delivered to a subscriber client *and* the client returns an acknowledgement, or(\* by default footnote... retaining msgs after an acknowledgement is possible)
            b)  the maximum message retention time elapses.
                The maximum message retention time is a setting on the *subscription* (not an individual message, or a topic).
                Both the default and the upper limit for this setting is 7 days.

**Message acknowledgement**

-   Pub/Sub sends messages to a subscriber client on time-limited "leases".

    -   A message is only deleted from the subscription if and when Pub/Sub receives a positive acknowledgement of that message back from the client.
    -   The client must acknowledge each message individually.
    -   If the client returns a negative acknowledgement, or does not return any acknowledgement before the lease expires, Pub/Sub will release the message back into the subscription.

        -   Pub/Sub will then re-deliver the message to a subscriber client at some arbitrary time in the future.

**Streaming pull:**

    -   always runs in a *background* thread.
        This means that

        -   the messages must be processed via a *callback*, and that the callback will be sent into the background thread *before* the stream is opened.

.. -   thus, the callback must operate as a stand-alone function.
        -   Thus it will not have access to the main thread's environment *while* it is processing messages.
    -   In addition, it's important to understand that:
        1.  The callback will receive a single message as input.
        2.  The *callback* must send an acknowledgement of the message to Pub/Sub.
        3.  As soon as Pub/Sub receives a positive acknowledgement it will *permanently delete* the message from the subscription\footnote{by default...}.
    -   This means that a client *cannot* collect multiple messages and then process them as a batch *before* telling Pub/Sub that it's okay to permanently delete all of those messages from the subscription.
        -   Thus the callback itself must ensure that the message (or at least the result obtained from processing the message) is stored securely and available for later access.
