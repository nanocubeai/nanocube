# Changelog

All notable changes to the CubedPandas project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Categories: Added, Changed, Fixed, Deprecated, Removed, Security, Fixed, Security

## [0.2.32] - in progress

### Added

- DateFilter class added to parse and filter by time text like "today", "yesterday", "last week", etc.
  and direct support for lambda function to filter Pandas or Numpy arrays or lambdas for Python internal use.
- Tokenizer and parser classes for time text parsing.
- DateSpan class added for handling of begin-end time spans.
- Added cubed() method to Context to create new cube from filtered cube.
### Changed
### Fixed


## [0.2.31] - 2024-09-09

### Added
- Added automated testing for real-world data sets located in`tests/datasets`.
- Added first version of time series intelligence. Needs full redesign.
- Added support for boolean string keywords as member names.
  True values: `true`, `t`, `1`, `yes`, `y`, `on`, `1`, `active`, `enabled`, `ok`, `done`
  False values: everything else
- Added support for `in` operator = `__contains__` method on DimensionContext to test
  if a member is contained in a dimension.
### Fixed
- NaN member names and values not properly recognized, #non.
- Member names containing `,` delimiter not properly recognized, #non.
- Numpy `__array_priority__` attribute calls not recognized and handled, #non.
- MkDocs documentation build on GitHub failing. Switched to static upload as a temp. solution, #non.


## Earlier changes

Earlier changes, before [0.2.30], are not documented here as a comprehensive
redesign and refactoring of the initial code base was done.
