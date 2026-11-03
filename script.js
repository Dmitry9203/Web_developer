// --- Палитра и константы ---
const COLOR_CLOSED = "#bdbdbd";
const COLOR_OPENED = "#f0f0f0";
const COLOR_CURSOR = "#000000";
const COLOR_MINE_BG = "#ff9999";

const NUM_COLORS = {
    1: "#0000ff", 2: "#008000", 3: "#ff0000", 4: "#000080",
    5: "#800000", 6: "#008080", 7: "#000000", 8: "#808080",
};


class Minesweeper {
    constructor(rootEl, rows = 9, cols = 9, mines = 10) {
        this.root = rootEl;
        this.rows = rows;
        this.cols = cols;
        this.minesCount = mines;

        // DOM-хранилища
        this.cells = {};      // (r,c) -> div.cell (обёртка)
        this.buttons = {};    // (r,c) -> button

        // Логическое состояние
        this.board = [];      // -1 = мина, 0..8 = число
        this.revealed = [];   // bool
        this.flags = [];      // bool

        this.gameOver = false;
        this.firstClick = true;

        // Курсор
        this.cursorR = 0;
        this.cursorC = 0;

        // Таймер
        this.timerRunning = false;
        this.time = 0;
        this.timerInterval = null;

        // Ссылки на элементы панели
        this.minesCounterEl = document.getElementById("mines-counter");
        this.timerEl = document.getElementById("timer");
        this.resetBtn = document.getElementById("reset-btn");

        this.resetBtn.addEventListener("click", () => this.resetGame());

        this.createWidgets();
        this.resetGame();
        this.bindKeys();
    }

