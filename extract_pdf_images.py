import os
import argparse
import os
import glob
from PyPDF2 import PdfWriter, PdfReader
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTFigure
from pdfminer.pdfpage import PDFPage
from PIL import Image, ImageDraw
from pdf2image import convert_from_path
from IPython.display import display
import numpy as np
import subprocess



def display_pdf_page_with_bounding_box(pdf_path, element, page_number=0):
    # Convert the PDF page to an image (PNG)
    dpi = 300
    images = convert_from_path(pdf_path, dpi=dpi ,first_page=page_number + 1, last_page=page_number + 1)

    # Display the image with bounding box in the notebook
    if images:
        image = images[0]
        
        # Get the bounding box coordinates from element.bbox
        x0, y0, x1, y1 = element.bbox
        # the magic numbers

        # correction PDF --> PIL
        startY = image.height - int(y0 * dpi/72)
        endY   = image.height - int(y1   * dpi/72)
        startX = int(x0 * dpi/72)
        endX   = int(x1   * dpi/72)
        
        # Calculate the initial crop box coordinates
        startY = image.height - int(y0 * dpi/72)
        endY = image.height - int(y1 * dpi/72)
        startX = int(x0 * dpi/72)
        endX = int(x1 * dpi/72)

        # Initialize the padding
        padding = 5

        # Check if the padding exceeds the image boundaries
        if startY - padding < 0:
            startY = 0
        else:
            startY += padding

        if endY + padding > image.height:
            endY = image.height
        else:
            endY -= padding

        if startX - padding < 0:
            startX = 0
        else:
            startX -= padding

        if endX + padding > image.width:
            endX = image.width
        else:
            endX += padding
            
        startY, endY = endY, startY 
            
        # Crop the image to the bounding box
        cropped_image = image.crop((startX, startY, endX, endY))

        # Display the image with bounding box
        #display(cropped_image)
        
        # turn image to array
        image_array = np.array(image)
        # get cropped box
        box = image_array[startY:endY,startX:endX,:]
        convert2pil_image = Image.fromarray(box)
        
        # Create directory if it doesn't exist
        if not os.path.exists("Images"):
            os.makedirs("Images")
            
        #show cropped box image
        # convert2pil_image.show()
        png = "Images/" + str(element.name) + ".png"
        convert2pil_image.save(png)

def save_figure_as_pdf(pdf_path, element, page_number=0):
    # Get the bounding box coordinates of the figure
    # The dimensions of the page (assumed to be A4 in points)
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    page = reader.pages[page_number]
    
    
    page_height = page.mediabox[3]
    page_width = page.mediabox[2]

    # The bounding box coordinates
    x0, y0, x1, y1 = element.bbox

    padding = 1
    # Check if the padding exceeds the page boundaries
    if x0 - padding < 0:
        x0 = 0
    else:
        x0 -= padding

    if y0 - padding < 0:
        y0 = 0
    else:
        y0 -= padding

    if x1 + padding > page_width:
        x1 = page_width
    else:
        x1 += padding

    if y1 + padding > page_height:
        y1 = page_height
    else:
        y1 += padding

    (x0, y0, x1, y1) = (int(x0), int(y0), int(x1), int(y1))
    
    #y0 = page.mediabox[3] - int(y0)
    #y1 = page.mediabox[3] - int(y1)
    #y0, y1 = y1, y0 
        
    page.cropbox.lower_left = (x0, y1)
    page.cropbox.upper_right = (x1, y0)
    writer.add_page(page)
    # Create directory if it doesn't exist
    if not os.path.exists("Images"):
        os.makedirs("Images")
        
    # Save the new PDF with the selected figure
    output_path = "Images/Fig." + str(element.name) + ".pdf"
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
        
def extract_images_from_pdf(pdf_path):
    # Generate output folder name based on the PDF filename
    pdf_filename = os.path.basename(pdf_path)
    pdf_name_without_extension = os.path.splitext(pdf_filename)[0]
    output_folder = f"Images_{pdf_name_without_extension}"

    try:
        # Create the output folder if it does not exist
        resource_manager = PDFResourceManager()
        device = PDFPageAggregator(resource_manager, laparams=LAParams())
        interpreter = PDFPageInterpreter(resource_manager, device)

        with open(pdf_path, 'rb') as file:
            for page_number, page in enumerate(PDFPage.get_pages(file)):
                interpreter.process_page(page)
                layout = device.get_result()

                for element in layout:
                    if isinstance(element, LTFigure):
                        # Specify the output path for the extracted figure
                        # Example usage:
                        # Replace 'your_pdf_file.pdf' with the path to your PDF file
                        display_pdf_page_with_bounding_box(pdf_path, element, page_number)
                        
                        save_figure_as_pdf(pdf_path, element, page_number)


    except Exception as e:
        print(f"Error processing file {pdf_path}: {e}")
    
    
def main(pdf_directory):
    if not os.path.isdir(pdf_directory):
        print(f"Error: The provided directory {pdf_directory} does not exist.")
        return

    # Pattern to match PDF files
    pdf_pattern = '*.pdf'

    # Use glob to find PDF files in the current directory
    pdf_files = glob.glob(os.path.join(pdf_directory, pdf_pattern))

    if not pdf_files:
        print(f"No PDF files found in directory {pdf_directory}")
        return

    # Process each PDF file
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file}")
        # Specify the output folder where you want to save the extracted figures

        # Extract figures from the current PDF file
        extract_images_from_pdf(pdf_file)

        print()  # Add an empty line for better readability between PDFs

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some PDFs.')
    parser.add_argument('--pdf_directory', type=str, default='.', 
                        help='the directory of input PDF files')

    args = parser.parse_args()

    main(args.pdf_directory)
