"попытка сделать тетрис"
#import time
from abc import abstractmethod as ameth
import random
import numpy as np
import keyboard
from typing import Generator

SIZE = (8, 14)
EMPTY = "_"
SEP   = " "


# вынести (config () ?)
# ссылаются на это вместо магических чисел
 

Cord  = tuple[int, int]
Cords = set[Cord]

Fig   = tuple[str, Cords]
Figs  = set[Fig]

Mfig  = tuple[str, "Matrix"]
Mfigs = list[Mfig]


class TRError(Exception):
    __slots__ = "text"
    def __init__(self, text:str="неизестно"):
        self.text = text
    def __repr__(self):
        return self.text
class ColisError  (TRError): ...
class EndGameError(TRError): ...

class AbcMatrix:
    array: np.ndarray
    def __repr__(self):
        return repr(self.array)
    def __get_item__(self, cord:Cord):
        return self.array[*cord]
    def __call__(self) -> np.ndarray:
        return self.array
    def __getitem__(self, *args:int|Cord) -> np.ndarray:
        return (self.array.__getitem__(*args))
    def __setitem__(self, *args:int|Cord):
        return self.array.__setitem__(*args)
    def __len__(self):
        return len(self.array)


    def sum(self) -> int:
        return int(self.array.sum())
    def max(self):
        return self.array.max()

class Matrix(AbcMatrix):
    __slots__ = "array"
    def __init__(self, cords:set[Cord]|np.ndarray=set()):
        if isinstance(cords, np.ndarray):
            self.array = cords
        else:
            self.array = np.full((SIZE[0]+1, SIZE[1]+1), 0)
            for cord in cords:
                x, y = cord
                if   x < 1       or y < 1             : ...
                elif x > SIZE[0] or y > SIZE[1] : ...
                else: self.array[x, y] = 1
        
    def redo_y(self, y:int):
        ny:int
        for ny in range(y, len(self.array)):
            self.array[ny] = self.array[ny+1]

def vi(mfigs:Mfigs) -> str:
    text = ""

    yl, xl = SIZE[1], SIZE[0]+1
    yr, xr = range(yl, 0, -1), range(1, xl, 1)

    for y in yr:
        for x in xr:
            
            flag = False #определять был ли отрисован* элемент для текущей позиции (x, y)
            for mfig in mfigs:
                matrix = mfig[1]
                w     = mfig[0]

                #print(x, y)
                if matrix[x, y] == 1:
                    if not flag:
                        text += w
                        flag = True

            if not flag:
                text += EMPTY
            text += SEP 
        text += "\n"

    return text
def vi_null(text:str) -> str:
    null = f"\033[{text.count("\n")+2}A\033[O\n"
    return null + text
def vi_buf(text1:str, text2:str|None = None) -> str:
    if text1.count("\n") == 0:
        raise ValueError("ожидается строка с переносами (\\n) но полученна без них")

    texts = text1.split("\n")
    max_len = max(map(len, texts))

    if text2 == None:
        for i in range(len(texts)):
            cur_len = max_len - len(texts[i])
            texts[i] += cur_len*" " + f"  | {i+1}"
    else:
        buf = text2.split("\n")
        buf += (len(texts)-len(buf))*["", ]
        for i in range(len(texts)):
            cur_len = max_len - len(texts[i])
            texts[i] += cur_len*" " + f"  | {buf[i]}" 
    
    return "\n".join(texts)

def move_xy(col:Cords, x:int=0, y:int=0):
    return type(col)(map(lambda a: (a[0]+x, a[1]+y), col))

def sex(col1:Cords, col2:Cords) -> bool:
    """сравнение интерируеммых объектов"
    есть хотябы 1 совпадения True иначе False"""
    for i in col1:
        if i in col2:
            return True
    return False
