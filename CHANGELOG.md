# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

<!-- uncomment the following when we're out of alpha and actually following it -->

<!-- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## \[Unreleased\]

### Added

- Schema maps
    - Added ZTF 'lite' schema map

### Fixed

- `Topic.publish()`: Message attributes were improperly defined

## \[v0.3.13\] - 2025-04-04

### Added

- `Alert`:
    - Properties: `ra`, `dec`, `healpix9`, `healpix19`, `healpix29`, `name_in_bucket`.
    - Add healpix properties to `Alert.attributes`.
- `Schema`:
    - Properties: `_name_in_bucket`, `serializer`, and `deserializer`. The last two can be used to
      switch between JSON and Avro on the fly.
    - Methods to support the LSST schema consolidation.
    - Schema map for the default schema.
- `Topic.publish()`: new keyword arg `drop_cutouts`.
- Dedicated classes for all schemas, including `DefaultSchema`, `ElasticcSchema`, `LsstSchema`,
  `LvkSchema`, and `ZtfSchema`. These are subclasses of `pittgoogle.Schema`.
- `schema.Serializers` class to hold all serializers and deserializers used by the schemas.
- Unit tests:
    - Tests for new `Alert` properties.
    - Tests for `Schema` and `Serializers`.
    - Randomly generated data for schema "lsst.v7_4.alert".
- Schema maps
    - LSST support for `ssObjectId`

### Changed

- `Alert`:
    - `from_*` methods now call `Schema._init_from_msg` so the schema version can be retrieved from the message.
    - `Schema.version` is now added to the `attributes` automatically.
- `Schema`:
    - Consolidate LSST schemas into one. Name is "lsst".
    - Change default schema name "default_schema" -> "default".
    - `serialize` and `deserialize` methods moved to `schema.Serializers`.
    - JSON serializer now accepts dicts containing bytes values.
- `Topic.publish()` now handles the duties of `Alert._prep_for_publish()` (which is removed).
- Documentation updated with new instructions for developers to implement support for a new schema.
- Unit tests:
    - Move `conftest.SampleAlert` -> `load_data.TestAlert`
    - Split `TestAlert` -> `TestAlertFrom`, `TestAlertProperties`, and `TestAlertMethods`

### Fixed

- Fix issue #76. Make `Alert.dataframe` succeed even when there are no previous sources.

### Removed

- `Alert._prep_for_publish()`. Equivalent functionality was added to `Topic.publish()`.
- `SchemaHelpers` class removed. These have been promoted to full `Schema` classes.
- `Schema._init_from_msg`. This functionality was moved to the `Schema._from_yaml` class methods.

## \[v0.3.12\] - 2025-03-07

### Added

- Data listings and references for LSST
- Support for LSST schema versions 7.2, 7.3, and 7.4
- README.md describing where the new LSST alert schemas were obtained.
- Add '\_\_package_path__' as a package-level variable.
- Add test data for LSST, LVK, and ZTF.
- Add unit tests for:
    - `registry.Schemas`
    - `alert.Alert`
    - `utils.Cast`
- Add `Alert` properties and methods:
    - `skymap`
    - `drop_cutouts`
    - `_prep_for_publish`
    - `_str_to_datetime`
- Add class `alert.MockInput` with support for Cloud Functions
- Add dependencies `hpgeom` and `google-cloud-functions`.

### Changed

- Update data listings for ZTF and LVK
- `schema.py` now specifies all schema versions that are available for LSST
- Schema mappings for new LSST alert versions incorporated into `schemas.yml`
- Implement `schema._ConfluentWireAvroSchema.serialize`.
- Add IDs to `Alert.attributes` the first time it is accessed.
- Dependencies: Lazy load astropy.

### Removed

- Remove `utils.Cast._strip_cutouts_ztf` (moved to `Alert`)

## \[v0.3.11\] - 2024-07-22

### Added

- Add 'Surveys' documentation section with pages for ZTF and LVK.
- Add LVK to Data Listings page.

### Changed

- Reorganize and update data listings.
- Add FAQ content.
- Clean up docs. Remove 'TODO's. Add autosummary to module pages.
- Update Google pricing on FAQ Costs.

## \[v0.3.10\] - 2024-07-22

### Added

- Add `bigquery.Client` class.
- Add class attributes `Table.query`, `Table.schema`.
- Add dependency on 'db-dtypes' to support BigQuery -> Pandas.

### Changed

- Remove `Table.auth` and simplify `Table.client`. This functionality is now managed by
  `bigquery.Client`.
- In `Table` and `Topic`, the project ID is no longer changed away from what the user provided.
  It was more confusing and dangerous than it was helpful.

### Removed

- `Table.auth`

## \[v0.3.9\] - 2024-07-02

### Changed

- Minor documentation updates.

## \[v0.3.8\] - 2024-07-02

### Changed

- Loosen `astropy` version restriction to ">=5.3". `astropy` v<6.0.0 is required by `supernnova` v3.0.1
  which is not a direct dependency of `pittgoogle-client` but is often used with it.

## \[v0.3.7\] - 2024-07-02

### Added

- A default schema to be used when no schema is provided.
- Child classes for `schema.Schema` that are specific to different serialization formats.

### Fixed

