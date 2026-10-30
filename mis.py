import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import sounddevice as sd

# Параметры ADSR (в секундах)
ADSR_ATTACK = 0.01      # x мс — старт
ADSR_DECAY = 0.05        # x мс — падение до уровня сустейна
ADSR_SUSTAIN = 0.85      # Уровень громкости во время удержания ноты (0.0–1.0)
ADSR_RELEASE = 0.01      # x мс — затухание после отпускания ноты


# --- 0. Настройка параметров + чтение файла ---

SAMPLE_RATE = 44100  # Частота дискретизации (Гц)
TEMPO = 120  # Темп (ударов в минуту)
BEAT_DURATION = 60 / TEMPO  # Длительность одной четвертной ноты


# Словарь для расшифровки фпйла
tabl = {
    'A': 9, 'A#': 10, 'B': 11,
    'C': 0, 'C#': 1, 'D': 2,
    'D#': 3, 'E': 4, 'F': 5,
    'F#': 6, 'G': 7, 'G#': 8,
    'РЎ': 0
}

# ------------------------------------------------------
def durat (razmernoti, bpm, delitel):
    dln=(((60*delitel)/bpm)/razmernoti)*1000
    return dln
# ------------------------------------------------------
def hz (vnutri, snaruzi):
    i= snaruzi*12 + tabl[vnutri]
    gerz=440*(2**((i-57)/12))
    return gerz
# ------------------------------------------------------

def high_pass_filter(x, cutoff_hz, sample_rate):
    """Простой High-Pass фильтр (срезает низкие частоты)"""
    # Коэффициент зависит от частоты среза
    alpha = np.exp(-2 * np.pi * cutoff_hz / sample_rate)
    y = np.zeros_like(x)
    if len(x) > 0:
        y[0] = x[0]
        for i in range(1, len(x)):
            y[i] = alpha * y[i-1] + alpha * (x[i] - x[i-1])
    return y

def low_pass_filter(x, cutoff_hz, sample_rate):
    """Простой Low-Pass фильтр (срезает высокие частоты)"""
    alpha = 1 / (1 + 2 * np.pi * cutoff_hz * (1/sample_rate))
    y = np.zeros_like(x)
    if len(x) > 0:
        y[0] = x[0]
        for i in range(1, len(x)):
            y[i] = alpha * x[i] + (1 - alpha) * y[i-1]
    return y
# --- 1. Выбор режима ---
mode_0 = 1
if mode_0 == 1:
    file = open(str(input('file\'s name, pls\n--->')))
    temp, raz = map(int, file.readline().rstrip('\n')[:-2].split())
    sound_smth = []
    for line in file:
        stroka = line.rstrip('\n')
        nota, octava, dlit = stroka.split()
        octava = int(octava)
        dlit = float(dlit)
        a = hz(nota, octava)
        b = round(durat(dlit,temp,raz))
        sound_smth.append((a,b/1000))
mode  = int(input('wave\'s modes:\nsin = 1\ncos = 2\nsaw = 3\nsquare = 4\ntriangle = 5\n--->'))
gain = int(input(f'gain--->'))

def saw(array):
    new_array = []
    for element in array:
        new_array.append(2 * (element - np.floor(element + 0.5)))
    return new_array
#wave = 2 * (t * frequency - np.floor(t * frequency + 0.5))

