from random import randrange as rnd, choice
from tkinter import *
# from tkinter import messagebox
# from tkinter import filedialog
import math
import time

WIDTH = 800
HEIGHT = 600
COLORS = ['red', 'green', 'blue', 'brown']
SHOTS = 0
SCORES = 0

# Создание новой игры
def newgame():
    pass


# Загрузка сохраненной игры
def loadgame():
    pass


# Сохранение игры
def savegame():
    pass


class ball():
    def __init__(self, balls, x=20, y=HEIGHT - 150, r=8):
        self.x = x
        self.y = y
        self.r = r
        self.color = choice(COLORS)
        self.points = 3
        self.id = canvas.create_oval(self.x - self.r, self.y - self.r, self.x + self.r, self.y + self.r,
                                     fill=self.color)
        # self.id_points = canv.create_text(self.x,self.y,text = self.points)
        self.live = 200  # время жизни снаряда после остановки
        self.nature = 1  # признак уменьшения радиуса, да =0 или нет =1
        self.balls = balls
        self.bum_on = 0  # признак детонации
        self.bum_time = 100  # время до детонации
        self.surprise = 0  # признак сюрприза(!!!)
        self.surprise_time = 0  # время до детонации(!!!)

    def paint(self):
        canvas.coords(self.id, self.x - self.r, self.y - self.r, self.x + self.r, self.y + self.r)
        # canv.coords(self.id_points,self.x,self.y)
        # canv.itemconfig(self.id_points,text = self.points)

    def move(self):
        if self.y <= 500:
            self.vy += 0.07
            self.y += self.vy
            self.x += self.vx
            self.vx *= 0.999
            #v = (self.vx ** 2 + self.vy ** 2) ** 0.5    #self
            #an = math.atan(self.vy / self.vx)    #self
            self.paint()
        else:
            if self.vx ** 2 + self.vy ** 2 > 10:
                self.vy = -self.vy * 0.7
                self.vx = self.vx * 0.7
                self.y = 499
            if self.live < 0:
                self.kill()
            else:
                self.live -= 1
        if self.x > 780:
            self.vx = - self.vx / 2 # возможно деление на 0, сделать проверку
            self.x = 779    # без этого залипает к правой стороне
        if self.bum_on and self.nature:
            self.bum_time -= 1
            if self.bum_time <= 0:
                self.bum()
        if not self.nature:
            self.live -= 0.1
            if self.r > 0.1:
                self.r -= 0.1
            else:
                self.kill()
            self.vy += 0.2
            if self.live < 0:
                self.kill()
        if self.surprise:
            self.surprise_time += 1
            if self.surprise_time > 13:
                self.surprise_time = 0
                self.detonation()

    def hittest(self, ob):
        if abs(ob.x - self.x) <= (self.r + ob.r) and abs(ob.y - self.y) <= (self.r + ob.r):
            return True
        else:
            return False

    def rebound(self, w):  # Рикошет от дальней стенки и пола
        v = (self.vx ** 2 + self.vy ** 2) ** 0.5    #self
        an = math.atan(self.vy / self.vx)    #self

        if self.x == w.x:
            self.x += 1

        if w.x - (self.x + self.vx):
            an_rad = math.atan((w.y - (self.y + self.vy)) / (w.x - (self.x + self.vx)))
            an_res = an_rad - (an - an_rad)    #self

            vx2 = 0.8 * v * math.cos(an_res)    #self
            vy2 = 0.8 * v * math.sin(an_res)    #self
            if an > 0 and self.vx < 0 and self.vy < 0 or an < 0 and self.vx < 0:    #self
                vx2 = -vx2
                vy2 = -vy2
            self.vx = -vx2
            self.vy = -vy2
            self.move()
            self.points += 1

    def kill(self):
        canvas.delete(self.id)
        # canv.delete(self.id_points)
        try:
            self.balls.pop(self.balls.index(self))
        except:
            pass

    def detonation(self):
        n = 5  # количество малых бомбочек(осколков)
        for i in range(1, n + 1):
            new_ball = ball(self.balls, r=5)
            v = 5 + rnd(5)
            an = i * 2 * math.pi / n + rnd(-2, 3) / 7
            new_ball.vx = v * math.cos(an)
            new_ball.vy = v * math.sin(an)
            new_ball.x = self.x + new_ball.vx * 3
            new_ball.y = self.y + new_ball.vy * 3
            new_ball.nature = 0
            new_ball.points = 1
            new_ball.live = rnd(10) + 30
            new_ball.color = choice(COLORS)
            self.balls += [new_ball]

    def bum(self):
        self.detonation()
        self.kill()


