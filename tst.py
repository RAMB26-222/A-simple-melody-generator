import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import sounddevice as sd


# --- 0. Выбор режима ---
mode  = int(input('modes:\nsin = 1\ncos = 2\nsaw = 3\nsquare = 4\ntriangle = 5'))
def square(array):
    new_array = []
    for element in array:
        new_array.append(2*(element-np.floor(element + 0.5)))
    return new_array

# --- 1. Настройка параметров ---
SAMPLE_RATE = 44100  # Частота дискретизации (Гц)
TEMPO = 120  # Темп (ударов в минуту)
BEAT_DURATION = 60 / TEMPO  # Длительность одной четвертной ноты

# Словарь частот нот первой и второй октавы (в Герцах)
NOTES = {
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'REST': 0
}


# --- 2. Функция генерации звука одной ноты ---
def generate_note(frequency, duration, sample_rate=SAMPLE_RATE):
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    if frequency == 0:
        return np.zeros(num_samples)

    # -----------------------------------------------------------------------------------------------
    x = 2 * np.pi * frequency * t
    if mode == 1: wave = np.sin(x)
    elif mode == 2: wave = np.cos(x)
    elif mode == 3: wave = square(x/8)
    elif mode == 4: wave = np.sign(np.sin(x))
    elif mode == 5: wave = (2/(math.pi))*np.arcsin(np.sin(x))


    # Плавное нарастание и затухание (ADSR-огибающая)
    attack_samples = int(sample_rate * 0.05)
    release_samples = int(sample_rate * 0.05)

    envelope = np.ones(num_samples)
    if num_samples > (attack_samples + release_samples):
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[-release_samples:] = np.linspace(1, 0, release_samples)
    else:
        envelope = np.linspace(1, 0, num_samples)

    return wave * envelope


# --- 3. Функция сборки мелодии ---
def create_melody(melody_score, sample_rate=SAMPLE_RATE):
    full_track = np.array([], dtype=np.float32)

    for note_name, beats in melody_score:
        duration = beats * BEAT_DURATION
        freq = NOTES.get(note_name, 0)

        note_wave = generate_note(freq, duration, sample_rate)
        full_track = np.concatenate((full_track, note_wave))

    return full_track


# --- 4. Основной блок выполнения ---
if __name__ == "__main__":
    my_song = [
        ('C4', 1.0), ('G4', 1.0), ('G4', 1.0), ('A4', 1.0), ('G4', 2.0),
        ('REST', 0.5),
        ('B4', 1.0), ('C5', 1.0)
    ]

    print("Генерируем мелодию...")
    audio_data = create_melody(my_song)

    # Нормализация громкости
    audio_data = audio_data / np.max(np.abs(audio_data))

    # -------------------------------------------------------------
    # --- НОВЫЙ БЛОК: Воспроизведение звука динамиков через Python ---
    # -------------------------------------------------------------
    print("Воспроизводим мелодию...")
    sd.play(audio_data, SAMPLE_RATE)
    sd.wait()  # Ожидаем окончания проигрывания перед выполнением следующего кода
    print("Воспроизведение завершено!")
    # -------------------------------------------------------------

    # Сохранение в WAV-файл (формат 16-бит PCM)
    audio_int16 = (audio_data * 32767).astype(np.int16)
    output_filename = "melody.wav"
    wavfile.write(output_filename, SAMPLE_RATE, audio_int16)
    print(f"Мелодия сохранена в файл: {output_filename}")

    # Визуализация осциллограммы
    print("Строим график осциллограммы...")
    plt.figure(figsize=(10, 4))
    zoom_samples = int(SAMPLE_RATE * 0.5)
    plt.plot(np.linspace(0, 0.5, zoom_samples), audio_data[:zoom_samples], color='b')
    plt.title("Осциллограмма сгенерированной мелодии (фрагмент)")
    plt.xlabel("Время (сек)")
    plt.ylabel("Амплитуда")
    plt.grid(True)

    plt.savefig("waveform.png", dpi=300)
    plt.show()
    print("График сохранен в файл: waveform.png")