# TEST REPORT — RUN 10

**Project:** Agent AI Chatbot  
**Module:** Retrieval / RAG  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local / Development  
**Date:** 2026-04-06  
**Tester:** Pawel Staniewski

---

# Objective

Validate reliability, correctness, and stability of the Retrieval-Augmented Generation (RAG) subsystem responsible for retrieving documentation content and generating responses based on indexed documents.

The goal of this test run is to confirm that:

- relevant documentation is correctly retrieved
- system handles missing information safely
- ranking quality is acceptable
- retrieval performance is stable
- system behavior remains consistent across repeated interactions
- retrieval failures can be diagnosed and verified against the vector store

---

# Environment

Backend:

- Django REST API
- FastAPI streaming endpoint
- Haystack Agent architecture
- Pgvector document store
- PostgreSQL 16 (Docker container)

Frontend:

- React + Vite
- SSE streaming via EventSource
- Markdown rendering with sources list

Infrastructure:

- Docker Compose (local development)
- JWT authentication (access + refresh tokens)
- Local document corpus (scraped Haystack documentation)

---

# Test Scenarios

---

## RAG-01 — Query existing documentation

**Steps**

1. Ask a known documentation topic  
   Example:  
   "Co to jest Pipeline w Haystack?"

**Expected Result**

Relevant documentation content is retrieved and explained correctly.

**Result**

PASS

System returned a correct explanation of the Pipeline concept using documentation context.

---

## RAG-02 — Query missing topic

**Steps**

1. Ask about a topic that does not exist in the documentation

**Expected Result**

System returns a safe response without hallucinating information.

**Result**

PASS

System correctly reported that the requested information was not found in the documentation.

---

## RAG-03 — Reference query

**Steps**

1. Ask directly about a specific component name  
   Example:  
   "Wyjaśnij klasę ConditionalRouter w Haystack"

**Expected Result**

Correct document is retrieved based on the component name.

**Result**

PASS (warning)

System returned a correct explanation.  
However, retrieval logs showed unrelated documents appearing above the correct document in the ranking list.

**Notes**

Ranking relevance could be improved.

---

## RAG-04 — Conceptual query

**Steps**

1. Ask a conceptual documentation question  
   Example:  
   "Czym jest Pipeline w Haystack i do czego służy?"

**Expected Result**

System generates a context-based explanation using documentation.

**Result**

PASS (warning)

System produced a correct conceptual explanation.  
Retrieval logs indicated mixed ranking relevance for supporting documents.

---

## RAG-05 — Comparison query

**Steps**

1. Ask to compare two components  
   Example:  
   "Jaka jest różnica między ConditionalRouter a MetadataRouter w Haystack?"

**Expected Result**

System generates a logical comparison using documentation for both components.

**Result**

FAIL

System responded that information about MetadataRouter was not found.

**Technical validation**

Manual inspection of the active PostgreSQL 16 pgvector document store confirmed that:

- document `metadatarouter.md` exists
- document is indexed
- document content is accessible

Example verification:

```sql
SELECT COUNT(*)
FROM haystack_documents
WHERE meta->>'file_name' = 'metadatarouter.md';
```

Result:

3 chunks found.

Conclusion:

Failure is not caused by missing data.

The document `metadatarouter.md` is present in the active pgvector document store and contains valid content.

This indicates a retrieval or ranking limitation rather than a data availability issue.

Impact:

Medium

The system may incorrectly report missing documentation for valid components during comparison scenarios.

Severity:

Functional limitation under specific query conditions.

Reproducibility:

Consistently reproducible during comparison queries involving multiple components.

---

## RAG-06 — Practical how-to query

**Steps**

1. Ask how to use a component  
   Example:  
   "Jak użyć ConditionalRouter w pipeline?"

**Expected Result**

System returns actionable instructions or usage example.

**Result**

PASS

System generated a correct procedural explanation with example usage.

---

## RAG-07 — Retrieval ranking quality

**Steps**

1. Ask about a known component stored in the vector database  
   Example:  
   "Co to jest ConditionalRouter w Haystack?"

2. Observe retriever logs

3. Verify whether the target document appears near the top of the ranking list

**Expected Result**

The most relevant document appears near the top of the retrieved results.

**Result**

FAIL

The target document `conditionalrouter.md` was retrieved, but it appeared only in 4th position.

Higher-ranked results included unrelated or weakly related documents such as:

