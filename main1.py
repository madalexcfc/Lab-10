import os
import requests
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer
import json

engine = pyttsx3.init()
engine.setProperty('rate', 150)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

if not os.path.exists("vosk-model-small-ru-0.22"):
    print("Пожалуйста, скачайте модель распознавания речи с https://alphacephei.com/vosk/models")
    exit(1)

model = Model("vosk-model-small-ru-0.22")
recognizer = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()

FACTS_FILE = "math_facts.txt"

current_fact = ""

def speak(text):
    print(text)
    engine.say(text)
    engine.runAndWait()

def get_math_fact():
    global current_fact
    try:
        response = requests.get("http://numbersapi.com/random/math?json")
        data = response.json()
        current_fact = data["text"]
        return current_fact
    except Exception as e:
        speak("Произошла ошибка при получении факта")
        print(f"Ошибка: {e}")
        return None

def save_fact_to_file():
    if not current_fact:
        speak("Сначала получите факт командой 'факт'")
        return
    
    try:
        with open(FACTS_FILE, "a", encoding="utf-8") as f:
            f.write(current_fact + "\n")
        speak("Факт успешно записан в файл")
    except Exception as e:
        speak("Произошла ошибка при записи в файл")
        print(f"Ошибка: {e}")

def delete_last_fact():
    try:
        with open(FACTS_FILE, "r+", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                speak("Файл с фактами пуст")
                return
            
            f.seek(0)
            f.truncate()
            f.writelines(lines[:-1])
        
        speak("Последний факт удалён из файла")
    except FileNotFoundError:
        speak("Файл с фактами не найден")
    except Exception as e:
        speak("Произошла ошибка при удалении факта")
        print(f"Ошибка: {e}")

def listen_command():
    print("Слушаю команду...")
    
    while True:
        data = stream.read(4000, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            command = result.get("text", "").lower()
            print(f"Распознано: {command}")
            return command

def main():
    speak("Голосовой ассистент для математических фактов запущен. Ожидаю команду.")
    
    while True:
        command = listen_command()
        
        if "факт" in command:
            fact = get_math_fact()
            if fact:
                speak(fact)
        
        elif "следующий" in command:
            fact = get_math_fact()
            if fact:
                speak("Вот новый факт")
                speak(fact)
        
        elif "прочитать" in command:
            if current_fact:
                speak(current_fact)
            else:
                speak("Сначала получите факт командой 'факт'")
        
        elif "записать" in command:
            save_fact_to_file()
        
        elif "удалить" in command:
            delete_last_fact()
        
        elif "выход" in command or "стоп" in command:
            speak("Завершаю работу")
            break
        
        else:
            speak("Команда не распознана. Попробуйте ещё раз")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nЗавершение работы...")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
