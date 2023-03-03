from os.path import exists
from re import findall
from colorama import Back, Fore, Style, init
from loguru import logger
@logger.catch
def path_generate():
    while True:
        if not exists((path := findall(r".+(?<=\\)", string=__file__)[0]) + "ui_tree.txt"):
            open(f"{path}ui_tree.txt", "x")
        tree_file = open(f"{path}ui_tree.txt")
        text, input_name, path = [line for line in tree_file.readlines() if line.strip() != ""], input("Enter a Window Name: "), []
        name = input_name.split("/")
        tree_file.close()
        for i, line in enumerate(text, 1):
            if f"[{name[-1].lower()}]" in line.lower():
                name_dup, temp_text, depth = name[:-1].copy(), text[:i][::-1], line.count("-") - 1
                should_break = False if name_dup else True
                while name_dup:
                    for j, subline in enumerate(temp_text, 0):
                        if f"[{name_dup[-1].lower()}]" in subline.lower():
                            name_dup.pop()
                            temp_text = temp_text[j:]
                            depth -= 1
                            if not name_dup:
                                should_break = True
                            break
                        elif subline.count("-") < depth:
                            name_dup = None
                            break
                    else:
                        break
                if should_break:
                    text = reversed(text[:i])
                    break
        for i, line in enumerate(text, 0):
            if not line.count("-"):
                break
            elif not i:
                depth = line.count("-") - 1
                path.append(findall("(?<=\[).+(?=\])", line)[0]) if "[]" not in line else path.append("")
            elif depth == line.count("-"):
                depth -= 1
                path.append(findall("(?<=\[).+(?=\])", line)[0]) if "[]" not in line else path.append("")
        print(f"{Style.BRIGHT}" + str(path[::-1]).replace(", ", f"{Fore.CYAN},{Fore.RESET} ").replace("['", f"{Fore.GREEN}[{Fore.RESET}'").replace("']", f"'{Fore.GREEN}]{Fore.RESET}") + f"{Style.NORMAL}") if path else print(f"{Back.RED}Window matching the name '{input_name}' not found.{Back.RESET}")
init()
path_generate()
