from PIL import Image, ImageDraw
import hashlib

def generate_identicon(
    email: str,
    size: int = 420,
    grid_size: int = 5
) -> Image.Image:
    """
    Генерирует GitHub-подобный identicon на основе email с настраиваемым размером сетки.
    
    :param email: строка (обычно email), используется для хеширования
    :param size: итоговый размер изображения в пикселях (должен быть кратен grid_size)
    :param grid_size: количество ячеек по ширине и высоте (рекомендуется нечётное число, например 5, 7, 9)
    :return: объект PIL Image
    :raises ValueError: если size не делится на grid_size без остатка
    """
    if grid_size <= 0:
        raise ValueError("grid_size должен быть положительным целым числом.")
    if size % grid_size != 0:
        raise ValueError(f"Размер изображения (size={size}) должен быть кратен grid_size ({grid_size}).")

    cell_size = size // grid_size

    # Хешируем email
    hash_hex = hashlib.md5(email.strip().lower().encode()).hexdigest()

    # Цвет из первых 6 символов хеша
    color = (
        int(hash_hex[0:2], 16),
        int(hash_hex[2:4], 16),
        int(hash_hex[4:6], 16)
    )

    # Сколько бит нужно для заполнения левой половины (включая центральную колонку)?
    # Для нечётного grid_size: cols_to_fill = (grid_size // 2) + 1
    cols_to_fill = (grid_size // 2) + 1
    total_bits_needed = grid_size * cols_to_fill

    # Берём достаточно байтов из хеша (начиная с 6-го символа)
    # Каждый байт даёт 8 бит → нужно ceil(total_bits_needed / 8) байт
    bytes_needed = (total_bits_needed + 7) // 8
    max_available_bytes = (len(hash_hex) - 6) // 2  # оставшиеся байты после первых 3
    bytes_to_use = min(bytes_needed, max_available_bytes)

    pattern_bytes = [int(hash_hex[i:i+2], 16) for i in range(6, 6 + 2 * bytes_to_use)]

    # Создаём сетку
    grid = [[False] * grid_size for _ in range(grid_size)]
    bit_index = 0
    for row in range(grid_size):
        for col in range(cols_to_fill):
            if bit_index >= len(pattern_bytes) * 8:
                bit = False  # недостающие биты считаются нулевыми
            else:
                byte_idx = bit_index // 8
                bit_pos = 7 - (bit_index % 8)
                bit = (pattern_bytes[byte_idx] >> bit_pos) & 1
            grid[row][col] = bool(bit)
            # Зеркалируем относительно центра
            mirrored_col = grid_size - 1 - col
            grid[row][mirrored_col] = bool(bit)
            bit_index += 1

    # Создаём изображение
    img = Image.new("RGB", (size, size), (240, 240, 240))  # фон как у GitHub
    draw = ImageDraw.Draw(img)

    for row in range(grid_size):
        for col in range(grid_size):
            if grid[row][col]:
                x0 = col * cell_size
                y0 = row * cell_size
                x1 = x0 + cell_size
                y1 = y0 + cell_size
                draw.rectangle([x0, y0, x1, y1], fill=color)

    return img



# Примеры использования
if __name__ == "__main__":
    # Большой и детальный: 9×9, 450px
    avatar4 = generate_identicon(str(uuid4())*3, size=400, grid_size=20)
    avatar4.save("identicon_45x45.png")





# def color(sadness, joy, anger, fear):
#     """
#     Возвращает смешанный RGB-цвет на основе интенсивности эмоций.
#     Параметры: значения от 0.0 до 1.0 (рекомендуется), но допустимы любые неотрицательные числа.
#     Возвращает: кортеж (R, G, B) в диапазоне [0, 255]
#     """
#     # Базовые цвета для эмоций (RGB)
#     EMOTIONS = {
#         'sadness': (0, 0, 255),    # Темно-синий
#         'joy':     (255, 255, 0),  # Ярко-жёлтый
#         'anger':   (255, 0, 0),    # Красный
#         'fear':    (128, 0, 128)   # Фиолетовый (как в исходном коде)
#     }
    
#     # Приводим значения к неотрицательным числам
#     weights = [
#         max(0, float(sadness)),
#         max(0, float(joy)),
#         max(0, float(anger)),
#         max(0, float(fear))
#     ]
    
#     total = sum(weights)
#     if total <= 1e-9:  # Защита от деления на ноль
#         return (0, 0, 0)  # Нейтральный чёрный
    
#     # Взвешенное смешение каналов
#     r = g = b = 0.0
#     for w, (cr, cg, cb) in zip(weights, EMOTIONS.values()):
#         r += w * cr
#         g += w * cg
#         b += w * cb
    
#     r /= total
#     g /= total
#     b /= total
    
#     # Нормализация в диапазон [0, 255] и преобразование в int
#     return (
#         int(round(max(0, min(255, r)))),
#         int(round(max(0, min(255, g)))),
#         int(round(max(0, min(255, b))))
#     )


# # Пример использования
# if __name__ == "__main__":
#     result = color(sadness=0.3, joy=0, anger=1, fear=0.5)
#     print(f"Результат смешения: {result}")
#     print(f"RGB: rgb{result}")
    
#     # Дополнительные примеры для наглядности
#     print("\nПримеры:")
#     print(f"Только радость: {color(0, 1, 0, 0)} → rgb{color(0,1,0,0)}")
#     print(f"Гнев + Страх:   {color(0, 0, 0.7, 0.3)} → rgb{color(0,0,0.7,0.3)}")
#     print(f"Грусть (макс):  {color(1, 0, 0, 0)} → rgb{color(1,0,0,0)}")