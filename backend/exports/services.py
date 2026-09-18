SUPPORTED_FORMATS={"csv","xlsx","json","jsonl","docx","pdf"}
def validate_format(value):
    if value not in SUPPORTED_FORMATS: raise ValueError("Unsupported export format")
    return value
