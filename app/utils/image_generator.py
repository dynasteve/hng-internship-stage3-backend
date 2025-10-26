from PIL import Image, ImageDraw, ImageFont

def generate_top5_gdp_image(top5_countries):
    if not top5_countries:
        return

    width, height = 800, 400
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    # Draw title
    draw.text((20, 20), "Top 5 Countries by Estimated GDP", fill="black", font=font)

    # Find max GDP
    max_gdp = max(c.estimated_gdp for c in top5_countries)
    bar_width = 100
    spacing = 30
    x = 100
    y_bottom = height - 50

    for country in top5_countries:
        bar_height = int((country.estimated_gdp / max_gdp) * 250)
        y_top = y_bottom - bar_height

        draw.rectangle([x, y_top, x + bar_width, y_bottom], fill="skyblue")
        draw.text((x, y_bottom + 5), country.name, fill="black", font=font)
        x += bar_width + spacing

    img.save("top5_gdp.png")
    print("✅ Saved image as top5_gdp.png")
