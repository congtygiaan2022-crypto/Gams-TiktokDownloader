import time
import logging

# Mock objects to simulate GemLogin and Selenium
class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")

logger = MockLogger()

class MockDriver:
    def __init__(self):
        self.window_handles = ["handle_main"]
        self.current_window_handle = "handle_main"
        self.current_url = "https://www.tiktok.com/@user"
    
    def execute_script(self, script, *args):
        if "window.open" in script:
            print("  -> Simulating window.open('')")
            self.window_handles.append(f"handle_new_{len(self.window_handles)}")
    
    def switch_to_window(self, handle):
        print(f"  -> Switching to {handle}")
        self.current_window_handle = handle

    def close(self):
        print(f"  -> Closing current window {self.current_window_handle}")
        self.window_handles.remove(self.current_window_handle)
        
    def get(self, url):
        self.current_url = url
        print(f"  -> Navigating to {url}")

class MockSwitchTo:
    def __init__(self, driver): self.driver = driver
    def window(self, handle): self.driver.switch_to_window(handle)

# The logic to be tested (Simplified version of scrape_channel)
def simulate_scrape_logic(driver):
    main_handle = driver.current_window_handle
    print(f"Initial Handle: {main_handle}")
    
    for i in range(2): # Simulate 2 videos
        print(f"\n--- Iteration {i+1} ---")
        
        # Simulating window open success
        driver.execute_script("window.open('');")
        
        # Wait logic (the one I implemented)
        new_tab_handle = None
        for _ in range(5):
            other_handles = [h for h in driver.window_handles if h != main_handle]
            if other_handles:
                new_tab_handle = other_handles[-1]
                break
            time.sleep(0.1)
        
        if not new_tab_handle:
            print("  !! ERROR: No new handle found")
            return
        
        driver.switch_to.window(new_tab_handle)
        driver.get("https://kituchat.net/...")
        
        # Simulation success and cleanup
        try:
            print("  -> Processing download...")
            if len(driver.window_handles) > 1:
                if driver.current_window_handle != main_handle:
                    driver.close()
                driver.switch_to.window(main_handle)
            else:
                print("  !! ERROR: Session lost (only 1 handle left)")
        except Exception as e:
            print(f"  !! Exception during tab cleanup: {e}")

if __name__ == "__main__":
    driver = MockDriver()
    driver.switch_to = MockSwitchTo(driver)
    
    print("Testing Normal Flow:")
    simulate_scrape_logic(driver)
    
    print("\n" + "="*20 + "\n")
    
    print("Testing Conflict/Race Condition simulation...")
    # Reset
    driver = MockDriver()
    driver.switch_to = MockSwitchTo(driver)
    # Simulate a scenario where window.open fails
    def fail_open(script): print("  -> Simulating FAILED window.open")
    driver.execute_script = fail_open
    
    simulate_scrape_logic(driver)
