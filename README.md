UR10e Drawing

## Group Members

| Name                         |
| -----------------------------|
| *Vincent Amberger*           |
| *Mihai-Andrei Dancu*         | 
| *Mohamed Altorky*            | 
| *Valentín Magdalena Sánchez* |


## Quick‑Start

### Simulator 
1. Install RoboDK  and open `svg_drawing_ur10.rdk`.
2. The scene loads the UR10e with a dry erase marker and a virtual whiteboard.
3. Open `draw_TUM.py`/ `draw_circles.py` depending on what you want to draw
   * Modify the path of the input svg file to where you placed the files located in `svg/`. Alternatively, you can choose another svg file.
   * Adapt the virtual board size of the script:

     ```python
     BOARD_WIDTH  = 500   # mm
     BOARD_HEIGHT = 250   # mm
     ```
   * adjust `home_joints` to a collision‑free position
4. Confirm that the robot moves to *Home* and then traces the SVG paths in the simulator.
5. Generate a robot program to export the `.script` and `.urp` files.

<img width="1440" alt="Screenshot 2025-06-23 at 19 44 25" src="https://github.com/user-attachments/assets/a288369d-9f34-4199-8f54-54ebfe6f74a7" />

### UR10e Robot
1. Equip the robot with a dry erase marker and teach the tool center point (TCP)
2. Using the Teach Panel, move the robot to 3 new points on the board using the the origin-x-y method, which you define as targets in RoboDK. Then create a new plane in RoboDK using those 3 points and align the whiteboard with it. Now the physical and the simulated board are aligned.
3. Copy the `.urp` and `.script` files to a USB stick and upload them to the Teach Panel
4. Ensure the workspace is clear and either load the `.urp` file or start the `.script` file in the Program Tab of the Teach Panel to start the program.
5. Watch and enjoy.
   
<img width="1093" alt="Screenshot 2025-06-23 at 20 06 37" src="https://github.com/user-attachments/assets/adfc8a3f-48d3-42fb-bfb5-3fa1a56280bc" />

## Demonstration Video

### [Concentric circles](videos/concentric-circles-drawing.mp4)
<video src="videos/concentric-circles-drawing.mp4" controls width="640" preload="none"></video>

### [TUM-Logo](videos/TUM_drawing.mp4)
<video src="videos/TUM_drawing.mp4" controls width="640" preload="none"></video>
