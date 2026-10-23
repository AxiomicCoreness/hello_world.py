# DeepInfer / kernel pin manifest

Recorded from `deepseek-ai/DeepInfer` commit
`9bd9cf243fc53ef9afbf8f04d391d989117d6ab9` (main, 2026-10-21).
Vendor directory contents at that commit (gitlink SHAs):

| Path | Commit SHA |
|------|------------|
| vendor/DeepInfer | `9bd9cf243fc53ef9afbf8f04d391d989117d6ab9` |
| vendor/DeepGEMM | `1fc9c66975ee322d628b3288534ca0e9ce12a64d` |
| vendor/FlashMLA | `2e5429fc5653bab6e081f09477126f731882a6a9` |
| vendor/DeepEP | `f6aa38fe06cd4a0489e7730365d4e0114970a2f3` |
| vendor/DeepSelect | `bfa4507d935f17ebfc3d0f00ff7d3c9a4d0e5c18` |
| vendor/DeepGEMM-Ascend | `3a35326271b069b8b5bf1a754435acd6cc91575b` |
| vendor/DeepEP-Ascend | `3b25377d04b24fc6154698ded78a2bcb2c59afff` |

Do **not** float on `main`. Run `scripts/init_deepinfer_vendors.sh` to clone and
`git checkout` these SHAs, then `git add` the gitlinks when landing a follow-up.

`vendor/teavm-sync` and `vendor/backend-workers` are Axiomic submodules; this
script does not pin them.