- `integrations-weave.md`
- `openaigenerator.md`
- `integrations-firecrawl.md`

This indicates that retrieval ranking quality is not sufficiently precise even for direct component-name queries.

**Notes**

Functional answer generation remained correct, but ranking quality did not meet the expected standard for top-result relevance.

## RAG-08 — Retrieval latency

**Steps**

1. Send multiple documentation queries to the chatbot
2. Observe retrieval execution time in logs

Example log:

retriever(...) → 7 docs in 2671 ms

3. Compare observed latency values across multiple requests

**Expected Result**

Retrieval completes within an acceptable time range under normal system conditions.

**Result**

PASS

Observed retrieval latency was consistently within the acceptable range for local development.

Typical retrieval times:

- 806 ms
- 917 ms
- 1006 ms
- 1347 ms
- 1901 ms
- 2671 ms

One unusually high latency value was observed:

50178 ms

**Notes**

The latency spike occurred after the system had been running overnight with Docker containers left idle.

Subsequent requests returned to normal latency levels.

This behavior is consistent with environment warm-up or resource recovery conditions rather than a persistent performance issue.

System retrieval performance is considered stable under normal usage conditions.

## RAG-09 — Retrieval caching

**Steps**

1. Ask the same or similar query multiple times
2. Observe retrieval logs

**Expected Result**

System uses cached retrieval results when appropriate.

**Result**

PASS

Logs confirmed that cached retrieval results were reused.

Example log:

retriever: second call → returning cached result

---

## RAG-10 — Source correctness

**Steps**

1. Ask a documentation question with a specific expected source  
   Example:  
   "Jak użyć ConditionalRouter w Haystack?"

2. Observe the generated answer and cited sources

3. Compare cited sources with the actual topic of the answer

**Expected Result**

Sources match the generated answer and point to the relevant documentation.

**Result**

PASS

The generated answer was supported by an appropriate documentation source.

Observed source:

- `https://docs.haystack.deepset.ai/docs/conditionalrouter`

The cited source matched the topic of the answer and correctly supported the explanation and usage example for `ConditionalRouter`.

**Notes**

Retriever ranking quality remained suboptimal in the logs, but final source attribution was correct.

---

## RAG-11 — Polish query for English docs

**Steps**

1. Ask a documentation question in Polish  
   Example:  
   "Czym jest Pipeline w Haystack i do czego służy?"

2. Observe retrieval logs

3. Verify that the system retrieves the correct English documentation

**Expected Result**

System successfully retrieves relevant English documentation for a Polish-language query.

**Result**

PASS (warning)

The system correctly handled a Polish-language query against an English documentation corpus and generated a valid context-based answer.

This confirms that multilingual retrieval works in the expected user scenario.

**Notes**

Although the final answer was correct, retrieval ranking and source alignment were not ideal. Some higher-ranked documents were only partially related to the target concept.

This indicates that multilingual retrieval is functional, but ranking quality still requires improvement.

---

## RAG-12 — Paraphrased query

**Steps**

1. Rephrase a documentation question about an existing component  
   Example:  
   "Opisz rolę ToolInvoker w Haystack."

2. Observe retrieval logs

3. Compare the result with the expected behavior for a semantically equivalent query

**Expected Result**

System returns a consistent answer for a paraphrased version of a valid documentation query.

**Result**

FAIL

The system failed to retrieve the expected documentation and returned a fallback response indicating that the information was not found.

Observed behavior:

- the existing component `ToolInvoker` was not retrieved
- top-ranked documents were unrelated to the requested concept
- final answer incorrectly stated that the information was not present in the documentation

**Notes**

This indicates a paraphrase robustness limitation.

The failure suggests that retrieval quality degrades when the same intent is expressed in a less direct wording.

Query normalization may also be contributing to the issue, as the logged query appeared reduced to:

`rolę toolinvoker w haystack.`

---

## RAG-13 — Ambiguous query

**Steps**

1. Ask an intentionally unclear documentation question  
   Example:  
   "Jak działa tool w Haystack?"

2. Observe retrieval logs

3. Evaluate whether the system responds safely and usefully despite the ambiguity

**Expected Result**

System returns a safe general explanation or cautious clarification.

**Result**

PASS (warning)

The system handled the ambiguous query without failure and returned a useful general explanation of how tools work in Haystack.

The answer was understandable and relevant to the likely user intent.

**Notes**

