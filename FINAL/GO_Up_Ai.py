import pygame
import random
from os import listdir
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as plt

pygame.init()
pygame.mixer.init()

pygame.display.set_caption("GO UP")

bg_color=(255,255,255)
WIDTH,HEIGHT=1650,950
fps=60
player_vel=10
e=0
score=0
score1=str(score)
y1_score=0
d=0
c=0
y_out =1000

window=pygame.display.set_mode((WIDTH,HEIGHT))

'''font1=pygame.font.SysFont("araiblack",200)
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
    c_xaxis.append(b)'''
# Add after line 83 (after all imports and global variables)
class Direction:
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

class GoUpEnvironment:
    def __init__(self):
        self.block_size = 96
        self.platform_height = 205
        self.base_win = -20360
        self.movement_speed = player_vel

        # Generate initial platforms
        self.final_platforms = self.generate_platforms()
        self.platforms = self.copy_platforms(self.final_platforms)

        # Game state variables
        self.direction = Direction.RIGHT
        self.is_paused = False
        self.platforms_reached = 0
        self.steps=0
        self.offset_x = 0
        self.offset_y = 0
        self.speed_inc = 0
        # Platform tracking
        self.platform_history = []
        self.current_platforms = []
        for platform in self.platforms:
            if platform['y_pos']==640:  # Get first platform
                self.current_platforms=[platform]
        self.window = pygame.display.set_mode((WIDTH, HEIGHT))
        with open("Practice_files//Color_c.txt", "r") as f:
            color = f.read()
        self.background, self.bg_image = get_background(color + ".png")

        # Initialize player and objects
        self.player = Player(WIDTH//2+20, HEIGHT-160, 50, 50)
        self.objects = self.object_pos()
        self.clock = pygame.time.Clock()
        self.reset()

    def generate_platforms(self):
        platforms = []
        current_y = 640  # Start from bottom
        is_left = True

        while current_y > -20360:
            # Generate 2 platforms per level (left and right side)
            platform = self._generate_single_platform(current_y, "left" if is_left else "right")
            platforms.append(platform)

            current_y -= self.platform_height  # Move up by fixed amount
            is_left = not is_left

        return platforms

    def _generate_single_platform(self, y_pos, side):
        platform_length = random.choice([3, 4])

        # More controlled x-position generation
        if side == "left":
            base_x = random.randint(430, WIDTH//2 - platform_length * (self.block_size))
        else:
            base_x = random.randint(WIDTH//2, WIDTH - (platform_length * self.block_size) - 440)

        # Create platform blocks
        platform_blocks = []
        for i in range(platform_length):
            x_pos = base_x + (i * self.block_size)
            block = Block(x_pos, y_pos, self.block_size, 96, 96, 0)
            platform_blocks.append(block)

        # Store platform metadata
        platform_data = {
            'start_x': base_x,
            'end_x': base_x + (platform_length * self.block_size),
            'y_pos': y_pos,
            'length': platform_length,
            'side': side,
            'blocks': platform_blocks
        }

        return platform_data

    def update_platform_tracking(self):
        try:
        # Find the platform player is currently on
            current_platform = []

            for platform in self.platforms:
                if (self.player.rect.bottom >= platform['y_pos']-5 and
                    self.player.rect.bottom <= platform['y_pos'] + 12 and  # Small tolerance
                    platform['start_x'] <= self.player.rect.centerx <= platform['end_x']):
                    current_platform = platform
                    break
            if(self.player.rect.bottom>845):
                #print("Resetting")
                for platform in self.platforms:
                    if platform['y_pos']>=630:  # Get first platform
                        self.current_platforms =[platform]
            if current_platform:
            # Check if falling back to previous platform
                if self.platform_history and current_platform['y_pos'] > self.platform_history[-1]['y_pos']:
                    return -5.0  # Penalty for falling back

                self.current_platforms = self._get_next_platforms(current_platform['y_pos'])
                #print(self.current_platforms)
                # Only add to history if it's a new platform
                if current_platform not in self.platform_history:
                    self.platforms_reached += 1
                    self.steps =0
                    self.platform_history.append(current_platform)
                    if len(self.platform_history) > 3:
                        self.platform_history.pop(0)

                # Calculate platform-specific rewards
                    return self._calculate_platform_rewards(current_platform)

            return 0  # No new platform reached

        except Exception as e:
            print(f"Error in update_platform_tracking: {e}")
            return 0

    def _calculate_platform_rewards(self, current_platform):
        try:
            reward = 0

            # Base reward for reaching new platform
            reward += 20.0

            # Bonus for height gained
            height_progress = (HEIGHT + 28020 - self.player.rect.y) / (HEIGHT + 28020)
            reward *= (1 + height_progress)

            # Bonus for efficient movement
            if len(self.platform_history) >= 2:
                last_platform = self.platform_history[-2]
                if current_platform['side'] != last_platform['side']:
                    reward *= 1.2  # Bonus for successful side switching

                if current_platform['y_pos'] >= last_platform['y_pos']:
                    reward *= 0.5

            # Bonus for maintaining momentum
            if self.speed_inc > 0:
                reward *= (1 + self.speed_inc)

            return reward

        except Exception as e:
            print(f"Error in _calculate_platform_rewards: {e}")
            return 0

    def _get_next_platforms(self, current_y):
        visible_platforms = []

        for platform in self.platforms:
            if platform['y_pos'] < current_y and \
                platform['y_pos'] > current_y - (self.platform_height*1.1 ):  # Show next 3 platforms
                visible_platforms.append(platform)
        return visible_platforms

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
        platforms = [block for platform in self.platforms for block in platform['blocks']]

        # Combine all objects
        objects = [*floor, *side_walls, *platforms]

        return objects

    def copy_platforms(self, platforms):
        """Deep copy platforms while preserving block objects"""
        copied_platforms = []
        for platform in platforms:
            copied_platform = {
                'blocks': [Block(block.rect.x, block.rect.y, block.width, block.height, 96, 0)
                          for block in platform['blocks']],
                'start_x': platform['start_x'],
                'end_x': platform['end_x'],
                'y_pos': platform['y_pos'],
                'length': platform['length'],
                'side': platform['side']
            }
            copied_platforms.append(copied_platform)
        return copied_platforms

    def reset(self):
        # Reset game state variables
        self.speed_inc = 0
        self.score = 0
        self.base_win = -20360
        self.steps=0
        self.platforms_reached = 0
        self.direction = Direction.RIGHT

        # Reset platform tracking
        self.platform_history = []
        self.current_platforms = []
        for platform in self.platforms:
            if platform['y_pos']==640:  # Get first platform
                self.current_platforms=[platform]

        # Reset platforms to initial configuration
        self.platforms = self.copy_platforms(self.final_platforms)

        # Reset player
        self.player = Player(WIDTH//2+20, HEIGHT-160, 50, 50)
        self.player.x_vel = 0
        self.player.y_vel = 0
        self.player.jump_count = 0

        # Reset objects
        self.objects = self.object_pos()

    def _move(self, action):
        # [straight, right, left]
        clock_wise = [Direction.RIGHT, Direction.UP, Direction.LEFT, Direction.DOWN]
        idx = clock_wise.index(self.direction)

        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx]  # no change
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]  # right turn r -> u -> l -> d
        else:  # [0, 0, 1]
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]  # left turn r -> d -> l -> u

        self.direction = new_dir

        # Apply movement based on direction
        if self.direction == Direction.RIGHT:
            if self.player.rect.x < WIDTH - 100:
                self.player.move_right(self.movement_speed)
        elif self.direction == Direction.LEFT:
            if self.player.rect.x > 100:
                self.player.move_left(self.movement_speed)
        elif self.direction == Direction.UP:
            if self.player.jump_count == 0:
                self.player.jump()

    def step(self, action):
        reward = 0
        list = [300,350,450,550,650,750,850,950,1050]
        done = False
        self.steps += 1
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                plt.close('all')
                quit()
            elif event.type == pygame.WINDOWMINIMIZED:
                self.is_paused = True
            elif event.type == pygame.WINDOWRESTORED:
                self.is_paused = False

        if self.is_paused:
            pygame.time.wait(100)
            return 0, False, self.score

        # Execute action
        self._move(action)
        # Update game state
        self.player.loop(fps)
        handle_move(self.player, self.objects)

        # Update current platforms list
        # Update platform tracking and get rewards
        platform_reward = self.update_platform_tracking()
        reward += platform_reward

        self.score = (self.platforms_reached*10)

        # Update screen position and scroll
        if self.player.rect.y < 500:
            self.speed_inc = min(self.speed_inc + 0.005, 2.0)
            scroll_speed = 2 * self.speed_inc

                # Move blocks down
            for platform in self.objects:
                platform.rect.y += scroll_speed

            for i in self.platforms:
                i['y_pos'] += scroll_speed

            # Update boundaries and positions
            if hasattr(self, 'last_platform_y'):
                self.last_platform_y += scroll_speed
            self.player.rect.y += scroll_speed
            self.base_win += scroll_speed

            # Position penalties
        for i in list:
            if(self.steps==i):
                reward -= 5

        if self.player.rect.x <= 370:
            reward -= abs(44 - self.player.rect.x) * 0.1
        elif self.player.rect.x >= WIDTH - 370:
            reward -= abs(self.player.rect.x - (WIDTH - 94)) * 0.1

            # Game end conditions
        if self.player.rect.y < self.base_win:  # Win
            reward += 2000 * (1 + self.platforms_reached / 100)  # Bonus for efficiency
            done = True
            print(f"Level Complete! Platforms reached: {self.platforms_reached} Steps: {self.steps}")
            return reward, done, self.score

        elif self.player.rect.y > 950 or self.player.rect.x <= 360 or self.player.rect.x >= WIDTH - 360 or self.steps>1200:  # die
            reward -= 100
            done = True
            print(f"Game Over - Platforms reached {self.platforms_reached} Steps: {self.steps}")
            return reward, done, self.score

        # Draw current state
        draw(self.window, self.background, self.bg_image,
                self.player,self.objects,
                self.offset_x, self.offset_y)

        pygame.display.update()
        self.clock.tick(60)
        #if(reward!=0):
            #print(reward)

        return reward, done, self.score

    def _get_state(self):
        try:
            state = [
                # Player position and movement
                self.player.x_vel > 0,  # Moving right
                self.player.x_vel < 0,  # Moving left
                self.player.y_vel < 0,  # Moving up
                self.player.y_vel > 0,  # Falling

                # Danger detection (collision checks)
                self.player.rect.x <= 365,  # Too close to left wall
                self.player.rect.x >= WIDTH - 365,  # Too close to right wall
                self.player.rect.y > 935,  # About to fall too far

                # Next platform relative position
                False,  # Initialize platform detection flags
                False,
                False,
                False
            ]

            # Update next platform relative position
            if self.current_platforms:
                #print(self.current_platforms[0]['y_pos'])
                next_platform = self.current_platforms[0]
                state[7] = next_platform['y_pos'] < self.player.rect.y  # Platform is above
                state[8] = next_platform['start_x'] > self.player.rect.x  # Platform is to the right
                state[9] = next_platform['end_x'] < self.player.rect.x  # Platform is to the left
                state[10] = next_platform['side'] == 'left'  # Platform is on left side
            #print(np.array(state, dtype=np.float32)))
            return np.array(state, dtype=np.float32)

        except Exception as e:
            print(f"Error in _get_state: {e}")
            return np.zeros(11, dtype=np.float32)
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
'''start_img=pygame.image.load("Practice_files//start_btn.png").convert_alpha()
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
Info_button=Button(1530,0,info_img,1)'''


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
        self.y_vel=-self.GRAVITY*10.5
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
'''class Fire(Object):
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
            self.animation_count=0'''

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
'''class Item(pygame.sprite.Sprite):
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
    return pygame.transform.scale2x(surface)'''

#draw the bckground
def draw(window,background,bg_image,player,objects,offset_x,offset_y):
    for tile in background:
        window.blit(bg_image,tile)

    for obj in objects:
        obj.draw(window,offset_x,offset_y)

    #item_x1.draw(window,offset_x,offset_y)

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