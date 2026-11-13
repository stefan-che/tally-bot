import random

emojis = ["😄" ,"😁 ","😅", "☺️", " 😛","🤪", "🤨", "🧐", "😎", "🥸", "🤗",
          "🤑", "🤢", "🤠", "🤒", "😪", "🤭", "🤫", "😱", "😏", "😔", "🥳", "🤩", 
          "🤟", "🤞", "✌️", "👍", "🤝"]

def get_random_emoji():
    index = random.randrange(len(emojis))
    return emojis[index]
