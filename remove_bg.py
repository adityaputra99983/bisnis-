from PIL import Image

def remove_background(input_path, output_path):
    try:
        img = Image.open(input_path).convert("RGBA")
        datas = img.getdata()
        
        newData = []
        for item in datas:
            # Get max brightness of the pixel
            r, g, b, a = item
            brightness = max(r, g, b)
            
            # The background is a dark gradient. Gold is bright.
            # We'll make anything very dark completely transparent.
            # And anything slightly dark partially transparent.
            if brightness < 25:
                newData.append((0, 0, 0, 0))
            elif brightness < 80:
                # Smooth transition for edges/glow
                alpha = int((brightness - 25) * (255 / 55))
                newData.append((r, g, b, alpha))
            else:
                newData.append((r, g, b, 255))
                
        img.putdata(newData)
        img.save(output_path, "PNG")
        print("Successfully removed background!")
    except Exception as e:
        print("Error:", e)

input_file = r'd:\Data C\Downloads\progres\bisnis\static\tattoo\img\bali_ink_logo.png'
# Save to a new file first to be safe, then we'll check it or just overwrite
output_file = r'd:\Data C\Downloads\progres\bisnis\static\tattoo\img\bali_ink_logo_transparent.png'
remove_background(input_file, output_file)
