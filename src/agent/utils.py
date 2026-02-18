from PIL import Image, ImageDraw
import hashlib

from src.agent.interfaces import ImageGeneratorPort


class ImageGenerator(ImageGeneratorPort):
    def __init__(self, size: int = 300, grid_size: int = 6):
        self.size = size
        self.grid_size = grid_size
    
    def generate(self, text: str) -> Image.Image:
        """
        Генерирует GitHub-подобный identicon на основе text с настраиваемым размером сетки.
        
        :param text: строка (обычно text), используется для хеширования
        :param size: итоговый размер изображения в пикселях (должен быть кратен grid_size)
        :param grid_size: количество ячеек по ширине и высоте (рекомендуется нечётное число, например 5, 7, 9)
        :return: объект PIL Image
        :raises ValueError: если size не делится на grid_size без остатка
        """
        if self.grid_size <= 0:
            raise ValueError("grid_size должен быть положительным целым числом.")
        if self.size % self.grid_size != 0:
            raise ValueError(f"Размер изображения (size={self.size}) должен быть кратен grid_size ({self.grid_size}).")

        cell_size = self.size // self.grid_size

        hash_hex = hashlib.md5(text.strip().lower().encode()).hexdigest()

        color = (
            int(hash_hex[0:2], 16),
            int(hash_hex[2:4], 16),
            int(hash_hex[4:6], 16)
        )

        cols_to_fill = (self.grid_size // 2) + 1
        total_bits_needed = self.grid_size * cols_to_fill

        bytes_needed = (total_bits_needed + 7) // 8
        max_available_bytes = (len(hash_hex) - 6) // 2
        bytes_to_use = min(bytes_needed, max_available_bytes)

        pattern_bytes = [int(hash_hex[i:i+2], 16) for i in range(6, 6 + 2 * bytes_to_use)]

        grid = [[False] * self.grid_size for _ in range(self.grid_size)]
        bit_index = 0
        for row in range(self.grid_size):
            for col in range(cols_to_fill):
                if bit_index >= len(pattern_bytes) * 8:
                    bit = False
                else:
                    byte_idx = bit_index // 8
                    bit_pos = 7 - (bit_index % 8)
                    bit = (pattern_bytes[byte_idx] >> bit_pos) & 1
                grid[row][col] = bool(bit)
                
                mirrored_col = self.grid_size - 1 - col
                grid[row][mirrored_col] = bool(bit)
                bit_index += 1

        img = Image.new("RGB", (self.size, self.size), (240, 240, 240))
        draw = ImageDraw.Draw(img)

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                if grid[row][col]:
                    x0 = col * cell_size
                    y0 = row * cell_size
                    x1 = x0 + cell_size
                    y1 = y0 + cell_size
                    draw.rectangle([x0, y0, x1, y1], fill=color)

        return img


def generate_color(sadness, joy, anger, fear) -> str:
    """
    Возвращает смешанный RGB-цвет на основе интенсивности эмоций.
    Параметры: значения от 0.0 до 1.0 (рекомендуется), но допустимы любые неотрицательные числа.
    Возвращает: кортеж (R, G, B) в диапазоне [0, 255]
    """
    # Базовые цвета для эмоций (RGB)
    EMOTIONS = {
        'sadness': (0, 0, 255),    # Темно-синий
        'joy':     (255, 255, 0),  # Ярко-жёлтый
        'anger':   (255, 0, 0),    # Красный
        'fear':    (128, 0, 128)   # Фиолетовый (как в исходном коде)
    }
    
    # Приводим значения к неотрицательным числам
    weights = [
        max(0, float(sadness)),
        max(0, float(joy)),
        max(0, float(anger)),
        max(0, float(fear))
    ]
    
    total = sum(weights)
    if total <= 1e-9:  # Защита от деления на ноль
        return "#ffffff"  # Нейтральный чёрный
    
    # Взвешенное смешение каналов
    r = g = b = 0.0
    for w, (cr, cg, cb) in zip(weights, EMOTIONS.values()):
        r += w * cr
        g += w * cg
        b += w * cb
    
    r /= total
    g /= total
    b /= total
    import random
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    # Нормализация и конвертация в int
    r_int = int(round(max(0, min(255, r))))
    g_int = int(round(max(0, min(255, g))))
    b_int = int(round(max(0, min(255, b))))
    
    # Преобразование в hex с zero-padding (2 символа на канал)
    return f"#{r_int:02X}{g_int:02X}{b_int:02X}"
