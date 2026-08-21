# Class 2 — Embeddings & Cosine Similarity with Ollama embedding all-minilm

**Stack:** `langchain-ollama` · Ollama (`all-minilm`) · `scikit-learn`
**Environment:** macOS · Python 3.11.9 · venv `myvenv-lc`

---

## Objective

Turn text into vectors, then measure how close a query is to each document using cosine similarity — the retrieval step that sits underneath every RAG pipeline, isolated here so the maths is visible.

---

## Prerequisites

Ollama must be running locally and the embedding model pulled before any of this works:

```bash
ollama serve                # if not already running as a service
ollama pull all-minilm      # ~46 MB, 384-dimension embeddings
ollama list                 # confirm all-minilm is present
```

`OllamaEmbeddings` talks to `http://localhost:11434`. If the model isn't pulled, the call fails at `embed_documents()`, not at import — so a clean import proves nothing.

---

## Setup

```bash
python3 -m venv myvenv-lc
source myvenv-lc/bin/activate
pip install langchain-ollama scikit-learn
```

Teardown when finished:

```bash
deactivate
```

---

## Walkthrough

### 1 — Imports

```python
from langchain_ollama import OllamaEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
```

### 2 — Corpus

Three documents, deliberately chosen so two are related (pets) and one is unrelated (astronomy):

```python
docs = [
    "Dogs are loyal and friendly domestic animals.",
    "Cats are independent and curious creatures.",
    "The Milky Way galaxy contains over 200 billion stars.",
]
```

### 3 — Embed the documents

```python
embedder = OllamaEmbeddings(model="all-minilm")
document_embeddings = embedder.embed_documents(docs)
```

`embed_documents()` takes a **list** and returns a list of vectors — one per document, 384 floats each.

### 4 — Embed the query

```python
query = "Which pet is known for loyalty?"
query_embedding = embedder.embed_query(query)
```

`embed_query()` takes a **single string** and returns **one** vector. Two methods rather than one because some embedding models apply different prefixes or pooling to queries versus passages. For `all-minilm` the two paths are equivalent, but using the right method keeps the code portable when the model is swapped.

### 5 — Score

```python
scores = cosine_similarity([query_embedding], document_embeddings)
```

```
array([[ 0.66347949,  0.45812654, -0.01676095]])
```

Note the brackets around `query_embedding`. `cosine_similarity` expects 2-D arrays of shape `(n_samples, n_features)`; a bare 1-D vector raises a reshape error. Passing `[query_embedding]` makes it a 1×384 matrix, and the result comes back as 1×3 — one row of scores, one column per document.

### 6 — Verify one at a time

Scoring each document individually returns exactly the same values, confirming the batched call does nothing clever:

```python
cosine_similarity([query_embedding], [document_embeddings[0]])   # [[ 0.66347949]]
cosine_similarity([query_embedding], [document_embeddings[1]])   # [[ 0.45812654]]
cosine_similarity([query_embedding], [document_embeddings[2]])   # [[-0.01676095]]
```

---

## Results

Query: *"Which pet is known for loyalty?"*

| # | Document | Score | Reading |
|---|---|---|---|
| 0 | Dogs are loyal and friendly domestic animals. | **0.6635** | Strong match — shares both *loyal* and the pet concept |
| 1 | Cats are independent and curious creatures. | **0.4581** | Moderate — same domain (pets), opposite trait |
| 2 | The Milky Way galaxy contains over 200 billion stars. | **-0.0168** | No relationship — effectively orthogonal |

The ranking is correct, and the *spacing* between scores is the interesting part.

---

## What the numbers mean

Cosine similarity measures the angle between two vectors, ignoring magnitude. Range is −1 to 1: **1** means identical direction, **0** means unrelated, **−1** means opposite.

Three things worth internalising from this run:

**Doc 0 scores 0.66, not 0.95.** Semantic similarity is not keyword overlap, but it isn't perfect recall either. A "good" match in embedding space is often in the 0.5–0.8 band. There is no universal threshold — a cutoff has to be calibrated per model and per corpus.

