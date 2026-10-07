import os
import hashlib

SENSITIVE_FILES = {
    r"C:\Users\Crown Tech\Desktop\AI-DLP-Agent\sensitive_files\employee_records.txt": "HIGH",
    r"C:\Users\Crown Tech\Desktop\AI-DLP-Agent\sensitive_files\salary.xlsx": "HIGH",
    r"C:\Users\Crown Tech\Desktop\AI-DLP-Agent\sensitive_files\company_strategy.docx": "HIGH",
    r"C:\Users\Crown Tech\Desktop\AI-DLP-Agent\sensitive_files\customer_data.txt": "CRITICAL",
}


def calculate_hash(file_path):
    sha256 = hashlib.sha256()

    try:
        with open(file_path, "rb") as file:
            while chunk := file.read(1024 * 1024):
                sha256.update(chunk)

        return sha256.hexdigest()

    except (FileNotFoundError, PermissionError, OSError):
        return None


def build_sensitive_hashes():
    sensitive_hashes = {}

    for file_path, sensitivity in SENSITIVE_FILES.items():

        if not os.path.isfile(file_path):
            continue

        file_hash = calculate_hash(file_path)

        if file_hash:
            sensitive_hashes[file_hash] = {
                "source_path": os.path.normcase(
                    os.path.abspath(file_path)
                ),
                "sensitivity": sensitivity
            }

    return sensitive_hashes


def get_sensitivity(file_path):
    filename = os.path.basename(file_path).lower()

    for sensitive_file, sensitivity in SENSITIVE_FILES.items():
        if os.path.basename(sensitive_file).lower() == filename:
            return sensitivity

    return "NORMAL"