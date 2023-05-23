import time
import pyautogui
import psutil
from time import strftime
import logging

# Output file name
output_file_name = 'time_log.txt'
logging.basicConfig(filename=output_file_name, level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Image to be used for closing the game upon detection
# Take a screenshot of something unique and immediately visible (such as small galaxy icon on the bottom portion of the screen)
# Save it to the same folder as this script, or enter the full path below
close_image_path = 'close.png'

def check_process():
    process_running = False
    continue_searching_close_image = True
    stellaris_process = None

    while continue_searching_close_image:
        if not process_running:
            print("Waiting for Stellaris", end='\r')
            for proc in psutil.process_iter():
                if proc.name() == 'stellaris.exe':
                    stellaris_process = proc
                    break
            if stellaris_process is not None:
                start_time = time.perf_counter()
                process_running = True
                print("Process has started. Recording time. Please don't touch your mouse or keyboard!")
        else:
            gone, alive = psutil.wait_procs([stellaris_process], timeout=0)
            if gone:
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                logging.info(f"Elapsed time: {elapsed_time:.2f} seconds")
                print(f"Elapsed time of: {elapsed_time:.2f} seconds has been added to the time_log.txt!")
                process_running = False
                stellaris_process = None
        
        if continue_searching_close_image:
            close_image = pyautogui.locateOnScreen(close_image_path)
            if close_image is not None and stellaris_process is not None:
                stellaris_process.terminate()
        
        time.sleep(1)

if __name__ == '__main__':
    check_process()
