import numexpr as ne
from colorama import Fore
from app.utils import exception_with_line


def validate_num(inp: str):
    try:
        temp = list(inp.replace(" ", "").replace(",", "."))
        print(Fore.BLACK, "validate_num :::", Fore.BLUE, temp)
        for i, x in enumerate(temp):
            # Convert all values with % to values like (... + 10% -> ... * 1.1) | (... - 25% -> ... * 0.75)
            if x == '%':
                
                # get full Number.
                k = i - 1
                newValue = []
                while (temp[k].isdigit() or temp[k] == "."):
                    newValue.insert(0, temp[k])
                    k -= 1
                
                # if value is 25.5% here would be 25.5 / 100 = 0.255
                newValue = float("".join(newValue)) / 100
                
                if temp[k] == '+' :
                    # If before percent was '+': 1 + 10% = 1 * 1.1
                    temp[k] = "*"
                    temp[k+1: i+1] = [str(1 + newValue)]
                elif temp[k] == '-':
                    # If before percent was '+': 1 - 10% = 1 * 0.9
                    temp[k] = "*"
                    temp[k+1: i+1] = [str(1 - newValue)]
                elif temp[k] in ["*", "/"]:
                    # If before percent was '*' or '/': #! we should not handle this
                    temp[k+1: i+1] = [str(0 + newValue)]
                else:
                    # If unknown symbol, just set the whole value to '0'
                    temp[k+1: i+1] = ["0"]

        print(f'{Fore.BLACK}Formula to evaluate:', Fore.YELLOW, "".join(temp))
        return "".join(temp)
    except Exception as e:
        print(Fore.RED, e)
        exception_with_line()