class gun():
    def __init__(self):
        self.firePowerUp = 0        # признак увеличения длинны ствола пушки
        self.firePower = 10         # длинна ствола пушки
        self.noCancelLevel = 1      # хз, похоже признак наличия не уничтоженных мишеней
        self.an = 1                 #
        self.points = 0             # количество выстрелов
        self.id = canvas.create_line(20, 450, 50, 420, width=7, smooth=1)
        self.id_points = canvas.create_text(30, 30, text=self.points, font='28')

        self.balls = []
        self.bullet = 0
        self.targets = []
        self.walls = []

    def fire_start(self, event):
        global SHOTS
        self.firePowerUp = 1
        SHOTS += 1

    def stop(self):
        self.firePowerUp = 0
        self.noCancelLevel = 0

    def fire_end(self, event):
        self.bullet += 1
        new_ball = ball(self.balls, r=8)
        new_ball.r += 5
        self.an = math.atan((event.y - new_ball.y) / (event.x - new_ball.x))
        new_ball.vx = self.firePower * math.cos(self.an) / 7
        new_ball.vy = self.firePower * math.sin(self.an) / 7
        if not rnd(12):
            new_ball.surprise = 1
        self.balls += [new_ball]
        self.firePowerUp = 0
        self.firePower = 35

    def targetting(self, event=None):
        if event:
            self.an = math.atan((event.y - 450) / (event.x - 20))
        if self.firePowerUp:
            canvas.itemconfig(self.id, fill='orange')
        else:
            canvas.itemconfig(self.id, fill='black')
        canvas.coords(self.id, 20, 450, 20 + max(self.firePower, 20) * math.cos(self.an), 450
                      + max(self.firePower, 20) * math.sin(self.an))

    def power_up(self):
        if self.firePowerUp:
            if self.firePower < 100:
                self.firePower += 1
            canvas.itemconfig(self.id, fill='orange')
        else:
            canvas.itemconfig(self.id, fill='black')

    def bum(self, event):
        for b in self.balls[::-1]:
            if b.nature:
                b.bum()
                break


class target():
    def __init__(self, targets):
        self.points = 1
        x = self.x = rnd(600, 780)  # область для мишеней
        y = self.y = rnd(300, 500)  # область для мишеней
        r = self.r = rnd(10, 40)
        self.live = 5 + rnd(5)      # жизни мишени
        self.change_color = 0       # счетчик смены цвета
        self.color = COLORS[0]      # 'red'
        self.id = canvas.create_oval(x - r, y - r, x + r, y + r, fill=self.color)
        self.id_live = canvas.create_text(x, y, text=self.live)     # выводим жизни мишени
        self.targets = targets

    def hit(self, points=1):
        self.live -= points     # уменьшаем жизни мишени на величину points при попадании
        canvas.itemconfig(self.id_live, text=self.live)     # и выводим их
        canvas.itemconfig(self.id, fill='orange')   # перекрашиваем в оранжевый при попадании
        self.change_color = 10                      # счетчик для изменения цвета к исходному
        # Убиваем если кончились жизни мишени
        if self.live < 1:
            self.kill()

    def kill(self):
        self.targets.pop(self.targets.index(self))
        canvas.delete(self.id)
        canvas.delete(self.id_live)


root = Tk()
root.title('Игра ПУШКА')
root.geometry(str(WIDTH) + 'x' + str(HEIGHT))  # ('800x600+600+100')

