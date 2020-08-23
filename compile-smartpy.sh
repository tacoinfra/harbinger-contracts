#!/usr/bin/env bash

set -e -o pipefail

# SmartPy Contracts
ORACLE_CONTRACT=./oracle.py
NORMALIZER_CONTRACT=./normalizer.py

# Target Files
ORACLE_TARGET="./oracle.tz"
NORMALIZER_TARGET="./normalizer.tz"

# Output directory
OUT_DIR=./.smartpy_out

# Expected location of SmartPy CLI.
SMART_PY_CLI=~/smartpy-cli/SmartPy.sh

# Ensure we have a SmartPy binary.
if [ ! -f "$SMART_PY_CLI" ]; then
    echo "Fatal: Please install SmartPy CLI at $SMART_PY_CLI" && exit
fi

# Ensure contracts exist. Implicitly, this forces you to run the script from the
# correct dir. 
if [ ! -f "$ORACLE_CONTRACT" ]; then
    echo "Fatal: $ORACLE_CONTRACT not found. Running from wrong dir?" && exit
fi
if [ ! -f "$NORMALIZER_CONTRACT" ]; then
    echo "Fatal: $NORMALIZER_CONTRACT not found. Running from wrong dir?" && exit
fi

# Run tests to ensure contracts work.
echo "Running Tests Before Compilation"
echo ">> Testing Oracle "
$SMART_PY_CLI test $ORACLE_CONTRACT $OUT_DIR
echo ">> Oracle Tests Passed"

echo ">> Testing Normalizer "
$SMART_PY_CLI test $NORMALIZER_CONTRACT $OUT_DIR
echo ">> Normalizer Tests Passed"
echo "Tests Pass!"
echo ""

# Compile contracts
echo "Compiling Contracts"
echo ">> Compiling Oracle"
$SMART_PY_CLI compile $ORACLE_CONTRACT "OracleContract()" $OUT_DIR
echo ">> Compiling Normalizer"
$SMART_PY_CLI compile $NORMALIZER_CONTRACT "NormalizerContract()" $OUT_DIR
echo "Compilation Successful!"
echo ""

# Copy artifacts for convenience.
echo "Copying Artifacts"
cp $OUT_DIR/oracle_compiled.tz $ORACLE_TARGET
cp $OUT_DIR/normalizer_compiled.tz $NORMALIZER_TARGET
echo "Done."
echo ""

# Remove other artifacts to reduce noise.
echo "Cleaning Up...."
rm -rf $OUT_DIR
echo "Done"
echo ""

echo "All Done!"
echo ">> Oracle Contract: $ORACLE_TARGET"
echo ">> Normalizer Contract: $NORMALIZER_TARGET"
echo ""