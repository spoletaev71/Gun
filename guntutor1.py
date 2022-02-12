from tkinter import *
from random import *

screen_width = 400
screen_height = 400
r_min = 20
r_max = 20
dt = 0.1  # физический шаг времени между кадрами обсчёта
V_max = 50
fps = 20  # количество кадров в секунду
sleep_time = round(1000/fps)
target_initial_number = 5
target_max_number = 10
default_target_born_time = 5  # секунд
scores_format = 'столкновений: %d'


class MainWindow:
    def __init__(self, root):
        global canvas
        canvas = Canvas(root)
        canvas["width"] = screen_width
        canvas["height"] = screen_height
        canvas.pack()

        self.gun = Gun()
        self.shells = []
        self.targets = [Target.generate_random() for i in range(target_initial_number)]
        self.scores = 0
        self.scores_text = canvas.create_text(screen_width - 50, 10,
                                              text=scores_format%self.scores)
        self.target_born_time = default_target_born_time
        self.game_cycle()  # запуск игрового цикла
        canvas.bind("<Button-1>", self.mouse_click)
        canvas.bind("<Motion>", self.mouse_motion)

    def mouse_motion(self, event):
        self.gun.aim(event.x, event.y)

    def mouse_click(self, event):
        """ Проверяем, далеко ли шарик, и, если в него попали, то "лопаем" его,
            создаём новый шарик, а за старый начисляем очки.
        """
        shell = self.gun.shoot(event.x, event.y)
        self.shells.append(shell)

    def game_cycle(self, *ignore):
        canvas.after(sleep_time, self.game_cycle)  # перезапуск цикла

        # смещаем цели и снаряды
        for target in self.targets:
            target.move()
        for shell in self.shells:
            shell.move()

        # для каждого атома проверяем столкновение со всеми остальными (кроме уже проверенных ранее)
        for i in range(len(self.targets)):
            for k in range(i+1, len(self.targets)):
                target1 = self.targets[i]
                target2 = self.targets[k]
                if check_collision(target1, target2):
                    self.scores += 1
                    canvas.itemconfig(self.scores_text, text=scores_format%self.scores)
                    # Упругое столкновение
                    collide(target1, target2)

        # порождаем новую цель, если настало для этого время:
        if len(self.targets) < target_max_number:
            self.target_born_time -= sleep_time/1000
            if self.target_born_time <= 0:
                self.targets.append(Target.generate_random())
                self.target_born_time = default_target_born_time

        # для каждой цели проверяем столкновение со снарядом
        for shell in self.shells:
            killed_target = None
            for i, target in enumerate(self.targets):
                if target.check_contact(shell.x, shell.y):
                    self.scores += target.scores
                    canvas.itemconfig(self.scores_text, text=scores_format%self.scores)
                    target.destroy()
                    killed_target = i
                    break
            if killed_target is not None:
                self.targets.pop(killed_target)


class Ball:
    def __init__(self, x, y, r, Vx, Vy, color):
        self.x, self.y, self.r = x, y, r
        self.Vx, self.Vy = Vx, Vy
        self.avatar = canvas.create_oval(x-r, y-r, x+r, y+r, fill=color)

    def check_contact(self, x, y):
        l = ((self.x - x)**2 + (self.y - y)**2)**0.5
        return l <= self.r

    def destroy(self):
        canvas.delete(self.avatar)

    def move(self):
        """ сдвинуть шарик на его скорость """
        ax = 0
        ay = 0
        self.x += self.Vx*dt  # Добавить поправку?!
        self.y += self.Vy*dt
        self.Vx += ax*dt
        self.Vy += ay*dt
        # отражения слева, справа, снизу, сверху
        if self.x - self.r <= 0:
            self.Vx = -self.Vx
            self.x = self.r+1
        if self.x + self.r >= screen_width:
            self.Vx = -self.Vx
            self.x = screen_width - self.r - 1
        if self.y + self.r >= screen_height:
            self.Vy = -self.Vy
            self.y = screen_height - self.r - 1
        if self.y - self.r <= 0:
            self.Vy = -self.Vy
            self.y = self.r+1

        canvas.coords(self.avatar, self.x-self.r, self.y-self.r,
                      self.x+self.r, self.y+self.r)


