# Harbinger Contracts

This repository contains reference implementations for the smart contracts that make up Harbinger.  To get started with Harbinger, visit the [main documentation](https://github.com/tacoinfra/harbinger).

This library provides functionality for interacting with the Harbinger oracle system. Users who want to post prices might also be interested in [Harbinger CLI](https://github.com/tacoinfra/harbinger-cli) or  [Harbinger Poster](https://github.com/tacoinfra/harbinger-poster) which is a hosted component providing similar functionality for posting data to Harbinger. Entities who wish to sign prices for Harbinger may want to look at [Harbinger Signer](https://github.com/tacoinfra/harbinger-signer). Developers of new Harbinger components may be interested in [harbinger-lib](https://github.com/tacoinfra/harbinger-lib).

## File Structure

The following source files produce oracle and normalizer contracts:
- `oracle.py`: The Harbinger oracle contract
- `normalizer.py`: The Harbinger normalizer contract

For convenience, these two contracts are precompiled to Michelson in `oracle.tz` and `normalizer.tz`, respectively. If you wish to compile the contracts yourself, please see 'Building and Testing' below.

Additionally, the following files provide helper functionality and are not top-level contracts:
- `fifo_queue.py`: A FIFO queue implementation
- `common.py`: Common utility functions 

## Building and Testing

Harbinger contracts are written in [SmartPy](https://smartpy.io/). Please consult the [SmartPy Documentation](https://smartpy.io/demo/reference.html) for instructions on how to install and get started with the SmartPy command line tools. 

You can run tests and compile with:
```shell
$ make all
```

To manually compile a contract:
```shell
$ make compile-minter
$ make compile-normalizer
```

To manually test a contract: 
```
$ make test-minter
$ make test-normalizer
```

## Contract Specifications

The provided contracts are reference implementations for a Harbinger implementation. It is possible to provide alternative implementations of these contracts as long as they conform to the same ABI.

### Oracle Contract Specifications

Oracle contracts are bound to a single price feed and can contain an unlimited number of assets. All updates must be monotonically increasing in start time.

Specifically, the oracle contract can be configured with the following parameters:
- **Signer Public Key:** The public key of the **signer** which provides the price feed for the oracle.
- **Asset List:** A list of assets that the oracle will keep track of. Higher numbers of assets lead to increased gas and storage fees when interacting with the oracle. 

An oracle contract has the following entrypoints:
- **`update`**: Receives an signed set of updates to the oracle contract.
- **`push`**: Pushes the data in the Oracle to a normalizer contract.
- **`revoke`**: Revokes an oracle contract by removing the signer public key. This effectively triggers an emergency shutdown of the Oracle.

### Normalizer Contract Specifications

Normalizer contracts normalize a single asset and can only receive updates from one Oracle.  All updates must be monotonically increasing in start time.

Specifically, the normalizer contract can be configured with the following parameters:
- **Oracle Contract Address:** The address of the oracle contract which provides updates.
- **Asset Name:** The name of the asset that the contract will normalize.
- **Number of Data Points:**: The number of data points to store and normalize. Higher numbers of data points lead to increased gas and storage fees when interactin with the normalizer.

A normalizer contract has the following entrypoints:
- **`update`**: Receives data from an oracle contract.

## Credits

Harbinger is written and maintained by [Luke Youngblood](https://github.com/lyoungblood) and [Keefer Taylor](https://github.com/keefertaylor). 
