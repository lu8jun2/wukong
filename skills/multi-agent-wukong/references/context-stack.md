# Context Stack

The public C-lite context stack models three stores:

- state: current task state
- memory: durable lessons with evidence
- facts: shared facts with confidence and temporal validity

Persistence is guarded. Only approved, evidence-backed writes are allowed.