def colis_SIZE(cords:Cords, SIZE:tuple[int, int]=SIZE) -> bool:
    """
    возращает True если фигура выходит из поля зрения
    иначе False
    """
    for cord in cords:
        x,   y  = cord[0] , cord[1]
        lx , ly = SIZE[0] , SIZE[1]
        if x < 1 or x > lx: return True
        if y < 1 or y > ly: return True
    return False
def colis_full(cords:Cords, colis:Cords=set(), SIZE:tuple[int, int]=SIZE) -> bool:
    if sex(cords, colis) or colis_SIZE(cords, SIZE):
        return True
    return False


class AbcTab:
    w:      str
    def __iter__(self):
        return iter(self.get_cords())
    def __len__(self):
        return len(self.get_cords())
    def __str__(self):
        return f"объект *AbcTab {self.get_fig()}"
    
    @ameth
    def get_cords(self) -> Cords: ...
    @ameth
    def get_fig(self) -> Fig: ...

    def get_matrix(self) -> Matrix:
        cords = self.get_cords()
        return Matrix(cords)
    def get_mfig(self) -> Mfig:
        return (self.w, self.get_matrix())
    
    def colis_size(self) -> bool:
        cords  = self.get_cords()
        matrix = self.get_matrix()
        return len(cords) != matrix.sum()
    def colis_matrix(self, colis:Matrix) -> bool:
        matrix:np.ndarray = self.get_matrix()() + colis
        return matrix.max() > 1
    def colis_full(self, colis:Matrix)   -> bool:
        if self.colis_matrix(colis): return True
        if self.colis_size():        return True
        return False
    
    def vi(self) -> str:
        mfigs:Mfigs = [self.get_mfig()]
        return vi(mfigs)

class Mtab(AbcTab):
    point:      Cord
    rotation:   int
    pos:    dict[int, Cords]
    ALL_POS = {
        "long": {
            0: {(0, 0), (1,  0), (2,  0), (3,  0)},
            1: {(0, 0), (0, -1), (0, -2), (0, -3)},
        },
        "cub": {
            0: {(0, -1), (0, 0), (1, -1), (1, 0)}
        },
        "g_left": {
            0: {(1,  0), (0,  0), (0, -1), (0, -2)},
            1: {(0,  0), (1,  0), (2,  0), (2, -1)},
            2: {(2,  0), (2, -1), (2, -2), (1, -2)},
            3: {(0, -1), (0, -2), (1, -2), (2, -2)},
        },
        "g_right": {
            0: {(1,  0), (2,  0), (2, -1), (2, -2)},
            1: {(2, -1), (2, -2), (1, -2), (0, -2)},
            2: {(1, -2), (0, -2), (0, -1), (0,  0)},
            3: {(0, -1), (0,  0), (1,  0), (2,  0)},
        },
        "te":{
            0: {(0, -1), (1, -1), (2, -1), (1,  0)},
            1: {(1,  0), (1, -1), (1, -2), (2, -1)},
            2: {(0, -1), (1, -1), (2, -1), (1, -2)},
            3: {(1,  0), (1, -1), (1, -2), (0, -1)}
        },
        "zeta":{
            0: {(0,  0), (1,  0), (1, -1), (2, -1)},
            1: {(2,  0), (2, -1), (1, -1), (1, -2)},
            2: {(0, -1), (1, -1), (1, -2), (2, -2)},
            3: {(0, -2), (0, -1), (1, -1), (1,  0)},
        },
        "seta":{
            0: {(0, -1), (1, -1), (1,  0), (2,  0)},
            1: {(1,  0), (1, -1), (2, -1), (2, -2)},
            2: {(0, -2), (1, -2), (1, -1), (2, -1)},
            3: {(0,  0), (0, -1), (1, -1), (1, -2)},
        },
        
    }   

    def __init__(self, pos:dict[int, Cords]|None=None, w:str="M"):
        self.w = w
        self.point = (3, 14)
        self.rotation = 0
        if pos == None: self.pos = random.choice(list(self.ALL_POS.values()))
        else:           self.pos= pos
    def __str__(self):
        return f"объект Mtab {self.get_fig()}"
    
    def get_cords(self) -> Cords:
        cords:Cords = set()
        for lcord in self.pos[self.rotation]:
            cord:Cord = (lcord[0] + self.point[0], + lcord[1] + self.point[1])
            cords.add(cord)
        return cords
    def get_fig(self)   -> Fig:
        return (self.w, self.get_cords())

    def move(self, x:int=0, y:int=0, colis:Cords=set()) -> None:
        if x == 0 and y == 0: return

        px, py = self.point

        self.point = (px + x, py +y)
        cords = self.get_cords()

        if colis_full(cords, colis):
            self.point = (px, py)
            raise ColisError
    def mmove(self, x:int=0, y:int=0, colis:Matrix=Matrix()) -> None:
        if x == 0 and y == 0: return

        px, py = self.point
        self.point = (px + x, py +y)

        if self.colis_full(colis):

            self.point = (px, py)
            raise ColisError

    def rotate(self, to:int, colis:Cords):
        self.rotation = (self.rotation + to) % len(self.pos)
        
        if colis_full(self.get_cords(), colis):
            self.rotation = (self.rotation - to) % len(self.pos)
            raise ColisError

    @classmethod
    def random(cls, w:str="M") -> "Mtab":
        rpos = random.choice(list(cls.ALL_POS.values()))
        return Mtab(rpos, w)