**Doc 1 scores 0.46 despite being the wrong answer.** The query says nothing about cats, yet the score is respectable because embeddings capture *topic*, not *truth*. Both sentences are about domestic pets and their temperaments. This is exactly why production RAG adds a reranker or an LLM filter after vector retrieval — a naive top-2 here would hand the cat sentence to the model as supporting context.

**Doc 2 scores ≈ 0, and slightly negative.** The small negative value isn't meaningful — it's noise around zero. Treat anything near 0 as "unrelated" rather than "opposite"; genuinely opposing meanings rarely produce strongly negative cosine scores in practice.

---

## Gotchas

- **Model not pulled** — `ollama pull all-minilm` first, or the embed call fails
- **1-D vs 2-D** — always wrap a single vector in a list for `cosine_similarity`
- **`embed_query` vs `embed_documents`** — singular vs plural, string vs list; mixing them up gives confusing shape errors
- **Model consistency** — query and documents must be embedded with the *same* model; vectors from different models are not comparable
- **Dimension check** — `len(document_embeddings[0])` should be 384 for `all-minilm`

---

## Script version

The same session as a runnable file:

```python
"""Session 2 — embeddings and cosine similarity with Ollama."""
sanjeev.rohilla@APAC-SANJEEV~/AI/session2  main % python3 -m venv myvenv-lc 
sanjeev.rohilla@APAC-SANJEEV~/AI/session2  main % source myvenv-lc/bin/activate
(myvenv-lc) sanjeev.rohilla@APAC-SANJEEV~/AI/session2  main % pip install langchain-ollama scikit-learn

(myvenv-lc) sanjeev.rohilla@APAC-SANJEEV~/AI/session2  main % python                                       
Python 3.11.9 (main, Mar 28 2025, 18:17:42) [Clang 16.0.0 (clang-1600.0.26.6)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from langchain_ollama import OllamaEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
>>> from sklearn.metrics.pairwise import cosine_similarity

>>> 
>>> docs = [
...     "Dogs are loyal and friendly domestic animals.",
...     "Cats are independent and curious creatures.",
...     "The Milky Way galaxy contains over 200 billion stars.",
... ]
>>> embedder = OllamaEmbeddings(model="all-minilm")
>>> document_embeddings = embedder.embed_documents(docs)
>>> query = "Which pet is known for loyalty?"
>>> query_embedding = embedder.embed_query(query)
>>> scores = cosine_similarity([query_embedding], document_embeddings)
>>> scores
array([[ 0.66347949,  0.45812654, -0.01676095]])
>>> score_0 = cosine_similarity([query_embedding],[document_embeddings[0]])
>>> score_0
array([[0.66347949]])
>>> score_1 = cosine_similarity([query_embedding],[document_embeddings[1]])
>>> score_1
array([[0.45812654]])
>>> 
>>> 
>>> score_2 = cosine_similarity([query_embedding],[document_embeddings[2]])
>>> score_2
array([[-0.01676095]])
>>> exit()
(myvenv-lc) sanjeev.rohilla@APAC-SANJEEV~/AI/session2  main % deactivate 
```

---

## Next steps

1. **Change the query** to *"Which pet is independent?"* and confirm docs 0 and 1 swap places — proof the model reads the trait, not just the topic
2. **Try an off-topic query** like *"How far away is Andromeda?"* and watch doc 2 jump to the top
3. **Swap the model** to `mxbai-embed-large` (1024-dim) and compare scores on the identical corpus — larger models usually widen the gap between relevant and irrelevant
4. **Scale the corpus** to 50+ sentences and time the loop; this is where a brute-force scan starts to hurt and a vector store earns its place
5. **Add a threshold** — return only documents scoring above ~0.5 and observe how often the cat sentence still slips through
6. **Move to a vector store** — replace the manual `cosine_similarity` call with ChromaDB or FAISS and confirm the top-k ordering matches what was computed by hand here

---

## Takeaway

A vector store is an index and a convenience, not a different algorithm. What Chroma or FAISS does at query time is precisely the operation run manually above — embed the query, compare against stored vectors, sort. Having seen the raw numbers once, the behaviour of the retrieval layer in a full RAG pipeline stops being opaque.

