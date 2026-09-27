PYTHON ?= python3
.PHONY: verify scan validate figures tables reproduce-public reproduce-full aggregate-audits paper
verify scan validate figures tables reproduce-public reproduce-full aggregate-audits:
	$(MAKE) -C artifact $@ PYTHON="$(PYTHON)"
paper:
	mkdir -p .build/paper
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=../.build/paper main.tex
