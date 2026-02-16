from PIL import Image, ImageDraw
import hashlib

def generate_identicon(email: str, size: int = 420, cell_size: int = 84) -> Image.Image:
    """
    Генерирует GitHub-подобный identicon на основе email.
    
    :param email: строка (обычно email), используется для хеширования
    :param size: итоговый размер изображения (по умолчанию 420x420)
    :param cell_size: размер одной ячейки (по умолчанию 84 → 5×84 = 420)
    :return: объект PIL Image
    """
    # Приведение к нижнему регистру и хеширование MD5
    hash_hex = hashlib.md5(email.strip().lower().encode()).hexdigest()
    
    # Первые 6 символов — цвет фона (не используется в GitHub, но можно добавить)
    # GitHub использует фиксированный фон (#f0f0f0), но мы возьмём цвет из хеша
    color = (
        int(hash_hex[0:2], 16),
        int(hash_hex[2:4], 16),
        int(hash_hex[4:6], 16)
    )
    
    # Остальные байты определяют паттерн (берём 15 бит: 3 байта → 24 бита, но достаточно 15)
    pattern_bytes = [int(hash_hex[i:i+2], 16) for i in range(6, 12)]
    
    # Создаём 5x5 сетку; используем только первые 3 столбца, остальные зеркальны
    grid = [[False for _ in range(5)] for _ in range(5)]
    bit_index = 0
    for row in range(5):
        for col in range(3):  # только левая половина + центр
            if bit_index < len(pattern_bytes) * 8:
                byte_index = bit_index // 8
                bit_in_byte = 7 - (bit_index % 8)
                bit = (pattern_bytes[byte_index] >> bit_in_byte) & 1
                grid[row][col] = bool(bit)
                grid[row][4 - col] = bool(bit)  # зеркальное отражение
                bit_index += 1

    # Создаём изображение
    img = Image.new("RGB", (size, size), (240, 240, 240))  # фон как у GitHub
    draw = ImageDraw.Draw(img)

    for row in range(5):
        for col in range(5):
            if grid[row][col]:
                x0 = col * cell_size
                y0 = row * cell_size
                x1 = x0 + cell_size
                y1 = y0 + cell_size
                draw.rectangle([x0, y0, x1, y1], fill=color)

    return img

# Пример использования
if __name__ == "__main__":
    avatar = generate_identicon("61f0c404-5cb3-11e7-907b-a6006ad3dba1")
    avatar.save("identicon.png")
    avatar.show()