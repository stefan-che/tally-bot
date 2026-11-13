from colorama import Fore
from .error import exception_with_line

def visualise(value, title=None, keyHighlight=[], skip=[],onlyK1=[], onlyK2=[], colorTemplate=1, colorHighlight=1, value_is_equal=[]):
    COLOR__K1_H = Fore.LIGHTCYAN_EX
    COLOR__V1_H = Fore.YELLOW
    COLOR__K2_H = Fore.CYAN
    COLOR__V2_H = Fore.WHITE
    if colorHighlight ==2:
        COLOR__K1_H = Fore.LIGHTCYAN_EX
        COLOR__V1_H = Fore.WHITE
        COLOR__K2_H = Fore.YELLOW
        COLOR__V2_H = Fore.LIGHTGREEN_EX

    COLOR_T = Fore.LIGHTMAGENTA_EX
    COLOR_K1 = Fore.RED
    COLOR_V1 = Fore.GREEN
    COLOR_K2 = Fore.BLUE
    COLOR_V2 = Fore.GREEN
    if colorTemplate == 2:
        COLOR_T = Fore.YELLOW
        COLOR_K1 = Fore.MAGENTA
        COLOR_V1 = Fore.LIGHTBLUE_EX
        COLOR_K2 = Fore.LIGHTMAGENTA_EX
        COLOR_V2 = Fore.BLUE

    try:
        if title:
            print()
            print(COLOR_T+title);
        if type(value) == type({}):
            for key in value:
                if key not in skip and (not onlyK1 or key in onlyK1):
                    if key in keyHighlight:
                        print(COLOR__K1_H+"",key, end="");
                    else:
                        print(COLOR_K1+"",key, end="");

                    if type(value[key]) == type({}):
                        print()
                        for k in value[key]:
                            if k not in skip and (not onlyK2 or k in onlyK2):
                                if (k in keyHighlight) or (value[key][k] in value_is_equal):
                                    print (COLOR__K2_H+"  ",k,COLOR__V2_H+"  ", value[key][k])
                                else:
                                    print (COLOR_K2+"  ",k,COLOR_V2+"  ", value[key][k])
                    else:
                        if key in keyHighlight or value[key] in value_is_equal:
                            print (COLOR__V1_H+"  ", value[key])
                        else:
                            print (COLOR_V1+"  ", value[key])
        else:
            for el in value:
                print(Fore.BLACK+"[")
                if type(el) == type({}):
                    for key in el:
                        if key not in skip and (not onlyK1 or key in onlyK1):   
                            if key in keyHighlight:
                                print(COLOR__K1_H+" ",key, end="");
                            else:
                                print(COLOR_K1+" ",key, end="");

                            if type(el[key]) == type({}):
                                print()
                                for k in el[key]:
                                    if k not in skip and (not onlyK2 or k in onlyK2):
                                        if k in keyHighlight or el[key][k] in value_is_equal:
                                            print (COLOR__K2_H+"     ",k,COLOR__V2_H+" ", el[key][k])
                                        else:
                                            print (COLOR_K2+"     ",k,COLOR_V2+" ", el[key][k])
                            else:
                                if key in keyHighlight or el[key] in value_is_equal:
                                    print (COLOR__V1_H+"  ", el[key])
                                else:
                                    print (COLOR_V1+"  ", el[key])
                else:
                    print (Fore.GREEN+" ", el)
                print(Fore.BLACK+"]")
                
        print()
    except Exception as e:
        print(Fore.RED,e)
        exception_with_line()
        print(Fore.LIGHTBLACK_EX+"ERR\n",value, "\n")
