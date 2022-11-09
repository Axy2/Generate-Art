from PIL import Image, ImageDraw, ImageChops
import os
import random
import colorsys
import argparse
from aleph_client.asynchronous import get_posts, create_store
from aleph_client.chains.ethereum import ETHAccount
from fastapi import FastAPI



#helper functions
def random_color():
    #hue, saturation, value
    h = random.random()
    s = 1
    v = 1
    float_rgb = colorsys.hsv_to_rgb(h,s,v)
    rgb = [int(255*color) for color in float_rgb]
    return tuple(rgb)

#helper functions
def interpolate(start_color, end_color ,factor: float):
    recip = 1 - factor
    return (
        int(start_color[0]*recip + end_color[0]*factor), 
        int(start_color[1]*recip + end_color[1]*factor),
        int(start_color[2]*recip + end_color[2]*factor)
           )


app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
	return {"message": "Main Page!"}


@app.post("/nfts/")
async def generate_nft(name: str) -> str:
    target_size_px = 256
    scale_factor = 2
    image_size_px = target_size_px*scale_factor 
    image_bg_color = (0,0,0)
    start_color = random_color()
    end_color = random_color()
    padding_px = 12 *scale_factor
    image = Image.new("RGB", 
                      size = (image_size_px, image_size_px), 
                      color = image_bg_color)
    #draw some lines
    draw = ImageDraw.Draw(image)
    
    points = []
    num_points = 10
    for _ in range(num_points):
        random_point = (random.randint(padding_px,image_size_px-padding_px),
                        random.randint(padding_px,image_size_px-padding_px))
        points.append(random_point)
    
    #centering
    #old bounding box
    min_x = min(p[0] for p in points)
    max_x = max(p[0] for p in points)
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
#     draw.rectangle((min_x,min_y, max_x,max_y), outline = (220,220,0))

    delta_x = (max_x + min_x)/2 - image_size_px/2
    delta_y = (max_y + min_y)/2 - image_size_px/2
    for idx, point in enumerate(points):
        points[idx] = (point[0] - delta_x, point[1] - delta_y)

    
    
    line_thickness = 0
    n_points = len(points)
    for idx,point in enumerate(points):
        
        #overlay canvas
        overlay_image = Image.new("RGB", 
                      size = (image_size_px, image_size_px), 
                      color = image_bg_color)
        overlay_draw = ImageDraw.Draw(overlay_image)
        
        p1 = point
        if idx == n_points -1:
            p2 = points[0]
        else:
            p2 = points[idx + 1]

        line_xy = (p1, p2)
        factor = idx/n_points
        line_color = interpolate(start_color,end_color, factor)
        line_thickness += scale_factor
        overlay_draw.line(line_xy, fill = line_color, width = line_thickness)
        image = ImageChops.add(image,overlay_image)
    image = image.resize((target_size_px, target_size_px), resample = Image.ANTIALIAS)
    image.save("nft.png")

    account = ETHAccount('8f45a0db3a691ff7aeaaee3953ed8016df868374d8bdfd644f946f011d09e19b')

    file = open(r"./nft.png", "rb").read()
    result = await create_store(file_content= file, account = account, storage_engine = "ipfs")    
    return result.content.item_hash   
