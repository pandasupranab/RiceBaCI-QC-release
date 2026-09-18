# Executable environments

Paper 2 uses two explicit environments because numerical analysis and rendered
figure bytes are different reproducibility claims.

- `analysis.json` and `requirements-analysis.txt` describe the environment that
  must run the statistical pipeline. BLAS identity is recorded in the check
  receipt, not claimed to be portable or pinned by pip.
- `figures.json` and `requirements-figures.txt` describe the environment that
  produced the committed figure bytes. FreeType and zlib are native-library
  requirements; pip alone does not install or guarantee those exact builds.

Create separate virtual environments with Python 3.12.14 and install the
matching requirements file. This is the Windows replay environment recorded
in `Reproducibility_2026-09-14/verification/environment.json`; the older root
requirements note naming Python 3.11.15 describes an earlier production
environment and is not evidence that 3.11.15 performed the independent replay.
Then run, from the repository root:

```text
python python/environment_check.py --profile analysis --receipt results/analysis-environment.json
python python/environment_check.py --profile figures --receipt results/figure-environment.json
```

The command fails on a version mismatch. A passing analysis check does not
establish figure-byte reproduction; a passing figure check does not establish
scientific-result reproduction. Neither specification promises cross-platform
byte identity.
