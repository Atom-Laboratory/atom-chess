# Contributing to Atom

Thank you for contributing to Atom.

Atom is an open-source project, and contributions from the community are welcome. Contributions can include bug fixes, new features, tests, documentation, performance improvements, refactoring, and architectural improvements.

The goal of this guide is to keep contributions consistent, reviewable, and easy to maintain.

## Before You Start

Before opening an issue or pull request:

1. Search existing issues and pull requests.
2. Check whether your change is already being discussed.
3. For significant features or architectural changes, open an issue first.
4. Keep changes focused on a single problem whenever possible.

Large changes are easier to review when they are divided into smaller, logically independent pull requests.

## Development Workflow

The recommended workflow is:

1. Fork the repository.
2. Create a dedicated branch.
3. Implement your changes.
4. Add or update tests.
5. Run the relevant test suite.
6. Review your own diff.
7. Open a pull request.

Use descriptive branch names.

Examples:

```text
feature/stockfish-uci
fix/board-state-validation
refactor/move-generation
test/chess-position
docs/development-setup
```

Avoid branches with names such as:

```text
test
changes
update
new-feature
my-branch
```

## Pull Requests

Every pull request should explain:

* What changed.
* Why the change was necessary.
* How the implementation works.
* How it was tested.
* Whether there are breaking changes.

Use the pull request template provided by the repository.

Keep pull requests focused. Avoid combining unrelated changes such as:

* Feature implementation + unrelated refactoring.
* Bug fix + formatting changes across the entire project.
* Dependency upgrades + unrelated behavioral changes.

Small and focused pull requests are easier to review, test, and merge.

### Allowing Maintainers to Edit Your Pull Request

When opening a pull request from a fork, contributors are encouraged to allow Atom maintainers to make changes directly to the pull request branch when necessary.

On the pull request page, enable:

> **Allow edits and access to secrets by maintainers**

This allows authorized Atom maintainers to push commits to the branch associated with the pull request.

Maintainers may use this capability to:

* Fix small issues identified during review.
* Apply requested changes directly.
* Improve tests.
* Resolve merge conflicts.
* Make small refactoring changes.
* Help contributors finish an otherwise acceptable contribution.

This does not mean that maintainers will rewrite a contributor's work without discussion. Significant changes should normally be discussed in the pull request before being applied.

### Security Considerations

Contributors should understand that enabling maintainer edits gives authorized maintainers the ability to modify the branch used by the pull request.

Do not place sensitive information such as:

* Passwords.
* API keys.
* Private credentials.
* Personal access tokens.
* Production secrets.

inside the pull request branch.

Maintainers should also avoid introducing or exposing secrets through code, commits, workflows, logs, or configuration files.

For pull requests from forks, GitHub applies additional security restrictions to workflows and secrets. Contributors should not assume that repository secrets are available to fork-based pull requests.

## Tests

Changes should include appropriate tests whenever practical.

Tests should cover:

* Expected behavior.
* Important edge cases.
* Error conditions.
* Regression scenarios for bug fixes.
* New behavior introduced by features.

A pull request should not intentionally introduce failing tests.

If a test cannot reasonably be added, explain why in the pull request.

## Code Quality

Contributions should follow the existing architecture and coding conventions of the project.

Prefer:

* Clear and descriptive names.
* Small and cohesive methods.
* Explicit behavior.
* Well-defined responsibilities.
* Minimal duplication.
* Meaningful tests.
* Simple abstractions.

Avoid:

* Unnecessary complexity.
* Premature optimization.
* Large unrelated refactors.
* Dead code.
* Temporary debugging code.
* Unnecessary dependencies.

Consistency with the existing codebase is generally preferred over introducing a new style.

## Dependencies

New dependencies should have a clear justification.

Before adding a dependency, consider:

* Whether the functionality can reasonably be implemented using existing dependencies.
* Maintenance status of the dependency.
* License compatibility.
* Security implications.
* Dependency size and runtime impact.
* Long-term maintenance cost.

