/*
  Первый тест мотора RS2205 + Bidirectional ESC 30A через ESP32

  Управление через Serial Monitor (115200 бод):
    - ввести число от 1000 до 2000 — выставить газ (мкс)
    - ввести "0" — мгновенный стоп (нейтраль 1500)
    - 1500 = нейтраль/стоп
    - 1000 = полный реверс
    - 2000 = полный вперёд
*/

#include <ESP32Servo.h>

Servo esc;

const int ESC_PIN = 22;      // сигнальный провод (оранжевый) сюда
const int NEUTRAL = 1500;    // нейтраль
const int MIN_US  = 1000;
const int MAX_US  = 2000;

void setup() {
  Serial.begin(115200);
  delay(500);

  esc.attach(ESC_PIN, MIN_US, MAX_US);
  esc.writeMicroseconds(NEUTRAL);

  Serial.println("Держим нейтраль. Можно подключать батарею к ESC.");
  Serial.println("Ждите характерных бипов ESC (готовность)...");
  delay(3000); // время на инициализацию ESC после подачи питания

  Serial.println("Готово. Введите значение 1000-2000 (1500 = стоп):");
}

void loop() {
  if (Serial.available() > 0) {
    int value = Serial.parseInt();

    if (value == 0) {
      esc.writeMicroseconds(NEUTRAL);
      Serial.println("СТОП (нейтраль)");
    }
    else if (value >= MIN_US && value <= MAX_US) {
      esc.writeMicroseconds(value);
      Serial.print("Газ установлен: ");
      Serial.println(value);
    }
    else {
      Serial.println("Вне диапазона. Введите число 1000-2000 (0 = стоп).");
    }

    // очистить остаток буфера (символ новой строки и т.п.)
    while (Serial.available() > 0) Serial.read();
  }
}
