import copy
import hit_check
import json
import math
import os
import tkinter as tk
from abc import ABC, abstractmethod
from PIL import ImageTk, Image
from random import randrange as rnd, choice
from tkinter import filedialog
from tkinter import messagebox


DT = 30  # FPS
VICTORY_MSG_TIME = 4000  # Время задержки между циклами игры
# GAME_OVER_MSG_TIME = 60000  # Время задержки по окончании игры
BACKGROUND = 'ScreenBG01.jpg'  # Картинка для фона на холст


def pass_event(event):
    """Заглушка."""
    pass


def about():
    """Вывод данных по пункту меню `О программе`."""
    messagebox.showinfo("О программе", "Игра \"Пушка\" создана на основе заготовки, написанной преподавателем МФТИ, "
                                       "как практика по обучению программирования на языке Python v3.\n\n"
                                       "Автор доработки: Полетаев Сергей")


def read_form_size():
    """Считывает размеры формы и возвращает в виде списка с размерами по `х` и `у`."""
    sz = app.geometry()
    sz = sz.split('+')
    sz = sz[0].split('x')
    return [int(sz[0]), int(sz[1])]


def set_window_size(size):
    """Изменяет глобальную переменную(список) `window_size`.
    Принимает в качестве параметра `size` набор данных в виде списка с размерами `x` и `y`.
    """
    global window_size
    window_size = size[:]


class Agent(ABC):
    """Абстрактный класс с методами, на основе которого создаются все изменяемые объекты игры.
    Этот класс-обертка частично реализует изменения состояния игры `job` и обновление элементов на холсте `canvas`
    в зависимости от `DT`.
    """
    def __init__(self):
        self.job = None
        self.canvas = None

    @abstractmethod
    def start(self):
        self.job = self.canvas.after(DT, self.update)

    @abstractmethod
    def play(self):
        if self.job == 'pause':
            self.job = self.canvas.after(DT, self.update)

    @abstractmethod
    def stop(self):
        if self.job is not None:
            self.canvas.after_cancel(self.job)
            self.job = None

    @abstractmethod
    def pause(self):
        if self.job is not None and self.job != 'pause':
            self.canvas.after_cancel(self.job)
            self.job = 'pause'

    @abstractmethod
    def update(self):
        pass


