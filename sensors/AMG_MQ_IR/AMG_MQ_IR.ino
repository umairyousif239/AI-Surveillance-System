#include <Wire.h>
#include <Adafruit_AMG88xx.h>

/* -------- Pin Definitions -------- */
#define SDA_PIN     27
#define SCL_PIN     26
#define FLAME_PIN   25
#define MQ135_PIN   34   // ADC-only pin

/* -------- Globals -------- */
Adafruit_AMG88xx amg;
float pixels[64];
uint32_t frame_id = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  /* Initialize I2C for AMG8833 */
  Wire.begin(SDA_PIN, SCL_PIN);

  /* Initialize sensors */
  pinMode(FLAME_PIN, INPUT);
  analogReadResolution(12); // 0–4095 ADC

  if (!amg.begin()) {
    Serial.println("ERR: AMG8833 not found!");
    while (1);
  }

  /* Optional header */
  Serial.println("F,frame_id,timestamp_ms,flame,mq135_raw,t0,t1,t2,t3,t4,t5,t6,t7,"
                 "t8,t9,t10,t11,t12,t13,t14,t15,t16,t17,t18,t19,t20,t21,t22,t23,"
                 "t24,t25,t26,t27,t28,t29,t30,t31,t32,t33,t34,t35,t36,t37,t38,t39,"
                 "t40,t41,t42,t43,t44,t45,t46,t47,t48,t49,t50,t51,t52,t53,t54,t55,"
                 "t56,t57,t58,t59,t60,t61,t62,t63");
}

void loop() {
  /* -------- Read Sensors -------- */
  amg.readPixels(pixels);

  int flame = (digitalRead(FLAME_PIN) == LOW) ? 1 : 0; // active LOW
  int mq135_raw = analogRead(MQ135_PIN);               // raw ADC 0–4095

  /* -------- Output CSV -------- */
  Serial.print("F,");
  Serial.print(frame_id++);
  Serial.print(",");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(flame);
  Serial.print(",");
  Serial.print(mq135_raw); // raw ADC value

  for (int i = 0; i < 64; i++) {
    Serial.print(",");
    Serial.print(pixels[i], 2);
  }

  Serial.println();

  delay(200); // ~5 FPS, adjust as needed
}
