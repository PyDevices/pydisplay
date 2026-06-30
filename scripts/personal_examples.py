"""Local-only trees under ``src/examples/`` — symlinks or gitignored checkouts.

Never included in ``packages/examples.json``, PyScript gallery generation, or CI.
"""

PERSONAL_EXAMPLE_DIRS = frozenset(
    {
        "frogger",
        "spotapi",
        "spotify_remote",  # apps/spotify_remote in spotapi repo
        "spotify_client",  # alias if the symlink is renamed locally
    }
)
