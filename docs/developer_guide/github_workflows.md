---
toc_depth: 2
---

# GitHub Workflows

Some work has to happen every time something changes: run the tests when someone proposes a change, publish the packages when a version is released. Done by hand, it is slow and easily forgotten. [GitHub Actions](https://docs.github.com/en/actions/about-github-actions/understanding-github-actions) does it automatically. When an **event** happens on GitHub, such as a pull request being opened, it starts fresh computers in GitHub's data centers and runs the commands we wrote down.

Those commands live in **workflows**: YAML files in [`.github/workflows/`](https://github.com/rendercv/rendercv/tree/main/.github/workflows) that say which events start them and what to do. A workflow is made of **jobs**, which run at the same time on separate machines unless one waits for another. Each job is a list of **steps**, such as downloading the code, installing dependencies, and running the tests.

Testing every proposed change automatically is called **continuous integration (CI)**. Reviewers see whether a change works on clean machines, not only on its author's computer. The workflows use the same `just` commands and the same locked versions as local development, so they check exactly what you can check yourself.

## Tests

[`test.yaml`](https://github.com/rendercv/rendercv/blob/main/.github/workflows/test.yaml) runs for every pull request, every change to `main`, on request, and when another workflow calls it. It:

1. Runs the code checks (`just check`) and builds the documentation in strict mode.
2. Runs the tests on Linux, Windows, and macOS, each with Python 3.12, 3.13, 3.14, and 3.15, recording coverage.
3. Combines the coverage of all those runs into one report and publishes it.
4. Builds the Docker image and renders a CV with the network switched off (see [Docker](dockerfile.md#building-and-testing-offline)).

The twelve combinations of operating system and Python version are called a **test matrix**. Running the same tests in each catches problems that appear only on one system, such as the backslashes Windows uses in file paths, or only with one Python version.

## Documentation

[`deploy-docs.yaml`](https://github.com/rendercv/rendercv/blob/main/.github/workflows/deploy-docs.yaml) builds the site with `just build-docs` and publishes it with GitHub Pages whenever changes reach `main`, or on request. See [Documentation](documentation.md).

## Executables

[`create-executables.yaml`](https://github.com/rendercv/rendercv/blob/main/.github/workflows/create-executables.yaml) builds the [single-file programs](project_management.md#delivering-rendercv-to-users) with `just create-executable`, on request or as part of a release. An executable only runs on the kind of computer it was built for, so it is built four times: Linux on x86_64 and on ARM64, macOS on ARM64, and Windows on x86_64. x86_64 and ARM64 are the two common families of processors; most Windows computers use x86_64, and Macs with Apple chips use ARM64. The workflow saves the programs as **artifacts**, files a workflow keeps so that people or later jobs can download them.

## Releases

A GitHub **release** marks a version as published and holds its release notes and downloadable files. Publishing one starts [`release.yaml`](https://github.com/rendercv/rendercv/blob/main/.github/workflows/release.yaml), which:

1. Runs the test workflow.
2. Builds the wheels and source distributions of `rendercv` and `rendercv-fonts`, and the executables.
3. Attaches those files to the GitHub release.
4. Uploads the wheels and source distributions to PyPI, skipping any version that is already there.
5. Builds the Docker image and uploads it to GitHub Container Registry.

The fonts package has its own version number, so step 4 publishes it only when that number changes.

PyPI accepts an upload only with proof that it comes from the project. Instead of a password stored in GitHub, which could leak, RenderCV uses **trusted publishing**: the project tells PyPI to accept uploads from one particular workflow, and GitHub vouches to PyPI for which workflow is running. Each package's trusted publisher on PyPI must name owner `rendercv`, repository `rendercv`, workflow `release.yaml`, and environment `release`.

Publishing on Typst Universe is separate; see [Publish the Typst Package](how_to/publish_typst_package.md).

## Published AI agent skill

An **AI agent skill** is a set of instructions that teaches AI assistants how to use RenderCV. `just update-skill` generates it into `skills/` from RenderCV's own themes, locales, and models, so it can't fall out of date. [`publish-skill.yaml`](https://github.com/rendercv/rendercv/blob/main/.github/workflows/publish-skill.yaml) copies that folder to the [rendercv-skill](https://github.com/rendercv/rendercv-skill) repository, where people install it from, whenever a release is published or on request. To be allowed to write there, it uses `RENDERCV_SKILL_DEPLOY_KEY`, a **repository secret**: a value stored encrypted in the repository's settings that workflows can use but nobody can read back.

## Issue and pull request assistance

Three workflows use Anthropic's Claude: one answers `@claude` requests, one reviews pull requests, and one triages new issues. They follow the same [contributing](contributing.md) and [testing](testing.md) guides as human contributors. They need the Claude GitHub App installed and the `ANTHROPIC_API_KEY` repository secret. Each workflow file defines what starts it and what it is allowed to do.
