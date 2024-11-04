import json

class JSONHandler:
    @staticmethod
    def get_token(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()

    @staticmethod
    def save_to_json(data, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
