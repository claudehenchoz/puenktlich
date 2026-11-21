# Releasing

1. Bump `version` in `pyproject.toml`. The GRF `version` property is derived from it, as `major*10000 + minor*100 + patch`.
2. `make lint test build`. Check the set in-game.
3. Commit, then `git tag vX.Y.Z && git push --tags`. The `Release` workflow attaches `puenktlich-X.Y.Z.tar` to a GitHub release.
4. **BaNaNaS** (in-game content service): upload the tar at <https://bananas.openttd.org> (OpenTTD account via GitHub). The first upload assigns the content id. After that, uploads can be automated with [bananas-cli](https://github.com/OpenTTD/bananas-cli) and a `BANANAS_TOKEN` secret.

Before the first public release:
- Set `min_compatible_version` deliberately in `nml/generate.py` once save compatibility matters.
- Never change the GRFID, item ids or livery order after release.
