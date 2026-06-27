from .imports import *
def resize_and_convert_to_webp(input_path, output_path):
    """
    Resize an image to approximately 1200x627 while maintaining aspect ratio,
    and convert it to WebP format.
    
    Args:
        input_path (str): Path to the input image.
        output_path (str): Path to save the output WebP image.
    
    Returns:
        tuple: (new_width, new_height) of the resized image, or None if an error occurs.
    """
    try:
        # Open the image
        img = Image.open(input_path)
        
        # Get the original dimensions
        original_width, original_height = img.size
        
        # Calculate the target aspect ratio
        target_ratio = TARGET_WIDTH / TARGET_HEIGHT
        original_ratio = original_width / original_height
        
        # Determine the new dimensions while maintaining aspect ratio
        if original_ratio > target_ratio:
            # Image is wider than the target ratio, fit to height
            new_height = TARGET_HEIGHT
            new_width = int(new_height * original_ratio)
        else:
            # Image is taller than the target ratio, fit to width
            new_width = TARGET_WIDTH
            new_height = int(new_width / original_ratio)
        
        # Resize the image
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # If the image is not in RGB mode, convert it (WebP requires RGB)
        if resized_img.mode != 'RGB':
            resized_img = resized_img.convert('RGB')
        
        # Save the image as WebP
        resized_img.save(output_path, 'WEBP', quality=80)
        print(f"Successfully processed: {input_path} -> {output_path}")
        
        return new_width, new_height
    
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return None

def get_file_size(file_path):
    """
    Get the file size in KB.
    
    Args:
        file_path (str): Path to the file.
    
    Returns:
        str: File size in KB (e.g., "100KB").
    """
    try:
        size_bytes = os.path.getsize(file_path)
        size_kb = size_bytes / 1024  # Convert bytes to KB
        return f"{int(size_kb)}KB"
    except Exception as e:
        print(f"Error getting file size for {file_path}: {e}")
        return "Unknown"

def update_json_metadata(json_path, new_filename, new_ext, new_width, new_height, new_file_size):
    """
    Update the info.json file with the new WebP image details.
    
    Args:
        json_path (str): Path to the info.json file.
        new_filename (str): New filename for the WebP image.
        new_ext (str): New extension ("webp").
        new_width (int): New width of the resized image.
        new_height (int): New height of the resized image.
        new_file_size (str): New file size in KB.
    """
    try:
        # Read the existing JSON file
        with open(json_path, 'r') as f:
            metadata = json.load(f)
        
        # Update the relevant fields
        metadata['filename'] = new_filename
        metadata['ext'] = new_ext
        if metadata.get('dimensions') == None:
            metadata['dimensions'] = {}
        metadata['dimensions']['width'] = new_width
        metadata['dimensions']['height'] = new_height
        metadata['file_size'] = new_file_size
        
        # Update the schema URLs
        new_url = f"https://thedailydialectics.com/imgs/{BASE_DIR}/{os.path.basename(os.path.dirname(json_path))}/{new_filename}.{new_ext}"
        if metadata.get('schema') == None:
            metadata['schema']={}
        metadata['schema']['url'] = new_url
        metadata['schema']['contentUrl'] = new_url
        metadata['schema']['width'] = new_width
        metadata['schema']['height'] = new_height
        if metadata.get('social_meta') == None:
            metadata['social_meta']={}        
        # Update the social media URLs
        metadata['social_meta']['og:image'] = new_url
        metadata['social_meta']['twitter:image'] = new_url
        
        # Write the updated JSON back to the file
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        print(f"Updated JSON metadata: {json_path}")
    
    except Exception as e:
        print(f"Error updating JSON metadata for {json_path}: {e}")

def process_directory(directory, image_path):
    try:
        json_path = os.path.join(directory, "info.json")

        if not os.path.isfile(json_path):
            safe_dump_to_json(file_path=json_path, data={})

        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            return

        image_parts = get_file_parts(image_path)
        new_filename = image_parts.get("filename")

        # Prevent repeated output names.
        while new_filename.endswith("_resized"):
            new_filename = new_filename[:-len("_resized")]

        output_path = os.path.join(directory, f"{new_filename}.webp")

        if os.path.abspath(image_path) == os.path.abspath(output_path):
            print(f"Skipping already converted image: {image_path}")
            return directory

        if os.path.exists(output_path):
            print(f"Output already exists, skipping: {output_path}")
            return directory

        result = resize_and_convert_to_webp(image_path, output_path)

        if result:
            new_width, new_height = result
            new_file_size = get_file_size(output_path)
            update_json_metadata(json_path, new_filename, "webp", new_width, new_height, new_file_size)

    except Exception as e:
        print(f"Error processing directory {directory}: {e}")

    return directory
