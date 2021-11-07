from pathlib import Path
from time import sleep

from compiler import Compiler

if __name__ == '__main__':
    with Path('src.pc').open('r', encoding='cp949') as src_file:
        content = src_file.read()

    try:
        Compiler(content)
    except BaseException as e:
        sleep(0.2)
        raise e
