# preCICE-AI: Approaches, Alternatives & Best Strategy

## A Comparative Analysis for Thesis Research

> **Author:** Vaibhav Dange  
> **Date:** May 2026
> **Purpose:** Systematic comparison of LLM integration and knowledge management approaches for building an AI assistant for the preCICE coupling library

---

## Table of Contents

1. [Introduction & Problem Statement](#1-introduction--problem-statement)
2. [Part A — LLM Tool Integration Approaches](#part-a--llm-tool-integration-approaches)
   - [Approach 1: MCP Server](#approach-1-mcp-server-model-context-protocol)
   - [Approach 2: LangChain / LangGraph Agent](#approach-2-langchain--langgraph-agent-with-custom-tools)
   - [Approach 3: Raw Function Calling (Anthropic / OpenAI API)](#approach-3-raw-function-calling-anthropic--openai-api)
   - [Approach 4: Semantic Kernel (Microsoft)](#approach-4-semantic-kernel-microsoft)
   - [Approach 5: Fine-Tuned Domain LLM](#approach-5-fine-tuned--domain-adapted-llm)
3. [Part B — Knowledge & Context Management Approaches](#part-b--knowledge--context-management-approaches)
   - [Approach A: Obsidian Vault + MCP Write-back](#approach-a-obsidian-vault--mcp-write-back)
   - [Approach B: Vector Database RAG Pipeline](#approach-b-vector-database-rag-pipeline)
   - [Approach C: mem0 — Agent Memory Layer](#approach-c-mem0--agent-memory-layer)
   - [Approach D: GraphRAG / Knowledge Graph](#approach-d-graphrag--knowledge-graph)
   - [Approach E: Fine-Tuned Embeddings](#approach-e-fine-tuned-embeddings)
4. [Comparison Matrices](#4-comparison-matrices)
5. [Best Approach & Recommended Architecture](#5-best-approach--recommended-architecture)
6. [Conclusion](#6-conclusion)
7. [References](#7-references)

---

## 1. Introduction & Problem Statement

preCICE is an open-source coupling library for multi-physics simulations, enabling solvers written in different languages and frameworks to exchange data at shared interfaces. Working with preCICE requires deep familiarity with its XML configuration schema, coupling algorithms (Aitken, IQN-ILS), mesh handling, participant coordination, and log interpretation — knowledge that is scattered across documentation, tutorials, and community forum posts.

The goal of **preCICE-AI** is to build an intelligent assistant that can:

- **Inspect** preCICE project configurations and detect misconfigurations
- **Execute** simulation runs and commands within tutorial projects
- **Analyze** coupling logs to detect convergence failures, errors, and warnings
- **Document** findings persistently across sessions
- **Answer** domain-specific questions about preCICE concepts and best practices

This document surveys every major technical approach for building such a system, evaluates their trade-offs in this specific domain context, and recommends the most suitable architecture for a thesis research project.

---

## Part A — LLM Tool Integration Approaches

These approaches address **how the LLM gains the ability to act** — to run commands, read files, analyze logs, and interact with the preCICE environment.

---

### Approach 1: MCP Server (Model Context Protocol)

#### Overview

MCP is an open standard developed by Anthropic that defines a protocol for LLM agents to discover and invoke external tools at runtime. A developer implements a server exposing named tools with typed schemas; the agent client (Claude Code, Codex, Cursor) automatically discovers these tools and decides when to invoke them during a conversation.

In preCICE-AI, the MCP server exposes tools such as `list_precice_projects`, `inspect_precice_config`, `run_command_in_project`, `analyze_precice_logs`, and `read_project_logs`. The agent calls these autonomously while helping a user debug a simulation.

#### How It Works

```
User: "Debug my heat-exchanger simulation"
         ↓
   Claude Code (MCP Client)
         ↓ discovers available tools via MCP protocol
   MCP Server (server.py)
     ├── list_precice_projects()        → ["heat-exchanger", "elastic-tube"]
     ├── inspect_precice_config(...)    → <precice-config.xml> content
     ├── run_command_in_project(...)    → stdout/stderr of run.sh
     └── analyze_precice_logs(...)      → "❌ Convergence failed at t=0.05"
         ↓
   Claude Code synthesizes findings → responds to user
```

#### Implementation Snapshot

```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("preCICE AI")

@mcp.tool()
def analyze_precice_logs(project_name: str) -> str:
    """Analyze preCICE log files and detect common success/failure patterns."""
    # reads .log files, checks for ERROR/WARNING/converged/failed keywords
    ...

if __name__ == "__main__":
    mcp.run()
```

#### Advantages

- **Zero boilerplate orchestration** — the agent loop is handled by the client (Claude Code); you only write tool implementations
- **Tool autodiscovery** — tools are described via docstrings and type hints; no manual schema registration
- **Native integration** with Claude Code, Codex, Cursor, and any MCP-compatible client
- **Stateless and composable** — each tool is independent; easy to add, remove, or modify
- **Low cognitive overhead** — the developer focuses entirely on domain logic, not on agent architecture
- **Standardized** — growing ecosystem; other MCP servers (GitHub, filesystem, databases) can be composed alongside your preCICE tools

#### Disadvantages

- **Client lock-in** — works natively only with MCP-compatible agents; not usable with arbitrary Python scripts or non-MCP LLM frameworks
- **No built-in persistent memory** — each session starts fresh; the agent has no recollection of previous debugging sessions
- **Limited agent control** — you cannot programmatically control the agent loop, inject intermediate reasoning steps, or define custom retry logic
- **Young ecosystem** — MCP was released in late 2024; tooling, debugging utilities, and community resources are still maturing
- **Single-process assumption** — the standard MCP model assumes one server process; running parallel simulations or managing concurrent tool calls requires additional engineering

#### Best Suited For

Rapid prototyping of AI-assisted engineering tools where the developer wants to focus on domain logic rather than agent architecture, and where Claude Code or Codex is the primary interface.

---

### Approach 2: LangChain / LangGraph Agent with Custom Tools

#### Overview

LangChain is a framework for building LLM-powered applications. LangGraph is its extension for stateful, multi-step agent workflows modelled as directed graphs. You define the same preCICE capabilities as LangChain `Tool` objects and wire them into a `ReAct` or custom agent that reasons and acts in a loop.

#### How It Works

```
User query
    ↓
LangGraph Agent (state machine)
    ├── Node: "Reason" — LLM decides next action
    ├── Node: "Act"    — dispatch to tool
    │     ├── AnalyzePreciceLogsTool
    │     ├── RunCommandTool
    │     └── InspectConfigTool
    ├── Node: "Observe" — process tool result
    └── Node: "Answer" — generate final response
    ↓
User response
```

#### Implementation Snapshot

```python
from langchain.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

@tool
def analyze_precice_logs(project_name: str) -> str:
    """Analyze preCICE log files for errors and convergence patterns."""
    # same core logic as MCP tool
    ...

llm = ChatAnthropic(model="claude-opus-4-5")
agent = create_react_agent(
    llm,
    tools=[analyze_precice_logs, run_command_in_project, inspect_precice_config],
    checkpointer=MemorySaver()   # built-in session memory
)

result = agent.invoke({
    "messages": [("user", "Why did the elastic-tube simulation diverge?")]
})
```

#### Advantages

- **Model-agnostic** — swap Claude for GPT-4o, Gemini, or a local Ollama model without rewriting tools
- **Explicit state management** — LangGraph's graph model makes multi-step reasoning transparent and auditable — important for a thesis
- **Built-in memory modules** — `MemorySaver`, `SqliteSaver`, and vector store integrations for cross-session memory
- **Rich ecosystem** — LangSmith for tracing, LangServe for deployment, hundreds of pre-built integrations
- **Custom agent loops** — full control: retry logic, human-in-the-loop checkpoints, conditional branching
- **Evaluation tooling** — LangSmith provides datasets and evaluation frameworks useful for thesis benchmarking

#### Disadvantages

- **Framework overhead** — significantly more boilerplate than MCP; the framework abstractions can be leaky and hard to debug
- **Abstraction churn** — LangChain has a history of frequent breaking API changes; research code can become fragile
- **Overkill for simple workflows** — for straightforward tool-calling, LangGraph's state machine is unnecessarily complex
- **Performance cost** — the framework adds latency through abstraction layers
- **Dependency weight** — `langchain` and `langgraph` bring large dependency trees

#### Best Suited For

Thesis work requiring explicit, auditable multi-step reasoning workflows, cross-session memory, and model-agnostic benchmarking across multiple LLMs.

---

### Approach 3: Raw Function Calling (Anthropic / OpenAI API)

#### Overview

Both the Anthropic API (Claude) and OpenAI API support structured tool/function calling natively. You define tools as JSON schemas, include them in an API request, and implement a dispatch loop that executes the chosen tool and feeds results back to the model. No framework is required.

#### How It Works

```python
import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "analyze_precice_logs",
        "description": "Analyze preCICE log files for errors and convergence",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Name of the preCICE project"}
            },
            "required": ["project_name"]
        }
    }
]

# Agentic loop
messages = [{"role": "user", "content": "Debug the heat-exchanger simulation"}]
while True:
    response = client.messages.create(
        model="claude-opus-4-5", tools=tools, messages=messages
    )
    if response.stop_reason == "end_turn":
        break
    # Dispatch tool calls, append results, continue loop
    for block in response.content:
        if block.type == "tool_use":
            result = dispatch(block.name, block.input)
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": block.id, "content": result}
            ]})
```

#### Advantages

- **Minimal dependencies** — only the Anthropic or OpenAI SDK; nothing else
- **Maximum transparency** — every step is explicit in your own code; ideal for understanding and teaching
- **Full control** — implement exactly the agent loop you need, nothing more
- **Stable interface** — the raw API changes far less frequently than framework abstractions
- **Ideal thesis baseline** — demonstrates understanding of the fundamentals without framework magic

#### Disadvantages

- **Repetitive boilerplate** — the dispatch loop, error handling, and message accumulation must be written from scratch every time
- **No built-in memory** — cross-session state requires manual implementation (database, file, etc.)
- **No tracing or observability** — must instrument everything yourself
- **Scales poorly** — as the number of tools and workflow complexity grows, the manual loop becomes unwieldy

#### Best Suited For

Establishing a clean baseline in thesis research, or for simple single-session workflows where framework overhead is not justified. Also ideal for teaching how LLM tool-calling works from first principles.

---

### Approach 4: Semantic Kernel (Microsoft)

#### Overview

Semantic Kernel is Microsoft's open-source SDK for integrating LLMs into applications, available in Python and C#. It introduces concepts of "plugins" (equivalent to tools), "planners" (automatic multi-step plan generation), and "memory" (vector-backed context retrieval). It has deep integration with Azure OpenAI and Microsoft 365.

#### Implementation Snapshot

```python
import semantic_kernel as sk
from semantic_kernel.functions import kernel_function

class PrecicePlugin:
    @kernel_function(description="Analyze preCICE logs for errors")
    async def analyze_logs(self, project_name: str) -> str:
        # same logic as MCP tool
        ...

kernel = sk.Kernel()
kernel.add_plugin(PrecicePlugin(), plugin_name="precice")
# Semantic Kernel's planner automatically chains plugins to answer queries
```

#### Advantages

- **Strong Azure ecosystem** — natural fit if the project will deploy to Azure or integrate with Microsoft tools
- **Built-in planner** — automatically generates multi-step execution plans from natural language goals
- **Memory abstraction** — built-in vector memory connectors (Azure AI Search, Chroma, Qdrant)
- **C# support** — unique among these frameworks; relevant if preCICE solvers have .NET components

#### Disadvantages

- **Microsoft-centric** — best features require Azure; less useful in academic/Linux HPC environments where preCICE typically runs
- **Python support is secondary** — C# is the primary target; Python SDK has historically lagged in features
- **Smaller research community** — less academic literature and fewer open examples compared to LangChain
- **Heavier integration requirements** — designed for enterprise integration patterns, which adds complexity to a research project

#### Best Suited For

Enterprise or industry-facing deployments, particularly those leveraging Azure infrastructure. Not well-suited for academic preCICE research in HPC/Linux environments.

---

### Approach 5: Fine-Tuned / Domain-Adapted LLM

#### Overview

Rather than giving a general-purpose LLM tools to look up preCICE knowledge at runtime, this approach bakes preCICE knowledge directly into the model's weights through fine-tuning. A smaller base model (Llama 3, Mistral, CodeLlama) is fine-tuned on a curated dataset of preCICE documentation, config XML examples, simulation logs, and Q&A pairs using parameter-efficient methods like LoRA.

#### How It Works

```
Data Collection:
  preCICE docs + tutorials + config XMLs + annotated logs + forum Q&As
          ↓
  Instruction-tuning dataset:
    {"instruction": "What does waveform-degree control in preCICE?",
     "response": "Waveform degree controls the polynomial order..."}
          ↓
  LoRA fine-tuning on CodeLlama-7B or Mistral-7B (GPU required)
          ↓
  Specialized "preCICE-LLM" with domain knowledge baked in
          ↓
  Deployed locally — answers preCICE questions without retrieval
```

#### Advantages

- **Deep domain knowledge** — the model reasons about preCICE natively, without needing retrieval at inference time
- **Local deployment** — no API costs, no data privacy concerns; runs on university HPC infrastructure
- **Highest thesis novelty** — creating a domain-specific LLM for a scientific computing library is a significant research contribution
- **Speed** — no retrieval latency; answers come directly from model weights
- **Offline capability** — works without internet access, important for HPC environments

#### Disadvantages

- **Data collection burden** — requires curating a high-quality, large-enough fine-tuning dataset; this alone is a substantial research effort
- **GPU requirement** — even with LoRA, fine-tuning a 7B parameter model requires significant GPU resources
- **Knowledge staleness** — as preCICE evolves and adds features, the model's knowledge becomes outdated and requires retraining
- **Limited to learned knowledge** — cannot execute simulations or read live logs; must be paired with tool-calling for execution
- **Evaluation complexity** — measuring whether the fine-tuned model is actually better than RAG on preCICE tasks requires careful benchmarking

#### Best Suited For

A thesis aiming to produce a novel research artifact — a preCICE-specialized language model — as a primary contribution. Best combined with RAG and tool-calling for a complete system.

---

## Part B — Knowledge & Context Management Approaches

These approaches address **how the system stores, retrieves, and maintains knowledge** across sessions — the "second brain" problem.

---

### Approach A: Obsidian Vault + MCP Write-back

#### Overview

Obsidian is a local-first Markdown knowledge management application with a powerful plugin ecosystem. The preCICE-AI MCP server is extended with tools that read and write Markdown notes into the vault. The agent autonomously documents experiments, errors, and decisions; the developer also writes in the vault manually. Together they create a shared knowledge base.

#### Advantages

- **Human-readable** — Markdown files are plain text; no database lock-in, easy to version control with Git
- **Bidirectional** — developer writes in Obsidian; agent writes back via MCP tools; both contribute to the same knowledge base
- **Rich linking** — Obsidian's `[[wikilinks]]` create a navigable knowledge graph of preCICE concepts
- **Plugin ecosystem** — Dataview for querying notes as a database, Templater for structured experiment logs, Git for version history
- **Thesis-ready** — the vault becomes living thesis documentation; experiments are logged automatically

#### Disadvantages

- **No semantic search** — Obsidian's native search is keyword-based; finding conceptually related notes requires manual linking or Dataview queries
- **Scale limits** — effective up to hundreds of notes; beyond that, navigation becomes difficult without additional tooling
- **No automatic retrieval** — the agent can search the vault by keyword but cannot semantically retrieve the most relevant past experiment when asked an oblique question

#### Best Suited For

Personal knowledge management, experiment logging, and thesis documentation. Most effective when combined with a vector database for semantic retrieval.

---

### Approach B: Vector Database RAG Pipeline

#### Overview

All preCICE knowledge — documentation pages, config XML examples, tutorial READMEs, past simulation logs, and experiment notes — is chunked and embedded into dense vectors stored in a vector database (ChromaDB, Qdrant, Weaviate). When the agent needs to answer a question, it embeds the query and retrieves the top-k semantically similar chunks to inject into the LLM context.

#### How It Works

```
Indexing (one-time):
  preCICE docs + configs + logs + experiment notes
          ↓ chunk (500 tokens, 50 overlap)
          ↓ embed (sentence-transformers/all-MiniLM-L6)
          ↓ store in ChromaDB

At query time:
  "Why does IQN-ILS diverge with large time steps?"
          ↓ embed query
          ↓ cosine similarity search → top-5 chunks
          ↓ inject chunks into LLM context
          ↓ LLM answers with grounding
```

#### Implementation Snapshot

```python
import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")
chroma = chromadb.Client()
collection = chroma.get_or_create_collection("precice-knowledge")

# Index
collection.add(
    documents=chunks,
    embeddings=embedder.encode(chunks).tolist(),
    ids=[f"chunk-{i}" for i in range(len(chunks))]
)

# Retrieve
results = collection.query(
    query_embeddings=embedder.encode(["IQN-ILS divergence"]).tolist(),
    n_results=5
)
```

#### Advantages

- **Semantic search** — finds relevant knowledge even when query wording doesn't exactly match source text
- **Scales to thousands of documents** — handles the full preCICE documentation corpus efficiently
- **Model-agnostic** — works with any LLM; the retrieval layer is independent
- **Grounded answers** — responses cite specific retrieved chunks, reducing hallucination
- **Updatable** — new logs and documents can be added to the index incrementally

#### Disadvantages

- **Retrieval quality depends on chunking** — poor chunking strategies can split semantically coherent content, degrading retrieval
- **No reasoning about relationships** — flat vector search doesn't understand that "participant" and "mesh" are related preCICE concepts
- **Passive knowledge** — RAG cannot execute simulations or run commands; it only retrieves static knowledge
- **Embedding model choice matters** — generic embedding models may not capture preCICE-specific terminology well
- **Infrastructure requirement** — requires running a vector database process alongside the agent

#### Best Suited For

Knowledge retrieval over large document corpora. Essential companion to any tool-based approach — RAG handles "what do I know?" while tools handle "what can I do?".

---

### Approach C: mem0 — Agent Memory Layer

#### Overview

mem0 is an open-source library designed specifically to give LLM agents persistent, structured memory across sessions. It automatically extracts, stores, and retrieves memories from conversation history, abstracting the complexity of embedding, storage, and retrieval.

#### Implementation Snapshot

```python
from mem0 import Memory

m = Memory()

# After a debugging session, the agent records what it learned
m.add(
    "The heat-exchanger tutorial diverges when time-window-size exceeds 0.01 with IQN-ILS",
    user_id="precice-ai",
    metadata={"project": "heat-exchanger", "category": "convergence"}
)

# In a future session, retrieve relevant memories before answering
results = m.search("time window convergence", user_id="precice-ai")
# → Returns the previously stored finding
```

#### Advantages

- **Session persistence** — memories survive across conversations; the agent remembers what was debugged before
- **Automatic extraction** — mem0 can automatically identify and store important facts from conversation history
- **Simple API** — `add`, `search`, `get_all` — far simpler than managing a vector database directly
- **User-scoped memory** — can maintain separate memory spaces for different projects or users
- **Structured + semantic** — combines metadata filtering with embedding-based retrieval

#### Disadvantages

- **Young library** — mem0 is relatively new; API stability and long-term maintenance are not guaranteed
- **Black box internals** — the automatic memory extraction may store irrelevant information or miss important facts
- **Limited control** — less control over chunking, embedding models, and retrieval strategies than a raw vector database
- **Not a document store** — designed for conversational memories, not for indexing large document corpora like preCICE documentation

#### Best Suited For

Giving the agent session-to-session memory of past debugging findings, decisions made, and patterns discovered — complementary to a RAG pipeline for document knowledge.

---

### Approach D: GraphRAG / Knowledge Graph

#### Overview

Instead of treating all knowledge as flat text chunks, GraphRAG builds a structured knowledge graph where entities (preCICE participants, meshes, coupling schemes, solvers) are nodes and their relationships (uses, requires, conflicts-with, described-in) are edges. The LLM traverses this graph to reason about multi-hop relationships.

preCICE's domain is inherently relational — a participant uses a mesh, a mesh has data, data is exchanged via a mapping, a mapping connects two participants — making it particularly well-suited to graph representation.

#### Advantages

- **Captures domain structure** — preCICE's participant-mesh-data-mapping relationships map naturally to a graph
- **Multi-hop reasoning** — "Which solvers use the mesh that has the data that's failing to converge?" is answerable via graph traversal
- **Richer context** — retrieved subgraphs carry relational context that flat chunks cannot
- **Reduces hallucination** — graph-grounded answers are more factually constrained

#### Disadvantages

- **High construction cost** — building a quality knowledge graph requires entity extraction, relation detection, and significant manual curation
- **Maintenance burden** — the graph must be updated as preCICE evolves; schema changes require graph restructuring
- **Complex infrastructure** — requires a graph database (Neo4j, Kuzu) and a GraphRAG pipeline on top
- **Overkill for simple queries** — for most questions a user asks, flat RAG performs comparably with far less complexity

#### Best Suited For

A thesis chapter demonstrating advanced knowledge representation for scientific computing domains, particularly if the research focuses on multi-hop reasoning about preCICE configuration correctness.

---

### Approach E: Fine-Tuned Embeddings

#### Overview

Rather than using a generic sentence-transformer model (trained on general web text) to embed preCICE documents, fine-tune an embedding model specifically on preCICE domain text using contrastive learning. The resulting embeddings understand that "data mapping" and "nearest-neighbor interpolation" are related in the preCICE context, improving RAG retrieval quality.

#### Advantages

- **Improved retrieval precision** — domain-specific embeddings retrieve more relevant chunks for preCICE-specific queries
- **Captures jargon** — preCICE terms like "waveform degree", "quasi-Newton coupling", and "implicit coupling scheme" are understood semantically
- **Reusable** — a fine-tuned preCICE embedding model could be released as an open-source contribution

#### Disadvantages

- **Requires training data** — needs pairs of related/unrelated preCICE text snippets for contrastive training
- **Engineering overhead** — adds another training pipeline to the project
- **Marginal gains may not justify cost** — for a thesis, demonstrating the concept may be more valuable than achieving peak retrieval performance

#### Best Suited For

A thesis with a focus on information retrieval quality for scientific computing documentation, as a component within a larger RAG pipeline.

---

## 4. Comparison Matrices

### 4.1 Tool Integration Approaches

| Criterion                | MCP Server | LangGraph    | Raw API    | Semantic Kernel | Fine-Tuned LLM |
| ------------------------ | ---------- | ------------ | ---------- | --------------- | -------------- |
| **Execution capability** | ✅ High    | ✅ High      | ✅ High    | ✅ High         | ⚠️ Limited     |
| **Setup complexity**     | 🟢 Low     | 🟡 Medium    | 🟢 Low     | 🔴 High         | 🔴 Very High   |
| **Model agnostic**       | ❌ No      | ✅ Yes       | ⚠️ Partial | ⚠️ Azure-first  | ✅ Yes         |
| **Agent loop control**   | ❌ None    | ✅ Full      | ✅ Full    | ✅ Full         | N/A            |
| **Built-in memory**      | ❌ No      | ✅ Yes       | ❌ No      | ✅ Yes          | ✅ Baked-in    |
| **Observability**        | ⚠️ Limited | ✅ LangSmith | ❌ Manual  | ✅ Yes          | ✅ Yes         |
| **Thesis novelty**       | 🟡 Medium  | 🟡 Medium    | 🔴 Low     | 🔴 Low          | 🟢 Very High   |
| **Maintenance burden**   | 🟢 Low     | 🟡 Medium    | 🟢 Low     | 🔴 High         | 🔴 Very High   |
| **HPC compatibility**    | ✅ Yes     | ✅ Yes       | ✅ Yes     | ⚠️ Limited      | ✅ Yes         |

### 4.2 Knowledge & Context Management Approaches

| Criterion                | Obsidian+MCP | Vector RAG   | mem0             | GraphRAG     | Fine-Tuned Embeddings |
| ------------------------ | ------------ | ------------ | ---------------- | ------------ | --------------------- |
| **Semantic search**      | ❌ No        | ✅ Yes       | ✅ Yes           | ✅ Yes       | ✅ Yes                |
| **Human readability**    | ✅ High      | ❌ Low       | ❌ Low           | ⚠️ Medium    | ❌ Low                |
| **Setup complexity**     | 🟢 Low       | 🟡 Medium    | 🟢 Low           | 🔴 High      | 🔴 Very High          |
| **Document scale**       | ⚠️ Hundreds  | ✅ Thousands | ❌ Memories only | ✅ Thousands | ✅ Thousands          |
| **Relational reasoning** | ❌ No        | ❌ No        | ❌ No            | ✅ Yes       | ❌ No                 |
| **Agent write-back**     | ✅ Yes       | ✅ Yes       | ✅ Yes           | ⚠️ Complex   | ❌ No                 |
| **Cross-session memory** | ✅ Yes       | ✅ Yes       | ✅ Yes           | ✅ Yes       | ✅ Yes                |
| **Thesis documentation** | ✅ Excellent | ⚠️ Indirect  | ❌ No            | ⚠️ Indirect  | ❌ No                 |
| **Ecosystem maturity**   | ✅ Mature    | ✅ Mature    | 🟡 New           | 🟡 Emerging  | ✅ Mature             |

---

## 5. Best Approach & Recommended Architecture

### Verdict

> **Recommended Stack: MCP Server + ChromaDB RAG + Obsidian Vault + mem0**

No single approach is optimal across all dimensions. The best architecture for a thesis on preCICE-AI is a **layered hybrid** where each component is chosen for what it does best, and together they form a complete, evaluable system.

### Why This Combination

**MCP Server** is the right choice for the tool/execution layer because:

- It is already implemented and working in your project — building on this foundation is efficient
- Its simplicity keeps the focus on preCICE domain logic, not agent plumbing
- Native integration with Claude Code makes the development loop fast
- The tool-centric design maps perfectly to preCICE operations (inspect config, run simulation, analyze logs)

**ChromaDB RAG** is the right choice for document knowledge because:

- preCICE has a large, well-structured documentation corpus that benefits from semantic retrieval
- It enables the agent to answer "what does this configuration parameter do?" without hardcoding answers
- Flat vector RAG is the established baseline against which more complex approaches (GraphRAG) can be compared in the thesis
- ChromaDB is lightweight, local, and requires no cloud infrastructure

**Obsidian Vault** is the right choice for human-AI collaborative knowledge management because:

- It provides a Git-trackable, human-readable record of the entire research process
- The MCP write-back tools make the agent an active contributor to the knowledge base
- It doubles as living thesis documentation
- Dataview queries and wikilinks create navigable structure over time

**mem0** is the right choice for agent session memory because:

- It gives the agent the ability to remember "last time I debugged the heat-exchanger, the time-window-size was the issue"
- It is far simpler to integrate than a custom memory system
- It complements RAG (which handles document knowledge) by handling experiential memory

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  Orchestration Layer                    │
│              Claude Code / Codex Agent                  │
│   (MCP client — discovers tools, drives reasoning loop) │
└────────────────────────┬────────────────────────────────┘
                         │ MCP Protocol
┌────────────────────────▼────────────────────────────────┐
│                   Execution Layer                       │
│                   MCP Server (server.py)                │
│  ┌──────────────────────────────────────────────────┐   │
│  │  list_precice_projects()                         │   │
│  │  inspect_precice_config(project_name)            │   │
│  │  run_command_in_project(project_name, command)   │   │
│  │  analyze_precice_logs(project_name)              │   │
│  │  write_experiment_note(title, content)           │   │
│  │  search_vault(query)                             │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │ reads / writes
         ┌───────────────┼───────────────────┐
         │               │                   │
┌────────▼──────┐ ┌──────▼──────┐  ┌─────────▼──────────┐
│  Knowledge    │ │   Agent     │  │  Human Knowledge   │
│  Retrieval    │ │   Memory    │  │  Management        │
│               │ │             │  │                    │
│  ChromaDB     │ │    mem0     │  │  Obsidian Vault    │
│  (RAG over    │ │  (session   │  │  (experiment logs, │
│  preCICE      │ │   memory,   │  │  ADRs, findings,   │
│   docs +      │ │  past       │  │  thesis notes)     │
│  past logs)   │ │  findings)  │  │                    │
└───────────────┘ └─────────────┘  └────────────────────┘
```

### Evaluation Strategy for the Thesis

The layered architecture allows ablation studies — systematically removing components to measure each one's contribution:

| Experiment  | System Configuration             | Metric                                    |
| ----------- | -------------------------------- | ----------------------------------------- |
| Baseline    | Raw API + no memory              | Task completion rate, answer accuracy     |
| + Tools     | MCP Server                       | Time to debug, error detection rate       |
| + RAG       | MCP + ChromaDB                   | Answer grounding rate, hallucination rate |
| + Memory    | MCP + ChromaDB + mem0            | Cross-session task performance            |
| Full System | MCP + ChromaDB + mem0 + Obsidian | Overall qualitative assessment            |

This gives the thesis rigorous, incremental evidence for each design decision.

### Roadmap for Implementation

**Phase 1 (Weeks 1–2):** MCP server stabilization — complete tool set, error handling, security hardening

**Phase 2 (Weeks 3–4):** RAG pipeline — index preCICE docs and tutorial configs into ChromaDB; add `search_precice_knowledge` MCP tool

**Phase 3 (Weeks 5–6):** Obsidian integration — add MCP write-back tools; set up vault structure; configure Git sync

**Phase 4 (Weeks 7–8):** mem0 integration — add session memory to the agent; test cross-session debugging scenarios

**Phase 5 (Weeks 9–12):** Evaluation — run ablation studies; collect metrics; document findings for thesis

---

## 6. Conclusion

Building preCICE-AI requires solving two distinct problems: giving an LLM the ability to act within a preCICE environment (execution), and giving it the knowledge to reason correctly about preCICE concepts and past experiences (context). No single technique solves both well.

The recommended hybrid architecture — MCP for execution, ChromaDB RAG for document knowledge, mem0 for experiential memory, and Obsidian for human-AI collaborative documentation — addresses all four requirements with components that are individually well-understood, independently evaluable, and collectively more capable than any single approach.

For a thesis, this architecture also offers a natural narrative: you can present the system as a series of incremental contributions, each motivated by a clear limitation of the previous configuration, and evaluate each addition with measurable experiments. The result is not just a working tool for preCICE users, but a rigorous study of how LLM agents can be effectively grounded in specialized scientific computing domains.

---

## 7. References

- Anthropic. (2024). _Model Context Protocol (MCP) Specification_. https://modelcontextprotocol.io
- Chase, H. (2022). _LangChain: Building applications with LLMs through composability_. GitHub. https://github.com/langchain-ai/langchain
- Bauer, G., et al. (2016). _preCICE — A fully parallel library for multi-physics surface coupling_. Computers & Fluids, 141, 250–258.
- Edge, D., et al. (2024). _From Local to Global: A Graph RAG Approach to Query-Focused Summarization_. Microsoft Research. arXiv:2404.16130
- Hu, E. J., et al. (2021). _LoRA: Low-Rank Adaptation of Large Language Models_. arXiv:2106.09685
- Lewis, P., et al. (2020). _Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks_. NeurIPS 2020.
- mem0. (2024). _mem0: The Memory Layer for AI Agents_. https://github.com/mem0ai/mem0
- Microsoft. (2023). _Semantic Kernel: Integrate Cutting-edge LLM technology quickly and easily into your apps_. https://github.com/microsoft/semantic-kernel
- Reimers, N., & Gurevych, I. (2019). _Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks_. EMNLP 2019.
- Trummer, I. (2023). _From BERT to GPT-3 Copilot: A Survey on Generative AI for Database Interaction_. VLDB 2023.

---

_Document generated as part of preCICE-AI thesis research. Last updated: May 2026._
