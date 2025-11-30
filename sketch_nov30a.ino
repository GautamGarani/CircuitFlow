const int IR_PIN = A0;         
const int FLOW_PIN = 2;       
const int LED_PIN = 9;         
const int VALVE_PIN = 3;       

volatile unsigned int flow_frequency; 
unsigned int flowRate_LPM;           
unsigned long currentTime;
unsigned long cloopTime;

const int FLOW_THRESHOLD_LPM = 5; 
const int IR_THRESHOLD = 500;     
                                  
void flow() {
  flow_frequency++;
}

void setup() {
  Serial.begin(9600); 
  pinMode(IR_PIN, INPUT);
  pinMode(FLOW_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(VALVE_PIN, OUTPUT);
  pinMode(FLOW_PIN,INPUT_PULLUP);
  digitalWrite(FLOW_PIN, HIGH); 
  attachInterrupt(0, flow, RISING); 
  
  currentTime = millis();
  cloopTime = currentTime;
  digitalWrite(VALVE_PIN, LOW); 
}

void loop() {
  currentTime = millis();
  
    if (currentTime >= (cloopTime + 1000)) {
    cloopTime = currentTime; 
    flowRate_LPM = (flow_frequency * 60 / 450); 
    flow_frequency = 0; 
    Serial.print(flowRate_LPM);
    Serial.println(" L/min");
  }
   int irValue = digitalRead(IR_PIN);
  if (irValue == HIGH && flowRate_LPM > FLOW_THRESHOLD_LPM) { 
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
  if (flowRate_LPM > FLOW_THRESHOLD_LPM) {
    digitalWrite(VALVE_PIN, LOW); 
  } else {
    digitalWrite(VALVE_PIN, HIGH); 
  }
}