class Stab(AbcTab):
    cords: Cords
    def __init__(self, cords:Cords, w:str="S"):
        self.w      = w
        self.cords  = cords
    def __hash__(self) -> int:
        return hash((self.w, tuple(self.cords)))
    def __eq__(self, value:object) -> bool:
        if type(value) == type(self):
            if self.get_fig == value.get_fig():
                return True
        return False

    def get_cords(self) -> Cords:
        return self.cords
    def get_fig(self) -> Fig:
        return (self.w, self.cords)

    def remove_y(self, y:int):
        ncords:set[Cord] = set()

        for cord in self.cords:
            if y != cord[1]:
                ncords.add(cord)

        self.cords = ncords 
    def redo(self, y:int):
        ncords:set[Cord] = set()
        for cord in self.cords:
            if y != cord[1]:
                if y < cord[1]:
                    ncords.add((cord[0], cord[1]-1))
                else:
                    ncords.add(cord)
        self.cords = ncords         

class Stabs():
    stabs: set[Stab]
    lines: int
    figs : int
    cn   : int
    SCORE_LIST  = [0, 100, 300, 700, 1500]

    def __init__(self, stabs:set[Stab]=set()) -> None:
        self.stabs   =  stabs
        self.cnlines = 0
        self.cnfigs  = 0
        self.score   = 0
    def __len__(self):
        return len(self.stabs)
    def __iter__(self):
        return iter(self.stabs)
    def add(self, stab:Stab) -> None:
        self.stabs.add(stab)
    
    def get_cords(self)     -> Generator[Cord]:
        for stab in self.stabs:
            for cord in stab:
                yield cord
    def get_mfigs(self)     -> Generator[Mfig]:
        for stab in self.stabs:
            yield(stab.get_mfig())
    def get_matrix(self)    -> Matrix        :
        m0:np.ndarray = np.zeros_like(list(self.stabs)[0].get_matrix())
        for stab in self.stabs:
            m0 += stab.get_matrix()
        return Matrix(m0)

    def redu(self, y:int)   -> None:
        for stab in self.stabs:
            stab.redo(y)
            if not stab:
                self.stabs
                self.cnfigs += 1
        self.cnlines += y    
    def clear_lines(self)   -> None:
        matrix   : Matrix = self.get_matrix()
        matrix_y : np.ndarray
        redu_cn  : int = 0
        for y in range(SIZE[1]-1, -1, -1):
            matrix_y = matrix[:, y] # pyright: ignore[reportArgumentType]
            if matrix.max() > 1:
                raise EndGameError
            elif matrix_y.sum() == SIZE[0] and matrix_y.min() == 0:
                self.redu(y)
                redu_cn += 1
        self.score += self.SCORE_LIST[redu_cn]
            
 
    def get_info(self) -> str:
        text:list[str] = []
        text.append(f"очищенно линий: {self.cnlines}")
        text.append(f"очищенно фигур: {self.cnfigs}")
        text.append(f"счёт: {self.score}")
        return "\n".join(text)



    
