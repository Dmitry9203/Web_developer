import tkinter as tk
from tkinter import messagebox
import random


# Палитра
COLOR_CLOSED  = "#bdbdbd"   # серый фон закрытой клетки
COLOR_OPENED  = "#f0f0f0"   # светло-серый фон открытой
COLOR_CURSOR  = "#000000"   # чёрная обводка курсора
COLOR_MINE_BG = "#ff9999"   # фон клетки с миной при проигрыше
COLOR_FLAG    = "#ffffff"   # цвет символа флажка
BORDER_PAD = 2              # толщина «обводки»


class Minesweeper:
    def __init__(self, root, rows=9, cols=9, mines=10):
        self.root = root
        self.rows = rows
        self.cols = cols
        self.mines_count = mines
        self.buttons = {}
        self.cells   = {}
        self.board = []
        self.revealed = []
        self.flags = []
        self.game_over = False
        self.first_click = True

        self.cursor_r = 0
        self.cursor_c = 0

        self.root.title("Сапёр")
        self.root.resizable(False, False)
        self.root.configure(bg="#ffffff")

        # Верхняя панель
        self.top_frame = tk.Frame(root, bg="#ffffff")
        self.top_frame.pack(pady=5)

        self.mines_label = tk.Label(
            self.top_frame, text=f"💣 {mines}",
            font=("Arial", 14, "bold"), bg="#ffffff"
        )
        self.mines_label.pack(side=tk.LEFT, padx=10)

        self.reset_btn = tk.Button(
            self.top_frame, text="🙂", font=("Arial", 14),
            command=self.reset_game,
            relief=tk.FLAT, borderwidth=0, bg="#e0e0e0",
        )
        self.reset_btn.pack(side=tk.LEFT, padx=10)

        self.timer_label = tk.Label(
            self.top_frame, text="⏱ 0",
            font=("Arial", 14, "bold"), bg="#ffffff"
        )
        self.timer_label.pack(side=tk.LEFT, padx=10)

        self.hint = tk.Label(
            root,
            text="Стрелки — курсор · Пробел/Enter — открыть · Ctrl+Пробел/Enter — флажок · R — новая игра",
            font=("Arial", 9), fg="#666", bg="#ffffff",
        )
        self.hint.pack(pady=(0, 4))

        # ---- Игровое поле ----
        self.board_frame = tk.Frame(root, bg="#ffffff")
        self.board_frame.pack(padx=5, pady=5)

        self.timer_running = False
        self.time = 0

        self.create_widgets()
        self.reset_game()
        self.bind_keys()
        self.root.focus_set()

    def create_widgets(self):
        GAP = 2
        for r in range(self.rows):
            for c in range(self.cols):
                cell = tk.Frame(
                    self.board_frame,
                    bg=COLOR_CLOSED,
                    padx=BORDER_PAD,
                    pady=BORDER_PAD,
                )
                cell.grid(row=r, column=c, padx=GAP, pady=GAP)
                self.cells[(r, c)] = cell

                btn = tk.Button(
                    cell,
                    width=2, height=1,
                    font=("Arial", 12, "bold"),
                    command=lambda r=r, c=c: self.on_left_click(r, c),
                    takefocus=False,
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=0,
                    bg=COLOR_CLOSED,
                    activebackground=COLOR_CLOSED,
                    fg="black",
                )
                btn.pack()
                btn.bind("<Button-3>", lambda e, r=r, c=c: self.on_right_click(r, c))
                self.buttons[(r, c)] = btn

    def bind_keys(self):
        self.root.bind("<Up>",    lambda e: self.move_cursor(-1, 0))
        self.root.bind("<Down>",  lambda e: self.move_cursor(1, 0))
        self.root.bind("<Left>",  lambda e: self.move_cursor(0, -1))
        self.root.bind("<Right>", lambda e: self.move_cursor(0, 1))

        self.root.bind("<space>",          lambda e: self.activate_current(False))
        self.root.bind("<Return>",         lambda e: self.activate_current(False))
        self.root.bind("<KP_Enter>",       lambda e: self.activate_current(False))

        self.root.bind("<Control-space>",    lambda e: self.activate_current(True))
        self.root.bind("<Control-Return>",   lambda e: self.activate_current(True))
        self.root.bind("<Control-KP_Enter>", lambda e: self.activate_current(True))

        self.root.bind("<r>", lambda e: self.reset_game())
        self.root.bind("<R>", lambda e: self.reset_game())
    
    def move_cursor(self, dr, dc):
        if self.game_over:
            return
        nr = min(max(self.cursor_r + dr, 0), self.rows - 1)
        nc = min(max(self.cursor_c + dc, 0), self.cols - 1)
        if (nr, nc) != (self.cursor_r, self.cursor_c):
            self.cursor_r, self.cursor_c = nr, nc
            self.refresh_cursor()

    def refresh_cursor(self):
        for r in range(self.rows):
            for c in range(self.cols):
                self._apply_style(
                    r, c,
                    is_cursor=(r == self.cursor_r and c == self.cursor_c)
                )

    def activate_current(self, flag):
        if self.game_over:
            return
        r, c = self.cursor_r, self.cursor_c
        if flag:
            self.on_right_click(r, c)
        else:
            self.on_left_click(r, c)
        self.refresh_cursor()

    def _apply_style(self, r, c, is_cursor=False):
        """
        Обводка курсора рисуется ВСЕГДА, независимо от того,
        открыта клетка или нет.
        """
        cell = self.cells[(r, c)]
        btn = self.buttons[(r, c)]

        # 1) Обводка. Курсор — всегда чёрный.
        if is_cursor:
            cell.config(bg=COLOR_CURSOR)
        elif self.revealed[r][c]:
            cell.config(bg=COLOR_OPENED)
        elif self.game_over and self.board[r][c] == -1 and not self.flags[r][c]:
            cell.config(bg=COLOR_MINE_BG)
        else:
            cell.config(bg=COLOR_CLOSED)

        # 2) Состояние кнопки — только для закрытых клеток.
        if self.revealed[r][c]:
            return

        btn.config(
            bg=COLOR_CLOSED, activebackground=COLOR_CLOSED,
            relief=tk.FLAT, borderwidth=0, state=tk.NORMAL,
        )
        if self.flags[r][c]:
            btn.config(text="⚑", fg=COLOR_FLAG)
        else:
            btn.config(text="", fg="black")

    def reset_game(self):
        self.game_over = False
        self.first_click = True
        self.time = 0
        self.timer_running = False
        self.timer_label.config(text="⏱ 0")
        self.reset_btn.config(text="🙂")
        self.mines_label.config(text=f"💣 {self.mines_count}")

        self.board = [[0] * self.cols for _ in range(self.rows)]
        self.revealed = [[False] * self.cols for _ in range(self.rows)]
        self.flags = [[False] * self.cols for _ in range(self.rows)]

        self.cursor_r, self.cursor_c = 0, 0

        for (r, c), btn in self.buttons.items():
            btn.config(
                text="", state=tk.NORMAL,
                bg=COLOR_CLOSED, activebackground=COLOR_CLOSED,
                fg="black", relief=tk.FLAT, borderwidth=0,
            )
            self.cells[(r, c)].config(bg=COLOR_CLOSED)

        self.refresh_cursor()

    def place_mines(self, safe_r, safe_c):
        forbidden = set()
        for dr in range(-1, 2):
            for dc in range(-1, 2):
                nr, nc = safe_r + dr, safe_c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    forbidden.add((nr, nc))

        cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                 if (r, c) not in forbidden]
        for r, c in random.sample(cells, self.mines_count):
            self.board[r][c] = -1

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1:
                    continue
                count = 0
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            if self.board[nr][nc] == -1:
                                count += 1
                self.board[r][c] = count

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            self.update_timer()

    def update_timer(self):
        if self.timer_running and not self.game_over:
            self.time += 1
            self.timer_label.config(text=f"⏱ {self.time}")
            self.root.after(1000, self.update_timer)

    def on_left_click(self, r, c):
        if self.game_over or self.flags[r][c]:
            return
        if self.first_click:
            self.first_click = False
            self.place_mines(r, c)
            self.start_timer()
        if self.revealed[r][c]:
            return
        if self.board[r][c] == -1:
            self.lose_game()
            return
        self.reveal(r, c)
        self.check_win()

    def reveal(self, r, c):
        if self.revealed[r][c] or self.flags[r][c]:
            return
        self.revealed[r][c] = True
        btn = self.buttons[(r, c)]
        cell = self.cells[(r, c)]
        value = self.board[r][c]

        # обводка: клетка под курсором остаётся с чёрной обводкой
        if r == self.cursor_r and c == self.cursor_c:
            cell.config(bg=COLOR_CURSOR)
        else:
            cell.config(bg=COLOR_OPENED)

        if value == 0:
            btn.config(
                text="", bg=COLOR_OPENED, activebackground=COLOR_OPENED,
                relief=tk.FLAT, borderwidth=0, state=tk.DISABLED,
            )
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        self.reveal(nr, nc)
        else:
            color = {1: "blue", 2: "green", 3: "red", 4: "navy",
                     5: "maroon", 6: "teal", 7: "black", 8: "gray"}.get(value, "black")
            btn.config(
                text=str(value), fg=color,
                bg=COLOR_OPENED, activebackground=COLOR_OPENED,
                relief=tk.FLAT, borderwidth=0, state=tk.DISABLED,
            )

    def on_right_click(self, r, c):
        if self.game_over or self.revealed[r][c]:
            return
        self.flags[r][c] = not self.flags[r][c]
        self.update_mines_label()
        self._apply_style(
            r, c,
            is_cursor=(r == self.cursor_r and c == self.cursor_c)
        )

    def update_mines_label(self):
        flag_count = sum(sum(row) for row in self.flags)
        self.mines_label.config(text=f"💣 {self.mines_count - flag_count}")

    def lose_game(self):
        self.game_over = True
        self.timer_running = False
        self.reset_btn.config(text="😵")

        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == -1 and not self.flags[r][c]:
                    # если мина под курсором — оставляем чёрную обводку
                    if r == self.cursor_r and c == self.cursor_c:
                        self.cells[(r, c)].config(bg=COLOR_CURSOR)
                    else:
                        self.cells[(r, c)].config(bg=COLOR_MINE_BG)
                    self.buttons[(r, c)].config(
                        text="💣",
                        bg=COLOR_MINE_BG, activebackground=COLOR_MINE_BG,
                        relief=tk.FLAT, borderwidth=0,
                    )

        messagebox.showinfo("Игра окончена", "Вы подорвались на мине! 💥")

    def check_win(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != -1 and not self.revealed[r][c]:
                    return
        self.game_over = True
        self.timer_running = False
        self.reset_btn.config(text="😎")
        messagebox.showinfo("Победа!", f"Вы победили за {self.time} секунд! 🎉")

if __name__ == "__main__":
    root = tk.Tk()
    game = Minesweeper(root, rows=12, cols=12, mines=20)
    root.mainloop()