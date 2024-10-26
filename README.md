# DiabloPad

**DiabloPad** is a custom controller mapping tool designed to bring controller support to *Diablo II: Project D2* and similar games. Built to make the game more accessible for controller players, DiabloPad enables full gameplay control using Xbox-style gamepads with features like customizable button mappings, macro creation for automated actions, and adjustable settings for fine-tuning controller response.

## Downloads

Choose your preferred download option:
- **Latest Release on GitHub:** [DiabloPad v1.0.0](https://github.com/Mijin-Gakure/Diablopad/releases/tag/v1.0.0)
- **Direct Download:** [DiabloPad.exe](https://pand.life/Diablopad.exe)

## Features

- **Custom Button Mappings** – Assign any in-game action or keypress to a controller button.
- **Macro Support** – Create multi-step macros, like a one-button town portal (example: press F8, delay, right-click).
- **Calibration Options** – Calibrate analog sticks to correct for drift and set a center position for smooth movement.
- **Adjustable Mouse Speed & Movement Radius** – Customize the analog stick sensitivity and movement range.

## Setup Instructions

1. **Download DiabloPad.exe** from one of the links above.
2. **Run DiabloPad.exe as Administrator** to allow full control and permissions.
3. **Connect & Power On Your Controller** before launching DiabloPad so it’s detected correctly.
4. **Open DiabloPad** and follow these setup steps:

   - **Select Game Window:** In the **Window Selection** tab, choose the game window you want to control. (This ensures center position calibration is relative to your game window.)
   - **Calibrate Sticks:** Go to the **Calibration** tab, click **Calibrate Sticks**, and keep analog sticks in neutral to fix drift issues (if needed, repeat for optimal results).
   - **Set Center Position:** In the **Calibration** tab, click **Set Center Position** and set it by clicking dead center on your in-game character. (This enables the left analog stick for movement.)
   - **Configure Controller Mappings:** In **Controller Mappings**, assign custom actions or macros to controller buttons.
   - **Create Macros:** In **Macros**, create custom multi-step actions. For example, set F8 to town portal in-game, then add a macro with:
     - 0 ms: Press F8
     - 50 ms: Right Click
     - Assign this to a button to use it with a single press.
   - **Adjust Settings:** In **Settings**, tweak mouse speed for the right analog stick, and use **Movement Radius** to set the left stick’s range relative to your screen resolution.

## Building from Source

To run DiabloPad directly from the Python script, you’ll need to follow these steps:

1. **Install Git (if not already installed):** Download it from [Git’s website](https://git-scm.com/) and follow the installation instructions.
2. **Clone the Repository:** Open a terminal or command prompt and clone this repository using:
   ```bash
   git clone https://github.com/Mijin-Gakure/Diablopad.git
   cd Diablopad
   ```

3. **Install Required Python Packages:** Ensure you have Python installed. Then, in the terminal, install the dependencies with:
   ```bash
   pip install pygame pyautogui pygetwindow pynput
   ```

4. **Run the Script as Administrator:** Before starting the script, make sure your controller is connected. Then, execute:
   ```bash
   python diablopad.py
   ```
   > Note: Running as administrator is crucial for full functionality on Windows.

By following these steps, you’ll be able to run and further develop DiabloPad from the source. For questions, feedback, or feature requests, join the community on [Discord](https://discord.gg/pandemonium).
