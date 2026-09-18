def normalize_persian(value:str)->str:
    return value.replace("ي","ی").replace("ى","ی").replace("ك","ک").replace("ۀ","هٔ").strip()
