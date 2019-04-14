/*
  RST     = GPIO5 (D1)
  SDA(SS) = GPIO4 (D2)
  MOSI    = GPIO13 (D7)
  MISO    = GPIO12 (D6)
  SCK     = GPIO14 (D5)
  GND     = GND (GND)
  3.3V    = 3.3V (3.3V)
*/

#define SS_PIN 4  //D2
#define RST_PIN 5 //D1

#include <SPI.h>
#include <MFRC522.h>
#include <ESP8266WiFi.h>
#include <ArduinoJson.h>

MFRC522 mfrc522(SS_PIN, RST_PIN);   // Create MFRC522 instance.
char retryNum = 0;
char* ssid = "umbrella";
char* password = "umbrella";
char* host = "192.168.1.100";
int port = 65432;
WiFiClient wifiClient;

void setup()
{
  const size_t capacity = JSON_OBJECT_SIZE(2) + JSON_OBJECT_SIZE(3) + JSON_OBJECT_SIZE(4);
  DynamicJsonDocument doc(capacity);
  doc["heart"] = false;
  doc["ack"] = false;
  JsonObject shelf = doc.createNestedObject("shelf");
  shelf["id"] = 5;
  shelf["code"] = "CA4238A0B923820DCC509A6F75849B";
  JsonObject action = doc.createNestedObject("action");
  action["number"] = -1;
  action["pos_id"] = -1;
  action["umbrella_uid"] = "";
  
  Serial.begin(9600);   // Initiate a serial communication
  SPI.begin();      // Initiate  SPI bus
  mfrc522.PCD_Init();   // Initiate MFRC522
  while (WiFi.status() != WL_CONNECTED)
  {
    WiFi.begin(ssid, password);
    delay(5000);
    Serial.print(".");
    if (WiFi.status() == WL_CONNECTED) break;
  }
  if (WiFi.status() == WL_CONNECTED)
  {
    Serial.print("WiFi connected, IP: ");
    Serial.println(WiFi.localIP());
  }
  while (!wifiClient.connect("192.168.1.100", 65432))
  {
    Serial.print(".");
    delay(5000);
  }
  Serial.print("Send Connection Message: ");
  serializeJson(doc, Serial);
  serializeJson(doc, wifiClient);
  delay(500);
  const size_t responseCapacity = JSON_OBJECT_SIZE(3) + JSON_OBJECT_SIZE(4) + 60;
  DynamicJsonDocument response(responseCapacity);
  deserializeJson(response, wifiClient);
  Serial.print("\nRecv from server: ");
  serializeJson(response, Serial);
  Serial.println("\nHello NodeMCU based Umbrella Rental System");
}

void wifiConnect()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.print("wifi connection broke down, re-connect");
    while (WiFi.status() != WL_CONNECTED)
    {
      WiFi.begin(ssid, password);
      delay(5000);
      Serial.print(".");
    }
  }
  if (!wifiClient.connected())
  {
    Serial.print("server connection broke down, re-connect");
    while (!wifiClient.connect(host, port))
    {
      Serial.print(".");
      delay(5000);
    }
    const size_t capacity = JSON_OBJECT_SIZE(2) + JSON_OBJECT_SIZE(3) + JSON_OBJECT_SIZE(4);
    DynamicJsonDocument doc(capacity);
    doc["heart"] = false;
    doc["ack"] = false;
    JsonObject shelf = doc.createNestedObject("shelf");
    shelf["id"] = 5;
    shelf["code"] = "CA4238A0B923820DCC509A6F75849B";
    JsonObject action = doc.createNestedObject("action");
    action["number"] = -1;
    action["pos_id"] = -1;
    action["umbrella_uid"] = "";
    Serial.print("Send Connection Message: ");
    serializeJson(doc, Serial);
    serializeJson(doc, wifiClient);
  }
}

String readWifiClient()
{
  String recvString = "";
  while(wifiClient.available())
  {
    recvString += char(wifiClient.read());
  }
  return recvString;
}

String readUID()
{
  if (!mfrc522.PICC_IsNewCardPresent())
  {
    return "";
  }
  // Select one of the cards
  if (!mfrc522.PICC_ReadCardSerial())
  {
    return "";
  }
  String umbrellaUID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++)
  {
    umbrellaUID.concat(String(mfrc522.uid.uidByte[i] < 0x10 ? "0" : ""));
    umbrellaUID.concat(String(mfrc522.uid.uidByte[i], HEX));
  }
  return umbrellaUID;
}

void giveBack(String umbrellaUID)
{
  const size_t capacity = JSON_OBJECT_SIZE(2) + JSON_OBJECT_SIZE(3) + JSON_OBJECT_SIZE(4);
  DynamicJsonDocument doc(capacity);
  doc["heart"] = false;
  doc["ack"] = false;
  JsonObject shelf = doc.createNestedObject("shelf");
  shelf["id"] = 5;
  shelf["code"] = "CA4238A0B923820DCC509A6F75849B";
  JsonObject action = doc.createNestedObject("action");
  action["number"] = 2;
  action["pos_id"] = 7;
  action["umbrella_uid"] = umbrellaUID.c_str();
  Serial.print("give back umbrella: ");
  Serial.println(umbrellaUID);
  wifiConnect();
  serializeJson(doc, wifiClient);
  delay(1000);
  Serial.print("waiting for ack");
  wifiConnect();
  while(!wifiClient.available())
  {
    Serial.print(".");
    delay(1000);
  }
  Serial.println("Client Ready for recv");
  String recvString = readWifiClient();
  Serial.println(recvString);
  const size_t responseCapacity = JSON_OBJECT_SIZE(3) + JSON_OBJECT_SIZE(4) + 60;
  DynamicJsonDocument response(responseCapacity);
  deserializeJson(response, recvString);
  if (response["ack"] == true && response["action"]["number"] == 2 && response["action"]["pos_id"] == 7)
  {
    Serial.println("give back succeed");
  } 
  else
  {
    Serial.println("give back failed");
  }
}

void loop()
{
  String umbrellaUID = readUID();
  if (umbrellaUID != "")
  {
    giveBack(umbrellaUID);
  }
  wifiConnect();
  if (wifiClient.available())
  {
    String recvString = readWifiClient();
    const size_t responseCapacity = JSON_OBJECT_SIZE(3) + JSON_OBJECT_SIZE(4) + 60;
    DynamicJsonDocument response(responseCapacity);
    Serial.print("Recv from server: ");
    Serial.println(recvString);
    deserializeJson(response, recvString);
    if (response["action"]["number"] == 1 and response["ack"] == false and response["action"]["pos_id"] == 7)
    {
      // 借伞请求
      const size_t capacity = JSON_OBJECT_SIZE(2) + JSON_OBJECT_SIZE(3) + JSON_OBJECT_SIZE(4);
      DynamicJsonDocument doc(capacity);
      doc["heart"] = false;
      doc["ack"] = true;
      JsonObject shelf = doc.createNestedObject("shelf");
      shelf["id"] = 5;
      shelf["code"] = "CA4238A0B923820DCC509A6F75849B";
      JsonObject action = doc.createNestedObject("action");
      action["number"] = 1;
      action["pos_id"] = 7;
      action["umbrella_uid"] = "";
      wifiConnect();
      serializeJson(doc, wifiClient);
      Serial.println("borrow umbrella, pos_id: 7 open");
    }
  }
  
  delay(500);
}
