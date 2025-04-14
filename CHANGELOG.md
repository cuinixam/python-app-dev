# CHANGELOG



## v2.11.1 (2025-04-14)

### Fix

* fix: directory not added if the binary is in the app root ([`9c5858a`](https://github.com/cuinixam/python-app-dev/commit/9c5858a6c208c5fda7b1b200c8aec3aaad1cd80b))


## v2.11.0 (2025-04-14)

### Feature

* feat: add support for scoop apps environment variables ([`7b63034`](https://github.com/cuinixam/python-app-dev/commit/7b6303458c527f86aa980d1e86faf1f6c30b18e3))

### Fix

* fix: app directory is added by default to path ([`562372f`](https://github.com/cuinixam/python-app-dev/commit/562372fa69aeb9ea8c678d9114a19697d82377b0))


## v2.10.0 (2025-04-04)

### Feature

* feat: support version for scoop apps ([`e2484ed`](https://github.com/cuinixam/python-app-dev/commit/e2484ed58b00aced1e02ecb4d808a35ec19b40d3))


## v2.9.0 (2025-04-01)

### Feature

* feat: add environment setup scripts generator ([`a7d096b`](https://github.com/cuinixam/python-app-dev/commit/a7d096b8c1fd564f29d762b3307f567863001bae))


## v2.8.0 (2025-03-13)

### Feature

* feat: add compile commands parsing ([`237adac`](https://github.com/cuinixam/python-app-dev/commit/237adac9b05cf53efa7181dd2b172a97877bc46e))


## v2.7.0 (2025-01-22)

### Feature

* feat: capture subprocess output ([`de4960c`](https://github.com/cuinixam/python-app-dev/commit/de4960cef867b3978942216db227cfd6a1319439))


## v2.6.0 (2025-01-21)

### Feature

* feat: data register supports dynamically loaded classes ([`b4329ef`](https://github.com/cuinixam/python-app-dev/commit/b4329ef5c9b330a7010aabbccd008600df91ccdb))


## v2.5.0 (2025-01-20)

### Feature

* feat: provide generic data registry ([`a6806e2`](https://github.com/cuinixam/python-app-dev/commit/a6806e24639d44530825e72ef4074c4b08e806a2))


## v2.4.0 (2024-12-05)

### Feature

* feat: update PipelineConfig to support a Union of List and OrderedDict ([`bb919d6`](https://github.com/cuinixam/python-app-dev/commit/bb919d6462db4d94433b33c02489b11ce418c5d3))


## v2.3.3 (2024-11-28)

### Fix

* fix: powershell $PSHOME variable is not expanded ([`99f564e`](https://github.com/cuinixam/python-app-dev/commit/99f564ea42f52516f352978917432ad2c7467934))


## v2.3.2 (2024-11-23)

### Fix

* fix: powershell module path is empty ([`e42bf78`](https://github.com/cuinixam/python-app-dev/commit/e42bf7897ce49d7cf5750e554810990e43474724))


## v2.3.1 (2024-11-23)

### Fix

* fix: scoop install &#39;Get-FileHash&#39; fails ([`6fa3592`](https://github.com/cuinixam/python-app-dev/commit/6fa3592c32760f7b8a6d63026b2a1f4cf65ccdd8))

* fix: scoop.cmd ignores the powershell proxy settings ([`44daef6`](https://github.com/cuinixam/python-app-dev/commit/44daef67ee734b94b2f0f8bfe1afd13c43ecc7df))


## v2.3.0 (2024-05-15)

### Feature

* feat: execute runnables without dependency management ([`04c8799`](https://github.com/cuinixam/python-app-dev/commit/04c879935054911426886adaf9dc8f6cfcb39716))


## v2.2.0 (2024-04-13)

### Documentation

* docs: move information from internals to features ([`97231d6`](https://github.com/cuinixam/python-app-dev/commit/97231d6d1a2c6029171cee4a69f4c5ec830727db))

### Feature

* feat: add dry_run option for executing runnables ([`927a662`](https://github.com/cuinixam/python-app-dev/commit/927a662dbb61a5287587677dacd3ef51d1df641a))

* feat: add custom configuration for steps ([`5c056d1`](https://github.com/cuinixam/python-app-dev/commit/5c056d10f133240a86a8bcaa6dadd73f08378b4f))

### Fix

* fix: semantic versioning can not build package with poetry ([`92d65d2`](https://github.com/cuinixam/python-app-dev/commit/92d65d21900beb1301e408cb696338aefa3ada9e))


## v2.1.1 (2024-04-12)

### Fix

* fix: scoop wrapper finds apps twice ([`4b704ad`](https://github.com/cuinixam/python-app-dev/commit/4b704ad615cfb91cbf51748be46b9a15a7e85585))


## v2.1.0 (2024-02-18)

### Feature

* feat: add option to force runnable execution ([`06fde72`](https://github.com/cuinixam/python-app-dev/commit/06fde72d02d4f040bd1c756e9e6f33484a082c2c))


## v2.0.0 (2024-02-17)

### Breaking

* feat!: make the pipeline loader generic ([`b516274`](https://github.com/cuinixam/python-app-dev/commit/b5162749433af13f14057aa278b5cbcc2df36142))


## v1.13.0 (2024-01-18)

### Feature

* feat: support deserialize method ([`17e063d`](https://github.com/cuinixam/python-app-dev/commit/17e063ddb39a94eb1d248403239d299511563d88))


## v1.12.0 (2024-01-15)

### Feature

* feat: support lists for registering arguments ([`64e477f`](https://github.com/cuinixam/python-app-dev/commit/64e477f27ff65e25fc46fa0647a1c2096892af14))


## v1.11.0 (2024-01-11)

### Feature

* feat: clear log file ([`76d1e08`](https://github.com/cuinixam/python-app-dev/commit/76d1e080d2879a71142adb1636cc1ea2031c0022))


## v1.10.0 (2024-01-11)

### Feature

* feat: add log to file context manager ([`a333716`](https://github.com/cuinixam/python-app-dev/commit/a3337164ce358de00f7dec9c5f67caac5118b814))


## v1.9.0 (2023-12-09)

### Feature

* feat: use shell for subprocess executor ([`baced78`](https://github.com/cuinixam/python-app-dev/commit/baced787c081f746fd21abf007d76a8cfdca0481))


## v1.8.2 (2023-11-26)

### Fix

* fix: application path is not in required paths ([`d1927ed`](https://github.com/cuinixam/python-app-dev/commit/d1927edc78ec0932c6310fa14cbc0434d9feecdb))


## v1.8.1 (2023-11-26)

### Fix

* fix: single env path is not parsed properly ([`6a4bb3e`](https://github.com/cuinixam/python-app-dev/commit/6a4bb3e948fc2730ccd3f2ff84023554cb63ca59))


## v1.8.0 (2023-11-26)

### Feature

* feat: read env paths for scoop tools ([`a253165`](https://github.com/cuinixam/python-app-dev/commit/a253165356672764d80288664f5ff57dbdbad12a))


## v1.7.0 (2023-11-26)

### Feature

* feat: suprocess executor can override the env ([`c51a413`](https://github.com/cuinixam/python-app-dev/commit/c51a4138f415ee7d4342dea4c4292556c32ee188))


## v1.6.2 (2023-11-26)

### Fix

* fix: wrong scoop executable is returned ([`3867df0`](https://github.com/cuinixam/python-app-dev/commit/3867df07643dcde3e1ca484091e70aa458a1630d))


## v1.6.1 (2023-11-26)

### Fix

* fix: wrong scoop executable is returned ([`f1a6a6a`](https://github.com/cuinixam/python-app-dev/commit/f1a6a6ae598e7cc55a926e704e7870fe298c4100))


## v1.6.0 (2023-11-25)

### Feature

* feat: check if scoop is installed in user home ([`007cf6a`](https://github.com/cuinixam/python-app-dev/commit/007cf6a6d349483a6cbeb170168b840a4fdc5acb))


## v1.5.1 (2023-11-02)

### Fix

* fix: optional arguments type is wrong ([`9687f6a`](https://github.com/cuinixam/python-app-dev/commit/9687f6a634046d16aee3d4f3b738b3ff31ef1c6a))


## v1.5.0 (2023-10-25)

### Feature

* feat: subprocess print stdout in realtime ([`78dc4ac`](https://github.com/cuinixam/python-app-dev/commit/78dc4ac02f9a1ff85cd45c697f2538757994683a))


## v1.4.1 (2023-10-24)

### Fix

* fix: exception is thrown if file is not found ([`4b44d10`](https://github.com/cuinixam/python-app-dev/commit/4b44d10d7f2d5eae9fa37768d626c216f7ac7848))


## v1.4.0 (2023-10-24)

### Feature

* feat: executor support for always run runnables ([`8015b85`](https://github.com/cuinixam/python-app-dev/commit/8015b858d457691978c6d161a990ae492fa5015c))


## v1.3.0 (2023-10-22)

### Feature

* feat: support registering arguments with action ([`0fc0261`](https://github.com/cuinixam/python-app-dev/commit/0fc02617712afdacd63b622bf69114542009d64e))


## v1.2.0 (2023-09-30)

### Feature

* feat: support directories as dependencies ([`da98390`](https://github.com/cuinixam/python-app-dev/commit/da983901e3c4d4b354ab7c57f61859962391cef7))


## v1.1.0 (2023-09-30)

### Documentation

* docs: remove username from project title ([`991cf61`](https://github.com/cuinixam/python-app-dev/commit/991cf61ab45533a1d31e356a9d6c2e02c276ff17))

### Feature

* feat: support callbacks with any number of args ([`5304ca6`](https://github.com/cuinixam/python-app-dev/commit/5304ca6f94e270792a2c742dfb23f7d20a5abcd0))


## v1.0.0 (2023-09-18)

### Breaking

* feat!: rename module to py-app-dev ([`206b8ac`](https://github.com/cuinixam/python-app-dev/commit/206b8ac6c5e43cb36fdf4172fe7b14c782185329))


## v0.1.1 (2023-09-15)

### Fix

* fix: optional types are not optional arguments ([`5a64123`](https://github.com/cuinixam/python-app-dev/commit/5a64123f8f049d90788e566892c226e2ddd4b68f))


## v0.1.0 (2023-09-10)

### Feature

* feat: make view class generic ([`3a641b7`](https://github.com/cuinixam/python-app-dev/commit/3a641b74839639351661d8a230c46662ad56e7f0))

