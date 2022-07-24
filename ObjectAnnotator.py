'''
@author: Fumiya Inaba 
Last edited: July 24, 2022 @ 12:34 AM 
File functionality: 
-> The user can create classes to annotate object within an image, which can be used to train 
   Apple's CreateML Object Detector Model. 
-> Input: a collection of images that will be annotated with user-input-classes one by one
-> Output: a json file contianing the annotated objects

Update: 
-> Reorganized code for readability 
-> Fixed continuation issue -> can now go back and continue to annotate images that have previously been annotated
   given that the information is stored in the json file
-> Will render and show previously made annotations
-> Will append to already existing imagefilename if the image has previously been annotated instead of making a duplicate
   entry in the json file
'''

import tkinter as tk
from tkinter import filedialog as fd
from PIL import Image, ImageTk
import ntpath
import numpy as np
import os 
import json

class ImageAnnotator(tk.Frame):
    def __init__(self, master, name):
        # ============================== Master Info ============================== # 
        self.master = master
        self.master.title(name)

        # ============================== Interface Settings ============================== # 
        # ------------------------------- Main Interface ------------------------------ #
        mainframe = tk.Frame(self.master)
        # ------------------------------ Image Interface ------------------------------ #
        self.current_image_index = 0
        self.image_canvas = tk.Canvas(mainframe, width = 600, height = 600)
        self.image_canvas.config(cursor = "crosshair")
        self.annotations = []
        self.select_image()
        self.img_tk = ImageTk.PhotoImage(self.image)
        self.display_image = self.image_canvas.create_image(0, 0, anchor = 'nw', image = self.img_tk)
        # ------------------------------ Annotation Metadata ------------------------------ #
        self.rect_count = 0 
        self.rect_label_count = 0 
        self.annotations = self.load_progress()
        self.render_previous_rect()
        # ------------------------------ Annotation Interface ------------------------------ #
        annotation_frame = tk.Frame(mainframe)
        self.annotation_display_frame = tk.Frame(annotation_frame)
        instruction_frame = tk.Frame(annotation_frame)
        # ------------------------------ User Input Bar ------------------------------ #
        self.v_var = tk.StringVar(self.annotation_display_frame)
        user_input_bar = tk.Frame(self.annotation_display_frame)
        self.user_input_entry = tk.Entry(user_input_bar)
        add_class_button = tk.Button(user_input_bar, text = "Add Class", command = self.class_addition) 
        # ------------------------------ Inputted Class Display ------------------------------ #
        class_display = tk.Frame(self.annotation_display_frame)
        # ------------------------------ Instructions Display ------------------------------ #
        instructions = tk.Frame(instruction_frame)
        instruction_title = tk.Label(instructions, text = "Interface Control - READ FIRST", font = ("Arial", 20))
        instructions_class_entry = tk.Label(instructions, text = "Create a class above by typing in class name and select before making annotations.")
        instructions_export_warn = tk.Label(instructions, text = "Ensure you click \"Export Annotations\" to save annotations for each image")
        instructions_export_warn2 = tk.Label(instructions, text = "CLICK EXPORT ANNOTATIONS BEFORE MOVING ON TO NEXT IMAGE")
        instructions_for_image_canvas = tk.Label(instructions, text = "Click and drag to make annotation rectangles")
        instructions_to_delete = tk.Label(instructions, text = "Backspace to undo last rectangle annotation")

        # ------------------------------ Lower Interface ------------------------------ #
        lower_frame = tk.Frame(self.master)
        metadata_frame = tk.Frame(lower_frame)
        buttons_frame = tk.Frame(lower_frame)
        # ------------------------------ Metadata Interface ------------------------------ #
        image_name_label = tk.Label(metadata_frame, text = f"Image Name: {self.image_name[:21]}", font = ("Arial", 18))
        image_original_size = tk.Label(metadata_frame, text = f"Original size: {int(self.image.size[0]/self.ratio)}, {int(self.image.size[1]/self.ratio)}", font = ("Arial", 18))

        # ------------------------------ Buttons for App ------------------------------ #
        quit_button = tk.Button(buttons_frame, text = "Quit Application", command = quit)
        export_button = tk.Button(buttons_frame, text = "Export Annotations", command = self.export_annotations) 
        next_image_button = tk.Button(buttons_frame, text = "Next Image", command = self.next_image) 

        # ============================== Pack Interface ============================== # 
        # ------------------------------ Main Interface ------------------------------ #
        mainframe.pack(side = tk.TOP, expand = True)
        # ------------------------------ Image Packing ------------------------------ #
        self.image_canvas.pack(side = tk.LEFT, expand = True, anchor = 'nw')
        # ------------------------------ User Entry Packing ------------------------------ #
        annotation_frame.pack(side = tk.LEFT, expand = True, anchor = 'ne', fill = 'both')
        self.annotation_display_frame.pack(side = tk.TOP, expand = True, anchor = 'n', fill = 'both')

        user_input_bar.pack(side = tk.TOP, anchor = 'ne', fill = 'x')
        add_class_button.pack(side = tk.RIGHT, anchor = 'ne')
        self.user_input_entry.pack(side = tk.RIGHT, fill = 'x', anchor='ne', expand = True)
        # ------------------------------ Class Display Packing ------------------------------ #
        class_display.pack(expand = True)
        # ------------------------------ Instructions Packing ------------------------------ #
        instruction_frame.pack()
        instructions.pack(anchor = 'sw')
        instruction_title.pack(anchor = 'sw')
        instructions_export_warn.pack(anchor = 'sw')
        instructions_export_warn2.pack(anchor = 'sw')
        instructions_class_entry.pack(anchor = 'sw')
        instructions_for_image_canvas.pack(anchor = 'sw')
        instructions_to_delete.pack(anchor = 'sw')
        # ------------------------------ Lower Interface ------------------------------ #
        lower_frame.pack(side = tk.TOP, expand = True, fill = 'x')
        metadata_frame.pack(side = tk.LEFT, expand = True, fill = 'x')
        buttons_frame.pack(side = tk.RIGHT, anchor = 'se')
        # ------------------------------ Metadata Packing ------------------------------ #
        image_name_label.pack(side = tk.TOP, anchor = 'w', fill = 'x')
        image_original_size.pack(side = tk.TOP, anchor = 'w', fill = 'x')
        # ------------------------------ Buttons Packing  ------------------------------ #
        quit_button.pack(side = tk.RIGHT)
        export_button.pack(side = tk.RIGHT)
        next_image_button.pack(side = tk.RIGHT)
        # ============================== Interface Bindings ============================== # 
        self.image_canvas.bind('<Button-1>', self.initiate_rectangle_drawing)
        self.image_canvas.bind('<B1-Motion>', self.draw_rectangle)
        self.image_canvas.bind('<ButtonRelease-1>', self.complete_rectangle)
        self.master.bind('<KeyPress-BackSpace>', self.delete_recent_rect)
        
    # ------------------------------ Interface Initialization Methods ------------------------------ # 
    def select_image(self):
        image_path = fd.askopenfilename(title = 'Select image to annotate')
        image = Image.open(image_path)
        image_name = ntpath.basename(image_path)
        w, h = image.size
        if w < 600:
            new_w = 600
            self.ratio = new_w / w
            new_h = int(self.ratio * h)
            image = image.resize((new_w, new_h))
        self.image = image
        self.image_name = image_name


    def load_progress(self):
        '''
        Purpose of the function is to get data from the json file if it exists. 
        '''
        # Check current directory and if file exists
        current_dir = os.getcwd()
        path_to_check = f'{current_dir}/Annotations/annotation.json'
        fileExists = os.path.isfile(path_to_check)
        # If file doesn't exist:
        if not fileExists:
            return [{'imagefilename': self.image_name, 'annotation':[]}]
        else: # If file exists 
            with open(path_to_check, 'r') as f:
                f_contents = f.read()
                # If file exists but is empty
                if f_contents != "":
                    progress_made = json.loads(f_contents) # Load as dictionary 
                    already_annotated_files = [] # Container for file names that have already been annotated
                    for file_annotated in progress_made:
                        already_annotated_files.append(file_annotated['imagefilename'])
                        print(already_annotated_files)
                    if self.image_name in already_annotated_files:
                        self.current_image_index = already_annotated_files.index(self.image_name)
                        return progress_made
                    else: # If the file hasn't been annotated yet 
                        progress_made.append({'imagefilename': self.image_name, 'annotation':[]})
                        self.current_image_index = len(already_annotated_files) 
                        return progress_made
                # If it's empty return template for json
                else:
                    return [{'imagefilename': self.image_name, 'annotation':[]}]
    
    def render_previous_rect(self):
        annotations_made = self.annotations[self.current_image_index]['annotation']
        for annotate in annotations_made:
            coords = annotate['coordinates']
            middle_y = coords['y'] * self.ratio
            middle_x = coords['x'] * self.ratio
            rect_h = coords['height'] * self.ratio
            rect_w = coords['width'] * self.ratio
            x1, y1, x2, y2 = self.get_rectangle_from_center((middle_x, middle_y, rect_w, rect_h))
            rect_index = annotations_made.index(annotate)
            self.image_canvas.create_rectangle(x1, y1, x2, y2, outline = 'red', tags = f'rect{rect_index}')
            self.image_canvas.create_text(middle_x, middle_y, text = annotate['label'], tags = f'label{rect_index}')
            self.rect_count += 1
            self.rect_label_count += 1

    def next_image(self):
        # Clear current image and rect 
        for i in range(self.rect_count):
            self.image_canvas.delete(f'rect{i}')
            self.image_canvas.delete(f'label{i}')
        # Load previous data 
        self.select_image()
        self.next_tk_img = ImageTk.PhotoImage(image = self.image)
        self.image_canvas.itemconfig(self.display_image, image = self.next_tk_img)
        self.image_canvas.config(cursor = 'crosshair')
        self.rect_count = 0 
        self.rect_label_count = 0
        self.annotations = self.load_progress()
        self.render_previous_rect()



    # ------------------------------ Rectangle Annotation Methods ------------------------------ #
    def initiate_rectangle_drawing(self, event):
        self.start_x = self.image_canvas.canvasx(event.x)
        self.start_y = self.image_canvas.canvasy(event.y)        
        self.rect_annotation = self.image_canvas.create_rectangle(self.start_x, self.start_y, self.start_x + 1, self.start_y + 1)
    
    def draw_rectangle(self, event):
        mouse_pos_x = self.image_canvas.canvasx(event.x)
        self.final_x = mouse_pos_x
        mouse_pos_y = self.image_canvas.canvasy(event.y)
        self.final_y = mouse_pos_y
        self.image_canvas.coords(self.rect_annotation, self.start_x, self.start_y, mouse_pos_x, mouse_pos_y)

    def complete_rectangle(self, event):
        # Create the resulting rectangle 
        x1, y1, x2, y2 = self.start_x, self.start_y, self.final_x, self.final_y 
        self.image_canvas.create_rectangle(x1, y1, x2, y2, outline = 'red', tags = f"rect{self.rect_count}")
        print(f'Rect count {self.rect_count}')
        self.rect_count += 1
        # Delete cursor rectangle
        self.image_canvas.delete(self.rect_annotation)
        # Calculate center x and y point for json annotation file and text label placement
        middle_x, middle_y, rect_w, rect_h = self.get_rectangle_center((x1, y1, x2, y2))
        # Make Label for rectnagle annotation 
        self.image_canvas.create_text(middle_x, middle_y, anchor = 'center', text = self.v_var.get(), tags = f'label{self.rect_label_count}')
        self.rect_label_count += 1
        # Add onto annotations to export 
        annotation_dict = self.annotations[self.current_image_index]['annotation']
        annotation_dict.append({
            "coordinates": {
                'y': int(middle_y / self.ratio),
                'x': int(middle_x / self.ratio), 
                'height': int(rect_h / self.ratio), 
                'width' : int(rect_w / self.ratio)
            }, 
            'label': self.v_var.get()
        })

    def get_rectangle_center(self, rect_coords):
        x1, y1, x2, y2 = rect_coords
        middle_x = np.mean([x1, x2])
        middle_y = np.mean([y1, y2])
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return middle_x, middle_y, width, height
    
    def get_rectangle_from_center(self, rect_coords):
        middle_x, middle_y, rect_w, rect_h = rect_coords
        # Width 
        half_width = int(rect_w / 2)
        x1 = middle_x - half_width
        x2 = middle_x + half_width 
        # Height
        half_height = int(rect_h / 2)
        y1 = middle_y - half_height
        y2 = middle_y + half_height
        return x1, y1, x2, y2
    
    def delete_recent_rect(self, events):
        try:
            self.image_canvas.delete(f'rect{self.rect_count-1}')
            self.image_canvas.delete(f'label{self.rect_label_count-1}')
            # Update annotation dictionary
            annotation_dict = self.annotations[self.current_image_index]['annotation']
            del annotation_dict[-1]
            # Update index parameters 
            self.rect_count -= 1
            self.rect_label_count -= 1
        except IndexError:
            pass

    # ------------------------------ Class Annotation Methods ------------------------------ #       
    def class_addition(self): 
        txt_input = self.user_input_entry.get()
        new_button = tk.Radiobutton(self.annotation_display_frame, text = txt_input, font = ("Arial", 25),variable = self.v_var, value = txt_input, selectcolor = "light blue")
        new_button.pack(side = tk.TOP, anchor = 'n')
        self.user_input_entry.delete(0, 'end')

    def export_annotations(self):
        output_dir = os.getcwd()
        output_path = f'{output_dir}/Annotations'
        path_exists = os.path.exists(output_path)
        if not path_exists:
            os.makedirs(output_path)
        with open(f'{output_dir}/Annotations/annotation.json', 'w') as json_annotes:
            json_annotes.write(json.dumps(self.annotations, indent = 4))

        res = tk.messagebox.askquestion("Export", "Export success! You can now quit the application. Quit application?")
        if res == 'yes':
            self.master.destroy()

if __name__ == "__main__":
    root_widget = tk.Tk(); root_widget.withdraw()
    annotator = ImageAnnotator(root_widget, "Image Annotator")
    root_widget.deiconify()
    root_widget.mainloop()
