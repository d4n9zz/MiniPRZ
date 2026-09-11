import pygame

# Класс для плавного появления элементов интерфейса
class UIAnimation:
    __slots__ = ['start_time', 'duration', 'active']

    def __init__(self, duration=250):
        # Время старта анимации и её длина в миллисекундах
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.active = True

    def restart(self):
        # Запускает анимацию заново с текущего момента
        self.start_time = pygame.time.get_ticks()
        self.active = True

    def get_progress(self):
        # Возвращает прогресс от 0.0 до 1.0 с плавным замедлением в конце
        if not self.active:
            return 1.0
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = min(1.0, elapsed / self.duration) if self.duration > 0 else 1.0
        return 1 - (1 - progress) ** 3

    def is_finished(self):
        # Анимация завершена, когда прошло нужное время
        elapsed = pygame.time.get_ticks() - self.start_time
        return elapsed >= self.duration


# Возвращает прогресс для элемента с задержкой по очереди
# Это позволяет кнопкам появляться одну за другой, а не все сразу
def staggered_progress(animation, index, total, stagger_delay=40, duration=None):
    if animation is None or not animation.active:
        return 1.0
    dur = duration if duration is not None else animation.duration
    elapsed = pygame.time.get_ticks() - animation.start_time
    button_delay = index * stagger_delay
    button_elapsed = max(0, elapsed - button_delay)
    progress = min(1.0, button_elapsed / dur) if dur > 0 else 1.0
    return 1 - (1 - progress) ** 3