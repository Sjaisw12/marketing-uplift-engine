# Interview notes

## Phase 1 — reproducible scaffold

I established a versioned Python package and a locked analysis environment before
accessing the data. Configuration declares the exact corrected Criteo archive,
visit outcome, feature allowlist, holdout fraction and five development seeds.
Commands for later phases fail explicitly until implemented, so a scaffold cannot
be mistaken for a validated experiment. CI checks the package without downloading
millions of rows. Data and local MLflow outputs are excluded from Git; provenance
and readable reports will be versioned separately.

**Why isn't a fixed seed enough to prove a reproducible split?**
A seed depends on algorithm, library version and input ordering. We must bind
membership to the verified source file, persist row indices and hashes, and reuse
that registry. Phase 1 only declares seeds; Phase 3 creates the actual partitions.

**Does a dependency lockfile make the experiment fully reproducible?**
It fixes Python package resolution and distribution hashes, but not hardware,
native runtimes, data identity, randomization or every model operation. We also
need checksum verification, recorded runtime and code versions, split artifacts,
training seeds and tested procedures. Those gates are added phase by phase.

## Phase 2 — acquisition implementation (actual download pending)

I pinned both the source revision and expected file digest. Acquisition verifies
compressed bytes before publishing the archive and writes provenance only after
that verification. Cached data is rehashed, so an old manifest cannot hide later
corruption. Tiny gzip fixtures test integrity failures without accessing real
outcomes. Environment network access currently blocks the official download;
fixture success alone is not evidence that the real dataset has been acquired.

**Why record a Git revision and a SHA-256 digest?**
The revision fixes the intended repository state; the digest checks the actual
large-file bytes served through storage redirects. A matching filename or Git LFS
pointer alone cannot establish that we downloaded the corrected archive.

**Does a matching checksum prove the dataset is ready for causal analysis?**
It establishes byte identity with the specified release, not correct schema,
valid split boundaries, randomization assumptions or population representativeness.
Those are later gates. The manifest leaves actual row count null until measured.