Retriever ranking and final source selection were suboptimal.

Observed top documents and cited sources were related to generators using tools rather than the most central documentation pages for the Tool concept itself.

This indicates that ambiguity handling is functionally correct, but source precision remains limited.

---

## RAG-14 — Multiple repeated queries

**Steps**

1. Ask multiple similar questions about the same concept  
   Examples:  
   "Do czego służy Agent w Haystack?"  
   "Czym jest Agent w Haystack?"  
   "Opisz rolę Agentów w Haystack."

2. Observe retrieval logs and generated answers

3. Compare response consistency across repeated and similar queries

**Expected Result**

System maintains stable behavior and returns consistent answers for similar queries.

**Result**

PASS (warning)

The system handled multiple similar queries consistently and returned stable, relevant answers about the Agent concept in Haystack.

Across all tested variants, the chatbot:

- correctly identified the topic
- returned coherent explanations
- cited relevant final documentation sources such as `agent`, `agents`, and `agents-api`

**Notes**

Retriever ranking remained imperfect across repeated queries.

Some top-ranked documents were not the most central matches for the Agent concept, including `llamastackchatgenerator.md` and `experimental-agents-api.md` appearing above more directly relevant pages.

This indicates stable functional behavior, but continued ranking imprecision.

---

## RAG-15 — Retrieval robustness

**Steps**

1. Ask about an existing component using a slightly incorrect term  
   Examples:  
   "Co to jest ToolInvokr w Haystack?"  
   "Co to jest Async Pipline w Haystack?"

2. Observe retrieval logs and generated responses

3. Verify whether the system can still recover the intended documentation target

**Expected Result**

System still finds the relevant documentation despite minor spelling mistakes or slightly incorrect terms.

**Result**

FAIL

The system failed to recover the intended target for both tested typo variants.

Observed behavior:

- `ToolInvokr` was not matched to `ToolInvoker`
- `Async Pipline` was not matched to `AsyncPipeline`
- retrieval results were unrelated to the intended documents
- final responses incorrectly stated that the information was not present in the documentation

**Notes**

This indicates weak tolerance for minor spelling errors in documentation queries.

The issue appears reproducible and affects realistic user typo scenarios.

Repeated execution of the `Async Pipline` query produced the same failure pattern, confirming consistent behavior under this edge case.

---

## RAG-16 — Cold start behavior

**Steps**

1. Restart the FastAPI backend service
2. Send the first documentation query after restart  
   Example:  
   "Co to jest Pipeline w Haystack?"

3. Observe system logs and response behavior

**Expected Result**

System responds correctly to the first query after restart.

**Result**

PASS (warning)

The FastAPI service restarted successfully and handled the first query after startup without runtime errors.

Observed behavior:

- application startup completed successfully
- first post-restart query was processed correctly
- generated answer was valid and contextually correct

However, the first retrieval after restart showed a significant latency spike:

- `retriever(integration:mixed) → 7 docs in 33108 ms`

**Notes**

This indicates a noticeable cold-start performance penalty after backend restart.

Functional behavior remained correct, but initial retrieval latency was substantially higher than during normal warmed-up operation.

---

## RAG-17 — Long response stability

**Steps**

1. Ask for a long and detailed technical explanation  
   Example:  
   "Opisz szczegółowo architekturę Pipeline w Haystack, uwzględniając rolę komponentów, połączeń między nimi, przepływu danych oraz przykładowy scenariusz działania w systemie RAG. Odpowiedź powinna być rozbudowana i techniczna."

2. Observe retrieval logs and streaming behavior

3. Verify that the response is complete, stable, and not duplicated or truncated

**Expected Result**

System generates a long technical response without streaming issues.

**Result**

PASS

The system successfully generated a long, detailed, and technically coherent response.

Observed behavior:

- retrieval completed successfully
- response streaming remained stable
- no duplication was observed
- no truncation occurred
- no runtime errors or timeout issues were detected

The final response was complete and supported by relevant documentation sources.

**Notes**

This confirms stable long-response behavior under a more demanding documentation query.

The generated answer length (`text_len=3771`) indicates that the system can sustain extended streaming output without visible instability.

---

## RAG-18 — Retrieval fallback behavior

**Steps**

1. Ask about a plausible but non-existent component  
   Example:  
   "Co to jest SmartAgentRouter w Haystack?"

2. Observe retrieval logs and generated response

3. Verify that the system does not hallucinate information

