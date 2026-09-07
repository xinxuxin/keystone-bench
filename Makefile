# Keystone: rebuild the release, run the checks, evaluate a model.
PY ?= python
MODEL ?= openrouter/openai/gpt-5.6-terra
JUDGE ?= openrouter/anthropic/claude-sonnet-5

.PHONY: data check test quick full regress judge-check site

data:            ## fetch HealthBench, replay the shipped edits, rebuild dist/ byte for byte
	$(PY) tools/build_release.py && $(PY) tools/build_release.py --check

check: data      ## mechanical quality checks and the degenerate-strategy test on the rebuilt release
	$(PY) tools/quality_checks.py > /dev/null && $(PY) tools/trivial_baselines.py > /dev/null && keystone validate

test:            ## the test suite (no keys needed)
	$(PY) -m pytest -q tests

quick:           ## first run: the fixed quick set, every family
	keystone run --family all --layer quick --model $(MODEL) --judge $(JUDGE) --out runs/quick__$(subst /,_,$(MODEL))

full:            ## the strict layer, every family (see `keystone estimate --family all --layer strict` first)
	keystone run --family all --layer strict --model $(MODEL) --judge $(JUDGE) --out runs/strict__$(subst /,_,$(MODEL))

regress:         ## what B fixed and regressed relative to A: make regress A=runs/x B=runs/y
	keystone regress $(A) $(B)

judge-check:     ## does the judge separate the six authored reply types
	$(PY) tools/judge_check.py --judge $(JUDGE)

site:            ## preview the project page
	$(PY) -m http.server 8791 --directory site