class Ball(Agent):
    """Класс для создания снарядов на холсте `canvas`. Создается и наследует методы от абстрактного класса `Agent(ABC)`.
    """
    def __init__(self, canvas, x, y, vx, vy, color=None, live=None, job_init=None):
        super().__init__()
        self.job = job_init

        self.canvas = canvas
        self.x = x  # координаты
        self.y = y
        self.r = 10  # радиус снаряда
        self.vx = vx  # ускорение по осям
        self.vy = vy
        self.color = choice(['blue', 'green', 'red', 'brown']) if color is None else color  # делаем их разноцветными
        # Создаем сам снаряд
        self.id = self.canvas.create_oval(
            self.x - self.r,
            self.y - self.r,
            self.x + self.r,
            self.y + self.r,
            fill=self.color
        )
        # Время жизни снаряда
        self.live = 250 if live is None else live
        self.canvas.bullets[self.id] = self
        # Используется для определения номера выстрела, которым уничтожена цель.
        self.bullet_number = self.canvas.get_bullet_number()

    def start(self):
        super().start()

    def play(self):
        super().play()

    def stop(self):
        super().stop()

    def pause(self):
        super().pause()

    def update(self):
        """Движение снарядов с гравитацией."""
        if self.y <= window_size[1] - 55:  # проверка на достижение нижней стенки
            self.vy += 0.098  # коэффициент - типа ускорение свободного падения
            self.y += self.vy * 0.65
            self.x += self.vx * 0.65
            self.vx *= 0.997  # типа коэффициент сопротивления воздуха
        elif self.vx ** 2 + self.vy ** 2 > 4:  # проверка не пора ли прекратить отскок от нижней стенки
            self.vy *= -0.65
            self.vx *= 0.65
            self.y = window_size[1] - 61

        if self.x > window_size[0] - 20:  # проверка не пора ли отскочить от правой стенки
            self.vx *= -0.65
            self.x = window_size[0] - 21  # иначе залипнет у стенки
        self.set_coords()

        decors_hit = self.hit_decors()
        if decors_hit:  # попал в дерево
            self.vx = - self.vx * 0.65
            self.x = self.x + decors_hit

        targets_hit = self.hit_targets()
        if targets_hit:  # попал в мишень
            self.destroy()
        else:
            if self.vx ** 2 + self.vy ** 2 <= 4:  # когда почти перестает двигаться отнимаем жизни у снаряда
                self.live -= 1
            if self.live > 0:
                self.job = self.canvas.after(DT, self.update)
            else:
                self.destroy()

    def destroy(self):
        self.stop()
        self.canvas.delete(self.id)
        del self.canvas.bullets[self.id]

    def set_coords(self):
        self.canvas.coords(
            self.id,
            self.x - self.r,
            self.y - self.r,
            self.x + self.r,
            self.y + self.r
        )

    def hit_decors(self):
        for d in list(self.canvas.decors.values()):
            # проверка попадания в дерево слева
            if self.x - self.r - self.vx < d.x and self.y > d.y:
                if self.x + self.r + self.vx > d.x and self.y > d.y:
                    return -1
            # проверка попадания в дерево справа
            elif self.x + self.r + self.vx > d.x and self.y > d.y:
                if self.x - self.r + self.vx < d.x and self.y > d.y:
                    return 1

    def hit_targets(self):
        ids_hit = []
        for t_id, t in list(self.canvas.targets.items()):
            # проверка попадания в цель
            if hit_check.is_hit(
                    (self.x, self.y),
                    self.r,
                    (-self.vx, -self.vy),
                    (t.x, t.y),
                    t.r
            ):
                self.canvas.report_hit(self, t)
                ids_hit.append(t_id)
                t.destroy()
        return ids_hit

    def get_state(self):
        state = {
            "x": self.x,
            "y": self.y,
            "vx": self.vx,
            "vy": self.vy,
            "color": self.color,
            "live": self.live,
            "job": self.job is not None
        }
        return state


