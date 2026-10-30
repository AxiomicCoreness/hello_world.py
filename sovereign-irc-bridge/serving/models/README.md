# models/ — drop-in folder for the Kaggle GGUF

Place `deepseek-r2-1.5b-Q4_K_M.gguf` (from
https://www.kaggle.com/models/clarkeyoursatee/deepseek-r2-1-5b-q4-k-m) in this folder.
Everything here except this README, `.gitignore` and `fetch-deepseek-r2.sh` is git-ignored, so the weights are never committed.

## Direct download (phones / PocketPal AI)

Single verified file, no reassembly needed:

https://github.com/AxiomicCoreness/hello_world.py/releases/download/model-deepseek-r2-1.5b-q4km-v1/deepseek-r2-1.5b-Q4_K_M.gguf

sha256 `80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1`, 1,117,320,640 bytes
(checksum also in the `deepseek-r2-1.5b-Q4_K_M.gguf.sha256` asset). On an iPhone, open the URL in
Safari, save to Files, then import it in PocketPal AI.

## Fetch from GitHub (single file, falls back to 25 MB chunks)

The same GGUF is published as 42 × 25 MB release assets (tar.gz split) on the pre-release
[`model-deepseek-r2-1.5b-q4km-v1`](https://github.com/AxiomicCoreness/hello_world.py/releases/tag/model-deepseek-r2-1.5b-q4km-v1),
with `SHA256SUMS` covering every part, the full `.tar.gz` and the `.gguf`. `fetch-deepseek-r2.sh` downloads the
single `.gguf` asset first and checks its sha256; only if it is missing or mismatched does it download, verify,
reassemble and extract the parts into this folder (`SKIP_SINGLE=1` forces the parts path):

```sh
./fetch-deepseek-r2.sh               # no token needed; uses public release URLs via curl
DEST=/other/dir ./fetch-deepseek-r2.sh
```

On the parts path the script checks each part's sha256, the reassembled archive's sha256 and the final GGUF sha256, and exits non-zero on any mismatch.
Windows users can download the single file from the URL above, or use `reassemble-deepseek-r2.ps1`
(a release asset, not in this repo) for the parts.

Expected file:

- name: `deepseek-r2-1.5b-Q4_K_M.gguf`
- size: 1,117,320,640 bytes
- sha256: `80a49c2fe2410f704ceda4590212174a99899341b01e6af5433319481179e5c1`

Verify before launching:

```sh
sha256sum deepseek-r2-1.5b-Q4_K_M.gguf      # Linux
shasum -a 256 deepseek-r2-1.5b-Q4_K_M.gguf  # macOS
```

Then start the server (127.0.0.1:8085 only):

```sh
../launch-8085-deepseek-r2.sh
```

The launch script checks the file exists and its sha256 matches, and exits with an error otherwise.

## Single-file asset

The joined file was attached by the `join-gguf-release` workflow (`.github/workflows/join-gguf-release.yml`),
which verifies the sha256 before uploading. Direct URL: https://github.com/AxiomicCoreness/hello_world.py/releases/download/model-deepseek-r2-1.5b-q4km-v1/deepseek-r2-1.5b-Q4_K_M.gguf
