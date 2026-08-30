# Pull Request Review

## Review Summary

<!--
Briefly summarize the overall quality and impact of the changes.
Focus on correctness, maintainability, architecture, testing, and potential risks.
-->

**Review Status:** 🟢 Approved / 🟡 Approved with Suggestions / 🔴 Changes Requested

**Overall Assessment:**

<!-- 1–3 sentences explaining the main conclusion of the review. -->

---

## 🚨 Blocking Issues

<!--
Only include issues that should prevent this PR from being merged.

Examples:
- Bugs or incorrect behavior
- Security vulnerabilities
- Data loss or corruption risks
- Breaking changes without proper migration
- Failing or missing critical tests
- Architectural violations
- Race conditions or concurrency problems
- Significant performance regressions
-->

* [ ] **`path/to/file.ext:line` — Issue title**

  * **Problem:** Describe the issue.
  * **Impact:** Explain why this prevents the PR from being merged.
  * **Suggested fix:** Provide a concrete recommendation when possible.

---

## ⚠️ Non-Blocking Suggestions

<!--
Improvements that are worth considering but should not prevent merging.

Examples:
- Readability
- Maintainability
- Refactoring
- Naming
- Performance improvements
- Better abstractions
- Test improvements
-->

* **`path/to/file.ext:line` — Suggestion title**

  * **Observation:** What could be improved?
  * **Recommendation:** What would you suggest?
  * **Rationale:** Why would this improve the implementation?

---

## Testing & Verification

<!--
Describe whether the changes were sufficiently tested.
Mention specific tests, manual verification, edge cases, or missing coverage.
-->

**Tests reviewed:**

* [ ] Existing tests
* [ ] New tests
* [ ] Integration tests
* [ ] Edge cases
* [ ] Error handling
* [ ] Manual verification

**Testing concerns:**

<!-- Describe missing or insufficient coverage. -->

---

## Architecture & Design

<!--
Use this section when the PR introduces or modifies architecture,
domain logic, APIs, modules, dependencies, or significant abstractions.

Remove this section if not applicable.
-->

* **Design decision:** Describe the relevant decision.
* **Recommendation:** Optional recommendation.
* **Rationale:** Explain the architectural impact.

---

## Questions & Clarifications

<!--
Questions are not necessarily problems.
Use this section when additional context would help understand
an implementation decision.
-->

* **`path/to/file.ext:line` — Question**

  * Explain what you would like clarified.

---

## Strengths & Highlights

<!--
Recognize good engineering decisions, clean implementations,
useful tests, documentation, or improvements introduced by the PR.
-->

* **Implementation:** Highlight a particularly good decision.
* **Testing:** Highlight useful or comprehensive tests.
* **Architecture:** Highlight a sound design decision.
* **Documentation:** Highlight helpful documentation.

---

## Final Recommendation

### 🟢 Approved

The changes look correct and are ready to be merged.

### 🟡 Approved with Suggestions

The implementation is acceptable and can be merged, but the suggestions above may improve maintainability, readability, or robustness.

### 🔴 Changes Requested

The PR contains blocking issues that should be addressed before it can be merged.
