import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import subprocess
from PIL import Image, ImageTk
import os

# Function to run subprocess command


def run_subprocess(command, input_data=None):
    result = subprocess.run(command, input=input_data,
                            text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error running command: {' '.join(command)}")
        print(result.stderr)
    return result.stdout

# Function to predict RNA structure


def predict_rna_structure(rna_sequence):
    # Run RNAfold to get MFE structure and energy
    fold_output = run_subprocess(
        ["RNAfold", "--noPS"], input_data=rna_sequence)

    ss = ""
    mfe = 0.0
    for line in fold_output.split('\n'):
        if line.startswith(rna_sequence):
            continue
        if line.startswith("("):
            pos = line.find(' ')
            ss = line[0: pos]
            mfe = float(line[pos+1:].strip("()"))

    # Run RNAsubopt to get suboptimal structures
    subopt_output = run_subprocess(
        ["RNAsubopt", "-e", "5.0"], input_data=rna_sequence)
    subopts = []
    for line in subopt_output.split('\n'):
        if line and not line.startswith(">"):
            parts = line.split()
            if len(parts) == 2:
                subopts.append((parts[0], float(parts[1])))

    return ss, mfe, subopts

# Function to plot RNA structure


def plot_rna_structure(rna_sequence, secondary_structure, output_file):
    # Create RNAplot input file
    with open("rna_plot_input.txt", "w") as f:
        f.write(f"{rna_sequence}\n{secondary_structure}\n")

    # Generate RNAplot structure plot
    run_subprocess(["RNAplot"], input_data=open("rna_plot_input.txt").read())

    # Rename rna.ps to the desired output_file (in this case, rna.png)
    if os.path.exists("rna.ps"):
        os.rename("rna.ps", output_file)

# Function to display image in GUI


def display_image(image_path):
    img = Image.open(image_path)
    img = img.resize((400, 300), Image.ANTIALIAS)  # Resize image if necessary
    img = ImageTk.PhotoImage(img)
    img_label.config(image=img)
    img_label.image = img

# Function to handle button click event


def on_predict_click():
    rna_sequence = sequence_entry.get("1.0", tk.END).strip()
    if not rna_sequence:
        messagebox.showerror("Error", "Please enter an RNA sequence.")
        return

    # Predict RNA structure
    ss, mfe, subopts = predict_rna_structure(rna_sequence)

    # Update GUI with results
    result_text.config(state=tk.NORMAL)
    result_text.delete("1.0", tk.END)
    result_text.insert(tk.END, f"Predicted Secondary Structure: {ss}\n")
    result_text.insert(
        tk.END, f"Minimum Free Energy (MFE): {mfe} kcal/mol\n\n")
    result_text.insert(tk.END, "Suboptimal Structures within 5 kcal/mol:\n")
    for structure, energy in subopts:
        result_text.insert(
            tk.END, f"Structure: {structure}, Energy: {energy} kcal/mol\n")
    result_text.config(state=tk.DISABLED)

    # Plot RNA structure and display in GUI
    plot_rna_structure(rna_sequence, ss, "rna_structure.png")
    display_image("rna_structure.png")


# Create the main application window
root = tk.Tk()
root.title("RNA Secondary Structure Prediction")
root.geometry("800x600")

# GUI Elements
sequence_label = ttk.Label(root, text="Enter RNA Sequence:")
sequence_label.pack(pady=10)

sequence_entry = ScrolledText(root, height=5, width=70)
sequence_entry.pack()

predict_button = ttk.Button(
    root, text="Predict Structure", command=on_predict_click)
predict_button.pack(pady=10)

result_text = ScrolledText(root, height=150, width=80, wrap=tk.WORD)
result_text.pack(pady=20)
result_text.config(state=tk.DISABLED)

img_label = ttk.Label(root)
img_label.pack()

# Start the GUI main loop
root.mainloop()
