import numpy as np
import cv2

def catmull_rom_spline(P0, P1, P2, P3, num_points=10):
    """
    Computes a Catmull-Rom spline between P1 and P2 using P0 and P3 as control points.
    Returns an array of shape (num_points, 2).
    """
    t = np.linspace(0, 1, num_points)
    t2 = t * t
    t3 = t2 * t
    
    # Catmull-Rom basis functions
    c0 = -t3 + 2*t2 - t
    c1 = 3*t3 - 5*t2 + 2
    c2 = -3*t3 + 4*t2 + t
    c3 = t3 - t2
    
    res = np.zeros((num_points, 2))
    res[:, 0] = 0.5 * (c0*P0[0] + c1*P1[0] + c2*P2[0] + c3*P3[0])
    res[:, 1] = 0.5 * (c0*P0[1] + c1*P1[1] + c2*P2[1] + c3*P3[1])
    return res

def create_spline_path(points, num_points_per_segment=10):
    """
    Takes a list of (x,y) points and generates a smooth Catmull-Rom spline path through them.
    """
    if len(points) < 3:
        return np.array(points, dtype=np.int32)
        
    # Duplicate start and end points for Catmull-Rom tangents
    pts = [points[0]] + points + [points[-1]]
    
    path = []
    for i in range(len(pts) - 3):
        segment = catmull_rom_spline(pts[i], pts[i+1], pts[i+2], pts[i+3], num_points_per_segment)
        path.extend(segment[:-1]) # Avoid duplicating points at joints
        
    path.append(pts[-2]) # Add final point
    return np.array(path, dtype=np.int32)

def draw_skeleton(canvas, frame_data, width, height, scale, offset, colors):
    """
    Draws the Organic Spline Avatar onto the provided canvas.
    """
    def to_pixel(pt):
        if not pt: return None
        x = int(((pt[0] * scale) + offset) * width)
        y = int(((pt[1] * scale) + offset) * height)
        return (x, y)
        
    # Extract points if available
    pose = frame_data.get("p", [])
    left_hand = frame_data.get("l", [])
    right_hand = frame_data.get("r", [])
    
    # Handle Tracking Drops (Cache the last valid face)
    if not hasattr(draw_skeleton, "cache"):
        draw_skeleton.cache = {"fj": [], "fl": [], "fre": [], "fle": []}
        
    fj_raw = frame_data.get("fj", [])
    if fj_raw:
        draw_skeleton.cache.update({
            "fj": fj_raw,
            "fl": frame_data.get("fl", []),
            "fre": frame_data.get("fre", []),
            "fle": frame_data.get("fle", [])
        })
        
    fj = draw_skeleton.cache["fj"]
    fl = draw_skeleton.cache["fl"]
    fre = draw_skeleton.cache["fre"]
    fle = draw_skeleton.cache["fle"]
    
    # Enhanced Draw Spline function with GLOW effect
    def draw_glowing_spline(points_list, color, thickness=3, is_closed=False):
        pixels = [to_pixel(pt) for pt in points_list if pt]
        if is_closed and len(pixels) > 0:
            pixels.append(pixels[0]) # Close the loop
            
        if len(pixels) >= 3:
            spline = create_spline_path(pixels, num_points_per_segment=8)
            
            # 1. Glow Base (Thick and Darker)
            glow_color = (int(color[0]*0.3), int(color[1]*0.3), int(color[2]*0.3))
            cv2.polylines(canvas, [spline], isClosed=False, color=glow_color, thickness=thickness+5, lineType=cv2.LINE_AA)
            
            # 2. Core Line (Thin and Bright)
            cv2.polylines(canvas, [spline], isClosed=False, color=color, thickness=thickness, lineType=cv2.LINE_AA)
            
            # Joints
            for px in pixels:
                cv2.circle(canvas, px, thickness-1, color, -1)
        elif len(pixels) == 2:
            glow_color = (int(color[0]*0.3), int(color[1]*0.3), int(color[2]*0.3))
            cv2.line(canvas, pixels[0], pixels[1], glow_color, thickness+5, cv2.LINE_AA)
            cv2.line(canvas, pixels[0], pixels[1], color, thickness, cv2.LINE_AA)
            for px in pixels:
                cv2.circle(canvas, px, thickness-1, color, -1)

    # 1. DRAW FACE CONTOURS
    face_color = colors.get("f", (0, 255, 255))
    draw_glowing_spline(fj, face_color, thickness=2, is_closed=False) # Jawline
    draw_glowing_spline(fl, face_color, thickness=2, is_closed=True)  # Lips
    draw_glowing_spline(fre, face_color, thickness=2, is_closed=True) # Right Eye
    draw_glowing_spline(fle, face_color, thickness=2, is_closed=True) # Left Eye

    # 2. DRAW TORSO & ARMS
    pose_color = colors.get("p", (255, 0, 255))
    if len(pose) >= 25: # Ensure pose landmarks exist up to hips
        # Torso Chest Box (Drawn FIRST so arms are in front)
        # Using 2-point straight lines to ensure perfectly symmetric, sharp corners (no blobby splines)
        draw_glowing_spline([pose[11], pose[12]], pose_color, thickness=4) # Shoulders
        draw_glowing_spline([pose[23], pose[24]], pose_color, thickness=4) # Hips
        draw_glowing_spline([pose[11], pose[23]], pose_color, thickness=4) # Left side
        draw_glowing_spline([pose[12], pose[24]], pose_color, thickness=4) # Right side
        
        # Left Arm (Tapered)
        draw_glowing_spline([pose[11], pose[13]], pose_color, thickness=8) # Thick Bicep
        draw_glowing_spline([pose[13], pose[15]], pose_color, thickness=5) # Thin Forearm
        
        # Right Arm (Tapered)
        draw_glowing_spline([pose[12], pose[14]], pose_color, thickness=8) # Thick Bicep
        draw_glowing_spline([pose[14], pose[16]], pose_color, thickness=5) # Thin Forearm
        
    # 3. DRAW HANDS
    def draw_hand(hand_data, color):
        if len(hand_data) >= 21:
            wrist = hand_data[0]
            fingers = [
                [wrist, hand_data[1], hand_data[2], hand_data[3], hand_data[4]], # Thumb
                [wrist, hand_data[5], hand_data[6], hand_data[7], hand_data[8]], # Index
                [wrist, hand_data[9], hand_data[10], hand_data[11], hand_data[12]], # Middle
                [wrist, hand_data[13], hand_data[14], hand_data[15], hand_data[16]], # Ring
                [wrist, hand_data[17], hand_data[18], hand_data[19], hand_data[20]]  # Pinky
            ]
            for finger_pts in fingers:
                draw_glowing_spline(finger_pts, color, thickness=3)

    draw_hand(left_hand, colors.get("l", (0, 255, 0)))
    draw_hand(right_hand, colors.get("r", (0, 255, 0)))
