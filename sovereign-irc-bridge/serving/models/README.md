# models/ — drop-in folder for the Kaggle GGUF

Place `deepseek-r2-1.5b-Q4_K_M.gguf` (from
https://www.kaggle.com/models/clarkeyoursatee/deepseek-r2-1-5b-q4-k-m) in this folder.
Everything here except this README and `.gitignore` is git-ignored, so the weights are never committed.

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
