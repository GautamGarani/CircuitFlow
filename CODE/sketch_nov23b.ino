volatile int pulse;
float volume;
unsigned char flowsensor = 2; 
const int irSensorPin = A0; 
const int ledPin = 4; 
const int buzzerPin = 5;
unsigned long currentTime;
unsigned long cloopTime;
const float FLOW_THRESHOLD = 5.0; 

void increase() 
{
  pulse++;
}

void setup()
{
  pinMode(flowsensor, INPUT);
  digitalWrite(flowsensor, HIGH); 
  pinMode(irSensorPin, INPUT);
  digitalWrite(irSensorPin, HIGH);
  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin,OUTPUT);
  Serial.begin(9600);
  attachInterrupt(digitalPinToInterrupt(flowsensor), increase, RISING); 
  sei(); 
  currentTime = millis();
  cloopTime = currentTime;
}

void loop()
{
  currentTime = millis();
  if (currentTime >= (cloopTime + 1000))
  {
    cloopTime = currentTime; 
    volume = 2.633*pulse; 

    int handdetectedHigh = digitalRead(irSensorPin);

    if (volume> FLOW_THRESHOLD && handdetectedHigh == LOW)
    {
      digitalWrite(ledPin, HIGH); 
      tone(buzzerPin, 1000);
      delay(1000);
    }
    else
    {
      digitalWrite(ledPin, LOW);
      noTone(buzzerPin);
      delay(1000);
    }

    Serial.print("Volume: ");
    Serial.println(volume);

    pulse = 0; 
  }
}
