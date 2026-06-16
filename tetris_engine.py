import random
from collections import deque
import numpy as np
from config import GRID_ROWS, GRID_COLS, SHAPES, LEVEL_SPEEDS

class TetrisEngine:
    def __init__(self):
        # ==========================================
        # 遊戲初始化
        # ==========================================
        self.grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=object)
        
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        
        # ==========================================
        # 7-Bag 初始化
        # ==========================================
        self.bag_queue = deque()
        self._fill_bag()  # 第一袋
        self._fill_bag()  # 第二袋
        
        # ==========================================
        # 方塊 / 暫存 / 狀態控制
        # ==========================================
        self.current_piece = None  
        self.current_matrix = None
        self.current_pos = [0, 0]
        self.current_rotation = 0 
        
        self.hold_piece = None
        self.has_held_this_turn = False 
        
        # 第一個方塊
        self.spawn_piece()
    # 7-BAG
    def _fill_bag(self):
        bag = list(SHAPES.keys())
        random.shuffle(bag)
        self.bag_queue.extend(bag)

    def spawn_piece(self):
        self.current_piece = self.bag_queue.popleft()
        self.current_matrix = SHAPES[self.current_piece].copy()
        self.current_rotation = 0
        self.has_held_this_turn = False
        
        # 補充一袋 (7個)
        if len(self.bag_queue) < 7:
            self._fill_bag()
            
        # 標準頂部生成
        spawn_col = (GRID_COLS - self.current_matrix.shape[1]) // 2
        self.current_pos = [0, spawn_col]
        
        # 檢查 Game Over
        if self.check_collision(self.current_pos, self.current_matrix):
            self.game_over = True

    def check_collision(self, pos, matrix):
        r_start, c_start = pos
        h, w = matrix.shape
        
        for r in range(h):
            for c in range(w):
                if matrix[r, c] != 0:
                    grid_r = r_start + r
                    grid_c = c_start + c
                    if grid_c < 0 or grid_c >= GRID_COLS or grid_r >= GRID_ROWS:
                        return True
                    # 標準規則允許在畫布上方（隱藏行）旋轉，但不能與已有方塊碰撞
                    if grid_r >= 0:
                        if self.grid[grid_r, grid_c] != 0:
                            return True
        return False

    def get_fall_delay(self):
        # Level 的下落時間
        return LEVEL_SPEEDS.get(self.level, LEVEL_SPEEDS[10])
    def move(self, dr, dc):
        next_pos = [self.current_pos[0] + dr, self.current_pos[1] + dc]
        if not self.check_collision(next_pos, self.current_matrix):
            self.current_pos = next_pos
            return True
        return False

    def hold(self):
        # Hold 暫存功能
        if self.has_held_this_turn or self.game_over:
            return

        from config import SHAPES
        if self.hold_piece is None:
            # 暫存區是空的，直接 hold 並抽取
            self.hold_piece = self.current_piece
            self.spawn_piece()
        else:
            # 暫存區有方塊，互換
            prev_hold = self.hold_piece
            self.hold_piece = self.current_piece
            
            self.current_piece = prev_hold
            self.current_matrix = SHAPES[self.current_piece].copy()
            self.current_rotation = 0
            spawn_col = (GRID_COLS - self.current_matrix.shape[1]) // 2
            self.current_pos = [0, spawn_col]
            if self.check_collision(self.current_pos, self.current_matrix):
                self.game_over = True
                
        self.has_held_this_turn = True

    def rotate_piece(self):
        # 踢牆查表
        if self.current_piece == 'O':  # 正方形跳過
            return
        next_matrix = np.rot90(self.current_matrix, k=-1)
        next_rotation = (self.current_rotation + 1) % 4
        from config import SRS_KICK_TABLE_B, SRS_KICK_TABLE_C
        if self.current_piece == 'I':
            kick_table = SRS_KICK_TABLE_C
        else:
            kick_table = SRS_KICK_TABLE_B
        lookup_key = (self.current_rotation, next_rotation)
        offsets = kick_table.get(lookup_key, [(0, 0)]) 

        for dy, dx in offsets:
            test_pos = [self.current_pos[0] - dy, self.current_pos[1] + dx]
            
            if not self.check_collision(test_pos, next_matrix):
                self.current_matrix = next_matrix
                self.current_pos = test_pos
                self.current_rotation = next_rotation
                return  # 旋轉成功

    def lock_piece(self):
        r_start, c_start = self.current_pos
        h, w = self.current_matrix.shape
        
        for r in range(h):
            for c in range(w):
                if self.current_matrix[r, c] != 0:
                    grid_r = r_start + r
                    grid_c = c_start + c
                    if 0 <= grid_r < GRID_ROWS and 0 <= grid_c < GRID_COLS:
                        self.grid[grid_r, grid_c] = self.current_piece
                        
        # 消行
        self.check_lines()
        # 下一顆方塊
        self.spawn_piece()

    def check_lines(self):
        full_rows = []
        for r in range(GRID_ROWS):
            if np.all(self.grid[r] != 0):
                full_rows.append(r)
                
        num_cleared = len(full_rows)
        if num_cleared == 0:
            return
            
        # 消行計分 (消除 1/2/3/4 行)
        score_values = {1: 100, 2: 300, 3: 500, 4: 800}
        self.score += score_values.get(num_cleared, 0)
        
        # 圖更新
        new_grid = [row for r, row in enumerate(self.grid) if r not in full_rows]
        while len(new_grid) < GRID_ROWS:
            new_grid.insert(0, np.zeros(GRID_COLS, dtype=object))
        self.grid = np.array(new_grid, dtype=object)
        
        # Level
        self.lines_cleared += num_cleared
        new_level = (self.lines_cleared // 10) + 1
        if new_level > self.level:
            self.level = min(new_level, 10) # 最高 Level 10 
    # 影子方塊位置
    def get_ghost_row(self):
        ghost_row = self.current_pos[0]
        while not self.check_collision([ghost_row + 1, self.current_pos[1]], self.current_matrix):
            ghost_row += 1
        return ghost_row