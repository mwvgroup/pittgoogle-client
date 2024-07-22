Add a new schema to the registry
================================

This page contains instructions for adding a new schema to the registry so that it can be loaded
using :meth:`pittgoogle.Schemas.get` and used to serialize and deserialize the alert bytes.
Only Avro and JSON schemas have been implemented so far.

First, a naming guideline:

- Schema names are expected to start with the name of the survey. If the survey has more than one schema,
  the survey name should be followed by a "." and then schema-specific specifier(s).

pittgoogle/registry_manifests/schemas.yml
-----------------------------------------

*pittgoogle/registry_manifests/schemas.yml* is the manifest of registered schemas.

Add a new section to the manifest following the template provided there. The fields are the same as
those of a :class:`pittgoogle.schema.Schema`.

Case 1: The schema definition is not needed in order to deserialize the alert bytes. This is true for
all Json, and the Avro streams which attach the schema in the data header. You should be able to use the
default helper (see below).

The rest of the cases assume the schema definition is required. This is true for "schemaless" Avro streams
which do not attach the schema to the data packet.

Case 2: You can write some code that will get the schema definition from an external repository. You will
probably need to write your own helper method (more below). Follow LSST as an example. This is
preferable to Case 3 because it's usually easier to access new schema versions as soon as the survey
releases them.

Case 3: You want to include schema definition files with the pittgoogle-client package. Follow
ELAsTiCC as an example. (1) Commit the files to the repo under the *pittgoogle/schemas* directory. It
is recommended that the main filename follow the syntax "<schema_name>.avsc". (2) Point 'path'
at the main file, relative to the package root. If the Avro schema is split into multiple files, you
usually only need to point to the main one. (3) If you've followed the recommendations then the default
helper should work, but you should check (more below). If you need to implement your own helper
or update the existing, do it.

pittgoogle/schema.py
--------------------

*pittgoogle/schema.py* is the file containing the :class:`pittgoogle.schema.Schema` class and helpers.

A "helper" method must exist in :class:`pittgoogle.schema.SchemaHelpers` that can find and load your new schema
definition. The 'helper' field in the yaml manifest (above) must be set to the name of this method. If a
suitable helper method does not already already exist for your schema, add one to this file by following
existing helpers like :meth:`pittgoogle.schema.SchemaHelpers.default_schema_helper` as examples. **If your helper
method requires a new dependency, be sure to add it following
:doc:`/main/for-developers/manage-dependencies-poetry`.**

pittgoogle/schemas/maps/
^^^^^^^^^^^^^^^^^^^^^^^^

*pittgoogle/schemas/maps/* is the directory containing our schema maps.

If you are adding a schema for a survey that does not yet have a schema map defined, you will need to add
a yaml file to define it. See :doc:`add-new-schema-map`.
