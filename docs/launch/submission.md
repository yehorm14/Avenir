# Portable submission

The delivery ZIP contains committed source, the built desktop UI, supplied evidence snapshots and a `SUBMISSION.json` file with the source revision and SHA-256 digest of every included file. Local settings, credentials, raw downloads and installed dependencies are excluded. It is a local hackathon delivery; source licence and catalogue-verification limits remain in the launch handoff.

## Run the prebuilt ZIP

Extract into a new folder. Python 3.12 or newer and an internet connection for the initial dependency installation are required. No Node installation, API key, database or cloud account is needed to run this prebuilt bundle.

From the extracted project folder on macOS/Linux:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e .
cd apps/web
../../.venv/bin/python -m uvicorn api.application:app --host 127.0.0.1 --port 4175
```

Open http://127.0.0.1:4175. On Windows, create the environment with `py -3.13 -m venv .venv`, install with `.venv\Scripts\python.exe -m pip install -e .`, then run `..\..\.venv\Scripts\python.exe -m uvicorn api.application:app --host 127.0.0.1 --port 4175` from `apps\web`.

After installation, the core flow uses local snapshots and prepared guidance. External course, learning and source websites require internet. The editable plan stays in this browser. Use a dedicated browser profile for a clean stage rehearsal.

Follow the [three-minute walkthrough](demo-script.md). Developer previews use an alternate port to preserve earlier work; the normal installation above uses 4175.

## Create a new delivery from Git

Use the [source setup](../../README.md#run-the-complete-product), run the release checks, commit source changes, and build the current UI before packaging:

```sh
npm --prefix apps/web run build
.venv/bin/python scripts/package_submission.py --output /tmp/aventier-submission.zip
```

The packager requires a clean tracked tree, runs the current-tree secret check, verifies the built page's referenced assets and rejects build symlinks. Untracked local files are excluded. It never overwrites an existing archive. Keep its output outside the checkout and use a new filename for each checkpoint. The manifest identifies the exact committed source; rebuild before packaging so the included bundle corresponds to that checkpoint.

The source README's `make check` workflow targets a Git checkout with development dependencies. The ZIP is intended for installing and running the submitted build; it does not contain Git history, `node_modules` or a Python environment.
