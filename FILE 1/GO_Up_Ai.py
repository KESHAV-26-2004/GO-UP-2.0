import pygame
import random
import os
import math
from os import listdir
from os.path import isfile, join
from threading import Timer
import time
import sys
import numpy as np

pygame.init()
pygame.mixer.init()

pygame.display.set_caption("GO UP")

bg_color=(255,255,255)
WIDTH,HEIGHT=1650,950
fps=60
player_vel=9
e=0
score=0
score1=str(score)
y1_score=0
d=0
c=0

clock=pygame.time.Clock()

window=pygame.display.set_mode((WIDTH,HEIGHT))

font1=pygame.font.SysFont("araiblack",200)
font2=pygame.font.SysFont("araiblack",50)
font3=pygame.font.SysFont("araiblack",85)
text_col1=(80,100,170)
text_col2=(0,0,0)
text_col3=(255,20,20)
text_col4=(190,0,0)
text_col5=(0,50,50)
a_yaxis=[]
c_xaxis=[]
side1_l=[]
y_axis=854
side1_y=854

for i in range(150):
    y_axis-=192
    a_yaxis.append(y_axis)
#print(a_yaxis)

for i in range(400):
    side1_y-=96
    side1_l.append(side1_y)

for i in range(150):
    b=[]
    x0=random.randint(80,120)
    x1=random.randint(230,420)
    x2=random.randint(570,780)
    x3=random.randint(910,1070)
    x4=random.randint(1220,1400)
    x5=random.randint(70,280)
    x6=random.randint(410,670)
    x7=random.randint(790,915)
    x8=random.randint(1130,1400)
    x9=random.randint(70,450)
    x10=random.randint(596,910)
    x11=random.randint(1070,1450)
    b.append(x0)
    b.append(x1)
    b.append(x2)
    b.append(x3)
    b.append(x4)
    b.append(x5)
    b.append(x6)
    b.append(x7)
    b.append(x8)
    b.append(x9)
    b.append(x10)
    b.append(x11)
    c_xaxis.append(b)
