import csv
import re
from pathlib import Path


_WORD_RE = re.compile(r"[A-Za-z0-9'-]+")
_TOKEN_RE = re.compile(r"[A-Za-z0-9'-]+|[^A-Za-z0-9'-]+")


class PhraseNormalizer:
    def __init__(self, mapping, max_len):
        self.mapping = mapping
        self.max_len = max_len

    @staticmethod
    def _tokenize(text):
        return _TOKEN_RE.findall(text)

    @staticmethod
    def _word_tokenize(text):
        return _WORD_RE.findall(text.lower())

    @staticmethod
    def _title_name(name):
        parts = [p for p in name.split("-") if p]
        titled = "-".join(part[:1].upper() + part[1:] for part in parts)
        return titled or name

    def _apply_custom_rules(self, text):
        def replace_delulu(match):
            name = match.group(1)
            suffix = match.group(2) or ""
            titled = self._title_name(name)
            return f"{titled} is being extremely delusional{suffix}"

        pattern = re.compile(r"\bsoafer\s+delulu\s+si\s+([A-Za-z][A-Za-z0-9-]*)([.!?]?)", re.IGNORECASE)
        updated = pattern.sub(replace_delulu, text)
        return updated

    def _apply_si_rule(self, tokens, word_positions):
        if not word_positions:
            return tokens

        output = []
        wi = 0
        first_word_pos = word_positions[0]
        output.extend(tokens[:first_word_pos])

        while wi < len(word_positions):
            token_index = word_positions[wi]
            word = tokens[token_index]
            lower = word.lower()
            if lower == "si" and wi + 1 < len(word_positions):
                name_token = tokens[word_positions[wi + 1]]
                titled = self._title_name(name_token)
                output.append(f"{titled} is")
                next_word_pos = word_positions[wi + 1]
                ay_pos = word_positions[wi + 2] if wi + 2 < len(word_positions) else None
                ay_token = tokens[ay_pos].lower() if ay_pos is not None else ""
                if ay_pos is not None and ay_token == "ay":
                    gap_tokens = tokens[next_word_pos + 1:ay_pos]
                    output.extend([tok for tok in gap_tokens if tok.strip()])
                    next_after = word_positions[wi + 3] if wi + 3 < len(word_positions) else len(tokens)
                    after_tokens = tokens[ay_pos + 1:next_after]
                    if output and after_tokens:
                        if output[-1].endswith(" ") and after_tokens[0].startswith(" "):
                            trimmed = after_tokens[0].lstrip()
                            after_tokens[0] = trimmed
                            if after_tokens[0] == "":
                                after_tokens = after_tokens[1:]
                    output.extend(after_tokens)
                    wi += 3
                else:
                    next_after = word_positions[wi + 2] if wi + 2 < len(word_positions) else len(tokens)
                    output.extend(tokens[next_word_pos + 1:next_after])
                    wi += 2
                continue

            output.append(word)
            next_after = word_positions[wi + 1] if wi + 1 < len(word_positions) else len(tokens)
            output.extend(tokens[token_index + 1:next_after])
            wi += 1

        return output

    def normalize(self, text):
        if not text:
            return text

        text = self._apply_custom_rules(text)

        tokens = self._tokenize(text)
        word_positions = [idx for idx, tok in enumerate(tokens) if _WORD_RE.fullmatch(tok)]
        word_tokens = [tokens[idx].lower() for idx in word_positions]

        if not word_tokens:
            return text

        output = []
        output.extend(tokens[:word_positions[0]])

        wi = 0
        while wi < len(word_tokens):
            matched = False
            max_len = min(self.max_len, len(word_tokens) - wi)
            for length in range(max_len, 0, -1):
                key = tuple(word_tokens[wi:wi + length])
                normalized = self.mapping.get(key)
                if normalized:
                    original_first = tokens[word_positions[wi]]
                    if wi == 0 and original_first[:1].isupper():
                        normalized = normalized[:1].upper() + normalized[1:]

                    output.append(normalized)
                    end_word_pos = word_positions[wi + length - 1]
                    next_after = word_positions[wi + length] if wi + length < len(word_positions) else len(tokens)
                    output.extend(tokens[end_word_pos + 1:next_after])
                    wi += length
                    matched = True
                    break

            if matched:
                continue

            token_index = word_positions[wi]
            output.append(tokens[token_index])
            next_after = word_positions[wi + 1] if wi + 1 < len(word_positions) else len(tokens)
            output.extend(tokens[token_index + 1:next_after])
            wi += 1

        output = self._apply_si_rule(output, [idx for idx, tok in enumerate(output) if _WORD_RE.fullmatch(tok)])
        normalized = "".join(output)
        normalized = re.sub(r"\bis,", "is", normalized)
        return normalized


def load_phrase_normalizer(csv_path):
    csv_path = Path(csv_path)
    mapping = {}
    max_len = 1

    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            slang = str(row.get("slang", "")).strip()
            normalized = str(row.get("normalized", "")).strip()
            if not slang or not normalized:
                continue
            tokens = _WORD_RE.findall(slang.lower())
            if not tokens:
                continue
            key = tuple(tokens)
            mapping[key] = normalized
            if len(tokens) > max_len:
                max_len = len(tokens)

    return PhraseNormalizer(mapping, max_len)
