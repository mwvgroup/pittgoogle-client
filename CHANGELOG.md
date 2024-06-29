# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

<!-- uncomment the following when we're out of alpha and actually following it -->

<!-- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## \[Unreleased\]

(none)

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
