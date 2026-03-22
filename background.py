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
            print(f"⚠️ Фон не найден: {base_path} (.png/.jpg)")
            self.bg_type = 'gradient'
            return False
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.png', '.jpg', '.jpeg', '.bmp']:
                self.current_bg = pygame.image.load(path).convert()
                self.bg_type = 'image'
                print(f"✓ Загружен фон: {path}")
                return True
            else:
                print(f"⚠️ Не поддерживаемый формат: {ext}")
                self.bg_type = 'gradient'
                return False
        except Exception as e:
            print(f"⚠️ Ошибка загрузки фона: {e}")
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