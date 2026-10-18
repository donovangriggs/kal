# Deepening

How to safely merge a cluster of shallow modules into one deeper module, given what it depends on. Uses the terms in [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**.

## Classify the dependencies

Sort each dependency of the candidate into one of four categories. The category decides how the deepened module is tested across its seam.

### 1. In-process

Pure computation and in-memory state, no I/O. Always deepenable: merge the modules and test through the new interface directly. No adapter needed.

### 2. Local stand-in available

Dependencies with a local substitute for tests, such as PGLite for Postgres or an in-memory file system. Deepenable when the substitute exists: the test suite runs the deepened module against the substitute. The seam stays internal; the module's external interface has no port for it.

### 3. Remote but ours (ports and adapters)

Your own services over a network: internal APIs, other services you run. Define a **port** (an interface) at the seam. The deep module owns the logic and receives the transport as an **adapter**: an in-memory adapter in tests, an HTTP, gRPC or queue adapter in production.

Shape of the recommendation: *"Put a port at the seam, with an HTTP adapter for production and an in-memory adapter for tests, so the logic lives in one deep module even though it runs across a network."*

### 4. Truly external (mock)

Third-party services you don't control, such as an email provider or a book-metadata API. The deepened module takes the dependency as an injected port, and tests supply a mock adapter.

## Seam discipline

- **One adapter is a hypothetical seam; two make it real.** Don't add a port unless at least two adapters are justified (usually production plus test). A seam with one adapter is just indirection.
- **Internal versus external seams.** A deep module can have internal seams (private, used by its own tests) alongside the external seam at its interface. Don't expose an internal seam through the interface just because tests use it.

## Testing: replace, don't layer

- Once tests exist at the deepened module's interface, the old unit tests on the shallow modules are waste. Delete them.
- Put the new tests at the deepened module's interface, because that interface **is** the test surface.
- Assert on outcomes observable through the interface, never on internal state.
- Tests describe behaviour, so they survive internal refactors. A test that must change when the implementation changes is testing past the interface.
