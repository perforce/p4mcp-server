# Contributing to P4MCP Server

Thank you for your interest in contributing to **P4MCP Server**!
This project integrates P4 with the Model Context Protocol (MCP), enabling structured and safe interactions with P4 through IDEs and AI agents.

We welcome contributions from the community.

---

## 📝 Contributor License Agreement

**Before your first contribution can be accepted, you must sign the Perforce Contributor License Agreement ("CLA").**

The CLA grants Perforce a perpetual, worldwide, royalty-free copyright and patent license to use, reproduce, modify, and distribute your contributions as part of this project. It also includes your representations that you are entitled to make the contribution, that your submission is your original work, and that you have disclosed any known third-party licenses or restrictions associated with your contribution.

To sign the CLA:

1. Download the CLA here: [CLA.docx](https://github.com/perforce/p4mcp-server/blob/main/CLA.docx);
2. Complete the signature block, including your name, title, date, and GitHub username; and
3. Return the signed CLA to [contracts@perforce.com](mailto:contracts@perforce.com) prior to submitting your first pull request.

Electronic signatures are accepted. Your pull request will not be reviewed until a signed CLA is on file with Perforce.

If you are contributing in the course of your employment, or your employer has intellectual property rights in your submission by contract or applicable law, you must obtain written permission from your employer before signing the CLA. In that case, the CLA will be treated as signed on behalf of both you and your employer. Please refer to Section 3 of the CLA for full details.

Signing the CLA does not affect your rights to use your own contributions for any other purpose.

---

## 🚀 Getting Started

### 1. Fork the Repository

Fork the repository to your GitHub account and clone it locally:

```
git clone https://github.com/<your-username>/p4mcp-server.git
cd p4mcp-server
```

Create a new branch for your work:

```
git checkout -b feature/<short-description>
```

Use descriptive branch names, such as:

* `feature/workspace-validation`
* `fix/workspace-switch-bug`
* `docs/update-readme`

---

## 📋 Coding Guidelines

* Follow PEP 8 style guidelines.
* Keep changes focused and minimal.
* Create small, reviewable pull requests where possible.
* Maintain backward compatibility where possible.
* Add inline comments where behavior may not be obvious.
* Update documentation when adding or modifying features.

---

## 🧪 Testing Guidelines

Before submitting a pull request (PR):

* Verify that basic MCP connectivity works.
* Test against a real P4 workspace.
* Validate both read-only and write operations.
* Ensure workspace and depot operations do not bypass safety checks.
* Confirm that error handling produces clear, actionable messages.

If your change affects any of the following, be especially careful with destructive operations:

* Workspace handling
* Workspace switching
* Spec editing
* Validation logic

---

## 🧠 Commit Message Guidelines

Use clear, imperative commit messages.

Good examples:

* `Added workspace deletion safeguard`
* `Fixed workspace switch validation`
* `Improved error message for invalid client spec`

Bad examples:

* `Fixed stuff`
* `Update`
* `Changes`

If applicable, reference related issues:

`Fixes issue #42`

---

## 🧾 Pull Request Process

1. Push your branch to your fork.
2. Open a pull request against the `main` branch.
3. Add PR details that include:

    * A clear summary of changes
    * Motivation / context
    * Any limitations or follow-up work
    * Screenshots or logs, if helpful

Pull requests may be reviewed for:

* Safety
* Security implications
* Workspace integrity
* Spec validation correctness
* Backward compatibility
* Code clarity

Maintainers may request changes before merging. Maintainers may also decide against accepting the pull request.

---

## 🔐 Safety and Permissions

P4MCP Server interacts with Perforce servers and may modify metadata.

Contributions must:

* Avoid force flags (`-f`) unless explicitly justified.
* Not introduce destructive operations by default.
* Preserve validation safeguards for workspace operations.
* Never expose credentials in logs or error messages.
* Use security-conscious design.

---

## 🐞 Reporting Issues

Please use GitHub Issues to report:

* Bugs
* Feature requests
* Documentation gaps

Include:

* Environment details (OS, Python version)
* P4 server version
* Clear steps to reproduce (greatly speeds up fixes)
* Relevant logs
* Expected vs actual behavior

---

## 📚 Documentation Contributions

Documentation improvements are welcome.

Examples:

* Adding usage examples
* Improving setup instructions
* Expanding safety notes

---

## ✅ Summary Checklist Before PR

Before submitting a pull request, check that:

* Code builds and runs locally
* It has been tested with a real P4 workspace
* No unsafe force operations have been added
* Documentation has been updated, if necessary
* Commit messages are clear
* A signed CLA is on file with Perforce

---

## 🤝 Community Expectations

* Be respectful and constructive.
* Focus on technical merit.
* Keep discussions professional.
* Assume good intent. See our code of conduct: [p4mcp-server/CODE_OF_CONDUCT.md](https://github.com/perforce/p4mcp-server/blob/main/CODE_OF_CONDUCT.md).

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT): [p4mcp-server/LICENSE.txt](https://github.com/perforce/p4mcp-server/blob/main/LICENSE.txt).
