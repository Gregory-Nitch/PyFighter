"""Player object for the game."""

import pygame

from pygame.sprite import Group as SpriteGroup
from pygame import Vector2
from pygame.mask import Mask
from pygame.mixer import Sound
from pygame.surface import Surface
from models.actor import Actor
from models.missile import Missile
from constants import (
    IMG_OFFSETS,
    BASE_LASER_SPEED,
    BASE_CANNON_COOLDOWN,
    BASE_LASER_DMG,
)


class Player(Actor):
    """Player object for the game"""

    def __init__(
        self,
        pos: Vector2,
        hp: int,
        speed: int,
        ship_img,
        ship_mask: Mask,
        offset: dict,
        laser_img,
        laser_mask: Mask,
        laser_sfx: Sound,
        missle_img,
        missle_mask: Mask,
        laser_hit_sfx: Sound,
        explosion_sfx: Sound,
        missile_sfx: Sound,
        idle_animation_frames: list[Surface],
    ):
        super().__init__(pos, hp, speed, ship_img, ship_mask, offset)
        self.cooldown_threshold = BASE_CANNON_COOLDOWN
        self.cooldown_counter = 0
        self.laser_dmg = BASE_LASER_DMG
        self.missile_count = 2
        self.score = 0
        self.laser_img = laser_img
        self.lasers_fired = SpriteGroup()
        self.laser_mask = laser_mask
        self.missile_img = missle_img
        self.missile_mask = missle_mask
        self.missiles_fired = SpriteGroup()
        self.missile_cooldown_threshold = BASE_CANNON_COOLDOWN
        self.missile_cooldown_counter = 0
        self.missile_sfx = missile_sfx
        self.laser_sfx = laser_sfx
        self.laser_hit_sfx = laser_hit_sfx
        self.explosion_sfx = explosion_sfx
        self.idle_animation_frames = idle_animation_frames
        self.current_frame = 0
        self.animation_counter = 0

        # Attributes for glow effect
        self.glow_effect_duration = 200  # Duration in milliseconds
        self.glow_effect_end_time = 0
        self.original_images = {}

    def shoot(self):
        """Appends a new laser to the laser list if the player's cannon is not in cooldown."""

        # 0 = player is ready to fire
        if self.cooldown_counter == 0:
            laser_pos = Vector2((self.pos.x), (self.pos.y - self.offset["y"]))
            laser = Actor(
                laser_pos,
                self.laser_dmg,
                BASE_LASER_SPEED,
                self.laser_img,
                self.laser_mask,
                IMG_OFFSETS["blueLaser"],
            )
            self.lasers_fired.add(laser)
            self.laser_sfx.play()
            # Setting to 1 starts timer (see cooldown_cannon())
            self.cooldown_counter = 1

    def update_idle_animation(self):
        """Update the idle animation for the player (engine effects)."""

        if self.animation_counter % 5 == 0:  # Adjust this value to change the speed
            self.current_frame = (self.current_frame + 1) % len(
                self.idle_animation_frames
            )
            self.img = self.idle_animation_frames[self.current_frame]

        if pygame.time.get_ticks() < self.glow_effect_end_time:
            # Before glow application add img to orginal img list
            if not self.original_images.get(self.current_frame):
                self.original_images[self.current_frame] = self.img.copy()

            glow_color = pygame.Color("yellow")
            self.img.fill(glow_color, special_flags=pygame.BLEND_ADD)
        else:
            # Restore images to before glow effect
            for frame_idx, frame_img in self.original_images.items():
                self.idle_animation_frames[frame_idx] = frame_img
            self.original_images.clear()

        self.animation_counter += 1

    def resolve_hits(self, laser: Actor, objs: list) -> list:
        """Resolves player lasers in the game, a hit = -1 hp on target. If
        the objects hp is <= 0 then method calls kill() on the object."""

        objs_to_kill = []

        for obj in objs:
            if obj is not None and Actor.resolve_collision(laser, obj):
                obj.hp -= 1
                self.laser_hit_sfx.play()
                if obj.hp <= 0:
                    obj.kill()
                    self.explosion_sfx.play()
                    objs_to_kill.append(obj)
                self.lasers_fired.remove(laser)  # Stop drawing laser that hit

        return objs_to_kill

    def cooldown_cannon(self):
        """Needs to be called on every frame of the game, once the threshold is
        reached the player can fire again."""

        # If threshold met, then set counter to 0 (player can fire again)
        if self.cooldown_counter >= self.cooldown_threshold:
            self.cooldown_counter = 0
        # Else increase counter (gets closer to threshold)
        elif self.cooldown_counter > 0:
            self.cooldown_counter += 1

    def fire_missle(self, targets: list):
        """Fires a missile from the players ship if they have picked up a
        missile to use."""

        if self.missile_count > 0 and self.missile_cooldown_counter == 0:
            missile_pos = Vector2((self.pos.x), (self.pos.y - self.offset["y"]))
            lock = Missile.lock(self.pos, targets)
            missile = Missile(
                missile_pos,
                1,
                self.speed,
                self.missile_img,
                self.missile_mask,
                IMG_OFFSETS["blueMissile"],
                lock,
                90.0,
            )
            self.missile_sfx.play()
            self.missiles_fired.add(missile)
            self.missile_count -= 1
            self.missile_cooldown_counter = 1

    def resolve_missiles(self, missile: Actor, objs: list) -> list:
        """Iterates through all Actor objects in the passed list of objects to
        check if a fired missile has hit it. Returns a list of hit objects."""

        objs_to_kill = []

        for obj in objs:
            if obj is not None and Actor.resolve_collision(missile, obj):
                self.explosion_sfx.play()
                obj.hp -= 3
                if obj.hp <= 0:
                    obj.kill()
                    objs_to_kill.append(obj)
                self.missiles_fired.remove(missile)  # Stop drawing missile that hit

        return objs_to_kill

    def start_glow_effect(self):
        """Initiates a glow effect on the player."""

        self.glow_effect_end_time = pygame.time.get_ticks() + self.glow_effect_duration

    def cooldown_missiles(self):
        """Ticks the cooldown for player missiles, should be callsed for
        every iteration of the main game loop."""

        if self.missile_cooldown_counter >= self.missile_cooldown_threshold:
            self.missile_cooldown_counter = 0
        elif self.missile_cooldown_counter > 0:
            self.missile_cooldown_counter += 1
