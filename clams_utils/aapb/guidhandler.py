"""
Module that provides a function to handle AAPB GUIDs, mainly recognizing and extracting the AAPB ID from a string (e.g., a file name). Note that GUID in this context refers to the AAPB media/asset ID, not the globally unique identifier (https://en.wikipedia.org/wiki/Universally_unique_identifier).

"""

import re
from typing import Optional


def get_aapb_guid_from(s: Optional[str]) -> Optional[str]:
    """
    Extracts the AAPB GUID from a string, if present.
    The function returns the GUID if found, otherwise it returns None.
    """
    if s is None:
        return None
    m = re.search(r'(cpb-aacip[-_][a-z0-9-]+).', s)
    
    if m is None:
        return m
    else:
        m_str = m.group(1)
        m_parts = list(reversed(re.split(r'[-_]', m_str)))
        cur = 0
        for part in m_parts:
            if part.isalpha():  # all alphabets means some meaningful suffix (like `-transcript`)
                cur += 1 
            else:
                break
        num_guid_chars = len(' '.join(m_parts[cur:]))
        return m_str[:num_guid_chars]


def prep_argparser(subparsers):
    """
    Prepare the argument parser for the guidhandler command.
    """
    guidhandler_parser = subparsers.add_parser(
        __name__.split('.')[-1],
        description="Extract an AAPB GUID from a string.",
        help="Extract an AAPB GUID from a string."
    )
    guidhandler_parser.add_argument("string", help="input string to search for a GUID")
    guidhandler_parser.set_defaults(func=main)


def main(args):
    """
    Main function for the guidhandler command.
    """
    guid = get_aapb_guid_from(args.string)
    if guid:
        print(guid)