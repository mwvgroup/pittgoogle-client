# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

<!-- uncomment the following when we're out of alpha and actually following it -->

<!-- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## \[Unreleased\]

### Added

-   `Alert` and `Table` classes.
-   Registry for alert schemas and GCP Project IDs.
-   Alert schemas (Avro) and schema maps (yaml).
-   Exceptions: `BadRequest` and `SchemaNotFoundError`.
-   Types: `PubsubMessageLike` and `Schema`.
-   ZTF Figures Tutorial

### Changed

-   Update PubSub classes.
-   update README.md to point to the new docs
-   remove setup and requirements files that are no longer needed after switching away from Read The Docs

### Removed

-   `figures` module (content moved to tutorial). This allowed the removal of the following explicit
    dependencies: `aplpy`, `matplotlib`, `numpy`.
-   v0.1 BigQuery functions.

## \[0.2.0\] - 2023-07-02

### Added

-   `auth` module supporting authentication via a service account or oauth2
-   `exceptions` module with class `OpenAlertError`
-   "Overview" section in docs
-   classes in `utils` module: `ProjectIds`, `Cast`
-   files: `CHANGELOG.md`, `pittgoogle_env.yml`

### Changed

-   Overhaul the `pubsub` module. Add classes `Topic`, `Subscription`, `Consumer`, `Alert`,
  `Response`.

### Fixed

-   cleanup some issues flagged by Codacy
