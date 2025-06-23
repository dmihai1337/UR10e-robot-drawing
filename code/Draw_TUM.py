from robodk import robolink, robomath, robodialogs
import os
import urllib.request

robolink.import_install('svgpathtools')
import svgpathtools as spt

#-------------------------------------------
# Settings
# IMAGE_FILE = "https://robodk.com/files/upload/robodk-logo.svg"  # Leave this empty ("") to prompt a file explorer
IMAGE_FILE = "C:/Users/moham/Desktop/IMPL/TUM.svg"

BOARD_WIDTH, BOARD_HEIGHT = 500, 250  # Size of the image. The image will be scaled keeping its aspect ratio
BOARD_BACKGROUND_COLOR = [0, 0, 0, 1]  # Background of the drawing board (R, G, B, A)

DEFAULT_PATH_COLOR = '#FFFFFF'  # Default drawing colors for path with no styling (should contrast with the background!)
USE_STYLE_COLOR = True
PREFER_STROKE_OVER_FILL_COLOR = True  # Prefer using a path stroke color over a path fill color

TCP_KEEP_TANGENCY = False  # Set to True to keep the tangency along the path
APPROACH = 150.0  # mm, approach distance for each path

MM_X_PIXEL = 5.0  # mm, the path will be cut depending on the pixel size. If this value is changed it is recommended to scale the pixel object.

#-------------------------------------------
# Load the SVG file
if IMAGE_FILE.startswith('http') and IMAGE_FILE.endswith('.svg'):
    r = urllib.request.urlretrieve(IMAGE_FILE, "drawing.svg")
    IMAGE_FILE = "drawing.svg"

elif not IMAGE_FILE or not os.path.exists(os.path.abspath(IMAGE_FILE)):
    IMAGE_FILE = robodialogs.getOpenFileName(strtitle='Open SVG File', defaultextension='.svg', filetypes=[('SVG files', '.svg')])

if not IMAGE_FILE or not os.path.exists(os.path.abspath(IMAGE_FILE)):
    quit()

paths, path_attribs, svg_attribs = spt.svg2paths2(IMAGE_FILE)

# Scale the SVG to fit in the desired drawing area
# 1. Find the bounding area
xmin, xmax, ymin, ymax = 9e9, 0, 9e9, 0
for path in paths:
    _xmin, _xmax, _ymin, _ymax = path.bbox()
    xmin = min(_xmin, xmin)
    xmax = max(_xmax, xmax)
    ymin = min(_ymin, ymin)
    ymax = max(_ymax, ymax)
bbox_height, bbox_width = ymax - ymin, xmax - xmin

# center_x = (xmin + xmax) / 2

# # Apply vertical flip around center
# flipped_paths = []
# for path in paths:
#     flipped = path.translated(-center_x)  # move to origin
#     flipped = flipped.scaled(-1, 1)       # horizontal mirror
#     flipped = flipped.translated(center_x)  # move back
#     flipped_paths.append(flipped)
# paths = flipped_paths

# 2. Scale the SVG file and recenter it to the drawing board
SCALE = min(BOARD_HEIGHT / bbox_height, BOARD_WIDTH / bbox_width)
svg_height, svg_width = bbox_height * SCALE, bbox_width * SCALE
svg_height_min, svg_width_min = ymin * SCALE, xmin * SCALE
TRANSLATE = complex((BOARD_WIDTH - svg_width) / 2 - svg_width_min, (BOARD_HEIGHT - svg_height) / 2 - svg_height_min)

#-------------------------------------------
# Get RoboDK Items
RDK = robolink.Robolink()
RDK.setSelection([])

robot = RDK.ItemUserPick(itemtype_or_list=robolink.ITEM_TYPE_ROBOT)
tool = robot.getLink(robolink.ITEM_TYPE_TOOL)
if not robot.Valid() or not tool.Valid():
    quit()

frames = RDK.ItemList(robolink.ITEM_TYPE_FRAME)
frames.remove(robot.Parent())
frame = RDK.ItemUserPick(itemtype_or_list=frames)  # Reference frame for the drawing
if not frame.Valid():
    quit()

pixel_ref = RDK.Item('pixel')  # Reference object to paint
if not frame.Valid():
    quit()

RDK.Render(False)

board_draw = RDK.Item('Drawing Board')  # Drawing board
if board_draw.Valid() and board_draw.Type() == robolink.ITEM_TYPE_OBJECT:
    board_draw.Delete()
