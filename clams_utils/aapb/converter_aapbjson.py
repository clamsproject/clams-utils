import argparse
import json
import math
import sys
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
    

def main():
    parser = argparse.ArgumentParser(description="Convert MMIF <-> AAPB-JSON.")
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')
    convert_parser = subparsers.add_parser('convert', help='Convert MMIF <-> AAPB-JSON')
    # TODO (krim @ 8/23/24): add the inverse conversion from AAPB-JSON to MMIF when the AAPB-JSON format is finalized. 
    convert_parser.add_argument('--from-mmif', action='store_true', help='conversion direction')
    convert_parser.add_argument('--to-mmif', action='store_true', help='conversion direction')
    convert_parser.add_argument("-p", '--pretty', action='store_true', help="indent output json (default: False)")
    convert_parser.add_argument("IN_FILE",
                                nargs="?", type=argparse.FileType("r"),
                                default=None if sys.stdin.isatty() else sys.stdin,
                                help='input MMIF file path, or STDIN if `-` or not provided.')
    convert_parser.add_argument("OUT_FILE",
                                nargs="?", type=argparse.FileType("w"),
                                default=sys.stdout,
                                help='output MMIF file path, or STDOUT if `-` or not provided.')
    args = parser.parse_args()
    if args.command == 'convert':
        # print(type(args.IN_FILE))
        if args.to_mmif:
            raise NotImplementedError("Conversion from AAPB-JSON to MMIF is not implemented yet.")
        else:  # meaning, --from-mmif flag actually doesn't need to be specified anyway. It's just for clarity.
            convert_mmif_to_aapbjson(mmif.Mmif(args.IN_FILE.read()), args.OUT_FILE, args.pretty)


if __name__ == "__main__":
    main()
