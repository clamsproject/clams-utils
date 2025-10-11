import argparse
import pkgutil
import importlib
import sys
from . import __name__ as package_name

def main():
    """
    The main entry point for the dynamic CLI.

    This script automatically discovers and registers subcommands from sibling modules
    that adhere to a specific convention. To make a module compatible with this
    dispatcher, the module must provide the following:

    1. A function `prep_argparser(subparsers)`:
       This function takes an `argparse._SubParsersAction` object and is responsible
       for creating a new subparser, defining its arguments, and setting the default
       function to be called.

    2. A function `main(args)`:
       This function takes the parsed arguments object and contains the core logic
       for the subcommand.

    3. (Optional) A string variable `CMD_NAME`:
       If provided, this variable is used as the subcommand name. If not, the
       subcommand name defaults to the module's filename.
    """
    parser = argparse.ArgumentParser(description="A unified CLI for CLAMS AAPB utilities.")
    subparsers = parser.add_subparsers(title="commands", dest="command")
    subparsers.required = True

    # Discover and register subcommands from sibling modules
    package = sys.modules[package_name]
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        if module_name == 'cli':
            continue
        try:
            module = importlib.import_module(f".{module_name}", package_name)
            if hasattr(module, 'prep_argparser'):
                module.prep_argparser(subparsers)
        except Exception as e:
            # Optionally, print a warning to stderr if a module fails to load
            print(f"Warning: Could not load subcommand from '{module_name}': {e}", file=sys.stderr)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)

if __name__ == '__main__':
    main()