board_250mm = RDK.Item('Whiteboard 250mm')
board_250mm.setVisible(False)
board_250mm.Copy()
board_draw = frame.Paste()
board_draw.setVisible(True, False)
board_draw.setName('Drawing Board')
board_draw.Scale([BOARD_HEIGHT / 250, BOARD_WIDTH / 250, 1])  # adjust the board size to the image size (scale)
board_draw.setColor(BOARD_BACKGROUND_COLOR)
RDK.setSelection([])

RDK.Render(True)

#-------------------------------------------
# Initialize the robot
home_joints = robot.JointsHome().tolist()
home_joints = [-90.0, -90.0000, -90.00, 0.0, 90.0, 0.00]

robot.setPoseFrame(frame)
robot.setPoseTool(tool)
# robot.MoveJ(home_joints)

# Get the orientation from the current TCP directly
orient_frame2tool = robomath.invH(frame.Pose()) * robot.SolveFK(home_joints)*  tool.Pose()
orient_frame2tool[0:3, 3] = robomath.Mat([0, 0, 0])
orient_frame2tool = orient_frame2tool * robomath.rotx(-0.7)


#-------------------------------------------
RDK.ShowMessage(f"Drawing {IMAGE_FILE}..", False)

for path_count, (path, attrib) in enumerate(zip(paths, path_attribs)):
    styles = {}

    if 'style' not in attrib:
        if 'fill' in attrib:
            styles['fill'] = attrib['fill']
        if 'stroke' in attrib:
            styles['stroke'] = attrib['stroke']
    else:
        for style in attrib['style'].split(';'):
            style_pair = style.split(':')
            if len(style_pair) != 2:
                continue
            styles[style_pair[0].strip()] = style_pair[1].strip()

    if 'fill' in styles and not styles['fill'].startswith('#'):
        styles.pop('fill')
    if 'stroke' in styles and not styles['stroke'].startswith('#'):
        styles.pop('stroke')

    hex_color = DEFAULT_PATH_COLOR
    if USE_STYLE_COLOR:
        if PREFER_STROKE_OVER_FILL_COLOR:
            if 'stroke' in styles:
                hex_color = styles['stroke']
            elif 'fill' in styles:
                hex_color = styles['fill']
        else:
            if 'fill' in styles:
                hex_color = styles['fill']
            elif 'stroke' in styles:
                hex_color = styles['stroke']

    draw_color = spt.misctools.hex2rgb(hex_color)
    draw_color = [round(x / 255, 4) for x in draw_color]

    if 'id' in attrib:
        RDK.ShowMessage(f"Drawing {attrib['id']} with color {hex_color}", False)
    else:
        RDK.ShowMessage(f"Drawing path {path_count} with color {hex_color}", False)

    approach_done = False
    prev_point = None
    for segment in path.scaled(SCALE).translated(TRANSLATE):
        segment_len = segment.length()
        steps = int(segment_len / MM_X_PIXEL)
        if steps < 1:
            continue

        for i in range(steps + 1):
            t = 1.0
            segment.point(t)
            if i < steps:
                # We need this check to prevent numerical accuracy going over 1, as t must be bound to [0,1]
                i_len = segment_len * i / steps
                t = segment.ilength(i_len)

            point = segment.point(t)
            py, px = point.real, point.imag

            pa = 0
            if prev_point:
                v = point - prev_point
                norm_v = robomath.sqrt(v.real * v.real + v.imag * v.imag)
                v = v / norm_v if norm_v > 1e-6 else complex(1, 0)
                pa = robomath.atan2(v.real, v.imag)

            if not approach_done and i == 0:
                # Safe approach to the first target
                target0 = robomath.transl(px, py, 0) * orient_frame2tool * robomath.rotz(pa)
                target0_app = target0 * robomath.transl(0, 0, -APPROACH)
                robot.MoveJ(target0_app)
                approach_done = True
                continue

            point_pose = robomath.transl(px, py, 0) * robomath.rotz(pa)
            
            robot_pose = robomath.transl(px, py, 0) * orient_frame2tool if not TCP_KEEP_TANGENCY else point_pose * orient_frame2tool

            robot.MoveL(robot_pose)

            pixel_ref.Recolor(draw_color)
            board_draw.AddGeometry(pixel_ref, point_pose)

            prev_point = point

    # Safe retract from the last target
    if approach_done:
        target_app = robot_pose * robomath.transl(0, 0, -APPROACH)
        robot.MoveL(target_app)

robot.MoveJ(home_joints)
RDK.ShowMessage(f"Done drawing {IMAGE_FILE}!", False)