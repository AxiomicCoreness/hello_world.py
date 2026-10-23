# DeepInfer Dockerfile location

There is **no** root `Dockerfile.deepinfer`. The build file is:

```
argocd/Dockerfile.deepinfer
```

Kaniko jobs must pass `--dockerfile=argocd/Dockerfile.deepinfer`.
Do not add a root copy unless Kaniko tooling cannot accept a nested path;
a symlink is optional and not required for this patch.
