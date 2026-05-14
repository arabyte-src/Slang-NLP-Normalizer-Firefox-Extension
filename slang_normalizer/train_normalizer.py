import argparse
import json
import random
from collections import Counter
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score


def load_lines(path):
    lines = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for raw in handle:
            text = raw.strip()
            if text:
                lines.append(text)
    return lines


def add_language_tag(text, language, use_language_tags):
    if not use_language_tags:
        return text
    tag = "__lang_en__" if language == "english" else "__lang_fil__"
    return f"{tag} {text}"


def build_examples(df, use_language_tags):
    inputs = []
    outputs = []
    for _, row in df.iterrows():
        slang = str(row["slang"]).strip()
        normalized = str(row["normalized"]).strip()
        language = str(row.get("language", "english")).strip().lower()
        if not slang or not normalized:
            continue
        inputs.append(add_language_tag(slang, language, use_language_tags))
        outputs.append(normalized)
    return inputs, outputs


def add_identity_examples(inputs, outputs, lines, language, use_language_tags):
    for text in lines:
        tagged = add_language_tag(text, language, use_language_tags)
        inputs.append(tagged)
        outputs.append(text)


def train_model(inputs, outputs, valid_split, random_seed):
    if valid_split > 0:
        label_counts = Counter(outputs)
        min_count = min(label_counts.values()) if label_counts else 0
        # Avoid stratification when rare labels exist.
        stratify_labels = outputs if min_count >= 2 else None
        x_train, x_valid, y_train, y_valid = train_test_split(
            inputs,
            outputs,
            test_size=valid_split,
            random_state=random_seed,
            stratify=stratify_labels,
        )
    else:
        x_train, y_train = inputs, outputs
        x_valid, y_valid = [], []

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    min_df=1,
                ),
            ),
            (
                "clf",
                LogisticRegression(max_iter=2000, solver="lbfgs"),
            ),
        ]
    )

    pipeline.fit(x_train, y_train)

    metrics = {}
    if x_valid:
        preds = pipeline.predict(x_valid)
        metrics["valid_accuracy"] = accuracy_score(y_valid, preds)
    return pipeline, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default=str(Path(__file__).resolve().parents[1] / "complete_slang_normalization_dataset.csv"),
    )
    parser.add_argument("--output", default="model.joblib")
    parser.add_argument("--extra-english", default=None)
    parser.add_argument("--extra-filipino", default=None)
    parser.add_argument("--use-language-tags", action="store_true", default=True)
    parser.add_argument("--no-language-tags", dest="use_language_tags", action="store_false")
    parser.add_argument("--valid-split", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args()

    random.seed(args.seed)

    df = pd.read_csv(args.csv)
    inputs, outputs = build_examples(df, args.use_language_tags)

    if args.extra_english:
        english_lines = load_lines(args.extra_english)
        add_identity_examples(inputs, outputs, english_lines, "english", args.use_language_tags)

    if args.extra_filipino:
        filipino_lines = load_lines(args.extra_filipino)
        add_identity_examples(inputs, outputs, filipino_lines, "filipino", args.use_language_tags)

    combined = list(zip(inputs, outputs))
    random.shuffle(combined)
    inputs, outputs = zip(*combined)

    model, metrics = train_model(list(inputs), list(outputs), args.valid_split, args.seed)

    payload = {
        "pipeline": model,
        "use_language_tags": args.use_language_tags,
        "metadata": {
            "valid_split": args.valid_split,
            "metrics": metrics,
            "label_count": len(set(outputs)),
        },
    }

    joblib.dump(payload, args.output)

    print(json.dumps(payload["metadata"], indent=2))


if __name__ == "__main__":
    main()
