volatile int pulse;
float volume;
unsigned char flowsensor = 2; 
const int irSensorPin = A0; 
const int ledPin1 = 4; 
const int ledPin2 = 6;
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
  pinMode(ledPin1, OUTPUT);
  pinMode(ledPin2, OUTPUT);
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
      tone(buzzerPin, 1000);
      delay(500);
    }
    else 
    {
      noTone(buzzerPin);
      delay(500);
    }
    if (handdetectedHigh == LOW)
    {
      digitalWrite(ledPin2, HIGH);
    }
    else 
    {
      digitalWrite(ledPin2, LOW);
    }
    if (volume>FLOW_THRESHOLD)
    {
      digitalWrite(ledPin1, HIGH);
    }
    else
    {
      digitalWrite(ledPin1, LOW);
    }

    while(true){
      Serial.println(volume);
      delay(500);
    }
    

    pulse = 0; 
  }
}
