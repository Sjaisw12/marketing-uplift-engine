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

## Phase 2 — verified dataset acquisition

I made acquisition reproducible by using a full repository commit and the exact
corrected v2.1 filename. The command streams compressed bytes to a temporary file,
then measures its actual size and calculates SHA-256 from disk. Only a matching
file becomes the published raw archive. An interrupted or corrupt download fails
without publishing it. Repeat runs verify the local file again without another
network download. The small provenance manifest can be reviewed in Git while the
311 MB archive stays outside Git. The manifest explicitly separates expected rows
from observed rows: acquisition has not parsed or counted any records.

**Does a matching SHA-256 prove that the data is valid for causal inference?**
No. It binds our local bytes to the reviewed reference digest, assuming that
reference is trustworthy. It does not validate schema, row count, randomized
assignment, missingness, or causal identification. Those require later, separately
approved checks. A file-size check catches truncation cheaply but cannot detect
same-size corruption; SHA-256 provides that second check.

**How do you preserve reproducibility when cloud workspaces can disappear or a
transfer is interrupted?**
The pinned source identity and digest are versioned, so a fresh workspace can
reacquire exactly the same bytes. Partial files are never promoted to the final
archive; a rerun starts a fresh download. Existing archives are rehashed before
reuse. A manifest records the last successful verification, not guaranteed current
file availability or permanent storage. Durable caching would be a separate
storage decision, and every restored archive must still pass verification.