# Add after line 83 (after all imports and global variables)
class GoUpEnvironment:
    def __init__(self):
        self.training_mode = True
        self.block_size = 96
        self.y_out = HEIGHT
        self.speed_inc = 0
        self.offset_x = 0
        self.offset_y = 0
        self.scroll_area_width = 200
        self.background_y = 0
        self.steps = 0
        self.window = window
        self.clock = clock
        self.initial_delay = 30
        self.is_paused = False
        
        with open("Practice_files//Color_c.txt", "r") as f:
            color = f.read()
        self.background, self.bg_image = get_background(color + ".png")
        self.item_x1 = Item(100, 758, 128, 97)
        
        # Initialize tracking variables
        self.blocks_reached = 0
        self.last_block_y = HEIGHT
        self.highest_y = HEIGHT
        self.total_reward = 0
        self.speed_inc = 0
        self.steps = 0
        
        # Initialize game objects
        self.reset() 
    def generate_platforms(self):
        platforms = []
        current_y = 620  # Start from bottom
        
        while current_y > -28020:  # Your game's height limit
            # Decide platform length (3 or 4 blocks)
            platform_length = random.choice([3, 4])
            base_x = random.randint(400, WIDTH//2 - platform_length * self.block_size)
            base_x2 = WIDTH-base_x
            # Decide platform x position
            if 0.25 < random.random() < 0.5:  # Left side platform
                base_x = random.randint(100, WIDTH//2 - platform_length * self.block_size)
                base_x2 = WIDTH-base_x
                x_direction = 1  # Build towards right
            elif 0.5< random.random() < 0.75:   # Right side platform
                base_x = random.randint(WIDTH//2, WIDTH - platform_length * self.block_size - 100)
                base_x2 = WIDTH-base_x
                x_direction = -1  # Build towards left
                
            # Create platform blocks
            for i in range(platform_length):
                x_pos = base_x + (i * self.block_size * x_direction)
                x_pos2 = base_x2 + (i * self.block_size * (-x_direction))
                block = Block(x_pos, current_y, self.block_size, 96, 96, 0)  # Using standard block
                block2 = Block(x_pos2, current_y, self.block_size, 96, 96, 0)  # Using standard block
                platforms.append(block)
                platforms.append(block2)
            
            # Move up for next platform (with some randomness in spacing)
            current_y -= 234  # Adjusted jump height
            
        return platforms
    def object_pos(self):
        floor = [Block(i * self.block_size, HEIGHT - self.block_size, 
                  self.block_size, 96, 0, 0)
             for i in range(-WIDTH//self.block_size, (WIDTH*2)//self.block_size)]
    
        # Create side walls (optional, for boundaries)
        side_walls = [
            Block(0, y, 32, 96, 240, 64) 
            for y in range(HEIGHT, -28020, -96)  # Left wall
        ]
        side_walls.extend([
            Block(WIDTH - 32, y, 32, 96, 240, 64) 
            for y in range(HEIGHT, -28020, -96)  # Right wall
        ])
        
        # Generate main platforms
        platforms = self.generate_platforms()
        
        # Combine all objects
        objects = [*floor, *side_walls, *platforms]
        
        return objects

    def reset(self):
        try:
            # Reset everything to initial state
            self.offset_y = 0
            self.offset_x = 0
            self.speed_inc = 0
            self.blocks_reached = 0
            self.last_block_y = HEIGHT
            self.highest_y = HEIGHT
            self.total_reward = 0
            self.y_out = HEIGHT
            self.steps = 0
            self.delay_counter = self.initial_delay
            self.is_paused = False  # Reset pause state
            
            # Spawn player in a safe position
            self.player = Player(WIDTH//2, HEIGHT-150, 50, 50)
            self.player.x_vel = 0
            self.player.y_vel = 0
            self.player.jump_count = 0
            
            # Generate objects
            self.objects = self.object_pos()
            self.previous_y = self.player.rect.y
            
            return self._get_state()
        except pygame.error as e:
            print(f"Pygame error in reset: {e}")
            pygame.init()  # Try reinitializing pygame
            return np.zeros(8, dtype=np.float32)
        except Exception as e:
            print(f"Error in reset: {e}")
            return np.zeros(8, dtype=np.float32)

    def step(self, action):
        previous_y = self.player.rect.y
        reward = 0
        done = False
        
        try:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return self._get_state(), 0, True, {}
                elif event.type == pygame.WINDOWMINIMIZED:
                    self.is_paused = True
                elif event.type == pygame.WINDOWRESTORED:
                    self.is_paused = False

            if self.is_paused:
                pygame.time.wait(100)
                return self._get_state(), 0, False, {}

            # Execute action
            if action == 0:  # Do nothing
                self.player.x_vel = 0
            elif action == 1:  # Left
                if self.player.rect.x > 33:
                    self.player.move_left(player_vel + self.speed_inc)
            elif action == 2:  # Right
                if self.player.rect.x < WIDTH - 33:
                    self.player.move_right(player_vel)
            elif action == 3:  # Jump
                if self.player.jump_count == 0:
                    self.player.jump()
                    # Find platforms above player
                    platforms = []
                    current_platform = []
                    last_x = None
                    
                    # Group adjacent blocks into platforms
                    for obj in self.objects:
                        if (isinstance(obj, Block) and 
                            obj.rect.y < self.player.rect.y and
                            obj.rect.y > self.player.rect.y - 300 and
                            obj.rect.x != 0 and 
                            obj.rect.x != WIDTH - 32):
                            
                            if last_x is None or abs(obj.rect.x - last_x) <= self.block_size:
                                current_platform.append(obj)
                            else:
                                if current_platform:
                                    platforms.append(current_platform)
                                current_platform = [obj]
                            last_x = obj.rect.x + obj.width
                    
                    if current_platform:
                        platforms.append(current_platform)
                    
                    # Reward for jumping when near a platform
                    if platforms:
                        nearest_platform = min(platforms, 
                            key=lambda p: ((p[0].rect.x - self.player.rect.x)**2 + 
                                        (p[0].rect.y - self.player.rect.y)**2)**0.5)
                        
                        platform_left = min(block.rect.x for block in nearest_platform)
                        platform_right = max(block.rect.x + block.width for block in nearest_platform)
                        platform_y = nearest_platform[0].rect.y
                        
                        # Check if jump is well-timed
                        if (abs(platform_y - self.player.rect.y) < 200 and  # Reachable height
                            platform_left - 50 <= self.player.rect.x <= platform_right + 50):  # Good horizontal position
                            reward += 10.0  # Reward for well-timed jump

            # Update game state
            self.player.loop(fps)
            handle_move(self.player, self.objects)

            # Find current platform player is on
            current_platform = []
            last_x = None
            for obj in self.objects:
                if (isinstance(obj, Block) and 
                    self.player.rect.bottom == obj.rect.top and
                    obj.rect.x != 0 and 
                    obj.rect.x != WIDTH - 32):
                    
                    if last_x is None or abs(obj.rect.x - last_x) <= self.block_size:
                        current_platform.append(obj)
                    last_x = obj.rect.x + obj.width

            # Platform-based rewards
            if current_platform:
                platform_y = current_platform[0].rect.y
                if not hasattr(self, 'last_platform_y') or platform_y < self.last_platform_y - 50:
                    self.blocks_reached += 1
                    self.last_platform_y = platform_y
                    
                    # Reward based on platform height and length
                    platform_reward = 20.0 * (1.1 ** self.blocks_reached)
                    platform_reward *= len(current_platform) / 3.0  # Extra reward for longer platforms
                    reward += platform_reward
                    print(f"Reached platform {self.blocks_reached}! Reward: {platform_reward:.1f}")

            # Update screen position and block movement
            if self.player.rect.y < 500:
                self.speed_inc += 0.005
                scroll_speed = 2 * self.speed_inc
                
                # Move blocks down
                for obj in self.objects:
                    if isinstance(obj, Block):
                        obj.rect.y += scroll_speed
                
                # Update boundaries and positions
                self.y_out += scroll_speed
                self.offset_y += scroll_speed
                if hasattr(self, 'last_platform_y'):
                    self.last_platform_y += scroll_speed
                self.player.rect.y += scroll_speed
                self.highest_y += scroll_speed

            # Anti-camping mechanism
            if self.steps % 50 == 0:
                if hasattr(self, 'last_positions'):
                    avg_movement = sum(abs(pos - self.player.rect.y) for pos in self.last_positions) / len(self.last_positions)
                    if avg_movement < 10:
                        reward -= 50
                        print("Camping penalty applied!")
                self.last_positions = self.last_positions[-4:] + [self.player.rect.y] if hasattr(self, 'last_positions') else [self.player.rect.y]

            # Progressive side penalty
            if self.player.rect.x <= 44 or self.player.rect.x >= WIDTH - 94:
                side_penalty = 1.0 * (1 + self.steps / 1000)
                reward -= side_penalty

            # Height progress reward
            y_progress = previous_y - self.player.rect.y
            if y_progress > 0:
                reward += y_progress * 0.2

            # New height record reward
            if not hasattr(self, 'highest_y'):
                self.highest_y = self.player.rect.y
            if self.player.rect.y < self.highest_y:
                reward += 5.0
                self.highest_y = self.player.rect.y

            # Game end conditions
            if self.player.rect.y < -28020:  # Win
                reward += 1000
                done = True
            elif self.player.rect.y > self.y_out:  # Fall
                reward -= 500
                done = True

            # Update screen position
            if self.player.rect.y < 500:
                self.y_out -= 2 * self.speed_inc
                self.offset_y -= 2 * self.speed_inc

            # Draw current state
            draw(self.window, self.background, self.bg_image, self.player, 
                self.objects, self.offset_x, self.offset_y, self.item_x1)
            pygame.display.update()

            self.steps += 1
            return self._get_state(), reward, done, {}
            
        except Exception as e:
            print(f"Error in step: {e}")
            return self._get_state(), -500, True, {}

    def _get_state(self):
        try:
            state = np.zeros(16, dtype=np.float32)  # Make sure it's 16 dimensions
            
            # Player information
            state[0] = (self.player.rect.x - 44) / (WIDTH - 138)
            state[1] = (self.player.rect.y + 28020) / (HEIGHT + 28020)
            state[2] = self.player.y_vel / 20.0
            state[3] = self.player.jump_count
            
            # Find nearest platform above player
            platforms = []
            current_platform = []
            last_x = None
            
            for obj in self.objects:
                if (isinstance(obj, Block) and 
                    obj.rect.y < self.player.rect.y and
                    obj.rect.y > self.player.rect.y - 300 and
                    obj.rect.x != 0 and 
                    obj.rect.x != WIDTH - 32):
                    
                    if last_x is None or abs(obj.rect.x - last_x) <= self.block_size:
                        current_platform.append(obj)
                    else:
                        if current_platform:
                            platforms.append(current_platform)
                        current_platform = [obj]
                    last_x = obj.rect.x + obj.width
            
            if current_platform:
                platforms.append(current_platform)
            
            # Platform information
            if platforms:
                nearest_platform = platforms[0]
                platform_left = min(block.rect.x for block in nearest_platform)
                platform_right = max(block.rect.x + block.width for block in nearest_platform)
                platform_y = nearest_platform[0].rect.y
                
                state[4] = (platform_left - self.player.rect.x) / WIDTH
                state[5] = (platform_right - self.player.rect.x) / WIDTH
                state[6] = (platform_y - self.player.rect.y) / HEIGHT
                state[7] = len(nearest_platform) / 4.0  # Platform length normalized
                state[8] = float(platform_left > self.player.rect.x)
                state[9] = float(platform_left < self.player.rect.x)
                state[10] = float(abs(platform_y - self.player.rect.y) < 200)
                
                if len(platforms) > 1:
                    next_platform = platforms[1]
                    next_left = min(block.rect.x for block in next_platform)
                    next_y = next_platform[0].rect.y
                    state[11] = (next_left - self.player.rect.x) / WIDTH
                    state[12] = (next_y - self.player.rect.y) / HEIGHT
                    state[13] = float(next_left > platform_right)
            
            # Progress tracking
            state[14] = (-28020 - self.player.rect.y) / 28020
            state[15] = self.speed_inc / 2.0
            
            return state
            
        except Exception as e:
            print(f"Error in _get_state: {e}")
            return np.zeros(16, dtype=np.float32)

#Import button from png
class Button():
    def __init__(self,x,y,image,scale):
        width=image.get_width()
        height=image.get_height()
        self.image=pygame.transform.scale(image,
            (int((width*scale)*3/2),int((height*scale)*3/2)))
        #print(width*scale,height*scale)
        self.rect=self.image.get_rect()
        self.rect.topleft=(x,y)
        self.clicked=False

    def draw(self,surface):
        action=False
        #get mouse postion
        pos=pygame.mouse.get_pos()

        #chech mouseover and clicked condtions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0]==1 and self.clicked==False:
                self.clicked=True
                action=True

        if pygame.mouse.get_pressed()[0]==0:
            self.clicked=False

        #drawbutton on screen
        surface.blit(self.image, (self.rect.x, self.rect.y))

        return action

    def draw2(self,surface):
        surface.blit(self.image,(self.rect.x,self.rect.y))

def draw_b(text,font,text_col,x,y):
    img=font.render(text,True,text_col)
    window.blit(img,(x,y))

#load buttons images
start_img=pygame.image.load("Practice_files//start_btn.png").convert_alpha()
start_img=pygame.transform.scale(start_img,((418.5/2),(189/2)))
options_img=pygame.image.load("Practice_files//button_options.png").convert_alpha()
exit_img=pygame.image.load("Practice_files//exit_btn.png").convert_alpha()
exit_img=pygame.transform.scale(exit_img,((360/2),(189/2)))
#quit_img=pygame.image.load("button_quit.png").convert_alpha()
#audio_img=pygame.image.load("button_audio.png").convert_alpha()
#video_img=pygame.image.load("button_video.png").convert_alpha()
back_img=pygame.image.load("Practice_files//button_back.png").convert_alpha()

Blue_img=pygame.image.load("Practice_files//Blue_k.png").convert_alpha()
Blue_img=pygame.transform.scale(Blue_img,((1612/8),(676/10)))

Yellow_img=pygame.image.load("Practice_files//Yellow_k.png").convert_alpha()
Yellow_img=pygame.transform.scale(Yellow_img,((1610/8),(677/10)))

Green_img=pygame.image.load("Practice_files//Green_k.png").convert_alpha()
Green_img=pygame.transform.scale(Green_img,((1611/8),(676/10)))

Pink_img=pygame.image.load("Practice_files//Pink_k.png").convert_alpha()
Pink_img=pygame.transform.scale(Pink_img,((1609/8),(676/10)))

resume_img=pygame.image.load("Practice_files//resume_b.png").convert_alpha()
resume_img=pygame.transform.scale(resume_img,((676/3),(225/(5/2))))

Back_img=pygame.image.load("Practice_files//Back_b.png").convert_alpha()
Back_img=pygame.transform.scale(Back_img,((435/2),(131/(2))))

Audio_img=pygame.image.load("Practice_files//Audio_b.png").convert_alpha()
Audio_img=pygame.transform.scale(Audio_img,((546/2),(133/(2))))

Character_img=pygame.image.load("Practice_files//Character_b.png").convert_alpha()
Character_img=pygame.transform.scale(Character_img,((676/2),(133/(2))))

Background_img=pygame.image.load("Practice_files//Background_b.png").convert_alpha()
Background_img=pygame.transform.scale(Background_img,((698/2),(131/(2))))

VIRTUAL_img=pygame.image.load("Practice_files//Virtual_m.png").convert_alpha()
VIRTUAL_img=pygame.transform.scale(VIRTUAL_img,((594/2),(130/(2))))

FROG_img=pygame.image.load("Practice_files//Frog_m.png").convert_alpha()
FROG_img=pygame.transform.scale(FROG_img,((600/2),(133/(2))))

MASK_img=pygame.image.load("Practice_files//Mask_m.png").convert_alpha()
MASK_img=pygame.transform.scale(MASK_img,((601/2),(135/(2))))

PINK_img=pygame.image.load("Practice_files//Pink_m.png").convert_alpha()
PINK_img=pygame.transform.scale(PINK_img,((598/2),(135/(2))))

info_img=pygame.image.load("Practice_files//button_info.png").convert_alpha()
info_img=pygame.transform.scale(info_img,((512/8),(512/8)))

Off_img=pygame.image.load("Practice_files//Off_b1.png").convert_alpha()
Off_img=pygame.transform.scale(Off_img,((512/5),(512/5)))

On_img=pygame.image.load("Practice_files//On_b1.png").convert_alpha()
On_img=pygame.transform.scale(On_img,((512/5),(512/5)))

Start_img=pygame.image.load("Practice_files//Start_b.png").convert_alpha()
Start_img=pygame.transform.scale(Start_img,((512//8),(512//8)))

#create button instances
start_button=Button(1200,300,start_img,1)
options_button=Button(1200,500,options_img,1)
exit_button=Button(1200,700,exit_img,1)
#quit_button=Button(1200,700,quit_img,1)
#audio_button=Button(1000,300,audio_img,1)
#video_button=Button(1000,500,video_img,1)
back_button=Button(1000,700,back_img,1)
Blue_button=Button(1100,200,Blue_img,1)
Yellow_button=Button(1100,300,Yellow_img,1)
Green_button=Button(1100,400,Green_img,1)
Pink_button=Button(1100,500,Pink_img,1)
Off_button=Button(1100,400,Off_img,1)
On_button=Button(1100,400,On_img,1)
resume_button=Button(1200,300,resume_img,1)
Back_button=Button(1000,700,Back_img,1)
Audio_button=Button(1000,250,Audio_img,1)
Character_button=Button(1000,400,Character_img,1)
Background_button=Button(1000,550,Background_img,1)
VIRTUAL_button=Button(1000,200,VIRTUAL_img,1)
FROG_button=Button(1000,300,FROG_img,1)
MASK_button=Button(1000,400,MASK_img,1)
PINK_button=Button(1000,500,PINK_img,1)
Info_button=Button(1530,0,info_img,1)


def flip(sprites):
    return[pygame.transform.flip(sprite,True,False) for sprite in sprites]

#Load the Character
def load_sprite_sheets(dir1,dir2,width,height,direction=False):
    path=join("assets",dir1,dir2)
    images=[f for f in listdir(path) if isfile(join(path,f))]

    all_sprites={}

    for image in images:
        sprite_sheet=pygame.image.load(join(path,image)).convert_alpha()

        sprites=[]
        for i in range(sprite_sheet.get_width()//width):
            surface=pygame.Surface((width,height),pygame.SRCALPHA,32)
            rect=pygame.Rect(i*width,0,width,height)
            surface.blit(sprite_sheet,(0,0),rect)
            sprites.append(pygame.transform.scale2x(surface))

        if direction:
            all_sprites[image.replace(".png","")+"_right"]=sprites
            all_sprites[image.replace(".png","")+"_left"]=flip(sprites)
        else:
            all_sprites[image.replace(".png","")]=sprites
    return all_sprites


#design the charcter and movement
class Player(pygame.sprite.Sprite):
    with open("Practice_files//character.txt","r") as f:
        cc=f.read()
    color=(255,0,0)
    GRAVITY=1
    ANIMATON_DELAY=2
    SPRITES=load_sprite_sheets("MainCharacters",(cc+".chr"),32,32,True)

    def __init__(self,x,y,width,height):
        super().__init__()
        self.rect=pygame.Rect(x,y,width,height)
        self.x_vel=0
        self.y_vel=0
        self.mask=None
        self.direction="left"
        self.animation_count=0
        self.fall_count=0
        self.jump_count=0
        self.hit=False
        self.hit_count=0

#Jump the player and jump_count is how many times you click jump buttton
    def jump(self):
        self.y_vel=-self.GRAVITY*12
        self.animation_count=0
        self.jump_count+=1
        if self.jump_count==1:
            self.fall_count=0

    def move(self,dx,dy):
        self.rect.x+=dx
        self.rect.y+=dy
        global y1_score
        y1_score=self.rect.y
        with open("Practice_files//y_score.txt","w") as f:
            f.write(str(y1_score))

#hit to fire trap animation
    def make_hit(self):
        self.hit=True
        self.hit_count=0

    def move_left(self,vel):
        if self.rect.x>32:
            self.x_vel=-vel
            if self.direction!= "left":
                self.direction="left"
                self.animation_count=0

    def move_right(self,vel):
        if self.rect.x<1600:
            self.x_vel=vel
            if self.direction!= "right":
                self.direction="right"
                self.animation_count=0

#Gravity
    def loop(self,fps):
        self.y_vel+=min(1,(self.fall_count/fps)*self.GRAVITY)
        self.move(self.x_vel,self.y_vel)

        #hit command
        if self.hit:
            self.hit_count+=1
        if self.hit_count>fps*2:
            self.hit=False
            self.hit_count=0

        self.fall_count+=1
        self.update_sprite()

#what happen when player on object
    def landed(self):
        self.fall_count=0
        self.y_vel=0
        self.jump_count=0

#what happen when player hit the object form bottom,hit head on object
    def hit_head(self):
        self.count=0
        self.y_vel*=-1

#ANIMATION adding in Game of differnt action
    def update_sprite(self):
        sprite_sheet="idle"

        #Hit Fire
        if self.hit:
            sprite_sheet="hit"

        if self.y_vel<0:
            if self.jump_count==1:
                sprite_sheet="jump"
            elif self.jump_count==2:
                sprite_sheet="double_jump"
                self.animation_count+=2
        elif self.y_vel>self.GRAVITY*2:
            sprite_sheet="fall"

        if self.x_vel !=0 and 0<=self.y_vel<(self.GRAVITY*2):
            sprite_sheet="run"

        sprite_sheet_name=sprite_sheet+"_"+self.direction
        sprites=self.SPRITES[sprite_sheet_name]
        sprite_index=(self.animation_count//self.ANIMATON_DELAY)%len(sprites)
        self.sprite=sprites[sprite_index]
        self.animation_count+=1
        self.update()

#update the surface rectangle according the charcter size
    def update(self):
        self.rect=self.sprite.get_rect(topleft=(self.rect.x,self.rect.y))
        self.mask=pygame.mask.from_surface(self.sprite)

    def draw(self,win,offset_x,offset_y):
        win.blit(self.sprite,(self.rect.x-offset_x,self.rect.y-offset_y))

#adding object
class Object(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,name=None):
        super().__init__()
        self.rect=pygame.Rect(x,y,width,height)
        self.image=pygame.Surface((width,height),pygame.SRCALPHA)
        self.width=width
        self.height=height
        self.name=name

    def draw(self,win,offset_x,offset_y):
        win.blit(self.image,(self.rect.x-offset_x,self.rect.y-offset_y))

class Block(Object):
    def __init__(self,x,y,sizex,sizey,x1,y1):
        super().__init__(x,y,sizex,sizey)
        block=get_block(sizex,sizey,x1,y1)
        self.image.blit(block,(0,0))
        self.mask=pygame.mask.from_surface(self.image)

#adding traps
class Fire(Object):
    Animation_Delay=3
    def __init__(self,x,y,width,height):
        super().__init__(x,y,width,height,"fire")
        self.fire=load_sprite_sheets("Traps","Fire",width,height)
        self.image=self.fire["off"][0]
        self.mask=pygame.mask.from_surface(self.image)
        self.animation_count=0
        self.animation_name="off"

    def on(self):
        self.animation_name="on"

    def off(self):
        self.animation_name="off"

    def loop(self):
        sprites=self.fire[self.animation_name]
        sprite_index=(self.animation_count//self.Animation_Delay)%len(sprites)
        self.image=sprites[sprite_index]
        self.animation_count+=1

        self.rect=self.image.get_rect(topleft=(self.rect.x,self.rect.y))
        self.mask=pygame.mask.from_surface(self.image)

        #this help to not increase the animation count at very high value
        if self.animation_count//self.Animation_Delay>len(sprites):
            self.animation_count=0

# Give image and list of tiles
def get_background(name):
    image=pygame.image.load(join("assets","Background",name))
    _,_,width,height=image.get_rect()
    tiles=[]

    for i in range(WIDTH//width+1):
        for j in range(HEIGHT//height+1):
            pos=[i*width,j*height]
            tiles.append(pos)
    return tiles,image

#Getting block from png
def get_block(sizex,sizey,x1,y1):
    path=join("assets","Terrain","Terrain.png")
    image=pygame.image.load(path).convert_alpha()
#creating a surface to append the image
    surface=pygame.Surface((sizex,sizey),pygame.SRCALPHA,32)
#coordinates the smaller block in the image
    rect=pygame.Rect(x1,y1,sizex,sizey)
#add that smaller block on the top of the surface
    surface.blit(image,(0,0),rect)
    return pygame.transform.scale2x(surface)

#Take item and draw it on window screen
class Item(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,name=None):
        super().__init__()
        self.rect=pygame.Rect(x,y,width,height)
        self.image=pygame.Surface((width,height),pygame.SRCALPHA)
        item1=get_item(128)
        self.image.blit(item1,(0,0))
        self.width=width
        self.height=height
        self.name=name

    def draw(self,win,offset_x,offset_y):
        win.blit(self.image,(self.rect.x-offset_x,self.rect.y-offset_y))

#Give the item by extracting it from image
def get_item(size):
    surface=pygame.Surface((size,size),pygame.SRCALPHA)
    rect=pygame.Rect(0,0,size,size)
    surface.blit(Start_img,(0,0),rect)
    return pygame.transform.scale2x(surface)

#draw the bckground
def draw(window,background,bg_image,player,objects,offset_x,offset_y,item_x1):
    for tile in background:
        window.blit(bg_image,tile)

    for obj in objects:
        obj.draw(window,offset_x,offset_y)

    item_x1.draw(window,offset_x,offset_y)

    player.draw(window,offset_x,offset_y)
    pygame.display.update()

#collision between player and object
def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            # Calculate collision overlap
            dx = obj.rect.centerx - player.rect.centerx
            dy = obj.rect.centery - player.rect.centery
            
            # If player is more to the side than top/bottom, don't count as vertical collision
            if abs(dx) > obj.width * 0.4:  # Using 40% of width as threshold
                continue
                
            if dy > 0:  # Player is above the object
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0:  # Player is below the object
                player.rect.top = obj.rect.bottom
                player.hit_head()
            
            collided_objects.append(obj)
    return collided_objects

#collision in horizontal direction
def collide(player, objects, dx):
    player.update()
    collided_object = None
    
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            # Calculate collision overlap
            overlap_x = obj.rect.centerx - player.rect.centerx
            overlap_y = obj.rect.centery - player.rect.centery
            
            # If more vertical overlap than horizontal, don't handle as side collision
            if abs(overlap_y) <= obj.height * 0.4:  # Using 40% of height as threshold
                collided_object = obj
                
                # Push player out horizontally
                if overlap_x > 0:  # Player is to the left
                    player.rect.right = obj.rect.left
                else:  # Player is to the right
                    player.rect.left = obj.rect.right
                
    player.update()
    return collided_object

#Handle movement
def handle_move(player,objects):
    #global life_1
    #life_1=2
    keys=pygame.key.get_pressed()

    player.x_vel=0
    collide_left=collide(player,objects,-player_vel*(0.5))
    collide_right=collide(player,objects,player_vel*(0.5))

    if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and not collide_left:
        player.move_left(player_vel)
    if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and not collide_right:
        player.move_right(player_vel)

    vertical_collide = handle_vertical_collision(player,objects,player.y_vel)

    #It will check all the object which collides with our player
    to_check=[collide_left,collide_right,*vertical_collide]
    #If that object is fire this will work
    for obj in to_check:
        if obj and obj.name=="fire":
            if c==0:
                pygame.mixer.music.load("Practice_files//over.wav")
                pygame.mixer.music.play()
            #player.make_hit()
            #time.sleep(0.2)
            #out_1()

#Game loop
'''def main():
    global score
    global y_out
    global y1_score
    global y_out
    global d
    global speed_inc

    x_m=1
    y_out=900
    speed_inc=1.000

    fire_list=[]

    with open("Practice_files//Color_c.txt","r") as f:
        a=f.read()
    exit_game=False
    background,bg_image=get_background(a+".png")
    block_size=96
    player=Player(300,850,50,50)
    fireyp6=[Fire((c_xaxis[(i)*3][6])+28,(a_yaxis[(i)*3])-62,16,32)
             for i in range(8,19,2)]

    fireyp7=[Fire((c_xaxis[(i)*2][7])+28,(a_yaxis[(i)*2])-62,16,32)
             for i in range(10,30,2)]

    fireyp77=[Fire((c_xaxis[(i)*3][7])+28,(a_yaxis[(i)*3])-62,16,32)
             for i in range(7,20,2)]

    fireyp66=[Fire((c_xaxis[(i)*3][6])+28,(a_yaxis[(i)*3])-62,16,32)
             for i in range(8,20,3)]

    fireyp8=[Fire((c_xaxis[(i)*3][8])+28,(a_yaxis[(i)*3])-62,16,32)
             for i in range(7,15,3)]

    fireg1=[Fire((c_xaxis[(i)*2][1])+28,(a_yaxis[(i)*2])-62,16,32)
            for i in range(1,10,2)]

    fireg2=[Fire((c_xaxis[(i)*2][2])+28,(a_yaxis[(i)*2])-62,16,32)
            for i in range(2,10,2)]

    fireg3=[Fire((c_xaxis[(i)*3][3])+28,(a_yaxis[(i)*3])-62,16,32)
            for i in range(1,6,2)]

    fireg4=[Fire((c_xaxis[(i)*2][0])+28,(a_yaxis[(i)*2])-62,16,32)
            for i in range(2,10,3)]

    fireg5=[Fire((c_xaxis[(i)*2][4])+28,(a_yaxis[(i)*2])-62,16,32)
            for i in range(1,10,3)]

    #fire_b=[Fire((c_xaxis[(i)*3][])+28)]

    fire_all=[*fireyp6,*fireyp7,*fireyp77,*fireg1,*fireg2,*fireg3,*fireyp66,
       *fireyp8,*fireg4,*fireg5]
    for obj in fire_all:
        obj.on()

    floor=[Block(i*block_size,HEIGHT-block_size,block_size,96,0,0)
            for i in range(-WIDTH//block_size,(WIDTH*2)//block_size)]

    Side1=[Block(0,side1_l[i],32,96,240,64) for i in range(400)]

    Side2=[Block(1618,side1_l[i],32,96,240,64) for i in range(400)]

    blocks_gx1=[Block(c_xaxis[i][0],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    blocks_yx1=[Block(c_xaxis[i][5],a_yaxis[i],block_size,96,96,64)
                for i in range(20,40)]

    blocks_px1=[Block(c_xaxis[i][5],a_yaxis[i],block_size,96,96,128)
                for i in range(40,60)]

    blocks_sx1=[Block(c_xaxis[i][9],a_yaxis[i],block_size,96,0,128)
                for i in range(60,80)]

    blocks_bx1=[Block(c_xaxis[i][9],a_yaxis[i],64,64,320,64)
                for i in range(80,105)]

    blocks_spx1=[Block(c_xaxis[i][5],a_yaxis[i],96,32,192,64)
                for i in range(105,120)]

    blocks_spx11=[Block(c_xaxis[i][9],a_yaxis[i],96,32,192,64)
                for i in range(120,130)]

    blocks_slimx1=[Block(c_xaxis[i][5],a_yaxis[i],100,16,270,0)
                for i in range(130,150)]

    blocks_gx2=[Block(c_xaxis[i][1],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    blocks_yx2=[Block(c_xaxis[i][6],a_yaxis[i],block_size,96,96,64)
                for i in range(20,40)]

    blocks_px2=[Block(c_xaxis[i][6],a_yaxis[i],block_size,96,96,128)
                for i in range(40,60)]

    blocks_sx2=[Block(c_xaxis[i][10],a_yaxis[i],block_size,96,0,128)
                for i in range(60,80)]

    blocks_bx2=[Block(c_xaxis[i][10],a_yaxis[i],64,64,320,64)
                for i in range(80,105)]

    blocks_spx2=[Block(c_xaxis[i][6],a_yaxis[i],96,32,192,64)
                for i in range(105,120)]

    blocks_spx22=[Block(c_xaxis[i][10],a_yaxis[i],96,32,192,64)
                for i in range(120,130)]

    blocks_slimx2=[Block(c_xaxis[i][6],a_yaxis[i],100,16,270,0)
                for i in range(130,150)]

    blocks_gx3=[Block(c_xaxis[i][2],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    blocks_yx3=[Block(c_xaxis[i][7],a_yaxis[i],block_size,96,96,64)
                for i in range(20,40)]

    blocks_px3=[Block(c_xaxis[i][7],a_yaxis[i],block_size,96,96,128)
                for i in range(40,60)]

    blocks_sx3=[Block(c_xaxis[i][11],a_yaxis[i],block_size,96,0,128)
                for i in range(60,80)]

    blocks_bx3=[Block(c_xaxis[i][11],a_yaxis[i],64,64,320,64)
                for i in range(80,105)]

    blocks_spx3=[Block(c_xaxis[i][7],a_yaxis[i],96,32,192,64)
                for i in range(105,120)]

    blocks_spx33=[Block(c_xaxis[i][11],a_yaxis[i],96,32,192,64)
                for i in range(120,130)]

    blocks_slimx3=[Block(c_xaxis[i][7],a_yaxis[i],100,16,270,0)
                for i in range(130,150)]

    blocks_gx4=[Block(c_xaxis[i][3],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    blocks_yx4=[Block(c_xaxis[i][8],a_yaxis[i],block_size,96,96,64)
                for i in range(20,40)]

    blocks_px4=[Block(c_xaxis[i][8],a_yaxis[i],block_size,96,96,128)
                for i in range(40,60)]

    #blocks_sx4=[Block(c_xaxis[i][8],a_yaxis[i],block_size,96,0,128)
                #for i in range(100,135)]

    blocks_spx4=[Block(c_xaxis[i][8],a_yaxis[i],96,32,192,64)
                for i in range(105,120)]

    blocks_slimx4=[Block(c_xaxis[i][8],a_yaxis[i],100,16,270,0)
                for i in range(130,150)]

    blocks_gx5=[Block(c_xaxis[i][4],a_yaxis[i],block_size,96,96,0)
                for i in range(0,20)]

    #blocks_yx5=[Block(c_xaxis[i][4],a_yaxis[i],block_size,96,96,64)
                #for i in range(30,65)]

    #blocks_px5=[Block(c_xaxis[i][4],a_yaxis[i],block_size,96,96,128)
                #for i in range(65,100)]

    item_x1=Item(100,758,128,97)

    objects=[*floor,*blocks_gx1,*blocks_yx1,*blocks_px1,*blocks_sx1,*blocks_gx2,
        *blocks_yx2,*blocks_px2,*blocks_sx2,*blocks_gx3,*blocks_yx3,*blocks_px3,
        *blocks_sx3,*blocks_gx4,*blocks_yx4,*blocks_px4,*blocks_gx5,*Side1,
        *Side2,*blocks_spx1,*blocks_spx2,*blocks_spx3,*blocks_spx4,*blocks_bx1,
        *blocks_bx2,*blocks_bx3,*blocks_slimx1,*blocks_slimx2,*blocks_slimx3,
        *blocks_slimx4,*blocks_spx11,*blocks_spx22,*blocks_spx33,
        *fireyp6,*fireyp7,*fireyp77,*fireg1,*fireg2,*fireg3,*fireyp66,*fireyp8,*fireg4,
        *fireg5]

    offset_x=0
    offset_y=0
    scroll_area_width=200

    while not exit_game:
        clock.tick(fps)
        if player.rect.y<500:
            y_out-=2*speed_inc

        if y_out < player.rect.y:
            exit_game=True
            if c==0:
                pygame.mixer.music.load("Practice_files//over.wav")
                pygame.mixer.music.play()
            out_1()
        if 44>=player.rect.x:
            exit_game=True
            out_1()
        if 1540<=player.rect.x:
            exit_game=True
            out_1()

        if player.rect.y<(-28020): #37600 #28000
            exit_game=True
            if c==0:
                pygame.mixer.music.load("Practice_files//Win_1.mp3")
                pygame.mixer.music.play()
            win_1()

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                exit_game=True
                break
            #command for Jump
            if event.type==pygame.KEYDOWN:
                if (event.key==pygame.K_SPACE or event.key==pygame.K_w) and player.jump_count<2:
                    player.jump()

                    if player.jump_count==1 and c==0:
                        pygame.mixer.music.load('Practice_files//Jump_s.mp3')
                        pygame.mixer.music.play()

                    if player.jump_count==2:
                        speed_inc+=0.005

                if event.key==pygame.K_ESCAPE:
                    d=0
                    exit_game=True
                    #start_back1()

        player.loop(fps)
        for obj in fire_all:
            obj.loop()
        handle_move(player,objects)
        draw(window,background,bg_image,player,objects,
            offset_x,offset_y,item_x1)

        if ((player.rect.right-offset_x>=WIDTH - scroll_area_width and
                 player.x_vel>0) or (player.rect.left-offset_x<=
                 scroll_area_width and player.x_vel<0)):
            offset_x += 0 #player.x_vel
        if player.rect.y<500:
            offset_y-=2*speed_inc


        pygame.display.update()
    pygame.quit()
    sys.exit()

main()'''