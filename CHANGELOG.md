# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

<!-- uncomment the following when we're out of alpha and actually following it -->

<!-- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## \[Unreleased\]

<!-- (none) -->

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