    // Создание сетки
    createWidgets() {
        this.root.style.gridTemplateColumns = `repeat(${this.cols}, auto)`;

        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                // Обёртка = «обводка»
                const cell = document.createElement("div");
                cell.className = "cell";
                this.root.appendChild(cell);

                // Кнопка внутри
                const btn = document.createElement("button");
                btn.type = "button";
                btn.addEventListener("click", () => this.onLeftClick(r, c));
                btn.addEventListener("contextmenu", (e) => {
                    e.preventDefault();
                    this.onRightClick(r, c);
                });
                cell.appendChild(btn);

                this.cells[`${r},${c}`] = cell;
                this.buttons[`${r},${c}`] = btn;
            }
        }
    }

    getCell(r, c)   { return this.cells[`${r},${c}`]; }
    getButton(r, c) { return this.buttons[`${r},${c}`]; }

    // Клавиатура
    bindKeys() {
        document.addEventListener("keydown", (e) => {
            // Стрелки
            switch (e.key) {
                case "ArrowUp":    e.preventDefault(); this.moveCursor(-1, 0); return;
                case "ArrowDown":  e.preventDefault(); this.moveCursor(1, 0);  return;
                case "ArrowLeft":  e.preventDefault(); this.moveCursor(0, -1); return;
                case "ArrowRight": e.preventDefault(); this.moveCursor(0, 1);  return;
            }

            // R — рестарт (латиница)
            if (e.key === "r" || e.key === "R") {
                this.resetGame();
                return;
            }

            // Пробел / Enter — открыть; Ctrl+… — флажок
            if (e.key === " " || e.key === "Enter") {
                e.preventDefault();
                this.activateCurrent(e.ctrlKey);
            }
        });
    }

    moveCursor(dr, dc) {
        if (this.gameOver) return;
        const nr = Math.min(Math.max(this.cursorR + dr, 0), this.rows - 1);
        const nc = Math.min(Math.max(this.cursorC + dc, 0), this.cols - 1);
        if (nr !== this.cursorR || nc !== this.cursorC) {
            this.cursorR = nr;
            this.cursorC = nc;
            this.refreshCursor();
        }
    }

    refreshCursor() {
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                this.applyStyle(r, c, r === this.cursorR && c === this.cursorC);
            }
        }
    }

    activateCurrent(flag) {
        if (this.gameOver) return;
        const r = this.cursorR, c = this.cursorC;
        if (flag) this.onRightClick(r, c);
        else      this.onLeftClick(r, c);
        this.refreshCursor();
    }

    // Стилизация
    applyStyle(r, c, isCursor = false) {
        const cell = this.getCell(r, c);
        const btn = this.getButton(r, c);

        // 1) Обводка. Курсор — всегда чёрный.
        cell.classList.remove("cursor", "revealed", "mine-visible");

        if (isCursor) {
            cell.classList.add("cursor");
        } else if (this.revealed[r][c]) {
            cell.classList.add("revealed");
        } else if (this.gameOver && this.board[r][c] === -1 && !this.flags[r][c]) {
            cell.classList.add("mine-visible");
        }
        // иначе — обычный .cell (серый)

        // 2) Кнопка — только для закрытых клеток.
        if (this.revealed[r][c]) return;

        btn.className = "";
        btn.textContent = "";
        btn.removeAttribute("data-num");

        if (this.flags[r][c]) {
            btn.textContent = "⚑";
            btn.classList.add("flagged");
        }
    }

    // Сброс
    resetGame() {
        this.gameOver = false;
        this.firstClick = true;

        this.stopTimer();
        this.time = 0;
        this.timerEl.textContent = "⏱ 0";
        this.resetBtn.textContent = "🙂";
        this.minesCounterEl.textContent = `💣 ${this.minesCount}`;

        // Матрицы
        this.board = [];
        this.revealed = [];
        this.flags = [];
        for (let r = 0; r < this.rows; r++) {
            this.board.push(new Array(this.cols).fill(0));
            this.revealed.push(new Array(this.cols).fill(false));
            this.flags.push(new Array(this.cols).fill(false));
        }

        this.cursorR = 0;
        this.cursorC = 0;

        // Сброс DOM
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                const cell = this.getCell(r, c);
                const btn = this.getButton(r, c);
                cell.className = "cell";
                btn.className = "";
                btn.textContent = "";
                btn.removeAttribute("data-num");
                btn.disabled = false;
            }
        }

        this.refreshCursor();
    }

    // Мины
    placeMines(safeR, safeC) {
        const forbidden = new Set();
        for (let dr = -1; dr <= 1; dr++) {
            for (let dc = -1; dc <= 1; dc++) {
                const nr = safeR + dr, nc = safeC + dc;
                if (nr >= 0 && nr < this.rows && nc >= 0 && nc < this.cols) {
                    forbidden.add(`${nr},${nc}`);
                }
            }
        }

        const cells = [];
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                if (!forbidden.has(`${r},${c}`)) cells.push([r, c]);
            }
        }

        // Перемешивание (аналог random.sample) — Фишер-Йетс
        for (let i = cells.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [cells[i], cells[j]] = [cells[j], cells[i]];
        }

        for (let i = 0; i < this.minesCount; i++) {
            const [r, c] = cells[i];
            this.board[r][c] = -1;
        }

        // Подсчёт чисел
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                if (this.board[r][c] === -1) continue;
                let count = 0;
                for (let dr = -1; dr <= 1; dr++) {
                    for (let dc = -1; dc <= 1; dc++) {
                        if (dr === 0 && dc === 0) continue;
                        const nr = r + dr, nc = c + dc;
                        if (nr >= 0 && nr < this.rows && nc >= 0 && nc < this.cols) {
                            if (this.board[nr][nc] === -1) count++;
                        }
                    }
                }
                this.board[r][c] = count;
            }
        }
    }

    // Таймер
    startTimer() {
        if (this.timerRunning) return;
        this.timerRunning = true;
        this.timerInterval = setInterval(() => {
            if (this.gameOver) return;
            this.time++;
            this.timerEl.textContent = `⏱ ${this.time}`;
        }, 1000);
    }

    stopTimer() {
        this.timerRunning = false;
        if (this.timerInterval !== null) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    // Открытие
    onLeftClick(r, c) {
        if (this.gameOver || this.flags[r][c]) return;

        if (this.firstClick) {
            this.firstClick = false;
            this.placeMines(r, c);
            this.startTimer();
        }

        if (this.revealed[r][c]) return;
        if (this.board[r][c] === -1) {
            this.loseGame();
            return;
        }

        this.reveal(r, c);
        this.checkWin();
    }

    reveal(r, c) {
        if (this.revealed[r][c] || this.flags[r][c]) return;
        this.revealed[r][c] = true;

        const cell = this.getCell(r, c);
        const btn = this.getButton(r, c);
        const value = this.board[r][c];

        // обводка: клетка под курсором остаётся чёрной
        cell.classList.remove("cursor", "revealed", "mine-visible");
        if (r === this.cursorR && c === this.cursorC) {
            cell.classList.add("cursor");
        } else {
            cell.classList.add("revealed");
        }

        btn.disabled = true;

        if (value === 0) {
            btn.textContent = "";
            for (let dr = -1; dr <= 1; dr++) {
                for (let dc = -1; dc <= 1; dc++) {
                    if (dr === 0 && dc === 0) continue;
                    const nr = r + dr, nc = c + dc;
                    if (nr >= 0 && nr < this.rows && nc >= 0 && nc < this.cols) {
                        this.reveal(nr, nc);
                    }
                }
            }
        } else {
            btn.textContent = String(value);
            btn.setAttribute("data-num", value);
        }
    }

    onRightClick(r, c) {
        if (this.gameOver || this.revealed[r][c]) return;
        this.flags[r][c] = !this.flags[r][c];
        this.updateMinesCounter();
        this.applyStyle(r, c, r === this.cursorR && c === this.cursorC);
    }

    updateMinesCounter() {
        let flagCount = 0;
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                if (this.flags[r][c]) flagCount++;
            }
        }
        this.minesCounterEl.textContent = `💣 ${this.minesCount - flagCount}`;
    }

    // Конец игры
    loseGame() {
        this.gameOver = true;
        this.stopTimer();
        this.resetBtn.textContent = "😵";

        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                if (this.board[r][c] === -1 && !this.flags[r][c]) {
                    const cell = this.getCell(r, c);
                    const btn = this.getButton(r, c);
                    cell.classList.remove("cursor", "revealed", "mine-visible");
                    if (r === this.cursorR && c === this.cursorC) {
                        cell.classList.add("cursor");
                    } else {
                        cell.classList.add("mine-visible");
                    }
                    btn.textContent = "💣";
                    btn.disabled = true;
                }
            }
        }

        setTimeout(() => alert("Вы подорвались на мине! 💥"), 50);
    }

    checkWin() {
        for (let r = 0; r < this.rows; r++) {
            for (let c = 0; c < this.cols; c++) {
                if (this.board[r][c] !== -1 && !this.revealed[r][c]) return;
            }
        }
        this.gameOver = true;
        this.stopTimer();
        this.resetBtn.textContent = "😎";
        setTimeout(() => alert(`Победа! Вы победили за ${this.time} секунд! 🎉`), 50);
    }
}


// --- Запуск ---
document.addEventListener("DOMContentLoaded", () => {
    const board = document.getElementById("board");
    new Minesweeper(board, 9, 9, 10);
});