Add a new schema to the registry
================================

This page contains instructions for adding a new schema to the registry so that it can be loaded
using :meth:`pittgoogle.Schemas.get` and used to serialize and deserialize the alert bytes.
There are three steps:

1. Add an entry in the registry manifest with basic info about the new schema.
2. Add a subclass of :class:`pittgoogle.schema.Schema` that defines the schema methods and behavior.
3. Add schema map yaml file for translating between generic and survey-specific field names.

1. pittgoogle/registry_manifests/schemas.yml
--------------------------------------------

*pittgoogle/registry_manifests/schemas.yml* is the manifest of registered schemas.

Add a new section to the manifest following the template provided there. The fields are the same as
those of a :class:`pittgoogle.schema.Schema`. Schema names are expected to start with the name of
the survey. If the survey has more than one schema, the survey name should be followed by a "." and
then schema-specific specifier(s).

Case 1: The schema definition is not needed in order to deserialize the alert bytes. This is true for
Avro which have the schema attached in the data header and all JSON. You should be able to subclass
:class:`pittgoogle.schema.DefaultSchema` (see below). Follow :class:`pittgoogle.schema.ZtfSchema` as
a guide.

Case 2: The schema definition is required in order to deserialize the alert bytes. This is true for
all "schemaless" Avro formats which do not attach the schema to the data packet. You should be able
to subclass :class:`pittgoogle.schema.Schema` (see below). Follow :class:`pittgoogle.schema.LsstSchema`
as a guide. You you will need to provide the schema definition either by (preferred) calling an external
library (e.g., `lsst.alert.packet.schema`) or by including the schema definition files with the
pittgoogle-client package. If the latter: (1) Commit the files to the repo under the *pittgoogle/schemas*
directory. It is recommended that the main filename follow the syntax "<schema_name>.<schema_version>.avsc"
or similar. (2) Point 'path' at the main file, relative to the package root. If the Avro schema is
split into multiple files, you usually only need to point to the main one.

2. pittgoogle/schema.py
-----------------------

*pittgoogle/schema.py* is the file containing the :class:`pittgoogle.schema.Schema` classes and the
serializers they depend on.

You must add a new schema class that is based on :class:`pittgoogle.schema.Schema` (or
:class:`pittgoogle.schema.DefaultSchema`) and named like "NameSchema", where "Name" is the name of
your schema in the registry manifest in camel case (capitalize the first letter only). Your schema must
implement the required methods such as `_from_yaml`, `serialize` and `deserialize`. Follow the existing
classes as examples. Use the serializers that are defined in the class
:class:`pittgoogle.schema.Serializers` or add your own to that class if a suitable one is not already
present. Be sure to add the name of your class under 'autosummary' in the module-level docsctring
so that it will show up in the rendered docs. If your class requires a new dependency, be sure to add
it following :doc:`manage-dependencies-poetry`.

3. pittgoogle/schemas/maps/
---------------------------

*pittgoogle/schemas/maps/* is the directory containing the schema maps.

If you are adding a schema for a survey that does not yet have a schema map defined, you will need to add
a yaml file to define it. See :doc:`add-new-schema-map`.
