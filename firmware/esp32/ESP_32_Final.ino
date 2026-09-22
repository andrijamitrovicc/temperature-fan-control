#define IR_SEND_PIN 4      // IR LED predajnik (GPIO4)

#include <Arduino.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <IRremote.hpp>

// =========================
// PINOVI
// =========================

#define ONE_WIRE_BUS 15    // DS18B20 data pin (GPIO15)
#define POT_PIN 34         // potenciometar (ADC1 GPIO34)

// =========================
// SENSOR SETUP
// =========================

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(115200);

  sensors.begin();
  IrSender.begin(IR_SEND_PIN);

  pinMode(POT_PIN, INPUT);

  Serial.println("ESP32 IR Predajnik startovan");
}

// =========================
// LOOP
// =========================

void loop() {

  sensors.requestTemperatures();
  float temp = sensors.getTempCByIndex(0);

  if (temp == DEVICE_DISCONNECTED_C) {
    Serial.println("DS18B20 error");
    delay(2000);
    return;
  }

  int pot = analogRead(POT_PIN);

  uint32_t prag = map(pot, 0, 4095, 15, 50);
  uint32_t tempInt = (uint32_t)(temp * 100);

  // MARKERI
  uint32_t rawTemp = 0x10000000 | tempInt;
  uint32_t rawPrag = 0x20000000 | prag;

  // SEND IR
  IrSender.sendNECRaw(rawTemp, 0);
  delay(100);

  IrSender.sendNECRaw(rawPrag, 0);

  // DEBUG
  Serial.print("Temp: ");
  Serial.print(temp);
  Serial.print(" | Prag: ");
  Serial.println(prag);

  delay(2000);
}

