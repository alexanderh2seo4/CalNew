# Curated NOSE training associations

The release is preserved under data/raw/nose/v1.0.0. This export canonicalizes molecules, removes repeated pairs, quarantines invalid/disconnected structures, excludes all existing reserved molecular groups, and additionally excludes every Abraham, Keller and Ravia development connectivity. Stereochemical IDs are preserved.

associations.parquet joins molecules.parquet on molecule_id. binary-associations.npz uses molecules.parquet row order and vocabulary.csv term_id columns. Labels remain augmented associations with unknown strong/weak origin. Do not treat them as measured intensity, negative labels or independently validated sensory observations. The additional development exclusion creates a conservative transfer corpus; more exclusions may be needed for new endpoints.

See manifest.json for counts, source checksum and all verification checks. Underlying source rights still apply.
