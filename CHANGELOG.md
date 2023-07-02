# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

<!-- uncomment the following when we're out of alpha and actually following it -->

<!-- and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## \[Unreleased\]

## \[0.2.0\] - 2023-06-26

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

