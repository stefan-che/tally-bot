
def get_base_quote(pair: str, default_quote:str = "USDT"):
    pair_split = pair.split("-")
    if len(pair_split) == 1:
        base = pair_split[0]
        quote = default_quote  # Set your desired default value here
    elif len(pair_split) == 2:
        base, quote = pair_split
    else:
        return "", ""
    
    return base, quote