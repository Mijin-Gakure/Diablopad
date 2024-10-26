import pygame
import pyautogui
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pygetwindow as gw
import sys
import math
import json
import os
from pynput.mouse import Controller as MouseController
import queue
import webbrowser

# Disable pyautogui's fail-safe (moving the mouse to a corner will not raise an exception)
pyautogui.FAILSAFE = False

# Set pyautogui pause to 0 for faster execution
pyautogui.PAUSE = 0

# Initialize pygame
pygame.init()
pygame.joystick.init()

# Check for joystick
if pygame.joystick.get_count() == 0:
    print("No joystick detected. Please connect an Xbox controller and try again.")
    sys.exit()

# Initialize the first joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Detected joystick: {joystick.get_name()}")

# Config file paths
CONFIG_FILE = 'controller_config.json'
MACROS_FILE = 'macros.json'

# Right stick configuration
RIGHT_STICK_X_AXIS = 2
RIGHT_STICK_Y_AXIS = 3
DEADZONE = 0.1

# Click interval in seconds
CLICK_INTERVAL = 0.1  # 100 milliseconds

# Mapping for buttons (These may vary depending on the controller and pygame's mapping)
BUTTON_MAPPING = {
    0: 'A',
    1: 'B', 
    2: 'X',
    3: 'Y',
    4: 'LB',
    5: 'RB',
    6: 'Back',
    7: 'Start',
    8: 'LeftThumb',
    9: 'RightThumb'
}

# Trigger axis mapping
TRIGGER_MAPPING = {
    4: 'LT',  # Left trigger axis
    5: 'RT'   # Right trigger axis
}

# Mapping for hats (DPad)
HAT_MAPPING = {
    (0, 1): 'DPad_Up',
    (0, -1): 'DPad_Down',
    (-1, 0): 'DPad_Left',
    (1, 0): 'DPad_Right',
    (0, 0): 'DPad_Center'
}

# Define possible actions
POSSIBLE_ACTIONS = ['nothing']

# Add mouse actions
mouse_actions = [
    'left_click',
    'right_click',
    'middle_click',
    'double_click',
    'mouse_wheel_up',
    'mouse_wheel_down'
]
POSSIBLE_ACTIONS.extend(mouse_actions)

# Add all keyboard keys as 'press_<key>'
for key in pyautogui.KEYBOARD_KEYS:
    POSSIBLE_ACTIONS.append(f'press_{key}')

# Default action mappings
DEFAULT_ACTIONS = {
    'A': 'nothing',
    'B': 'mouse_wheel_up',
    'X': 'press_k',
    'Y': 'press_i',
    'LB': 'press_ctrl',
    'RB': 'right_click',
    'LT': 'press_shift',
    'RT': 'press_space',
    'Back': 'press_n',
    'Start': 'press_escape',
    'LeftThumb': 'press_r',
    'RightThumb': 'nothing',
    'DPad_Up': 'press_n',
    'DPad_Down': 'press_tab',
    'DPad_Left': 'press_q',
    'DPad_Right': 'press_c'
}

def normalize(value, deadzone):
    if abs(value) < deadzone:
        return 0
    return value

class MacrosManager:
    def __init__(self, macros_file=MACROS_FILE):
        self.macros_file = macros_file
        self.macros = {}
        self.load_macros()

    def load_macros(self):
        if os.path.exists(self.macros_file):
            try:
                with open(self.macros_file, 'r') as f:
                    self.macros = json.load(f)
                print(f"Loaded macros: {list(self.macros.keys())}")
            except Exception as e:
                print(f"Error loading macros: {e}")
                self.macros = {}
        else:
            self.macros = {}
            self.save_macros()

    def save_macros(self):
        try:
            with open(self.macros_file, 'w') as f:
                json.dump(self.macros, f, indent=4)
            print("Macros saved successfully.")
        except Exception as e:
            print(f"Error saving macros: {e}")

    def add_macro(self, name, actions):
        self.macros[name] = actions
        self.save_macros()

    def delete_macro(self, name):
        if name in self.macros:
            del self.macros[name]
            self.save_macros()

    def get_macro(self, name):
        return self.macros.get(name, [])

    def get_all_macros(self):
        return list(self.macros.keys())

    def execute_macro(self, name):
        if name not in self.macros:
            print(f"Macro '{name}' not found.")
            return
        actions = self.macros[name]
        threading.Thread(target=self.run_macro, args=(actions,), daemon=True).start()

    def run_macro(self, actions):
        for action_step in actions:
            delay_ms = action_step.get('delay_ms', 0)
            action = action_step.get('action', 'nothing')
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)  # Delay before action
            if action == 'nothing':
                continue
            elif action == 'mouse_wheel_up':
                try:
                    pyautogui.scroll(100)  # Increased scroll amount
                    print("Scrolled mouse wheel up.")
                except Exception as e:
                    print(f"Error scrolling mouse wheel up: {e}")
            elif action == 'mouse_wheel_down':
                try:
                    pyautogui.scroll(-100)  # Increased scroll amount
                    print("Scrolled mouse wheel down.")
                except Exception as e:
                    print(f"Error scrolling mouse wheel down: {e}")
            elif action in ['left_click', 'right_click', 'middle_click', 'double_click']:
                try:
                    if action == 'left_click':
                        pyautogui.click(button='left')
                        print("Performed left mouse click.")
                    elif action == 'right_click':
                        pyautogui.click(button='right')
                        print("Performed right mouse click.")
                    elif action == 'middle_click':
                        pyautogui.click(button='middle')
                        print("Performed middle mouse click.")
                    elif action == 'double_click':
                        pyautogui.doubleClick()
                        print("Performed double mouse click.")
                except Exception as e:
                    print(f"Error performing mouse action '{action}': {e}")
            elif action.startswith('press_'):
                key = action.split('_', 1)[1]
                try:
                    pyautogui.press(key)
                    print(f"Pressed key '{key}'.")
                except Exception as e:
                    print(f"Error pressing key '{key}': {e}")
            else:
                print(f"Unknown action in macro: {action}")

