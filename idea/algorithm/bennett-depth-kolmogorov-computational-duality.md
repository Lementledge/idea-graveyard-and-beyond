# The Duality of Generalized Computation: Decomposing Composite Workloads into Causal Dependency Chains and State Transport Costs

> **One-sentence Abstract:** Real-world computational complexity emerges from the topological coupling of two fundamental cost primitives across decomposed task graphs: the cost of traversing irreducible causal dependency chains (Bennett's logical depth / compute-bound) and the cost of acquiring, moving, and materializing high-entropy data states (Kolmogorov volume / memory-I/O bound).

- **Status:** Formulated Hypothesis
- **Domain:** Algorithm / Theoretical Computer Science & Computer Architecture
- **Primary Bottleneck:** Formalizing Tight Lower Bounds on the Coupling of Spatial Transport and Causal Graph Depth
- **Created Date:** 2026-10-20

---

## 1. Context & Motivation

- **The Fallacy of Monolithic Classification:** Categorizing macroscopic computational problems as strictly "rule-generated" (e.g., SAT, Collatz) or "data-explicit" (e.g., log parsing, vector search) introduces severe analytical distortion. Any complex, real-world computational workload is not an atomic leaf node; it decomposes into a structured network of sub-tasks.
- **The True Nature of Systemic Bottlenecks:** At the architectural analysis level, system stalls and energy dissipation do not stem from a single scalar metric. They arise from two fundamentally different, competing physical bottlenecks:
  1. *The Execution of Dependent Operations:* Sequences of operations where each step strictly requires the output of its predecessor (governed by serialization latency and Amdahl's Law).
  2. *The Transport and Materialization of State:* The ingestion, routing, cache buffering, and memory-bus transfer of high-volume data payloads (governed by the Von Neumann memory wall and communication lower bounds).
- **The Core Objective:** Formulate a decomposition framework where rule-generation ($K(x) \to 0, D(x) \to \infty$) and explicit-data materialization ($K(x) \to |x|, D(x) \to O(1)$) serve as the orthogonal basis primitives, and total system complexity is analyzed via the structural coupling of both costs across the task dependency graph.

---

## 2. Core Hypothesis & Mechanics

### 1. The Two Primitive Cost Mechanisms
For any atomic sub-computation $v_i$, execution cost is governed by two orthogonal primitives:

1. **Causal Dependency Cost ($\mathcal{C}_{\text{dep}}$ — Bennett Logical Depth):**
   - **Informational Invariant:** Characterized by minimal Kolmogorov complexity $K(v_i)$ but extreme logical depth $D_s(v_i)$.
   - **Mechanical Mechanism:** A deterministic state transition $\delta: S_t \to S_{t+1}$ with high algebraic irreducibility. The system cannot evaluate state $S_t$ without sequentially evaluating $S_{t-1}$.
   - **Hardware Manifestation:** Compute/ALU-bound. Bounded by CPU/GPU clock cycles, instruction dependency pipelines, and branch prediction latency.

2. **Data Transport and Materialization Cost ($\mathcal{C}_{\text{trans}}$ — Kolmogorov State Volume):**
   - **Informational Invariant:** Characterized by high Kolmogorov complexity $K(v_i) \approx |v_i|$ (high Shannon entropy) with trivial logical depth $D_s(v_i) \to O(1)$.
   - **Mechanical Mechanism:** Processing pre-materialized, unstructured, or arbitrary data streams where operations across elements are mutually independent.
   - **Hardware Manifestation:** Memory/IO-bound. Bounded by DRAM/HBM bandwidth, PCIe/interconnect latency, cache line thrashing, and disk I/O throughput.

---

### 2. Composite Problem Decomposition: The Coupled DAG Model
A composite macroscopic computation $\mathcal{P}$ is formalized as a Directed Acyclic Graph (DAG) of tasks:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E})$$

Where:
- Each vertex $v_i \in \mathcal{V}$ represents a computational kernel incurring an internal causal dependency cost $\mathcal{C}_{\text{dep}}(v_i)$.
- Each directed edge $e_{ij} = (v_i, v_j) \in \mathcal{E}$ represents the data payload transferred from task $v_i$ to task $v_j$, incurring a state transport cost $\mathcal{C}_{\text{trans}}(e_{ij})$.
```
[Input Data Ingestion: High C_trans]
                     │
                     ▼
    ┌──────────────────────────────────┐
    │  Kernel v1 (Filter / Parse)      │ ──> Low C_dep, High C_trans
    └──────────────────────────────────┘
                     │
      e12 (Intermediate Tensor / Token) ──> Bandwidth & Cache Cost
                     ▼
    ┌──────────────────────────────────┐
    │  Kernel v2 (Recurrent / Search)  │ ──> High C_dep, Low C_trans
    └──────────────────────────────────┘
                     │
                     ▼
     [State Materialization / Storage Output]
```
### 3. Emergent Complexity from Structural Coupling
The actual wall-clock execution time $\mathcal{T}(\mathcal{P})$ and energy expenditure $\mathcal{E}(\mathcal{P})$ are neither purely compute-bound nor purely memory-bound, but emerge from how $\mathcal{C}_{\text{dep}}$ and $\mathcal{C}_{\text{trans}}$ interact along the critical path $\Pi_{\text{crit}} \subseteq \mathcal{G}$:

