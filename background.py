import pygame
import os


def _find_image_file(base_path):
    if base_path is None:
        return None
    extensions = ['.png', '.jpg', '.jpeg', '.bmp']
    for ext in extensions:
        full_path = base_path + ext
        if os.path.exists(full_path):
            return full_path
    if os.path.exists(base_path):
        return base_path
    return None


class BackgroundManager:
    __slots__ = ['current_bg', 'bg_type']

    def __init__(self):
        self.current_bg = None
        self.bg_type = None

    def load_background(self, bg_key, backgrounds_dict):
        base_path = backgrounds_dict.get(bg_key)
        if base_path is None or base_path == '':
            self.bg_type = 'gradient'
            self.current_bg = None
            return True
        path = _find_image_file(base_path)
        if path is None:
            self.bg_type = 'gradient'
            return False
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                self.current_bg = pygame.image.load(path).convert()
                self.bg_type = 'image'
                return True
            else:
                self.bg_type = 'gradient'
                return False
        except Exception:
            self.bg_type = 'gradient'
            return False

    def draw(self, screen, width, height):
        if self.bg_type == 'gradient':
            return False
        elif self.bg_type == 'image':
            if self.current_bg:
                bg_scaled = pygame.transform.scale(self.current_bg, (width, height))
                screen.blit(bg_scaled, (0, 0))
                return True
        return False

    def cleanup(self):
        self.current_bg = None