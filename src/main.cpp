#include <Arduino.h>
#include <RBDdimmer.h>

const int zero_cross_pin  = 2;
const int lamp_pin  = 3;
const int MIN_POWER  = 0;
const int MAX_POWER  = 56;
dimmerLamp lamp(lamp_pin);
 

void Serial_Setup_Reply();
void Dimmer_Setup();
int Read_Serial();
void Set_Intensity(int intensity);
void Arduino_Testing();



void setup() {
  Serial_Setup_Reply();
  Dimmer_Setup();
  
}


//Change LED's intensity according to recieved intensity value
void loop() {
  //Set_Intensity(100);
  Set_Intensity(Read_Serial());
}




//Sweep light power to test dimmer
void Dimmer_Setup(){/* function testDimmer */ 
  const int POWER_STEP  = 2;
  const int delay_t = 50;
  int power  = 0;

  lamp.begin(NORMAL_MODE,ON);

  for(power=MIN_POWER;power<=MAX_POWER;power+=POWER_STEP){
    Set_Intensity(power);
    delay(delay_t);
  }
  for(power=MAX_POWER;power>=MIN_POWER;power-=POWER_STEP){
    Set_Intensity(power);
    delay(delay_t);
  }
}


//Setup the Serial Communicaiton
void Serial_Setup_Reply(){
  Serial.begin(115200);
  Serial.setTimeout(1);
  if(Serial.available()){
    //Serial.print(100);
  }
}


//Read Serial input to arudino
int Read_Serial(){
  while (!Serial.available());  //Loop until serial available
  return Serial.readString().toInt();  //Recieve value from the serial port
}


//Set the intensity of the lamp
void Set_Intensity(int intensity){
  intensity = map(intensity,0,100,MIN_POWER,MAX_POWER);
  lamp.setPower(intensity);
}


//Quick Built in LED blinking testing
void Arduino_Testing(){
  digitalWrite(13,HIGH);
  delay(1000);
  digitalWrite(13,LOW);
  delay(1000);
}