Dependency changes should be explicitly mentioned in the pull request.

## Architecture

Architectural changes require additional consideration.

For significant changes, explain:

* The problem being solved.
* The proposed design.
* Alternatives considered.
* Trade-offs.
* Impact on existing components.
* Migration requirements, if any.

Do not introduce abstractions solely to make the code appear more generic.

Prefer abstractions that represent an actual domain or architectural boundary.

## Community Code Review

Community members are encouraged to review open pull requests.

A good review should focus on the code and its consequences rather than the contributor.

Reviewers should consider:

* Correctness.
* Tests.
* Security.
* Performance.
* Maintainability.
* Architecture.
* API compatibility.
* Error handling.
* Edge cases.

When reviewing a pull request, distinguish between blocking issues and non-blocking suggestions.

### Blocking Issues

A blocking issue is a problem that should be fixed before the pull request is merged.

Examples include:

* Incorrect behavior.
* Security vulnerabilities.
* Data corruption.
* Broken critical functionality.
* Missing required migration.
* Serious performance regressions.
* Architectural violations that would create significant maintenance problems.

### Non-Blocking Suggestions

A non-blocking suggestion is an improvement that does not prevent the pull request from being merged.

Examples include:

* Naming improvements.
* Readability.
* Minor refactoring.
* Optional performance improvements.
* Additional tests that are useful but not critical.

Do not mark stylistic preferences as blocking issues.

## Review Guidelines

Reviewers should:

* Explain why an issue matters.
* Provide actionable feedback.
* Reference the relevant file and line when possible.
* Separate facts from preferences.
* Avoid personal or dismissive language.
* Recognize good implementation decisions.
* Ask questions when additional context is needed.

Instead of:

```text
This is wrong.
```

Prefer:

```text
This can produce an invalid board state when the move is generated after a
promotion. Could we validate the resulting position here or move this check
to the position validation layer?
```

## Review Template

A standard review template is available at:

```text
.github/REVIEW_TEMPLATE.md
```

Reviewers are encouraged to use it for structured community reviews.

The template distinguishes between:

* Blocking issues.
* Non-blocking suggestions.
* Testing concerns.
* Architectural questions.
* Clarifications.
* Strengths and highlights.

## Commit Messages

Use clear commit messages that describe the intent of the change.

Prefer:

```text
feat: implement Stockfish UCI communication
fix: validate illegal chess moves
test: add move generation edge cases
refactor: simplify board state management
docs: update development setup
```

Avoid:

```text
update
fix
changes
stuff
final
test
```

Keep commits logically focused whenever practical.

## Security

Do not report security vulnerabilities through public issues.

If you discover a security vulnerability, use the repository's private security reporting mechanism when available.

Do not include credentials, API keys, tokens, passwords, or other sensitive information in commits or pull requests.

## Documentation

Documentation changes are welcome.

Update documentation when your contribution changes:

* Public APIs.
* Configuration.
* Development setup.
* Build instructions.
* User-facing behavior.
* Architectural behavior.

Documentation should remain concise and technically accurate.

## Licensing

By contributing to Atom, you agree that your contribution can be distributed under the project's applicable license.

Do not submit code copied from incompatible licenses or sources without verifying that it can legally be included in the project.

## Maintainer Review

Maintainers may request changes, additional tests, documentation, or architectural discussion before merging a contribution.

Approval from one reviewer does not necessarily guarantee that a pull request will be merged.

Maintainers may also close or redirect contributions that:

* Duplicate existing work.
* Fall outside the project's scope.
* Introduce unnecessary complexity.
* Do not meet project quality requirements.
* Cannot reasonably be maintained.

## Questions

If you are unsure about an implementation approach, open an issue or start a discussion before investing significant effort.

For smaller questions, feel free to comment on the relevant pull request.

Good contributions are not limited to code. Bug reports, documentation, testing, reviews, benchmarks, and technical discussions are all valuable contributions to Atom.
