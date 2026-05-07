from pathlib import Path


def build_email_map(email_file: Path, doc_numbers) -> dict:
    """Stream the email file once and pull mappings for the requested doc numbers."""
    wanted = {d for d in doc_numbers if d}
    if not wanted:
        return {}

    mapping = {}
    with email_file.open("r", encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line:
                continue
            doc, _, email = line.partition(",")
            doc = doc.strip()
            if doc in wanted and doc not in mapping:
                mapping[doc] = email.strip()
                if len(mapping) == len(wanted):
                    break
    return mapping
