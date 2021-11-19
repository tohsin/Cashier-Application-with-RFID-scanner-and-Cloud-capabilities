
#include "MQ135.h"
#include <SoftwareSerial.h>
#define DEBUG true
int Contrast = 75;
const int sensorPin = A0;
int buzzer = 10;
int air_quality;
#define RX 7
#define TX 8
 // This makes pin 9 of Arduino as RX pin and pin 10 of Arduino as the TX pin
String AP = "Tosin";     
String PASS = "123456789"; 
String API = "2TKLJWFBMBZ79W62";   // Write API KEY
String HOST = "api.thingspeak.com";
String PORT = "80";
String airQualityField = "field1";
int countTrueCommand;
int countTimeCommand;
boolean found = false;
String info;
#include <LiquidCrystal.h>
SoftwareSerial esp8266(RX, TX);
LiquidCrystal lcd(12, 11, 5, 4, 3, 2);

void setup() {
  analogWrite(6, Contrast);
  pinMode(buzzer, OUTPUT);
  lcd.begin(16, 2);
  lcd.setCursor (0, 0);
  lcd.print ("POWER ON ");
  lcd.setCursor (0, 1);
  lcd.print ("Sensor Warming ");
  delay(1000);
  Serial.begin(9600);
  esp8266.begin(115200);
  pinMode(sensorPin, INPUT);        //Gas sensor will be an input to the arduino
  lcd.clear();
  sendCommand("AT", 5, "OK");
  sendCommand("AT+CWMODE=1", 5, "OK");
  sendCommand("AT+CWJAP=\"" + AP + "\",\"" + PASS + "\"", 20, "OK");
 
}

void loop() {

  MQ135 gasSensor = MQ135(A0);
  float air_quality = gasSensor.getPPM();

  String getAirData = "GET /update?api_key=" + API + "&" + airQualityField  + "=" + String(air_quality);
  sendCommand("AT+CIPMUX=1", 5, "OK");
  sendToCloud(getAirData);
  //
  lcd.setCursor (0, 0);
  lcd.print ("Air Quality is ");
  lcd.print (air_quality);
  lcd.print (" PPM ");
  lcd.setCursor (0, 1);
  if (air_quality <= 1000)
  {
    String d="Fresh Air "+info;
    lcd.print(d);
    unbuzz();
  }
  else if ( air_quality >= 1000 && air_quality <= 2000 )
  {
    String d="Poor Air, Open Windows " +info; 
    lcd.print(d);
    buzz();
  }
  else if (air_quality >= 2000 )
  {
    String d="Danger! Move to Fresh Air "+ info;
    lcd.print(d);
    buzz();   // turn the LED on
  }
  lcd.scrollDisplayLeft();
  countTrueCommand++;
  sendCommand("AT+CIPCLOSE=0", 5, "OK");

}

void sendToCloud(String api) {
  sendCommand("AT+CIPSTART=0,\"TCP\",\"" + HOST + "\"," + PORT, 15, "OK");
  sendCommand("AT+CIPSEND=0," + String(api.length() + 4), 4, ">");
  esp8266.println(api);
}

void buzz() {
  tone(buzzer, 1000);
  delay(100);
}
void unbuzz() {
  noTone(buzzer);
  delay(100);
}
void sendCommand(String command, int maxTime, char readReplay[]) {
  Serial.print(countTrueCommand);
  Serial.print(". at command => ");
  Serial.print(command);
  Serial.print(" ");
  while (countTimeCommand < (maxTime * 1))
  {
    esp8266.println(command);//at+cipsend
    if (esp8266.find(readReplay)) //ok
    {
      found = true;
      break;
    }

    countTimeCommand++;
  }

  if (found == true)
  {
    if (command != "AT+CIPCLOSE=0") {
      info = "OK   ";
    }
    Serial.println("OYI");
    countTrueCommand++;
    countTimeCommand = 0;
  }

  if (found == false)
  {
    if (command != "AT+CIPCLOSE=0") {
      info = "BAD   ";
    }
    Serial.println("Fail");
    countTrueCommand = 0;
    countTimeCommand = 0;
  }

  found = false;
}


















//
// if (esp8266.available()) // check if the esp is sending a message
//  {
//    if (esp8266.find("+IPD"))      {
//      delay(1000);
//      int connectionId = esp8266.read() - 48; /* We are subtracting 48 from the output because the read() function returns the ASCII decimal value and the first decimal number which is 0 starts at 48*/
//      String webpage = "<h1>IOT Air Pollution Monitoring System</h1>";
//      webpage += "<p><h2>";
//      webpage += " Air Quality is ";
//      webpage += air_quality;
//      webpage += " PPM";
//      webpage += "<p>";
//
//      if (air_quality <= 1000)
//      {
//        webpage += "Fresh Air";
//      }
//      else if (air_quality <= 2000 && air_quality >= 1000)
//      {
//        webpage += "Poor Air";
//      }
//
//      else if (air_quality >= 2000 )
//      {
//        webpage += "Danger! Move to Fresh Air";
//      }
//
//      webpage += "</h2></p></body>";
//      String cipSend = "AT+CIPSEND=";
//      cipSend += connectionId;
//      cipSend += ",";
//      cipSend += webpage.length();
//      cipSend += "\r\n";
//
//      sendData(cipSend, 1000, DEBUG);
//      sendData(webpage, 1000, DEBUG);
//
//      cipSend = "AT+CIPSEND=";
//      cipSend += connectionId;
//      cipSend += ",";
//      cipSend += webpage.length();
//      cipSend += "\r\n";
//
//      String closeCommand = "AT+CIPCLOSE=";
//      closeCommand += connectionId; // append connection id
//      closeCommand += "\r\n";
//
//      sendData(closeCommand, 3000, DEBUG);
//    }
//  }
