"""Entry point for ``python -m brew_tui`` and ``brew-tui`` CLI."""

from .app import BrewTUI


def main() -> None:
    BrewTUI().run()


if __name__ == "__main__":
    main()
