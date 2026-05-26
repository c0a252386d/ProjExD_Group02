import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100
HEIGHT = 650
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内にあるか判定する
    """
    yoko, tate = True, True

    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Player(pg.sprite.Sprite):
    """
    プレイヤーに関するクラス
    """

    delta = {
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self):
        super().__init__()
        self.image = pg.image.load("fig/alien1.png")
        self.rect = self.image.get_rect()

        # スタート位置
        self.rect.center = (50, HEIGHT//2)

        # ★変更：速度設定
        self.normal_speed = 1
        self.dash_speed = 3
        self.speed = self.normal_speed

        self.move_flag = False

        # ★追加：スタミナ
        self.stamina = 100
        self.max_stamina = 100

        # 足音
        self.walk_se = pg.mixer.Sound("sound/asioto.mp3")

    def update(self, key_lst: list[bool]):
        """
        プレイヤー更新
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        moving = (sum_mv != [0, 0])  # ★追加：移動中判定
        # ★追加：ダッシュ処理
        if key_lst[pg.K_LSHIFT] and self.stamina > 0:
            self.speed = self.dash_speed
            self.stamina -= 1
        else:
            self.speed = self.normal_speed
            if not moving:
                self.stamina += 0.2

        # ★追加：スタミナ制限
        if self.stamina < 0:
            self.stamina = 0
        if self.stamina > self.max_stamina:
            self.stamina = self.max_stamina

        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

        self.rect.move_ip(
            self.speed * sum_mv[0],
            self.speed * sum_mv[1]
        )

        # 画面外判定
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(
                -self.speed * sum_mv[0],
                -self.speed * sum_mv[1]
            )

        # 移動判定
        if sum_mv != [0, 0]:
            self.move_flag = True

            if not self.walk_se.get_num_channels():
                self.walk_se.play(-1)
        else:
            self.move_flag = False
            self.walk_se.stop()


class Oni(pg.sprite.Sprite):
    """
    鬼に関するクラス
    """

    def __init__(self):
        super().__init__()
        self.image_back = pg.image.load("fig/2.png")
        self.image_front = pg.transform.flip(
            self.image_back,
            True,
            False
        )

        self.image = self.image_back
        self.rect = self.image.get_rect()

        # 開始時
        self.rect.center = (WIDTH-50, HEIGHT//2)
        self.look_flag = False

        # 次に振り向く時間
        self.next_turn = time.time() + random.uniform(5, 15)

        # 音声
        self.voice = pg.mixer.Sound("sound/sound.mp3")
        self.voice.play(-1)

    def update(self, n:int, turn_min:int, turn_max: int):
        """
        鬼更新
        """
        now = time.time()

        if not self.look_flag:
            if now >= self.next_turn:
                self.look_flag = True
                self.image = self.image_front
                self.voice.stop()
                self.next_turn = now + n #次ステージ：n秒後に後ろ向き

        else:
            if now >= self.next_turn:
                self.look_flag = False
                self.image = self.image_back
                self.voice.play(-1)
                self.next_turn = now + random.uniform(turn_min, turn_max) #次ステージ：振り向き間隔


#爆弾クラスの追加
class Bomb(pg.sprite.Sprite):
    def __init__(self, life:int):
        super().__init__()
        rad = 40
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image,(255,0,0),(rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.image.set_alpha(200)
        self.rect = self.image.get_rect()
        centerx = random.randint(0,WIDTH)
        centery = random.randint(0,HEIGHT)
        self.rect.center = centerx, centery
        self.life = life
        
    def update(self, player):
        self.life -= 1
        if self.life <= 0:
            if self.rect.colliderect(player.rect):
                return "boom"
            self.kill()
        elif self.life <= 3:
            self.image.set_alpha(255)
        elif self.life %30 >= 15:
            self.image.set_alpha(0)
        else:
            self.image.set_alpha(120)


def draw_text(
        screen: pg.Surface,
        text: str,
        size: int,
        color: tuple[int, int, int],
        center: tuple[int, int]
):
    """
    文字表示
    """
    font = pg.font.Font(None, size)
    txt = font.render(text, True, color)
    rect = txt.get_rect()
    rect.center = center
    screen.blit(txt, rect)


def gameover(screen: pg.Surface):
    fonto = pg.font.Font(None, 80)
    txt = fonto.render("Game Over", True, (255, 0, 0))
    screen.blit(txt, [WIDTH//2-150, HEIGHT//2])


def clear(screen: pg.Surface):
    fonto = pg.font.Font(None, 80)
    txt = fonto.render("Clear!", True, (0, 255, 0))
    screen.blit(txt, [WIDTH//2-150, HEIGHT//2])


# ★追加：スタミナバー表示
def draw_stamina(screen: pg.Surface, player: Player):
    pg.draw.rect(screen, (255, 255, 255), [20, 20, 200, 20])
    pg.draw.rect(screen, (0, 255, 0), [20, 20, player.stamina * 2, 20])
    pg.draw.rect(screen, (0, 0, 0), [20, 20, 200, 20], 2)

    draw_text(screen, "STAMINA", 30, (255, 255, 255), (120, 55))

n = 3
turn_min = 5
turn_max = 15 #次ステージ：追加
def main():
    pg.display.set_caption("こうかとんが転んだ")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()

    bg_img = pg.image.load("fig/pg_bg.jpg")
    player = Player()
    oni = Oni()
    bombs = pg.sprite.Group()
    bomb_time = 0 #次ステージ：爆弾の規定

    while True:
        key_lst = pg.key.get_pressed()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_r:
                return "restart"

        screen.blit(bg_img, [0, 0])

        player.update(key_lst)
        oni.update(n, turn_min, turn_max) #次ステージ：追加した変数の規定

        screen.blit(player.image, player.rect)
        screen.blit(oni.image, oni.rect)

        # ★追加：スタミナ表示
        draw_stamina(screen, player)
        
        if n>=4: #1回クリア後、15秒ごとに爆弾が現れる
            bomb_time += 1
            if bomb_time %750 == 0:
                for bomb in range(n+2): #ステージ数+4個の爆弾生成
                    bombs.add(Bomb(200))
                    pg.display.update()
            
            for bomb in bombs: #playerが爆弾の爆発時に当たったらgameover
                crash = bomb.update(player)
                screen.blit(bomb.image, bomb.rect)
                if crash == "boom":
                    gameover(screen)
                    pg.display.update()
                    time.sleep(3)
                    return

        # ゲームオーバー
        if oni.look_flag and player.move_flag:
            gameover(screen)
            pg.display.update()
            time.sleep(3)
            return

        # クリア
        if player.rect.colliderect(oni.rect):
            clear(screen)
            pg.display.update()
            time.sleep(3)
            return "clear" #次ステージ：変更

        pg.display.update()
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    while True:
        ret = main()
        if ret == "clear": #次ステージ：クリアのたび難易度up
            n += 1
            if turn_min > 1:
                turn_max -= 2
                turn_min -= 1
        elif ret != "restart":
            break
    pg.quit()
    sys.exit()