- Support for the latest LSST schema version (lsst.v7_1.alert). Note that this is the only LSST schema
  version currently supported.

### Changed

- Renamed `exceptions.SchemaNotFoundError` -> `exceptions.SchemaError`, repurposed for more general use.
- Updates to documentation.

### Removed

- Removed `exceptions.OpenAlertError`. Use `exceptions.SchemaError` instead.
- Removed dependency on `lsst-alert-packet` package. We cannot install this from a git repo and also
  publish our package to PyPI. Need to figure out how to fix this. Without it,
  'schema.SchemaHelper.lsst_auto_schema_helper' will not work.

## \[v0.3.6\] - 2024-07-01

### Changed

- Renamed `exceptions.PubSubInvalid` -> `exceptions.CloudConnectionError`, repurposed for more general use.

## \[v0.3.5\] - 2024-07-01

### Added

- Support for the LSST alert schema.
- `types_.Schema._from_yaml` class method and the related helpers `_local_schema_helper` and
  `_lsst_schema_helper`.
- Dependency on `lsst-alert-packet` package for the `_lsst_schema_helper`.
- `types_.Schema.schemaless_alert_bytes` bool indicating whether the alert bytes are schemaless
  and thus a `types_.Schema.definition` is required in order to serialize and deserialize them.
- `types_.Schama.manifest` containing the schemas.yml file loaded as a list of dicts.
- `types_.Schema.filter_map`, moved from the schema map's "FILTER_MAP".
- `Schema.origin` and schema-map key name "SCHEMA_ORIGIN" (see Changed).
- `types_.Schema.definition`. Not actually new, but repurposed (see Changed, Removed).

### Fixed

- Don't let `Subscription._set_topic` clobber an existing topic attribute. This was preventing the user
  from creating a subscription attached to a topic in a different project.

### Changed

- Changed some schema-map keys to include an underscore for clarity, e.g., "magerr" -> "mag_err"
  (breaking change).
- Change method to private `Alert.add_id_attributes` -> `Alert._add_id_attributes`.
- Changed attribute name `types_.Schema.definition` -> `Schema.origin`. Related, changed
  schema-map key name "SURVEY_SCHEMA" -> "SCHEMA_ORIGIN". Both for clarity.
- `types_.Schema.definition` is now used to hold the actual schema definition. Currently this only
  needed for Avro and so holds the dict loaded from the ".avsc" file(s).
- Update docstrings for clarity and accuracy.
- Improve type hints.
- Fix up Sphinx and rst to improve how docs are being rendered.

### Removed

- `types_.Schema.avsc`. Replaced by `types_.Schema.definition`.
- Schema-map keys "SURVEY_SCHEMA" (replaced), "TOPIC_SYNTAX" (dropped), "FILTER_MAP" (moved).

## \[v0.3.4\] - 2024-06-29

### Added

- Documentation pages for `alert` and `types_`.

### Changed

- Updated docs dependencies. This helped fix a bug that was preventing some documentation from building.
- Modernized some type hints to (e.g.,) use ` | ` instead of `typing.Optional`.
- Moved usage examples into the respective class docstrings.
- Cleaned up some documentation verbiage and Sphinx directives.

## \[v0.3.3\] - 2024-06-28

### Changed

- Minor documentation updates.

## \[v0.3.2\] - 2024-06-28

### Added

- PubSubInvalid exception. Raised when an invalid Pub/Sub configuration is encountered.

### Changed

- Major documentation reorganization and updates.
- Rename the PubSub.Consumer parameter batch_maxwait -> batch_max_wait_between_messages for clarity.

## \[v0.3.1\] - 2024-06-26

### Added

- Subscription.purge method.

### Fixed

- Bugfix message format in Alert.from_cloud_run.

### Changed

- Updated dependencies in poetry.lock file to latest versions.
- Relaxed pandas version pin in pyproject.toml file (for SuperNNova library).

### Removed

- pittgoogle_env.yml file

## \[v0.3.0\] - 2024-06-08

### Added

- `Alert` and `Table` classes.
- Registry for alert schemas and GCP Project IDs.
- Alert schemas (Avro) and schema maps (yaml).
- Exceptions: `BadRequest` and `SchemaNotFoundError`.
- Types: `PubsubMessageLike` and `Schema`.
- ZTF Figures Tutorial

### Changed

- Major updates to `pubsub` classes.
- Make README.md point to the new docs.

### Removed

- `figures` module (content moved to tutorial). This allowed the removal of the following explicit
    dependencies: `aplpy`, `matplotlib`, `numpy`. Content moved to ZTF Figures Tutorial.
- v0.1 `bigquery` functions.
- Setup and requirements files that are no longer needed after switching away from Read The Docs.

## \[v0.2.0\] - 2023-07-02

### Added

- `auth` module supporting authentication via a service account or oauth2
- `exceptions` module with class `OpenAlertError`
- "Overview" section in docs
- classes in `utils` module: `ProjectIds`, `Cast`
- files: `CHANGELOG.md`, `pittgoogle_env.yml`

### Changed

- Overhaul the `pubsub` module. Add classes `Topic`, `Subscription`, `Consumer`, `Alert`,
  `Response`.

### Fixed

- cleanup some issues flagged by Codacy
