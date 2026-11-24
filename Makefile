.PHONY: setup tools build grf preview lint test test-fast fmt coverage install clean

PK := uv run pk

setup: tools          ## first-time setup: python deps + external tools
	uv sync

tools:                ## build pinned gorender/cargopositor into .tools/bin
	./tools/install.sh

build grf:            ## full build -> build/puenktlich.grf
	$(PK) build

preview:              ## contact sheets for all vehicles -> build/previews/
	$(PK) preview

lint:                 ## data + sprite lint, ruff
	$(PK) lint --no-sprites
	uv run ruff check .
	uv run ruff format --check .

test:                 ## unit + end-to-end tests
	uv run pytest -q

test-fast:            ## unit tests only (skips GRF compiles / renders)
	uv run pytest -q -m "not slow"

fmt:
	uv run ruff format .
	uv run ruff check --fix .

coverage:             ## completeness report -> docs/COMPLETENESS.md
	$(PK) coverage

install: build        ## copy the grfs into OpenTTD's newgrf folder (~/.local/share/openttd, Windows: Documents/OpenTTD)
	$(PK) install

clean:
	$(PK) clean
