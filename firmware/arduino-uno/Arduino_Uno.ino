#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#define IR_RECEIVE_PIN 11
#include <IRremote.hpp>

#define RELEJ_PIN 7
#define BUZER_PIN 3

LiquidCrystal_I2C lcd(0x27, 16, 2);

// -------------------------------
// PODACI
// -------------------------------

float trenutnaTemperatura = 0.0;
int podeseniPrag = 50;

int prethodnoStanjeReleja = LOW;
int pythonVentilator = LOW;

// 0 = AUTO_ARDUINO
// 1 = OVERRIDE_ON
// 2 = OVERRIDE_OFF
// 3 = AUTO_PYTHON

int rezimRada = 0;

unsigned long zadnjeSlanje = 0;

// -------------------------------
// BUZZER FUNKCIJE
// -------------------------------

void beepON()
{
    digitalWrite(BUZER_PIN, HIGH);
    delay(500);
    digitalWrite(BUZER_PIN, LOW);
}

void beepOFF()
{
    digitalWrite(BUZER_PIN, HIGH);
    delay(150);
    digitalWrite(BUZER_PIN, LOW);

    delay(100);

    digitalWrite(BUZER_PIN, HIGH);
    delay(150);
    digitalWrite(BUZER_PIN, LOW);
}

// -------------------------------
// SETUP
// -------------------------------

void setup()
{
    Serial.begin(115200);

    IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);

    lcd.init();
    lcd.backlight();

    pinMode(RELEJ_PIN, OUTPUT);
    pinMode(BUZER_PIN, OUTPUT);

    digitalWrite(RELEJ_PIN, LOW);
    digitalWrite(BUZER_PIN, LOW);

    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("IR Receiver");
    lcd.setCursor(0, 1);
    lcd.print("Starting...");
}

// -------------------------------
// LOOP
// -------------------------------

void loop()
{
    // =====================================
    // 1. KOMANDE IZ PYTHONA
    // =====================================

    if (Serial.available())
    {
        String komanda = Serial.readStringUntil('\n');
        komanda.trim();

        if (komanda == "A")
        {
            rezimRada = 0;
        }

        else if (komanda == "ON")
        {
            rezimRada = 1;
        }

        else if (komanda == "OFF")
        {
            rezimRada = 2;
        }

        else if (komanda == "P")
        {
            rezimRada = 3;
        }

        else if (komanda == "FAN_ON")
        {
            pythonVentilator = HIGH;
        }

        else if (komanda == "FAN_OFF")
        {
            pythonVentilator = LOW;
        }
    }

    // =====================================
    // 2. IR PRIJEM
    // =====================================

    if (IrReceiver.decode())
    {
        uint32_t rawPodatak =
            IrReceiver.decodedIRData.decodedRawData;

        uint32_t marker =
            rawPodatak & 0xF0000000;

        uint32_t vrijednost =
            rawPodatak & 0x0FFFFFFF;

        if (marker == 0x10000000)
        {
            trenutnaTemperatura =
                vrijednost / 100.0;
        }

        else if (marker == 0x20000000)
        {
            podeseniPrag =
                vrijednost;
        }

        IrReceiver.resume();
    }

    // =====================================
    // 3. ODREĐIVANJE STANJA FAN-a
    // =====================================

    int zeljenoStanjeReleja = LOW;

    if (rezimRada == 0)
    {
        // AUTO ARDUINO

        if (trenutnaTemperatura >= podeseniPrag)
        {
            zeljenoStanjeReleja = HIGH;
        }
        else
        {
            zeljenoStanjeReleja = LOW;
        }
    }

    else if (rezimRada == 1)
    {
        // OVERRIDE ON

        zeljenoStanjeReleja = HIGH;
    }

    else if (rezimRada == 2)
    {
        // OVERRIDE OFF

        zeljenoStanjeReleja = LOW;
    }

    else if (rezimRada == 3)
    {
        // AUTO PYTHON

        zeljenoStanjeReleja =
            pythonVentilator;
    }

    // =====================================
    // 4. RELEJ
    // =====================================

    digitalWrite(
        RELEJ_PIN,
        zeljenoStanjeReleja
    );

    // =====================================
    // 5. BUZZER
    // =====================================

    if (zeljenoStanjeReleja != prethodnoStanjeReleja)
    {
        if (zeljenoStanjeReleja == HIGH)
        {
            beepON();
        }
        else
        {
            beepOFF();
        }

        prethodnoStanjeReleja =
            zeljenoStanjeReleja;
    }

    // =====================================
    // 6. LCD
    // =====================================

    lcd.setCursor(0, 0);
    lcd.print("T:");
    lcd.print(trenutnaTemperatura, 1);
    lcd.print((char)223);
    lcd.print("C ");

    lcd.print("P:");
    lcd.print(podeseniPrag);
    lcd.print("  ");

    lcd.setCursor(0, 1);

    if (rezimRada == 0)
    {
        lcd.print("AUTO ARD ");
    }
    else if (rezimRada == 1)
    {
        lcd.print("OVR ON   ");
    }
    else if (rezimRada == 2)
    {
        lcd.print("OVR OFF  ");
    }
    else if (rezimRada == 3)
    {
        lcd.print("AUTO PY  ");
    }

    if (zeljenoStanjeReleja == HIGH)
    {
        lcd.print("ON ");
    }
    else
    {
        lcd.print("OFF");
    }

    // =====================================
    // 7. SERIAL ZA PYTHON
    // =====================================

    if (millis() - zadnjeSlanje > 500)
    {
        Serial.print(trenutnaTemperatura);
        Serial.print(",");

        Serial.print(podeseniPrag);
        Serial.print(",");

        Serial.print(zeljenoStanjeReleja);
        Serial.print(",");

        Serial.println(rezimRada);

        zadnjeSlanje = millis();
    }
}

