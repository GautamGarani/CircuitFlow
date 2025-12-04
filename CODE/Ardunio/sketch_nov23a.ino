
const int ledPin = 9;
const int irSensorPin = A0;       
const int flowSensorPin = 2;      

// Threshold for your IR sensor — adjust as needed
const int irThreshold = 500;
const float pulsesPerLiter = 5880.0;

volatile unsigned long pulseCount = 0;   // number of pulses from flow sensor

void setup() {
  pinMode(ledPin, OUTPUT);
  pinMode(flowSensorPin, INPUT_PULLUP);  
  Serial.begin(9600);
  attachInterrupt(digitalPinToInterrupt(flowSensorPin), countPulse, RISING);
}

void loop() {
  int irValue = analogRead(irSensorPin);
  bool handDetected = (irValue > irThreshold);
  float liters = pulseCount / pulsesPerLiter;
  Serial.print("IR value: ");
  Serial.print(irValue);
  Serial.print(" | Volume (L): ");
  Serial.println(liters, 3);
  if (handDetected && liters > 3.0) {
    digitalWrite(ledPin, HIGH);
  } else {
    digitalWrite(ledPin, LOW);
  }

  delay(200);
}

void countPulse() {
  pulseCount++;
}
