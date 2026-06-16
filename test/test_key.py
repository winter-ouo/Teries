# key_test.py
import keyboard

def main():
    print("====================  測試用  ====================")
    print(" ")
    print(" 請直接按下鍵盤任意鍵（例如：Shift, S, 方向鍵...）")
    print(" 畫面會即時顯示該按鍵的『文字名稱』與『底層數字編號』。")
    print(" 想要結束測試，請按下 [ESC] 鍵。")
    print("==================================================")
    
    # 監聽鍵盤
    while True:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            print(f"偵測到按鍵 -> 名稱: {event.name:<10} | 底層數字(Scan Code): {event.scan_code}")
            if event.name == 'esc':
                print("測試結束！")
                break

if __name__ == "__main__":
    main()