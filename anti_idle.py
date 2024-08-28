import pyautogui
import time

limter = None


def work():
    start = time.time()
    iterationCount = 0
    try:
        while True:
            def_position = pyautogui.position()
            pyautogui.moveTo(def_position + (750, 850), duration=0)
            pyautogui.click(def_position + (250, 250), clicks=1, button='left')
            pyautogui.moveTo(def_position + (450, 450), duration=0)
            # time.sleep(0.5)
            pyautogui.moveTo(def_position)
            print(f"[{time.asctime()}] Pausing for 60sec")
            iterationCount += 1
            time.sleep(60)
            if limter and limter <= iterationCount:
                print("Limiter exit.")
                break
    except KeyboardInterrupt as x:
        print("Closing... Interupted by user.")
    except Exception as x:
        print(f"Closing.. -> {x}")

    end = time.time()
    ts = int(end - start)
    timespend = "N/A"
    if ts < 60:
        timespend = f"{ts}s"
    elif ts / 60 < 60:
        timespend = f"~{int(ts / 60)}m"
    else:
        timespend = f"~{int((ts / 60) / 60)}h"
    print(
        f"Software ran for {timespend} and had {iterationCount} {'iterations' if iterationCount > 1 else 'iteration'}")


if __name__ == "__main__":
    try:
        limter = int(input("Limit iterations?(enter ammount): "))
    except Exception as x:
        print(f"Failed to set limit: {x}")
        limter = None
    work()

