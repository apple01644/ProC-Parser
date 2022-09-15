import hashlib
import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Iterable, Tuple


@dataclass
class Quest:
    title: str
    desc: str
    correct_answer: bool


class MainProgram:
    def __init__(self):
        self.cwd: Path = Path(os.getcwd())
        print('Program run on', self.cwd)
        self.__files__: Optional[List[Path]] = None
        self.stat_file = self.cwd / 'stat.json'
        self.stat: Dict[int, int] = {}
        self.quests: List[Quest] = list()
        self.deck: List[Tuple[Quest, int]] = list()

        if self.stat_file.is_file() is True:
            self.stat = {
                int(k): v for k, v in json.loads(self.stat_file.read_text()).items()
            }

    def save(self):
        self.stat_file.write_text(json.dumps(self.stat, indent=2))

    def __del__(self):
        self.save()

    @property
    def files(self) -> List[Path]:
        if self.__files__ is None:
            self.__files__ = list()
            parent_dir = self.cwd / '부자체'
            for child_dir in parent_dir.iterdir():
                if child_dir.is_dir() is False:
                    continue
                for data_file in child_dir.iterdir():
                    self.__files__.append(data_file)
        return self.__files__

    def load_questions(self):
        be_statement_pair = [
            ('된다.', '되지 아니한다.'),
            ('본다.', '보지 아니한다.'),
            ('있다.', '있지 않다.'),
            ('포함한다.', '제외한다.'),
            ('한다.', '하지 않는다.'),
            ('가능하다.', '불가하다.'),
        ]

        for file in self.files:
            title = f'{file.parent.name}:{file.stem}'
            content = file.read_text(encoding='utf-8')
            content = content.replace('\\\n', '\1')
            for line in content.splitlines():
                line = line.replace('\1', '\n')
                if line.endswith('.false'):
                    quest = Quest(
                        title=title,
                        desc=line[:-5],
                        correct_answer=False,
                    )
                    self.quests.append(quest)
                elif line.endswith('.true'):
                    quest = Quest(
                        title=title,
                        desc=line[:-4],
                        correct_answer=True,
                    )
                    self.quests.append(quest)
                else:
                    for positive, negative in be_statement_pair:
                        if line.endswith(positive):
                            quest = Quest(
                                title=title,
                                desc=line,
                                correct_answer=True,
                            )
                            self.quests.append(quest)
                            false_desc = line.replace(positive, negative)
                            quest = Quest(
                                title=title,
                                desc=false_desc,
                                correct_answer=False,
                            )
                            self.quests.append(quest)
                            break
                        elif line.endswith(negative):
                            quest = Quest(
                                title=title,
                                desc=line,
                                correct_answer=True,
                            )
                            self.quests.append(quest)
                            false_desc = line.replace(negative, positive)
                            quest = Quest(
                                title=title,
                                desc=false_desc,
                                correct_answer=False,
                            )
                            self.quests.append(quest)
                            break
                        else:
                            pass
                    else:
                        raise ValueError((file, line))

    def get_quest(self) -> Iterable[Quest]:
        while True:
            if len(self.deck) == 0:
                for quest in self.quests:
                    point = random.random() * 2
                    desc_hash = self.hash_into_number(quest.desc)
                    if desc_hash in self.stat:
                        point += self.stat[desc_hash]
                    self.deck.append((quest, point))
                self.deck.sort(key=lambda tup: tup[1])
            t = self.deck.pop(0)
            yield t[0]

    def hash_into_number(self, src: str) -> int:
        result = hashlib.sha1(src.encode("utf-8"))
        return int(result.hexdigest(), 16)

    def run(self):
        self.load_questions()

        print(self.hash_into_number('123'))
        print(self.hash_into_number('345'))
        for quest in self.get_quest():
            print('{:=^60s}'.format(' %s ' % quest.title))
            print(self.hash_into_number(quest.desc))
            print(quest.desc)

            while True:
                raw_answer = input('>> ')
                if len(raw_answer) > 0:
                    break
            if raw_answer in ('1', ']'):
                print('>> 예')
                answer = True
            elif raw_answer in ('2', '['):
                answer = False
                print('>> 아니요')
            else:
                answer = None
                print(f'>> 기권({raw_answer})')

            desc_hash = self.hash_into_number(quest.desc)
            if desc_hash not in self.stat:
                self.stat[desc_hash] = 0

            if quest.correct_answer == answer:
                print('정답입니다.')
                self.stat[desc_hash] += 1
            elif answer is not None:
                print('오답입니다.')
                self.stat[desc_hash] -= 1
            else:
                print(f'기권하였습니다.')
                self.stat[desc_hash] -= 0.5
            self.save()


if __name__ == '__main__':
    MainProgram().run()
