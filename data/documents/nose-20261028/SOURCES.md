# NOSE sources downloaded 2026-10-28

The published 33-page paper is `NOSE-ACL-2026.acl-long.898.pdf`, downloaded from https://aclanthology.org/2026.acl-long.898.pdf. SHA256: `5b103b81c8c4bac510c0fdbfb6bb92d9cf2f4639035fcb5848c4e069b8fe73e0`.

The earlier benchmark reference is retained as `NOSE-2604.10452v2.pdf`, downloaded from https://arxiv.org/pdf/2604.10452v2. SHA256: `c1782967170b5c7a8003cb183e2816f7667c55c8038880a9a7baa5ad31c1fa71`.

The ACL paper's Tables 24 and 25 retain the precise Pearson references 0.836 for Abraham threshold and 0.715 for Keller pleasantness. Tables 3/4 and 10 retain the rounded results and dataset sizes used in the earlier local analysis. Relevant pages 26/27 were rendered and visually checked; extracted text is saved for search.

The official inference-code repository is archived at `data/checkpoints/nose-v1.0.0/source`, commit `5fa2d5c6846908bf37c6d4464b42dbd5d8dc759a`. The repository still provides inference code and no exact downstream task splits. Official released adapters were not used in the new clean-data experiments because their pretraining overlap with reserved evaluation molecules cannot be audited from the supplied release.

The original dataset is `data/raw/nose/v1.0.0/nose-smiles-descriptor-v1.0.0.csv.gz`. Its SHA256 was checked against the official release sidecar: `858e482f407a3577870a87a61f8f16b488412ed06922dd35dd8d4fe4cf5e6ff2`.

The cleaned export and its independently reconstructed canonical pair count are in `data/curated/nose-20261028-v1/manifest.json`. The original release is preserved. Cleaning does not create new measured labels or recover the absent strong/weak-positive and upstream provenance annotations.
