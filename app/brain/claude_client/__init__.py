"""Shared Claude API wrapper for all Surf specialist scripts."""
# --------------------------------------------------------------------------- #
# PACKAGE RE-EXPORT — `app.brain.claude_client`
# --------------------------------------------------------------------------- #
# Simple explanation:
# This tiny file is the public door into the Claude client package. Any
# Surf script that needs to talk to Claude imports `call_claude` (and the
# key validator) from here, so the inner module file can move or be
# renamed without breaking callers.
#
# Important code pieces:
# - `from app.brain.claude_client.claude_client import ...`: pulls the two
#   real helpers out of the implementation file inside this folder.
# - `call_claude`: the single wrapper every specialist script uses to send
#   a system prompt + user message to Anthropic's Claude API.
# - `validate_anthropic_key`: cheap "does this key work" check used by P1
#   signup and P7 settings before saving a typed key.
# - `__all__`: lists the names a `from ... import *` would expose; also
#   signals to the team what is meant to be public from this package.
#
# App connection:
# Every Claude call in Surf — factsheet cleaner, LO extractor, MCQ
# generator, difficulty metadata critic — comes through `call_claude`.
from app.brain.claude_client.claude_client import call_claude, validate_anthropic_key

__all__ = ["call_claude", "validate_anthropic_key"]