$$\mathcal{T}(\mathcal{P}) = \max_{\Pi \in \text{Paths}(\mathcal{G})} \left[ \sum_{v \in \Pi} \frac{\mathcal{C}_{\text{dep}}(v)}{\text{ClockRate}} + \sum_{e \in \Pi} \frac{\mathcal{C}_{\text{trans}}(e)}{\text{Bandwidth}(e)} \right] + \Delta_{\text{contention}}$$

- **Pathological Coupling 1 (Thrashing):** When a high $\mathcal{C}_{\text{trans}}$ edge feeds into a high $\mathcal{C}_{\text{dep}}$ vertex that has insufficient local register/cache memory, the system suffers severe context switching and cache invalidation penalties.
- **Pathological Coupling 2 (Starvation):** When processing units capable of resolving deep causal dependencies sit idle waiting for non-contiguous data payloads across high-latency buses (arithmetic intensity $I \ll 1$).
- **Optimal Decoupling:** Efficient system architecture isolates sub-graphs dominated by $\mathcal{C}_{\text{trans}}$ onto wide, embarrassingly parallel pipelines (vector engines, DMA channels, MapReduce fabrics) while concentrating sub-graphs dominated by $\mathcal{C}_{\text{dep}}$ onto ultra-low-latency, tightly coupled register cores with high single-thread clock frequencies.

---

## 3. Potential Impact & Applications

- **Architectural Profiling of Modern AI Workloads:**
  - *Autoregressive Generation:* Exhibits a hybrid bottleneck. Token sampling along the generation horizon forms a serialized causal chain ($\mathcal{C}_{\text{dep}}$), while loading large KV-cache matrices at each step constitutes an extreme memory-transport bottleneck ($\mathcal{C}_{\text{trans}}$).
  - *Reasoning Models & Agentic Search:* Decomposing MCTS and Chain-of-Thought verifies where compute cycles are spent (deep tree exploration) versus where memory bandwidth dominates (context retrieval).
- **Database & Query Engine Compilation:** Enables adaptive query optimizers to construct physical execution plans that deliberately alter graph topology, trading compute steps (re-evaluating deterministic predicates on the fly) to minimize cross-node data shuffling (reducing $\mathcal{C}_{\text{trans}}$ at the expense of local $\mathcal{C}_{\text{dep}}$).

---

## 4. The Bottlenecks (Why It's Beyond Current Reach)

- **Unifying Communication Complexity with Irreducible Circuit Depth:** Classical lower-bound techniques either analyze circuit depth (e.g., $NC \neq P$, Ladner's theorem) while assuming free wire communication, or analyze communication complexity while treating internal node processing as instantaneous $O(1)$ black boxes. A unified algebraic framework bridging both remains non-existent.
- **Dynamic Input-Dependent Graph Reconfiguration:** In NP-hard solvers (e.g., CDCL SAT) and adaptive simulations, the topology of $\mathcal{G}$ and the weights of $\mathcal{C}_{\text{dep}}$ mutate dynamically during runtime based on intermediate state discoveries.

---

## 5. Potential Attack Vectors & Next Steps

- **Graph-Based Extension of the Roofline Model:**
  - Expand the classical 2D Roofline Model (Arithmetic Intensity vs. Attainable Performance) into a topological formulation that accounts for graph path depth (longest directed path of dependent operations) alongside memory traffic.
- **Information-Theoretic Metric Development:**
  - Formulate an empirical proxy $\kappa(\mathcal{G}) = \frac{\sum \text{Depth}(v)}{\sum \text{Volume}(e)}$ to classify workload segments and automatically dispatch sub-graphs to heterogenous accelerators (e.g., Neuromorphic/ASIC for $\mathcal{C}_{\text{dep}}$ vs. HBM/Processing-in-Memory for $\mathcal{C}_{\text{trans}}$).
- **Open Questions:**
  1. What is the fundamental trade-off curve between re-computing an irreducible function locally versus transferring its materialized output over a physical communication channel bounded by light speed and wire resistance?
  2. Does every P-Complete problem possess an intrinsic graph topology where $\mathcal{C}_{\text{dep}}$ cannot be decoupled from $\mathcal{C}_{\text{trans}}$ by any polynomial transformation?

---

## 6. References & Prior Art

- **Bennett, C. H. (1988):** *Logical Depth and Physical Complexity*. The Universal Turing Machine: A Half-Century Survey, Oxford University Press, 227–257.
- **Kolmogorov, A. N. (1965):** *Three approaches to the quantitative definition of information*. Problems of Information Transmission, 1(1), 1–7.
- **Williams, S., Waterman, A., & Patterson, D. (2009):** *Roofline: an insightful visual performance model for multicore architectures*. Communications of the ACM, 52(4), 65–76.
- **Amdahl, G. M. (1967):** *Validity of the single processor approach to achieving large scale computing capabilities*. AFIPS Conference Proceedings, 30, 483–485.
- **Brent, R. P. (1974):** *The parallel evaluation of general arithmetic expressions*. Journal of the ACM, 21(2), 201–206.
