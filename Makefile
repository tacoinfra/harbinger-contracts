SMART_PY_CLI := ~/smartpy-cli/SmartPy.sh
OUT_DIR := ./.smartpy_out

###### AGGREGATE TARGETS ###### 

# Build everything
all:
	make test
	make compile

# Compile Everything
compile:
	make compile-normalizer
	make compile-oracle

#Test Everything
test:
	make test-normalizer
	make test-oracle

###### TESTS ###### 

# Run tests for the Normalizer contract
test-normalizer:
	$(SMART_PY_CLI) test normalizer.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

# Run tests for the Oracle contract
test-oracle:
	$(SMART_PY_CLI) test oracle.py $(OUT_DIR)
	rm -rf $(OUT_DIR)

###### COMPILE TARGETs ######

# Compile the Normalizer
compile-normalizer:
	$(SMART_PY_CLI) compile normalizer.py $(OUT_DIR)
	cp $(OUT_DIR)/normalizer/step_000_cont_0_contract.tz normalizer.tz
	rm -rf $(OUT_DIR)

# Compile the Oracle
compile-oracle:
	$(SMART_PY_CLI) compile oracle.py $(OUT_DIR)
	cp $(OUT_DIR)/oracle/step_000_cont_0_contract.tz oracle.tz
	rm -rf $(OUT_DIR)
