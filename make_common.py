#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
# SPDX-FileCopyrightText: Ferrous Systems and AdaCore

# Convenience script to build Sphinx books, including setting up a Python
# virtual environment to install Sphinx into (removing the need to manage
# dependencies globally). Each book should have a `make.py` script that updates
# the submodules, import this shared module, and calls the main function here.

from pathlib import Path
import argparse
import subprocess
import venv
import sys


def build_docs(root, env, builder, clear, serve, debug):
    dest = root / "build"

    args = ["-b", builder, "-d", dest / "doctrees"]
    if debug:
        # Disable parallel builds and show exceptions in debug mode.
        #
        # We can't show exceptions in parallel mode because in parallel mode
        # all exceptions will be swallowed up by Python's multiprocessing.
        # That's also why we don't show exceptions outside of debug mode.
        args += ["-j", "1", "-T"]
    else:
        # Enable parallel builds:
        args += ["-j", "auto"]
    if clear:
        args.append("-E")
    if serve:
        args += ["--watch", root / "exts", "--watch", root / "themes"]
    else:
        # Error out at the *end* of the build if there are warnings:
        args += ["-W", "--keep-going"]

    commit = current_git_commit(root)
    if commit is not None:
        args += ["-D", f"html_theme_options.commit={commit}"]

    try:
        subprocess.run(
            [
                env.bin("sphinx-autobuild" if serve else "sphinx-build"),
                *args,
                root / "src",
                dest / builder,
            ],
            check=True,
        )
    except KeyboardInterrupt:
        exit(1)
    except subprocess.CalledProcessError:
        print("\nhint: if you see an exception, pass --debug to see the full traceback")
        exit(1)

    return dest / builder


def build_linkchecker(root):
    repo = root / ".linkchecker"
    src = repo / "src" / "tools" / "linkchecker"
    bin = src / "target" / "release" / "linkchecker"

    if not src.is_dir():
        subprocess.run(["git", "init", repo], check=True)

        def git(args):
            subprocess.run(["git", *args], cwd=repo, check=True)

        # Avoid fetching blobs unless needed by the sparse checkout
        git(["remote", "add", "origin", "https://github.com/rust-lang/rust"])
        git(["config", "remote.origin.promisor", "true"])
        git(["config", "remote.origin.partialCloneFilter", "blob:none"])

        # Checkout only the linkchecker tool rather than the whole repo
        git(["config", "core.sparsecheckout", "true"])
        with open(repo / ".git" / "info" / "sparse-checkout", "w") as f:
            f.write("/src/tools/linkchecker/")

        # Avoid fetching the whole history
        git(["fetch", "--depth=1", "origin", "master"])
        git(["checkout", "master"])

    if not bin.is_file():
        subprocess.run(["cargo", "build", "--release"], cwd=src, check=True)

    return bin


def current_git_commit(root):
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                stdout=subprocess.PIPE,
            )
            .stdout.decode("utf-8")
            .strip()
        )
    # `git` executable missing from the system
    except FileNotFoundError:
        print("warning: failed to detect git commit: missing executable git")
        return
    # `git` returned an error (git will print the actual error to stderr)
    except subprocess.CalledProcessError:
        print("warning: failed to detect git commit: git returned an error")
        return


class VirtualEnv:
    def __init__(self, root, path):
        self.path = path
        self.requirements = root / "shared" / "requirements.txt"
        self.installed_requirements = path / "installed-requirements.txt"

        if not self.up_to_date():
            self.create()

    def bin(self, name):
        if sys.platform == "win32":
            return self.path / "scripts" / name
        else:
            return self.path / "bin" / name

    def up_to_date(self):
        if self.installed_requirements.exists():
            expected = self.requirements.read_bytes()
            installed = self.installed_requirements.read_bytes()
            if expected == installed:
                return True
        return False

    def create(self):
        venv.EnvBuilder(clear=True, symlinks=True, with_pip=True).create(self.path)
        subprocess.run(
            [self.bin("pip"), "install", "-r", self.requirements, "--require-hashes"],
            check=True,
        )
        self.installed_requirements.write_bytes(self.requirements.read_bytes())


def main(root):
    root = Path(root)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--clear", help="disable incremental builds", action="store_true"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-s",
        "--serve",
        help="start a local server with live reload",
        action="store_true",
    )
    group.add_argument(
        "--check-links", help="Check whether all links are valid", action="store_true"
    )
    group.add_argument(
        "--xml", help="Generate Sphinx XML rather than HTML", action="store_true"
    )
    group.add_argument(
        "--debug",
        help="Debug mode for the extensions, showing exceptions",
        action="store_true",
    )
    args = parser.parse_args()

    env = VirtualEnv(root, root / ".venv")
    rendered = build_docs(
        root, env, "xml" if args.xml else "html", args.clear, args.serve, args.debug
    )

    if args.check_links:
        linkchecker = build_linkchecker(root)
        if subprocess.run([linkchecker, rendered]).returncode != 0:
            print("error: linkchecker failed")
            exit(1)
