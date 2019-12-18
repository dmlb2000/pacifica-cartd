# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2019-12-18
### Added
- Pull #92 Update to Pylint 2.0+ by [@dmlb2000](https://github.com/dmlb2000)
- Pull #93 Include testing Python 3.7 and 3.8 by [@dmlb2000](https://github.com/dmlb2000)

### Changed
- Fix #85 Add option to disable cart purge by [@dmlb2000](https://github.com/dmlb2000)
- Fix #88 Remove traceback from 404 carts by [@dmlb2000](https://github.com/dmlb2000)

## [0.5.0] - 2019-12-11
### Added
- Pull #90 add cart purge subcommand by [@karcaw](https://github.com/karcaw)
- Pull #83 Add cart dump command by [@karcaw](https://github.com/karcaw)

### Changed
- Fix #81 add help for no subcommand by [@dmlb2000](https://github.com/dmlb2000)
- Fix #86 drop support for Python 2.7 by [@dmlb2000](https://github.com/dmlb2000)
- Fix #84 fix Travis CI by [@dmlb2000](https://github.com/dmlb2000)
- Fix #82 update Development Docs by [@karcaw](https://github.com/karcaw)

## [0.4.0] - 2019-08-14
### Changed
- Fix #76 Updated testing framework by [@dmlb2000](https://github.com/dmlb2000)
- Fix #75 Add cart rebuild command by [@dmlb2000](https://github.com/dmlb2000)
- Fix #74 File download retry loop by [@dmlb2000](https://github.com/dmlb2000)

## [0.3.11] - 2019-05-16
### Added
- Download of data in the archiveinterface
- Building structure locally to serve the data
- ReadtheDocs supported Sphinx docs
- Backend file structure as directory or single tarfile
- Data checksum validation
- REST API for sending and recieving data
  - POST - Create a cart
  - GET - Get data in the cart
  - HEAD - Get cart status
  - DELETE - Delete the cart

### Changed