class Gun(Agent):
    """Класс для отрисовки фоновой картинки и пушки на холсте `canvas`.
    Создается и наследует методы от абстрактного класса `Agent(ABC)`.
    """
    def __init__(self, canvas, gun_coords=None, job_init=None):
        super().__init__()

        self.job = job_init
        self.gun_velocity = 2  # шаг движения пушки по вертикали
        self.gun_power_gain = 1  # приращение мощности пушки
        # Мин мощность пушки, зависит от размеров игрового поля
        self.min_gun_power = 2 * round(math.sqrt(window_size[0]**2 + window_size[1]**2) // 400)
        # Макс мощность пушки, зависит от размеров игрового поля
        self.max_gun_power = 10 * round(math.sqrt(window_size[0]**2 + window_size[1]**2) // 400)
        self.zero_power_length = 10

        self.gun_coords = list(gun_coords) if gun_coords else [20, window_size[1] - 100]
        self.vy = 0
        self.mouse_coords = [None, None]
        self.fire_power = 5
        self.fire_on = 0
        self.an = 1

        self.canvas = canvas
        self.img = Image.open(BACKGROUND)
        self.img = self.img.resize((window_size[0], window_size[1]), Image.LANCZOS)
        self.image = ImageTk.PhotoImage(self.img)
        self.id1 = self.canvas.create_image(window_size[0] >> 1, window_size[1] >> 1, image=self.image)

        self.id = self.canvas.create_line(*self.gun_coords, *self.get_gunpoint(), width=7)
        self.canvas.gun[self.id, self.id1] = self

    def start(self):
        self.bind_all()
        super().start()

    def play(self):
        if self.job == 'pause':
            self.bind_all()
        super().play()

    def stop(self):
        super().stop()
        self.unbind_all()
        self.vy = 0
        self.fire_power = self.min_gun_power
        self.fire_on = 0
        self.mouse_coords = [None, None]

    def pause(self):
        super().pause()
        self.unbind_all()
        self.mouse_coords = [None, None]

    def update(self):
        # Ограничение движения пушки по вертикали
        if self.gun_coords[1] < self.zero_power_length:
            self.stop_movement(None)
            self.gun_coords[1] = self.zero_power_length
        elif self.gun_coords[1] > window_size[1] - 100:
            self.stop_movement(None)
            self.gun_coords[1] = window_size[1] - 100
        elif self.zero_power_length <= self.gun_coords[1] <= window_size[1] - 100:
            self.gun_coords[1] += self.vy

        self.update_angle()
        # Ограничение изменения мощности пушки циклически между `min_gun_power` и `max_gun_power`
        if self.fire_on:
            self.fire_power += self.gun_power_gain
            if self.fire_power > self.max_gun_power or self.fire_power < self.min_gun_power:
                self.gun_power_gain = -self.gun_power_gain
        else:
            self.fire_power = self.min_gun_power
            self.gun_power_gain = abs(self.gun_power_gain)

        self.redraw()
        self.job = self.canvas.after(DT, self.update)

    def update_angle(self):
        self.mouse_coords = self.canvas.get_mouse_coords()
        dx = self.mouse_coords[0] - self.gun_coords[0]
        dy = self.mouse_coords[1] - self.gun_coords[1]
        self.an = 1 if dx == 0 else math.atan(dy / dx)

    def get_gunpoint(self):
        length = (self.fire_power << 1) + self.zero_power_length
        x = self.gun_coords[0] + length * math.cos(self.an)
        y = self.gun_coords[1] + length * math.sin(self.an)
        return x, y

    def redraw(self):
        self.canvas.coords(self.id, *self.gun_coords, *self.get_gunpoint())
        if self.fire_on:
            self.canvas.itemconfig(self.id, fill='orange')
        else:
            self.canvas.itemconfig(self.id, fill='yellow')

    def fire_start(self, event):
        self.fire_on = 1

    def fire_end(self, event):
        self.update_angle()
        bullet_vx = self.fire_power * math.cos(self.an)
        bullet_vy = self.fire_power * math.sin(self.an)
        bullet = Ball(self.canvas, *self.get_gunpoint(), bullet_vx, bullet_vy)
        bullet.start()
        self.fire_on = 0
        self.fire_power = self.min_gun_power

    def set_movement_direction_to_up(self, event):
        if self.gun_coords[1] > self.zero_power_length:
            self.vy = -self.gun_velocity
        else:
            self.stop_movement(None)

    def set_movement_direction_to_down(self, event):
        if self.gun_coords[1] < window_size[1] - 100:
            self.vy = self.gun_velocity
        else:
            self.stop_movement(None)

    def stop_movement(self, event):
        self.vy = 0

    def bind_all(self):
        self.canvas.bind('<Button-1>', self.fire_start, add='')
        self.canvas.bind('<ButtonRelease-1>', self.fire_end, add='')
        root = self.canvas.get_root()
        root.bind('<Up>', self.set_movement_direction_to_up, add='')
        root.bind('<KeyRelease-Up>', self.stop_movement, add='')
        root.bind('<Down>', self.set_movement_direction_to_down, add='')
        root.bind('<KeyRelease-Down>', self.stop_movement, add='')

    def unbind_all(self):
        self.canvas.bind('<Button-1>', pass_event, add='')
        self.canvas.bind('<ButtonRelease-1>', pass_event, add='')
        root = self.canvas.get_root()
        root.bind('<Up>', pass_event, add='')
        root.bind('<KeyRelease-Up>', pass_event, add='')
        root.bind('<Down>', pass_event, add='')
        root.bind('<KeyRelease-Down>', pass_event, add='')

    def destroy(self):
        self.stop()
        self.canvas.delete(self.id)
        self.canvas.delete(self.id1)
        del self.canvas.gun[self.id, self.id1]

    def get_state(self):  # все параметры, кроме `self.gun_coords`, инициализируются в `Gun.__init__()`
        state = {
            "gun_coords": self.gun_coords,
            "job": self.job is not None
        }
        return state


class Target(Agent):
    """Класс для создания мишени на холсте `canvas`. Создается и наследует методы от абстрактного класса `Agent(ABC)`.
    """

    def __init__(self, canvas, level=0, x=None, y=None, r=None, color=None, job_init=None):
        super().__init__()
        self.job = job_init
        # Область вывода мишеней
        x = self.x = rnd((window_size[0] // 3) << 1, window_size[0] - 20) if x is None else x
        y = self.y = rnd(window_size[1] >> 1, window_size[1] - 40) if y is None else y
        # Радиус мишеней
        r = self.r = rnd(42 - level, 51 - level) if r is None else r
        color = self.color = 'red' if color is None else color

        self.canvas = canvas
        self.id = self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=color)

        self.canvas.targets[self.id] = self

    def start(self):
        super().start()

    def play(self):
        super().play()

    def stop(self):
        super().stop()

    def pause(self):
        super().pause()

    def update(self):
        self.job = self.canvas.after(DT, self.update)

    def destroy(self):
        self.stop()
        self.canvas.delete(self.id)
        del self.canvas.targets[self.id]

    def get_state(self):
        state = {
            "x": self.x,
            "y": self.y,
            "r": self.r,
            "color": self.color,
            "job": self.job is not None
        }
        return state


class Decor(Agent):
    """Класс для создания деревьев-препятствий для снарядов на холсте `canvas`.
    Создается и наследует методы от абстрактного класса `Agent(ABC)`.
    """
    def __init__(self, canvas, x=None, y=None, job_init=None):
        super().__init__()

        self.job = job_init
        # Область вывода деревьев
        x = self.x = rnd(window_size[0] // 3, (window_size[0] // 3) << 1) if x is None else x
        y = self.y = rnd(window_size[1] >> 1, (window_size[1] // 3) << 1) if y is None else y

        self.canvas = canvas
        # ствол дерева
        self.id1 = self.canvas.create_polygon(x, y,
                                              x + 0.01*window_size[0], window_size[1],
                                              x - 0.01*window_size[0], window_size[1],
                                              fill='brown')
        # крона дерева
        self.id2 = self.canvas.create_polygon(x, y,
                                              x + 0.015*window_size[0], y + 0.06*window_size[1],
                                              x + 0.007*window_size[0], y + 0.06*window_size[1],
                                              x + 0.03*window_size[0], y + 0.12*window_size[1],
                                              x + 0.015*window_size[0], y + 0.12*window_size[1],
                                              x + 0.04*window_size[0], y + 0.2*window_size[1],
                                              x - 0.04*window_size[0], y + 0.2*window_size[1],
                                              x - 0.015*window_size[0], y + 0.12*window_size[1],
                                              x - 0.03*window_size[0], y + 0.12*window_size[1],
                                              x - 0.007*window_size[0], y + 0.06*window_size[1],
                                              x - 0.015*window_size[0], y + 0.06*window_size[1],
                                              fill='green')

        self.canvas.decors[self.id1, self.id2] = self
        # трава
        # for i in range(1, window_size[0], 10):
        #    self.canvas.create_arc(i, window_size[1]-25,
        #                           i + 10, window_size[1] - 60,
        #                           start=180, extent=-95, style=ARC, outline='green', width=5)

    def start(self):
        super().start()

    def play(self):
        super().play()

    def stop(self):
        super().stop()

    def pause(self):
        super().pause()

    def update(self):
        self.job = self.canvas.after(DT, self.update)

    def destroy(self):
        self.stop()
        self.canvas.delete(self.id1, self.id2)
        del self.canvas.decors[self.id1, self.id2]

    def get_state(self):
        state = {
            "x": self.x,
            "y": self.y,
            "job": self.job is not None
        }
        return state


class BattleField(tk.Canvas):
    """Класс для создания игрового поля. Создается и наследует методы от `tk.Canvas`."""

    def __init__(self, master):
        super().__init__(master, background='black')

        self.num_targets = 2
        self.num_decors = 2

        self.gun = {}
        self.decors = {}
        self.targets = {}
        self.bullets = {}

        # Переменная для присвоения номеров выпущенным снарядам.
        # Номера используются для определения, каким по счету выстрелом была уничтожена цель.
        self.bullet_counter = 0
        self.last_hit_bullet_number = None
        self.victory_text_id = self.create_text(0, 0, text='', font='28', fill="grey")

        self.catch_victory_job = None
        self.canvas_restart_job = None

    def remove_gun(self):
        if len(self.gun) > 0:
            [self.gun[key].destroy() for key in list(self.gun.keys())]
            # Не нужно удалять элемент словаря `self.gun`, т.к. удаление осуществляется в `Gun.destroy()`

    def remove_decors(self, decors_to_remove=None):
        ids = list(self.decors) if decors_to_remove is None else list(decors_to_remove)
        [self.decors[id_].destroy() for id_ in ids]
        # Не нужно удалять элемент словаря `self.decors`, т.к. удаление осуществляется в `Decor.destroy()`

    def remove_targets(self, targets_to_remove=None):
        ids = list(self.targets) if targets_to_remove is None else list(targets_to_remove)
        [self.targets[id_].destroy() for id_ in ids]
        # Не нужно удалять элемент словаря `self.targets`, т.к. удаление осуществляется в `Target.destroy()`

    def remove_bullets(self, bullets_to_remove=None):
        ids = list(self.bullets) if bullets_to_remove is None else list(bullets_to_remove)
        [self.bullets[id_].destroy() for id_ in ids]
        # Не нужно удалять элемент словаря `self.bullets`, т.к. удаление осуществляется в методе `Ball.destroy()`

    def create_gun(self):
        Gun(self)

    def create_targets(self):
        [Target(self, level=self.master.level) for _ in range(self.num_targets)]
        # Не нужно добавлять элемент в словарь `self.targets`, т.к. добавление осуществляется в `Target.__init__()`

    def create_decors(self):
        [Decor(self) for _ in range(self.num_decors)]
        # Не нужно добавлять элемент в словарь `self.decors`, т.к. добавление осуществляется в `Decor.__init__()`

    def create_gun_from_states(self, states, job_init):
        states = copy.deepcopy(states)
        for state in states:
            job_active = state.pop('job')
            Gun(self, **state, job_init=job_init if job_active else None)

    def create_targets_from_states(self, states, job_init):
        states = copy.deepcopy(states)
        for state in states:
            job_active = state.pop('job')
            Target(self, **state, level=self.master.level, job_init=job_init if job_active else None)

    def create_decors_from_states(self, states, job_init):
        states = copy.deepcopy(states)
        for state in states:
            job_active = state.pop('job')
            Decor(self, **state, job_init=job_init if job_active else None)

    def create_bullets_from_states(self, states, job_init):
        states = copy.deepcopy(states)
        for state in states:
            job_active = state.pop('job')
            Ball(self, **state, job_init=job_init if job_active else None)

    def start(self):
        self.catch_victory_job = self.after(DT, self.catch_victory)
        [g.start() for g in self.gun.values()]
        [d.start() for d in self.decors.values()]
        [t.start() for t in self.targets.values()]
        [b.start() for b in self.bullets.values()]

    def play_jobs(self):
        if self.catch_victory_job == 'pause':
            self.catch_victory_job = self.after(DT, self.catch_victory)
        if self.canvas_restart_job == 'pause':
            self.canvas_restart_job = self.after(VICTORY_MSG_TIME, self.restart)

    def play(self):
        self.play_jobs()
        [g.play() for g in self.gun.values()]
        [d.play() for d in self.decors.values()]
        [t.play() for t in self.targets.values()]
        [b.play() for b in self.bullets.values()]

    def stop(self):
        [g.stop() for g in self.gun.values()]
        [d.stop() for d in self.decors.values()]
        [t.stop() for t in self.targets.values()]
        [b.stop() for b in self.bullets.values()]
        if self.catch_victory_job is not None:
            self.after_cancel(self.catch_victory_job)
            self.catch_victory_job = None
        if self.canvas_restart_job is not None:
            self.after_cancel(self.canvas_restart_job)
            self.canvas_restart_job = None

    def pause_jobs(self):
        if self.catch_victory_job is not None:
            self.after_cancel(self.catch_victory_job)
            self.catch_victory_job = 'pause'
        if self.canvas_restart_job is not None:
            self.after_cancel(self.canvas_restart_job)
            self.canvas_restart_job = 'pause'

    def pause(self):
        [g.pause() for g in self.gun.values()]
        [d.pause() for d in self.decors.values()]
        [t.pause() for t in self.targets.values()]
        [b.pause() for b in self.bullets.values()]
        self.pause_jobs()

    def restart(self):
        self.stop()
        self.remove_gun()
        self.remove_decors()
        self.remove_targets()
        self.remove_bullets()
        self.create_gun()
        self.create_decors()
        self.create_targets()
        self.bullet_counter = 0
        self.start()

    def get_root(self):
        root = self.master
        while root.master is not None:
            root = root.master
        return root

    def get_mouse_coords(self):
        abs_x = self.winfo_pointerx()
        abs_y = self.winfo_pointery()
        canvas_x = self.winfo_rootx()
        canvas_y = self.winfo_rooty()
        return [abs_x - canvas_x, abs_y - canvas_y]

    def show_victory_text(self):
        """Проверяет окончание раунда или игры.
        Если раунда - то повышает уровень, а если окончанию игры - то выводит сообщение."""
        if self.master.level >= 40:
            self.remove_gun()
            self.remove_bullets()
            self.remove_decors()
            self.coords(self.victory_text_id, window_size[0] >> 1, window_size[1] >> 1)
            self.itemconfig(self.victory_text_id,
                            text=f'               Поздравляем!\n'
                                 f'Вы поразили {self.master.score} мишеней {self.master.shot} выстрелами.\n\n'
                                 f'              Игра окончена.'
                            )
            self.update()
            # self.canvas_restart_job = self.after(GAME_OVER_MSG_TIME, self.master.new_game())
        else:
            self.canvas_restart_job = self.after(VICTORY_MSG_TIME, self.restart)
        self.master.report_level()

    def catch_victory(self):
        """Завершает раунд"""
        if not self.targets:
            self.catch_victory_job = None
            self.stop()
            self.show_victory_text()
        else:
            self.catch_victory_job = self.after(DT, self.catch_victory)

    def get_bullet_number(self):
        self.bullet_counter += 1
        self.master.report_shot()
        return self.bullet_counter

    def report_hit(self, bullet, target):
        self.last_hit_bullet_number = bullet.bullet_number
        self.master.report_hit()

    def get_state(self):
        state = {
            "gun": [g.get_state() for g in self.gun.values()],
            "decors": [d.get_state() for d in self.decors.values()],
            "targets": [t.get_state() for t in self.targets.values()],
            "bullets": [b.get_state() for b in self.bullets.values()],
            "bullet_counter": self.bullet_counter,
            "last_hit_bullet_number": self.last_hit_bullet_number,
            "catch_victory_job": self.catch_victory_job is not None,
            "canvas_restart_job": self.canvas_restart_job is not None
        }
        return state

    def set_state(self, state, job_init):
        self.remove_gun()
        self.create_gun_from_states(state['gun'], job_init)
        self.remove_decors()
        self.create_decors_from_states(state['decors'], job_init)
        self.remove_targets()
        self.create_targets_from_states(state['targets'], job_init)
        self.remove_bullets()
        self.create_bullets_from_states(state['bullets'], job_init)
        self.bullet_counter = state['bullet_counter']
        self.last_hit_bullet_number = state['last_hit_bullet_number']
        self.catch_victory_job = job_init if state['catch_victory_job'] else None
        self.canvas_restart_job = job_init if state['canvas_restart_job'] else None


class MainFrame(tk.Frame):
    """Класс для создания фреймов с отображаемыми результатами и под основное игровое поле.
    Создается и наследует методы от `tk.Frame`."""
    def __init__(self, master):
        super().__init__(master)

        # Фрейм с выводом результатов
        self.fr_top = tk.Frame()
        self.fr_top.pack(side=tk.TOP, fill=tk.X)

        self.level = 0
        self.level_tmpl = 'Уровень: {}'
        self.level_lbl = tk.Label(self.fr_top, fg="blue", text=self.level_tmpl.format(self.level),
                                  font=("Comic Sans MS", 18, "bold"))
        self.level_lbl.pack(side=tk.LEFT)

        self.score = 0
        self.score_tmpl = 'Попаданий: {}'
        self.score_lbl = tk.Label(self.fr_top, fg="green", text=self.score_tmpl.format(self.score),
                                  font=("Comic Sans MS", 18, "bold"))
        self.score_lbl.pack(side=tk.RIGHT)

        self.shot = 0
        self.shot_tmpl = 'Выстрелов: {}'
        self.shot_lbl = tk.Label(self.fr_top, fg="orange", text=self.shot_tmpl.format(self.shot),
                                 font=("Comic Sans MS", 18, "bold"))
        self.shot_lbl.pack(side=tk.RIGHT)

        self.battlefield = BattleField(self)
        self.battlefield.pack(fill=tk.BOTH, expand=1)

    def new_game(self):
        self.shot = 0
        self.shot_lbl['text'] = self.shot_tmpl.format(self.shot)
        self.level = 0
        self.level_lbl['text'] = self.level_tmpl.format(self.level)
        self.score = 0
        self.score_lbl['text'] = self.score_tmpl.format(self.score)
        self.battlefield.restart()

    def stop(self):
        self.battlefield.stop()

    def play(self):
        self.battlefield.play()

    def pause(self):
        self.battlefield.pause()

    def report_level(self):
        self.level += 1
        self.level_lbl['text'] = self.level_tmpl.format(self.level)

    def report_shot(self):
        self.shot += 1
        self.shot_lbl['text'] = self.shot_tmpl.format(self.shot)

    def report_hit(self):
        self.score += 1
        self.score_lbl['text'] = self.score_tmpl.format(self.score)

    def get_state(self):
        state = {
            'level': self.level,
            'shot': self.shot,
            'score': self.score,
            'battlefield': self.battlefield.get_state(),
            'geometry': window_size
        }
        return state

    def set_state(self, state, job_init):
        self.level = state['level']
        self.level_lbl['text'] = self.level_tmpl.format(self.level)
        self.shot = state['shot']
        self.shot_lbl['text'] = self.shot_tmpl.format(self.shot)
        self.score = state['score']
        self.score_lbl['text'] = self.score_tmpl.format(self.score)
        self.battlefield.set_state(state['battlefield'], job_init)


class Menu(tk.Menu):
    """Класс для создания игрового меню. Создается и наследует методы от `tk.Menu`."""
    def __init__(self, master, game):
        super().__init__(master)

        self.game = game

        self.game_menu = tk.Menu(self, tearoff=0)
        self.game_menu.add_command(label="Новая", command=self.master.new_game)
        self.game_menu.add_command(label="Загрузить...", command=self.master.load)
        self.game_menu.add_command(label="Сохранить...", command=self.master.save)
        self.game_menu.add_separator()
        self.game_menu.add_command(label="Выход", command=exit)
        self.add_cascade(label="Игра", menu=self.game_menu)

        self.help_menu = tk.Menu(self, tearoff=0)
        self.help_menu.add_command(label="О программе", command=about)
        self.add_cascade(label="Справка", menu=self.help_menu)


class GunGameApp(tk.Tk):
    """Основной класс приложения-формы. Создается и наследует методы от `tk.Tk`."""
    def __init__(self):
        super().__init__()
        self.geometry('{}x{}+0+0'.format(*window_size))
        self.title('Пушка')

        # Переменная `__file__` содержит путь к файлу, в котором используется.
        #
        # Функция `os.path.split()` разделяет путь к файлу на имя директории и имя файла.
        #
        # Функция `os.path.join()` объединяет несколько путей в один. Она самостоятельно подбирает разделитель
        # в соответствии с операционной системой: '/' для UNIX и '\' для Windows.
        self.save_dir = os.path.join(os.path.split(__file__)[0], 'save')

        self.main_frame = MainFrame(self.master)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        self.menu = Menu(self.master, self)
        self.config(menu=self.menu)

        self.bind('<Configure>', self.app_resize)
        self.bind("<Control-s>", self.save)
        self.bind("<Control-l>", self.load)

    def app_resize(self, event=None):
        """Процедура пропорционального изменения координат виджетов игры в зависимости от изменения размеров формы"""
        self.pause()
        game_state = self.get_state()   # собираем состояния
        # высчитываем коэффициенты для изменения координат виджетов
        size = read_form_size()
        kx = size[0]/window_size[0]
        ky = size[1]/window_size[1]
        set_window_size(size)    # изменяем глобальную переменную
        # изменяем координаты виджетов `decors` и `targets`
        game_state['main_frame'].update({'geometry': size})
        for d in game_state['main_frame']['battlefield']['decors']:
            d.update({'x': int(d['x']*kx)})
            d.update({'y': int(d['y']*ky)})
        for t in game_state['main_frame']['battlefield']['targets']:
            t.update({'x': int(t['x']*kx)})
            t.update({'y': int(t['y']*ky)})

        self.set_state(game_state)  # применяем новые состояния
        self.play()

    def get_state(self):
        """Собирает все меняющиеся признаки виджетов и подвижных элементов из `canvas`."""
        return {'main_frame': self.main_frame.get_state()}

    def set_state(self, state, job_init='pause'):
        """Создает игру соответствующую состоянию `state`.
        Применяется к состояниям приложения полученным с помощью метода `GunGameApp.get_state()`.
        `state` содержит значения всех изменяющихся в процессе игры признаков. Эти значения присваиваются признакам
        `MainFrame`, `BattleField`, пушке с фоном, мишени, деревьям и снарядам.
        Отложенным событиям, которым соответствует `True` в `state`, присваивается значение `job_init`.
        Если `job_init == 'pause'`, то после выполнения `GunGameApp.set_state()` игра может быть запущена
        `GunGameApp.play()`.

        Args:
            state (словарь, содержащий другие словари и списки): Структура словаря `state` должна повторять структуру
                виджетов приложения. В словаре `state` есть ключ `'main_frame'`, в словаре `state['main_frame']`
                -- элемент `'battlefield'` и т.д..
            job_init (`str` или `None`): Этим значением инициализируется активные на момент получения состояния игры
                `state` отложенные задачи.
        Returns:
            None
        """
        self.main_frame.set_state(state['main_frame'], job_init)

    def get_save_file_name(self):
        os.makedirs(self.save_dir, exist_ok=True)
        file_name = filedialog.asksaveasfilename(
            initialdir=self.save_dir,
            title='Сохранить игру',
            filetypes=(("json files", "*.json"), ("all files", "*.*")),
            initialfile='Untitled.json',
            defaultextension='.json'
        )
        if file_name in [(), '']:
            return None
        return file_name

    def get_load_file_name(self):
        file_name = filedialog.askopenfilename(
            initialdir=self.save_dir,
            title='Загрузить игру',
            filetypes=(("json files", "*.json"), ("all files", "*.*"))
        )
        if file_name in [(), '']:
            return None
        return file_name

    def save(self, event=None):
        self.pause()
        game_state = self.get_state()
        file_name = self.get_save_file_name()
        if file_name is not None:
            with open(file_name, 'w') as f:
                # Аргумент `indent` обеспечивает красивое оформление JSON файла.
                json.dump(game_state, f, indent=2)
        self.play()

    def load(self):
        # Приложение ставится на паузу, а не останавливается, чтобы при сборе
        # состояния игры было видно, какие отложенные задачи активны.
        self.pause()
        file_name = self.get_load_file_name()
        if file_name is not None:
            with open(file_name) as f:
                state = json.load(f)   # загружаем состояния виджетов игры
            self.set_state(state)
            # корректируем размер окна игры под загружаемую
            if app.state() == 'zoomed' and read_form_size() != state['main_frame']['geometry']:
                app.state('normal')
            set_window_size(state['main_frame']['geometry'])
            app.geometry('{}x{}'.format(*window_size))
        self.play()

    def new_game(self):
        self.main_frame.new_game()

    def pause(self):
        """Приостанавливает игру. Отложенным задачам присваивается значение `'pause'`.
        Игру можно возобновить с помощью метода `GunGameApp.play()`."""
        self.main_frame.pause()

    def play(self):
        self.main_frame.play()

    def stop(self):
        """Снимает все отложенные задачи. Отложенным задачам присваивается `None`."""
        self.main_frame.stop()


# глобальная переменная с первоначальными размерами формы, изменяется методом `set_window_size()`
window_size = [1000, 700]

app = GunGameApp()
app.state('zoomed')
app.mainloop()
