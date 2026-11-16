# Literature and RAG protocol

1. Search exact research question, relevant algorithm/constraints and versions.
2. Start with 3-5 primary papers or official documentation sources. Verify DOI/title/year using authoritative metadata.
3. Fetch full text/PDF only when legally accessible and necessary. Respect licensing. Track URL, hash, version, pages, section and retrieval time.
4. Extract narrow evidence spans. For mathematical formulas record notation, assumptions and conditions; compare to the code.
5. Build citation graph: paper CITES parent; claim SUPPORTED_BY source; recommendation DEPENDS_ON claim. Follow references on a specific evidence gap.
6. Never convert abstract/snippet into claims about uninspected equations. Never invent access to restricted PDFs. If unavailable, mark UNVERIFIED.
7. Stop retrieval once the exact question is answered with sufficient evidence or the research budget is consumed.
8. Log query, pages searched, retained papers, rejected duplicates, uncertainty and next needed source. Negative search does not prove novelty.
