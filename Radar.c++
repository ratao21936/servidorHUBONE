#include <Servo.h>

// Definição dos pinos
#define TRIG_PIN 9
#define ECHO_PIN 10
#define SERVO_PIN 11

Servo meuServo;
float distancia;
int angulo;

void setup() {
  Serial.begin(9600);
  meuServo.attach(SERVO_PIN);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  
  Serial.println("Iniciando Radar...");
  delay(2000);
}

float medirDistancia() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duracao = pulseIn(ECHO_PIN, HIGH);
  float distancia = duracao * 0.034 / 2;
  
  // Limitar distância máxima para 200cm
  if (distancia > 200) {
    distancia = 200;
  }
  
  return distancia;
}

void loop() {
  // Varredura de 0 a 180 graus
  for (angulo = 0; angulo <= 180; angulo++) {
    meuServo.write(angulo);
    delay(30); // Tempo para o servo se mover
    
    distancia = medirDistancia();
    
    // Envia dados: ângulo,distância
    Serial.print(angulo);
    Serial.print(",");
    Serial.println(distancia);
    
    delay(50); // Delay entre medições
  }
  
  // Varredura de 180 a 0 graus
  for (angulo = 180; angulo >= 0; angulo--) {
    meuServo.write(angulo);
    delay(30);
    
    distancia = medirDistancia();
    
    Serial.print(angulo);
    Serial.print(",");
    Serial.println(distancia);
    
    delay(50);
  }
}