# --- 2. Функция генерации звука одной ноты ---
def generate_note(frequency, duration, sample_rate=SAMPLE_RATE):
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    if frequency == 0:
        return np.zeros(num_samples)

    # -----------------------------------------------------------------------------------------------
    x = 2 * np.pi * frequency * t
    if mode == 1:
        wave = np.sin(x)
    elif mode == 2:
        wave = np.cos(x)
    elif mode == 3:
        wave = saw(x/8)
    elif mode == 4:
        wave = np.sign(np.sin(x))
    elif mode == 5:
        wave = (2 / math.pi) * np.arcsin(np.sin(x))
    else:
        print('Нука перевведи циферку нормально')

    if gain != 1:
        wave = np.tanh(gain*wave) # Делаем джджджжжжжжжжжж через гиперболический тангенс

        max_val = np.max(np.abs(wave)) # Ограничиваем, чтобы не клиппировало
        if max_val > 0:
            wave = wave / max_val


    # А. Срезаем низ (High Pass ~100Hz) - убирает гул
    wave = high_pass_filter(wave, 100, sample_rate)

    # Б. Поднимаем середину (Mid Boost) 
    window_size = int(sample_rate / 1000) * 5  # Окно около 5-10 мс для сглаживания
    if window_size % 2 == 0: window_size += 1

    smoothed = np.convolve(wave, np.ones(window_size) / window_size, mode='same')
    mid_boost_factor = 1.4  # Насколько сильно поднимаем середину (1.0 = нет эффекта)
    wave = wave + mid_boost_factor * (wave - smoothed)

    # В. Срезаем верх (Low Pass ~6000Hz) - убирает цифровое шипение
    wave = low_pass_filter(wave, 6000, sample_rate)

    # Нормализуем после всех обработок, чтобы не было клиппинга
    max_val = np.max(np.abs(wave))
    if max_val > 0.1:  # Защита от деления на ноль или слишком тихий звук
        wave = wave / max_val

    attack_samples = int(ADSR_ATTACK * sample_rate)
    decay_samples = int(ADSR_DECAY * sample_rate)
    release_samples = int(ADSR_RELEASE * sample_rate)

    envelope = np.ones(num_samples)

    # Stage 1: Attack (0 -> max)
    if attack_samples > 0:
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)

    # Stage 2: Decay (max -> sustain)
    if decay_samples > 0:
        start_idx = attack_samples
        end_idx = start_idx + decay_samples
        if end_idx <= num_samples:
            envelope[start_idx:end_idx] = np.linspace(1, ADSR_SUSTAIN, decay_samples)
        else:
            # Если нота слишком короткая, плавно идём от 1 до sustain до конца
            envelope[start_idx:] = np.linspace(1, ADSR_SUSTAIN, num_samples - start_idx)

    # Stage 3: Sustain (держим sustain до начала Release)
    sustain_start = attack_samples + decay_samples
    if sustain_start < num_samples:
        envelope[sustain_start:] = ADSR_SUSTAIN

    # Stage 4: Release (sustain -> 0)
    # Release начинается в конце ноты и должен уйти в ноль.
    # Но у нас нота уже имеет фиксированную длительность, поэтому Release делаем внутри неё.
    # Если нота короче, чем Attack+Decay+Release, делаем упрощённо.
    release_start = max(0, num_samples - release_samples)
    if release_start < num_samples:
        release_len = num_samples - release_start
        envelope[release_start:] = np.linspace(envelope[release_start - 1] if release_start > 0 else ADSR_SUSTAIN, 0.0,
                                               release_len)

    return wave * envelope

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
        if mode_0 == 1:
            duration = beats
            freq = note_name
        else:
            duration = beats * BEAT_DURATION
            freq = NOTES.get(note_name, 0)

        note_wave = generate_note(freq, duration, sample_rate)
        full_track = np.concatenate((full_track, note_wave))

    return full_track


# --- 4. Основной блок выполнения ---
if __name__ == "__main__":

    my_song = sound_smth

    print("Генерируем мелодию...")
    audio_data = create_melody(my_song)

    # Нормализация громкости
    audio_data = audio_data / np.max(np.abs(audio_data))

    # Воспроизведение звука динамиков через Python
    print("Воспроизводим мелодию...")
    sd.play(audio_data, SAMPLE_RATE)
    sd.wait()  # Ожидаем окончания проигрывания
    print("Воспроизведение завершено!")

    # Сохранение в WAV-файл (формат 16-бит PCM)
    audio_int16 = (audio_data * 32767).astype(np.int16)
    output_filename = "melody.wav"
    wavfile.write(output_filename, SAMPLE_RATE, audio_int16)
    print(f"Мелодия сохранена в файл: {output_filename}")
    print("Строим график осциллограммы...")

    plt.figure(figsize=(12, 6))
    zoom_samples = int(SAMPLE_RATE * 0.5)
    plt.subplot(2, 1, 1)
    plt.plot(np.linspace(0, 0.5, zoom_samples), audio_data[:zoom_samples], color="b")
    plt.xlabel("Время (с)")
    plt.ylabel("Амплитуда")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.title("Осциллограмма сгенерированной мелодии (фрагмент)")

    plt.subplot(2, 1, 2)
    samples_to_show = min(len(audio_data), int(SAMPLE_RATE * 0.05))
    time_axis = (np.arange(samples_to_show) / SAMPLE_RATE * 1000)
    plt.plot(time_axis, audio_data[:samples_to_show], color="navy")
    plt.xlabel("Время (мс)")
    plt.ylabel("Амплитуда")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.title("Фрагмент волны")

    plt.tight_layout()
    plt.savefig("waveform.png", dpi=300)
    plt.show()
    print("График сохранен в файл: waveform.png")
    
