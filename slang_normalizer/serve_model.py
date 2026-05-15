import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import joblib

from phrase_normalizer import load_phrase_normalizer
# from nlp_normalizer import load_nlp_normalizer  # Optional; commented out if unavailable


class ModelHandler(BaseHTTPRequestHandler):
    model_payload = None
    phrase_normalizer = None
    nlp_normalizer = None

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_POST(self):
        if self.path != "/normalize":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode("utf-8"))
            return

        text = str(payload.get("text", "")).strip()
        language = str(payload.get("language", "auto")).lower()

        normalized = self.phrase_normalizer.normalize(text)
        found = normalized.strip() != text.strip()
        confidence = 1.0 if found else 0.0

        # Fallback to NLP-based fuzzy match when phrase lookup didn't change the text
        if not found and hasattr(self, "nlp_normalizer") and self.nlp_normalizer is not None:
            nlp_normalized, nlp_score = self.nlp_normalizer.normalize(text)
            confidence = float(nlp_score)
            if nlp_score >= getattr(self, "nlp_threshold", 0.5):
                normalized = nlp_normalized
                found = True

        self._set_headers(200)
        self.wfile.write(json.dumps({"meaning": normalized, "found": found, "confidence": confidence}).encode("utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="model.joblib")
    parser.add_argument(
        "--csv",
        default=str(Path(__file__).resolve().parents[1] / "complete_slang_normalization_dataset.csv"),
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--nlp-threshold", type=float, default=0.5,
                        help="Similarity threshold for NLP fallback (0-1)")
    args = parser.parse_args()

    ModelHandler.model_payload = joblib.load(args.model)
    ModelHandler.phrase_normalizer = load_phrase_normalizer(args.csv)
    # ModelHandler.nlp_normalizer = load_nlp_normalizer(args.csv)  # Optional fallback
    ModelHandler.nlp_threshold = float(args.nlp_threshold)
    server = HTTPServer((args.host, args.port), ModelHandler)
    print(f"Model server listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
