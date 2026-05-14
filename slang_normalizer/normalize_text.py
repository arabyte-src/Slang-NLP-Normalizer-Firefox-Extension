import argparse
from pathlib import Path

import joblib

from phrase_normalizer import load_phrase_normalizer


def load_inputs(args):
    if args.text:
        return [args.text]
    lines = []
    with Path(args.file).open("r", encoding="utf-8") as handle:
        for raw in handle:
            text = raw.rstrip("\n")
            if text:
                lines.append(text)
    return lines


def add_language_tag(text, language, use_language_tags):
    if not use_language_tags or language == "auto":
        return text
    tag = "__lang_en__" if language == "english" else "__lang_fil__"
    return f"{tag} {text}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="model.joblib")
    parser.add_argument("--text", default=None)
    parser.add_argument("--file", default=None)
    parser.add_argument("--language", choices=["english", "filipino", "auto"], default="auto")
    parser.add_argument("--min-confidence", type=float, default=0.0)
    parser.add_argument(
        "--force-model",
        action="store_true",
        help="Always output the model prediction, ignoring confidence.",
    )
    args = parser.parse_args()

    if not args.text and not args.file:
        raise SystemExit("Provide --text or --file")

    payload = joblib.load(args.model)
    phrase_normalizer = load_phrase_normalizer(
        Path(__file__).resolve().parents[1] / "complete_slang_normalization_dataset.csv"
    )

    inputs = load_inputs(args)
    for original in inputs:
        normalized = phrase_normalizer.normalize(original)
        if args.force_model:
            print(normalized)
        else:
            print(normalized)


if __name__ == "__main__":
    main()
