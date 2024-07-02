Add a new schema to the registry
================================

This page contains instructions for adding a new schema to the registry so that it can be loaded
using :meth:`pittgoogle.Schemas.get` and used to serialize and deserialize the alert bytes.

You will need to update at least the "Required" files listed below, and potentially one or more of the
others. The schema format is expected to be either Avro or Json.

First, a naming guideline:

- Schema names are expected to start with the name of the survey. If the survey has more than one schema,
  the survey name should be followed by a "." and then schema-specific specifier(s).

Required
--------

pittgoogle/registry_manifests/schemas.yml
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*pittgoogle/registry_manifests/schemas.yml* is the manifest of registered schemas.

Add a new section to the manifest following the template provided there. The fields are the same as
those of a :class:`pittgoogle.schema.Schema`. The ``helper`` field must point to code that can find and load
the new schema definition; more information below.

Case 1: The schema definition is not needed in order to deserialize the alert bytes. This is true for
all Json, and the Avro streams which attach the schema in the data header. Set
``schemaless_alert_bytes='false'``. Leave ``helper`` and ``path`` as defaults.

The rest of the cases assume the schema definition is required. This is true for "schemaless" Avro streams
which do not attach the schema to the data packet. Set ``schemaless_alert_bytes='true'``

Case 2: You can write some code that will get the schema definition from an external repository. You will
probably need to write your own ``helper`` method (more below). Follow ``lsst`` as an example. This is
preferable to Case 3 because it's usually easier to access new schema versions as soon as the survey
releases them.

Case 3: You want to include schema definition files with the ``pittgoogle-client`` package. Follow
``elasticc`` as an example. (1) Commit the files to the repo under the *pittgoogle/schemas* directory. It
is recommended that the main filename follow the syntax "<schema_name>.avsc". (2) Point ``path``
at the main file, relative to the package root. If the Avro schema is split into multiple files, you
usually only need to point to the main one. (3) If you've followed the recommendations then the default
``helper`` should work, but you should check (more below). If you need to implement your own helper
or update the existing, do it.

Potentially Required
--------------------

pittgoogle/schema.py
^^^^^^^^^^^^^^^^^^^^

# [FIXME]
*pittgoogle/schema.py* is the file containing the :class:`pittgoogle.schema.Schema` class.

If ``schemaless_alert_bytes='false'``, the defaults (mostly null/None) should work and you can ignore
this file (skip to the next section).

A "helper" method must exist in :class:`pittgoogle.schema.Schema` that can find and load your new schema
definition. The ``helper`` field in the yaml manifest (above) must be set to the name of this method. If a
suitable helper method does not already already exist for your schema, add one to this file by following
existing helpers like :meth:`pittgoogle.schema.Schema.default_schema_helper` as examples. **If your helper
method requires a new dependency, be sure to add it following
:doc:`/main/for-developers/manage-dependencies-poetry`.**

pittgoogle/schemas/maps/
^^^^^^^^^^^^^^^^^^^^^^^^

*pittgoogle/schemas/maps/* is the directory containing our schema maps.

If you are adding a schema for a survey that does not yet have a schema map defined, you will need to add
a yaml file to define it. See :doc:`add-new-schema-map`.