# создание меню
mainmenu = Menu(root)
root.config(menu=mainmenu)
filemenu = Menu(mainmenu, tearoff=0)
filemenu.add_command(label="Новая", command=newgame)
filemenu.add_command(label="Загрузить...", command=loadgame)
filemenu.add_command(label="Сохранить...", command=savegame)
filemenu.add_command(label="Выход", command=sys.exit)
helpmenu = Menu(mainmenu, tearoff=0)
helpmenu.add_command(label="О программе")

mainmenu.add_cascade(label="Файл", menu=filemenu)
mainmenu.add_cascade(label="Справка", menu=helpmenu)

# Фрейм с выводом результатов
fr_top = Frame()
fr_top.pack(side=TOP, fill=X)
label_shot = Label(fr_top, text='Выстрелов: ', font=("Comic Sans MS", 20, "bold")).pack(side=LEFT)
lbl_shot = Label(fr_top, text=SHOTS, fg="orange", font=("Comic Sans MS", 24), justify=RIGHT).pack(side=LEFT)
lbl_score = Label(fr_top, text='0', fg="green", font=("Comic Sans MS", 24), justify=RIGHT).pack(side=RIGHT)
label_score = Label(fr_top, text='Попаданий: ', font=("Comic Sans MS", 20, "bold")).pack(side=RIGHT)

# Создаем холст
canvas = Canvas(root, bg='white')
canvas.pack(expand=1, fill=BOTH)


# Основная обработка логики игры

myGun = gun()

while 1:
    balls = myGun.balls
    targets = myGun.targets
    walls = myGun.walls
    myGun.noCancelLevel = 1
    for z in range(rnd(3, 7)):
        targets += [target(targets)]

    for z in range(rnd(1, 8)):
        walls += [target(walls)]
        walls[-1].x = rnd(200, 600)
        walls[-1].y = rnd(100, 400)
        walls[-1].r = rnd(20, 50)
        canvas.delete(walls[-1].id_live)
        canvas.itemconfig(walls[-1].id, fill='gray', width=0)
        canvas.coords(walls[-1].id, walls[-1].x - walls[-1].r, walls[-1].y - walls[-1].r, walls[-1].x + walls[-1].r,
                      walls[-1].y + walls[-1].r)

    canvas.bind('<Button-1>', myGun.fire_start)
    canvas.bind('<Button-3>', myGun.bum)
    canvas.bind('<ButtonRelease-1>', myGun.fire_end)
    canvas.bind('<Motion>', myGun.targetting)

    result = canvas.create_text(400, 300, text='', font="28")
    z = 0.03
    while targets or balls:
        for b in balls:
            b.move()
            for w in walls:
                if b.hittest(w):
                    b.rebound(w)

            for b_test in balls:
                if b != b_test and b.hittest(b_test):
                    if b.nature:
                        b_test.rebound(b)
                        if b_test.nature:
                            b.rebound(b_test)
                            b_test.bum()

            for t in targets:
                if b.hittest(t):
                    b.kill()
                    t.hit(b.points)
                    myGun.points += 1
                    canvas.itemconfig(myGun.id_points, text=myGun.points)

        if not targets and myGun.noCancelLevel:
            canvas.bind('<Button-1>', '')
            canvas.bind('<ButtonRelease-1>', '')
            myGun.stop()
            canvas.itemconfig(result, text='Вы уничтожили все цели за ' + str(myGun.bullet) + ' выстрелов')
            for b in balls:
                b.bum_time = 20
                b.bum_on = 1

        # Похоже на изменение цвета мишени к исходному
        for t in targets:
            if t.change_color <= 0:
                canvas.itemconfig(t.id, fill=t.color)
            else:
                t.change_color -= 1

        canvas.update()

        t = 0.008 - (len(balls) - 5) * 0.0001
        t = max(t, 0)
        time.sleep(t)
        myGun.targetting()
        myGun.power_up()
    canvas.update()
    time.sleep(0.1)
    canvas.delete(result)

root.mainloop()
