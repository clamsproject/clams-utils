import mmif
import json
import argparse
import os

GUID = 'cpb-aacip' # The `id` should be only the AAPB “GUID”, which always start with 'cpb-aacip'.

def read_mmif(mmif_file: str) -> mmif.Mmif:
    """
    Function to read mmif file and return the mmif object.

    :param mmif_file: file path to the mmif.
    :return: mmif object
    """
    try:
        with open(mmif_file, 'r') as file:
            mmif_obj = mmif.Mmif(file.read())

    except FileNotFoundError:
        print(f"Error: MMIF file '{mmif_file}' not found.")
    except Exception as e:
        print(f"Error: An unexpected error occurred - {e}")

    return mmif_obj


def get_parts_from_mmif(mmif_obj: mmif.Mmif) -> list[dict[str, str]]:
    """
    Function to get necessary annotations from mmif file for converting to AAPB.

    :param mmif_obj: mmif object
    :return: list of dictionaries correspond to the parts of AAPB-json.
    """
    parts = []
    for view in mmif_obj.views:
        tmp_TF = []
        AAPB_dict = {}
        speaker_id = 1

        if "/whisper-wrapper/" in view.metadata.app:
            for annotation in view.annotations:
                if "TimeFrame" in str(annotation.at_type):
                    tmp_TF.append((annotation.get_property("start"), annotation.get_property("end")))

                if "Sentence" in str(annotation.at_type):
                    try:
                        if len(tmp_TF) == len(annotation.get_property("targets")):
                            AAPB_dict["start_time"] = str(tmp_TF[0][0])
                            AAPB_dict["end_time"] = str(tmp_TF[-1][1])
                            AAPB_dict["text"] = annotation.get_property("text")
                            AAPB_dict["speaker_id"] = speaker_id
                        else:
                            print("Error: Token length mismatch in Sentence")

                        parts.append(AAPB_dict)
                        tmp_TF = []
                        AAPB_dict = {}
                        speaker_id += 1

                    except (KeyError, IndexError) as e: # some empty sentence annotation in whisper-out mmif.
                        print("Empty Sentence:", annotation.get_property("id"))
        
        else:
            for annotation in view.annotations:
                if "Alignment" in str(annotation.at_type):
                    target = view.get_annotation_by_id(annotation.get_property("target"))
                    if "Sentence" in str(target.at_type):
                        tf = view.get_annotation_by_id(annotation.get_property("source"))
                        AAPB_dict["start_time"] = str(tf.get_property("start"))
                        AAPB_dict["end_time"] = str(tf.get_property("end"))
                        AAPB_dict["text"] = target.get_property("text")
                        AAPB_dict["speaker_id"] = speaker_id
                    
                        parts.append(AAPB_dict)
                        AAPB_dict = {}
                        speaker_id += 1

    return parts


def get_id_lang_from_mmif(mmif_obj: mmif.Mmif) -> tuple[str, str]:  ## location? or only file name for ID?
    """
    Fucntion to get id and language from mmif.

    :param mmif_obj: mmif object
    :return: id, language in tuple of string format
    """
    lang = None
    for doc in mmif_obj.documents:
        file_name = os.path.basename(doc.properties.location)
        file_name, _ = os.path.splitext(file_name)
        assert GUID in file_name, "Missing GUID in document file name in the mmif file"

        first_occurrence_index = set((file_name.find('.'), file_name.find('_'), file_name.find(' ')))

        if max(first_occurrence_index) == -1:
            # If none of ".", "_", or whitespace found, id would be the whole string
            id = file_name
        else:
            # Otherwise, return the substring up to the first occurrence
            first_occurrence_index.remove(-1)
            id = file_name[:min(first_occurrence_index)]


    for view in mmif_obj.views:
        for annotation in view.annotations:
            if "TextDocument" in str(annotation.at_type):
                lang = annotation.get_property("text")._language

    return id, lang


def create_AAPB_json(id:str, lang:str, parts:list[dict], file_path:str, pretty=True):
    """
    Create AAPB-JSON file to a given file path.

    :param id: id
    :param lang: language
    :param parts: list of dictionaries for annotations
    :param file_path: path to save the converted output file
    :param pretty: boolean whether using pretty printing or not
    """
    AAPB_dict = {}
    AAPB_dict["id"] = id
    AAPB_dict["language"] = lang
    AAPB_dict["parts"] = parts
    # Check if the same file name exist in the path and avoid overwriting.
    if os.path.exists(file_path):
        file_name, file_extension = os.path.splitext(file_path)
        count = 1
        while os.path.exists(f"{file_name}_{count}.json"):
            count += 1
        file_path = f"{file_name}_{count}.json"

    with open(file_path, "w") as json_file:
        if pretty:
            json.dump(AAPB_dict, json_file, indent=2)
        else:
            json.dump(AAPB_dict, json_file)

def main():
    parser = argparse.ArgumentParser(description="Convert MMIF <-> AAPB-JSON.")
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')
    convert_parser = subparsers.add_parser('convert', help='Convert MMIF <-> AAPB-JSON')
    convert_parser.add_argument('--from-mmif', action='store_true', help='Specify the format')
    convert_parser.add_argument('-i', '--input', type=str, required=True, help='Input file')
    convert_parser.add_argument("-o", '--output', default="converted.json", type=str,
                        help="Path to the converted AAPB-JSON output file (default: converted.json)")
    convert_parser.add_argument("-p", '--pretty', default=True, type=bool, help="Pretty print (default: pretty=True)")
    args = parser.parse_args()

    if args.command == 'convert':
        if args.input:
            mmif_obj = read_mmif(args.input)
            parts = get_parts_from_mmif(mmif_obj)
            id, lang = get_id_lang_from_mmif(mmif_obj)
            create_AAPB_json(id, lang, parts, args.output, args.pretty)

if __name__ == "__main__":
    main()