class Table():
    __slots__ = {"mtab", "stabs"}
    mtab : Mtab
    stabs: Stabs
    hook : object

    def __init__(self): 
        self.stabs = Stabs()
        self.mtab  = Mtab.random()
    def new_mtab(self): 
        cords = self.mtab.get_cords()
        stab  = Stab(cords)
        self.stabs.add(stab)

        self.mtab = Mtab.random()
        self.stabs.clear_lines()

    def get_mfigs(self) -> Mfigs:
        mfigs: list[Mfig] = list(self.stabs.get_mfigs())
        mfigs.append(self.mtab.get_mfig())
        return mfigs
        

    def move(self, x:int=0, y:int=0):
        try:
            colis = set(self.stabs.get_cords())
            self.mtab.move(x, y, colis)
        except ColisError:
            self.new_mtab()
    def rotate(self, r:int):
        try:
            colis = set(self.stabs.get_cords())
            self.mtab.rotate(r, colis)
        except ColisError:
            self.new_mtab()
    def over_down(self):
        try:
            x =  0
            y = -1
            while True:
                colis = set(self.stabs.get_cords())
                self.mtab.move(x, y, colis)
        except ColisError:
            self.new_mtab()

    def get_info(self) -> str:
        info = self.stabs.get_info()
        return info

    def vi_start(self):
        mfigs = self.get_mfigs()
        buf = self.get_info()
        text = vi_buf(vi(mfigs), buf)
        print(text)
    def vi(self):
        mfigs = self.get_mfigs()
        buf = self.get_info()
        text = vi_null(vi_buf(vi(mfigs), buf))
        print(text)

    def on_press(self, press:keyboard._keyboard_event.KeyboardEvent): # pyright: ignore[reportPrivateUsage]
        if press.name == None: return
        n:str = press.name
        do_list = {
            "a": self.l,
            "left":self.l, 

            "d": self.r,
            "right":self.r, 

            "s": self.d,
            "down": self.d, 

            "w":self.over_down,
            "up":self.over_down,

            "q": self.q,
            "home": self.q,

            "e": self.e,
            "page up": self.e,

            "k": self.k
        }


        if n in do_list:
            try:
                do_list[n]()
                self.vi()                
            except EndGameError:
                self.vi()
                return
                self.vi()
                print("ю сакю (esc что бы выйти)")
                self.on_press = lambda *a, **ka: None # pyright: ignore[reportUnknownLambdaType]
            

    def d(self):
        return self.move(y=-1)
    def r(self):
        return self.move(x= 1)  
    def l(self):
        return self.move(x=-1)  
        
    def e(self):
        self.rotate( 1)
    def q(self):
        self.rotate(-1)
   
    def k(self):
        self.mtab = Mtab.random()


def main():
    table = Table()
    hook = keyboard.on_press(table.on_press)
    print ("""
    тетрис запущен!
    asd для упраления
    esc для закрытия
    """)
    table.vi_start()
    keyboard.wait("esc")
    keyboard.unhook(hook)
def teste():
    table = Table()
    table.vi_start()
    for _ in range(3):
        table.over_down()
        table.vi()
        #print(table.get_stabs_matrix2())
        

if __name__ == "__main__":
    main();  exit()
    teste(); exit()