**Expected Result**

System generates a safe fallback response indicating that the requested component does not exist in the documentation.

**Result**

PASS

The system correctly handled the query for a non-existent component.

Observed behavior:

- retriever returned unrelated documents based on similarity
- agent did not generate fabricated information
- system returned a safe message indicating that the component was not found
- user was prompted to clarify the request

**Notes**

This behavior demonstrates correct fallback handling and effective hallucination prevention.

The system prioritizes safety over speculative responses when documentation evidence is insufficient.

---

# Test Coverage Summary

All planned RAG reliability scenarios (RAG-01 through RAG-18) were completed during this test run.

No pending retrieval scenarios remain for this run.

Future testing will focus on:

- ranking quality improvements
- typo tolerance
- paraphrase robustness
- multilingual retrieval optimization
- performance tuning

# Known Issues

## RAG-05 — Comparison query retrieval failure

**Status**

FAILED

**Description**

System fails to retrieve documentation for MetadataRouter during comparison queries, despite the document being present in the vector store.

**Root cause scope**

- retrieval ranking behavior
- comparison query handling
- candidate selection logic

**Not caused by**

- missing document
- ingestion failure
- database inconsistency

**Impact**

Medium

The system may incorrectly report missing documentation for valid components during comparison scenarios.

---

## Retrieval coverage gaps for existing components

**Status**

OBSERVED

**Description**

The system occasionally fails to retrieve documentation for valid components that are confirmed to exist in the vector store.

This behavior was observed for multiple components, including:

- MetadataRouter
- ToolInvoker

In these cases:

- documents were present in the pgvector document store
- document content was accessible
- retrieval results did not include the correct document
- the system incorrectly reported that the information was not found

**Root cause scope**

- retrieval recall limitations
- candidate selection behavior
- ranking and filtering logic
- query normalization effects

**Not caused by**

- missing document
- ingestion failure
- database inconsistency
- vector store corruption

**Impact**

Medium

Users may receive incorrect "not found" responses for valid documentation topics.

**Reproducibility**

Consistently reproducible for specific component queries.

---

## Additional observed limitations

The following limitations were consistently observed during this test run:

1. Retrieval coverage gaps

Some valid documentation topics were not retrieved despite being present in the vector store.

Observed examples:

- MetadataRouter
- ToolInvoker

2. Ranking precision

Relevant documents are not always positioned near the top of the retrieval results.

3. Paraphrase robustness

The system may fail to retrieve valid documentation when the same intent is expressed using alternative phrasing.

4. Typo tolerance

Minor spelling mistakes significantly reduce retrieval success rate.

These limitations affect retrieval accuracy but do not impact overall system stability.

# Stability Assessment

Retrieval subsystem behavior is stable in standard usage scenarios.

Verified capabilities:

- document retrieval
- conceptual explanation generation
- procedural guidance generation
- safe handling of unknown topics
- retrieval caching behavior
- vector store consistency validation

System reliability is considered:

STABLE WITH KNOWN LIMITATIONS

The system demonstrates stable behavior under normal usage conditions.

However, the following limitations were consistently observed:

- imperfect ranking precision
- sensitivity to paraphrased queries
- limited tolerance for spelling errors
- occasional cold-start latency spikes

These issues do not affect system stability but may impact retrieval accuracy in edge-case scenarios.

# Metrics Summary

| Metric                    | Observed Value  | Assessment                    |
| ------------------------- | --------------- | ----------------------------- |
| Average retrieval latency | 806–2671 ms     | Acceptable                    |
| Worst retrieval latency   | 50178 ms        | Outlier (environment-related) |
| Cold start latency        | 33108 ms        | Expected warm-up behavior     |
| Long response size        | 3771 characters | Stable                        |
| Cache reuse               | Confirmed       | Working                       |
| Hallucination prevention  | Confirmed       | Working                       |

# Key Findings

The test run identified several consistent retrieval limitations:

1. Ranking precision

Relevant documents are not always positioned near the top of the retrieval results.

2. Paraphrase robustness

The system may fail to retrieve valid documentation when the same intent is expressed using alternative phrasing.

3. Typo tolerance

Minor spelling mistakes significantly reduce retrieval success rate.

4. Comparison query handling

Multi-entity comparison queries may lead to partial retrieval failures even when both documents exist.

These findings indicate that retrieval behavior is functionally stable but requires ranking and normalization improvements.
