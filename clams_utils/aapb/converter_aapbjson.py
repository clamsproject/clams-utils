import argparse
import sys
import json
import math
import typing

import mmif
from lapps.discriminators import Uri
from mmif import AnnotationTypes, DocumentTypes, Document
from mmif.utils import timeunit_helper as tuh

from clams_utils.aapb import guidhandler


def normalize_timeframe_times(tf: mmif.Annotation) -> typing.Tuple[float, float]:
    s = tuh.convert(tf.get_property("start"), tf.get_property("timeUnit"), "ms", 0) / 1000
    e = tuh.convert(tf.get_property("end"), tf.get_property("timeUnit"), "ms", 0) / 1000
    return s, e


def get_parts_from_view(view: mmif.View) -> typing.List[typing.Dict[str, typing.Union[str, float]]]:
    parts = []
    AAPB_dict = {}
    speaker_id = 1

    for sent in view.get_annotations(Uri.SENTENCE):
        direct_tf = False
        s = e = -1
        # 1. sentence is directly aligned to the time frame (the easier case)
        for aligned in sent.get_all_aligned():
            if aligned.at_type == AnnotationTypes.TimeFrame:
                direct_tf = True
                s, e = normalize_timeframe_times(aligned)
                break
        # 2. sentence has a list of targets of tokens that are aligned to time frames
        if not direct_tf:
            stoken = view.get_annotation_by_id(sent.get_property("targets")[0])
            etoken = view.get_annotation_by_id(sent.get_property("targets")[-1])
            s = math.inf
            e = -1
            for token in (stoken, etoken):
                for aligned in token.get_all_aligned():
                    if aligned.at_type == AnnotationTypes.TimeFrame:
                        tok_s, tok_e = normalize_timeframe_times(aligned)
                        s = min(s, tok_s)
                        e = max(e, tok_e)
        AAPB_dict["start_time"] = f"{s:.3f}"
        AAPB_dict["end_time"] = f"{e:.3f}"
        AAPB_dict["text"] = sent.get_property("text")
        AAPB_dict["speaker_id"] = speaker_id
        parts.append(AAPB_dict)
        AAPB_dict = {}
        speaker_id += 1
    return parts


def convert_mmif_to_aapbjson(mmif_obj: mmif.Mmif, out_f: typing.IO, pretty=True):
    done = False
    for view in mmif_obj.views:
        # TODO (krim @ 8/23/24): is this the best check to grab an ASR view? 
        if all(map(lambda x: x in view.metadata.contains, [
            Uri.SENTENCE,
            AnnotationTypes.TimeFrame,
            AnnotationTypes.Alignment,
            DocumentTypes.TextDocument,
        ])):
            lang = 'en-US'  # default language
            guid = None
            for annotation in view.annotations:
                if annotation.at_type == DocumentTypes.TextDocument:
                    lang = annotation.text_language
                    for aligned in annotation.get_all_aligned():
                        if aligned.at_type in (DocumentTypes.AudioDocument, DocumentTypes.VideoDocument):
                            guid = guidhandler.get_aapb_guid_from(Document(aligned.serialize()).location_address())
                            break
            if guid is None:
                raise ValueError("No GUID found in the MMIF file.")
            parts = get_parts_from_view(view)
            out_obj = {
                'id': guid,
                'language': lang,
                'parts': parts
            }
            json.dump(out_obj, out_f, indent=2 if pretty else None)
            done = True
            break
    if not done:
        raise ValueError("No ASR view found in the MMIF file.")


CMD_NAME = 'convert-json'


def prep_argparser(subparsers):
    """
    Prepare the argument parser for the convert command.
    """
    convert_parser = subparsers.add_parser(
        CMD_NAME,
        description="Convert between MMIF and AAPB-JSON formats.",
        help="Convert between MMIF and AAPB-JSON formats."
    )
    convert_group = convert_parser.add_mutually_exclusive_group(required=True)
    convert_group.add_argument('--from-aapb', action='store_true', help='Convert from AAPB-JSON to MMIF (not implemented).')
    convert_group.add_argument('--to-aapb', action='store_true', help='Convert from MMIF to AAPB-JSON.')
    convert_parser.add_argument('IN_FILE', nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file path, or STDIN if not provided")
    convert_parser.add_argument('OUT_FILE', nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file path, or STDOUT if not provided")
    convert_parser.add_argument('-p', '--pretty', action='store_true', help="indent output json (default: False)")
    convert_parser.set_defaults(func=main)


def main(args):
    """
    Main function for the convert command.
    """
    if args.to_aapb:
        try:
            mmif_obj = mmif.Mmif(args.IN_FILE.read())
            convert_mmif_to_aapbjson(mmif_obj, args.OUT_FILE, pretty=args.pretty)
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)
    elif args.from_aapb:
        print("Conversion from AAPB-JSON to MMIF is not implemented yet.", file=sys.stderr)
        sys.exit(1)