class ControllerHandler:
    def __init__(self, gui, event_queue, macros_manager):
        self.actions = DEFAULT_ACTIONS.copy()
        self.running = True
        self.gui = gui
        self.event_queue = event_queue
        self.macros_manager = macros_manager

        # Selected game window title
        self.selected_window_title = None

        # Initialize movement coordinates
        self.x_center = 0
        self.y_center = 0
        self.movement_radius = 50
        self.movement_points = {}

        # Initialize is_active attribute
        self.is_active = False

        # Mouse movement settings
        self.mouse_speed = 15
        self.mouse = MouseController()
        
        # Left stick state
        self.left_stick_active = False
        self.click_thread = None
        self.click_thread_running = False
        self.click_lock = threading.Lock()

        # Sets to track pressed buttons and keys
        self.pressed_buttons = set()
        self.pressed_keys = set()

        # Drift Correction Variables
        self.left_stick_neutral_x = 0.0  # Neutral position for left stick X
        self.left_stick_neutral_y = 0.0  # Neutral position for left stick Y
        self.right_stick_neutral_x = 0.0  # Neutral position for right stick X
        self.right_stick_neutral_y = 0.0  # Neutral position for right stick Y

        # Load saved configuration
        try:
            self.load_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.movement_points = {}

        # Start threads
        self.event_thread = threading.Thread(target=self.controller_event_loop, daemon=True)
        self.event_thread.start()

        self.window_monitor_thread = threading.Thread(target=self.window_monitor_loop, daemon=True)
        self.window_monitor_thread.start()

    def save_config(self):
        config = {
            'x_center': self.x_center,
            'y_center': self.y_center,
            'movement_radius': self.movement_radius,
            'mouse_speed': self.mouse_speed,
            'window_title': self.selected_window_title,
            'actions': self.actions,
            # Save Neutral Stick Positions for Drift Correction
            'left_stick_neutral_x': self.left_stick_neutral_x,
            'left_stick_neutral_y': self.left_stick_neutral_y,
            'right_stick_neutral_x': self.right_stick_neutral_x,
            'right_stick_neutral_y': self.right_stick_neutral_y
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            self.x_center = config.get('x_center', self.x_center)
            self.y_center = config.get('y_center', self.y_center)
            self.movement_radius = config.get('movement_radius', self.movement_radius)
            self.mouse_speed = config.get('mouse_speed', self.mouse_speed)
            self.selected_window_title = config.get('window_title', self.selected_window_title)
            self.actions.update(config.get('actions', {}))
            # Load Neutral Stick Positions
            self.left_stick_neutral_x = config.get('left_stick_neutral_x', 0.0)
            self.left_stick_neutral_y = config.get('left_stick_neutral_y', 0.0)
            self.right_stick_neutral_x = config.get('right_stick_neutral_x', 0.0)
            self.right_stick_neutral_y = config.get('right_stick_neutral_y', 0.0)
            if self.x_center and self.y_center:
                self.init_movement_coords(use_saved=True)

    def init_movement_coords(self, use_saved=False):
        if not use_saved and self.selected_window_title:
            try:
                window = gw.getWindowsWithTitle(self.selected_window_title)[0]
                if window.isMinimized:
                    window.restore()
                    time.sleep(0.5)
                left, top, width, height = window.left, window.top, window.width, window.height
                self.x_center = left + width // 2
                self.y_center = top + height // 2
            except Exception as e:
                print(f"Error initializing coordinates: {e}")
                return

        # Generate 360-degree movement points
        self.movement_points = {}
        for angle in range(0, 360, 10):
            rad = math.radians(angle)
            x = self.x_center + int(self.movement_radius * math.cos(rad))
            y = self.y_center + int(self.movement_radius * math.sin(rad))
            self.movement_points[angle] = (x, y)

        self.save_config()

    def get_movement_position(self, x_val, y_val):
        if abs(x_val) < DEADZONE and abs(y_val) < DEADZONE:
            return None
            
        angle = math.degrees(math.atan2(y_val, x_val))
        if angle < 0:
            angle += 360

        closest_angle = min(self.movement_points.keys(), 
                          key=lambda k: abs((k - angle + 180) % 360 - 180))
        return self.movement_points[closest_angle]

    def window_monitor_loop(self):
        while self.running:
            if self.selected_window_title:
                active_window = gw.getActiveWindow()
                if active_window and self.selected_window_title.lower() in active_window.title.lower():
                    self.is_active = True
                else:
                    self.is_active = False
            else:
                self.is_active = False
            time.sleep(0.5)

    def controller_event_loop(self):
        while self.running:
            if self.is_active:
                pygame.event.pump()

                # Handle right stick with Drift Correction
                right_x_raw = joystick.get_axis(RIGHT_STICK_X_AXIS)
                right_y_raw = joystick.get_axis(RIGHT_STICK_Y_AXIS)

                # Apply Drift Correction by subtracting neutral positions
                axis_x = normalize(right_x_raw - self.right_stick_neutral_x, DEADZONE)
                axis_y = normalize(right_y_raw - self.right_stick_neutral_y, DEADZONE)
                
                if abs(axis_x) > 0 or abs(axis_y) > 0:
                    move_x = axis_x * self.mouse_speed
                    move_y = axis_y * self.mouse_speed
                    self.mouse.move(move_x, move_y)
                    # Debugging
                    print(f"Mouse moved by ({move_x}, {move_y})")

                # Handle left stick with Drift Correction
                left_x_raw = joystick.get_axis(0)
                left_y_raw = joystick.get_axis(1)

                adjusted_left_x = left_x_raw - self.left_stick_neutral_x
                adjusted_left_y = left_y_raw - self.left_stick_neutral_y

                x_val = normalize(adjusted_left_x, DEADZONE)
                y_val = normalize(adjusted_left_y, DEADZONE)
                
                if abs(x_val) >= DEADZONE or abs(y_val) >= DEADZONE:
                    if not self.left_stick_active:
                        self.left_stick_active = True
                        print("Left stick activated.")
                        self.start_clicking()
                    
                    target_pos = self.get_movement_position(x_val, y_val)
                    if target_pos:
                        try:
                            pyautogui.moveTo(target_pos[0], target_pos[1])
                            print(f"Moved mouse to {target_pos}")
                        except Exception as e:
                            print(f"Error moving mouse: {e}")
                else:
                    if self.left_stick_active:
                        self.left_stick_active = False
                        print("Left stick released.")
                        self.stop_clicking()
                        try:
                            pyautogui.moveTo(self.x_center, self.y_center)
                            print(f"Moved mouse back to center ({self.x_center}, {self.y_center})")
                        except Exception as e:
                            print(f"Error moving mouse to center: {e}")

                # Handle triggers
                for axis, trigger in TRIGGER_MAPPING.items():
                    trigger_value = joystick.get_axis(axis)
                    # Apply Drift Correction for triggers if necessary
                    if trigger_value > 0:  # Trigger pressed
                        self.perform_action(self.actions.get(trigger, 'nothing'), pressed=True)
                        self.event_queue.put(('press', trigger))
                    else:  # Trigger released
                        self.perform_action(self.actions.get(trigger, 'nothing'), pressed=False)
                        self.event_queue.put(('release', trigger))

                # Handle other events
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        self.handle_button(event.button)
                    elif event.type == pygame.JOYBUTTONUP:
                        self.handle_button_release(event.button)
                    elif event.type == pygame.JOYHATMOTION:
                        self.handle_hat(event.value)

                # After handling all events, check if any buttons are pressed or left stick is active
                if not self.pressed_buttons and not self.left_stick_active:
                    self.release_all_keys()
                    self.stop_clicking()
            else:
                # Ensure that clicking is stopped if the controller is not active
                if self.left_stick_active:
                    self.left_stick_active = False
                    print("Controller inactive. Stopping clicking.")
                    self.stop_clicking()
                    try:
                        pyautogui.moveTo(self.x_center, self.y_center)
                        print(f"Moved mouse back to center ({self.x_center}, {self.y_center})")
                    except Exception as e:
                        print(f"Error moving mouse to center: {e}")
                # Additionally, release all keys if controller becomes inactive
                self.release_all_keys()

            time.sleep(0.01)

    def start_clicking(self):
        with self.click_lock:
            if not self.click_thread_running:
                self.click_thread_running = True
                self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
                self.click_thread.start()
                print("Started clicking thread.")

    def stop_clicking(self):
        with self.click_lock:
            if self.click_thread_running:
                self.click_thread_running = False
                if self.click_thread is not None:
                    self.click_thread.join()
                    self.click_thread = None
                print("Stopped clicking thread.")

    def click_loop(self):
        while self.click_thread_running and self.left_stick_active:
            try:
                pyautogui.click(button='left')
                print("Performed left mouse click.")
            except Exception as e:
                print(f"Error performing left mouse click: {e}")
            time.sleep(CLICK_INTERVAL)

    def handle_button(self, button):
        button_name = BUTTON_MAPPING.get(button, 'unknown')
        action_name = self.actions.get(button_name, 'nothing')
        self.pressed_buttons.add(button_name)
        self.perform_action(action_name, pressed=True)
        # Send event to GUI
        self.event_queue.put(('press', button_name))

    def handle_button_release(self, button):
        button_name = BUTTON_MAPPING.get(button, 'unknown')
        action_name = self.actions.get(button_name, 'nothing')
        self.pressed_buttons.discard(button_name)
        self.perform_action(action_name, pressed=False)
        # Send event to GUI
        self.event_queue.put(('release', button_name))

    def handle_hat(self, value):
        hat_name = HAT_MAPPING.get(value, 'DPad_Center')
        action_name = self.actions.get(hat_name, 'nothing')
        if hat_name != 'DPad_Center':
            self.pressed_buttons.add(hat_name)
            self.perform_action(action_name, pressed=True)
            self.event_queue.put(('press', hat_name))
        else:
            self.pressed_buttons.discard(hat_name)
            self.perform_action(action_name, pressed=False)
            self.event_queue.put(('release', hat_name))

    def perform_action(self, action, pressed=True):
        if action == 'nothing':
            return
        elif action == 'mouse_wheel_up':
            if pressed:
                try:
                    pyautogui.scroll(100)  # Increased scroll amount
                    print("Scrolled mouse wheel up.")
                except Exception as e:
                    print(f"Error scrolling mouse wheel up: {e}")
        elif action == 'mouse_wheel_down':
            if pressed:
                try:
                    pyautogui.scroll(-100)  # Increased scroll amount
                    print("Scrolled mouse wheel down.")
                except Exception as e:
                    print(f"Error scrolling mouse wheel down: {e}")
        elif action in ['left_click', 'right_click', 'middle_click', 'double_click']:
            try:
                if pressed:
                    if action == 'left_click':
                        pyautogui.click(button='left')
                        print("Performed left mouse click.")
                    elif action == 'right_click':
                        pyautogui.click(button='right')
                        print("Performed right mouse click.")
                    elif action == 'middle_click':
                        pyautogui.click(button='middle')
                        print("Performed middle mouse click.")
                    elif action == 'double_click':
                        pyautogui.doubleClick()
                        print("Performed double mouse click.")
            except Exception as e:
                print(f"Error performing mouse action '{action}': {e}")
        elif action.startswith('press_'):
            key = action.split('_', 1)[1]
            try:
                if pressed:
                    pyautogui.keyDown(key)
                    self.pressed_keys.add(key)
                    print(f"Key '{key}' pressed down.")
                else:
                    pyautogui.keyUp(key)
                    self.pressed_keys.discard(key)
                    print(f"Key '{key}' released.")
            except Exception as e:
                print(f"Error performing key action '{action}': {e}")
        elif action.startswith('macro:'):
            macro_name = action.split(':', 1)[1]
            print(f"Executing macro '{macro_name}'.")
            self.macros_manager.execute_macro(macro_name)
        else:
            print(f"Unknown action: {action}")

    def release_all_keys(self):
        keys_to_release = list(self.pressed_keys)
        for key in keys_to_release:
            try:
                pyautogui.keyUp(key)
                print(f"Key '{key}' released.")
                self.pressed_keys.discard(key)
            except Exception as e:
                print(f"Error releasing key '{key}': {e}")

    def calibrate_sticks(self):
        """
        Calibrate the neutral positions of both left and right sticks.
        """
        print("Starting stick calibration...")
        # Wait a short moment to ensure user is ready
        time.sleep(0.5)
        # Read current stick positions
        self.left_stick_neutral_x = joystick.get_axis(0)
        self.left_stick_neutral_y = joystick.get_axis(1)
        self.right_stick_neutral_x = joystick.get_axis(RIGHT_STICK_X_AXIS)
        self.right_stick_neutral_y = joystick.get_axis(RIGHT_STICK_Y_AXIS)
        # Save the calibrated neutral positions
        self.save_config()
        print("Stick calibration completed.")

    def stop(self):
        self.running = False
        self.stop_clicking()
        self.release_all_keys()
        # Release any pressed keys
        keys = ['shift', 'ctrl']
        for key in keys:
            try:
                pyautogui.keyUp(key)
                print(f"Key '{key}' released on stop.")
            except Exception as e:
                print(f"Error releasing key '{key}' on stop: {e}")

class ControllerGUI:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.macros_manager = MacrosManager()
        self.handler = ControllerHandler(self, self.event_queue, self.macros_manager)
        self.root = tk.Tk()
        self.root.title("Controller Configuration")
        self.root.geometry("800x1000")  # Increased height for more mappings

        self.mapping_rows = {}
        self.comboboxes = {}  # To store combobox references
        self.default_bg = None  # To store default background color

        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.process_event_queue()

    def create_widgets(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both')

        # Create tabs
        tab_mappings = ttk.Frame(notebook)
        tab_calibration = ttk.Frame(notebook)
        tab_window = ttk.Frame(notebook)
        tab_settings = ttk.Frame(notebook)
        tab_macros = ttk.Frame(notebook)  # Macros tab
        tab_info = ttk.Frame(notebook)     # Info tab

        notebook.add(tab_mappings, text='Controller Mappings')
        notebook.add(tab_calibration, text='Calibration')
        notebook.add(tab_window, text='Window Selection')
        notebook.add(tab_settings, text='Settings')
        notebook.add(tab_macros, text='Macros')  # Add Macros tab
        notebook.add(tab_info, text='Info')      # Add Info tab

        # Controller Mappings Section
        ttk.Label(tab_mappings, text="Button Mappings:", font=('Arial', 14, 'bold')).pack(pady=10)

        self.vars = {}
        frame = tk.Frame(tab_mappings)
        frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Add a scrollbar for mappings
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Populate mappings
        self.update_possible_actions()  # Update POSSIBLE_ACTIONS with macros

        for button_name in sorted(DEFAULT_ACTIONS.keys()):
            row = tk.Frame(scrollable_frame)
            row.pack(fill='x', pady=2, padx=5)
            label = tk.Label(row, text=button_name, width=20, anchor='w', bg='SystemButtonFace')
            label.pack(side='left')
            var = tk.StringVar(value=self.handler.actions.get(button_name, 'nothing'))
            self.vars[button_name] = var
            combo = ttk.Combobox(row, textvariable=var, values=POSSIBLE_ACTIONS, state='readonly')
            combo.pack(side='right', expand=True, fill='x')
            # Store reference to label for highlighting
            self.mapping_rows[button_name] = label
            # Store combobox reference
            self.comboboxes[button_name] = combo

        ttk.Button(tab_mappings, text='Save Mappings', command=self.save_mappings).pack(pady=10)
        ttk.Button(tab_mappings, text='Reset to Default', command=self.reset_mappings).pack(pady=5)

        # Calibration Section
        ttk.Label(tab_calibration, text="Calibration:", font=('Arial', 14, 'bold')).pack(pady=10)

        # Center Position Calibration
        ttk.Button(tab_calibration, text='Set Center Position', 
                  command=self.set_center_position).pack(pady=5)
        self.center_status = ttk.Label(tab_calibration, text="Center Position: Not set")
        self.center_status.pack()

        # Movement Radius Setting
        ttk.Label(tab_calibration, text="Movement Radius:", font=('Arial', 12)).pack(pady=5)
        self.radius_var = tk.IntVar(value=self.handler.movement_radius)
        radius_scale = ttk.Scale(tab_calibration, from_=20, to=200, 
                               variable=self.radius_var, orient='horizontal')
        radius_scale.pack(fill='x', padx=20)

        def update_radius(*args):
            self.handler.movement_radius = self.radius_var.get()
            if self.handler.x_center and self.handler.y_center:
                self.handler.init_movement_coords(use_saved=True)
        self.radius_var.trace('w', update_radius)

        ttk.Button(tab_calibration, text='Save Calibration', 
                  command=self.save_calibration).pack(pady=20)

        # **Added: Stick Calibration Section**
        ttk.Label(tab_calibration, text="Drift Correction (Stick Calibration):", font=('Arial', 14, 'bold')).pack(pady=10)

        ttk.Button(tab_calibration, text='Calibrate Sticks', command=self.calibrate_sticks).pack(pady=5)
        self.stick_calibration_status = ttk.Label(tab_calibration, text="Stick Calibration: Not done")
        self.stick_calibration_status.pack()

        # Settings Section
        ttk.Label(tab_settings, text="Mouse Speed:", font=('Arial', 12)).pack(pady=5)
        self.mouse_speed_var = tk.IntVar(value=self.handler.mouse_speed)
        mouse_speed_scale = ttk.Scale(tab_settings, from_=1, to=50, 
                                    variable=self.mouse_speed_var, orient='horizontal')
        mouse_speed_scale.pack(fill='x', padx=20)
        
        def update_mouse_speed(*args):
            self.handler.mouse_speed = self.mouse_speed_var.get()
            self.handler.save_config()
        self.mouse_speed_var.trace('w', update_mouse_speed)

        # Window Selection Section
        ttk.Label(tab_window, text="Window Selection:", font=('Arial', 14, 'bold')).pack(pady=10)

        self.window_var = tk.StringVar()
        self.window_dropdown = ttk.Combobox(tab_window, textvariable=self.window_var, 
                                          values=self.get_window_titles(), state='readonly', width=50)
        self.window_dropdown.pack(pady=5)
        self.window_dropdown.set("Select Window")

        ttk.Button(tab_window, text='Select Window', command=self.select_window).pack(pady=10)
        ttk.Button(tab_window, text='Refresh Window List', 
                  command=self.update_window_list).pack(pady=5)

        # **Added: Macros Section**
        ttk.Label(tab_macros, text="Macros:", font=('Arial', 14, 'bold')).pack(pady=10)

        # Listbox to display macros
        self.macros_listbox = tk.Listbox(tab_macros)
        self.macros_listbox.pack(padx=10, pady=10, fill='both', expand=True)

        # Buttons for Macros
        btn_frame = tk.Frame(tab_macros)
        btn_frame.pack(pady=5)

        ttk.Button(btn_frame, text='Create New Macro', command=self.create_new_macro).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Edit Selected Macro', command=self.edit_selected_macro).pack(side='left', padx=5)
        ttk.Button(btn_frame, text='Delete Selected Macro', command=self.delete_selected_macro).pack(side='left', padx=5)

        self.refresh_macros_list()

        # **Added: Info Section**
        ttk.Label(tab_info, text="Info", font=('Arial', 14, 'bold')).pack(pady=10)

        info_frame = tk.Frame(tab_info)
        info_frame.pack(padx=10, pady=10, fill='both', expand=True)

        # Main Message
        main_message = (
            "This script was made by me (Mijin) for my wife Wembley so she could play PD2 with me since she "
            "refuses to play games without a controller. I decided to upload it for anyone to use if they like. "
            "I may or may not add more features later. If someone is really interested in features being added, "
            "you could always donate XD. If you have any questions, feel free to reach out on my Discord server. "
        )
        label_main = tk.Label(info_frame, text=main_message, wraplength=750, justify='left', anchor='w')
        label_main.pack(anchor='w')

        # Donation Link
        donation_url = "https://www.paypal.com/donate/?hosted_button_id=Q5ZQGAEFVTZAE"
        discord_url = "https://discord.gg/pandemonium"

        def open_donation_link(event):
            webbrowser.open_new(donation_url)

        def open_discord_link(event):
            webbrowser.open_new(discord_url)    

        # Donation Label
        donation_label = tk.Label(info_frame, text="Donate via Paypal", fg="blue", cursor="hand2", font=('Arial', 10, 'underline'))
        donation_label.pack(anchor='w')
        donation_label.bind("<Button-1>", open_donation_link)

        # Discord Label
        discord_label = tk.Label(info_frame, text="Discord Server", fg="blue", cursor="hand2", font=('Arial', 10, 'underline'))
        discord_label.pack(anchor='w')
        discord_label.bind("<Button-1>", open_discord_link)

        # Instructions Label
        instructions_title = tk.Label(info_frame, text="Instructions:", font=('Arial', 12, 'bold'))
        instructions_title.pack(pady=(10,0), anchor='w', padx=10)

        instructions = (
            "1. Select Game Window: Navigate to the [Window Selection] tab and choose the game window you want to control. "
            "This ensures that the center position calibrates correctly relative to your game window.\n\n"
            "2. Calibrate Sticks: Go to the [Calibration] tab and click on [Calibrate Sticks] while keeping both analog sticks in their neutral positions. "
            "This helps address controller drift, a common issue. You may need to calibrate multiple times for optimal results.\n\n"
            "3. Set Center Position: In the [Calibration] tab, click on [Set Center Position]. Move your mouse to the center position and confirm. "
            "This sets the left analog stick for movement. Ensure that you've selected the game window first, then click dead center on your character in the game.\n\n"
            "4. Configure Controller Mappings: Navigate to the [Controller Mappings] tab to assign actions or macros to your controller buttons.\n\n"
            "5. Create Macros: In the [Macros] tab, create custom macros. For example, set F8 to perform a town portal in-game, then create a macro with:\n"
            "   - 0 ms: Press F8\n"
            "   - 50 ms: Right Click\n"
            "   Bind this macro to a controller button to open a portal with a single press.\n\n"
            "6. Adjust Settings: Go to the [Settings] tab to adjust the mouse speed, which controls how fast the right analog stick moves the mouse.\n\n"
            "7. Movement Radius Slider: In the [Calibration] tab, adjust the [Movement Radius] slider to define how far the left analog stick pulls away from the center of your character. "
            "This may need to be adjusted based on your screen resolution for precise movement."
        )
        instructions_label = tk.Label(info_frame, text=instructions, justify='left', anchor='w', wraplength=750)
        instructions_label.pack(anchor='w', padx=10, pady=(0,10))

    def update_possible_actions(self):
        # Clear existing macros from POSSIBLE_ACTIONS and re-add
        global POSSIBLE_ACTIONS
        # Remove any existing macro entries
        POSSIBLE_ACTIONS = [action for action in POSSIBLE_ACTIONS if not action.startswith('macro:')]
        # Add macros from MacrosManager
        for macro in self.macros_manager.get_all_macros():
            macro_action = f'macro:{macro}'
            POSSIBLE_ACTIONS.append(macro_action)
        print(f"Possible actions updated with macros: {POSSIBLE_ACTIONS}")

        # Update all comboboxes' values
        for combo in self.comboboxes.values():
            current_value = combo.get()
            combo['values'] = POSSIBLE_ACTIONS
            # If the current value is a macro and it's been deleted, set to 'nothing'
            if current_value.startswith('macro:') and current_value[6:] not in self.macros_manager.macros:
                combo.set('nothing')

    def refresh_macros_list(self):
        self.macros_listbox.delete(0, tk.END)
        for macro in self.macros_manager.get_all_macros():
            self.macros_listbox.insert(tk.END, macro)

    def create_new_macro(self):
        # Dialog to get macro name
        macro_name = simpledialog.askstring("Macro Name", "Enter a name for the new macro:")
        if not macro_name:
            return
        if macro_name in self.macros_manager.get_all_macros():
            messagebox.showerror("Error", "A macro with this name already exists.")
            return

        # Create a new window to build the macro
        macro_window = tk.Toplevel(self.root)
        macro_window.title(f"Create Macro: {macro_name}")
        macro_window.geometry("400x450")

        ttk.Label(macro_window, text=f"Building Macro: {macro_name}", font=('Arial', 12, 'bold')).pack(pady=10)

        instructions = tk.Label(macro_window, text="Each action will be executed after the specified delay (in milliseconds).", wraplength=380, justify='left')
        instructions.pack(pady=5)

        actions = []

        def add_action(action_data=None):
            frame = tk.Frame(macro_window)
            frame.pack(pady=5, padx=10, fill='x')

            delay_label = tk.Label(frame, text="Delay (ms):")
            delay_label.pack(side='left')
            delay_entry = tk.Entry(frame, width=10)
            delay_entry.pack(side='left', padx=5)
            if action_data:
                delay_entry.insert(0, str(action_data.get('delay_ms', '')))

            action_label = tk.Label(frame, text="Action:")
            action_label.pack(side='left', padx=(10,0))
            action_var = tk.StringVar(value='nothing')
            action_combo = ttk.Combobox(frame, textvariable=action_var, values=POSSIBLE_ACTIONS, state='readonly', width=20)
            action_combo.pack(side='left', padx=5)
            if action_data:
                action_combo.set(action_data.get('action', 'nothing'))

            remove_button = ttk.Button(frame, text="Remove", command=lambda: remove_action(frame, action_step))
            remove_button.pack(side='left', padx=5)

            action_step = {'delay_entry': delay_entry, 'action_var': action_var}
            actions.append(action_step)

        def remove_action(frame, action_step):
            frame.destroy()
            actions.remove(action_step)

        def save_macro():
            macro_actions = []
            for idx, action_step in enumerate(actions, start=1):
                delay = action_step['delay_entry'].get()
                action = action_step['action_var'].get()
                if not delay.isdigit():
                    messagebox.showerror("Error", f"Delay for action {idx} must be a number in milliseconds.")
                    return
                macro_actions.append({'delay_ms': int(delay), 'action': action})
            self.macros_manager.add_macro(macro_name, macro_actions)
            self.update_possible_actions()
            self.refresh_macros_list()
            messagebox.showinfo("Success", f"Macro '{macro_name}' has been created.")
            macro_window.destroy()

        ttk.Button(macro_window, text="Add Action", command=add_action).pack(pady=5)
        ttk.Button(macro_window, text="Save Macro", command=save_macro).pack(pady=5)

    def edit_selected_macro(self):
        selection = self.macros_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No macro selected.")
            return
        macro_name = self.macros_listbox.get(selection[0])

        # Retrieve existing macro actions
        existing_actions = self.macros_manager.get_macro(macro_name)

        # Create a window to edit the macro
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"Edit Macro: {macro_name}")
        edit_window.geometry("400x450")

        ttk.Label(edit_window, text=f"Editing Macro: {macro_name}", font=('Arial', 12, 'bold')).pack(pady=10)

        instructions = tk.Label(edit_window, text="Each action will be executed after the specified delay (in milliseconds).", wraplength=380, justify='left')
        instructions.pack(pady=5)

        actions = []

        def add_action(action_data=None):
            frame = tk.Frame(edit_window)
            frame.pack(pady=5, padx=10, fill='x')

            delay_label = tk.Label(frame, text="Delay (ms):")
            delay_label.pack(side='left')
            delay_entry = tk.Entry(frame, width=10)
            delay_entry.pack(side='left', padx=5)
            if action_data:
                delay_entry.insert(0, str(action_data.get('delay_ms', '')))

            action_label = tk.Label(frame, text="Action:")
            action_label.pack(side='left', padx=(10,0))
            action_var = tk.StringVar(value='nothing')
            action_combo = ttk.Combobox(frame, textvariable=action_var, values=POSSIBLE_ACTIONS, state='readonly', width=20)
            action_combo.pack(side='left', padx=5)
            if action_data:
                action_combo.set(action_data.get('action', 'nothing'))

            remove_button = ttk.Button(frame, text="Remove", command=lambda: remove_action(frame, action_step))
            remove_button.pack(side='left', padx=5)

            action_step = {'delay_entry': delay_entry, 'action_var': action_var}
            actions.append(action_step)

        def remove_action(frame, action_step):
            frame.destroy()
            actions.remove(action_step)

        def save_edits():
            macro_actions = []
            for idx, action_step in enumerate(actions, start=1):
                delay = action_step['delay_entry'].get()
                action = action_step['action_var'].get()
                if not delay.isdigit():
                    messagebox.showerror("Error", f"Delay for action {idx} must be a number in milliseconds.")
                    return
                macro_actions.append({'delay_ms': int(delay), 'action': action})
            self.macros_manager.add_macro(macro_name, macro_actions)
            self.update_possible_actions()
            self.refresh_macros_list()
            messagebox.showinfo("Success", f"Macro '{macro_name}' has been updated.")
            edit_window.destroy()

        # Populate existing actions
        for action_data in existing_actions:
            add_action(action_data)

        ttk.Button(edit_window, text="Add Action", command=lambda: add_action()).pack(pady=5)
        ttk.Button(edit_window, text="Save Changes", command=save_edits).pack(pady=5)

    def delete_selected_macro(self):
        selection = self.macros_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No macro selected.")
            return
        macro_name = self.macros_listbox.get(selection[0])
        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete macro '{macro_name}'?")
        if confirm:
            self.macros_manager.delete_macro(macro_name)
            self.update_possible_actions()
            self.refresh_macros_list()
            messagebox.showinfo("Deleted", f"Macro '{macro_name}' has been deleted.")

    def set_center_position(self):
        self.root.withdraw()
        time.sleep(0.2)
        
        messagebox.showinfo("Calibration", 
                          "Move your mouse to the center position and press OK.")

        pos = pyautogui.position()
        self.handler.x_center = pos[0]
        self.handler.y_center = pos[1]
        self.handler.init_movement_coords(use_saved=True)

        self.center_status.config(text=f"Center Position: {pos}")
        self.root.deiconify()
        messagebox.showinfo("Calibration", "Center position calibrated.")

    def set_region(self, region_name):
        # Removed image recognition region setting as per user instruction
        pass

    def get_window_titles(self):
        windows = gw.getAllTitles()
        return [title for title in windows if 'game.exe' in title.lower() or 'diablo ii' in title.lower()]

    def update_window_list(self):
        self.window_dropdown['values'] = self.get_window_titles()

    def select_window(self):
        selected_title = self.window_var.get()
        if not selected_title:
            messagebox.showerror("Selection Error", "No window selected.")
            return
        self.handler.selected_window_title = selected_title
        self.handler.init_movement_coords()
        messagebox.showinfo("Window Selected", f"Selected window: {selected_title}")

    def save_calibration(self):
        if self.handler.x_center and self.handler.y_center:
            self.handler.save_config()
            messagebox.showinfo("Calibration Saved", "Calibration has been saved successfully.")
        else:
            messagebox.showerror("Calibration Incomplete", "Please set the center position before saving calibration.")

    def save_mappings(self):
        for button_name, var in self.vars.items():
            self.handler.actions[button_name] = var.get()
        self.handler.save_config()
        messagebox.showinfo("Mappings Saved", "Controller mappings have been saved.")
        self.update_possible_actions()  # Update actions in Comboboxes

    def reset_mappings(self):
        self.handler.actions = DEFAULT_ACTIONS.copy()
        for button_name, var in self.vars.items():
            var.set(self.handler.actions[button_name])
        self.handler.save_config()
        messagebox.showinfo("Mappings Reset", "Controller mappings have been reset to default.")
        self.update_possible_actions()  # Update actions in Comboboxes

    def calibrate_sticks(self):
        """
        Initiates the stick calibration process.
        """
        self.root.withdraw()
        time.sleep(0.2)
        
        messagebox.showinfo("Stick Calibration", 
                          "Keep both analog sticks in their neutral positions and click OK to calibrate.")
        
        self.handler.calibrate_sticks()
        self.stick_calibration_status.config(text="Stick Calibration: Completed")
        self.root.deiconify()
        messagebox.showinfo("Calibration", "Stick calibration completed successfully.")

    def on_close(self):
        self.handler.stop()
        self.root.quit()
        self.root.destroy()

    def highlight_mapping(self, button_name):
        label = self.mapping_rows.get(button_name)
        if label:
            label.configure(bg='yellow')

    def unhighlight_mapping(self, button_name):
        label = self.mapping_rows.get(button_name)
        if label:
            label.configure(bg=self.default_bg or 'SystemButtonFace')

    def process_event_queue(self):
        try:
            while True:
                event, button_name = self.event_queue.get_nowait()
                if event == 'press':
                    self.highlight_mapping(button_name)
                elif event == 'release':
                    self.unhighlight_mapping(button_name)
        except queue.Empty:
            pass
        # Schedule next check
        self.root.after(100, self.process_event_queue)

def main():
    gui = ControllerGUI()
    try:
        gui.root.mainloop()
    except KeyboardInterrupt:
        gui.handler.stop()

if __name__ == '__main__':
    main()
