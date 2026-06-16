import time
import numpy as np
import cv2
import keyboard 
from config import (
    GRID_ROWS, GRID_COLS, CELL_SIZE, GAME_HEIGHT, GAME_WIDTH,
    PANEL_WIDTH, TOTAL_WIDTH, COLOR_MAP, SHAPES
)
from tetris_engine import TetrisEngine

def draw_cell(img, r, c, color, is_ghost=False):
    y1, x1 = r * CELL_SIZE, c * CELL_SIZE
    y2, x2 = y1 + CELL_SIZE, x1 + CELL_SIZE
    
    if is_ghost:
        # 影子方塊
        cv2.rectangle(img, (x1 + 2, y1 + 2), (x2 - 2, y2 - 2), color, 2)
    else:
        # 實心方塊
        cv2.rectangle(img, (x1, y1), (x2, y2), color, -1)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 1)

def render_game(engine):
    #建構完整畫布(遊戲區+右側資訊)
    canvas = np.zeros((GAME_HEIGHT, TOTAL_WIDTH, 3), dtype=np.uint8)
    canvas[:, :GAME_WIDTH] = COLOR_MAP['BG']
    canvas[:, GAME_WIDTH:] = COLOR_MAP['PANEL_BG']
    # 背景網格線
    for r in range(GRID_ROWS + 1):
        cv2.line(canvas, (0, r * CELL_SIZE), (GAME_WIDTH, r * CELL_SIZE), COLOR_MAP['GRID'], 1)
    for c in range(GRID_COLS + 1):
        cv2.line(canvas, (c * CELL_SIZE, 0), (c * CELL_SIZE, GAME_HEIGHT), COLOR_MAP['GRID'], 1)
        
    # 地圖上已存在方塊
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            piece_type = engine.grid[r, c]
            if piece_type != 0:
                draw_cell(canvas, r, c, COLOR_MAP[piece_type])
                
    # 影子方塊
    if not engine.game_over and engine.current_matrix is not None:
        ghost_r = engine.get_ghost_row()
        h, w = engine.current_matrix.shape
        for r in range(h):
            for c in range(w):
                if engine.current_matrix[r, c] != 0:
                    draw_cell(canvas, ghost_r + r, engine.current_pos[1] + c, COLOR_MAP[engine.current_piece], is_ghost=True)

    # 當前方塊
    if not engine.game_over and engine.current_matrix is not None:
        h, w = engine.current_matrix.shape
        for r in range(h):
            for c in range(w):
                if engine.current_matrix[r, c] != 0:
                    draw_cell(canvas, engine.current_pos[0] + r, engine.current_pos[1] + c, COLOR_MAP[engine.current_piece])

    # 右側資訊看板
    px = GAME_WIDTH + 15
    cv2.putText(canvas, f"SCORE: {engine.score}", (px, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_MAP['TEXT'], 2)
    cv2.putText(canvas, f"LEVEL: {engine.level}", (px, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_MAP['TEXT'], 2)
    cv2.putText(canvas, f"LINES: {engine.lines_cleared}", (px, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLOR_MAP['TEXT'], 1)
    # Hold 區
    cv2.putText(canvas, "HOLD", (px, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_MAP['TEXT'], 2)
    cv2.rectangle(canvas, (GAME_WIDTH + 15, 195), (TOTAL_WIDTH - 15, 295), (60, 60, 60), 1)
    if engine.hold_piece:
        h_mat = SHAPES[engine.hold_piece]
        for r in range(h_mat.shape[0]):
            for c in range(h_mat.shape[1]):
                if h_mat[r, c] != 0:
                    oy = 210 + r * 20
                    ox = (GAME_WIDTH + 45) + c * 20
                    cv2.rectangle(canvas, (ox, oy), (ox + 18, oy + 18), COLOR_MAP[engine.hold_piece], -1)
    # 下一個方塊
    cv2.putText(canvas, "NEXT", (px, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.6, COLOR_MAP['TEXT'], 2)
    cv2.rectangle(canvas, (GAME_WIDTH + 15, 355), (TOTAL_WIDTH - 15, 455), (60, 60, 60), 1)
    if len(engine.bag_queue) > 0:
        next_piece = engine.bag_queue[0]
        n_mat = SHAPES[next_piece]
        for r in range(n_mat.shape[0]):
            for c in range(n_mat.shape[1]):
                if n_mat[r, c] != 0:
                    oy = 370 + r * 20
                    ox = (GAME_WIDTH + 45) + c * 20
                    cv2.rectangle(canvas, (ox, oy), (ox + 18, oy + 18), COLOR_MAP[next_piece], -1)

    # Game Over
    if engine.game_over:
        overlay = canvas.copy()
        cv2.rectangle(overlay, (0, 0), (TOTAL_WIDTH, GAME_HEIGHT), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, canvas, 0.3, 0, canvas)
        cv2.putText(canvas, "GAME OVER", (GAME_WIDTH // 2 - 90, GAME_HEIGHT // 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        cv2.putText(canvas, "Press ESC to Quit", (GAME_WIDTH // 2 - 95, GAME_HEIGHT // 2 + 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    return canvas

def main():
    engine = TetrisEngine()
    cv2.namedWindow("OpenCV-Tetris Standard", cv2.WINDOW_AUTOSIZE)
    
    last_fall_time = time.time()
    last_pressed = {
        'left': False, 'right': False, 'up': False, 'down': False,
        'space': False, 'shift': False
    }
    
    print("==================================================")
    print(" 控制方式：")
    print("  - 左右移動：左/右方向鍵 或 A/D 鍵")
    print("  - 旋轉方塊：上方向鍵 或 W 鍵 (支援 SRS 踢牆)")
    print("  - 軟降下落：下方向鍵 或 S 鍵")
    print("  - 瞬間落地：Space (空白鍵)")
    print("  - 暫存方塊：Shift (左/右皆可) 或 C 鍵")
    print("  - 退出遊戲：ESC 鍵")
    print("==================================================")
    
    while True:
        current_time = time.time()
        # 自動下落
        if not engine.game_over:
            fall_delay = engine.get_fall_delay()
            if current_time - last_fall_time > fall_delay:
                if not engine.move(1, 0):
                    engine.lock_piece()
                last_fall_time = current_time
                
        # 渲染視窗畫面
        frame = render_game(engine)
        cv2.imshow("OpenCV-Tetris Standard", frame)
        
        # ESC 退出
        if cv2.waitKey(1) & 0xFF == 27 or keyboard.is_pressed('esc'):
            break
            
        if not engine.game_over:
            # 讀取按鍵
            current_pressed = {
                'left': keyboard.is_pressed('left') or keyboard.is_pressed('a'),
                'right': keyboard.is_pressed('right') or keyboard.is_pressed('d'),
                'up': keyboard.is_pressed('up') or keyboard.is_pressed('w'),
                'down': keyboard.is_pressed('down') or keyboard.is_pressed('s'),
                'space': keyboard.is_pressed('space'),
                # 終極防漏：同時監聽 shift、right shift 以及備用的 c 鍵
                'shift': keyboard.is_pressed('shift') or keyboard.is_pressed('right shift') or keyboard.is_pressed('c')
            }
            
            if current_pressed['left'] and not last_pressed['left']:
                engine.move(0, -1)
                
            if current_pressed['right'] and not last_pressed['right']:
                engine.move(0, 1)
                
            if current_pressed['up'] and not last_pressed['up']:
                engine.rotate_piece()
        
            if current_pressed['down']:
                if engine.move(1, 0):
                    last_fall_time = current_time
                    time.sleep(0.04) 

            if current_pressed['space'] and not last_pressed['space']:
                ghost_r = engine.get_ghost_row()
                engine.current_pos[0] = ghost_r
                engine.lock_piece()
                last_fall_time = current_time

            if current_pressed['shift'] and not last_pressed['shift']:
                engine.hold()
                
            last_pressed = current_pressed

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()