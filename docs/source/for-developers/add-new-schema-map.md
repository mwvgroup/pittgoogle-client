# Add a schema map

This page contains instructions for adding a new schema map.

A "schema map" maps our generic field names (keys) to the corresponding name used by the survey (values).
Pitt-Google defines this set of generic field names so that we can write code that can process
different surveys without having to worry that one survey might call the (e.g.,) time field "MJD" while
another calls it "midPointTai". This map is what makes the :meth:`pittgoogle.alert.Alert.get` method work.

Currently, we define schema maps on a per-survey basis. :meth:`pittgoogle.types_.Schema.map` will load
the yaml file for the survey :meth:`pittgoogle.types_.Schema.survey` and return it as a dictionary.
If you need something different, a more significant refactor will be required (left as an exercise
for the reader).

## Add a schema map for a new survey

*pittgoogle/schemas/maps* is the directory containing the schema maps as yaml files.

To add a schema map, make a copy of the file *pittgoogle/schemas/maps/TEMPLATE.yml* and alter it.


### How to use the TEMPLATE.yml file

*pittgoogle/schemas/maps/TEMPLATE.yml* : Make a copy of this file and name it using the syntax
*<survey_name>.yml*.

Alter the new file, keeping these important things to keep in mind:

- These key/value pairs exist to make it easier for users (which may be anyone from Pitt-Google
  Broker developers to end-user scientists) to write one piece of code that can process multiple surveys.
- The keys should be used as-is (but see below for excluding or adding keys). Changing a key's
  spelling could make things difficult for the user.
- Our schema maps support nested fields. The values in your new yaml file should be given as strings
  (for top-level fields) or lists of strings (for nested fields).
- Values given in the *TEMPLATE.yml* file are only examples or descriptions and should be substituted
  with new values appropriate for the new survey.
- While a key's *name* is fixed, we do not explicitly define how the key is to be interpreted --
  there is no ground-truth answer to the question, "Which LSST field should I assign as the 'flux'?".
- Comments are left in *TEMPLATE.yml* that note the typical data types and interpretations for each field
  to help guide your decisions.
- Try to make decisions that result in schema maps that are conceptually consistent across surveys.

### Excluding or adding field names (keys) from the set of Pitt-Google generics

Excluding fields : If your survey/schema does not need a particular key, that key does does not need to
be included in your new schema map's yaml file. There's not much code in ``pittgoogle-client`` itself
that cares what these key/value pairs actually are. Notable exceptions *may* include the survey name,
schema origin, and the IDs.

Adding fields : New keys can be added, but please do two sanity checks first.

1. Is there an existing key that can suite my needs? (if yes, stop)
2. How would this new key be interpreted if/when used with a different survey? Will it be useful or
   at least neutral (go ahead), or will it cause confusion (stop, reconsider the key's name and purpose,
   try to improve it)?

**If you define a new key, be sure to add it to the *TEMPLATE.yml* file.**

You may also want to update existing yaml files so the new key can be used with those surveys.