class Atom(Ball):
    def __init__(self, x, y, r, Vx, Vy):
        super().__init__(x, y, r, Vx, Vy, "red")

    @classmethod
    def generate_random(cls):
        r = randint(r_min, r_max)
        x = randint(r, screen_width-r-1)
        y = randint(r, screen_height-r-1)
        # генерация случайной скорости
        Vx = randint(-V_max, +V_max)
        Vy = randint(-V_max, +V_max)
        return Atom(x, y, r, Vx, Vy)


def check_collision(atom1, atom2):
    l = ((atom1.x - atom2.x)**2 + (atom1.y - atom2.y)**2)**0.5
    return l <= atom1.r + atom2.r


def collide(atom1, atom2):
    lx, ly = atom2.x - atom1.x, atom2.y - atom1.y
    l = (lx**2 + ly**2)**0.5
    nx, ny = lx/l, ly/l
    # выделение компонент скорости атома 1:
    v1_parallel = atom1.Vx*nx + atom1.Vy*ny
    v1_parallel_x = v1_parallel*nx
    v1_parallel_y = v1_parallel*ny
    v1_perpendicular_x = atom1.Vx - v1_parallel_x
    v1_perpendicular_y = atom1.Vy - v1_parallel_y
    # выделение компонент скорости атома 2:
    v2_parallel = atom2.Vx*nx + atom2.Vy*ny
    v2_parallel_x = v2_parallel*nx
    v2_parallel_y = v2_parallel*ny
    v2_perpendicular_x = atom2.Vx - v2_parallel_x
    v2_perpendicular_y = atom2.Vy - v2_parallel_y
    # перпендикулярная компонента скорости не меняется, а параллельными атомы обмениваются
    atom1.Vx = v1_perpendicular_x + v2_parallel_x
    atom1.Vy = v1_perpendicular_y + v2_parallel_y
    atom2.Vx = v2_perpendicular_x + v1_parallel_x
    atom2.Vy = v2_perpendicular_y + v1_parallel_y


class Shell(Ball):
    def __init__(self, x, y, r, Vx, Vy):
        super().__init__(x, y, r, Vx, Vy, "red")


class Target(Atom):
    def __init__(self, x, y, r, Vx=0, Vy=0):
        super().__init__(x, y, r, Vx, Vy)
        self.scores = 10 + r_max - r

    @classmethod
    def generate_random(cls):
        r = randint(r_min, r_max)
        x = randint(r, screen_width-r-1)
        y = randint(r, screen_height-r-1)
        # генерация случайной скорости
        Vx = randint(-V_max, +V_max)
        Vy = randint(-V_max, +V_max)
        return Target(x, y, r, Vx, Vy)


class Gun:
    max_cannon_length = 40
    shell_radius = 5

    def __init__(self):

        self.x, self.y = [0, screen_height]
        self.lx = 20
        self.ly = 0
        self.line = canvas.create_line(self.x, self.y, self.x+self.lx, self.y+self.ly,
                                            width=5, fill='red')

    def aim(self, x, y):
        self.lx = (x - self.x)
        self.ly = (y - self.y)
        l = (self.lx**2 + self.ly**2)**0.5
        self.lx = Gun.max_cannon_length*self.lx/l
        self.ly = Gun.max_cannon_length*self.ly/l

        canvas.coords(self.line, self.x, self.y, self.x+self.lx, self.y+self.ly,)

    def shoot(self, x, y):
        self.aim(x, y)
        Vx = 1*self.lx
        Vy = 1*self.ly
        return Shell(self.x+self.lx, self.y+self.ly, self.shell_radius, Vx, Vy)



root_window = Tk()
window = MainWindow(root_window)
root_window.mainloop()
