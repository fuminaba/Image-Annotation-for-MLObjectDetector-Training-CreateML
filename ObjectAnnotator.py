import os; import ntpath
import tkinter as tk; from tkinter import BOTTOM, Toplevel, filedialog as fd
from PIL import Image, ImageTk
import numpy as np
import json

class ObjectAnnotator(tk.Canvas):
    def __init__(self, master, title):
        # Store all annotations made
        self.annotations = []
        self.rect_index = 0
        self.annotation_index = 0 

        # Initialize metadata 
        self.current_image_index = -1
        self.current_image, self.image_name = self.select_image()

        # Interface metadata initialization
        self.master = master; self.master.title(title)
        super(ObjectAnnotator, self).__init__(self.master)

        # Create subframes as containers for widgets 
        self.mainframe = tk.Frame(self.master); self.mainframe.pack()
        self.bottomframe = tk.Frame(self.master); self.bottomframe.pack()
        # -- Second layer of subframes 
        self.image_canvas = tk.Canvas(self.mainframe, width = self.current_image.width, height = self.current_image.height); self.image_canvas.pack(side = tk.LEFT)
        self.class_menu = tk.Frame(self.mainframe); self.class_menu.pack(side = tk.LEFT, anchor = 'ne')
        self.metadata_frame = tk.Frame(self.bottomframe); self.metadata_frame.pack(side = tk.LEFT)
        self.buttons_container = tk.Frame(self.bottomframe); self.buttons_container.pack(side = tk.LEFT)
        # ------ Third layer of subframes
        self.user_inputframe = tk.Frame(self.class_menu); self.user_inputframe.pack(side = tk.TOP, anchor = 'ne')
        self.class_display = tk.Frame(self.class_menu); self.class_display.pack(side = tk.TOP)

        # Image_canvas components 
        self.tk_img = ImageTk.PhotoImage(self.current_image)
        self.display_image = self.image_canvas.create_image(0, 0, anchor = 'nw', image = self.tk_img)

        # Class Menu components
        self.v_var = tk.StringVar(self.class_menu) # May need to edit the master parameter
        add_class_button = tk.Button(self.user_inputframe, text = "Add class", command = self.class_addition); add_class_button.pack(side = tk.RIGHT, anchor = 'n') 
        self.user_entry = tk.Entry(self.user_inputframe); self.user_entry.pack(side = tk.RIGHT, anchor = 'n')

        # Button Container 
        quit_button = tk.Button(self.buttons_container, text = "Quit Application", command = quit).pack(side = tk.RIGHT)
        export_button = tk.Button(self.buttons_container, text = "Export Annotations", command = self.export_annotations).pack(side = tk.RIGHT) 
        next_button = tk.Button(self.buttons_container, text = "Next Image", command = self.next_image); next_button.pack()

        # Metadata Container 
        self.image_name_display = tk.Label(self.metadata_frame, text = self.image_name[:21])
        self.image_name_display.pack(side = tk.LEFT)

        # Rectangle parameters
        self.start_x = 0
        self.start_y = 0
        self.image_canvas.config(cursor = 'crosshair')

        # -------------------- Bindings to Canvas -------------------- #
        self.image_canvas.bind('<Button-1>', self.initiate_rectangle_drawing)
        self.image_canvas.bind('<B1-Motion>', self.draw_rectangle)
        self.image_canvas.bind('<ButtonRelease-1>', self.complete_rectangle)
        self.image_canvas.bind('<Motion>', self.track_mouse)
        self.master.bind('<KeyPress-BackSpace>', self.delete_recent_rect)
        # -------------------- End Initialization -------------------- #


    def select_image(self):
        image_path = fd.askopenfilename(title = "Select image to annotate: ")
        image = Image.open(image_path)
        image_name = ntpath.basename(image_path)
        self.current_image_index += 1
        self.annotations.append(
            {
                'imagefilename':image_name, 
                'annotation': []
            })

        return image, image_name

    # -------------------- Processing Methods --------------------- #
    def next_image(self):
        # Clear current image and rect 
        for i in range(self.rect_index):
            self.image_canvas.delete(f'rect{i}')
            self.image_canvas.delete(f'label{i}')
        # Update parameters 
        self.current_image, self.image_name = self.select_image()
        self.next_tk_img = ImageTk.PhotoImage(image = self.current_image)
        self.image_canvas.itemconfig(self.display_image, image = self.next_tk_img)
        self.image_canvas.config(cursor = 'crosshair')
        self.rect_index = 0 
        self.annotation_index = 0

    def class_addition(self): 
        txt_input = self.user_entry.get()
        new_button = tk.Radiobutton(self.class_display, text = txt_input, variable = self.v_var, value = txt_input, selectcolor = "light blue")
        new_button.pack(side = tk.TOP, anchor = 'center')
        self.user_entry.delete(0, 'end')

    def get_rectangle_center(self, rect_coords):
        x1, y1, x2, y2 = rect_coords
        middle_x = int(np.mean([x1, x2]))
        middle_y = int(np.mean([y1, y2]))
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return (middle_x, middle_y, width, height)

    def initiate_rectangle_drawing(self, event):
        self.start_x = self.image_canvas.canvasx(event.x)
        self.start_y = self.image_canvas.canvasy(event.y)
        self.rect = self.image_canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, width = 2, outline = 'white')
        
    def draw_rectangle(self, event):
        mouse_pos_x = self.image_canvas.canvasx(event.x)
        self.final_x = mouse_pos_x
        mouse_pos_y = self.image_canvas.canvasy(event.y)
        self.final_y = mouse_pos_y
        self.image_canvas.coords(self.rect, self.start_x, self.start_y, mouse_pos_x, mouse_pos_y)

    def complete_rectangle(self, event):
        x1, y1, x2, y2 = self.start_x, self.start_y, self.final_x, self.final_y
        middle_point = self.get_rectangle_center((x1, y1, x2, y2))
        annotation_dict = self.annotations[self.current_image_index]['annotation']
        annotation_dict.append({
            "coordinates": {
                "y": middle_point[1],
                "x": middle_point[0],
                "height": middle_point[3],
                "width": middle_point[2],
            }, 
            "label": self.v_var.get()
        })
        self.image_canvas.create_rectangle(x1, y1, x2, y2, outline = 'red', tags = f'rect{self.rect_index}')
        self.image_canvas.create_text((middle_point[0], middle_point[1]), text = self.v_var.get(), tags = f'label{self.annotation_index}')
        print(f"Rect tag = rect{self.rect_index}, Label tag = label{self.annotation_index}")        
        self.rect_index += 1
        self.annotation_index += 1
        self.image_canvas.delete(self.rect)

    def delete_recent_rect(self, event):
        try:
            self.image_canvas.delete(f'rect{self.rect_index-1}')
            self.image_canvas.delete(f'label{self.annotation_index-1}')
            self.image_canvas.delete(self.rect)
            # Update annotation dictionary
            annotation_dict = self.annotations[self.current_image_index]['annotation']
            del annotation_dict[-1]
            # Update index parameters 
            self.rect_index -= 1
            self.annotation_index -= 1
        except IndexError:
            pass

    def track_mouse(self, event):
        self.x_pos = event.x
        self.y_pos = event.y
        print(f'\r {self.x_pos}, {self.y_pos}', end = '\r')
    
    def export_annotations(self):
        output_dir = os.getcwd()
        output_path = f'{output_dir}/Annotations'
        path_exists = os.path.exists(output_path)
        if not path_exists:
            os.makedirs(output_path)
        with open(f'{output_dir}/Annotation_file/annotation.json', 'w') as json_annotes:
            json_annotes.write(json.dumps(self.annotations, indent = 4))
    
if __name__ == "__main__":
    root_widget = tk.Tk(); root_widget.withdraw()
    annotator = ObjectAnnotator(root_widget, "Object Annotator for Deep Learning Training Data Processing")
    root_widget.deiconify()

    root_widget.mainloop()