import json
import math
import os

def generate_idle_animation():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, "assets", "jsons", "t", "to", "today.json")
    
    with open(template_path, 'r') as f:
        template_data = json.load(f)
        
    base_frame = template_data[0] # Usually neutral
    
    # Ensure hands are empty so they drop
    base_frame['l'] = []
    base_frame['r'] = []
    
    num_frames = 90 # 3 seconds at 30fps
    amplitude = 0.006 # Subtle Y-axis movement
    
    idle_sequence = []
    
    for i in range(num_frames):
        # 0 to 2*pi over the sequence
        phase = (i / num_frames) * 2 * math.pi
        y_offset = math.sin(phase) * amplitude
        
        new_frame = {}
        for key, points in base_frame.items():
            if not points:
                new_frame[key] = []
                continue
                
            new_points = []
            for pt in points:
                # MediaPipe points are [x, y, z]
                new_pt = [pt[0], pt[1] + y_offset, pt[2]]
                new_points.append(new_pt)
            new_frame[key] = new_points
            
        idle_sequence.append(new_frame)
        
    out_dir = os.path.join(base_dir, "assets", "jsons", "i", "id")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "idle.json")
    
    with open(out_path, 'w') as f:
        json.dump(idle_sequence, f)
        
    print(f"Generated {num_frames} frame idle animation at {out_path}")

if __name__ == '__main__':
    generate_idle_animation()
